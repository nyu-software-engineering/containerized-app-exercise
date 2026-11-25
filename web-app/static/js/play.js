// Play page: sends camera frames to the server and plays the chords that come
// back. The next frame is only sent after the last reply arrives, so a slow
// server can't build up a backlog.
import { KEYS, chordFor, prettyName } from "./music.js";
import { INSTRUMENTS, Piano } from "./piano.js";

// must match POSES in machine-learning-client/logic.py
const POSES = [
  { degree: 1, fingers: [0, 1, 0, 0, 0] },
  { degree: 2, fingers: [0, 1, 1, 0, 0] },
  { degree: 3, fingers: [0, 1, 1, 1, 0] },
  { degree: 4, fingers: [0, 1, 1, 1, 1] },
  { degree: 5, fingers: [1, 1, 1, 1, 1] },
  { degree: 6, fingers: [1, 0, 0, 0, 0] },
  { degree: 7, fingers: [1, 1, 0, 0, 0] },
  { degree: 8, fingers: [1, 1, 1, 0, 0] },
];

// which of MediaPipe's 21 hand points connect to each other
const HAND_CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16],
  [13, 17], [17, 18], [18, 19], [19, 20],
  [0, 17],
];
const FINGERTIPS = [4, 8, 12, 16, 20];
const FRAME_WIDTH = 320;

// legend glyph: one rectangle per finger, drawn like a left hand in a mirror
// (pinky on the left, thumb leaning out on the right). folded fingers are short stubs.
const GLYPH_FINGERS = [
  { finger: 4, x: 1, height: 18 },
  { finger: 3, x: 8, height: 24 },
  { finger: 2, x: 15, height: 27 },
  { finger: 1, x: 22, height: 24 },
  { finger: 0, x: 29, height: 13, rotate: 40 },
];

// color grade for the video (only changes what the player sees)
const LOOK = { saturation: 0.9, warmth: -0.2, tint: 0.1, contrast: 1.05 };

const $ = (id) => document.getElementById(id);
const video = $("camera");
const overlay = $("overlay");
const startButton = $("start");
const hud = $("hud");
const legend = $("legend");
const keySelect = $("key");
const scaleSelect = $("scale");
const instrumentSelect = $("instrument");
const volume = $("volume");
const reverb = $("reverb");
const release = $("release");
const bass = $("bass");
const frameCanvas = document.createElement("canvas");

let piano = null;
let stream = null;
let sessionId = null;
let playing = false;
let soundingDegree = null;
let sessionStartedAt = 0;

// ---------- setup

for (const key of KEYS) {
  keySelect.add(new Option(prettyName(key), key));
}
for (const [value, label] of Object.entries(INSTRUMENTS)) {
  instrumentSelect.add(new Option(label, value));
}

startButton.addEventListener("click", () => (playing ? stop() : start()));
$("settings-toggle").addEventListener("click", () => {
  $("settings").hidden = !$("settings").hidden;
});
keySelect.addEventListener("change", renderLegend);
scaleSelect.addEventListener("change", renderLegend);

instrumentSelect.addEventListener("change", () => {
  if (!piano) return;
  piano.setInstrument(instrumentSelect.value);
  soundingDegree = null; // replay the current chord on the new instrument
});
bindSlider(volume, (v) => `${Math.round(v * 100)}%`, (v) => piano.setVolume(v));
bindSlider(reverb, (v) => `${Math.round(v * 100)}%`, (v) => piano.setReverb(v));
bindSlider(release, (v) => `${v.toFixed(1)} s`, (v) => piano.setRelease(v));
bass.addEventListener("change", () => piano && piano.setBass(bass.checked));

applyLook();
renderLegend();

// shows a slider's value next to it and passes changes on to the piano
function bindSlider(input, format, onChange) {
  const output = $(`${input.id}-value`);
  output.value = format(Number(input.value));
  input.addEventListener("input", () => {
    output.value = format(Number(input.value));
    if (piano) onChange(Number(input.value));
  });
}

function applyLook() {
  const { saturation, warmth, tint, contrast } = LOOK;
  // white balance: warmth moves along blue <-> amber, tint along green <-> pink
  const r = 1 + 0.12 * warmth + 0.03 * tint;
  const g = 1 + 0.05 * warmth - 0.1 * tint;
  const b = 1 - 0.14 * warmth + 0.03 * tint;
  $("grade-matrix").setAttribute("values", `${r} 0 0 0 0  0 ${g} 0 0 0  0 0 ${b} 0 0  0 0 0 1 0`);
  video.style.filter = `saturate(${saturation}) contrast(${contrast}) url(#grade)`;
}

function applySound() {
  piano.setInstrument(instrumentSelect.value);
  piano.setVolume(Number(volume.value));
  piano.setReverb(Number(reverb.value));
  piano.setRelease(Number(release.value));
  piano.setBass(bass.checked);
}

function setStatus(text, isError = false) {
  $("status").textContent = text;
  $("status").classList.toggle("error", isError);
}

// ---------- server

async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `${path} failed (${response.status})`);
  return data;
}

// the current camera frame as a base64 JPEG (not mirrored)
function grabFrame() {
  frameCanvas.width = FRAME_WIDTH;
  frameCanvas.height = Math.round((FRAME_WIDTH * video.videoHeight) / video.videoWidth);
  frameCanvas.getContext("2d").drawImage(video, 0, 0, frameCanvas.width, frameCanvas.height);
  return frameCanvas.toDataURL("image/jpeg", 0.7).split(",")[1];
}

// ---------- start / stop

async function start() {
  startButton.disabled = true;
  try {
    setStatus("Loading…");
    await Tone.start();
    if (!piano) piano = await Piano.create();
    applySound();

    stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
    video.srcObject = stream;
    await video.play();

    const data = await postJson("/api/session/start", {
      key: keySelect.value,
      scale: scaleSelect.value,
    });
    sessionId = data.session_id;

    playing = true;
    soundingDegree = null;
    sessionStartedAt = performance.now();
    setPlaying(true);
    setStatus(`Playing in ${prettyName(keySelect.value)} ${scaleSelect.value}. Hold up your left hand.`);
    requestAnimationFrame(tick);
  } catch (err) {
    closeCamera();
    if (err.name === "NotAllowedError") {
      setStatus("Camera permission was blocked. Allow it and press Start again.", true);
    } else {
      setStatus(err.message, true);
    }
  }
  startButton.disabled = false;
}

async function stop(errorMessage) {
  playing = false;
  piano.stop();
  soundingDegree = null;
  closeCamera();
  clearOverlay();
  setPlaying(false);
  renderChord(null);
  highlightLegend(null);

  const seconds = Math.round((performance.now() - sessionStartedAt) / 1000);
  if (errorMessage) {
    setStatus(errorMessage, true);
  } else {
    setStatus(`Session over: ${seconds} s. Press Start to play again.`);
  }
  try {
    await postJson("/api/session/stop", { session_id: sessionId });
  } catch (err) {
    setStatus(`Couldn't save the session: ${err.message}`, true);
  }
  sessionId = null;
}

function closeCamera() {
  if (stream) stream.getTracks().forEach((track) => track.stop());
  stream = null;
  video.srcObject = null;
}

// key and scale stay fixed during a session
function setPlaying(on) {
  keySelect.disabled = on;
  scaleSelect.disabled = on;
  startButton.textContent = on ? "Stop" : "Start";
  startButton.classList.toggle("playing", on);
}

// ---------- main loop

async function tick() {
  if (!playing) return;
  try {
    const result = await postJson("/api/frame", { session_id: sessionId, image: grabFrame() });
    if (!playing) return; // Stop was pressed while this frame was in flight
    updateSound(result);
    drawOverlay(result);
    renderChord(result);
    highlightLegend(result.left.degree);
  } catch (err) {
    if (playing) stop(`Hand tracking stopped: ${err.message}`);
    return;
  }
  requestAnimationFrame(tick);
}

function updateSound(result) {
  const { degree, notes } = result.left;
  if (degree === soundingDegree) return;
  if (degree === null) {
    piano.stop();
  } else {
    piano.playChord(notes);
  }
  soundingDegree = degree;
}

// ---------- drawing

// resizes the canvas to the screen (sharp on retina screens) and clears it
function clearOverlay() {
  const ratio = window.devicePixelRatio || 1;
  overlay.width = overlay.clientWidth * ratio;
  overlay.height = overlay.clientHeight * ratio;
  const ctx = overlay.getContext("2d");
  ctx.scale(ratio, ratio);
  return ctx;
}

function drawOverlay(result) {
  const ctx = clearOverlay();
  const width = overlay.clientWidth;
  const height = overlay.clientHeight;

  // the video is mirrored and cropped to fill the screen (object-fit: cover),
  // so map the points the same way
  const scale = Math.max(width / video.videoWidth, height / video.videoHeight);
  const shownWidth = video.videoWidth * scale;
  const shownHeight = video.videoHeight * scale;
  const offsetX = (width - shownWidth) / 2;
  const offsetY = (height - shownHeight) / 2;

  for (const hand of result.hands || []) {
    const isLeft = hand.label === "Left";
    const color = isLeft ? "#fff" : "rgba(255, 255, 255, 0.35)";
    const points = hand.points.map(([x, y]) => [
      offsetX + (1 - x) * shownWidth,
      offsetY + y * shownHeight,
    ]);

    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (const [a, b] of HAND_CONNECTIONS) {
      ctx.moveTo(points[a][0], points[a][1]);
      ctx.lineTo(points[b][0], points[b][1]);
    }
    ctx.stroke();

    points.forEach(([x, y], i) => {
      if (!FINGERTIPS.includes(i)) ctx.fillRect(x - 1.5, y - 1.5, 3, 3);
    });

    // fingertips: filled square = up, outline = folded
    FINGERTIPS.forEach((i, finger) => {
      const [x, y] = points[i];
      if (isLeft && result.fingers && result.fingers[finger]) {
        ctx.fillRect(x - 4.5, y - 4.5, 9, 9);
      } else {
        ctx.strokeRect(x - 3, y - 3, 6, 6);
      }
    });

    ctx.font = '10px "Helvetica Neue", Helvetica, Arial, sans-serif';
    ctx.letterSpacing = "2px";
    ctx.textAlign = "center";
    const label = isLeft ? "LEFT / CHORDS" : hand.label.toUpperCase();
    ctx.fillText(label, points[0][0], Math.min(points[0][1] + 24, height - 8));
  }
}

function renderChord(result) {
  if (!result || result.left.degree === null) {
    let state = "Idle";
    if (result && !result.hand_found) {
      state = (result.hands || []).length > 0 ? "Use your left hand" : "No hands";
    } else if (result) {
      state = result.left.stable ? "Fist (silent)" : "Waiting for a pose";
    }
    hud.dataset.state = "silent";
    $("chord-name").textContent = "—";
    $("chord-notes").textContent = "";
    $("chord-numeral").textContent = "";
    $("chord-state").textContent = state;
    return;
  }

  const { degree, chord, notes, stable } = result.left;
  hud.dataset.state = stable ? "playing" : "changing";
  $("chord-name").textContent = prettyName(chord);
  $("chord-notes").textContent = notes.map(prettyName).join("  ");
  $("chord-numeral").textContent = chordFor(keySelect.value, scaleSelect.value, degree).numeral;
  $("chord-state").textContent = stable ? `Degree ${degree}` : "Changing";
}

function handGlyph(fingers) {
  const SVG = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("viewBox", "0 0 44 32");
  svg.classList.add("glyph");
  for (const { finger, x, height, rotate } of GLYPH_FINGERS) {
    const up = fingers[finger] === 1;
    const h = up ? height : 6;
    const rect = document.createElementNS(SVG, "rect");
    rect.setAttribute("x", x + 0.5);
    rect.setAttribute("y", 31 - h + 0.5);
    rect.setAttribute("width", 4);
    rect.setAttribute("height", h - 1);
    if (rotate) rect.setAttribute("transform", `rotate(${rotate} ${x} 31)`);
    if (up) rect.classList.add("up");
    svg.append(rect);
  }
  return svg;
}

function renderLegend() {
  const rows = POSES.map(({ degree, fingers }) => {
    const chord = chordFor(keySelect.value, scaleSelect.value, degree);
    return { degree, label: `0${degree}`, fingers, name: prettyName(chord.name), numeral: chord.numeral };
  });
  rows.push({ degree: "fist", label: "--", fingers: [0, 0, 0, 0, 0], name: "Silence", numeral: "" });

  legend.replaceChildren();
  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.dataset.degree = row.degree;
    tr.innerHTML = `<td>${row.label}</td><td></td><td>${row.name} <small>${row.numeral}</small></td>`;
    tr.children[1].append(handGlyph(row.fingers));
    legend.append(tr);
  }
}

function highlightLegend(degree) {
  for (const tr of legend.children) {
    tr.classList.toggle("active", tr.dataset.degree === String(degree));
  }
}
