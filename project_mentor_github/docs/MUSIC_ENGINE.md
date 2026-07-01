# Music Engine

The Music Engine is the first domain engine for Project Mentor.

It powers the AI Piano Teacher prototype and should eventually support many instruments.

## Inputs

Initial:
- MIDI keyboard

Future:
- microphone for acoustic piano
- camera for hand posture
- MusicXML sheet music
- MIDI files
- audio files
- voice questions

## Current Capabilities

- receive live MIDI input
- display pressed keys
- detect common chords
- compare pressed notes to a target chord
- identify missing and extra notes
- provide style-aware critique
- train simple chord progressions

## Future Capabilities

### Chord Intelligence

Support:
- inversions
- slash chords
- 9ths, 11ths, 13ths
- altered dominants
- tritone substitutions
- borrowed chords
- modal interchange
- ambiguous jazz voicings

### Rhythm Engine

Detect:
- early notes
- late notes
- rushing
- dragging
- uneven subdivisions
- inconsistent tempo

### Sheet Music Understanding

Use MusicXML first.

The engine should identify key, meter, measures, phrases, chords, scale patterns, arpeggios, repeated motifs, and difficult sections.

### Musical X-Ray

The long-term dream:

When a learner plays or imports music, the mentor overlays melody, bass line, chord function, tension, resolution, voice leading, scale options, technique requirements, and why the music works emotionally.
