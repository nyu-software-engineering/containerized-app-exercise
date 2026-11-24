"""Music theory: key + scale + scale degree -> chord name and notes.

The play page has a copy of this in web-app/static/js/music.js for its legend,
so keep the two in sync.
"""

KEYS = ("C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")

# semitones above the tonic for each scale degree (natural minor)
SCALE_STEPS = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
}
SHARPS = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
FLATS = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
NUMERALS = ("I", "II", "III", "IV", "V", "VI", "VII")


def uses_flats(key, scale):
    """Whether to spell notes with flats (Eb) instead of sharps (D#)."""
    if key.endswith("b"):
        return True
    if scale == "major":
        return key == "F"
    return key in ("C", "D", "F", "G")


def chord_for(key, scale, degree):
    """Return {"name", "numeral", "notes"} for a scale degree 1-8.

    Degree 8 is degree 1 an octave up. The tonic sits between F3 and E4 so
    every key is in the same range. Example: chord_for("C", "major", 2) is
    {"name": "Dm", "numeral": "ii", "notes": ["D4", "F4", "A4"]}.
    """
    tonic = SHARPS.index(key) if key in SHARPS else FLATS.index(key)
    tonic_midi = (48 if tonic >= 5 else 60) + tonic
    steps = SCALE_STEPS[scale]
    index = (degree - 1) % 7
    octave = 12 if degree == 8 else 0

    # stack thirds: degree, degree + 2, degree + 4
    offsets = [steps[(index + k) % 7] + 12 * ((index + k) // 7) for k in (0, 2, 4)]
    names = FLATS if uses_flats(key, scale) else SHARPS
    notes = []
    for offset in offsets:
        midi = tonic_midi + offset + octave
        notes.append(f"{names[midi % 12]}{midi // 12 - 1}")

    root = names[(tonic_midi + offsets[0]) % 12]
    if offsets[1] - offsets[0] == 4:  # major third
        return {"name": root, "numeral": NUMERALS[index], "notes": notes}
    if offsets[2] - offsets[0] == 6:  # diminished fifth
        return {
            "name": root + "dim",
            "numeral": NUMERALS[index].lower() + "°",
            "notes": notes,
        }
    return {"name": root + "m", "numeral": NUMERALS[index].lower(), "notes": notes}
