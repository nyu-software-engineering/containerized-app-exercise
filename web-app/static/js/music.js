// Chord names for the legend. The chord that actually plays comes from the
// ML client's music.py -- these MUST stay in sync (check!)

export const KEYS = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];

// semitones above the tonic for each scale degree (natural minor)
const SCALE_STEPS = {
  major: [0, 2, 4, 5, 7, 9, 11],
  minor: [0, 2, 3, 5, 7, 8, 10],
};
const SHARPS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const FLATS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];
const NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII"];

function usesFlats(key, scale) {
  if (key.endsWith("b")) return true;
  if (scale === "major") return key === "F";
  return ["C", "D", "F", "G"].includes(key);
}

// Triad chord calculation for a scale degree (notes 1 to 8)
// The note / tonic sits between F3 and E4 so every key is in the same range 
// as opposed to like C4 -> B4, B4 is too much higher
// this puts C4 to E4, then F3 to B3 so the notes / chords are more in same range
export function chordFor(key, scale, degree) {
  const tonicPc = SHARPS.includes(key) ? SHARPS.indexOf(key) : FLATS.indexOf(key);
  const tonicMidi = (tonicPc >= 5 ? 48 : 60) + tonicPc;
  const steps = SCALE_STEPS[scale];
  const index = (degree - 1) % 7;
  const octave = degree === 8 ? 12 : 0;

  // stack thirds (chord calc): degree, degree + 2, degree + 4
  const offsets = [0, 2, 4].map((k) => steps[(index + k) % 7] + 12 * Math.floor((index + k) / 7));
  const names = usesFlats(key, scale) ? FLATS : SHARPS;
  const notes = offsets.map((offset) => {
    const midi = tonicMidi + offset + octave;
    return names[midi % 12] + (Math.floor(midi / 12) - 1);
  });

  const root = names[(tonicMidi + offsets[0]) % 12];
  const third = offsets[1] - offsets[0];
  const fifth = offsets[2] - offsets[0];
  if (third === 4) return { name: root, numeral: NUMERALS[index], notes };
  if (fifth === 6) return { name: root + "dim", numeral: NUMERALS[index].toLowerCase() + "°", notes };
  return { name: root + "m", numeral: NUMERALS[index].toLowerCase(), notes };
}

// "Eb" -> "E♭", "F#m" -> "F♯m"
export function prettyName(name) {
  return name.replace(/^([A-G])b/, "$1♭").replace(/^([A-G])#/, "$1♯");
}
