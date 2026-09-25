# SC2 Tournament Overlay

HTML/CSS/JS overlays (no Node.js required) for broadcasting **StarCraft II** match stats in **OBS Studio**, built for tournament casting: player names, races, and win/loss record, read directly from the live game state.

## Project contents

| File | Type | Description |
|---|---|---|
| `sc2_proxy.py` | Standalone Python script | CORS proxy run manually (`python sc2_proxy.py`) in a separate console window. Reads the local SC2 API and writes the data so the overlays can consume it. |
| `sc2_proxy_for_obs.py` | OBS script | Same function as `sc2_proxy.py`, but packaged as an **OBS script** (`Tools -> Scripts`). Starts automatically when OBS opens and stops automatically when OBS closes, no separate console needed. Includes a live status panel and a manual "check connection" button. |
| `SC2 Tournament Overlay.html` | Main overlay | OBS browser source showing the current match's player names, race, and series score, styled with a StarCraft II-inspired design and race logos. |
| `SC2 Session Stats Overlay.html` | Secondary overlay | Small, semi-transparent panel meant for a screen corner, showing the running session total: games played, wins, losses, and the breakdown against each race. |
| `style.css` | Stylesheet | Shared CSS with the StarCraft II look (Orbitron/Rajdhani fonts, per-race colors, angular HUD). Used by both HTML overlays. |
| `status.json` | Data file | Automatically generated and updated by whichever proxy is running. The "bridge" between the game and the overlays. Not meant to be edited by hand. |

## What is this for?

SC2 does not allow a web overlay to read match state directly, due to CORS and browser security restrictions. This project solves that with a 3-layer architecture:

```
SC2 (local API :6119/game)
        │
        ▼
   Python proxy (sc2_proxy.py or sc2_proxy_for_obs.py)
        │  writes
        ▼
   status.json (same folder)
        │  read via fetch()
        ▼
HTML overlays (Tournament Overlay / Session Stats Overlay) in OBS
```

- The **proxy** is the only component that talks directly to SC2 (`http://localhost:6119/game`, requires launching the game with `-gamestate 6119 -displaymode 1`).
- The proxy **writes the result to `status.json`** atomically (avoiding reads of a half-written JSON file).
- The **HTML overlays** never contact SC2 directly and never hit CORS issues: they only read `status.json` every 1.5 seconds via `fetch`.
- Both overlays identify "which player is me" by comparing the `MY_PLAYER_NAME` constant (defined at the top of each HTML file's `<script>` block) against the names returned by the API, so it works whether the configured player shows up as `players[0]` or `players[1]`, and even if different team members are casting different matches.

## Requirements

- Windows (or whichever OS runs SC2) with Python 3 installed.
- StarCraft II launched with the flags:
  ```
  -gamestate 6119 -displaymode 1
  ```
- OBS Studio with **Browser Source** support.
- If using `sc2_proxy_for_obs.py`: OBS's Python scripting plugin enabled (`Tools -> Scripts -> Python Settings`, pointing to your Python installation folder).

## Installation

1. Download all 6 files and place them **all in the same folder**:
   ```
   /sc2-overlay/
     ├── sc2_proxy.py
     ├── sc2_proxy_for_obs.py
     ├── SC2 Tournament Overlay.html
     ├── SC2 Session Stats Overlay.html
     ├── style.css
     └── status.json
   ```
2. Choose **one** of the two proxy options (do not run both at once, they share the same port):
   - **Option A — Manual (`sc2_proxy.py`)**: useful for quick testing or for using the overlay outside OBS.
   - **Option B — Automatic (`sc2_proxy_for_obs.py`)**: recommended for broadcasts, integrates with OBS's own lifecycle.
3. Before using either HTML overlay, open the file in a text editor and change the constant at the top of the `<script>` block:
   ```html
   <script>
     const MY_PLAYER_NAME = "Kvzonbr"; // <-- CHANGE THIS to your SC2 username
   </script>
   ```
   It must match exactly (case-sensitive) the name you use in-game.

## Usage

### Option A: manual proxy (`sc2_proxy.py`)

1. Launch SC2 with the flags above and enter a match.
2. Open a console (PowerShell/CMD) in the project folder and run:
   ```
   python sc2_proxy.py
   ```
3. Leave that console open while broadcasting; the proxy will keep polling the SC2 API and updating `status.json`.
4. Add the overlays to OBS as **Browser Sources**, pointing to the local HTML file (see "Adding overlays to OBS" below).

### Option B: automatic proxy inside OBS (`sc2_proxy_for_obs.py`)

1. In OBS: **Tools -> Scripts -> "Python Settings" tab**, and select your Python installation folder.
2. In the same window, Scripts tab, click **"+"** and select `sc2_proxy_for_obs.py`.
3. The proxy starts automatically when the script loads (i.e. as soon as OBS opens with the script already added) and stops automatically when OBS closes.
4. Select the script in the list to see the **status panel** ("Connected to SC2", "Proxy active, no connection to SC2", etc.) and use the **"Check connection now"** button to confirm the connection immediately, without waiting for the next 15-second cycle.

### Adding the overlays to OBS

1. In OBS, add a **Browser Source**.
2. Under "Local file", select `SC2 Tournament Overlay.html` (main scoreboard) and/or `SC2 Session Stats Overlay.html` (session stats).
3. Adjust the source size to fit the design (the Tournament Overlay needs more space; the Session Stats Overlay is meant for a corner, with a transparent background).
4. If you edit the HTML/CSS files afterward, right-click the source and choose **"Refresh cache of current page"** so OBS reloads the changes.

## How each part works

### `SC2 Tournament Overlay.html`
- Shows each player's name and race (with logo) for the current match, plus the running series score.
- The score resets automatically when `MY_PLAYER_NAME` changes or when a new match is detected.
- Detects back-to-back matches against the same opponent using drops in `displayTime` (if it drops more than 3 seconds compared to the last value seen, a new match is assumed).
- Completely ignores data where `isReplay` is `true` (replays are never counted).
- Automatically looks for a `[race].png/jpg/svg` logo in the same folder; if none is found, it falls back to the default design.

### `SC2 Session Stats Overlay.html`
- Compact, semi-transparent panel meant to stay visible in a screen corner throughout a casting session.
- Tracks: games played, wins, losses, and the win/loss breakdown against each race (Terran/Protoss/Zerg).
- Data persists in the OBS browser's `localStorage`, so it survives source reloads.
- Includes a "Reset" button to manually restart the session count.
- Uses the same `MY_PLAYER_NAME` identification logic, replay filtering, and consecutive-match detection as the main overlay.

### `style.css`
- Shared stylesheet: per-race color palette, Orbitron/Rajdhani fonts, API connection indicator, and the overall StarCraft II-inspired "HUD" style.
- Edited in one place, affects both HTML overlays that reference it (`<link rel="stylesheet" href="style.css">`).

### `sc2_proxy.py` / `sc2_proxy_for_obs.py`
- Both do the same thing: query `http://localhost:6119/game` (the local API SC2 exposes when launched with the flags above) and write the result to `status.json` atomically (using a temp file + `os.replace`), preventing the overlays from reading a half-written JSON file.
- `sc2_proxy.py` runs as a standalone script in a console window.
- `sc2_proxy_for_obs.py` runs embedded in OBS as a script (`obspython`), with automatic start/stop tied to OBS's lifecycle and a visible status panel under `Tools -> Scripts`.

### `status.json`
- Automatically generated by whichever proxy is active. Holds the latest reading from the SC2 API, for example:
  ```json
  {"isReplay": false, "displayTime": 187.0, "players": [
    {"id": 1, "name": "Kvzonbr", "type": "user", "race": "Terr", "result": "Undecided"},
    {"id": 2, "name": "A.I. 1 (Very Easy)", "type": "computer", "race": "random", "result": "Undecided"}
  ]}
  ```
- Should not be edited by hand; if deleted, the proxy recreates it on the next cycle.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Overlay shows "No connection" | The proxy isn't running, or SC2 wasn't launched with `-gamestate 6119 -displaymode 1`. Check in a browser that `http://localhost:6119/game` responds. |
| CORS error in the OBS console | Happens if an overlay tries to read the SC2 API directly instead of `status.json`. Always use the proxy -> `status.json` -> overlay flow. |
| Manual proxy closes by itself | Run it from a console (PowerShell/CMD) with `python sc2_proxy.py` and check for syntax errors in the file. |
| HTML/CSS changes don't show up in OBS | Right-click the source -> "Refresh cache of current page". |
| Stats don't update correctly after watching a replay | Make sure you're using the overlay version that ignores `isReplay` and forces new-match detection right after coming back from a replay (included in this delivery). |
| A match played twice in a row against the same opponent gets missed | The overlay uses `displayTime` to detect resets; if the drop is smaller than 3 seconds it might not be detected — report it if it happens consistently. |

## Notes for the team

- Everyone running these overlays on their own machine must **edit `MY_PLAYER_NAME`** in both HTML files so stats get attributed to the correct player.
- Do not run `sc2_proxy.py` and `sc2_proxy_for_obs.py` at the same time: both use port `6120` and will conflict with each other.
- The whole project is **standalone**: no Node.js, no npm, no extra dependencies beyond Python 3 (the standard installation already includes `http.server`, `urllib`, `json`, `threading`, and `os`, all part of the standard library).
