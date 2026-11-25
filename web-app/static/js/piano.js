// Plays chords with Tone.js (loaded by the page). Session replay can reuse this.
// piano samples, every few notes; Tone.Sampler fills in the ones between
// sound settings slightly inspired by strudel 
const SAMPLE_NOTES = [
  "A1", "C2", "D#2", "F#2", "A2", "C3", "D#3", "F#3", "A3", "C4", "D#4",
  "F#4", "A4", "C5", "D#5", "F#5", "A5", "C6", "D#6", "F#6", "A6", "C7",
];
const SAMPLE_URLS = {};
for (const note of SAMPLE_NOTES) {
  SAMPLE_URLS[note] = note.replace("#", "s") + ".mp3"; // D#2 -> Ds2.mp3
}

export const INSTRUMENTS = {
  piano: "grand piano",
  soft: "soft synth",
  keys: "electric keys",
};

export class Piano {
  // call after Tone.start(); waits for the piano samples to load
  static async create() {
    const volume = new Tone.Volume(-6).toDestination();
    const reverb = new Tone.Reverb({ decay: 3, wet: 0.25 }).connect(volume);
    const voices = {
      piano: new Tone.Sampler({
        urls: SAMPLE_URLS,
        baseUrl: "https://tonejs.github.io/audio/salamander/",
        release: 1.2,
      }).connect(reverb),
      soft: new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: "triangle" },
        envelope: { attack: 0.02, decay: 0.4, sustain: 0.5, release: 1.2 },
      }).connect(reverb),
      keys: new Tone.PolySynth(Tone.FMSynth, {
        harmonicity: 3,
        modulationIndex: 2,
        envelope: { attack: 0.005, decay: 1.2, sustain: 0.2, release: 1.2 },
      }).connect(reverb),
    };
    await Promise.all([Tone.loaded(), reverb.ready]);
    return new Piano(voices, volume, reverb);
  }

  constructor(voices, volume, reverb) {
    this.voices = voices;
    this.volume = volume;
    this.reverb = reverb;
    this.current = "piano";
    this.held = [];
    this.bass = true;
  }

  setInstrument(name) {
    this.stop();
    this.current = name;
  }

  setVolume(level) {
    this.volume.volume.value = Tone.gainToDb(level);
  }

  setReverb(wet) {
    this.reverb.wet.value = wet;
  }

  setRelease(seconds) {
    this.voices.piano.release = seconds;
    this.voices.soft.set({ envelope: { release: seconds } });
    this.voices.keys.set({ envelope: { release: seconds } });
  }

  setBass(on) {
    this.bass = on;
  }

  // stops the old chord and plays the new one; notes are root first, e.g. ["E4", "G4", "B4"]
  playChord(notes) {
    this.stop();
    const bassNote = Tone.Frequency(notes[0]).transpose(-12).toNote();
    this.held = this.bass ? [bassNote, ...notes] : notes;
    this.voices[this.current].triggerAttack(this.held, Tone.now(), 0.7);
  }

  stop() {
    if (this.held.length > 0) {
      this.voices[this.current].triggerRelease(this.held, Tone.now());
    }
    this.held = [];
  }
}
