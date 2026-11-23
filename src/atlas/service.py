"""Service-layer simulation: visibility, handover, Doppler, latency bounds.

The model is deliberately geometric.  It propagates the public TLE catalog with
SGP4, rotates to ECEF, and evaluates each site independently.  It does not model
scheduling, beam assignment, weather, or the terrestrial gateway route; latency
is therefore reported as a radio bounding box, not as an end-to-end prediction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .constants import C, ELEV_MASK_DEG, F_KU_12, F_KU_DL, F_KU_UL, RE
from .data import propagate_ecef
from .geometry import Site, elevation_range_azimuth, range_rate


@dataclass(frozen=True)
class ServiceSite:
    name: str
    lat_deg: float
    lon_deg: float


DEFAULT_SITES: tuple[ServiceSite, ...] = (
    ServiceSite("Munich", 48.137, 11.575),
    ServiceSite("Berlin", 52.520, 13.405),
    ServiceSite("Zurich", 47.377, 8.542),
    ServiceSite("Vienna", 48.208, 16.373),
    ServiceSite("Milan", 45.464, 9.190),
    ServiceSite("Paris", 48.857, 2.352),
    ServiceSite("London", 51.507, -0.128),
    ServiceSite("Tromso", 69.649, 18.956),
    ServiceSite("Longyearbyen", 78.223, 15.647),
    ServiceSite("Singapore", 1.352, 103.820),
)


@dataclass
class _SiteState:
    prev_vis: np.ndarray
    prev_rr: np.ndarray
    run_steps: np.ndarray
    run_max_elev: np.ndarray
    run_max_rr: np.ndarray
    run_max_rr_rate: np.ndarray
    prev_serving: int = -1
    handover_times: list[pd.Timestamp] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    pass_duration: list[float] = field(default_factory=list)
    pass_max_elev: list[float] = field(default_factory=list)
    pass_max_doppler_khz: list[float] = field(default_factory=list)
    pass_max_rate_khz_s: list[float] = field(default_factory=list)


def simulate_service(
    df: pd.DataFrame,
    timestamps: pd.Series,
    sites: tuple[ServiceSite, ...] = DEFAULT_SITES,
    chunk: int = 48,
    dt_s: float = 15.0,
    max_steps: int | None = None,
    max_sats: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Run the service simulation.

    Returns (site_summary, rtt_rows, handover_rows, pass_rows, meta).
    """
    work = df
    if max_sats is not None:
        work = work.iloc[:max_sats].copy()
    if max_steps is not None:
        timestamps = timestamps.iloc[:max_steps]
    nsat = len(work)
    states = {
        s.name: _SiteState(
            prev_vis=np.zeros(nsat, dtype=bool),
            prev_rr=np.zeros(nsat),
            run_steps=np.zeros(nsat, dtype=np.int32),
            run_max_elev=np.zeros(nsat),
            run_max_rr=np.zeros(nsat),
            run_max_rr_rate=np.zeros(nsat),
        )
        for s in sites
    }
    site_objs = {s.name: Site(s.name, s.lat_deg, s.lon_deg) for s in sites}
    n_bad = 0
    n_total = 0

    for err, r_ecef, v_ecef, keys, names, ts in propagate_ecef(work, timestamps, chunk=chunk):
        ntime = r_ecef.shape[1]
        n_bad += int(np.sum(err != 0))
        n_total += err.size
        good = err == 0
        r_sat = np.linalg.norm(r_ecef, axis=-1)
        cols = np.arange(ntime)
        for s in sites:
            st = states[s.name]
            site = site_objs[s.name]
            elev, rng, _ = elevation_range_azimuth(r_ecef, site)
            rr = range_rate(r_ecef, v_ecef, site)
            vis = (elev >= ELEV_MASK_DEG) & good
            n_visible = vis.sum(axis=0)
            elev_masked = np.where(good, elev, -np.inf)
            serving = np.argmax(elev_masked, axis=0)
            serving = np.where(n_visible > 0, serving, -1)
            serv_elev = np.where(serving >= 0, elev[serving, cols], np.nan)
            serv_rng = np.where(serving >= 0, rng[serving, cols], np.nan)
            serv_h = np.where(serving >= 0, r_sat[serving, cols] - RE, np.nan)
            rtt_low = 2.0 * (serv_rng + serv_h) / C * 1e3
            rtt_high = 4.0 * serv_rng / C * 1e3
            for j in range(ntime):
                st.rows.append((
                    s.name, ts[j], int(n_visible[j]), float(serv_elev[j]),
                    float(serv_rng[j]), float(rtt_low[j]), float(rtt_high[j]),
                ))
            chg = (
                (serving[1:] != serving[:-1])
                & (serving[1:] >= 0)
                & (serving[:-1] >= 0)
            )
            if ntime and st.prev_serving >= 0 and serving[0] >= 0 and serving[0] != st.prev_serving:
                st.handover_times.append(ts[0])
            st.handover_times.extend(ts[1:][chg].tolist())
            st.prev_serving = int(serving[-1])

            prev_vis = st.prev_vis
            for j in range(ntime):
                v = vis[:, j]
                e = elev[:, j]
                q = rr[:, j]
                rate = (q - st.prev_rr) / dt_s
                start = v & ~prev_vis
                cont = v & prev_vis
                end = ~v & prev_vis
                if start.any():
                    st.run_steps[start] = 1
                    st.run_max_elev[start] = e[start]
                    st.run_max_rr[start] = np.abs(q[start])
                    st.run_max_rr_rate[start] = 0.0
                if cont.any():
                    st.run_steps[cont] += 1
                    st.run_max_elev[cont] = np.maximum(st.run_max_elev[cont], e[cont])
                    st.run_max_rr[cont] = np.maximum(st.run_max_rr[cont], np.abs(q[cont]))
                    st.run_max_rr_rate[cont] = np.maximum(
                        st.run_max_rr_rate[cont], np.abs(rate[cont])
                    )
                if end.any():
                    idx = np.where(end)[0]
                    st.pass_duration.extend((st.run_steps[idx] * dt_s).tolist())
                    st.pass_max_elev.extend(st.run_max_elev[idx].tolist())
                    st.pass_max_doppler_khz.extend(
                        (st.run_max_rr[idx] * F_KU_DL / C / 1e3).tolist()
                    )
                    st.pass_max_rate_khz_s.extend(
                        (st.run_max_rr_rate[idx] * F_KU_DL / C / 1e3).tolist()
                    )
                prev_vis = v
                st.prev_rr = q.copy()
            st.prev_vis = prev_vis

    # Close passes still active at the end of the window.
    for s in sites:
        st = states[s.name]
        idx = np.where(st.prev_vis)[0]
        if len(idx):
            st.pass_duration.extend((st.run_steps[idx] * dt_s).tolist())
            st.pass_max_elev.extend(st.run_max_elev[idx].tolist())
            st.pass_max_doppler_khz.extend((st.run_max_rr[idx] * F_KU_DL / C / 1e3).tolist())
            st.pass_max_rate_khz_s.extend((st.run_max_rr_rate[idx] * F_KU_DL / C / 1e3).tolist())

    duration_h = len(timestamps) * dt_s / 3600.0
    summary, rtt_rows, hoff_rows, pass_rows = [], [], [], []
    for s in sites:
        st = states[s.name]
        rows = pd.DataFrame(st.rows, columns=[
            "site", "time", "n_visible", "serving_elev_deg", "serving_range_km",
            "rtt_lower_ms", "rtt_upper_ms",
        ])
        rtt_rows.append(rows)
        hoffs = pd.to_datetime(pd.Series(st.handover_times), utc=True)
        intervals = hoffs.diff().dt.total_seconds().dropna().to_numpy()
        if len(hoffs):
            hoff_rows.append(pd.DataFrame({"site": s.name, "time": hoffs, "interval_s": np.r_[np.nan, intervals]}))
        passes = pd.DataFrame({
            "site": s.name,
            "duration_s": st.pass_duration,
            "max_elev_deg": st.pass_max_elev,
            "max_doppler_khz": st.pass_max_doppler_khz,
            "max_doppler_rate_khz_s": st.pass_max_rate_khz_s,
        })
        pass_rows.append(passes)
        night = rows.dropna(subset=["rtt_lower_ms"])
        summary.append({
            "site": s.name,
            "lat_deg": s.lat_deg,
            "lon_deg": s.lon_deg,
            "n_visible_p50": float(rows["n_visible"].median()),
            "n_visible_p95": float(rows["n_visible"].quantile(0.95)),
            "n_visible_max": int(rows["n_visible"].max()),
            "serving_elev_p50_deg": float(night["serving_elev_deg"].median()),
            "serving_elev_p95_deg": float(night["serving_elev_deg"].quantile(0.95)),
            "serving_range_p50_km": float(night["serving_range_km"].median()),
            "serving_range_p95_km": float(night["serving_range_km"].quantile(0.95)),
            "rtt_lower_p50_ms": float(night["rtt_lower_ms"].median()),
            "rtt_lower_p95_ms": float(night["rtt_lower_ms"].quantile(0.95)),
            "rtt_upper_p50_ms": float(night["rtt_upper_ms"].median()),
            "rtt_upper_p95_ms": float(night["rtt_upper_ms"].quantile(0.95)),
            "handovers_per_hour": float(len(hoffs) / duration_h),
            "handover_interval_p50_s": float(np.median(intervals)) if len(intervals) else np.nan,
            "handover_interval_p90_s": float(np.percentile(intervals, 90)) if len(intervals) else np.nan,
            "handover_interval_max_s": float(intervals.max()) if len(intervals) else np.nan,
            "handover_slot_fraction": float(len(hoffs) / max(len(timestamps), 1)),
            "passes": len(passes),
            "pass_duration_p50_s": float(passes["duration_s"].median()) if len(passes) else np.nan,
            "pass_duration_p90_s": float(passes["duration_s"].quantile(0.90)) if len(passes) else np.nan,
            "pass_max_elev_p50_deg": float(passes["max_elev_deg"].median()) if len(passes) else np.nan,
            "pass_max_elev_p90_deg": float(passes["max_elev_deg"].quantile(0.90)) if len(passes) else np.nan,
            "pass_max_doppler_p50_khz": float(passes["max_doppler_khz"].median()) if len(passes) else np.nan,
            "pass_max_doppler_p95_khz": float(passes["max_doppler_khz"].quantile(0.95)) if len(passes) else np.nan,
            "pass_max_doppler_rate_p50_khz_s": float(passes["max_doppler_rate_khz_s"].median()) if len(passes) else np.nan,
            "pass_max_doppler_rate_p95_khz_s": float(passes["max_doppler_rate_khz_s"].quantile(0.95)) if len(passes) else np.nan,
            "frac_passes_doppler_gt_230khz": float((passes["max_doppler_khz"] > 230.0).mean()) if len(passes) else np.nan,
            "frac_passes_rate_gt_5khz_s": float((passes["max_doppler_rate_khz_s"] > 5.0).mean()) if len(passes) else np.nan,
        })

    meta = {
        "n_satellites": nsat,
        "n_steps": len(timestamps),
        "dt_s": dt_s,
        "duration_h": duration_h,
        "t0": timestamps.iloc[0].isoformat(),
        "t1": timestamps.iloc[-1].isoformat(),
        "elev_mask_deg": ELEV_MASK_DEG,
        "sgp4_error_rate": n_bad / max(n_total, 1),
        "frequencies_hz": {
            "downlink_ku_hz": F_KU_DL,
            "uplink_ku_hz": F_KU_UL,
            "reference_12ghz_hz": F_KU_12,
        },
    }
    return (
        pd.DataFrame(summary),
        pd.concat(rtt_rows, ignore_index=True),
        pd.concat(hoff_rows, ignore_index=True) if hoff_rows else pd.DataFrame(),
        pd.concat(pass_rows, ignore_index=True),
        meta,
    )
