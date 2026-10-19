# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Overview

**TESAIoT Hackathon** is a multi-platform IoT/BLE sensor framework with published reference implementations. The repo houses:

- **Firmware**: PSoC Edge DevKit binary (`hex/`)
- **Extensions**: Bitstream Studio VSIX for VS Code / Cursor (`vsix/`)
- **Reference clients**: Browser BLE (React) and desktop BLE (Python Flet)
- **Web examples**: HTML telemetry demos (WS / MQTT)
- **Teaching labs**: Progressive BLE labs (Python, Browser)

**Key fact:** Futures instances ship with VSIX and HEX binaries (Git LFS). Work is typically on the labs, examples, and client libraries, **not** the firmware or extension itself.

## Project structure

| Folder | Role | Build |
|--------|------|-------|
| [`ble-react/`](#ble-react) | React monorepo: labs UI + BLE packages for publishing | `pnpm` |
| [`ble-flet/`](#ble-flet) | Python Flet desktop app: DevKit viewer (bleak) | `pip` |
| [`web-app/`](#web-app) | Static HTML demos (telemetry via WS / MQTT) | None — served as-is |
| [`hex/`](#hex-and-firmware) | Firmware HEX binaries (Git LFS, read-only) | Maintained externally |
| [`vsix/`](#vsix-and-extension) | Bitstream Studio extension (Git LFS, read-only) | Maintained externally |
| [`flasher/`](#flasher) | Device flasher installers (Git LFS, read-only) | Maintained externally |

## ble-react

A **TypeScript monorepo** for interactive BLE labs + publishable packages. **Status:** EVT-first (interactive tutorial + live BLE packages implemented; npm publish is preparation-only).

**Key docs:**
- [`docs/LABS.md`](ble-react/docs/LABS.md) — Tutorial map, run commands, EVT-first notes, RESET tip
- [`docs/ARCHITECTURE.md`](ble-react/docs/ARCHITECTURE.md) — Layers, packages, naming
- [`docs/WEB_BLUETOOTH_WINDOWS.md`](ble-react/docs/WEB_BLUETOOTH_WINDOWS.md) — Windows Web Bluetooth + Node bridge bring-up

**Layout:**
```
packages/tbs-core              wire / chunk / decode (shared parsing)
packages/tbs-ble-session       goLive + fire-and-forget CFG
apps/labs                      interactive tutorial (chapters 1–6)
apps/labs/src/tutorial         TutorialShell / steps / progress
apps/dashboard                 Connect / Live / Link / Log pages
tools/ble-bridge               Node.js WebSocket bridge to host BLE (Windows workaround)
```

**Critical rule:** `ble-react` must **not** depend on `Bitstream-Studio/extension/` at build time. Reference code lives in `../python-app/shared/` for parity checks only.

### Dev commands

```bash
cd ble-react
pnpm install              # Install all workspaces
pnpm test                 # Run tests in all packages
pnpm typecheck            # TypeScript check all packages
pnpm dev                  # Run labs UI (http://localhost:5174/)
pnpm dev:dashboard        # Run dashboard demo (http://localhost:5175/)
pnpm build                # Build packages + both apps
pnpm bridge:install       # Install Node BLE bridge (first time)
pnpm bridge               # Start WebSocket bridge (Terminal 2, Windows)
```

**Test one package:**
```bash
pnpm --filter @ternion/tbs-core test
```

**Requirements:**
- **Node.js** 20+
- **Package manager:** pnpm 10.11.0 (`packageManager` in root `package.json`)
- **Browser:** System Chrome or Edge (not Cursor's embedded browser; Web Bluetooth needs system APIs)

**Windows + GATT note:** After OS pair (Settings → Bluetooth), use `http://localhost:5174/?ble=bridge` to route through the Node BLE bridge if Web Bluetooth drops GATT mid-stream.

## ble-flet

A **Python Flet desktop app** — DevKit viewer over direct BLE (bleak, no browser relay). Implements **viewer go-live** without `SENSOR_CFG_SET` (firmware defaults drive the stream).

**Key docs:**
- [`docs/ARCHITECTURE.md`](ble-flet/docs/ARCHITECTURE.md) — FSM, BLE data flow
- README has the sensor-node contract matrix (Flet role, firmware role, configurator role)

**Layout:**
```
main.py                   Flet entry (theme, min width)
ui/app.py                 Session controller, routing, Auto FSM
ui/pages/                 Live, Connect, Log, Settings pages
bs2/session.py            Async bleak session (connect_as_viewer, stream heal)
bs2/connection_fsm.py     ConnPhase labels + backoff
ui/charts.py              Ring buffers + line charts
```

### Dev commands

```bash
cd ble-flet
python -m venv .venv
# Windows (cmd): .venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate
python -m pip install -r requirements.txt

# Run with auto venv setup (preferred)
./run.sh                  # macOS / Linux / Git Bash
run.bat                   # Windows

# Or manual:
./.venv/Scripts/python.exe main.py        # Windows
./.venv/bin/python main.py                # macOS / Linux

# Hot reload (after venv ready)
./.venv/Scripts/python.exe -m flet run main.py

# Verify EVT rate (no UI — check cadence vs SENSOR_CFG)
./.venv/Scripts/python.exe scripts/verify_firmware_evt_rate.py
```

**Requirements:**
- **Python** 3.10+
- **Dependencies:** `flet>=0.27.0,<0.86`, `bleak>=0.22.0`
- **Firmware:** BLE module profile enabled + reboot (one-time)

**Auto UX:** Launch → hunt `TESAIoT-*` → connect → stream from firmware `SENSOR_CFG` defaults → **Live** page. Same sequence on reconnect (no `SENSOR_CFG_SET`).

## web-app

Static HTML demos with live sensor data during Bitstream Studio telemetry. No build step — served as-is via VS Code / Cursor's **Serve Web App Folder over HTTP** command (requires Studio telemetry running + MQTT broker for ex09–ex15).

**Examples:**
- ex01–ex05: Single sensors (SHT40 temperature, DPS368 pressure, BMM350 compass, BMI270 IMU, horizon)
- ex06: Dashboard (all six sensors)
- ex07: Catalog browser
- ex08: Connection status + stale data demo
- ex09–ex15: MQTT subscribers / publishers / wildcards
- ex16–ex17: ADC pots / switch inputs

No source code to modify — drop new `.html` files here to add examples.

## hex and firmware

Read-only Git LFS binaries: `tesaiot-bitstream-<version>.hex`. Flash before hardware labs.

**Note:** In git status, many files show as deleted. This is expected when LFS pointers are tracked but binaries are not checked out locally. Run `git lfs pull` to fetch binaries if needed.

See [`hex/README.md`](hex/README.md) for flash instructions and firmware manifest.

## vsix and extension

Read-only Git LFS: Bitstream Studio extension. Install via **Extensions → Install from VSIX** → select `bitstream-studio-<version>.vsix` (current: 0.1.14).

**Rule:** Do **not** modify the VSIX or depend on it at build time in `ble-react`.

## flasher

Read-only Git LFS: Desktop installers for TESAIoT Flasher (Windows .exe, macOS .dmg, Linux AppImage).

## Firmware prerequisites

Before running BLE labs (**ble-react**, **ble-flet**, **python-app**):

1. Flash HEX from `hex/` using **TESAIoT Flasher** or **ModusToolbox**.
2. One-time: Enable **BLE module profile** bit `0x08` in Bitstream Studio → Sensor settings → reboot (UART step).
3. Disconnect other BLE centrals (nRF Connect, etc.).pnpm
4. After connect timeout or unplug, press **RESET** until TFT turns soft-blue.

## Teaching path (EVT-first)

Canonical BLE flow (mirrors `python-app` labs):

1. **Scan & connect GATT**
2. **Start notifications on `BS_TX`** (CCCD arms `TX_EVT` on firmware)
3. **Decode `EVT_SENSOR`** frames

PING / POLICY operations are **advanced / optional**, not required for early-lab acceptance.

## Key design patterns

**Session go-live:** Both `ble-react` and `ble-flet` implement **viewer go-live** — no `SENSOR_CFG_SET` required. Firmware boots with default measurement rates; the client opens the EVT pipe and streams immediately. This is distinct from **configurator** workflows (Bitstream Studio labs) which may set rates before streaming.

**Wire compatibility:** `ble-react` packages and `ble-flet` share wire logic from `../python-app/shared/` (reference for parity). They do **not** import from the extension at build time.

**EVT-first:** Labs prioritize observation (EVT decode) before configuration (CFG set). PING and POLICY are supporting operations, not required for the critical path.

## Common commands

### Testing & CI

```bash
# All packages
cd ble-react
pnpm test
pnpm typecheck

# Single package
pnpm --filter @ternion/tbs-core test

# Python (ble-flet)
cd ble-flet
python -m pytest               # If tests exist
python scripts/verify_firmware_evt_rate.py
```

### Development

```bash
# React labs
cd ble-react
pnpm dev              # Labs UI on :5174
pnpm dev:dashboard    # Dashboard on :5175

# Python app
cd ble-flet
./run.sh              # macOS / Linux
run.bat               # Windows
./.venv/Scripts/python.exe -m flet run main.py  # Hot reload

# Web examples (served via VS Code command)
# Command Palette → Serve Web App Folder over HTTP → web-app
```

### Debugging

**ble-flet logs:**
```bash
./.venv/Scripts/python.exe scripts/verify_firmware_evt_rate.py --duration 45
```

**ble-react diagnostics:**
- Dev tools: browser DevTools (F12)
- TypeScript errors: `pnpm typecheck`
- `/diag` page in labs UI: run all 1→6 checks

## Versioning notes

- **VSIX:** `0.1.14` (current)
- **Firmware HEX:** `0.1.12` (paired with VSIX; newer HEX may lag VSIX)
- **Monorepo packages:** `@ternion/tbs-*` in `ble-react/packages/` (use `version` in each `package.json`)
- **Publish status:** Preparation-only (not yet on npm)

Prefer **matching VSIX and firmware versions**. When in doubt, use the **`latest`** entry in the firmware manifest (`hex/firmware-manifest.json`).

## Windows-specific notes

1. **Web Bluetooth GATT drops:** After connecting, if GATT disconnects mid-stream, pair the board in **Settings → Bluetooth** first. Then use the Node BLE bridge: `pnpm bridge` (Terminal 1) + `http://localhost:5174/?ble=bridge` (Terminal 2).
2. **Board not visible in flasher:** Install **KitProg3 driver** (bundled with ModusToolbox or TESAIoT Flasher).
3. **Python venv:** Use `run.bat` or `.venv\Scripts\python.exe` directly (avoids Git Bash `python` alias issues).

## Repository status

- **Git LFS:** Tracks VSIX, HEX, flasher installers (read-only; do not edit).
- **Main branch:** Default; merges go here.
- **Handoff artifacts:** VSIX and HEX are published for each release; see recent commits.

## External references

- **Canonical GATT / firmware details:** `extension/src/bitstream2/docs/BLE_BS2.md` (in Bitstream Studio repo; not in this repo)
- **Bleak examples:** `packages/bitstream-ble-client/examples/` (reference; not in this repo)
