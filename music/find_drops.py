# Finds each song's "drops": the starts of its most intense 10 s stretches (loudness plus brightness), for Tower Defence
# to jump to on boss moves. Needs ffmpeg and numpy. Run: python music/find_drops.py, then paste the printed
# SONG_DROPS lines into music/jukebox.js.
import subprocess, numpy as np, json, glob, os
SR = 11025; HOP = .25
out = {}
for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '*.mp3'))):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32)/32768
    n = int(SR*HOP); frames = x[:len(x)//n*n].reshape(-1, n)
    rms = np.sqrt((frames**2).mean(1) + 1e-12)
    hf = np.sqrt((np.diff(frames, axis=1)**2).mean(1) + 1e-12)          # brightness: drums, distortion
    loud = 20*np.log10(rms) ; inten = loud + 8*np.log10(hf/rms + 1e-6)
    dur = len(rms)*HOP
    w = int(10/HOP); k = np.ones(w)/w
    sm = np.convolve(inten, k, 'valid')                                 # 10 s mean intensity starting at each frame
    order = np.argsort(-sm); picks = []
    for i in order:
        t = i*HOP
        if t < 3 or t > dur - 15: continue
        if all(abs(t - p) >= 20 for p in picks): picks.append(t)
        if len(picks) == 4: break
    # move each pick back to the sharpest rise in the 5 s before it, so the jump lands on an attack
    s1 = np.convolve(loud, np.ones(4)/4, 'same'); rise = np.r_[0, np.diff(s1)]
    cues = []
    for t in picks:
        a, b = int(max(0, t - 5)/HOP), int((t + 1)/HOP)
        j = a + int(np.argmax(rise[a:b])); cues.append(round(max(0, j*HOP - .25), 1))
    start = next((i*HOP for i, v in enumerate(loud) if v > np.median(loud) - 12), 0)
    out[os.path.basename(f)[:-4]] = {'dur': round(dur), 'start': round(start, 1), 'hot': sorted(cues),
                                      'spread': round(float(sm.max() - np.median(sm)), 1)}
for k, v in out.items(): print(f"  '{k}':[{', '.join(str(t) for t in v['hot'])}],")
