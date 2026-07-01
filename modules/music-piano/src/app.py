"""
Project Mentor - Music Piano MVP

First runnable app module.

Features:
- MIDI keyboard input
- Live digital piano UI
- Chord detection
- Target chord practice
- Green/red feedback
- Simple progression trainer

Run:
    pip install -r requirements.txt
    python src/app.py
"""

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import mido


NOTE_NAMES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_TO_PC = {name: i for i, name in enumerate(NOTE_NAMES_SHARP)}
NOTE_TO_PC.update({"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10})

FLAT_EQUIV = {
    "A#": "Bb",
    "C#": "Db",
    "D#": "Eb",
    "F#": "Gb",
    "G#": "Ab",
}


def midi_to_note_name(note_number: int) -> str:
    octave = (note_number // 12) - 1
    return f"{NOTE_NAMES_SHARP[note_number % 12]}{octave}"


def midi_to_pitch_class(note_number: int) -> int:
    return note_number % 12


def pc_to_name(pc: int, prefer_flats: bool = False) -> str:
    name = NOTE_NAMES_SHARP[pc % 12]
    if prefer_flats and name in FLAT_EQUIV:
        return FLAT_EQUIV[name]
    return name


CHORD_QUALITIES: Dict[str, Tuple[int, ...]] = {
    "": (0, 4, 7),
    "m": (0, 3, 7),
    "dim": (0, 3, 6),
    "aug": (0, 4, 8),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "6": (0, 4, 7, 9),
    "m6": (0, 3, 7, 9),
    "7": (0, 4, 7, 10),
    "maj7": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10),
    "m7b5": (0, 3, 6, 10),
    "dim7": (0, 3, 6, 9),
    "add9": (0, 2, 4, 7),
}

QUALITY_NAMES = {
    "": "major",
    "m": "minor",
    "dim": "diminished",
    "aug": "augmented",
    "sus2": "sus2",
    "sus4": "sus4",
    "6": "major 6",
    "m6": "minor 6",
    "7": "dominant 7",
    "maj7": "major 7",
    "m7": "minor 7",
    "m7b5": "half diminished 7",
    "dim7": "diminished 7",
    "add9": "add9",
}

CHORD_PATTERNS = [(QUALITY_NAMES[suffix], intervals, suffix) for suffix, intervals in CHORD_QUALITIES.items()]

PRESET_PROGRESSIONS = {
    "Jazz ii-V-I in C": ["Dm7", "G7", "Cmaj7"],
    "Pop I-V-vi-IV in C": ["C", "G", "Am", "F"],
    "Blues I-IV-V in C": ["C7", "F7", "G7"],
    "Classical I-IV-V-I in C": ["C", "F", "G", "C"],
}


@dataclass
class ChordResult:
    name: str
    quality: str
    root_pc: Optional[int]
    bass_pc: Optional[int]
    notes: List[str]


@dataclass
class TargetChord:
    name: str
    pcs: Set[int]
    root_pc: int
    quality: str


def parse_chord_name(chord_name: str) -> Optional[TargetChord]:
    chord_name = chord_name.strip()
    if not chord_name:
        return None

    root = None
    suffix = ""

    if len(chord_name) >= 2 and chord_name[:2] in NOTE_TO_PC:
        root = chord_name[:2]
        suffix = chord_name[2:]
    elif chord_name[0] in NOTE_TO_PC:
        root = chord_name[0]
        suffix = chord_name[1:]

    if root is None:
        return None

    suffix = suffix.replace("min", "m").replace("Δ", "maj7")
    if suffix == "M7":
        suffix = "maj7"

    if suffix not in CHORD_QUALITIES:
        return None

    root_pc = NOTE_TO_PC[root]
    pcs = {(root_pc + interval) % 12 for interval in CHORD_QUALITIES[suffix]}
    return TargetChord(chord_name, pcs, root_pc, QUALITY_NAMES[suffix])


def detect_chord(held_notes: Set[int]) -> ChordResult:
    if not held_notes:
        return ChordResult("No chord", "none", None, None, [])

    pcs = sorted({midi_to_pitch_class(n) for n in held_notes})
    bass_pc = midi_to_pitch_class(min(held_notes))
    note_names = [pc_to_name(pc, prefer_flats=True) for pc in pcs]

    if len(pcs) == 1:
        return ChordResult(note_names[0], "single note", pcs[0], bass_pc, note_names)

    pc_set = set(pcs)

    for root in pcs:
        intervals = tuple(sorted(((pc - root) % 12 for pc in pc_set)))
        for quality_name, pattern, suffix in CHORD_PATTERNS:
            if intervals == pattern:
                root_name = pc_to_name(root, prefer_flats=True)
                slash = ""
                if bass_pc != root:
                    slash = f"/{pc_to_name(bass_pc, prefer_flats=True)}"
                return ChordResult(f"{root_name}{suffix}{slash}", quality_name, root, bass_pc, note_names)

    return ChordResult("Unknown / colorful voicing", "unknown", None, bass_pc, note_names)


class MidiListener(threading.Thread):
    def __init__(self, input_name: str, event_queue: queue.Queue):
        super().__init__(daemon=True)
        self.input_name = input_name
        self.event_queue = event_queue
        self.running = True

    def run(self):
        try:
            with mido.open_input(self.input_name) as port:
                while self.running:
                    for msg in port.iter_pending():
                        if msg.type in ("note_on", "note_off"):
                            self.event_queue.put(msg)
                    time.sleep(0.005)
        except Exception as e:
            self.event_queue.put(("error", str(e)))

    def stop(self):
        self.running = False


class PianoKeyboardCanvas(tk.Canvas):
    def __init__(self, master, start_note=48, octaves=4, **kwargs):
        super().__init__(master, height=180, bg="#202124", highlightthickness=0, **kwargs)
        self.start_note = start_note
        self.end_note = start_note + octaves * 12
        self.white_key_width = 42
        self.white_key_height = 150
        self.black_key_width = 26
        self.black_key_height = 95
        self.draw_keyboard(set(), None)

    def is_black(self, midi_note: int) -> bool:
        return midi_note % 12 in {1, 3, 6, 8, 10}

    def white_index(self, midi_note: int) -> int:
        return sum(1 for n in range(self.start_note, midi_note) if not self.is_black(n))

    def note_fill(self, midi_note: int, held_notes: Set[int], target: Optional[TargetChord]) -> str:
        if midi_note not in held_notes:
            return "black" if self.is_black(midi_note) else "white"

        if target is None:
            return "#00bcd4" if self.is_black(midi_note) else "#9be7ff"

        pc = midi_to_pitch_class(midi_note)
        return "#35d06f" if pc in target.pcs else "#ff5c5c"

    def draw_keyboard(self, held_notes: Set[int], target: Optional[TargetChord]):
        self.delete("all")
        white_notes = [n for n in range(self.start_note, self.end_note + 1) if not self.is_black(n)]
        total_width = len(white_notes) * self.white_key_width
        self.config(width=total_width)

        for n in white_notes:
            idx = self.white_index(n)
            x1 = idx * self.white_key_width
            x2 = x1 + self.white_key_width
            self.create_rectangle(x1, 0, x2, self.white_key_height, fill=self.note_fill(n, held_notes, target), outline="black")

            if n % 12 == 0:
                self.create_text((x1 + x2) / 2, self.white_key_height - 15, text=midi_to_note_name(n), fill="black", font=("Arial", 9))

        for n in range(self.start_note, self.end_note + 1):
            if not self.is_black(n):
                continue

            prev_white_idx = self.white_index(n)
            x_center = prev_white_idx * self.white_key_width
            x1 = x_center - self.black_key_width / 2
            x2 = x_center + self.black_key_width / 2
            self.create_rectangle(x1, 0, x2, self.black_key_height, fill=self.note_fill(n, held_notes, target), outline="#333333")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Mentor - AI Piano Teacher MVP")
        self.root.geometry("1050x720")

        self.event_queue: queue.Queue = queue.Queue()
        self.listener: Optional[MidiListener] = None
        self.held_notes: Set[int] = set()
        self.last_chord_name = ""

        self.input_var = tk.StringVar(value="")
        self.target_var = tk.StringVar(value="Cmaj7")
        self.progression_var = tk.StringVar(value="Jazz ii-V-I in C")
        self.progression_index = 0
        self.current_progression: List[str] = PRESET_PROGRESSIONS[self.progression_var.get()]

        self.build_ui()
        self.refresh_inputs()
        self.root.after(20, self.process_midi_events)

    def build_ui(self):
        top = ttk.Frame(self.root, padding=12)
        top.pack(fill="x")

        ttk.Label(top, text="MIDI Input:").pack(side="left")
        self.input_combo = ttk.Combobox(top, textvariable=self.input_var, width=45, state="readonly")
        self.input_combo.pack(side="left", padx=6)

        ttk.Button(top, text="Refresh", command=self.refresh_inputs).pack(side="left", padx=4)
        ttk.Button(top, text="Connect", command=self.connect_midi).pack(side="left", padx=4)
        ttk.Button(top, text="Stop", command=self.stop_midi).pack(side="left", padx=4)

        target_frame = ttk.Frame(self.root, padding=(12, 0, 12, 8))
        target_frame.pack(fill="x")

        ttk.Label(target_frame, text="Target chord:").pack(side="left")
        ttk.Entry(target_frame, textvariable=self.target_var, width=12).pack(side="left", padx=6)
        ttk.Button(target_frame, text="Set Target", command=self.set_manual_target).pack(side="left")

        ttk.Label(target_frame, text="Progression:").pack(side="left", padx=(25, 4))
        self.progression_combo = ttk.Combobox(
            target_frame,
            textvariable=self.progression_var,
            values=list(PRESET_PROGRESSIONS.keys()),
            width=28,
            state="readonly",
        )
        self.progression_combo.pack(side="left", padx=6)
        ttk.Button(target_frame, text="Load Progression", command=self.load_progression).pack(side="left")
        ttk.Button(target_frame, text="Next Chord", command=self.next_progression_chord).pack(side="left", padx=6)

        self.keyboard = PianoKeyboardCanvas(self.root, start_note=48, octaves=4)
        self.keyboard.pack(pady=12)

        info = ttk.Frame(self.root, padding=12)
        info.pack(fill="both", expand=True)

        self.target_label = ttk.Label(info, text="Target: Cmaj7", font=("Arial", 20, "bold"))
        self.target_label.pack(anchor="w")

        self.progression_label = ttk.Label(info, text="Progression: Dm7 → G7 → Cmaj7", font=("Arial", 14))
        self.progression_label.pack(anchor="w", pady=(4, 0))

        self.chord_label = ttk.Label(info, text="Chord: No chord", font=("Arial", 28, "bold"))
        self.chord_label.pack(anchor="w", pady=(10, 0))

        self.notes_label = ttk.Label(info, text="Held notes: none", font=("Arial", 14))
        self.notes_label.pack(anchor="w", pady=(8, 0))

        self.feedback_label = ttk.Label(info, text="Feedback: play the target chord.", font=("Arial", 15))
        self.feedback_label.pack(anchor="w", pady=(8, 0))

        self.log_text = tk.Text(info, height=8, wrap="word", font=("Arial", 12))
        self.log_text.pack(fill="both", expand=True, pady=(12, 0))
        self.write_log("Welcome to Project Mentor Piano MVP.")
        self.write_log("Green keys are target notes. Red keys are outside the target chord.")

    def get_current_target(self) -> Optional[TargetChord]:
        return parse_chord_name(self.target_var.get())

    def refresh_inputs(self):
        inputs = mido.get_input_names()
        self.input_combo["values"] = inputs
        self.input_var.set(inputs[0] if inputs else "")

    def connect_midi(self):
        input_name = self.input_var.get()
        if not input_name:
            messagebox.showerror("No MIDI input", "No MIDI input found. Plug in your keyboard and click Refresh.")
            return

        self.stop_midi()
        self.listener = MidiListener(input_name, self.event_queue)
        self.listener.start()
        self.write_log(f"Connected to: {input_name}")

    def stop_midi(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
            self.write_log("MIDI listener stopped.")

    def set_manual_target(self):
        target = self.get_current_target()
        if not target:
            self.write_log("Target chord not recognized. Try C, Cm, C7, Cmaj7, Dm7, G7, Am, or F.")
            return
        self.target_label.config(text=f"Target: {target.name}")
        self.update_display()
        self.write_log(f"New target: {target.name}. Required notes: {self.format_pcs(target.pcs)}")

    def load_progression(self):
        name = self.progression_var.get()
        self.current_progression = PRESET_PROGRESSIONS.get(name, ["C"])
        self.progression_index = 0
        self.target_var.set(self.current_progression[0])
        self.progression_label.config(text="Progression: " + " → ".join(self.current_progression))
        self.set_manual_target()

    def next_progression_chord(self):
        if not self.current_progression:
            return
        self.progression_index = (self.progression_index + 1) % len(self.current_progression)
        self.target_var.set(self.current_progression[self.progression_index])
        self.set_manual_target()

    def process_midi_events(self):
        updated = False

        while not self.event_queue.empty():
            msg = self.event_queue.get()

            if isinstance(msg, tuple) and msg[0] == "error":
                self.write_log("MIDI error: " + msg[1])
                continue

            if msg.type == "note_on" and msg.velocity > 0:
                self.held_notes.add(msg.note)
                updated = True
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                self.held_notes.discard(msg.note)
                updated = True

        if updated:
            self.update_display()

        self.root.after(20, self.process_midi_events)

    def update_display(self):
        target = self.get_current_target()
        self.keyboard.draw_keyboard(self.held_notes, target)

        chord = detect_chord(self.held_notes)
        self.chord_label.config(text=f"Chord: {chord.name}")

        self.notes_label.config(text="Held notes: " + (" ".join(chord.notes) if chord.notes else "none"))
        self.feedback_label.config(text="Feedback: " + self.get_target_feedback(target))

        if chord.name != self.last_chord_name:
            self.last_chord_name = chord.name
            self.write_log(f"Detected: {chord.name}")

    def get_target_feedback(self, target: Optional[TargetChord]) -> str:
        if target is None:
            return "Set a valid target chord first."

        held_pcs = {midi_to_pitch_class(n) for n in self.held_notes}
        if not held_pcs:
            return f"Play {target.name}: {self.format_pcs(target.pcs)}"

        missing = target.pcs - held_pcs
        extra = held_pcs - target.pcs

        if not missing and not extra:
            return f"Correct. You played {target.name}."

        parts = []
        if missing:
            parts.append("missing " + self.format_pcs(missing))
        if extra:
            parts.append("extra " + self.format_pcs(extra))
        return "; ".join(parts)

    def format_pcs(self, pcs: Set[int]) -> str:
        return " ".join(pc_to_name(pc, prefer_flats=True) for pc in sorted(pcs))

    def write_log(self, text: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {text}\n")
        self.log_text.see("end")


def main():
    root = tk.Tk()
    app = App(root)

    def on_close():
        app.stop_midi()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
