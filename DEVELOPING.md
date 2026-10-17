# Little Jimmy games: developer hand-off

This repo holds two browser games for phones, built with Claude: **Pocket Soccer** and **Tower Defence**.
This guide is for whoever (and whichever Claude) picks them up next. Give your Claude this file first.

- Pocket Soccer: `soccer.html` (live at https://keithharro-dot.github.io/Little-Jimmy/soccer.html)
- Tower Defence: `tower-defence.html` (live at https://keithharro-dot.github.io/Little-Jimmy/tower-defence.html)
- Music: the repo owner's own songs in `music/` (covers in `music/covers/`), shared freely for these games. Credit by song title only; the files deliberately carry no artist name. `music/jukebox.js` holds the song list and the picker both games use; to add a song, add the MP3, a 160px cover and one line there. Tower Defence also plays `music/eradicator-mk2-phonk.mp3` (a phonk remix of the owner's MK II theme) as the MK II boss music, through `BOSSM`/`fadeTo`; other bosses keep the synthesised boss music.
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
  - There is one version of the game: 3D, with chaos power-ups and goal movies always on. Phones that can't do 3D fall back to 2D by themselves.
  - Version 0.147 is deliberate: it is the last one that ships plain-script `examples/js` files (glow/bloom, RoomEnvironment) usable without a bundler.
  - Colour uses sRGB (`ColorManagement.legacyMode = false`, sRGB textures, and a `GammaCorrectionShader` pass after bloom). Without that, scenes look washed out.
- **The simulation catches up after slow frames:** it runs in small fixed-size steps (see `runSim` / `startGame`), so a phone busy drawing 3D doesn't play in slow motion.
- **Theme music (`THEME`, `themeTo(vol)`):**
  - One looping `<audio>` element, routed through Web Audio so it can fade. iPhones ignore `audio.volume`.
  - It starts on the first tap, because browsers block sound before that.
- **Inside the Claude app**, a copy of each game runs with a flag (`window.PS_EMBEDDED` / `window.TD_EMBEDDED`) that hides features needing a network. Those copies belong to the owner's Claude account; you'll publish your own if you want one. They are built by stripping the doctype/html/head/body tags and the PeerJS/QR scripts, adding the flag line before `<script src="music/jukebox.js">`, and publishing the whole `music/` folder with the page (in two uploads, as it's about 70 MB).

## Pocket Soccer (`soccer.html`)

- **LEO BOMB** (`LEO`, `leoBlast`): at the start of the boss round the ball is dropped on the centre spot as the LEO BOMB (`ball.leo`). The first team to touch it arms it (`powerTouch`); a touch by anyone on the other team sets it off. Their whole team within 75 units is blasted away and frozen for 3.5 s (bosses less), and the ball rockets at their goal. One per match. The snapshot sends `bl`: 0 none, 1 unarmed, 2 armed by blue, 3 armed by red.

Finger soccer for 1–16 players, phones first. Each player is a square block with your face (photo or cartoon) on top. You drag your players with your finger. Touch control (`holds`, `isHeld`, `drawTethers`): a touch within about 1 cm (`GRAB_PX`) grabs the nearest of your players, and the player keeps its offset from the finger so the finger never covers it; a dotted line shows the link. The in-game 🎵 button and the menu chip both open the music picker.

- **Pitch and physics:**
  - `F` holds the sizes (pitch 100 × 160 units).
  - Players are square "Pong paddles": hitting the ball off-centre angles it, which makes aiming easier.
  - Corners are cut off so the ball can't wedge, and there's a throw-in after 2.5 s stuck by a wall.
  - Goals widen slightly for 6–8-a-side (`goalWidth`).
- **Teams:**
  - One outfield player per person on the bigger team (`teamSize`, `OUTFIELD` formations), plus a keeper per side.
  - The computer plays the keeper until a teammate drags it, and whoever grabbed it last controls it (`applyInput`, `grab`).
  - Empty spots are computer players (`aiTarget`).
- **Joining: one link, by QR code or sent:**
  - **📲 Invite friends to play** (`#goHost`) hosts a match and opens the share sheet straight away. Each lobby has one join link: `#join=CODE.PASS&from=Name`, where PASS is a 10-letter pass (`inviteToken`) that lasts until the host leaves the lobby. The lobby shows it as a QR code for friends in the room, and **Send the link** (`shareInvite`) opens the phone's share sheet (WhatsApp, Messages…) and copies it too. Without a share sheet it just copies, and without clipboard access it shows the link to copy.
  - Opening the link (scanned or tapped) shows a Join screen: who invited you, your face and name, and **Join game** (`join` → `connectTo`).
  - Host and guests use PeerJS's own servers (`PEER_NET`), so it works across the internet. The TV screen still uses `PEER_OPTS` (no STUN/TURN), since it sits on the same Wi-Fi as the host.
  - A guest's first message must be `{t:'knock', token}`.
  - Some school and guest Wi-Fi networks block phones talking to each other; the hotspot is the workaround.
- **Chaos power-ups** (`POWERS`; always on):
  - Each goal powers up the team that let it in; a team 2+ goals behind gets two powers. Powers stack.
  - The ladder: turbo boots, banana peels, human cannon, tennis rackets, ghost curse (10 s, every 40 s), freeze ray, magnet boots, brick wall, homing rocket ball, nuclear ball.
  - All trigger automatically: on touch, or on a timer. `powerTouch` and `powerStep` hold the logic.
  - Balance notes: power shots lose their boost when they hit a player (otherwise rebounds fly back at rocket speed), and the cannon is tuned via `CANNON = [speed, cooldown]`.
- **Goal movies** (`CUT`, `cutStart`, `drawCut`; always on, sent as `info.cut`): after every goal the host holds the match for `CUT.len()` (7.1 s with chaos, 3.6 s without) and every phone plays an arcade-style cut scene, drawn at 256×192 on `cutLow` and blown up with hard pixels on `#cutcv`.
  - Scene 1: four cheerleaders in the scorers' colours (`figure` jointed puppets, `cheerPose` star jumps and toe touches, `pompom`) in the floodlit stadium (`stadium`: crowd, boards), with GOAL! and the scorer's face.
  - Scene 2 (chaos only): the camera pans down the sideline, and a player from the team that let it in (a person if there is one, wearing their face) runs to the esky, chugs a stubby and powers up with the power their team just got.
  - Text is drawn crisp on top (`mkText`). An announcer says "Goal!" and "Power up!" through the browser's speech. Tap skips it; on the host or a single phone that also ends the pause for everyone.
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
- **Saved on the phone:** `ps_profile` (name, faces, boss name), `ps_music`, `ps_records`.

## Tower Defence (`tower-defence.html`)

Two players: one sends zombies, one builds towers. Board: 15 × 9 tiles (`COLS`, `ROWS`).

- **Maps** (`MAPS`: Graveyard, Frozen, Desert): road waypoints, colours and scenery.
- **Enemies** (`ENEMIES`):
  - Zombies, speedy, phantom (hidden; only 📡 towers see it), bats (fly straight), riot (shield), medic (heals), brute (armour).
  - Bosses: Eradicator, MK II (rages at half health), Doom Dad and the Void (mind control, Voidlings, stomp), plus minions (Avatars, Voidlings).
- **Towers:** design your own (`stats`, `cleanSpec`) or use the `PRESETS`. Levels 1–4 change the soldier's uniform colour (`LEVEL_UNIFORM`). Reviver and DJ are support towers.
- **Waves** (`WAVES = 50`): an Eradicator on wave 20, an MK II on 40, Doom Dad on 45, the Void on 50. The zombie sender's economy is in `ECO`.
- **LEO BOMB** (`LEO`, the gold first card in the tower list): the most powerful weapon. It charges over time (`g.leo` toward `g.leoNeed`: 180 s for the first, then 300 s). Tap the card, then the board: `{type:'leo', x, y}` kicks it from the castle (fx `leoK`, 1.3 s flight), and on landing (`p.leo` in `g.proj`) it does 9000 damage within 1.2 tiles, fading to 30% at 3.2 tiles, straight through shields and armour, flyers included (fx `leo`). The snapshot sends the charge as `lb` (0–1).
- **Launcher tower** (`role:'launcher'`, the last preset): one tower whose weapon changes with each upgrade, up to level 5 (`maxLvl`). The `LAUNCHER` table holds each level's weapon, damage, rate, range, blast radius, whether it hits flyers (`air`) and hidden zombies (`det`), and the upgrade price: Mortar → Missile pod → Twin pods → Laser → ANNIHILATOR (death ray plus a 6-missile `swarm` salvo).
  - Shells and missiles: `launch` aims where the target will be when it lands (zombies follow a fixed route, so `posAt`/`flyAt` give it exactly) and puts it in `g.proj`. `step` blasts everything nearby when it lands. Clients draw the flight from the `shell`/`msl` fx (start, end, time left), so no positions travel over the network; 3D reuses `launchMissile` (a ball for shells).
  - Beams: `fireLauncher` hurts every zombie within 0.35 tiles of the line, out to full range. Shot kinds in the snapshot: 0 bullet, 1 splash, 2 laser, 3 death ray.
  - Measured balance (damage per second against one zombie / a pack of 6, total gold): Lv1 12/38 (180), Lv2 27/103 (400), Lv3 58/272 (780), Lv4 96/288 (1380), Lv5 263/1050 (2380). One maxed launcher placed 3 tiles from the road takes an MK II from 9000 to about 2000 HP alone; place it out of the 2.2-tile rocket-burst reach or it gets cracked.
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

- **Doom Dad** (`doom`, `doomAbilities`, `DOOM`, `GRAPPLE`): the ultimate boss of wave 45 (also sendable, 2500 energy), a cartoon space marine with the repo owner's face in the helmet. The face is pixel art (56×85) embedded as the `DOOM_FACE` data URI; `doomDad` in `drawUnit` draws it in 2D and `doomTpl` puts it on the 3D helmet as a texture. Every 10 s he charges his BFG (`holdK` 8, 1.4 s) at the biggest group of towers within 7 tiles, then the blast (fx `bfg`, a green plasma ball) stuns and cracks every tower within 1.8 tiles. Every 5 s a super shotgun (fx `sgun`) knocks out the 3 closest towers within 2.6 tiles for 1.5 s, no crack. Every 12 s his grappling hook (`GRAPPLE`, `holdK` 11, fx `hook` → `rip` → `crunch`) flies out of his mouth at the priciest tower within 5.5 tiles, rips it out, reels it up (`t.hk.q` 0→1, sent as the tower's `hk` with his mouth position; `hookPos` places it in 2D and 3D) and he eats it: gone, no refund, no revive. If he dies mid-grab the tower drops back. At half HP he goes BERSERK (`e.zerk`, `holdK` 9): shield refilled, 1.7× speed, BFG every 6 s. Unlike the MK II's rage, berserk doesn't halve income. The snapshot's fury flag covers both. His face is public with the game; to change it, make a new 56×85 PNG and replace the data URI and `models/doomdad-face.png` (8× nearest-neighbour upscale, dark green background).

## Doom Dad in AR (`doom-dad-ar.html`, `models/build_doomdad.py`)

`python models/build_doomdad.py [--render <dir>]` builds him in Blender with `arlib.py` (2.1 m tall, the face from `models/doomdad-face.png`) and writes `models/doom-dad.glb` and `.usdz`.

## Doom Dad 3D print (`models/print/`, `models/build_doomdad_print.py`)

`python models/build_doomdad_print.py [--height 150] [--render <dir>]` poses him kicking the LEO BOMB on a base and writes `models/print/doom-dad-kick.stl` (one piece) and `doom-dad-kick.3mf` (green body and gold ball as two lined-up parts), in millimetres. Parts are fused with a voxel remesh so the meshes are watertight; it prints the non-manifold edge count (should be 0). The face is a height map, `models/doomdad-face-relief.png` (bright = raised). `models/print/README.md` has the printing notes.

## Eradicator in AR (`eradicator-ar.html`, `models/`)

`models/build_eradicator.py` builds the MK II in Blender (run it with `pip install bpy==5.2.2`, then `python models/build_eradicator.py`; add `--render <dir>` for preview stills). It writes `eradicator-mk2.glb` for Android and the web, and `eradicator-mk2.usdz` for iPhone/iPad AR Quick Look (Y-up, metres, feet on the floor, about 2 m tall). `eradicator-ar.html` shows it with Google's `<model-viewer>`; its "View in your room" button opens AR on phones. Change the script and re-run it rather than editing the exported files.

## Battles in AR (`battlefield-ar.html`, `models/`)

Three frozen moments from the games, each life size for walking around a sports oval or table size for the lounge room: The Battlefield and Boss Assault (Tower Defence), and the Soccer Boss Round. Each was staged in the real game, exported, and dressed up in Blender with explosions, smoke, missile trails, glowing beams and mushroom clouds. The shared Blender toolkit is `models/arlib.py`. See `models/battle/README.md` for how to stage and rebuild a scene.
