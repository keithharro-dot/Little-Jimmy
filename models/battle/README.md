# The battlefield, mid-battle

`battlefield-ar.html` shows a frozen moment of a real Tower Defence battle in AR: life size for walking around a sports oval (`models/battlefield.*`, about 93 × 65 m) or table size for the lounge room (`models/battlefield-mini.*`, about 2 × 1.3 m).

How it's made:

1. **Stage and freeze a battle in the game** (`stage.js`, `export.mjs`). The game runs in a headless browser in 3D. The script places a defence (Launchers at every level, plus snipers, boomers, frost, troopers, DJ and reviver), spawns the MK I, a raging MK II, the Void, bats and a horde, and lets it fight for a couple of seconds while keeping everyone alive. It then clones the 3D world and writes `battle.glb` with three.js's GLTFExporter, plus `battle.json`, which lists every missile, beam and particle in the air at that instant.
2. **Make it epic in Blender** (`../build_battlefield.py`, run with `pip install bpy==5.2.2`). This step:
   - turns the game's vertex-painted blocks into real materials
   - adds fireballs, smoke, missile trails, glowing beams, sparks, boss auras and scorch marks
   - trims the scenery, scales it (`TILE` metres per game tile) and slices it at ground level
   - exports GLB for Android and the web, and USDZ for iPhone/iPad

   Blender's USD exporter drops transparency and AR clips glow above 1, so the script patches opacity and normalised emissive colours into the USD before packaging it.

To stage a different battle, edit `stage.js`, run `export.mjs`, then run `build_battlefield.py`.
