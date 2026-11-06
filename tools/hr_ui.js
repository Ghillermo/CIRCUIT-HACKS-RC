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
const TABS = [["samples", "Samples", "Samples"], ["patterns", "Patrones", "Patterns"], ["fm", "Parches", "Patches"]];
const state = {tab: "samples", busy: false, backup: null};
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
const kindLabel = k => ({tracks: "Hacks · Circuit Tracks", rhythm: "Remix · Circuit Rhythm", folder: T("carpeta", "folder")})[k] || "";

// ---- the items of a pane in the current tab: {slot, empty, name, extra}
const FOLDER_EXT = {samples: /\.wav$/i, patterns: /\.(ctpat|rmpat)$/i, fm: /\.(fm8|ctm)$/i};
async function folderFiles(p) {
  const out = [];
  for await (const [n, h] of p.dir.entries()) if (h.kind === "file" && FOLDER_EXT[state.tab].test(n)) out.push({n, h});
  out.sort((a, b) => a.n.localeCompare(b.n));
  return out;
}
async function loadItems(p) {
  const tab = state.tab;
  if (p.kind === "folder") return (await folderFiles(p)).map((f, i) => ({slot: i, empty: false, name: f.n, file: f}));
  const pl = place(p); if (!pl) return [];
  if (tab === "samples") return (p.kind === "rhythm" ? SDR.Samples : SDT.Drums).list(pl);
  if (tab === "patterns") {
    const m = await core(p).sessionsOf(pl.pack);
    if (p.sess === null || !m.has(p.sess)) p.sess = m.size ? [...m.keys()][0] : null;
    if (p.sess === null) return [];
    const TN = core(p).TRACK_NAME;
    return (await core(p).Patterns.list({pack: pl.pack, sess: p.sess})).map(x => Object.assign(x, {name: `${TN[x.slot >> 3]} · ${(x.slot & 7) + 1}`, extra: x.empty ? "" : `${x.notes} ${T("notas", "notes")}${x.lanes ? `, ${x.lanes} ${T("carriles", "lanes")}` : ""}`}));
  }
  if (p.kind === "rhythm") return RFM.list(pl);
  const L = await SDT.Custom.list(pl);
  for (const x of L) if (!x.empty && !x.bad) x.extra = engineOf(await SDT.Custom.get(pl, x.slot));
  return L.map(x => Object.assign(x, {empty: x.empty || x.bad, name: x.name || ""}));
}
async function getItem(p, n) {                              // -> {kind, name, bytes / pad / rec}
  const tab = state.tab, it = p.items[n];
  if (p.kind === "folder") {
    const b = new Uint8Array(await (await it.file.h.getFile()).arrayBuffer()), nm = it.name.replace(/\.[^.]+$/, "");
    if (tab === "samples") return {name: nm, bytes: b};
    if (tab === "patterns") return {name: nm, bytes: b, from: /\.rmpat$/i.test(it.name) ? "rhythm" : "tracks", slot: b.length === SDT.patSize(32) ? 32 : 0};
    return /\.fm8$/i.test(it.name) ? {name: nm, rec: b.subarray(0, FM_REC)} : {name: nm, rec: HR.fmOfCustom(b), pad: b};
  }
  const pl = place(p);
  if (tab === "samples") return (p.kind === "rhythm" ? SDR.Samples : SDT.Drums).get(pl, n);
  if (tab === "patterns") return {name: it.name, bytes: await core(p).Patterns.get({pack: pl.pack, sess: p.sess}, n), from: p.kind, slot: n};
  if (p.kind === "rhythm") { const pad = await RFM.get(pl, n); return pad ? {name: SDT.ctmName(pad) || `Remix ${SDR.pad2(n)}`, pad, rec: HR.fmOfCustom(pad)} : null; }
  const pad = await SDT.Custom.get(pl, n); return pad ? {name: SDT.ctmName(pad) || `Hacks ${SDT.pad2(n)}`, pad, rec: HR.fmOfCustom(pad)} : null;
}
async function putItem(q, n, x, ctx) {                       // into pane q's slot n (a folder: a new file)
  const tab = state.tab;
  if (q.kind === "folder") {
    const ext = tab === "samples" ? ".wav" : tab === "patterns" ? (x.from === "rhythm" ? ".rmpat" : ".ctpat") : x.pad ? ".ctm" : ".fm8";
    const data = tab === "fm" ? (x.pad || x.rec) : x.bytes;
    let name = (x.name || "item").replace(/[\\/:*?"<>|]/g, "_").trim() + ext;
    for (let k = 2; await q.dir.getFileHandle(name).then(() => true, () => false); k++) name = name.replace(/( \d+)?(\.[^.]+)$/, ` ${k}$2`);
    await SDT.writeFile(q.dir, name, data); return;
  }
  const pl = place(q);
  if (tab === "samples") return (q.kind === "rhythm" ? SDR.Samples : SDT.Drums).put(pl, n, {name: x.name, bytes: x.bytes}, ctx);
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
  if (state.tab === "patterns" && q.kind !== "folder" && q.sess === null) return say(T("Sin proyecto", "No project"), T("El otro lado no tiene un proyecto elegido.", "The other side has no project chosen."));
  let to = [];
  if (q.kind !== "folder") {
    const start = q.sel.size ? Math.min(...q.sel) : q.items.findIndex(x => x.empty);
    if (start < 0) return say(T("No cabe", "It does not fit"), T("Elige el hueco de destino en el otro lado.", "Choose the target slot on the other side."));
    to = from.map((_, i) => start + i);
    if (to[to.length - 1] >= q.items.length) return say(T("No cabe", "It does not fit"), T("No hay huecos suficientes desde el elegido.", "Not enough slots from the chosen one."));
    const hit = to.filter(n => !q.items[n].empty);
    if (hit.length && !await ask(T("Huecos ocupados", "Slots in use"), `<p>${hit.map(n => esc(`${n} ${q.items[n].name}`)).join("<br>")}</p>`, [[T("Sobrescribir", "Overwrite"), true, "dng"], [T("Cancelar", "Cancel"), false]])) return;
  }
  const across = p.kind !== q.kind && p.kind !== "folder" && q.kind !== "folder";
  await run(`${T("Copiar", "Copy")} ${from.length}${across ? " · " + T("adaptado", "adapted") : ""}`, async ctx => {
    for (let i = 0; i < from.length; i++) {
      const x = await getItem(p, from[i]);
      if (!x) continue;
      try { await putItem(q, to[i], x, ctx); } catch (e) { log(`${x.name}: ${e.message || e}`, "bad"); }
      ctx.progress("", i + 1, from.length);
    }
    for (const k of [p, q]) { const pk = pack(k); if (pk) { pk._samples = null; pk._banks = null; pk._fmb = null; pk._info = null; } }
  });
  q.sel.clear();
}

// ---- drawing
function paneHtml(p) {
  let s = `<div class="prow"><b class="grow">${esc(p.dir ? p.dir.name : T("Sin carpeta", "No folder"))}</b>${p.kind ? `<span class="kind ${p.kind[0]}">${esc(kindLabel(p.kind))}</span>` : ""}<button type="button" data-act="open">${T("Abrir carpeta…", "Open folder…")}</button></div>`;
  if (p.card) {
    s += `<div class="prow"><select data-sel="pack">${p.card.packs.map(x => `<option value="${x.slot}"${x.slot === p.packSlot ? " selected" : ""}>${SDT.pad2(x.slot)} ${esc(x.name)}</option>`).join("")}</select>`;
    if (state.tab === "patterns") s += `<select data-sel="sess"></select>`;
    s += "</div>";
  }
  s += `<div class="tool"><button type="button" class="pri" data-act="copy">${p.i ? "← " : ""}${T("Copiar", "Copy")}${p.i ? "" : " →"}</button><span class="hint">${esc(hintOf(p))}</span></div><div class="list"></div>`;
  return s;
}
function hintOf(p) {
  const q = p.other;
  if (!p.kind || !q.kind || p.kind === q.kind || p.kind === "folder" || q.kind === "folder") return "";
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
  l.innerHTML = p.items.map((it, n) => `<div class="row${it.empty ? " empty" : ""}${p.sel.has(n) ? " sel" : ""}" data-n="${n}"><span class="c0">${p.kind === "folder" ? "" : SDT.pad2(it.slot)}</span><span class="c1"></span><span class="c2">${esc(it.empty ? "—" : it.name || T("(sin nombre)", "(no name)"))}</span><span class="c3">${esc(it.extra || "")}</span><span></span></div>`).join("") ||
    `<div class="blank dim" style="padding:10px">${p.kind ? T("Nada aquí.", "Nothing here.") : T("Abre una tarjeta (o una copia / snapshot) del Tracks o del Rhythm, o una carpeta de ficheros.", "Open a Tracks or Rhythm card (or a copy / snapshot), or a folder of files.")}</div>`;
}
async function renderAll() {
  document.documentElement.lang = LANG;
  $("sub").textContent = T("Hacks (Circuit Tracks) y Remix (Circuit Rhythm): samples, patrones y parches entre los dos, y carpetas", "Hacks (Circuit Tracks) and Remix (Circuit Rhythm): samples, patterns and patches between them, and folders");
  $("tabs").innerHTML = TABS.map(t => `<button type="button" data-tab="${t[0]}" class="${t[0] === state.tab ? "on" : ""}">${esc(T(t[1], t[2]))}</button>`).join("");
  for (const b of document.querySelectorAll(".lang button")) b.classList.toggle("on", b.dataset.lang === LANG);
  $("bBackup").textContent = state.backup ? T("Copias: ", "Backups: ") + state.backup.dir.name : T("Copias de seguridad…", "Backups…");
  $("notice").textContent = window.showDirectoryPicker ? "" : T("Este navegador no puede abrir carpetas: usa Chrome o Edge en un ordenador.", "This browser cannot open folders: use Chrome or Edge on a computer.");
  for (const p of panes) await render(p);
}

// ---- events
$("tabs").addEventListener("click", e => { const t = e.target.dataset && e.target.dataset.tab; if (t && !state.busy) { state.tab = t; for (const p of panes) p.sel.clear(); renderAll(); } });
for (const b of document.querySelectorAll(".lang button")) b.onclick = () => { LANG = b.dataset.lang; try { localStorage.setItem("hrapp.lang", LANG); } catch (_) { /* none */ } renderAll(); };
$("bBackup").onclick = async () => { let d; try { d = await window.showDirectoryPicker({mode: "readwrite"}); } catch (_) { return; } state.backup = new SDT.Backup(d, d.name); renderAll(); };
for (const p of panes) {
  p.el.addEventListener("click", async e => {
    if (state.busy) return;
    const act = e.target.dataset ? e.target.dataset.act : null;
    if (act === "open") { let d; try { d = await window.showDirectoryPicker({mode: "readwrite"}); } catch (_) { return; } try { await openPane(p, d); } catch (er) { log(er.message || String(er), "bad"); } return; }
    if (act === "copy") return copyAct(p);
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
window.HRAPP = {state, panes, openPane, renderAll, copyAct, ask: null};
renderAll();
})();
