gesture piano
left hand holds chords, right hand plays melody

ML client container runs MediaPipe hand tracking on each frame
left hand -- chord combinations choose which chord. for simplicity we just do C major
FIST = nothing playing
Chords: (1 to 8)
1: thumb out
2: thumb index
etc 1 to 5, each time add the next finger
6 to 8 -- subtract a finger from the other end
eg: 6: all fingers except thumb
(this way there are no repeating combos)

RH can be melody
vertical scale
pinch to play, if not pinched then notes aren't played but it automatically holds (this way it doesnt slide / play all the notes as it slides up the scale)
FIST = nothing playing