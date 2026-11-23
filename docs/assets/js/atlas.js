import * as THREE from "three";
import { OrbitControls } from "../vendor/OrbitControls.js";

const EARTH_RADIUS_KM = 6371;
const FAMILY_COLORS = {
  "30.5": "#ff8a5c",
  "43.0": "#5eead4",
  "53.1": "#7dd3fc",
  "70.0": "#c084fc",
  "97.4": "#facc15",
  other: "#94a3b8",
};

const container = document.getElementById("atlas-canvas");
const fallback = document.getElementById("atlas-fallback");
const tooltip = document.getElementById("atlas-tooltip");
const selectedPanel = document.getElementById("atlas-selected");
const visibleOut = document.getElementById("atlas-visible");
const clockOut = document.getElementById("atlas-clock");
const altOut = document.getElementById("altitude-value");
const speedOut = document.getElementById("speed-value");
const pauseButton = document.getElementById("pause-button");
const resetButton = document.getElementById("reset-button");
const toggles = document.getElementById("family-toggles");
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
} catch (error) {
  showFallback(error);
  throw error;
}

renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
container.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(46, container.clientWidth / container.clientHeight, 0.01, 300);
const home = new THREE.Vector3(2.75, 1.55, 4.0);
camera.position.copy(home);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.rotateSpeed = 0.55;
controls.zoomSpeed = 0.75;
controls.minDistance = 1.35;
controls.maxDistance = 14;
controls.autoRotate = !reduced;
controls.autoRotateSpeed = 0.35;
controls.addEventListener("start", () => {
  controls.autoRotate = false;
});

scene.add(new THREE.AmbientLight(0x8ea6cc, 1.0));
const sun = new THREE.DirectionalLight(0xffffff, 2.6);
sun.position.set(5, 3, 6);
scene.add(sun);
const rim = new THREE.DirectionalLight(0x2dd4bf, 0.55);
rim.position.set(-4, -2, -5);
scene.add(rim);

const earthMaterial = new THREE.MeshPhongMaterial({
  color: 0xffffff,
  emissive: 0x06101f,
  specular: 0x22344c,
  shininess: 9,
});
const earth = new THREE.Mesh(new THREE.SphereGeometry(1, 72, 72), earthMaterial);
scene.add(earth);
new THREE.TextureLoader().load(
  "../assets/earth_atmos_2048.jpg",
  (texture) => {
    texture.colorSpace = THREE.SRGBColorSpace;
    earthMaterial.map = texture;
    earthMaterial.needsUpdate = true;
  },
  undefined,
  () => {
    earthMaterial.color.set(0x1b4d6b);
  }
);

const atmosphere = new THREE.Mesh(
  new THREE.SphereGeometry(1.035, 72, 72),
  new THREE.ShaderMaterial({
    transparent: true,
    side: THREE.BackSide,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    vertexShader: "varying vec3 vNormal; void main(){ vNormal = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
    fragmentShader: "varying vec3 vNormal; void main(){ float intensity = pow(0.72 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 3.0); gl_FragColor = vec4(0.22, 0.74, 1.0, 0.65) * intensity; }",
  })
);
scene.add(atmosphere);

const stars = makeStars();
scene.add(stars);

const shellGroup = new THREE.Group();
scene.add(shellGroup);

const marker = new THREE.Mesh(
  new THREE.SphereGeometry(0.016, 12, 12),
  new THREE.MeshBasicMaterial({ color: 0xffffff })
);
marker.visible = false;
scene.add(marker);

const familyGroups = new Map();
const allSats = [];
const clock = new THREE.Clock();
let time = 0;
let speed = reduced ? 0 : 60;
let paused = reduced;
let altitudeScale = 2.5;
let hovered = null;
let selected = null;
let pointer = null;
let pointerDown = null;
let lastPick = 0;

const vertexShader = `
  uniform float uTime;
  uniform float uExag;
  attribute vec3 aBasisU;
  attribute vec3 aBasisV;
  attribute float aPhase;
  attribute float aRate;
  attribute float aAlt;
  attribute vec3 aColor;
  attribute float aSize;
  varying vec3 vColor;
  void main() {
    float theta = aPhase + aRate * uTime;
    vec3 dir = normalize(aBasisU * cos(theta) + aBasisV * sin(theta));
    float radius = 1.0 + (aAlt / 6371.0) * uExag;
    vec3 p = dir * radius;
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    gl_PointSize = aSize * (300.0 / max(0.1, -mv.z));
    gl_Position = projectionMatrix * mv;
    vColor = aColor;
  }
`;

const fragmentShader = `
  varying vec3 vColor;
  void main() {
    vec2 c = gl_PointCoord - vec2(0.5);
    float d = length(c);
    if (d > 0.5) discard;
    float alpha = smoothstep(0.5, 0.12, d);
    gl_FragColor = vec4(vColor, alpha * 0.9);
  }
`;

function makeStars() {
  const count = 2400;
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i += 1) {
    const radius = 30 + Math.random() * 70;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = radius * Math.cos(phi);
    positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({
    color: 0xbfdbfe,
    size: 0.12,
    sizeAttenuation: true,
    transparent: true,
    opacity: 0.72,
    depthWrite: false,
  });
  return new THREE.Points(geometry, material);
}

function degrees(value) {
  return (Number(value) * Math.PI) / 180;
}

function colorFor(family) {
  return new THREE.Color(FAMILY_COLORS[String(family)] || FAMILY_COLORS.other);
}

function buildSatelliteData(rows) {
  const groups = new Map();
  rows.forEach((row) => {
    const [name, norad, inc, raan, ecc, argp, ma, mm, alt, a, family, shell] = row;
    const omega = degrees(raan);
    const incRad = degrees(inc);
    const cosO = Math.cos(omega);
    const sinO = Math.sin(omega);
    const cosI = Math.cos(incRad);
    const sinI = Math.sin(incRad);
    const sat = {
      name,
      norad,
      inc,
      raan,
      ecc,
      argp,
      ma,
      mm,
      alt,
      a,
      family: String(family),
      shell,
      basisU: [cosO, sinO, 0],
      basisV: [-sinO * cosI, cosO * cosI, sinI],
      phase: degrees(argp + ma),
      rate: (Number(mm) * Math.PI * 2) / 86400,
      color: colorFor(family),
    };
    allSats.push(sat);
    if (!groups.has(sat.family)) groups.set(sat.family, []);
    groups.get(sat.family).push(sat);
  });
  return groups;
}

function createFamilyPoints(family, sats) {
  const n = sats.length;
  const basisU = new Float32Array(n * 3);
  const basisV = new Float32Array(n * 3);
  const phase = new Float32Array(n);
  const rate = new Float32Array(n);
  const alt = new Float32Array(n);
  const color = new Float32Array(n * 3);
  const size = new Float32Array(n);
  sats.forEach((sat, i) => {
    basisU.set(sat.basisU, i * 3);
    basisV.set(sat.basisV, i * 3);
    phase[i] = sat.phase;
    rate[i] = sat.rate;
    alt[i] = sat.alt;
    color[i * 3] = sat.color.r;
    color[i * 3 + 1] = sat.color.g;
    color[i * 3 + 2] = sat.color.b;
    size[i] = sat.family === "other" ? 0.045 : 0.062;
  });
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("aBasisU", new THREE.BufferAttribute(basisU, 3));
  geometry.setAttribute("aBasisV", new THREE.BufferAttribute(basisV, 3));
  geometry.setAttribute("aPhase", new THREE.BufferAttribute(phase, 1));
  geometry.setAttribute("aRate", new THREE.BufferAttribute(rate, 1));
  geometry.setAttribute("aAlt", new THREE.BufferAttribute(alt, 1));
  geometry.setAttribute("aColor", new THREE.BufferAttribute(color, 3));
  geometry.setAttribute("aSize", new THREE.BufferAttribute(size, 1));
  geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  const material = new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 }, uExag: { value: altitudeScale } },
    vertexShader,
    fragmentShader,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const points = new THREE.Points(geometry, material);
  points.frustumCulled = false;
  return points;
}

function addShellRings(shells) {
  shells.forEach((shell) => {
    const radius = 1 + Number(shell.alt_median_km) / EARTH_RADIUS_KM;
    const inc = degrees(shell.inc_median_deg);
    const points = [];
    for (let i = 0; i < 160; i += 1) {
      const u = (i / 160) * Math.PI * 2;
      points.push(new THREE.Vector3(radius * Math.cos(u), radius * Math.sin(u) * Math.cos(inc), radius * Math.sin(u) * Math.sin(inc)));
    }
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({
      color: colorFor(shell.family),
      transparent: true,
      opacity: 0.16,
      depthWrite: false,
    });
    shellGroup.add(new THREE.LineLoop(geometry, material));
  });
}

function setupToggles(groups) {
  const order = ["30.5", "43.0", "53.1", "70.0", "97.4", "other"];
  order.forEach((family) => {
    if (!groups.has(family)) return;
    const count = groups.get(family).length;
    const label = document.createElement("label");
    label.className = "family-toggle";
    label.innerHTML = `<input type="checkbox" checked data-family="${family}"><span class="swatch" style="--c:${FAMILY_COLORS[family]}"></span>${family === "other" ? "Other" : family + "°"} <span class="faint">(${count.toLocaleString("en-US")})</span>`;
    label.querySelector("input").addEventListener("change", (event) => {
      const group = familyGroups.get(family);
      if (group) group.visible = event.target.checked;
      updateVisibleCount();
    });
    toggles.appendChild(label);
  });
}

function updateVisibleCount() {
  let count = 0;
  familyGroups.forEach((group) => {
    if (group.visible) count += group.userData.count;
  });
  visibleOut.textContent = count.toLocaleString("en-US");
}

function formatClock(seconds) {
  const total = Math.max(0, Math.floor(seconds));
  const h = Math.floor(total / 3600) % 24;
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return `T+ ${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function setSelected(sat) {
  selected = sat;
  if (!sat) {
    marker.visible = false;
    selectedPanel.innerHTML = '<strong>Click a point</strong><div class="sub" style="color:var(--faint);font-size:11px;margin-top:3px">Satellite name, altitude, inclination, RAAN, and shell will appear here.</div>';
    return;
  }
  marker.visible = true;
  selectedPanel.innerHTML = `
    <strong>${escapeHtml(sat.name)}</strong>
    <div class="grid">
      <span>Altitude</span><span class="mono">${sat.alt.toFixed(1)} km</span>
      <span>Inclination</span><span class="mono">${sat.inc.toFixed(2)}°</span>
      <span>RAAN</span><span class="mono">${sat.raan.toFixed(2)}°</span>
      <span>Shell</span><span class="mono">${sat.shell === null ? "unassigned" : sat.shell.toFixed(0) + " km"}</span>
      <span>Eccentricity</span><span class="mono">${Number(sat.ecc).toFixed(5)}</span>
      <span>Mean motion</span><span class="mono">${Number(sat.mm).toFixed(4)} rev/day</span>
    </div>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function satPosition(sat, t, target) {
  const theta = sat.phase + sat.rate * t;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const radius = 1 + (sat.alt / EARTH_RADIUS_KM) * altitudeScale;
  target.set(
    (sat.basisU[0] * c + sat.basisV[0] * s) * radius,
    (sat.basisU[1] * c + sat.basisV[1] * s) * radius,
    (sat.basisU[2] * c + sat.basisV[2] * s) * radius
  );
  return target;
}

const pickVector = new THREE.Vector3();
function pickAt(clientX, clientY) {
  const rect = renderer.domElement.getBoundingClientRect();
  const mx = clientX - rect.left;
  const my = clientY - rect.top;
  const w = rect.width;
  const h = rect.height;
  camera.updateMatrixWorld();
  let best = null;
  let bestDistance = 13;
  allSats.forEach((sat) => {
    const group = familyGroups.get(sat.family);
    if (!group || !group.visible) return;
    satPosition(sat, time, pickVector);
    pickVector.project(camera);
    if (pickVector.z > 1) return;
    const sx = (pickVector.x * 0.5 + 0.5) * w;
    const sy = (-pickVector.y * 0.5 + 0.5) * h;
    const distance = Math.hypot(sx - mx, sy - my);
    if (distance < bestDistance) {
      bestDistance = distance;
      best = sat;
    }
  });
  return best;
}

function handlePointerMove(event) {
  pointer = { x: event.clientX, y: event.clientY };
  const now = performance.now();
  if (now - lastPick < 80) return;
  lastPick = now;
  const sat = pickAt(event.clientX, event.clientY);
  hovered = sat;
  if (sat) {
    tooltip.style.display = "block";
    tooltip.textContent = `${sat.name} · ${sat.alt.toFixed(0)} km · ${sat.inc.toFixed(1)}°`;
    const rect = container.getBoundingClientRect();
    tooltip.style.left = `${event.clientX - rect.left + 12}px`;
    tooltip.style.top = `${event.clientY - rect.top + 12}px`;
    renderer.domElement.style.cursor = "pointer";
  } else {
    tooltip.style.display = "none";
    renderer.domElement.style.cursor = "grab";
  }
}

function handlePointerDown(event) {
  pointerDown = { x: event.clientX, y: event.clientY };
}

function handlePointerUp(event) {
  if (!pointerDown) return;
  const moved = Math.hypot(event.clientX - pointerDown.x, event.clientY - pointerDown.y);
  pointerDown = null;
  if (moved > 5) return;
  setSelected(pickAt(event.clientX, event.clientY));
}

function onResize() {
  const width = container.clientWidth;
  const height = container.clientHeight;
  if (!width || !height) return;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.05);
  if (!paused) time += delta * speed;
  familyGroups.forEach((group) => {
    group.material.uniforms.uTime.value = time;
    group.material.uniforms.uExag.value = altitudeScale;
  });
  if (selected) {
    satPosition(selected, time, marker.position);
  }
  clockOut.textContent = formatClock(time);
  controls.update();
  renderer.render(scene, camera);
}

function showFallback(error) {
  if (fallback) fallback.hidden = false;
  console.error(error);
}

async function init() {
  const response = await fetch("../data/atlas.json");
  if (!response.ok) throw new Error(`atlas.json: ${response.status}`);
  const atlas = await response.json();
  const satResponse = await fetch("../data/satellites.json");
  if (!satResponse.ok) throw new Error(`satellites.json: ${satResponse.status}`);
  const satellites = await satResponse.json();

  addShellRings(atlas.shells);
  const groups = buildSatelliteData(satellites.rows);
  groups.forEach((sats, family) => {
    const points = createFamilyPoints(family, sats);
    points.userData.count = sats.length;
    familyGroups.set(family, points);
    scene.add(points);
  });
  setupToggles(groups);
  updateVisibleCount();

  document.getElementById("altitude-scale").addEventListener("input", (event) => {
    altitudeScale = Number(event.target.value);
    altOut.textContent = `${altitudeScale.toFixed(1)}×`;
  });
  document.getElementById("time-speed").addEventListener("input", (event) => {
    speed = Number(event.target.value);
    speedOut.textContent = `${speed}×`;
    if (speed > 0 && paused) {
      paused = false;
      pauseButton.textContent = "Pause";
    }
  });
  document.getElementById("toggle-shells").addEventListener("change", (event) => {
    shellGroup.visible = event.target.checked;
  });
  document.getElementById("toggle-stars").addEventListener("change", (event) => {
    stars.visible = event.target.checked;
  });
  pauseButton.addEventListener("click", () => {
    paused = !paused;
    pauseButton.textContent = paused ? "Play" : "Pause";
  });
  resetButton.addEventListener("click", () => {
    camera.position.copy(home);
    controls.target.set(0, 0, 0);
    controls.update();
    controls.autoRotate = !reduced;
  });

  if (reduced) {
    pauseButton.textContent = "Play";
    speedOut.textContent = "0×";
    document.getElementById("time-speed").value = "0";
  }

  renderer.domElement.addEventListener("pointermove", handlePointerMove);
  renderer.domElement.addEventListener("pointerdown", handlePointerDown);
  renderer.domElement.addEventListener("pointerup", handlePointerUp);
  renderer.domElement.addEventListener("pointerleave", () => {
    tooltip.style.display = "none";
    hovered = null;
  });
  window.addEventListener("resize", onResize);
  if ("ResizeObserver" in window) new ResizeObserver(onResize).observe(container);
  animate();
}

init().catch(showFallback);
