"""Physical constants. Units: km, s, Hz, degrees where stated."""

MU = 398600.4418          # Earth gravitational parameter, km^3 s^-2
RE = 6378.137             # Earth equatorial radius, km
C = 299792.458            # speed of light in vacuum, km/s
J2 = 1.08262668e-3        # Earth second zonal harmonic
OMEGA_E = 7.2921150e-5    # Earth rotation rate, rad/s

H_GEO = 35786.0           # geostationary altitude above equator, km

# Starlink Ku-band anchor frequencies used in the literature / public specs.
F_KU_DL = 11.325e9        # downlink anchor used by Jardak & Adam (2023)
F_KU_12 = 12.0e9          # round figure used in the source explainer
F_KU_UL = 14.25e9         # uplink centre of the 14.0-14.5 GHz band

ELEV_MASK_DEG = 25.0      # user-terminal elevation mask used by Jardak & Adam
ELEV_MASK_RAD = 0.4363323129985824

# Nominal constellation period, used for arithmetic sanity checks.
NOMINAL_PERIOD_S = 5760.0  # 96 min at ~550 km
HANDOVER_SLOT_S = 15.0     # independently measured global reconfiguration slot
