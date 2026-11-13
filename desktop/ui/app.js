'use strict';
const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let api, S = {}, players = [], R = {tab: 'pro'}, sig = '', lab = {zoom: 4, light: false}, sel = new Set(), form = {};

async function call(name, ...args) {
  const r = await api[name](...args);
  if (!r || !r.ok) throw new Error(r ? r.error : 'No response from the app.');
  return r.data;
}
async function guard(fn) { try { return await fn(); } catch (e) { toast(e.message, true); } }
function toast(text, bad) {
  const t = document.createElement('div');
  t.className = 'toast' + (bad ? ' err' : ''); t.textContent = text;
  $('#toasts').append(t); setTimeout(() => t.remove(), bad ? 6000 : 3200);
  status(text);
}
function status(text) { $('#status').textContent = text; }
async function copy(text) {
  try { await navigator.clipboard.writeText(text); }
  catch { const a = document.createElement('textarea'); a.value = text; document.body.append(a); a.select(); document.execCommand('copy'); a.remove(); }
  toast('Copied to clipboard.');
}
function ask(title, body, ok = 'Continue') {
  return new Promise(done => {
    const m = $('#modal');
    m.innerHTML = `<div class="dlg" role="dialog" aria-modal="true" aria-label="${esc(title)}"><h2>${esc(title)}</h2><p>${esc(body)}</p><div class="row"><button class="ghost" data-m="0">Cancel</button><button class="btn" data-m="1">${esc(ok)}</button></div></div>`;
    m.hidden = false; $('[data-m="1"]', m).focus();
    const end = v => { m.hidden = true; m.innerHTML = ''; m.onclick = null; document.removeEventListener('keydown', key, true); done(v); };
    const key = e => { if (e.key === 'Escape') { e.stopPropagation(); end(false); } };
    document.addEventListener('keydown', key, true);
    m.onclick = e => { const b = e.target.closest('[data-m]'); if (b) end(b.dataset.m === '1'); else if (e.target === m) end(false); };
  });
}

function xhair(c, z) {
  const k = z * 2, o = Math.max(0, c.gap * k) + 3, l = Math.max(2, c.length * k), w = Math.max(1, c.thickness * z * .6), h = 100;
  const arms = [[h - w / 2, h - o - l, w, l], [h - w / 2, h + o, w, l], [h - o - l, h - w / 2, l, w], [h + o, h - w / 2, l, w]];
  const r = (a, f, p = 0) => `<rect x="${a[0] - p}" y="${a[1] - p}" width="${a[2] + 2 * p}" height="${a[3] + 2 * p}" fill="${f}"/>`;
  return `<svg viewBox="0 0 200 200">${c.outline ? arms.map(a => r(a, '#000', 1.5)).join('') : ''}${arms.map(a => r(a, c.color)).join('')}</svg>`;
}
const stats = items => `<div class="stats">${items.map(([k, v]) => `<div class="stat"><small>${esc(k)}</small><b>${esc(v)}</b></div>`).join('')}</div>`;
const code = t => t.split('\n').map(l => l.trim().startsWith('//') ? `<span class="c">${esc(l)}</span>` : esc(l)).join('\n');
const backBtn = '<button class="ghost small" data-act="back">← Back</button> <small class="muted">Esc</small>';

/* ---------- views ---------- */
function viewIntro() {
  const card = (id, mk, tag, title, text) => `<button class="gamecard" data-act="pick" data-g="${id}" aria-pressed="${sel.has(id)}"><span class="mk">${mk}</span><span><span class="tag">${tag}</span><h3>${title}</h3><p>${text}</p></span><span class="tick">${sel.has(id) ? '✓ Selected' : '+ Select'}</span></button>`;
  return `<div class="page" style="max-width:720px;padding-top:64px"><p class="kicker">PerfSettings / Your games. Your performance.</p><h1>Make it your workspace.</h1><p class="sub">Choose the games you care about. You can change this any time.</p>
  ${card('cs2', 'CS2', 'AVAILABLE NOW', 'Counter-Strike 2', 'Pro settings, crosshair previews and your config library.')}
  ${card('fivem', 'V', 'COMING SOON', 'FiveM', 'Save your interest. FiveM presets and installation are not available yet.')}
  <p class="muted" id="hint">${sel.size ? 'Ready when you are.' : 'Choose at least one game to continue.'}</p>
  <button class="btn" data-act="finish" style="padding:14px 28px">Continue to PerfSettings →</button></div>`;
}
const plist = list => list.length ? list.map(p => `<button class="card pcard" data-act="player" data-id="${esc(p.id)}"><div class="top" style="background:linear-gradient(135deg,${esc(p.accent)}22,transparent)"><span class="role" style="color:${esc(p.accent)}">${esc(p.role)}</span><div class="nick">${esc(p.name)}</div><div class="team">${esc(p.team)}</div></div><div class="mini"><div><small>DPI</small><b>${p.dpi}</b></div><div><small>SENS</small><b>${p.sens}</b></div><div><small>eDPI</small><b>${p.edpi}</b></div></div></button>`).join('') : '<p class="muted">No players found. Try another search.</p>';
function viewPro() {
  const q = (R.q || '').toLowerCase(), list = players.filter(p => (p.name + ' ' + p.team + ' ' + p.role).toLowerCase().includes(q));
  return `<div class="page"><section class="hero"><div><p class="kicker">● Built for Counter-Strike 2</p><h1>Their settings.<br><em>Your edge.</em></h1><p class="sub">Find a preset. Make it yours. Join the server.</p><button class="btn" data-act="nav" data-tab="library">Open your library →</button></div>
  <div><div class="scope" role="img" aria-label="Crosshair preview">${xhair(players[0].crosshair, 6)}</div></div></section>
  <div class="row spread mt2"><h2>Pro players</h2><small class="muted">${players.length} presets</small></div>
  <input class="search mt" data-in="q" placeholder="Search by player, team or role" value="${esc(R.q || '')}" aria-label="Search players">
  <div class="grid3 mt" id="plist">${plist(list)}</div>
  <p class="muted mt" style="font-size:13px">Snapshot: Nov 12, 2026 · ProSettings.net · Partial presets, not original player files.</p></div>`;
}
function viewPlayer(p) {
  const c = p.crosshair, sec = (k, t, cap, body) => `<section class="card sec" id="sec-${k}"><div class="head"><h2>${t}</h2><p class="muted" style="margin:6px 0 0;font-size:14px">${cap}</p></div>${body}</section>`;
  return `<div class="page">${backBtn}
  <div class="card mt row" style="gap:24px;background:linear-gradient(135deg,#1e1316,var(--panel))"><div class="av">${esc(p.name.slice(0, 2).toUpperCase())}</div><div class="grow"><p class="kicker">Pro player / Counter-Strike 2</p><h1 style="margin:8px 0 4px">${esc(p.name)}</h1><div class="muted">${esc(p.real)} · ${esc(p.country)}</div><div style="color:${esc(p.accent)};font-weight:700;margin-top:6px">${esc(p.team)} / ${esc(p.role)}</div></div></div>
  <div class="row mt"><button class="btn" data-act="addPlayer" data-id="${esc(p.id)}">＋ Add preset to library</button><button class="ghost" data-act="copyPreset" data-id="${esc(p.id)}">Copy preset</button><button class="ghost" data-act="url" data-u="${esc(p.source)}" style="margin-left:auto">Source ↗</button></div>
  <p class="muted" style="font-size:13px">Snapshot / Nov 12, 2026 · Partial preset; DPI and video require manual setup.</p>
  <div class="pills">${[['mouse', 'Mouse'], ['crosshair', 'Crosshair'], ['viewmodel', 'Viewmodel'], ['video', 'Video'], ['gear', 'Gear'], ['code', 'Config']].map(([k, t]) => `<button data-act="scroll" data-t="sec-${k}">${t}</button>`).join('')}</div>
  ${sec('mouse', 'Mouse settings', esc(p.mouse), stats([['DPI', p.dpi], ['Sensitivity', p.sens], ['eDPI', p.edpi], ['Zoom sensitivity', 1], ['Polling rate', p.hz + ' Hz'], ['Windows sensitivity', p.windows]]))}
  ${sec('crosshair', 'Crosshair', 'Illustration of the recorded values. Preview zoom does not change your config.', `<div class="lab"><div><label class="muted" for="zoom">Preview zoom: <b id="zv">${lab.zoom}</b></label><input id="zoom" data-in="zoom" type="range" min="1" max="8" value="${lab.zoom}"><button class="ghost mt" data-act="bg">Switch background</button></div><div class="scope ${lab.light ? 'light' : ''}" id="lab" style="max-height:260px;aspect-ratio:auto;height:240px">${xhair(c, lab.zoom)}</div></div>${stats([['Style', 'Static cross'], ['Follow recoil', 'No'], ['Center dot', 'No'], ['Length (px)', c.length], ['Thickness (px)', c.thickness], ['Gap (px)', c.gap], ['Outline', c.outline ? 'Yes' : 'No'], ['Color', c.color.toUpperCase()], ['Opacity', 255]])}`)}
  ${sec('viewmodel', 'Viewmodel', 'Position and field of view included in the partial preset.', stats([['Field of view', 68], ['Offset X', 2.5], ['Offset Y', 0], ['Offset Z', -1.5]]))}
  ${sec('video', 'Video settings', 'Reference values — set these manually in CS2.', stats([['Resolution', p.res], ['Aspect ratio', '4:3'], ['Scaling', 'Stretched'], ['Display mode', 'Fullscreen'], ['Brightness', p.brightness], ['MSAA', p.msaa], ['V-Sync', 'Disabled'], ['NVIDIA Reflex', p.reflex]]))}
  ${sec('gear', 'Peripherals', 'Only documented equipment is shown; missing gear is not guessed.', stats([['Mouse', p.mouse], ['Keyboard', 'Not documented'], ['Headset', 'Not documented'], ['Monitor', 'Not documented']]))}
  ${sec('code', 'Config preview', 'Generated sensitivity and viewmodel preset. This is not the player’s original config or a crosshair share code.', `<pre class="code">${code(p.preset)}</pre>`)}</div>`;
}
const libRows = (items, q) => {
  const rows = items.filter(i => i.name.toLowerCase().includes((q || '').toLowerCase()));
  if (!rows.length) return `<div class="card empty"><h2>${items.length ? 'No configs found.' : 'Your library starts here.'}</h2><p class="muted">Import a .cfg or choose a preset from Pro players.</p><button class="btn" data-act="import">↑ Import config</button></div>`;
  return rows.map(i => `<button class="item" data-act="cfg" data-id="${i.id}"><span class="ic">{ }</span><span class="grow"><b>${esc(i.name)}</b><br><small>.cfg · ${i.size.toLocaleString('en-US')} bytes · Saved locally</small></span><span class="ghost small">Open ↗</span></button>`).join('');
};
async function viewLibrary() {
  const d = await call('library'); sig = d.sig; R.items = d.items; $('#count').textContent = d.items.length;
  return `<div class="page"><p class="kicker">Your config collection</p><h1>My configs.</h1><p class="sub">Your pro presets and imported configs, ready for the next match.</p>
  <div class="metrics"><div class="card"><small>Saved configs</small><b>${String(d.items.length).padStart(2, '0')}</b></div><div class="card"><small>Storage</small><b>This PC</b></div><div class="card"><small>Backup</small><b>Before overwrite</b></div></div>
  <div class="row spread" style="margin-bottom:14px"><input class="search grow" data-in="lq" placeholder="Search your library" value="${esc(R.lq || '')}" aria-label="Search library"><button class="btn" data-act="import">↑ Import config</button></div>
  <div id="llist">${libRows(d.items, R.lq)}</div></div>`;
}
async function viewCfg(id) {
  const c = await call('get_config', id);
  return `<div class="page">${backBtn}<p class="kicker mt">Config workspace</p><h1>${esc(c.name)}</h1><p class="sub">Review the commands before applying. Close CS2 before launching.</p>
  <pre class="code">${code(c.content)}</pre>
  <div class="row mt"><button class="ghost" data-act="export" data-id="${id}">Export .cfg</button><button class="ghost" data-act="edit" data-id="${id}">Edit</button><button class="ghost danger" data-act="del" data-id="${id}">Delete</button></div>
  <div class="note mt">Each config gets its own file. Overwrites create a .bak backup; autoexec.cfg is left untouched.</div>
  <div class="row mt spread"><button class="ghost" data-act="apply" data-id="${id}" style="padding:14px 26px">Apply config</button><button class="btn" data-act="apply" data-id="${id}" data-launch="1" style="padding:14px 26px">▶ Apply &amp; launch CS2</button></div></div>`;
}
async function viewEdit(id) {
  const c = await call('get_config', id);
  return `<div class="page">${backBtn}<h1 class="mt">Edit config</h1><label class="f">Config name<input id="e-name" value="${esc(c.name)}" maxlength="120"></label>
  <label class="f">Commands<textarea class="code" id="e-text" spellcheck="false">${esc(c.content)}</textarea></label>
  <div class="row mt" style="justify-content:flex-end"><button class="btn" data-act="saveEdit" data-id="${id}" style="padding:14px 30px">Save changes</button></div></div>`;
}
async function viewCommunity() {
  const rows = await call('community');
  const cards = rows.length ? rows.map(r => `<div class="card" style="margin-bottom:14px"><p class="kicker">${esc(r.author)} / local</p><h2 style="margin:8px 0">${esc(r.name)}</h2><p class="muted" style="margin:0 0 10px">${esc(r.description || '')}</p><small class="muted">MOUSE ${esc(r.mouse || '—')} &nbsp;/&nbsp; KEYBOARD ${esc(r.keyboard || '—')}</small><div class="row mt"><button class="btn" data-act="toLib" data-id="${r.id}">Add to library</button><button class="ghost danger" data-act="delCom" data-id="${r.id}" style="margin-left:auto">Delete</button></div></div>`).join('')
    : '<div class="card empty"><h2>Make the first setup yours.</h2><p class="muted">A config, a nickname and the gear you play with.</p></div>';
  return `<div class="page"><p class="kicker">Made by players</p><h1>Your setup. Your community.</h1><p class="sub">Add your config, peripherals and the details that make it yours.</p>
  <div class="note">LOCAL COMMUNITY / These setups stay on this PC. Online accounts and publishing are not available yet.</div>
  <div class="mt" style="margin-bottom:22px"><button class="btn" data-act="newCom">＋ Create your setup</button></div>${cards}</div>`;
}
function viewForm() {
  const f = (id, t, v = '') => `<label class="f">${t}<input id="c-${id}" value="${esc(v)}" maxlength="240"></label>`;
  return `<div class="page" style="max-width:720px">${backBtn}<h1 class="mt">Create a local setup</h1>${f('name', 'Config name')}${f('author', 'Nickname', S.nickname)}${f('mouse', 'Mouse')}${f('keyboard', 'Keyboard')}${f('description', 'Short description')}
  <label class="f">.CFG file / maximum 256 KB</label><div class="row mt"><button class="ghost" data-act="pickCfg">Choose .cfg file</button><span class="muted" id="cfile">${form.content ? esc(form.fname) : 'No file chosen'}</span></div>
  <div class="row mt2" style="justify-content:flex-end"><button class="btn" data-act="saveCom" style="padding:14px 30px">Save setup</button></div></div>`;
}
function viewSettings() {
  const path = (id, t, sub, v, pick, label) => `<div class="card mt"><h3>${t}</h3><p class="muted" style="margin:4px 0 0">${sub}</p><div class="path"><input id="${id}" value="${esc(v)}" spellcheck="false" aria-label="${t}"><button class="ghost" data-act="${pick}">${label}</button></div></div>`;
  return `<div class="page" style="max-width:860px"><p class="kicker">Make it yours</p><h1>Ready when you are.</h1><p class="sub">Set your folders once. Then pick a config and get into the game.</p>
  <div class="row"><button class="ghost" data-act="detect">⌕ Detect Steam &amp; CS2 automatically</button><span class="muted" id="pstat"></span></div>
  ${path('p-game', 'Counter-Strike 2 installation', 'The folder containing game / bin / win64 / cs2.exe', S.game, 'pickGame', 'Choose folder')}
  ${path('p-steam', 'Steam', 'The Steam.exe used to launch the game', S.steam, 'pickSteam', 'Choose Steam.exe')}
  <div class="row mt"><button class="btn" data-act="savePaths" style="padding:13px 28px">Verify &amp; save</button></div>
  <div class="note mt">AUTOMATIC BACKUP / Before replacing a settingscs2_*.cfg file, its previous version is saved as .bak. This backup does not cover every setting changed in-game.</div>
  <div class="card mt"><label class="sw"><input type="checkbox" id="motion" data-act="motion" ${S.reduce_motion ? 'checked' : ''}>Reduce motion</label></div>
  <div class="card mt"><h3>Website connection</h3><p class="muted" style="margin:4px 0 14px">Reconnect “Add to app” after moving the app to a different folder.</p><button class="ghost" data-act="proto">Reconnect Add to app</button></div>
  <div class="card mt"><h3>Updates / v${esc(S.version)}</h3><p class="muted" style="margin:4px 0 0">Trusted public repository: username/settingscs2</p><div class="path"><input id="u-repo" value="${esc(S.update_repo)}" spellcheck="false" aria-label="Update repository"></div>
  <label class="sw mt"><input type="checkbox" id="u-auto" ${S.update_auto ? 'checked' : ''}>Check automatically at startup</label>
  <div class="row mt"><button class="ghost" data-act="saveUpd">Save</button><button class="ghost" data-act="chkUpd">Check for updates</button><button class="btn" data-act="instUpd" id="u-inst" hidden>Install &amp; restart</button></div><p class="muted" id="ustat" style="margin:12px 0 0">Installed version: ${esc(S.version)}</p></div></div>`;
}
const viewFivem = () => `<div class="page"><p class="kicker">FiveM / Coming soon</p><h1>Your next workspace.</h1><div class="card empty" style="text-align:left"><h2>FiveM is on the roadmap.</h2><p class="muted">Choose CS2 to explore the available pro settings and config tools.</p><button class="btn" data-act="games">Change games →</button></div></div>`;

/* ---------- routing ---------- */
async function go(tab, sub = null, id = null) { R = {tab, sub, id, q: '', lq: ''}; await render(); }
async function render() {
  const m = $('#main');
  document.body.classList.toggle('intro', !S.intro_complete);
  document.body.toggleAttribute('data-reduce', !!S.reduce_motion);
  $('#ver').textContent = 'v' + S.version;
  $('#games').textContent = (S.games || []).map(g => g === 'cs2' ? 'CS2' : 'FiveM · soon').join(' / ') || 'Choose games';
  try {
    let html, t = R.tab;
    if (!S.intro_complete) html = viewIntro();
    else {
      if (['pro', 'community', 'library'].includes(t) && !S.games.includes('cs2')) t = 'fivem';
      if (t === 'fivem') html = viewFivem();
      else if (t === 'pro') html = R.sub === 'player' ? viewPlayer(players.find(p => p.id === R.id)) : viewPro();
      else if (t === 'library') html = R.sub === 'cfg' ? await viewCfg(R.id) : R.sub === 'edit' ? await viewEdit(R.id) : await viewLibrary();
      else if (t === 'community') html = R.sub === 'form' ? viewForm() : await viewCommunity();
      else html = viewSettings();
      document.querySelectorAll('#nav button').forEach(b => { if (b.dataset.tab === t) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current'); });
    }
    m.innerHTML = html; m.scrollTop = 0;
    if (t === 'settings' && S.intro_complete && !S.game && !S.steam) guard(() => acts.detect());
  } catch (e) { m.innerHTML = `<div class="page"><div class="card empty"><h2>Something went wrong</h2><p class="muted">${esc(e.message)}</p></div></div>`; }
}
async function refresh() { S = await call('state'); }
const back = () => R.sub === 'edit' ? go('library', 'cfg', R.id) : R.sub ? go(R.tab) : null;

/* ---------- actions ---------- */
const val = id => $('#' + id).value;
async function ensurePaths(launch) {
  if (S.game && (!launch || S.steam)) return true;
  const d = await call('detect_paths');
  if (d.game || d.steam) {
    await call('save_paths', S.game || d.game, S.steam || d.steam || ''); await refresh();
    if (S.game && (!launch || S.steam)) { toast('Found your game automatically.'); return true; }
  }
  toast(S.game ? 'Choose Steam.exe in Settings to launch the game.' : 'Choose your CS2 folder in Settings first.', true);
  go('settings'); return false;
}
const acts = {
  nav: el => go(el.dataset.tab),
  back: () => back(),
  site: () => call('open_url', S.site),
  url: el => call('open_url', el.dataset.u),
  games: () => { sel = new Set(S.games); S.intro_complete = false; render(); },
  pick: el => { const g = el.dataset.g; sel.has(g) ? sel.delete(g) : sel.add(g); $('#main').innerHTML = viewIntro(); },
  finish: async () => {
    if (!sel.size) { $('#hint').textContent = 'Choose at least one game to continue.'; return; }
    S.games = await call('set_games', [...sel]); S.intro_complete = true; go(S.games.includes('cs2') ? 'pro' : 'fivem');
  },
  player: el => go('pro', 'player', el.dataset.id),
  addPlayer: async el => { await call('save_player', el.dataset.id); toast(players.find(p => p.id === el.dataset.id).name + ' is in your library.'); go('library'); },
  copyPreset: el => copy(players.find(p => p.id === el.dataset.id).preset),
  scroll: el => $('#' + el.dataset.t).scrollIntoView({behavior: S.reduce_motion ? 'auto' : 'smooth', block: 'start'}),
  bg: () => { lab.light = !lab.light; $('#lab').classList.toggle('light', lab.light); },
  import: async () => { const r = await call('import_file'); if (r) { toast('Config imported. Open it to review and apply.'); go('library'); } },
  cfg: el => go('library', 'cfg', el.dataset.id),
  edit: el => go('library', 'edit', el.dataset.id),
  saveEdit: async el => { await call('save_config', el.dataset.id, val('e-name'), val('e-text')); toast('Changes saved. Apply again to update the file in CS2.'); go('library', 'cfg', el.dataset.id); },
  del: async el => { if (await ask('Remove from library', 'Delete this config? The file already placed in the game folder will be kept.', 'Delete')) { await call('delete_config', el.dataset.id); go('library'); } },
  export: async el => { const p = await call('export_config', el.dataset.id); if (p) toast('Config exported.'); },
  apply: async el => {
    const id = el.dataset.id, launch = !!el.dataset.launch, c = await call('get_config', id);
    if (!await ask('Apply ' + c.name + '?', 'Have you closed CS2 and reviewed the commands?\nThis writes a dedicated preset file. The config can change game settings and key bindings.', launch ? 'Apply & launch' : 'Apply')) return;
    if (!await ensurePaths(launch)) return;
    const r = await call('apply_config', id, launch);
    toast(r.launched ? 'Launch requested through Steam with +exec ' + r.target + '. Check the result in-game.' : 'Config installed' + (r.backup ? ' (backup created)' : '') + ': exec ' + r.target);
  },
  newCom: () => { form = {}; go('community', 'form'); },
  pickCfg: async () => { const r = await call('pick_cfg'); if (r) { form = {content: r.content, fname: r.name + '.cfg'}; $('#cfile').textContent = form.fname; } },
  saveCom: async () => {
    const d = {content: form.content}; ['name', 'author', 'mouse', 'keyboard', 'description'].forEach(k => d[k] = val('c-' + k));
    await call('community_add', d); await refresh(); toast('Setup saved on this PC.'); go('community');
  },
  toLib: async el => { await call('community_to_library', el.dataset.id); toast('Community config added to your library.'); go('library'); },
  delCom: async el => { if (await ask('Delete setup', 'Delete this setup from your local Community?', 'Delete')) { await call('community_delete', el.dataset.id); go('community'); } },
  pickGame: async () => { const p = await call('pick_folder'); if (p) $('#p-game').value = p; },
  pickSteam: async () => { const p = await call('pick_steam'); if (p) $('#p-steam').value = p; },
  detect: async () => {
    const d = await call('detect_paths'), s = $('#pstat');
    if (d.game) $('#p-game').value = d.game; if (d.steam) $('#p-steam').value = d.steam;
    if (s) s.textContent = d.game || d.steam ? 'Found ' + [d.steam && 'Steam', d.game && 'CS2'].filter(Boolean).join(' and ') + '. Press Verify & save.' : 'Nothing found. Choose the folders manually.';
  },
  savePaths: async () => { await call('save_paths', val('p-game'), val('p-steam')); await refresh(); $('#pstat').innerHTML = '<span class="ok">✓ CS2 and Steam verified. Settings saved.</span>'; status('CS2 and Steam verified. Settings saved.'); },
  motion: async el => { await call('set_motion', el.checked); S.reduce_motion = el.checked; document.body.toggleAttribute('data-reduce', el.checked); },
  proto: async () => { await call('register_protocol'); toast('Add to app reconnected.'); },
  saveUpd: async () => { S.update_repo = await call('save_update_settings', val('u-repo'), $('#u-auto').checked); S.update_auto = $('#u-auto').checked; $('#ustat').textContent = 'Repository saved. Check for updates.'; },
  chkUpd: async () => { await acts.saveUpd(); $('#ustat').textContent = 'Checking GitHub…'; await checkUpdate(true); },
  instUpd: async () => {
    if (!await ask('Install this update?', 'The update will be downloaded, verified and installed. The app will close and restart. Your library and configs will be kept.', 'Install & restart')) return;
    $('#ustat').textContent = 'Downloading and verifying the installer…'; await call('install_update');
  },
};
async function checkUpdate(manual) {
  try {
    const u = await call('check_update'), s = $('#ustat'), b = $('#u-inst');
    const text = u ? 'Available: v' + u.version + ' — install it below.' : 'You are up to date: v' + S.version;
    if (s) s.textContent = text; if (b) b.hidden = !u;
    if (u && !manual) toast('Update available: v' + u.version + '. Install it from Settings.');
  } catch (e) { if (manual) { const s = $('#ustat'); if (s) s.textContent = 'Update unavailable: ' + e.message; } }
}
document.addEventListener('click', e => { const el = e.target.closest('[data-act]'); if (el && el.dataset.act !== 'motion') { e.preventDefault(); guard(() => acts[el.dataset.act](el)); } });
document.addEventListener('change', e => { if (e.target.dataset.act === 'motion') guard(() => acts.motion(e.target)); });
document.addEventListener('input', e => {
  const k = e.target.dataset.in; if (!k) return;
  if (k === 'q') { R.q = e.target.value; $('#plist').innerHTML = plist(players.filter(p => (p.name + ' ' + p.team + ' ' + p.role).toLowerCase().includes(R.q.toLowerCase()))); }
  if (k === 'lq') { R.lq = e.target.value; $('#llist').innerHTML = libRows(R.items, R.lq); }
  if (k === 'zoom') { lab.zoom = +e.target.value; $('#zv').textContent = lab.zoom; $('#lab').innerHTML = xhair(players.find(p => p.id === R.id).crosshair, lab.zoom); }
});
document.addEventListener('keydown', e => {
  if ((e.key === 'Escape' || (e.altKey && e.key === 'ArrowLeft')) && $('#modal').hidden) guard(back);
  if (e.key === 'Enter' && e.target.matches('.gamecard,.item,.pcard')) e.target.click();
});

/* ---------- start ---------- */
async function init() {
  api = window.pywebview.api;
  await guard(async () => {
    S = await call('state'); players = await call('players'); sel = new Set(S.games);
    sig = await call('library_sig');
    await render();
    const n = S.notice; if (n) { toast(n.text, !n.goto); if (n.goto) go(n.goto); }
    if (S.update_auto) setTimeout(() => checkUpdate(false), 3000);
    setInterval(() => guard(async () => {
      if (!S.intro_complete) return;
      const s = await call('library_sig');
      if (s !== sig) { sig = s; status('Library updated. A new or modified config is available.'); if (R.tab === 'library' && !R.sub) render(); }
    }), 2000);
  });
}
if (window.pywebview && window.pywebview.api) init(); else window.addEventListener('pywebviewready', init);
