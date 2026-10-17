# Little Jimmy games: developer hand-off

This repo holds two browser games for phones, built with Claude: **Pocket Soccer** and **Tower Defence**.
This guide is for whoever (and whichever Claude) picks them up next. Give your Claude this file first.

- Pocket Soccer: `soccer.html` (live at https://keithharro-dot.github.io/Little-Jimmy/soccer.html)
- Tower Defence: `tower-defence.html` (live at https://keithharro-dot.github.io/Little-Jimmy/tower-defence.html)
- Theme music: `music/dikshifter-the-2nd-take.mp3` and its cover `music/dikshifter-cover.jpg`. The track was written by the repo owner, who shared it freely for these games.
- Tests: `tests/smoke.mjs`, plus the stand-ins it uses (`tests/mockpeer.js`, `tests/qrstub.js`)
- `index.html` and `CLAUDE.md`'s main sections are about a **separate trading app**, unrelated to the games.

## Getting started

1. **Get the code.** Ask the owner (keithharro-dot) to add you as a collaborator (see **Working together** below), then clone: `git clone https://github.com/keithharro-dot/Little-Jimmy`
2. **Run it.** No build step: each game is one self-contained HTML file.
   - Serve the folder: `python3 -m http.server 8000`, then open `http://localhost:8000/soccer.html`.
   - Multiplayer and the theme music need `http(s)://`; opening the file directly doesn't work.
3. **Publish it.** GitHub Pages serves the `main` branch, so pushing to `main` updates the live games within a minute or two.
   - **If you fork:** switch on Pages for your fork (Settings → Pages → Deploy from branch → `main`), and change the `HOME` constant near the top of each game's script to your own Pages URL. Invite links and QR codes are built from `HOME`.
4. **Test it.** `npm i -D playwright && npx playwright install chromium`, then `node tests/smoke.mjs`.
   - It plays both games headlessly, including a two-phone Pocket Soccer match, and should end with "All checks passed".

## How both games are built

- **One file each:** CSS, HTML, then one `<script>` with everything else. There's no framework and no bundler. The only external scripts are loaded from CDNs:
  - PeerJS 1.5.4 (unpkg) for phone-to-phone play
  - qrcodejs 1.0.0 (cdnjs) for QR codes
  - Three.js 0.147.0 (jsDelivr), loaded only when 3D graphics is switched on
  - Google Fonts (Cinzel) for Pocket Soccer's steampunk lettering
- **Host-authoritative multiplayer:**
  - The host's phone runs the whole simulation (`step(g, dt)`) and sends a snapshot (`snap(g)`) to guests about 15–30 times a second.
  - Guests only draw what they receive and send their input back (soccer: `{t:'in'}` targets; tower defence: `{t:'cmd'}` commands).
  - Never put game logic on the guest side.
- **Rendering is separate from the simulation.** Each frame, `frame()` gets a view (a snapshot or an interpolated guest view) and draws it. Both games have two renderers:
  - **2D canvas:** the original look.
  - **3D (Three.js):** `G3` holds its state, `render3D(view)` draws the scene, and `overlay3D(view)` draws labels, health bars and pop-up text on the 2D canvas on top.
  - In 3D, screen↔world conversion goes through the camera (`project3D`/`unproject3D` in soccer, `project3`/`tileAt3D` in tower defence). Touch input, controllers and labels all work in both modes.
- **3D safeguards:**
  - Three.js loads on demand (`load3D()`).
  - The game falls back to 2D if WebGL or the download fails.
  - Quality steps down automatically (glow off, then shadows off) if the frame rate drops below about 30.
  - The menu has a "3D graphics / Classic 2D" switch.
  - Version 0.147 is deliberate: it is the last one that ships plain-script `examples/js` files (glow/bloom, RoomEnvironment) usable without a bundler.
  - Colour uses sRGB (`ColorManagement.legacyMode = false`, sRGB textures, and a `GammaCorrectionShader` pass after bloom). Without that, scenes look washed out.
- **The simulation catches up after slow frames:** it runs in small fixed-size steps (see `runSim` / `startGame`), so a phone busy drawing 3D doesn't play in slow motion.
- **Theme music (`THEME`, `themeTo(vol)`):**
  - One looping `<audio>` element, routed through Web Audio so it can fade. iPhones ignore `audio.volume`.
  - It starts on the first tap, because browsers block sound before that.
- **Inside the Claude app**, a copy of each game runs with a flag (`window.PS_EMBEDDED` / `window.TD_EMBEDDED`) that hides features needing a network. Those copies belong to the owner's Claude account; you'll publish your own if you want one.

## Pocket Soccer (`soccer.html`)

Finger soccer for 1–16 players, phones first. Each player is a square block with your face (photo or cartoon) on top. You drag your players with your finger.

- **Pitch and physics:**
  - `F` holds the sizes (pitch 100 × 160 units).
  - Players are square "Pong paddles": hitting the ball off-centre angles it, which makes aiming easier.
  - Corners are cut off so the ball can't wedge, and there's a throw-in after 2.5 s stuck by a wall.
  - Goals widen slightly for 6–8-a-side (`goalWidth`).
- **Teams:**
  - One outfield player per person on the bigger team (`teamSize`, `OUTFIELD` formations), plus a keeper per side.
  - The computer plays the keeper until a teammate drags it, and whoever grabbed it last controls it (`applyInput`, `grab`).
  - Empty spots are computer players (`aiTarget`).
- **Joining is in-person only:**
  - The host shows a QR code whose pass changes every 30 s (`rotateQR`). The previous pass stays valid as grace.
  - A guest's first message must be `{t:'knock', token}`.
  - PeerJS runs with **no STUN/TURN** (`PEER_OPTS`), and `sameNetwork()` rejects relayed connections. Players must be on the same Wi-Fi or the host's hotspot. The internet is only used briefly for the PeerJS hello.
  - Some school and guest Wi-Fi networks block phones talking to each other; the hotspot is the workaround.
- **Chaos power-ups** (`POWERS`; on by default, with a "Normal soccer" switch):
  - Each goal powers up the team that let it in; a team 2+ goals behind gets two powers. Powers stack.
  - The ladder: turbo boots, banana peels, human cannon, tennis rackets, ghost curse (10 s, every 40 s), freeze ray, magnet boots, brick wall, homing rocket ball, nuclear ball.
  - All trigger automatically: on touch, or on a timer. `powerTouch` and `powerStep` hold the logic.
  - Balance notes: power shots lose their boost when they hit a player (otherwise rebounds fly back at rocket speed), and the cannon is tuned via `CANNON = [speed, cooldown]`.
- **Boss round** (`startBoss`): in the last 45 s, or at match point in "First to 5", each team's champion (`pickChamp`) becomes a 2.2× giant named with its owner's boss name (profile field, or `BOSS_NAMES`).
- **Lightsaber duel** (`startDuel`, `duelStep`): a timed match that ends level goes to sudden death.
  - Each blade points the way the player moves, and only cuts when swung.
  - 3 hits wins the match. After 60 s, whoever has more health wins.
- **Records ("Hall of Fame")** (`RECS` in localStorage `ps_records`):
  - The device running the match records it and sends `{t:'result'}` to guests and TVs. There's no server, so each device keeps its own table.
  - Names are the identity: a renamed player gets a new row.
- **TV screen mode:** any browser (Xbox Edge, a PC on HDMI, a smart TV) taps "TV screen" and shows a 4-letter code. The host taps "Add a TV" and types it. The TV is added to `conns` as `tv-XXXX` and receives everything guests receive, but never plays.
- **Big screens and controllers:**
  - Landscape screens show the pitch sideways (`rot`).
  - Game controllers work through `pollPads()`: left stick moves your player nearest the ball, right stick moves your keeper.
  - Computers and consoles can host and practise, but can't join a match, since joining means scanning a QR code with a camera.
- **Steampunk look:** CSS variables in `:root` (brass, copper, rivets, Cinzel fonts); the 2D canvas uses `drawPitch`/`gear`, and the 3D scene is built in `setup3D`.
- **Saved on the phone:** `ps_profile` (name, faces, boss name), `ps_chaos`, `ps_gfx`, `ps_music`, `ps_records`.

## Tower Defence (`tower-defence.html`)

Two players: one sends zombies, one builds towers. Board: 15 × 9 tiles (`COLS`, `ROWS`).

- **Maps** (`MAPS`: Graveyard, Frozen, Desert): road waypoints, colours and scenery.
- **Enemies** (`ENEMIES`):
  - Zombies, speedy, phantom (hidden; only 📡 towers see it), bats (fly straight), riot (shield), medic (heals), brute (armour).
  - Bosses: Eradicator, MK II (rages at half health) and the Void (mind control, Voidlings, stomp), plus minions (Avatars, Voidlings).
- **Towers:** design your own (`stats`, `cleanSpec`) or use the `PRESETS`. Levels 1–4 change the soldier's uniform colour (`LEVEL_UNIFORM`). Reviver and DJ are support towers.
- **Waves** (`WAVES = 50`): an Eradicator on wave 20, an MK II on 40, the Void on 50. The zombie sender's economy is in `ECO`.
- **Eradicator abilities** (the `E.boss` branch of `step`):
  - Rocket bursts (stun and crack), Avatar calls, and a laser sweep through the busiest group of towers.
  - The MK II rages at half health and rains missiles while raging.
  - Both melt down when destroyed.
  - `stunTower(g, t, secs, crack)`: only rocket bursts and Void stomps crack towers (3 cracks destroys one). Lasers, missiles and meltdowns just knock towers out.
- **3D Eradicators** (`mechTpl`): walking mechs with named parts (`hip±1`, `knee±1`, `torso`, `gun-1`, plus `gun1` on MK II or the `fist` gauntlet on MK I, `reactor`, `core`) that `render3D` animates. MK II is its own model, `mk2Tpl`: a hunched olive siege walker with four spinning rocket pods (`gun±1` forearms, `gun±2` shoulders), a missile box, and one red eye as its `core`; `mk2` in `drawUnit` is its 2D version. The look: gunmetal armour with white triangle emblems, a black faceplate in a glowing frame with lava cracks, horns, shoulder pauldrons carrying ring-sight rifles, brass arm cannons, white-striped boots and a jetpack that spits flame. The 2D fallback (`mech` in `drawUnit`) draws the same design. They're drawn 1.5× size. `launchMissile`/`stepMissiles` fly missiles for rocket bursts and missile rain.
- **Close-up camera** (`CU`, `closeup()`, `closeupCam()`), 3D only:
  - 🔍 turns it on. Tap a character to follow it, drag to orbit, pinch or scroll to zoom.
  - An info card shows health and abilities. Taps don't build while it's on.
  - The camera glides between the board view and the close-up (`G3.camPos`/`G3.camLook`).
  - The Eradicator models are original block-built mechs in a Tower Defense X–like style, not copies of TDX's models. The current design is inspired by the TDX Eradicator, made meaner.
- **In-game layout:** full screen, with no page scrolling. The board is always the biggest 15:9 box that fits (`resize`). The CSS at the end of the `<style>` block picks one of three layouts by screen shape:
  - Wide (phones sideways): side columns, towers left and zombies right; one role puts its column on the right.
  - Landscape and at least 600 px tall (tablets, laptops, TVs): a bottom strip of buttons.
  - Upright: a scrolling tray under the board.
  - Upgrade/Sell (`#selInfo`) and the boss bar float over the board.
  - ⛶ uses the Fullscreen API where it exists (Android, iPad) and locks the screen sideways; starting a game on a touch device asks for full screen automatically. iPhone Safari can't go full screen, so the button tells you to use Add to Home Screen.
- **Multiplayer:** PeerJS with its default servers, so it works over the internet. Join by invite link, 4-letter code or QR code.
- **Music:**
  - The theme plays on menus and through battles. The bosses keep their built-in synthesised metal themes (`TRACKS`, `startMusic`), and players can pick their own boss songs from their phone (IndexedDB `tower-defence`).
  - If the theme file can't load, the old synth battle track plays instead.
- **Saved on the phone:** `tc_designs`, `tc_map`, `tc_mute`, `tc_gfx`.

## Testing tips (learned the hard way)

- **Two-phone play in one browser:** use one Playwright browser context with `tests/mockpeer.js` routed in place of PeerJS. Pages in the same context talk over a BroadcastChannel. `tests/qrstub.js` makes the QR element contain its link as text.
- **Use `hasTouch: true`** in Playwright contexts: the games are built for touch.
- **Headless 3D is slow:** headless Chromium renders 3D in software, so it shows correctness but not real phone speed.
  - To test 3D, serve Three.js locally (`npm pack three@0.147.0`) and route `cdn.jsdelivr.net/npm/three@0.147.0/**` to it.
  - Set `G3.ft = -1e9` so the automatic quality drop doesn't kick in during the test.
- **Synthetic pointer events can throw:** they make `setPointerCapture` throw "No active pointer", which is harmless in tests. Check the movement target rather than the position.
- **Balance work:** simulate many matches in-page with `newMatch` + `step` and computer players (set `w.ctl = null`). Look at averages over 15+ matches: single matches are very noisy.
- **Things that don't work inside the Claude app:** `alert`, `confirm` and `prompt`. The games use tap-twice confirmations instead, and the host-only nickname `prompt()` only runs on the website.

## Not yet verified on real devices

- Real phone-to-phone WebRTC on a home Wi-Fi; test environments block it, so it has only been tested with the stand-in.
- 3D speed on older phones, especially late Tower Defence waves.
- Xbox Edge: WebRTC, and whether the controller drives the game or a mouse cursor.
- Smart-TV browsers for TV mode. An Xbox or a laptop on HDMI is the safe bet.

## Ideas parked for later

- "MEGA" powers after the nuke, so the chaos ladder keeps escalating.
- A clone-army power (extra players mid-match). It needs match info re-sent to guests, since the widget list is currently fixed at kick-off.
- Records shared between phones (merge tables when players join).
- 3D: proper character models (free CC0 packs such as Kenney or Quaternius) instead of block-built ones.

## Working together (Keith and Leo, each with their own Claude)

Both of you work in this one repo as collaborators. Don't fork: a fork drifts apart and has to be merged back by hand.

- **Start every job from the latest `main`**, on a new branch named for the job (`leo/eradicator-mk3`, `keith/soccer-penalties`).
- **Never push straight to `main`.** Open a pull request and let the other person look at it (or at least see it), then merge it on GitHub. Merging is what makes it live, because Pages deploys from `main`.
- **Say which game you're in.** Each game is one big HTML file, so two people changing the same file at once is where clashes come from. If you both need the same file, keep the PRs small and merge often.
- **If GitHub says a PR has conflicts**, ask your Claude to merge the latest `main` into the branch and sort it out. It can do that.
- Run `node tests/smoke.mjs` before opening a PR. It should end with "All checks passed".

## Working conventions so far

- Before pushing: run `node tests/smoke.mjs`, plus a syntax check (e.g. parse the last `<script>` with acorn).
- Keep the code style of the surrounding code: compact functions, short comments explaining *why*.

## Eradicator in AR (`eradicator-ar.html`, `models/`)

`models/build_eradicator.py` builds the MK II in Blender (run it with `pip install bpy==5.2.2`, then `python models/build_eradicator.py`; add `--render <dir>` for preview stills). It writes `eradicator-mk2.glb` for Android and the web, and `eradicator-mk2.usdz` for iPhone/iPad AR Quick Look (Y-up, metres, feet on the floor, about 2 m tall). `eradicator-ar.html` shows it with Google's `<model-viewer>`; its "View in your room" button opens AR on phones. Change the script and re-run it rather than editing the exported files.
