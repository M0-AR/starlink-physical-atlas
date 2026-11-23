import * as THREE from "three";
import { OrbitControls } from "../vendor/OrbitControls.js";

const LEVEL_COLORS = {
  explorer: "#67e8f9",
  analyst: "#5eead4",
  operator: "#c084fc",
  researcher: "#facc15",
};
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const container = document.getElementById("game-canvas");
const startPanel = document.getElementById("start-panel");
const questionPanel = document.getElementById("question-panel");
const levelPanel = document.getElementById("level-panel");
const finishPanel = document.getElementById("finish-panel");
const startButton = document.getElementById("start-button");
const nextButton = document.getElementById("next-button");
const continueButton = document.getElementById("continue-button");
const restartButton = document.getElementById("restart-button");
const promptEl = document.getElementById("question-prompt");
const answersEl = document.getElementById("answers");
const explainEl = document.getElementById("explain");
const progressEl = document.getElementById("question-progress");
const countEl = document.getElementById("question-count");
const levelEl = document.getElementById("question-level");
const runningEl = document.getElementById("running-score");
const hudLevel = document.getElementById("hud-level");
const hudScore = document.getElementById("hud-score");
const bestEl = document.getElementById("best-score");
const levelKicker = document.getElementById("level-kicker");
const levelTitle = document.getElementById("level-title");
const levelSummary = document.getElementById("level-summary");
const levelCorrectEl = document.getElementById("level-correct");
const levelTotalEl = document.getElementById("level-total");
const finalText = document.getElementById("final-text");
const finalScore = document.getElementById("final-score");
const finalBest = document.getElementById("final-best");
const muteButtons = [document.getElementById("mute-button"), document.getElementById("mute-button-2")].filter(Boolean);

let data;
let questionsByLevel = [];
let nodes = new Map();
let nodeById = new Map();
let edges = [];
let scene;
let camera;
let renderer;
let controls;
let graph;
let clock;
let elapsed = 0;
let muted = false;
let state = { levelIndex: 0, qIndex: 0, totalCorrect: 0, levelCorrect: 0, answered: false };
let best = Number(localStorage.getItem("neural-orbit-best") || 0);

function initScene() {
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  } catch (error) {
    console.warn("3D graph unavailable", error);
    container.innerHTML = '<div class="atlas-fallback"><p class="muted">The 3D graph is unavailable, but the questions still work.</p></div>';
    return;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(42, container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.set(0, 0.35, 9.2);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.enablePan = false;
  controls.enableZoom = false;
  controls.autoRotate = !reduced;
  controls.autoRotateSpeed = 0.32;
  controls.minPolarAngle = Math.PI * 0.28;
  controls.maxPolarAngle = Math.PI * 0.72;
  controls.target.set(0, 0, 0);

  scene.add(new THREE.AmbientLight(0xb8ccef, 1.25));
  const key = new THREE.PointLight(0x67e8f9, 8, 30);
  key.position.set(4, 5, 7);
  scene.add(key);
  const fill = new THREE.PointLight(0xc084fc, 5, 30);
  fill.position.set(-5, -2, 4);
  scene.add(fill);

  graph = new THREE.Group();
  scene.add(graph);
  addStars();
  clock = new THREE.Clock();
  animate();
}

function addStars() {
  const count = 1300;
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i += 1) {
    const radius = 16 + Math.random() * 24;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = radius * Math.cos(phi);
    positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({ color: 0x9fb1cc, size: 0.07, transparent: true, opacity: 0.6, depthWrite: false });
  scene.add(new THREE.Points(geometry, material));
}

function labelSprite(text, color) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 96;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = '600 34px "Avenir Next", "Segoe UI", ui-sans-serif, sans-serif';
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const width = Math.min(490, ctx.measureText(text).width + 34);
  ctx.fillStyle = "rgba(5,9,20,0.62)";
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect((512 - width) / 2, 17, width, 62, 18);
  else ctx.rect((512 - width) / 2, 17, width, 62);
  ctx.fill();
  ctx.fillStyle = color;
  ctx.fillText(text, 256, 50);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(1.35, 0.25, 1);
  return sprite;
}

function buildGraph() {
  if (!scene) return;
  const levelIds = data.levels.map((l) => l.id);
  const perLevel = new Map();
  data.concepts.forEach((concept) => {
    if (!perLevel.has(concept.level)) perLevel.set(concept.level, []);
    perLevel.get(concept.level).push(concept);
  });
  const positions = new Map();
  data.levels.forEach((level, levelIndex) => {
    const concepts = perLevel.get(level.id) || [];
    const radius = 2.25;
    concepts.forEach((concept, index) => {
      const angle = (index / concepts.length) * Math.PI * 2 + levelIndex * 0.55;
      const position = new THREE.Vector3(radius * Math.cos(angle), 2.0 - levelIndex * 1.33, radius * Math.sin(angle));
      positions.set(concept.id, position);
      const color = new THREE.Color(LEVEL_COLORS[level.id] || "#67e8f9");
      const geometry = new THREE.IcosahedronGeometry(0.1, 1);
      const material = new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.18,
        roughness: 0.35,
        metalness: 0.25,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.copy(position);
      mesh.userData.concept = concept;
      graph.add(mesh);
      nodes.set(concept.id, mesh);
      nodeById.set(concept.id, concept);
      const wire = new THREE.LineSegments(
        new THREE.EdgesGeometry(geometry),
        new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.4 })
      );
      mesh.add(wire);
      const label = labelSprite(concept.label, LEVEL_COLORS[level.id] || "#eaf2ff");
      label.position.set(position.x, position.y + 0.2, position.z);
      graph.add(label);
      mesh.userData.label = label;
    });
  });

  const seen = new Set();
  data.concepts.forEach((concept) => {
    (concept.links || []).forEach((targetId) => {
      if (!positions.has(targetId)) return;
      const key = [concept.id, targetId].sort().join("::");
      if (seen.has(key)) return;
      seen.add(key);
      const material = new THREE.LineBasicMaterial({ color: 0x5b7aa8, transparent: true, opacity: 0.18 });
      const geometry = new THREE.BufferGeometry().setFromPoints([positions.get(concept.id), positions.get(targetId)]);
      const line = new THREE.Line(geometry, material);
      graph.add(line);
      edges.push({ a: concept.id, b: targetId, line });
    });
  });
  setActiveLevel(0);
}

function setActiveLevel(index) {
  const active = data.levels[index].id;
  nodes.forEach((mesh) => {
    const isActive = mesh.userData.concept.level === active;
    mesh.material.emissiveIntensity = isActive ? 0.7 : 0.12;
    mesh.scale.setScalar(isActive ? 1.25 : 1);
    if (mesh.userData.label) mesh.userData.label.visible = isActive;
  });
}

function highlightConcept(id, color) {
  const mesh = nodes.get(id);
  if (!mesh) return;
  mesh.material.emissive.set(color);
  mesh.material.emissiveIntensity = 2.2;
  mesh.scale.setScalar(1.55);
  mesh.userData.pulse = 2.2;
  edges.forEach((edge) => {
    if (edge.a === id || edge.b === id) {
      edge.line.material.color.set(color);
      edge.line.material.opacity = 0.92;
    }
  });
}

function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.05);
  elapsed += delta;
  nodes.forEach((mesh) => {
    if (mesh.userData.pulse > 0) {
      mesh.userData.pulse = Math.max(0, mesh.userData.pulse - delta);
      const pulse = 1 + Math.sin(elapsed * 7) * 0.12;
      mesh.scale.setScalar(1.55 * pulse);
    }
  });
  controls.update();
  renderer.render(scene, camera);
}

function resize() {
  if (!renderer || !camera) return;
  const width = container.clientWidth;
  const height = container.clientHeight;
  if (!width || !height) return;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

function speak(text) {
  if (muted || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.98;
  utterance.pitch = 1.0;
  utterance.volume = 0.92;
  window.speechSynthesis.speak(utterance);
}

function setMuted(next) {
  muted = next;
  muteButtons.forEach((button) => {
    button.textContent = muted ? "Sound off" : "Sound on";
    button.setAttribute("aria-pressed", String(muted));
  });
  if (muted && "speechSynthesis" in window) window.speechSynthesis.cancel();
}

function showPanel(panel) {
  [startPanel, questionPanel, levelPanel, finishPanel].forEach((item) => {
    item.hidden = item !== panel;
  });
}

function updateHud() {
  const level = data.levels[state.levelIndex];
  hudLevel.textContent = level.name;
  hudScore.textContent = `${state.totalCorrect} correct`;
  runningEl.textContent = `${state.totalCorrect} correct`;
}

function startGame() {
  state = { levelIndex: 0, qIndex: 0, totalCorrect: 0, levelCorrect: 0, answered: false };
  setActiveLevel(0);
  updateHud();
  const level = data.levels[0];
  speak(`${level.name}. ${level.subtitle}.`);
  showQuestion();
}

function showQuestion() {
  showPanel(questionPanel);
  const level = data.levels[state.levelIndex];
  const questions = questionsByLevel[state.levelIndex];
  const question = questions[state.qIndex];
  state.answered = false;
  levelEl.textContent = level.name;
  countEl.textContent = `Question ${state.qIndex + 1} of ${questions.length}`;
  progressEl.style.width = `${((state.qIndex + 1) / questions.length) * 100}%`;
  promptEl.textContent = question.prompt;
  explainEl.hidden = true;
  explainEl.textContent = "";
  nextButton.hidden = true;
  answersEl.innerHTML = "";
  question.options.forEach((option, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "answer";
    button.textContent = option;
    button.addEventListener("click", () => answer(index));
    answersEl.appendChild(button);
  });
  updateHud();
  const first = answersEl.querySelector("button");
  if (first) first.focus({ preventScroll: true });
}

function answer(index) {
  if (state.answered) return;
  state.answered = true;
  const question = questionsByLevel[state.levelIndex][state.qIndex];
  const buttons = Array.from(answersEl.querySelectorAll("button"));
  const correct = index === question.answer;
  buttons.forEach((button, i) => {
    button.disabled = true;
    if (i === question.answer) button.classList.add("correct");
    else if (i === index) button.classList.add("wrong");
  });
  if (correct) {
    state.totalCorrect += 1;
    state.levelCorrect += 1;
    highlightConcept(question.concept, "#86efac");
    speak(`Correct. ${question.explain}`);
  } else {
    highlightConcept(question.concept, "#facc15");
    speak(`Not quite. ${question.explain}`);
  }
  explainEl.textContent = question.explain;
  explainEl.hidden = false;
  nextButton.hidden = false;
  nextButton.textContent = state.qIndex === questionsByLevel[state.levelIndex].length - 1 ? "Finish level →" : "Next question →";
  updateHud();
  nextButton.focus({ preventScroll: true });
}

function nextQuestion() {
  const questions = questionsByLevel[state.levelIndex];
  if (state.qIndex < questions.length - 1) {
    state.qIndex += 1;
    showQuestion();
  } else {
    showLevelPanel();
  }
}

function showLevelPanel() {
  showPanel(levelPanel);
  const level = data.levels[state.levelIndex];
  const questions = questionsByLevel[state.levelIndex];
  levelKicker.textContent = `${level.name} complete`;
  levelTitle.textContent = `${level.name} complete.`;
  levelSummary.textContent = level.summary;
  levelCorrectEl.textContent = `${state.levelCorrect} / ${questions.length}`;
  levelTotalEl.textContent = `${state.totalCorrect} / ${data.questions.length}`;
  continueButton.textContent = state.levelIndex === data.levels.length - 1 ? "See final result →" : `Continue to ${data.levels[state.levelIndex + 1].name} →`;
  speak(level.summary);
  continueButton.focus({ preventScroll: true });
}

function continueGame() {
  if (state.levelIndex === data.levels.length - 1) {
    finishGame();
    return;
  }
  state.levelIndex += 1;
  state.levelCorrect = 0;
  state.qIndex = 0;
  setActiveLevel(state.levelIndex);
  updateHud();
  const level = data.levels[state.levelIndex];
  speak(`${level.name}. ${level.subtitle}.`);
  showQuestion();
}

function finishGame() {
  showPanel(finishPanel);
  nodes.forEach((mesh) => { if (mesh.userData.label) mesh.userData.label.visible = true; });
  best = Math.max(best, state.totalCorrect);
  localStorage.setItem("neural-orbit-best", String(best));
  finalText.textContent = data.final;
  finalScore.textContent = `${state.totalCorrect} / ${data.questions.length}`;
  finalBest.textContent = String(best);
  bestEl.textContent = `Best: ${best} / ${data.questions.length}`;
  speak(data.final);
  restartButton.focus({ preventScroll: true });
}

function setup() {
  questionsByLevel = data.levels.map((level) => data.questions.filter((q) => q.level === level.id));
  bestEl.textContent = best > 0 ? `Best: ${best} / ${data.questions.length}` : "Best: not played yet";
  startButton.addEventListener("click", startGame);
  nextButton.addEventListener("click", nextQuestion);
  continueButton.addEventListener("click", continueGame);
  restartButton.addEventListener("click", startGame);
  muteButtons.forEach((button) => {
    button.addEventListener("click", () => setMuted(!muted));
  });
  setMuted(false);
  initScene();
  buildGraph();
  window.addEventListener("resize", resize);
  if ("ResizeObserver" in window) new ResizeObserver(resize).observe(container);
}

fetch("../data/learning.json")
  .then((response) => {
    if (!response.ok) throw new Error(`learning.json: ${response.status}`);
    return response.json();
  })
  .then((json) => {
    data = json;
    setup();
  })
  .catch((error) => {
    console.error(error);
    startPanel.innerHTML = '<div class="callout">The learning data could not load. Open the <a href="learn.html">beginner guide</a> instead.</div>';
  });
