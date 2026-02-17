# AirController

Real-time hand gesture engine that converts natural human hand motion into computer input for games, design software, and machine-control scenarios.

## Goal
Build a dependable system that can:
- Track **both hands** in real time.
- Detect hand landmarks and gestures.
- Measure motion signals per hand:
  - position
  - depth
  - speed
  - acceleration
- Map gestures/motion to input actions:
  - mouse
  - keyboard/hotkeys
  - scroll
  - macros / control commands
- Support profile-based control:
  - Gaming (left hand movement, right hand combat/actions)
  - Design tools (Blender/Photoshop style workflows)
  - Machine/mechanics control (with safety constraints)
- Evolve toward sign language understanding.

## Current Status
- Prototype exists with webcam tracking and basic gesture-to-input mapping.
- Next stage is refactoring into a scalable multi-module engine.

## High-Level Plan

## Phase 0 - Foundation
- Stabilize camera + tracking loop.
- Ensure clean exits, errors, and frame timing.
- Baseline performance and latency measurements.

## Phase 1 - Core Two-Hand Motion Engine
- Track left and right hands with stable IDs.
- Build per-hand state stream:
  - `x, y, z`
  - velocity
  - acceleration
- Add smoothing and jitter reduction.

## Phase 2 - Gesture Recognition
- Static gestures (pinch, open palm, fist, etc.).
- Dynamic gestures (swipes, push/pull, rotation).
- Bi-manual gestures (left/right combined logic).
- Confidence scoring + debounce/cooldowns.

## Phase 3 - Input Translation Layer
- Configurable mapping:
  - gesture -> action
  - motion speed -> action speed (slow/fast rotation behavior)
  - depth -> intensity/zoom/trigger parameters
- Add profile system:
  - `game`
  - `design`
  - `machine`

## Phase 4 - Domain Adapters
- Game controls: split left/right hand responsibilities.
- Design controls: one hand for tool action, one for modifiers.
- Machine controls: safe-zone checks, rate limits, confirmation gestures, emergency stop.

## Phase 5 - Sign Language Track
- Build separate temporal recognition pipeline for sign language.
- Start with limited vocabulary, then scale.
- Use labeled datasets and sentence-level sequence modeling.

## Phase 6 - Hardening and Release
- Testing matrix across lighting/background/hardware conditions.
- Reliability metrics (false trigger rate, recovery time, latency).
- Packaging, docs, and calibration wizard.

## Architecture (Target)
```text
Camera -> Hand Tracker -> Feature Extractor -> Gesture Recognizer
       -> Debounce/State Machine -> Action Mapper -> Input Dispatcher
       -> Overlay UI + Logger + Profile Manager
```

## Repository Roadmap (Planned Structure)
```text
AirController/
  main.py
  requirements.txt
  config/
  engine/
  ui/
  tests/
  docs/
```

## Immediate Next Steps
1. Refactor `main.py` into `engine/` modules.
2. Add config-driven gesture and action mapping files.
3. Implement robust two-hand motion state API.
4. Add profile switching for game/design/machine modes.
5. Add logging + replay for tuning thresholds.

## Notes
- For accurate depth and motion dynamics, a depth camera is strongly recommended.
- Machine/mechanical control must include a strict safety layer before deployment.

## Browser + YouTube Control Profile
- Default runtime now loads: `config/browser_youtube_profile.json`
- You can edit this file to rebind any gesture/action and cooldown.

### Included gesture bindings
- `LEFT SWIPE_UP` -> open YouTube video URL
- `LEFT TWO_UP` -> YouTube play/pause (`k`)
- `LEFT TWO_DOWN` -> YouTube fullscreen (`f`)
- `RIGHT PUSH` -> YouTube seek forward (`l`)
- `RIGHT PULL` -> YouTube seek backward (`j`)
- `RIGHT TWO_UP` -> volume up (`up`)
- `RIGHT TWO_DOWN` -> volume down (`down`)
- `RIGHT SWIPE_LEFT` -> browser back
- `RIGHT SWIPE_RIGHT` -> browser forward
- `LEFT SWIPE_DOWN` -> browser refresh
- `RIGHT PINCH` -> left click
- `LEFT PINCH` -> right click

### Change the video to play
Edit:
- `config/browser_youtube_profile.json`

Update action:
- `actions.open_youtube_video.url`

Then run:
- `.\venv\Scripts\python.exe .\main.py`
