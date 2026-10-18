// Shared music picker for both games. To add a song: drop the MP3 in music/, a 160px cover in music/covers/, and add a line below.
// The choice is remembered per phone and shared by both games (same site). "Play my own song" plays a file from the player's
// own phone; it never leaves the phone, and it isn't remembered after a reload.
// Each song's "drops": the starts (in seconds) of its most intense 10-second stretches, found by measuring loudness and
// brightness through the track (music/find_drops.py; re-run it when you add a song). Tower Defence jumps to
// one of these when a boss makes a big move. A song with no entry just doesn't jump.
window.SONG_DROPS = {
  'blues-hammer':[154.8, 190.8, 218.2, 238.0],
  'broken':[152.8, 173.8, 223.2, 248.5],
  'cool-rocks':[54.2, 78.0, 97.2, 119.5],
  'demise':[23.0, 61.8, 89.2, 134.0],
  'dikshifter-the-2nd-take':[11.8, 54.2, 88.5, 107.2],
  'dream':[25.0, 49.5, 70.0, 95.2],
  'eradicator-mk2-phonk':[19.8, 58.5, 114.5, 134.2],
  'inner-demons':[43.5, 66.0, 98.2, 122.5],
  'listen':[70.8, 94.2, 121.2, 148.0],
  'lock-down-blues':[35.8, 57.5, 74.0, 100.8],
  'over-the-edge':[16.8, 111.5, 169.5, 192.5],
  'psycholists':[71.8, 142.8, 181.8, 206.2],
  'softard-blues':[24.5, 47.2, 69.2, 111.8],
  'the-legend-part-5':[44.5, 66.2, 88.8, 110.5],
  'the-legend-v2':[44.8, 73.0, 91.5, 134.8],
  'what-we-do-v2':[68.2, 131.8, 148.0, 187.0],
  'what-we-do':[63.8, 84.2, 108.0, 144.8]
};
window.SONGS = [
  ['dikshifter-the-2nd-take', 'Dikshifter — The 2nd Take'],
  ['eradicator-mk2-phonk', 'Eradicator MK2 (Phonk)'],
  ['psycholists', 'Psycholists'],
  ['the-legend-part-5', 'The Legend Part 5'],
  ['the-legend-v2', 'The Legend V2'],
  ['inner-demons', 'Inner Demons'],
  ['broken', 'Broken'],
  ['what-we-do-v2', 'What We Do V2'],
  ['what-we-do', 'What We Do'],
  ['cool-rocks', 'Cool Rocks'],
  ['over-the-edge', 'Over the Edge'],
  ['dream', 'Dream'],
  ['softard-blues', 'Softard Blues'],
  ['demise', 'Demise'],
  ['lock-down-blues', 'Lock Down Blues'],
  ['listen', 'Listen'],
  ['blues-hammer', 'Blues Hammer'],
].map(([id, title]) => ({id, title, url:'music/' + id + '.mp3', cover:'music/covers/' + id + '.jpg', hot:(window.SONG_DROPS || {})[id] || []}));

// Jukebox(hooks): hooks.change() is called when the song changes; hooks.isOn()/hooks.setOn(on) read and switch the game's music.
window.Jukebox = function (hooks) {
  const SONGS = window.SONGS, J = {own:null, shuffle:false, song:SONGS[0]};
  let saved = null; try { saved = localStorage.getItem('jb_song'); } catch (e) {}
  if (saved === 'shuffle' || !saved) { J.shuffle = true; J.song = SONGS[Math.floor(Math.random()*SONGS.length)]; }   // shuffle until the player picks a song
  else J.song = SONGS.find(s => s.id === saved) || SONGS[0];
  const save = v => { try { localStorage.setItem('jb_song', v); } catch (e) {} };
  J.url = () => J.own ? J.own.url : J.song.url;
  J.title = () => J.own ? J.own.title : J.shuffle ? 'Shuffle: ' + J.song.title : J.song.title;
  J.cover = () => J.own ? '' : J.song.cover;
  J.loop = () => !J.shuffle || !!J.own;
  J.hot = () => J.own ? [] : J.song.hot;
  J.next = () => {   // shuffle: any song but the one that just finished
    const rest = SONGS.filter(s => s !== J.song); J.song = rest[Math.floor(Math.random()*rest.length)]; hooks.change();
  };
  const on = () => { if (!hooks.isOn()) hooks.setOn(true); };   // picking a song means you want to hear it
  const pick = s => { J.own = null; J.shuffle = false; J.song = s; save(s.id); close(); on(); hooks.change(); };

  // ---- the picker sheet (styles itself; each game can tint it with --jb-bg / --jb-panel / --jb-text / --jb-accent) ----
  const css = document.createElement('style');
  css.textContent = `
#jbSheet{position:fixed;inset:0;z-index:9999;display:flex;align-items:flex-end;justify-content:center;background:rgba(0,0,0,.55)}
#jbSheet[hidden]{display:none}
#jbSheet .jb{width:min(520px,100%);max-height:86vh;max-height:86dvh;display:flex;flex-direction:column;background:var(--jb-bg,#161b22);color:var(--jb-text,#e6edf3);
  border-radius:18px 18px 0 0;padding:14px 14px calc(14px + env(safe-area-inset-bottom));box-shadow:0 -8px 30px rgba(0,0,0,.5);font:15px/1.3 system-ui,-apple-system,sans-serif}
#jbSheet .jbHead{display:flex;align-items:center;gap:8px;margin-bottom:10px}
#jbSheet .jbHead b{flex:1;font-size:18px}
#jbSheet button{font:inherit;color:inherit;border:0;cursor:pointer}
#jbSheet .jbX{background:var(--jb-panel,#21262d);border-radius:50%;width:36px;height:36px;font-size:18px;padding:0}
#jbSheet .jbOn{background:var(--jb-panel,#21262d);border-radius:999px;padding:8px 14px}
#jbSheet .jbOn.on{background:var(--jb-accent,#3fb950);color:#0d1117;font-weight:600}
#jbSheet .jbTop{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px}
#jbSheet .jbTop button{background:var(--jb-panel,#21262d);border-radius:12px;padding:12px 8px;font-weight:600}
#jbSheet .jbList{overflow-y:auto;-webkit-overflow-scrolling:touch;display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;padding-bottom:4px}
#jbSheet .jbSong{background:var(--jb-panel,#21262d);border-radius:12px;padding:8px;text-align:left;display:flex;flex-direction:column;gap:6px;outline:2px solid transparent}
#jbSheet .jbSong img{width:100%;aspect-ratio:1;border-radius:8px;object-fit:cover;background:#000}
#jbSheet .jbSong.cur{outline-color:var(--jb-accent,#3fb950)}
#jbSheet .jbSong.cur span::before{content:'▶ ';color:var(--jb-accent,#3fb950)}
#jbSheet .jbTop button.cur{outline:2px solid var(--jb-accent,#3fb950)}`;
  document.head.appendChild(css);
  const sheet = document.createElement('div'); sheet.id = 'jbSheet'; sheet.hidden = true;
  sheet.innerHTML = `<div class="jb" role="dialog" aria-label="Choose the music">
    <div class="jbHead"><b>🎵 Music</b><button class="jbOn"></button><button class="jbX" aria-label="Close">✕</button></div>
    <div class="jbTop"><button class="jbShuf">🔀 Shuffle all</button><button class="jbOwn">📁 Play my own song</button></div>
    <div class="jbList"></div>
    <input type="file" accept="audio/*" hidden></div>`;
  document.body.appendChild(sheet);
  const q = s => sheet.querySelector(s), list = q('.jbList'), file = q('input');
  for (const s of SONGS) {
    const b = document.createElement('button'); b.className = 'jbSong'; b.dataset.id = s.id;
    b.innerHTML = `<img loading="lazy" alt=""><span></span>`; b.querySelector('img').src = s.cover; b.querySelector('span').textContent = s.title;
    b.onclick = () => pick(s); list.appendChild(b);
  }
  const paint = () => {
    for (const b of list.children) b.classList.toggle('cur', !J.own && !J.shuffle && b.dataset.id === J.song.id);
    q('.jbShuf').classList.toggle('cur', J.shuffle && !J.own); q('.jbOwn').classList.toggle('cur', !!J.own);
    q('.jbOwn').textContent = J.own ? '📁 ' + J.own.title : '📁 Play my own song';
    const on = hooks.isOn(); q('.jbOn').textContent = on ? 'Music on' : 'Music off'; q('.jbOn').classList.toggle('on', on);
  };
  const close = () => { sheet.hidden = true; };
  J.open = () => { paint(); sheet.hidden = false; };
  q('.jbX').onclick = close;
  sheet.addEventListener('pointerdown', e => { if (e.target === sheet) close(); });
  q('.jbOn').onclick = () => { hooks.setOn(!hooks.isOn()); paint(); };
  q('.jbShuf').onclick = () => { J.own = null; J.shuffle = true; save('shuffle'); close(); on(); J.next(); };
  q('.jbOwn').onclick = () => file.click();
  file.onchange = () => {
    const f = file.files[0]; if (!f) return;
    if (J.own) URL.revokeObjectURL(J.own.url);
    J.own = {url:URL.createObjectURL(f), title:f.name.replace(/\.[^.]+$/, '')}; file.value = ''; close(); on(); hooks.change();
  };
  return J;
};
