const button = document.querySelector("#record");
const icon = document.querySelector("#record-icon");
const label = document.querySelector("#record-label");
const statusMessage = document.querySelector("#status");
const playback = document.querySelector("#playback");

let recorder;
let stream;
let playbackUrl;
let pageActive = true;
let pageVersion = 0;

function releaseMicrophone() {
  stream?.getTracks().forEach((track) => track.stop());
  stream = undefined;
}

function resetButton() {
  delete button.dataset.recording;
  icon.textContent = "🎙";
  label.textContent = "Start recording";
  button.disabled = false;
}

button.addEventListener("click", async () => {
  if (recorder?.state === "recording") {
    button.disabled = true;
    recorder.stop();
    releaseMicrophone();
    return;
  }

  button.disabled = true;
  statusMessage.textContent = "Waiting for microphone permission…";
  const requestVersion = pageVersion;

  try {
    const microphone = await navigator.mediaDevices.getUserMedia({ audio: true });
    if (requestVersion !== pageVersion) {
      microphone.getTracks().forEach((track) => track.stop());
      return;
    }
    stream = microphone;

    const chunks = [];
    const recording = new MediaRecorder(stream);
    recorder = recording;

    recording.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) chunks.push(event.data);
    });

    recording.addEventListener("error", () => {
      if (!pageActive || recorder !== recording) return;
      recorder = undefined;
      releaseMicrophone();
      resetButton();
      statusMessage.textContent = "Recording failed. Try again.";
    }, { once: true });

    recording.addEventListener("stop", () => {
      if (!pageActive || recorder !== recording) return;
      recorder = undefined;
      releaseMicrophone();
      resetButton();

      if (chunks.length === 0) {
        statusMessage.textContent = "No audio was captured. Try recording again.";
        return;
      }

      if (playbackUrl) URL.revokeObjectURL(playbackUrl);
      playbackUrl = URL.createObjectURL(new Blob(chunks, {
        type: recording.mimeType || chunks[0].type,
      }));
      playback.src = playbackUrl;
      playback.hidden = false;
      statusMessage.textContent = "Recording ready to play.";
    }, { once: true });

    recording.start();
    playback.pause();
    button.dataset.recording = "";
    icon.textContent = "■";
    label.textContent = "Stop recording";
    statusMessage.textContent = "Recording…";
    button.disabled = false;
  } catch (error) {
    if (requestVersion !== pageVersion) return;
    recorder = undefined;
    releaseMicrophone();
    resetButton();
    statusMessage.textContent = error.name === "NotAllowedError"
      ? "Allow microphone access in your browser and try again."
      : "Could not start recording. Check your microphone and try again.";
  }
});

window.addEventListener("pagehide", () => {
  pageActive = false;
  pageVersion += 1;
  if (recorder?.state === "recording") recorder.stop();
  recorder = undefined;
  releaseMicrophone();

  if (playbackUrl) {
    playback.removeAttribute("src");
    playback.load();
    playback.hidden = true;
    URL.revokeObjectURL(playbackUrl);
    playbackUrl = undefined;
  }
});

window.addEventListener("pageshow", (event) => {
  pageActive = true;
  if (event.persisted && navigator.mediaDevices?.getUserMedia && window.MediaRecorder) {
    resetButton();
    statusMessage.textContent = "Record audio from your microphone.";
  }
});

if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
  button.disabled = true;
  statusMessage.textContent = "Recording requires a supported browser on HTTPS or localhost.";
}
