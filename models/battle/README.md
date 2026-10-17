# Battles in AR

`battlefield-ar.html` shows frozen moments from the games in AR. Each scene comes life size, for walking around a sports oval, or table size (`-mini`), for the lounge room:

| Scene | Files | Life size |
|---|---|---|
| ⚔️ The Battlefield (Tower Defence) | `models/battlefield.*` | about 93 × 65 m |
| 💥 Boss Assault (Tower Defence) | `models/td-boss.*` | about 93 × 65 m |
| ⚽ Boss Round (Pocket Soccer) | `models/soccer-boss.*` | about 71 × 129 m (the pitch is 50 × 80 m) |

How they're made:

1. **Stage and freeze a moment in the real game.** A headless browser runs the game in 3D and the stage script sets up the scene. The export script clones the 3D world and writes `<scene>.glb` with three.js's GLTFExporter, plus a `.json` listing every missile, beam and particle in the air at that instant.
   - Tower Defence: `models/battle/stage.js` and `export.mjs`. Run `node models/battle/export.mjs <three-pkg dir> battle|boss`.
   - Soccer: `models/soccer/stage.js` and `export.mjs`.
2. **Make it epic in Blender.** `pip install bpy==5.2.2`, then run `python models/build_battlefield.py battle|boss` or `python models/build_soccer.py`.
   - Both scripts use `models/arlib.py`, which:
     - turns vertex paint into real materials (iPhone AR ignores vertex colours)
     - provides the effect builders: fireballs, smoke, mushroom clouds, beams, 3D lettering
     - scales the scene and clips it at ground level
     - exports GLB for Android and the web, and USDZ for iPhone/iPad
   - Blender's USD exporter drops transparency and AR clips glow above 1, so `arlib.export` patches opacity and normalised emissive colours into the USD before packaging it.

To make a new scene, stage it in the game, export it, then write a small build script using `arlib`.
