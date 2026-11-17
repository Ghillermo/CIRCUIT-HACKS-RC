/* Hacks + Remix (tools/make_hr_app.py builds tools/hr_app.html with this and the two apps' data layers, SDT = the Tracks', SDR = the Rhythm's).
   Two panes; each opens a Tracks card (or a Tracks app snapshot: a folder with Tracks/), a Rhythm card (Rhythm/) or a plain folder of files.
   Samples, patterns and own-synth patches copy between them; across devices they are adapted (HR.* below, tested by tools/hr_app_test.html). */
(() => {
"use strict";
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
let LANG = (() => { try { const s = localStorage.getItem("hrapp.lang"); if (s === "es" || s === "en") return s; } catch (_) { /* no storage */ } return (navigator.language || "en").startsWith("es") ? "es" : "en"; })();
const T = (es, en) => LANG === "es" ? es : en;

// ================================================================ the adapters (no UI)
const FM_REC = 224, FM_AT = 4096, REC = 512;
const HR = {
  /* a Tracks note pattern -> a Rhythm pattern (over the destination's bytes): each step = its root (the lowest note on): its gate, micro-step (as the
     Rhythm's mask bit), velocity, tie; the step's probability; the settings (last, first, rate, direction, order); the Rhythm's lanes stay */
  t2rNote(tb, rbase) {
    const m = SDT.patParse(tb), r = SDR.patParse(rbase);
    r.steps = m.steps.map((st, s) => {
      const on = st.units.filter(u => u.on);
      if (!on.length) return Object.assign({}, r.steps[s], {on: false});
      const u = on.reduce((a, b) => b.note < a.note ? b : a);
      return {on: true, note: u.note, gate: Math.max(1, u.gate), mask: 1 << Math.min(5, u.micro), vel: u.vel || 100, prob: Math.min(7, st.prob), flip: 0xFF, tie: u.tie};
    });
    for (const k of ["last", "first", "rate", "dir", "order"]) r[k] = m[k];
    return SDR.patBuild(r, rbase);
  },
  /* a Rhythm pattern -> a Tracks note pattern: one note a step (its first micro-step); the others off; the Tracks' lanes stay */
  r2tNote(rb, tbase) {
    const m = SDR.patParse(rb), t = SDT.patParse(tbase);
    t.steps = t.steps.map((st, s) => {
      const r = m.steps[s], units = st.units.map(u => Object.assign({}, u, {on: false}));
      if (r.on) { let mi = 0; while (mi < 5 && !(r.mask >> mi & 1)) mi++; units[0] = {on: true, note: r.note, gate: r.gate || 6, tie: r.tie, micro: mi, vel: r.vel}; }
      return Object.assign({}, st, {prob: r.on ? r.prob : st.prob, units});
    });
    for (const k of ["last", "first", "rate", "dir", "order"]) t[k] = m[k];
    return SDT.patBuild(t, tbase);
  },
  /* a Tracks drum pattern (velocity + 0, probability + 32, flip + 64, micro mask + 96; settings + 0x80) -> a Rhythm pattern: a hit = its velocity,
     probability and micro mask at the Rhythm's own note (0x48); flips none (the sample numbers differ) */
  t2rDrum(tb, rbase) {
    const r = SDR.patParse(rbase);
    r.steps = r.steps.map((st, s) => tb[s] ? {on: true, note: 0x48, gate: 6, mask: tb[96 + s] || 1, vel: tb[s], prob: Math.min(7, tb[32 + s]), flip: 0xFF, tie: 0}
                                           : Object.assign({}, st, {on: false}));
    const S = 0x80;
    r.last = tb[S]; r.first = tb[S + 1]; r.rate = tb[S + 2]; r.dir = tb[S + 3]; r.order = tb[S + 7];
    return SDR.patBuild(r, rbase);
  },
  r2tDrum(rb, tbase) {
    const m = SDR.patParse(rb), b = tbase.slice(), S = 0x80;
    m.steps.forEach((st, s) => {
      if (st.on) { b[s] = st.vel || 100; b[32 + s] = st.prob; b[64 + s] = 0xFF; b[96 + s] = st.mask || 1; }
      else { b[s] = 0; b[96 + s] = 0; b[64 + s] = 0xFF; }
    });
    b[S] = m.last; b[S + 1] = m.first; b[S + 2] = m.rate; b[S + 3] = m.dir; b[S + 7] = m.order;
    return b;
  },
  /* a pattern from one device into a slot of the other: by the kinds */
  adaptPattern(src, srcKind, srcSlot, dstBase, dstKind, dstSlot) {
    if (srcKind === dstKind) return src;
    const tDrum = (k, n) => k === "tracks" && n >= 32;
    if (srcKind === "tracks") return tDrum(srcKind, srcSlot) ? HR.t2rDrum(src, dstBase) : HR.t2rNote(src, dstBase);
    return tDrum(dstKind, dstSlot) ? HR.r2tDrum(src, dstBase) : HR.r2tNote(src, dstBase);
  },
  /* the 8-operator FM: a Hacks custom patch (padding + record) <-> a Remix patch (the record alone, the same "FM8" 1 format) */
  fmOfCustom(pad) {
    if (!pad) return null;
    const f = SDT.fmGet(pad), rec = pad.length > SDT.PADN ? pad.subarray(SDT.PADN, SDT.PADN + FM_REC) : null;
    return f && f.ver === 3 && rec && SDT.fm8Get(rec) ? rec.slice() : null;
  },
  customOfFm(rec, name) { const p = SDT.fm8Get(rec); return p ? SDT.dx7Patch({name: name || "Remix", params: p}) : null; },
};
window.HR = HR;

/* ---- the Remix patches: Patches/NN_PATCHBANK.cpb of the pack, slot n in bank n >> 3 in Hacks' own places (the user, 2026-11-06: «Añade la opción
   a la app para pasar patches VA» -> «Copiar al pack del Rhythm»): the custom patch's padding (CTM1: the engine, its values, the name) at 512 (n & 7)
   + 340, the 8-operator FM record at 4096 + 512 (n & 7); the first 340 B of a record (the Tracks' Nova patch) stay 0xFF on the Rhythm.  So a Hacks
   patch of any engine (VA, VA-drum, granular, FM, wavetable ...) goes as it is, and a bank file reads the same on both.  A slot with only the FM
   record (written before) reads as an FM custom patch. */
const PSZ = 340;
const RFM = {
  size: 64,
  async banks(pack) {
    if (pack._fmb) return pack._fmb;
    const m = new Map(), d = await SDR.subdir(pack.dir, "Patches");
    if (d) for (const [n, h] of await SDR.entries(d)) { const r = /^(\d+)_PATCHBANK\.cpb$/i.exec(n); if (r && h.kind === "file") m.set(+r[1], {name: n, bytes: await SDR.readHandle(h)}); }
    return pack._fmb = m;
  },
  /* -> the custom patch (padding + FM record, as SDT.Custom.get), or null */
  async get(pl, n) {
    const e = (await RFM.banks(pl.pack)).get(n >> 3), r = REC * (n & 7), b = e ? e.bytes : new Uint8Array(0);
    const cut = (a, l) => b.subarray(Math.min(a, b.length), Math.min(a + l, b.length));
    const pad = new Uint8Array(SDT.PADN + FM_REC).fill(0xFF);
    pad.set(cut(r + PSZ, SDT.PADN)); pad.set(cut(FM_AT + r, FM_REC), SDT.PADN);
    if (SDT.ctmState(pad.subarray(0, SDT.PADN)) === "ok") return pad;
    const rec = pad.subarray(SDT.PADN);
    return SDT.fm8Get(rec) ? HR.customOfFm(rec.slice(), `Remix ${SDR.pad2(n)}`) : null;
  },
  async list(pl) {
    const out = [];
    for (let n = 0; n < RFM.size; n++) { const p = await RFM.get(pl, n); out.push({slot: n, empty: !p, name: p ? SDT.ctmName(p) : "", extra: p ? engineOf(p) : ""}); }
    return out;
  },
  /* pad = a custom patch (padding, then the FM record or nothing); the FM record written when there is one, or when the bank already reaches it */
  async put(pl, n, pad, ctx = {}) {
    const m = await RFM.banks(pl.pack), b = n >> 3, e = m.get(b), r = REC * (n & 7);
    const dir = await SDR.subdir(pl.pack.dir, "Patches", true);
    if (e && ctx.backup) await ctx.backup.file([pl.pack.folder, "Patches"], e.name, e.bytes);
    const rec = pad.length > SDT.PADN ? pad.subarray(SDT.PADN, SDT.PADN + FM_REC) : new Uint8Array(0);
    const old = e ? e.bytes : new Uint8Array(0), withFm = rec.some(x => x !== 0xFF) || old.length > FM_AT + r;
    const out = new Uint8Array(Math.max(old.length, r + PSZ + SDT.PADN, withFm ? FM_AT + r + FM_REC : 0)).fill(0xFF);
    out.set(old); out.set(pad.subarray(0, SDT.PADN), r + PSZ);
    if (withFm) { out.fill(0xFF, FM_AT + r, FM_AT + r + FM_REC); out.set(rec, FM_AT + r); }
    const name = e ? e.name : SDR.pad2(b) + "_PATCHBANK.cpb";
    await SDR.writeFile(dir, name, out); m.set(b, {name, bytes: out});
  },
};
const algName = p => { const a = p[200]; return a < 16 ? `FM · ${T("algoritmo", "algorithm")} ${a + 1}` : a < 48 ? `FM · DX7 ${a - 15}` : `FM · 8 op ${a - 47}`; };
/* a custom patch's engine (the padding's flags, as the Hacks app's engineName; the FM with its algorithm) */
const ENGINES = {1: ["Entrada de línea", "Line in"], 3: ["VA", "VA"], 7: ["VA-drum", "VA-drum"], 15: ["VA-drum", "VA-drum"], 11: ["Granular", "Granular"],
                 9: ["Muestra", "Sample"], 5: ["Secuenciador de efectos", "FX sequencer"]};
function engineOf(pad) {
  const f = pad[4], k = f & 1 ? f & 15 : 0, fm = SDT.fmGet(pad);
  if (k === 3 && fm && fm.on) { const x = fm.ver === 3 && pad.length > SDT.PADN ? SDT.fm8Get(pad.subarray(SDT.PADN)) : null; return x ? algName(x) : "FM"; }
  if (k === 3 && pad[150] === 0xB7 && pad[151] === 1) return "Wavetable";
  return ENGINES[k] ? T(ENGINES[k][0], ENGINES[k][1]) : T("Apagado", "Off");
}
window.RFM = RFM;

// ================================================================ the panes
const TABS = [["samples", "Samples", "Samples"], ["patterns", "Patrones", "Patterns"], ["fm", "Parches", "Patches"], ["projects", "Proyectos", "Projects"], ["packs", "Packs", "Packs"]];
const state = {tab: "samples", busy: false, backup: null, view: "both", fwT: "auto", fwR: "auto", fwdev: "hacks"};
try { const v = localStorage.getItem("hrapp.view"); if (v === "hacks" || v === "remix" || v === "firmware") state.view = v; } catch (_) { /* no storage */ }
/* (2026-11-13, the user: «add Remix to the master app … under firmware options», «Both») the firmware of each device: automatic (no device here:
   everything), stock only, Hacks / Remix.  The Tracks one is the Hacks app's own setting (sdapp.fw: its view follows it); stock only = no own patches
   on that side (the Tracks' custom patches are Hacks', the Rhythm's patches are Remix's) */
try {
  const t = localStorage.getItem("sdapp.fw"); if (t === "stock" || t === "hacks") state.fwT = t;
  const r = localStorage.getItem("hrapp.rfw"); if (r === "stock" || r === "remix") state.fwR = r;
  const d = localStorage.getItem("hrapp.fwdev"); if (d === "hacks" || d === "remix") state.fwdev = d;
} catch (_) { /* no storage */ }
const fwOK = kind => kind === "rhythm" ? state.fwR !== "stock" : kind === "tracks" ? state.fwT !== "stock" : true;

/* ---- the views: «Entre los dos» (the panes below) or one device's own app whole (its packs, editors, the device over USB, snapshot / restore ...;
   window.HR_APPS from make_hr_app.py), each in a same-origin frame made the first time it is shown and kept */
const VIEWS = [["both", "Entre los dos", "Between the two"], ["hacks", "Hacks · Circuit Tracks", "Hacks · Circuit Tracks"], ["remix", "Remix · Circuit Rhythm", "Remix · Circuit Rhythm"],
               ["editor", "Editor de patches", "Patch editor"], ["firmware", "Firmware", "Firmware"]];
/* (2026-11-13) the Firmware view: the two installers, Hacks for the Circuit Tracks (tools/rc_uploader.html) and Remix for the Circuit Rhythm (the
   published Remix app opened on its Firmware tab), each in its own frame (fwhacks / fwremix) */
const FWDEV = [["hacks", "Circuit Tracks · Hacks", "Circuit Tracks · Hacks"], ["remix", "Circuit Rhythm · Remix", "Circuit Rhythm · Remix"]];
const frames = {};
/* (2026-11-10) the patch editor (tools/patch_editor.html: the own synth's 33 values sent live over MIDI) is a view too; «Editar» opens the chosen
   patch of a pane in it, and its «Guardar en …» writes it back to that slot */
function frameReady(v) {
  const f = frames[v];
  return new Promise(res => { const ok = () => f.contentWindow && f.contentWindow.PE ? res(f.contentWindow) : setTimeout(ok, 50); ok(); });
}
function showView() {
  const app = state.view !== "both";
  document.body.classList.toggle("appmode", app);
  const box = $("appview"); box.hidden = !app;
  const fw = state.view === "firmware", key = fw ? "fw" + state.fwdev : state.view;
  const nav = $("fwnav"); nav.hidden = !fw;
  nav.innerHTML = FWDEV.map(d => `<button type="button" data-fwdev="${d[0]}" class="${d[0] === state.fwdev ? "on" : ""}">${esc(T(d[1], d[2]))}</button>`).join("");
  for (const [k, f] of Object.entries(frames)) f.hidden = k !== key;
  if (app && !frames[key] && window.HR_APPS) {
    const f = document.createElement("iframe");
    f.setAttribute("allow", "midi; clipboard-write");
    f.title = ({hacks: "Hacks", remix: "Remix", editor: T("Editor de patches", "Patch editor"), fwhacks: T("Instalador de Hacks", "Hacks installer"), fwremix: T("Instalador de Remix", "Remix installer")})[key];
    if (key === "fwremix") f.onload = () => { try { const b = f.contentDocument.querySelector('[data-tab="firmware"]'); if (b) b.click(); } catch (_) { /* not reachable */ } };
    f.srcdoc = window.HR_APPS[key === "fwhacks" ? "hinst" : key === "fwremix" ? "remix" : key]; box.append(f); frames[key] = f;
  }
  $("views").innerHTML = VIEWS.map(v => `<button type="button" data-view="${v[0]}" class="${v[0] === state.view ? "on" : ""}">${esc(T(v[1], v[2]))}</button>`).join("");
}
window.HRFRAMES = frames;
const panes = [0, 1].map(i => ({i, el: $("pane" + i), kind: null, card: null, dir: null, packSlot: null, sess: null, items: [], sel: new Set()}));
panes[0].other = panes[1]; panes[1].other = panes[0];
const core = p => p.kind === "rhythm" ? SDR : SDT;
const pack = p => p.card && p.packSlot !== null ? p.card.pack(p.packSlot) : null;
const place = p => { const k = pack(p); return k ? {pack: k, sess: p.sess} : null; };

function log(t, cls) { const l = $("log"), d = document.createElement("div"); d.textContent = new Date().toTimeString().slice(0, 8) + "  " + t; if (cls) d.className = cls; l.append(d); l.scrollTop = l.scrollHeight; }
function ask(title, html, buttons) {
  const d = $("dlg");
  d.innerHTML = `<h3>${esc(title)}</h3><div class="body">${html}</div><div class="btns">${buttons.map((b, i) => `<button type="button" data-i="${i}" class="${b[2] || ""}">${esc(b[0])}</button>`).join("")}</div>`;
  return new Promise(res => { d.onclick = e => { const i = e.target.dataset ? e.target.dataset.i : undefined; if (i === undefined) return; d.close(); res(buttons[+i][1]); }; d.oncancel = () => res(null); d.showModal(); });
}
const say = (t, h) => ask(t, h, [["OK", true, "pri"]]);
async function run(title, fn) {
  if (state.busy) return; state.busy = true; log(title + " …");
  const prog = $("prog"); prog.hidden = false; prog.removeAttribute("value");
  const ctx = {backup: state.backup, progress: (name, i, n) => { prog.max = n; prog.value = i; }};
  try { await fn(ctx); log(title + ": " + T("hecho", "done"), "ok"); } catch (e) { log(title + ": " + (e && e.message || e), "bad"); console.error(e); }
  prog.hidden = true; state.busy = false;
  await renderAll();
}

// the kind of a folder: a Tracks card / snapshot (Tracks/ or its packs' sessions 0x2740C), a Rhythm one (Rhythm/ or 0x29484), else plain files
async function kindOf(dir) {
  const has = async n => { try { await dir.getDirectoryHandle(n); return true; } catch (_) { return false; } };
  if (await has("Tracks")) return "tracks";
  if (await has("Rhythm")) return "rhythm";
  for await (const [n, h] of dir.entries()) {
    if (h.kind !== "directory" || !/^\d\d_/.test(n)) continue;
    try { const s = await h.getDirectoryHandle("Sessions"); for await (const [, f] of s.entries()) if (f.kind === "file") { const z = (await f.getFile()).size; if (z === SDT.SESS_SIZE) return "tracks"; if (z === SDR.SESS_SIZE) return "rhythm"; } } catch (_) { /* no sessions */ }
    try { const s = await h.getDirectoryHandle("PCM"); for await (const [f] of s.entries()) { if (/^\d\d\d_/.test(f)) return "rhythm"; if (/^\d\d_/.test(f)) return "tracks"; } } catch (_) { /* no samples */ }
  }
  return "folder";
}
async function openPane(p, dir) {
  const k = await kindOf(dir);
  p.kind = k; p.dir = dir; p.card = null; p.packSlot = null; p.sess = null; p.sel.clear();
  if (k !== "folder") { p.card = await (k === "rhythm" ? SDR : SDT).Card.open(dir); p.packSlot = p.card.packs.length ? p.card.packs[0].slot : null; }
  log(`${T("Abierta", "Opened")}: ${dir.name} (${kindLabel(k)})`);
  await renderAll();
}
const kindLabel = k => ({tracks: "Hacks · Circuit Tracks", rhythm: "Remix · Circuit Rhythm", folder: T("carpeta", "folder"), demos: T("parches demo", "demo patches")})[k] || "";
/* (2026-11-10) the demo patches (docs/patches, tools/make_examples.py: 33 classic sounds + the 48 FM instruments; window.HR_DEMOS from make_hr_app.py)
   as a read-only source of the Patches tab: copy them into a Tracks or Rhythm card, a folder, or open them in the editor */
const demoBytes = d => { const t = atob(d.b64), u = new Uint8Array(t.length); for (let i = 0; i < t.length; i++) u[i] = t.charCodeAt(i); return u; };
async function openDemos(p) {
  p.kind = "demos"; p.dir = {name: T("Parches demo", "Demo patches")}; p.card = null; p.packSlot = null; p.sess = null; p.sel.clear();
  if (state.tab !== "fm") state.tab = "fm";
  log(T("Abiertos los parches demo", "Demo patches opened") + ` (${(window.HR_DEMOS || []).length})`);
  await renderAll();
}
/* the colour the device shows a custom patch in (its engine: MIDI 1 / 2's Preset slots), SDT.customColour */
function patchRgb(pad) {
  if (!pad || SDT.ctmState(pad.subarray(0, SDT.PADN)) !== "ok") return null;
  return SDT.customColour(pad[4], SDT.fmGet(pad), pad[150] === 0xB7 && pad[151] === 1).rgb;
}

// ---- the items of a pane in the current tab: {slot, empty, name, extra}
const FOLDER_EXT = {samples: /\.wav$/i, patterns: /\.(ctpat|rmpat)$/i, fm: /\.(fm8|ctm)$/i, projects: /\.ncs$/i, packs: /^$/};
async function folderFiles(p) {
  const out = [];
  for await (const [n, h] of p.dir.entries()) if (h.kind === "file" && FOLDER_EXT[state.tab].test(n)) out.push({n, h});
  out.sort((a, b) => a.n.localeCompare(b.n));
  return out;
}
async function loadItems(p) {
  const tab = state.tab;
  if (p.kind === "demos") return tab !== "fm" ? [] : (window.HR_DEMOS || []).map((d, i) => { const pad = demoBytes(d); return {slot: i, empty: false, name: d.name.slice(3), extra: engineOf(pad), rgb: patchRgb(pad), demo: d}; });
  if (p.kind === "folder") {
    const F = (await folderFiles(p)).map((f, i) => ({slot: i, empty: false, name: f.n, file: f}));
    if (tab === "fm") for (const x of F) if (/\.ctm$/i.test(x.name)) { try { const pad = new Uint8Array(await (await x.file.h.getFile()).arrayBuffer()); x.rgb = patchRgb(pad); if (x.rgb) x.extra = engineOf(pad); } catch (_) { /* unreadable */ } }
    return F;
  }
  p.fwOff = tab === "fm" && !fwOK(p.kind);                  // (2026-11-13) own patches need Hacks / Remix: nothing with «stock only»
  if (p.fwOff) return [];
  if (tab === "packs") {                                    // (2026-11-13) the card's pack numbers: 0..30, as the device's packs 1..31
    if (!p.card) return [];
    const out = [];
    for (let n = 0; n < core(p).NPACKS; n++) {
      const k = p.card.pack(n);
      if (!k) { out.push({slot: n, empty: true, name: ""}); continue; }
      const i = await core(p).packInfo(k);
      out.push({slot: n, empty: false, name: k.name, extra: i ? `${i.sessions} ${T("proy.", "proj.")} · ${i.samples} ${T("samples", "samples")}` : ""});
    }
    return out;
  }
  const pl = place(p); if (!pl) return [];
  if (tab === "samples") return (p.kind === "rhythm" ? SDR.Samples : SDT.Drums).list(pl);
  if (tab === "projects") return core(p).Projects.list(pl);
  if (tab === "patterns") {
    const m = await core(p).sessionsOf(pl.pack);
    if (p.sess === null || !m.has(p.sess)) p.sess = m.size ? [...m.keys()][0] : null;
    if (p.sess === null) return [];
    const TN = core(p).TRACK_NAME;
    return (await core(p).Patterns.list({pack: pl.pack, sess: p.sess})).map(x => Object.assign(x, {name: `${TN[x.slot >> 3]} · ${(x.slot & 7) + 1}`, extra: x.empty ? "" : `${x.notes} ${T("notas", "notes")}${x.lanes ? `, ${x.lanes} ${T("carriles", "lanes")}` : ""}`}));
  }
  if (p.kind === "rhythm") { const L = await RFM.list(pl); for (const x of L) if (!x.empty) x.rgb = patchRgb(await RFM.get(pl, x.slot)); return L; }
  const L = await SDT.Custom.list(pl);
  for (const x of L) if (!x.empty && !x.bad) { const pad = await SDT.Custom.get(pl, x.slot); x.extra = engineOf(pad); x.rgb = patchRgb(pad); }
  return L.map(x => Object.assign(x, {empty: x.empty || x.bad, name: x.name || ""}));
}
async function getItem(p, n) {                              // -> {kind, name, bytes / pad / rec}
  const tab = state.tab, it = p.items[n];
  if (p.kind === "demos") { const pad = demoBytes(it.demo); return {name: it.name, pad, rec: HR.fmOfCustom(pad)}; }
  if (p.kind === "folder") {
    const b = new Uint8Array(await (await it.file.h.getFile()).arrayBuffer()), nm = it.name.replace(/\.[^.]+$/, "");
    if (tab === "samples") return {name: nm, bytes: b};
    if (tab === "projects") return {name: nm.replace(/^\d\d_/, ""), bytes: b, from: b.length >= SDR.SESS_SIZE && b.length !== SDT.SESS_SIZE && !(b.length > SDT.SESS_SIZE && SDT.latin(b, SDT.SESS_SIZE, 4) === "XLN1") ? "rhythm" : "tracks"};
    if (tab === "patterns") return {name: nm, bytes: b, from: /\.rmpat$/i.test(it.name) ? "rhythm" : "tracks", slot: b.length === SDT.patSize(32) ? 32 : 0};
    return /\.fm8$/i.test(it.name) ? {name: nm, rec: b.subarray(0, FM_REC)} : {name: nm, rec: HR.fmOfCustom(b), pad: b};
  }
  if (tab === "packs") return {name: it.name, pack: p.card.pack(n), from: p.kind};
  const pl = place(p);
  if (tab === "samples") return (p.kind === "rhythm" ? SDR.Samples : SDT.Drums).get(pl, n);
  if (tab === "projects") { const x = await core(p).Projects.get(pl, n); return x ? {name: x.name, bytes: x.bytes, from: p.kind} : null; }
  if (tab === "patterns") return {name: it.name, bytes: await core(p).Patterns.get({pack: pl.pack, sess: p.sess}, n), from: p.kind, slot: n};
  if (p.kind === "rhythm") { const pad = await RFM.get(pl, n); return pad ? {name: SDT.ctmName(pad) || `Remix ${SDR.pad2(n)}`, pad, rec: HR.fmOfCustom(pad)} : null; }
  const pad = await SDT.Custom.get(pl, n); return pad ? {name: SDT.ctmName(pad) || `Hacks ${SDT.pad2(n)}`, pad, rec: HR.fmOfCustom(pad)} : null;
}
async function putItem(q, n, x, ctx) {                       // into pane q's slot n (a folder: a new file)
  const tab = state.tab;
  if (q.kind === "demos") throw new Error(T("los parches demo son de solo lectura", "the demo patches are read-only"));
  if (tab === "fm" && !fwOK(q.kind)) throw new Error(q.kind === "rhythm" ? T("los parches del Rhythm necesitan el firmware Remix (selector Firmware)", "the Rhythm's patches need the Remix firmware (Firmware selector)")
                                                                         : T("los parches custom del Tracks necesitan el firmware Hacks (selector Firmware)", "the Tracks' custom patches need the Hacks firmware (Firmware selector)"));
  if ((tab === "packs" || tab === "projects") && q.kind !== "folder" && x.from !== q.kind)
    throw new Error(T("un proyecto o un pack solo va a una tarjeta del mismo aparato", "a project or a pack only goes to a card of the same device"));
  if (tab === "packs") {
    if (q.kind === "folder") throw new Error(T("un pack va a una tarjeta, no a una carpeta de ficheros", "a pack goes to a card, not to a folder of files"));
    return core(q).copyPack(x.pack, q.card, n, ctx);
  }
  if (q.kind === "folder") {
    const ext = tab === "samples" ? ".wav" : tab === "projects" ? ".ncs" : tab === "patterns" ? (x.from === "rhythm" ? ".rmpat" : ".ctpat") : x.pad ? ".ctm" : ".fm8";
    const data = tab === "fm" ? (x.pad || x.rec) : x.bytes;
    let name = (x.name || "item").replace(/[\\/:*?"<>|]/g, "_").trim() + ext;
    for (let k = 2; await q.dir.getFileHandle(name).then(() => true, () => false); k++) name = name.replace(/( \d+)?(\.[^.]+)$/, ` ${k}$2`);
    await SDT.writeFile(q.dir, name, data); return;
  }
  const pl = place(q);
  if (tab === "samples") return (q.kind === "rhythm" ? SDR.Samples : SDT.Drums).put(pl, n, {name: x.name, bytes: x.bytes}, ctx);
  if (tab === "projects") return core(q).Projects.put(pl, n, {name: x.name, bytes: x.bytes}, ctx);
  if (tab === "patterns") {
    const P = core(q).Patterns, ql = {pack: pl.pack, sess: q.sess}, base = await P.get(ql, n);
    if (x.from === "tracks" && q.kind === "tracks" && (x.slot >= 32) !== (n >= 32)) throw new Error(T("un patrón de drums solo va a una pista de drums", "a drum pattern only goes to a drum track"));
    const data = HR.adaptPattern(x.bytes, x.from, x.slot, base, q.kind, n);
    if (data.length !== base.length) throw new Error(T("tamaño de patrón distinto", "pattern size differs"));
    await P.putRaw(ql, n, data); await P.flush(ql, ctx); return;
  }
  const pad = x.pad && SDT.ctmState(x.pad.subarray(0, SDT.PADN)) === "ok" ? x.pad : x.rec ? HR.customOfFm(x.rec, x.name) : null;
  if (!pad) throw new Error(T(`${x.name}: no es un parche`, `${x.name}: not a patch`));
  if (q.kind === "rhythm") return RFM.put(pl, n, pad, ctx);
  return SDT.Custom.put(pl, n, pad, ctx);
}

async function copyAct(p) {
  const q = p.other, from = [...p.sel].sort((a, b) => a - b).filter(n => p.items[n] && !p.items[n].empty);
  if (!from.length) return say(T("Nada elegido", "Nothing chosen"), T("Elige filas con contenido.", "Choose rows with content."));
  if (!q.kind) return say(T("Falta el destino", "No target"), T("Abre una carpeta en el otro lado.", "Open a folder on the other side."));
  if (q.kind === "demos") return say(T("Solo lectura", "Read-only"), T("Los parches demo no se pueden cambiar: abre una tarjeta o una carpeta en el otro lado.", "The demo patches cannot be changed: open a card or a folder on the other side."));
  if (state.tab === "patterns" && q.kind !== "folder" && q.sess === null) return say(T("Sin proyecto", "No project"), T("El otro lado no tiene un proyecto elegido.", "The other side has no project chosen."));
  let to = [];
  if (q.kind !== "folder") {
    const start = q.sel.size ? Math.min(...q.sel) : q.items.findIndex(x => x.empty);
    if (start < 0) return say(T("No cabe", "It does not fit"), T("Elige el hueco de destino en el otro lado.", "Choose the target slot on the other side."));
    to = from.map((_, i) => start + i);
    if (to[to.length - 1] >= q.items.length) return say(T("No cabe", "It does not fit"), T("No hay huecos suficientes desde el elegido.", "Not enough slots from the chosen one."));
    const hit = to.filter(n => !q.items[n].empty);
    if (hit.length && state.tab === "packs") return say(T("Huecos ocupados", "Slots in use"), T("El destino de un pack tiene que estar libre: elimina antes el que hay o elige otro número.", "A pack's target must be free: delete what is there first or choose another number."));
    if (hit.length && !await ask(T("Huecos ocupados", "Slots in use"), `<p>${hit.map(n => esc(`${n} ${q.items[n].name}`)).join("<br>")}</p>`, [[T("Sobrescribir", "Overwrite"), true, "dng"], [T("Cancelar", "Cancel"), false]])) return;
  }
  const across = p.kind !== q.kind && !["folder", "demos"].includes(p.kind) && q.kind !== "folder";
  await run(`${T("Copiar", "Copy")} ${from.length}${across ? " · " + T("adaptado", "adapted") : ""}`, async ctx => {
    for (let i = 0; i < from.length; i++) {
      const x = await getItem(p, from[i]);
      if (!x) continue;
      try { await putItem(q, to[i], x, ctx); } catch (e) { log(`${x.name}: ${e.message || e}`, "bad"); }
      ctx.progress("", i + 1, from.length);
    }
    for (const k of [p, q]) { const pk = pack(k); if (pk) { pk._samples = null; pk._banks = null; pk._fmb = null; pk._info = null; pk._sessions = null; } }
  });
  q.sel.clear();
}

/* (2026-11-15, the user: «add the starter packs as an option/shortcut inside the sd app, add an option to upload … to more than one pack at once»)
   «Sonidos de partida…» on a card pane of the Patches tab: a set of the demo patches (the 48 FM starters = the instruments the firmware no longer
   carries since Beta 5.58, the 33 classics, or all 81) into the custom-patch slots of one or several packs of that card from a start slot;
   «A varios packs…» next to Copy (Patches and Samples): the chosen rows into the same slots of several packs of the other side's card.
   opts = {set, packs, start} (the tests) skips the dialog. */
const DEMO_SETS = () => { const n = (window.HR_DEMOS || []).length; return [["fm", T("Sonidos de partida del FM (48)", "FM starter sounds (48)"), 33, n], ["classic", T("Sonidos clásicos (33)", "Classic sounds (33)"), 0, 33], ["all", T("Todos los parches demo", "All the demo patches") + ` (${n})`, 0, n]]; };
function packChecks(card, chosen) {
  return `<p class="dim" style="margin-bottom:4px">${T("Packs de destino", "Target packs")}</p><div style="max-height:150px;overflow:auto;margin-bottom:8px">` +
    card.packs.map(x => `<label style="display:block"><input type="checkbox" data-pk="${x.slot}"${x.slot === chosen ? " checked" : ""}> ${SDT.pad2(x.slot)} ${esc(x.name)}</label>`).join("") + "</div>";
}
async function toPacks(q, packs, start, items, title) {        // items: getters -> {name, pad / rec / bytes}; into each pack's slots start.. (the current tab)
  const was = q.packSlot; let done = 0, skipped = 0;
  await run(title, async ctx => {
    for (const pk of packs) {
      q.packSlot = pk; let cap = 64;
      try { cap = (await loadItems(q)).length || cap; } catch (_) { /* keep 64 */ }
      for (let i = 0; i < items.length; i++) {
        const n = start + i;
        if (n >= cap) { skipped++; continue; }
        const x = await items[i]();
        if (!x) { skipped++; continue; }
        try { await putItem(q, n, x, ctx); done++; } catch (e) { log(`${SDT.pad2(pk)} · ${SDT.pad2(n)} ${x.name}: ${e.message || e}`, "bad"); skipped++; }
        ctx.progress(SDT.pad2(pk), done + skipped, items.length * packs.length);
      }
      const k = q.card.pack(pk); if (k) { k._samples = null; k._banks = null; k._fmb = null; k._info = null; k._sessions = null; }
    }
  });
  q.packSlot = was; q.sel.clear();
  const msg = T(`${done} escritos en ${packs.length} pack(s)`, `${done} written into ${packs.length} pack(s)`) + (skipped ? T(`, ${skipped} saltados (sin hueco o con error)`, `, ${skipped} skipped (no slot or an error)`) : "");
  if (skipped) log(msg, "bad"); else log(msg);
  await renderAll();
}
async function loadDemosAct(p, opts) {
  if (!p.card || !fwOK(p.kind)) return say(T("Sin tarjeta", "No card"), T("Abre una tarjeta del Tracks o del Rhythm (con el firmware Hacks / Remix: los parches custom).", "Open a Tracks or Rhythm card (with the Hacks / Remix firmware: the custom patches)."));
  const sets = DEMO_SETS(); let set = "fm", packs = [p.packSlot], start = 0;
  if (!opts) {
    const pr = ask(T("Sonidos de partida", "Starter sounds"),
      `<p>${T("Los parches demo de la app en los huecos de parches custom de los packs elegidos: los sonidos de partida del FM ya no van en el firmware (desde la Beta 5.58).", "The app's demo patches into the custom-patch slots of the chosen packs: the FM starter sounds are no longer in the firmware (since Beta 5.58).")}</p>` +
      `<p><label>${T("Juego", "Set")} <select data-ds>${sets.map(s => `<option value="${s[0]}">${esc(s[1])}</option>`).join("")}</select></label></p>` +
      `<p><label>${T("Desde el hueco", "From slot")} <select data-dt>${Array.from({length: 64}, (_, i) => `<option value="${i}">${SDT.pad2(i)}</option>`).join("")}</select></label></p>` +
      packChecks(p.card, p.packSlot) + `<p class="dim" data-dw></p>`,
      [[T("Subir", "Upload"), true, "pri"], [T("Cancelar", "Cancel"), false]]);
    const D = $("dlg"), ds = D.querySelector("[data-ds]"), dt = D.querySelector("[data-dt]"), dw = D.querySelector("[data-dw]"), go = D.querySelector('[data-i="0"]');
    const upd = () => {
      const s = sets.find(x => x[0] === ds.value), n = s[3] - s[2], st = +dt.value, cnt = D.querySelectorAll("[data-pk]:checked").length, over = Math.max(0, st + n - 64);
      dw.textContent = T(`${n} parches × ${cnt} pack(s), huecos ${SDT.pad2(st)}-${SDT.pad2(Math.min(63, st + n - 1))}${over ? ` (${over} no caben)` : ""}; los huecos ocupados se sustituyen${state.backup ? " (con copia antes)" : ""}.`,
                         `${n} patches × ${cnt} pack(s), slots ${SDT.pad2(st)}-${SDT.pad2(Math.min(63, st + n - 1))}${over ? ` (${over} do not fit)` : ""}; slots in use are replaced${state.backup ? " (a backup first)" : ""}.`);
      go.disabled = !cnt;
    };
    D.addEventListener("change", upd); upd();
    const ok = await pr; D.removeEventListener("change", upd);
    if (!ok) return;
    set = ds.value; start = +dt.value; packs = [...D.querySelectorAll("[data-pk]:checked")].map(x => +x.dataset.pk);
  } else { set = opts.set || set; packs = opts.packs || packs; start = opts.start || 0; }
  const s = sets.find(x => x[0] === set);
  if (!s || !packs.length) return;
  const demos = (window.HR_DEMOS || []).slice(s[2], s[3]).map(d => async () => { const pad = demoBytes(d); return {name: d.name.slice(3), pad, rec: HR.fmOfCustom(pad)}; });
  state.tab = "fm";
  await toPacks(p, packs, start, demos, `${T("Sonidos de partida", "Starter sounds")} (${s[1]}) → ${packs.length} pack(s)`);
}
async function multiCopyAct(p, opts) {
  const q = p.other, from = [...p.sel].sort((a, b) => a - b).filter(n => p.items[n] && !p.items[n].empty);
  if (!["fm", "samples"].includes(state.tab)) return say(T("Parches y samples", "Patches and samples"), T("A varios packs a la vez: en las pestañas Parches y Samples.", "To several packs at once: in the Patches and Samples tabs."));
  if (!from.length) return say(T("Nada elegido", "Nothing chosen"), T("Elige filas con contenido.", "Choose rows with content."));
  if (!q.card) return say(T("Falta el destino", "No target"), T("Abre una tarjeta en el otro lado.", "Open a card on the other side."));
  let packs = [q.packSlot], start = q.sel.size ? Math.min(...q.sel) : Math.max(0, q.items.findIndex(x => x.empty));
  if (!opts) {
    const pr = ask(T("A varios packs", "To several packs"),
      `<p>${from.length} ${T("filas elegidas → los mismos huecos de cada pack elegido", "chosen rows → the same slots of each chosen pack")}.</p>` +
      `<p><label>${T("Desde el hueco", "From slot")} <select data-mt>${q.items.map((x, i) => `<option value="${i}"${i === start ? " selected" : ""}>${SDT.pad2(x.slot)} ${x.empty ? T("(libre)", "(free)") : esc(x.name)}</option>`).join("")}</select></label></p>` +
      packChecks(q.card, q.packSlot) + `<p class="dim">${T("Los huecos ocupados se sustituyen", "Slots in use are replaced")}${state.backup ? T(" (con copia antes)", " (a backup first)") : ""}.</p>`,
      [[T("Copiar", "Copy"), true, "pri"], [T("Cancelar", "Cancel"), false]]);
    const D = $("dlg"), mt = D.querySelector("[data-mt]"), go = D.querySelector('[data-i="0"]');
    const upd = () => { go.disabled = !D.querySelectorAll("[data-pk]:checked").length; };
    D.addEventListener("change", upd); upd();
    const ok = await pr; D.removeEventListener("change", upd);
    if (!ok) return;
    start = +mt.value; packs = [...D.querySelectorAll("[data-pk]:checked")].map(x => +x.dataset.pk);
  } else { packs = opts.packs || packs; start = opts.start !== undefined ? opts.start : start; }
  if (!packs.length) return;
  await toPacks(q, packs, start, from.map(n => () => getItem(p, n)), `${T("Copiar", "Copy")} ${from.length} → ${packs.length} pack(s)`);
}

/* «Editar»: the chosen patch into the editor view; a slot of a card (or a .ctm of a folder) gets «Guardar en …», a demo patch only the editor's own .ctm */
async function editAct(p) {
  const n = p.sel.size === 1 ? [...p.sel][0] : null, it = n === null ? null : p.items[n];
  if (!it || it.empty) return say(T("Nada elegido", "Nothing chosen"), T("Elige un parche (una fila con contenido).", "Choose a patch (a row with content)."));
  const x = await getItem(p, n), pad = x && x.pad && SDT.ctmState(x.pad.subarray(0, SDT.PADN)) === "ok" ? x.pad : x && x.rec ? HR.customOfFm(x.rec, x.name) : null;
  if (!pad) return say(T("No es un parche", "Not a patch"), T("Solo se editan parches del sinte propio (.ctm).", "Only own-synth patches (.ctm) can be edited."));
  const label = p.kind === "demos" ? null : p.kind === "folder" ? it.name : `${p.kind === "rhythm" ? "Remix" : "Hacks"} ${SDT.pad2(pack(p).slot)} · ${SDT.pad2(it.slot)}`;
  const save = p.kind === "demos" ? null : async (bytes, name) => {
    const b = Uint8Array.from(bytes), ctx = {backup: state.backup};
    if (name !== undefined) { SDT.ctmSetName(b, name); SDT.ctmSum(b); }
    if (p.kind === "folder") await SDT.writeFile(p.dir, it.name, b);
    else if (p.kind === "rhythm") { const pk = pack(p); pk._fmb = null; await RFM.put(place(p), it.slot, b, ctx); pk._fmb = null; }
    else { const pk = pack(p); pk._banks = null; await SDT.Custom.put(place(p), it.slot, b, ctx); pk._banks = null; }
    log(`${T("Guardado en", "Saved to")} ${label}`, "ok");
  };
  state.view = "editor"; try { localStorage.setItem("hrapp.view", "editor"); } catch (_) { /* none */ }
  showView();
  const w = await frameReady("editor");
  w.PE.openFrom({bytes: pad, name: x.name, label, save});
}

/* (2026-11-13, moved here from the Hacks app: «el trabajo de SD app se destinan a hr») Packs: «Duplicar…» (a copy in a free number of the same card,
   another name on the Tracks) and «Pack nuevo…» (Tracks: SDT.newPack, empty or with the banks and samples of a pack of the card); Projects: «Proyecto
   vacío…» (Tracks: SDT.projectEmpty, the sounds of another project of the pack without notes, scenes or chains) */
async function newPackAct(p, dup) {
  const card = p.card, C = core(p), tracks = p.kind === "tracks";
  if (!card) return say(T("Nada abierto", "Nothing open"), T("Abre una tarjeta del Tracks o del Rhythm.", "Open a Tracks or Rhythm card."));
  const sel = [...p.sel].filter(n => p.items[n] && !p.items[n].empty), src = sel.length ? card.pack(sel[0]) : null;
  if (dup && (sel.length !== 1 || !src)) return say(T("Un solo pack", "One pack only"), T("Elige el pack que quieres duplicar.", "Choose the pack to duplicate."));
  if (!dup && !tracks) return say(T("Solo en el Tracks", "Tracks only"), T("El pack nuevo es de las tarjetas del Tracks.", "The new pack is for Tracks cards."));
  const free = []; for (let n = 0; n < C.NPACKS; n++) if (!card.pack(n)) free.push(n);
  if (!free.length) return say(T("No cabe", "It does not fit"), T("La tarjeta ya tiene todos los packs: elimina alguno antes.", "The card already has every pack: delete one first."));
  const sel0 = [...p.sel].find(n => p.items[n] && p.items[n].empty), start = sel0 !== undefined ? sel0 : free[0];
  const max = SDT.NAME_RULE.packs.max, cur = dup ? src.name : "New Pack";
  const opts = [["-1", T("Ninguno: pack vacío", "None: an empty pack")], ...card.packs.map(x => [String(x.slot), x.folder])];
  const pr = ask(dup ? T("Duplicar pack", "Duplicate pack") : T("Pack nuevo", "New pack"),
    (dup ? `<p>${esc(src.folder)}</p>` : "") +
    (tracks ? `<p><label>${T("Nombre", "Name")} <input type="text" data-np maxlength="${max}" spellcheck="false" style="width:100%" value="${esc(cur)}"></label></p>` : "") +
    `<p><label>${T("Número", "Number")} <select data-nn>${free.map(n => `<option value="${n}"${n === start ? " selected" : ""}>${SDT.pad2(n)} · Pack ${n + 1}</option>`).join("")}</select></label></p>` +
    (dup ? `<p class="dim">${T("Una copia exacta: proyectos, patches y samples; los proyectos apuntan a los samples y patches por su número y suenan igual.", "An exact copy: projects, patches and samples; the projects point at samples and patches by number and sound the same.")}</p>`
         : `<p><label>${T("Patches y samples de", "Patches and samples from")} <select data-ns>${opts.map(([v, l]) => `<option value="${v}"${src && v === String(src.slot) ? " selected" : ""}>${esc(l)}</option>`).join("")}</select></label></p><p class="dim" data-ni></p>`),
    [[dup ? T("Duplicar", "Duplicate") : T("Crear", "Create"), true, "pri"], [T("Cancelar", "Cancel"), false]]);
  const D = $("dlg"), inp = D.querySelector("[data-np]"), ns = D.querySelector("[data-ns]"), ni = D.querySelector("[data-ni]"), go = D.querySelector('[data-i="0"]');
  const check = () => {
    if (inp) { let ok = true; try { SDT.checkName("packs", inp.value); inp.title = ""; } catch (e) { ok = false; inp.title = e.message; } inp.style.outline = ok ? "" : "1px solid var(--bad)"; go.disabled = !ok; }
    if (ni) ni.textContent = ns.value === "-1" ? T("Sin samples ni patches: los drums callan y los sintes no tienen patches hasta que subas los tuyos. Sin proyectos: cada hueco empieza como un proyecto nuevo.", "No samples or patches: the drums are silent and the synths have no patches until you upload yours. No projects: each slot starts as a new project.")
                                        : T("Los samples y los bancos de patches de ese pack (también los parches custom), sin sus proyectos: cada hueco empieza como un proyecto nuevo.", "That pack's samples and patch banks (custom patches too), without its projects: each slot starts as a new project.");
  };
  if (inp) { inp.oninput = check; inp.onkeydown = e => { if (e.key === "Enter" && !go.disabled) go.click(); }; inp.focus(); inp.select(); }
  if (ns) ns.onchange = check;
  check();
  if (!await pr) return;
  const name = inp ? inp.value.trim() : src.name, to = Number(D.querySelector("[data-nn]").value), from = dup ? src : ns.value === "-1" ? null : card.pack(Number(ns.value));
  p.sel.clear();
  await run(`${dup ? T("Duplicar", "Duplicate") : T("Pack nuevo", "New pack")} ${C.folderName(to, name)}`, async ctx => {
    const q = dup ? await C.copyPack(src, card, to, tracks ? Object.assign({}, ctx, {name}) : ctx) : await SDT.newPack(card, to, name, from, ctx);
    if (q) p.sel.add(q.slot);
  });
}
async function emptyProjAct(p) {
  const pl = place(p);
  if (!pl || p.kind !== "tracks") return say(T("Solo en el Tracks", "Tracks only"), T("Abre una tarjeta del Tracks y elige un pack.", "Open a Tracks card and choose a pack."));
  const used = p.items.filter(x => !x.empty), free = p.items.filter(x => x.empty).map(x => x.slot);
  if (!used.length) return say(T("Sin proyectos", "No projects"), T("El proyecto vacío toma los sonidos de otro proyecto del pack, y este pack no tiene ninguno. Un hueco vacío ya empieza en el aparato como un proyecto nuevo.", "The empty project takes the sounds of another project of the pack, and this pack has none. An empty slot already starts on the device as a new project."));
  const sel = [...p.sel].sort((a, b) => a - b), src0 = sel.find(n => p.items[n] && !p.items[n].empty), to0 = sel.find(n => p.items[n] && p.items[n].empty);
  const start = to0 !== undefined ? to0 : free.length ? free[0] : (src0 !== undefined ? src0 : used[0].slot), first = src0 !== undefined ? src0 : used[0].slot;
  const pr = ask(T("Proyecto vacío", "Empty project"),
    `<p><label>${T("Nombre", "Name")} <input type="text" data-ep maxlength="${SDT.NAME_RULE.projects.max}" spellcheck="false" style="width:100%" value="Empty"></label></p>` +
    `<p><label>${T("Sonidos de", "Sounds from")} <select data-es>${used.map(x => `<option value="${x.slot}"${x.slot === first ? " selected" : ""}>${SDT.pad2(x.slot)} ${esc(x.name)}</option>`).join("")}</select></label></p>` +
    `<p><label>${T("Hueco", "Slot")} <select data-et>${p.items.map(x => `<option value="${x.slot}"${x.slot === start ? " selected" : ""}>${SDT.pad2(x.slot)} ${x.empty ? T("(libre)", "(free)") : esc(x.name)}</option>`).join("")}</select></label></p>` +
    `<p class="dim">${T("Sin notas, automatización, escenas ni cadenas; con los patches de los sintes, los samples y los knobs de los drums, el mixer, los efectos y el sinte propio de MIDI 1 / 2 del proyecto elegido.", "No notes, automation, scenes or chains; with the chosen project's synth patches, drum samples and knobs, mixer, effects and MIDI 1 / 2 own synth.")}</p><p class="warn" data-ew></p>`,
    [[T("Crear", "Create"), true, "pri"], [T("Cancelar", "Cancel"), false]]);
  const D = $("dlg"), inp = D.querySelector("[data-ep]"), et = D.querySelector("[data-et]"), ew = D.querySelector("[data-ew]"), go = D.querySelector('[data-i="0"]');
  const check = () => {
    let ok = true; try { SDT.checkName("projects", inp.value); inp.title = ""; } catch (e) { ok = false; inp.title = e.message; }
    inp.style.outline = ok ? "" : "1px solid var(--bad)"; go.disabled = !ok;
    const t = p.items[Number(et.value)];
    ew.textContent = t && !t.empty ? T(`Sustituye a ${t.name}${state.backup ? " (se guarda antes una copia)" : ""}.`, `Replaces ${t.name}${state.backup ? " (a backup is kept first)" : ""}.`) : "";
    go.className = t && !t.empty ? "dng" : "pri";
  };
  inp.oninput = check; et.onchange = check;
  inp.onkeydown = e => { if (e.key === "Enter" && !go.disabled) go.click(); };
  inp.focus(); inp.select(); check();
  if (!await pr) return;
  const name = inp.value.trim(), from = Number(D.querySelector("[data-es]").value), to = Number(et.value);
  p.sel.clear();
  await run(`${T("Proyecto vacío", "Empty project")} ${SDT.pad2(to)}_${name}`, async ctx => {
    const src = await SDT.Projects.get(pl, from);
    if (!src) throw new Error(T("ese proyecto ya no está", "that project is gone"));
    await SDT.Projects.put(pl, to, {name, bytes: SDT.projectEmpty(src.bytes, name)}, ctx);
    p.sel.add(to);
  });
}

// ---- drawing
function paneHtml(p) {
  let s = `<div class="prow"><b class="grow">${esc(p.dir ? p.dir.name : T("Sin carpeta", "No folder"))}</b>${p.kind ? `<span class="kind ${p.kind[0]}">${esc(kindLabel(p.kind))}</span>` : ""}<button type="button" data-act="open">${T("Abrir carpeta…", "Open folder…")}</button>${state.tab === "fm" ? `<button type="button" data-act="demos">${T("Parches demo", "Demo patches")}</button>` : ""}${state.tab === "fm" && p.card ? `<button type="button" data-act="starters" title="${esc(T("Los parches demo (los sonidos de partida del FM, que el firmware ya no lleva, los clásicos o todos) a los huecos de parches custom de uno o varios packs de esta tarjeta", "The demo patches (the FM starter sounds the firmware no longer carries, the classics or all of them) into the custom-patch slots of one or several packs of this card"))}">${T("Sonidos de partida…", "Starter sounds…")}</button>` : ""}</div>`;
  if (p.card && state.tab !== "packs") {
    s += `<div class="prow"><select data-sel="pack">${p.card.packs.map(x => `<option value="${x.slot}"${x.slot === p.packSlot ? " selected" : ""}>${SDT.pad2(x.slot)} ${esc(x.name)}</option>`).join("")}</select>`;
    if (state.tab === "patterns") s += `<select data-sel="sess"></select>`;
    s += "</div>";
  }
  s += `<div class="tool"><button type="button" class="pri" data-act="copy">${p.i ? "← " : ""}${T("Copiar", "Copy")}${p.i ? "" : " →"}</button>${(state.tab === "fm" || state.tab === "samples") && p.kind && p.other.card ? `<button type="button" data-act="multi" title="${esc(T("Las filas elegidas a los mismos huecos de varios packs de la tarjeta del otro lado", "The chosen rows into the same slots of several packs of the other side's card"))}">${T("A varios packs…", "To several packs…")}</button>` : ""}${state.tab === "fm" && p.kind ? `<button type="button" data-act="edit" title="${esc(T("Abre el parche elegido en el editor: sus valores suenan en el aparato al moverlos", "Opens the chosen patch in the editor: its values play on the device as you move them"))}">${T("Editar", "Edit")}</button>` : ""}${state.tab === "packs" && p.card ? `<button type="button" data-act="duppack" title="${esc(T("Una copia del pack elegido en un número libre de la misma tarjeta", "A copy of the chosen pack in a free number of the same card"))}">${T("Duplicar…", "Duplicate…")}</button>${p.kind === "tracks" ? `<button type="button" data-act="newpack">${T("Pack nuevo…", "New pack…")}</button>` : ""}` : ""}` +
       `${state.tab === "projects" && p.kind === "tracks" ? `<button type="button" data-act="newproj" title="${esc(T("Un proyecto sin notas con los sonidos de otro del pack", "A project without notes, with the sounds of another of the pack"))}">${T("Proyecto vacío…", "Empty project…")}</button>` : ""}<span class="hint">${esc(hintOf(p))}</span></div><div class="list"></div>`;
  return s;
}
function hintOf(p) {
  const q = p.other;
  if (p.kind === "demos") return T("solo lectura: cópialos a una tarjeta o carpeta, o ábrelos con Editar", "read-only: copy them to a card or folder, or open them with Edit");
  if (state.tab === "packs" || state.tab === "projects") return p.kind && q.kind && p.kind !== q.kind && p.kind !== "folder" && q.kind !== "folder" ? T("entre tarjetas del mismo aparato", "between cards of the same device") : "";
  if (!p.kind || !q.kind || p.kind === q.kind || p.kind === "folder" || q.kind === "folder" || q.kind === "demos") return "";
  return state.tab === "patterns" ? T("Tracks → Rhythm: la nota más grave de cada paso; Rhythm → Tracks: una nota por paso", "Tracks → Rhythm: each step's lowest note; Rhythm → Tracks: one note a step")
       : state.tab === "fm" ? T("el parche entero, tal cual: motor (VA, granular, FM…), valores y nombre", "the whole patch as it is: engine (VA, granular, FM…), values and name")
       : T("los WAV tal cual", "the WAVs as they are");
}
async function render(p) {
  p.el.innerHTML = paneHtml(p);
  try { p.items = p.kind ? await loadItems(p) : []; } catch (e) { p.items = []; log(e.message || String(e), "bad"); }
  const ss = p.el.querySelector('[data-sel="sess"]');
  if (ss) { const m = await core(p).sessionsOf(pack(p)); ss.innerHTML = [...m.values()].map(e => `<option value="${e.slot}"${e.slot === p.sess ? " selected" : ""}>${SDT.pad2(e.slot)} ${esc(e.label || "")}</option>`).join(""); }
  const l = p.el.querySelector(".list");
  l.innerHTML = p.items.map((it, n) => `<div class="row${it.empty ? " empty" : ""}${p.sel.has(n) ? " sel" : ""}" data-n="${n}"><span class="c0">${p.kind === "folder" ? "" : SDT.pad2(it.slot)}</span><span class="c1">${state.tab === "fm" && !it.empty && it.rgb ? `<span class="sw" style="background:${it.rgb}" title="${esc(T("El color del hueco en el aparato (su motor)", "The slot's colour on the device (its engine)"))}"></span>` : ""}</span><span class="c2">${esc(it.empty ? "—" : it.name || T("(sin nombre)", "(no name)"))}</span><span class="c3">${esc(it.extra || "")}</span><span></span></div>`).join("") ||
    `<div class="blank dim" style="padding:10px">${p.fwOff ? (p.kind === "rhythm" ? T("Los parches del Rhythm son de Remix: elige «Rhythm: Remix» o «automático» en el firmware de arriba.", "The Rhythm's patches are Remix's: pick «Rhythm: Remix» or «automatic» in the firmware options above.")
      : T("Los parches custom del Tracks son de Hacks: elige «Tracks: Hacks» o «automático» en el firmware de arriba.", "The Tracks' custom patches are Hacks': pick «Tracks: Hacks» or «automatic» in the firmware options above.")) : p.kind ? T("Nada aquí.", "Nothing here.") : T("Abre una tarjeta (o una copia / snapshot) del Tracks o del Rhythm, o una carpeta de ficheros.", "Open a Tracks or Rhythm card (or a copy / snapshot), or a folder of files.")}</div>`;
}
async function renderAll() {
  document.documentElement.lang = LANG;
  showView();
  $("sub").textContent = T("Hacks (Circuit Tracks) y Remix (Circuit Rhythm): samples, patrones y parches entre los dos, y carpetas", "Hacks (Circuit Tracks) and Remix (Circuit Rhythm): samples, patterns and patches between them, and folders");
  $("tabs").innerHTML = TABS.map(t => `<button type="button" data-tab="${t[0]}" class="${t[0] === state.tab ? "on" : ""}">${esc(T(t[1], t[2]))}</button>`).join("");
  for (const b of document.querySelectorAll(".lang button")) b.classList.toggle("on", b.dataset.lang === LANG);
  $("bBackup").textContent = state.backup ? T("Copias: ", "Backups: ") + state.backup.dir.name : T("Copias de seguridad…", "Backups…");
  const opts = (sel, L) => L.map(([v, es, en]) => `<option value="${v}"${v === sel ? " selected" : ""}>${esc(T(es, en))}</option>`).join("");
  $("fwT").innerHTML = opts(state.fwT, [["auto", "Tracks: automático", "Tracks: automatic"], ["stock", "Tracks: solo stock", "Tracks: stock only"], ["hacks", "Tracks: Hacks", "Tracks: Hacks"]]);
  $("fwR").innerHTML = opts(state.fwR, [["auto", "Rhythm: automático", "Rhythm: automatic"], ["stock", "Rhythm: solo stock", "Rhythm: stock only"], ["remix", "Rhythm: Remix", "Rhythm: Remix"]]);
  $("fwT").title = $("fwR").title = T("El firmware de cada aparato. Automático: todo (las apps de cada aparato preguntan al aparato conectado). Solo stock: sin lo propio de Hacks / Remix (los parches).",
                                      "Each device's firmware. Automatic: everything (each device's app asks the connected device). Stock only: nothing of Hacks / Remix (the patches).");
  $("notice").textContent = window.showDirectoryPicker ? "" : T("Este navegador no puede abrir carpetas: usa Chrome o Edge en un ordenador.", "This browser cannot open folders: use Chrome or Edge on a computer.");
  for (const p of panes) await render(p);
}

// ---- events
$("views").addEventListener("click", e => {
  const v = e.target.dataset && e.target.dataset.view;
  if (!v || state.busy || v === state.view) return;
  state.view = v; try { localStorage.setItem("hrapp.view", v); } catch (_) { /* none */ }
  if (v === "both") renderAll(); else showView();
});
$("fwnav").addEventListener("click", e => {
  const d = e.target.dataset && e.target.dataset.fwdev;
  if (!d || d === state.fwdev) return;
  state.fwdev = d; try { localStorage.setItem("hrapp.fwdev", d); } catch (_) { /* none */ }
  showView();
});
for (const [id, k, key] of [["fwT", "fwT", "sdapp.fw"], ["fwR", "fwR", "hrapp.rfw"]])
  $(id).addEventListener("change", e => {
    if (state.busy) { e.target.value = state[k]; return; }
    state[k] = e.target.value; try { localStorage.setItem(key, state[k]); } catch (_) { /* none */ }
    for (const p of panes) p.sel.clear();
    renderAll();
  });
$("tabs").addEventListener("click", e => { const t = e.target.dataset && e.target.dataset.tab; if (t && !state.busy) { state.tab = t; for (const p of panes) p.sel.clear(); renderAll(); } });
for (const b of document.querySelectorAll(".lang button")) b.onclick = () => { LANG = b.dataset.lang; try { localStorage.setItem("hrapp.lang", LANG); } catch (_) { /* none */ } renderAll(); };
$("bBackup").onclick = async () => { let d; try { d = await window.showDirectoryPicker({mode: "readwrite"}); } catch (_) { return; } state.backup = new SDT.Backup(d, d.name); renderAll(); };
for (const p of panes) {
  p.el.addEventListener("click", async e => {
    if (state.busy) return;
    const act = e.target.dataset ? e.target.dataset.act : null;
    if (act === "open") { let d; try { d = await window.showDirectoryPicker({mode: "readwrite"}); } catch (_) { return; } try { await openPane(p, d); } catch (er) { log(er.message || String(er), "bad"); } return; }
    if (act === "copy") return copyAct(p);
    if (act === "demos") return openDemos(p);
    if (act === "starters") return loadDemosAct(p);
    if (act === "multi") return multiCopyAct(p);
    if (act === "edit") return editAct(p);
    if (act === "newpack") return newPackAct(p, false);
    if (act === "duppack") return newPackAct(p, true);
    if (act === "newproj") return emptyProjAct(p);
    const row = e.target.closest(".row"); if (!row) return;
    const n = +row.dataset.n;
    if (e.ctrlKey || e.metaKey) { p.sel.has(n) ? p.sel.delete(n) : p.sel.add(n); }
    else if (e.shiftKey && p.sel.size) { const a = Math.min(...p.sel); p.sel = new Set(); for (let k = Math.min(a, n); k <= Math.max(a, n); k++) p.sel.add(k); }
    else p.sel = new Set([n]);
    for (const r of p.el.querySelectorAll(".row")) r.classList.toggle("sel", p.sel.has(+r.dataset.n));
  });
  p.el.addEventListener("change", async e => {
    const w = e.target.dataset ? e.target.dataset.sel : null;
    if (w === "pack") { p.packSlot = +e.target.value; p.sess = null; p.sel.clear(); await render(p); }
    else if (w === "sess") { p.sess = +e.target.value; p.sel.clear(); await render(p); }
  });
}
window.HRAPP = {state, panes, openPane, openDemos, editAct, newPackAct, emptyProjAct, loadDemosAct, multiCopyAct, frameReady, renderAll, copyAct, showView, fwOK, ask: null};
renderAll();
})();
