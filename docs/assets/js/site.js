(function () {
  "use strict";

  const $ = (selector, root) => (root || document).querySelector(selector);
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));

  function fmt(value, digits) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/a";
    return Number(value).toLocaleString("en-US", {
      minimumFractionDigits: digits || 0,
      maximumFractionDigits: digits || 0,
    });
  }

  async function fetchJSON(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${path}`);
    return response.json();
  }

  function initHeader() {
    const header = $(".site-header");
    if (!header) return;
    const toggle = $(".nav-toggle", header);
    const update = () => header.classList.toggle("is-scrolled", window.scrollY > 8);
    update();
    window.addEventListener("scroll", update, { passive: true });
    if (toggle) {
      toggle.addEventListener("click", () => {
        const open = header.getAttribute("data-nav-open") === "true";
        header.setAttribute("data-nav-open", String(!open));
        toggle.setAttribute("aria-expanded", String(!open));
      });
    }
  }

  function initReveal() {
    const items = $$(".reveal");
    if (!items.length) return;
    if (!("IntersectionObserver" in window)) {
      items.forEach((item) => item.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );
    items.forEach((item) => observer.observe(item));
  }

  const PREVIEW_CAPTIONS = {
    overview: "Overview — population, shells, launches, and claim strength",
    atlas: "3D Atlas — mean elements, shell rings, and inclination families",
    migration: "Migration — shell-specific altitude change and catalog flow",
    planes: "Planes — effective RAAN lattice after J2 rectification",
    service: "Service — visibility, handover, Doppler, and radio-only latency",
    learn: "Learn — a 20-concept path from first principles to research vocabulary",
    game: "Neural Orbit — four levels, twenty questions, and a live 3D concept graph",
  };

  function initPreview() {
    const shell = $("[data-preview]");
    if (!shell) return;
    const tabs = $$('[role="tab"]', shell);
    const panels = $$('[role="tabpanel"]', shell);
    const url = $(".fake-url", shell);
    const open = $(".open-demo", shell);
    const caption = $("#preview-caption-text", shell);
    let activeIndex = tabs.findIndex((tab) => tab.getAttribute("aria-selected") === "true");
    if (activeIndex < 0) activeIndex = 0;

    const activate = (index, focus) => {
      if (index < 0) index = tabs.length - 1;
      if (index >= tabs.length) index = 0;
      tabs.forEach((tab, i) => {
        const selected = i === index;
        tab.setAttribute("aria-selected", String(selected));
        tab.setAttribute("tabindex", selected ? "0" : "-1");
      });
      panels.forEach((panel, i) => {
        const selected = i === index;
        panel.hidden = !selected;
        if (!selected) return;
        const frame = $("iframe", panel);
        const wrapper = $(".preview-frame", panel);
        if (frame && !frame.getAttribute("src")) {
          panel.setAttribute("aria-busy", "true");
          frame.addEventListener(
            "load",
            () => {
              panel.setAttribute("aria-busy", "false");
              wrapper.classList.add("is-loaded");
            },
            { once: true }
          );
          frame.setAttribute("src", frame.getAttribute("data-src"));
        }
        if (url) url.textContent = `m0-ar.github.io/starlink-physical-atlas/${panel.getAttribute("data-path")}`;
        if (open) open.setAttribute("href", panel.getAttribute("data-path"));
        if (caption) {
          const key = (panel.id || "").replace(/^panel-/, "");
          caption.textContent = PREVIEW_CAPTIONS[key] || "Interactive product preview";
        }
      });
      if (focus) tabs[index].focus();
      activeIndex = index;
    };

    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => activate(index, false));
      tab.addEventListener("keydown", (event) => {
        const keys = ["ArrowLeft", "ArrowRight", "Home", "End"];
        if (!keys.includes(event.key)) return;
        event.preventDefault();
        if (event.key === "Home") activate(0, true);
        else if (event.key === "End") activate(tabs.length - 1, true);
        else activate(activeIndex + (event.key === "ArrowRight" ? 1 : -1), true);
      });
    });

    activate(activeIndex, false);
  }

  function initYear() {
    $$("[data-year]").forEach((el) => {
      el.textContent = String(new Date().getFullYear());
    });
  }

  function initCharts() {
    if (!window.Chart) return;
    Chart.defaults.color = "#9fb1cc";
    Chart.defaults.borderColor = "rgba(148,183,255,0.12)";
    Chart.defaults.font.family = '"Avenir Next", "Segoe UI", ui-sans-serif, system-ui, sans-serif';
    Chart.defaults.font.size = 11;
    Chart.defaults.plugins.legend.labels.boxWidth = 9;
    Chart.defaults.plugins.legend.labels.boxHeight = 9;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.tooltip.backgroundColor = "rgba(5,12,26,0.96)";
    Chart.defaults.plugins.tooltip.borderColor = "rgba(148,183,255,0.22)";
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.titleColor = "#eaf2ff";
    Chart.defaults.plugins.tooltip.bodyColor = "#9fb1cc";
  }

  window.Atlas = { $, $$, fmt, fetchJSON, initCharts };

  document.addEventListener("DOMContentLoaded", () => {
    initHeader();
    initReveal();
    initPreview();
    initYear();
    initCharts();
  });
})();
