# Project Mentor

**Project Mentor** is an experimental AI learning platform built around one belief:

> Every learner deserves a mentor that adapts to how they think, remembers their progress, encourages curiosity, and helps them become independent.

The first module is an **AI Piano Teacher** that listens through MIDI, shows a live keyboard UI, detects chords, gives style-aware critique, and teaches music theory through practice.

This project starts with music, but the long-term goal is bigger: a reusable learning framework that can eventually support music, trades, languages, art, math, science, and more.

---

## Mission

Build AI mentors that help every person discover what they are capable of learning.

---

## Core Learning Loop

```text
Inspire
↓
Observe
↓
Understand
↓
Adapt
↓
Teach
↓
Practice
↓
Remember
↓
Celebrate
↓
Inspire Again
```

The AI should not simply answer questions. It should build a model of how the learner learns.

---

## First Module: AI Piano Teacher

Current prototype features:

- Live MIDI keyboard input
- Digital piano UI
- Keys light up as you play
- Live chord detection
- Target chord mode
- Green/red note feedback
- Progression trainer
- Style-aware critique for beginner, pop, jazz, blues, and classical modes

See: [`modules/music-piano`](modules/music-piano)

---

## Project Documents

- [`docs/VISION.md`](docs/VISION.md)
- [`docs/MENTOR_MODEL.md`](docs/MENTOR_MODEL.md)
- [`docs/LEARNING_BRAIN.md`](docs/LEARNING_BRAIN.md)
- [`docs/KNOWLEDGE_GRAPH.md`](docs/KNOWLEDGE_GRAPH.md)
- [`docs/MUSIC_ENGINE.md`](docs/MUSIC_ENGINE.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## First Principle

> Every feature must help the learner become more capable without making them feel less capable.

---

## Status

This is early research and prototyping. The first goal is not to build a perfect app. The first goal is to prove the learning loop:

> Can the AI observe what a learner is doing, understand their mistake, and teach the next useful concept in a way that builds confidence?
