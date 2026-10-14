"""The own-synth patches of MIDI 1 / 2 (the mod's own: Components does not know them), on the PC: a library of patch files and the slots of a pack
(the microSD card in a reader, or a copy of it).  List, dump, upload, copy, name, read and edit the parameters.

A patch is named by WHERE it is:  a file  (bass.ctm)  or a slot of a pack  (E:/29_PACK:5  = slot 5, 0..63;  the pack = the folder that holds
Patches/, or its Patches folder).

    patchtool.py list PACK                      the 64 slots: index, page / pad of the Preset view of MIDI 1 / 2, name, engine
    patchtool.py show WHERE                     the name, the engine and every parameter with its value
    patchtool.py set  WHERE NAME=VALUE ...      edit parameters (the names of `show`; engine=... too); the sum is redone
    patchtool.py name WHERE "NAME"              the name (up to 16 ASCII characters; "" removes it)
    patchtool.py new  FILE.ctm [engine]         a new patch file with the initial values (engine: osc, va-drum, granular, line, fxseq, off)
    patchtool.py copy WHERE WHERE               file -> slot = upload; slot -> file = dump; slot -> slot (also between packs); file -> file
    patchtool.py dump PACK DIR                  every slot in use as DIR/NN_name.ctm
    patchtool.py clear PACK:N                   the slot empty
    patchtool.py slist PACK / sname PACK:N "NAME" / sdump PACK:N FILE.bin     the stock synth patches (0..127): list, rename, dump
    patchtool.py fxdiag PACK                    the marks the SC40D diagnostic leaves after project saves (records 64..127)
    patchtool.py patdiag PACK                   the marks the SC403D diagnostic leaves in the settings of every pattern
    patchtool.py sessdiag PACK                  the marks the SC402D diagnostic leaves in the last 1000 bytes of the projects

Every write into a pack copies the bank to *.bak first (once) and never touches the 340 bytes of the synth patch of the record.  A slot whose
record (or bank file) does not exist yet is created with empty synth patches (0xFF, what the device itself leaves between patches).

Where they live (tools/mpatch.py, docs/NOTAS.md): Patches/NN_PATCHBANK.cpb = 8 records of 512 bytes; a record = 340 bytes of a stock synth patch
(Components' business) + 172 bytes of padding.  Slot n of the own synth is the padding of record n (bank n / 8, record n % 8):
    [0..3] "CTM1"  [4] flags  [5] step-drummer nibble  [6..31] the values of codes 1..26  [32..39] codes 27..34  [40] sum of [4..39]  [41] 1
    [44..59] the name this tool keeps (the device ignores it; Duplicate + A + B on the device moves it with the patch (SC39.4), a save on the
             device over the slot removes it)
A .ctm file is those first 64 bytes.  The flags: bit 0 the mode on, 1 the oscillator source, 2 / 3 the engine bits, 4 two oscillators, 5 the
chain order.  The values are the knob values of tools/vcf21.py: 0..127, or -64..63 for the bipolar ones; this tool takes -64..127 and does
not know each knob's own range: `show` on a patch made on the device tells what a value looks like.
"""
from __future__ import annotations
import argparse, re, shutil, sys
from pathlib import Path

REC, PSZ, PER = 512, 340, 8
DATA, NAME_AT, NAME_LEN, FILE_LEN = 42, 44, 16, 64
MODES = {0: "mono", 1: "mono AG", 2: "poly"}
# code -> (name, what it is; after " | " what it is with the granular engine, which shares the values of the oscillator pages)
PARAMS = {1: ("filt", "filtro"), 2: ("res", "resonancia"), 3: ("envf", "envolvente -> filtro"), 4: ("lfof", "LFO -> filtro"), 5: ("atk", "ataque"), 6: ("dec", "decay"),
          7: ("sus", "sustain"), 8: ("rel", "release"), 9: ("fxamt", "cantidad de efecto"), 10: ("gain", "gain del VCA"), 11: ("lrate", "velocidad del LFO"),
          12: ("lfov", "LFO -> nivel"), 13: ("fxtype", "tipo de efecto"), 14: ("note2", "segunda nota (la pone cada nota tocada)"), 15: ("enva", "envolvente -> nivel"),
          16: ("ftype", "tipo de filtro"), 17: ("tune", "tono | granular: tono"), 18: ("fine", "fino | granular: tamaño del grano"),
          19: ("wave", "forma de onda (morph) | granular: posición"), 20: ("shape", "forma / ancho | granular: densidad"), 21: ("lfop", "LFO -> tono | granular: scan"),
          22: ("envp", "envolvente -> tono | granular: envolvente -> posición"), 23: ("envw", "envolvente -> forma | granular: zona del scan"),
          24: ("lfow", "LFO -> forma | granular: LFO -> posición"), 25: ("envm", "envolvente -> morph | granular: fuente"), 26: ("lfom", "LFO -> morph | granular: modo de nota"),
          27: ("tune2", "tono del OSC 2 | granular: LFO -> tamaño"), 28: ("fine2", "fino del OSC 2 | granular: fino"), 29: ("wave2", "forma del OSC 2 | granular: dispersión del tono"),
          30: ("shape2", "forma / ancho del OSC 2 | granular: ventana"), 31: ("mix", "mezcla OSC 1 <-> OSC 2"), 32: ("bitsync", "BITSYNC"),
          33: ("fm", "FM | granular: dispersión de la posición"), 34: ("ring", "ring | granular: probabilidad de grano al revés")}
BYNAME = {v[0]: k for k, v in PARAMS.items()}
DEFAULTS = (0, 0, 0, 0, 0, 0, 127, 0, 0, 0, 40, 0, 0, 60, 63, 0, 0, 0, 0, 50, 0, 0, 0, 0, 0, 0) + (0, 0, 0, 50, 64, 0, 0, 0)
ENGINES = {"off": 0b0000, "line": 0b0001, "fxseq": 0b0101, "osc": 0b0011, "va-drum": 0b0111, "granular": 0b1011}
ENGINE_ES = {"off": "apagado", "line": "entrada de línea", "fxseq": "secuenciador de efectos", "osc": "oscilador", "va-drum": "VA-drum", "granular": "granular"}


# ---------------------------------------------------------------- a patch (64 bytes)
def state(b: bytes):
    if len(b) < DATA or b[:4] != b"CTM1": return "empty"
    return "ok" if sum(b[4:40]) & 0xFF == b[40] else "bad sum"


def name_of(b: bytes):
    n = b[NAME_AT:NAME_AT + NAME_LEN]
    return n.decode("ascii").rstrip() if len(n) == NAME_LEN and all(32 <= c < 127 for c in n) else ""


def norm(b: bytes):
    """any padding / file -> the 64 bytes of a .ctm"""
    return bytes(b[:DATA]) + b"\xFF" * (NAME_AT - DATA) + name_of(b).ljust(NAME_LEN).encode("ascii") + b"\xFF" * (FILE_LEN - NAME_AT - NAME_LEN) if name_of(b) \
        else bytes(b[:DATA]) + b"\xFF" * (FILE_LEN - DATA)


def engine_of(b: bytes):
    fl = b[4]
    if not fl & 1: return "off"
    if not fl & 2: return "fxseq" if fl & 4 else "line"
    if fl & 4: return "va-drum"
    return "granular" if fl & 8 else "osc"


def make(flags, sd, vals, name=""):
    body = bytes([flags, sd]) + bytes(v & 0xFF for v in vals)
    b = b"CTM1" + body + bytes([sum(body) & 0xFF, 1])
    return norm(b + b"\xFF" * (NAME_AT - DATA) + (name.ljust(NAME_LEN).encode("ascii") if name else b"\xFF" * NAME_LEN))


def values(b): return [v - 256 if v >= 128 else v for v in b[6:40]]


def describe(b: bytes):
    fl, e = b[4], engine_of(b)
    out = [f"nombre:   {name_of(b) or '(sin nombre)'}", f"engine:   {e} ({ENGINE_ES[e]})" + (", velocity -> envolventes" if e == 'va-drum' and fl & 8 else ""),
           f"dual:     {fl >> 4 & 1}   (dos osciladores)", f"route:    {fl >> 5 & 1}   (orden de la cadena)",
           f"sd:       {b[5]}   (step-drummer: bit 0 activado, bits 1-3 destino)", ""]
    for c, v in enumerate(values(b), 1):
        nm, what = PARAMS[c]
        if e != "granular": what = what.split(" | ")[0]
        elif " | granular: " in what: what = "granular: " + what.split(" | granular: ")[1]
        out.append(f"{nm:<8}  {v:4d}   {what}")
    return "\n".join(out)


def edit(b: bytes, pairs):
    fl, sd, vals = b[4], b[5], values(b)
    for pr in pairs:
        if "=" not in pr: sys.exit(f"{pr}: se esperaba NOMBRE=VALOR")
        k, v = pr.split("=", 1); k = k.lower()
        if k == "engine":
            if v not in ENGINES: sys.exit("engine: " + ", ".join(ENGINES))
            fl = fl & ~0x0F | ENGINES[v]; continue
        try: n = int(v)
        except ValueError: sys.exit(f"{pr}: el valor debe ser un número")
        if k == "dual": fl = fl & ~0x10 | (0x10 if n else 0)
        elif k == "route": fl = fl & ~0x20 | (0x20 if n else 0)
        elif k == "velocity": fl = fl & ~0x08 | (0x08 if n else 0)
        elif k == "sd":
            if not 0 <= n <= 15: sys.exit("sd: 0..15")
            sd = n
        elif k in BYNAME:
            if not -64 <= n <= 127: sys.exit(f"{k}: -64..127")
            vals[BYNAME[k] - 1] = n
        else: sys.exit(f"{k}: parámetro desconocido (mira `show`)")
    return make(fl, sd, vals, name_of(b))


# ---------------------------------------------------------------- a pack
def patches_dir(pack: Path):
    d = pack / "Patches" if (pack / "Patches").is_dir() else pack
    if not d.is_dir(): sys.exit(f"{pack}: no es una carpeta")
    return d


def banks(pack: Path):
    out = {}
    for f in sorted(patches_dir(pack).glob("*_PATCHBANK.cpb")):
        m = re.match(r"(\d+)_", f.name)
        if m: out[int(m.group(1))] = f
    return out


def bank_file(pack: Path, b: int, create=False):
    bk = banks(pack)
    if b in bk: return bk[b]
    if not create: return None
    if not bk: sys.exit(f"no hay *_PATCHBANK.cpb en {patches_dir(pack)}: ¿es la carpeta de un pack?")
    width = len(re.match(r"(\d+)_", next(iter(bk.values())).name).group(1))
    return patches_dir(pack) / f"{b:0{width}d}_PATCHBANK.cpb"


def record(data: bytes, slot: int):
    r = data[REC * slot:REC * (slot + 1)]
    return (None, b"") if len(r) < PSZ else (r[:PSZ], r[PSZ:])


def backup(f: Path):
    b = f.with_suffix(f.suffix + ".bak")
    if f.exists() and not b.exists(): shutil.copy2(f, b); print("copia:", b)


def read_slot(pack: Path, n: int):
    """-> the padding of slot n as it is (b'' when the record is not there)"""
    f = bank_file(pack, n // PER)
    return record(f.read_bytes(), n % PER)[1] if f else b""


def write_slot(pack: Path, n: int, chunk: bytes, at=0):
    """chunk into the padding of record n at `at`; the file / the records that are missing are made of 0xFF (empty synth patches)"""
    f = bank_file(pack, n // PER, create=True)
    data = f.read_bytes() if f.exists() else b""
    o = REC * (n % PER) + PSZ + at
    end = REC * (n % PER + 1)                                                     # the record complete (the device takes a short padding for an empty slot)
    if len(data) < end: data += b"\xFF" * (end - len(data))
    backup(f); f.write_bytes(data[:o] + chunk + data[o + len(chunk):])
    return f


class Where:
    def __init__(self, s: str):
        m = re.match(r"^(.*):(\d+)$", s)
        self.text = s
        if m and Path(m.group(1)).is_dir():
            self.pack, self.n, self.file = Path(m.group(1)), int(m.group(2)), None
            if not 0 <= self.n < 64: sys.exit(f"{s}: hueco 0..63")
        else: self.pack, self.n, self.file = None, None, Path(s)
    def read(self, must=True):
        b = self.file.read_bytes() if self.file and self.file.exists() else (read_slot(self.pack, self.n) if self.pack else b"")
        st = state(b)
        if must and st != "ok": sys.exit(f"{self.text}: " + {"empty": "vacío / no es un patch del sinte propio", "bad sum": "dañado (la suma no coincide)"}[st])
        return norm(b) if st == "ok" else None
    def write(self, b: bytes):
        if self.file: self.file.write_bytes(b); return
        write_slot(self.pack, self.n, b[:DATA] + b"\xFF" * (NAME_AT - DATA) + b[NAME_AT:NAME_AT + NAME_LEN])


def safe(s): return re.sub(r"[^A-Za-z0-9 _.-]", "_", s).strip()
def sempty(p): return p is None or set(p[:16]) <= {0xFF}
def sname_of(p): return p[:16].decode("latin-1").rstrip(" \0")


def main():
    ap = argparse.ArgumentParser(description="Patches del sinte propio de MIDI 1 / 2: biblioteca de ficheros y huecos de un pack", epilog="python tools/patchtool.py -h; la cabecera del fichero explica cada orden")
    ap.add_argument("cmd", choices=["list", "show", "set", "name", "new", "copy", "dump", "clear", "slist", "sname", "sdump", "fxdiag", "sessdiag", "patdiag"]); ap.add_argument("args", nargs="*")
    a = ap.parse_args(); A = a.args
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    need = lambda k, usage: len(A) >= k or sys.exit("uso: patchtool.py " + usage)

    if a.cmd == "list":
        need(1, "list PACK"); pack = Path(A[0]); bk = banks(pack)
        if not bk: sys.exit(f"no hay *_PATCHBANK.cpb en {patches_dir(pack)}")
        print(" idx  pág pad  nombre            motor")
        for n in range(64):
            pad = read_slot(pack, n); st = state(pad)
            txt = "" if st == "empty" else ENGINE_ES[engine_of(pad)] if st == "ok" else "DAÑADO (suma)"
            print(f" {n:3d}   {n // 16 + 1}   {n % 16 + 9:2d}  {name_of(pad) if st != 'empty' else '':<16}  {txt if st != 'empty' else '-'}")
    elif a.cmd == "show":
        need(1, "show DÓNDE"); print(describe(Where(A[0]).read()))
    elif a.cmd == "set":
        need(2, "set DÓNDE NOMBRE=VALOR ..."); w = Where(A[0]); b = edit(w.read(), A[1:]); w.write(b); print(f"{w.text}: {', '.join(A[1:])}")
    elif a.cmd == "name":
        need(2, 'name DÓNDE "NOMBRE"'); w = Where(A[0]); new = A[1]
        if len(new) > NAME_LEN or any(not 32 <= ord(c) < 127 for c in new): sys.exit("nombre: hasta 16 caracteres ASCII")
        b = w.read(); w.write(make(b[4], b[5], values(b), new)); print(f"{w.text}: «{name_of(b)}» -> «{new}»")
    elif a.cmd == "new":
        need(1, "new FICHERO.ctm [engine]"); e = A[1] if len(A) > 1 else "osc"
        if e not in ENGINES: sys.exit("engine: " + ", ".join(ENGINES))
        f = Path(A[0])
        if f.exists(): sys.exit(f"{f}: ya existe")
        f.write_bytes(make(ENGINES[e], 0, DEFAULTS)); print(f"{f}: patch nuevo ({ENGINE_ES[e]}, valores iniciales)")
    elif a.cmd == "copy":
        need(2, "copy ORIGEN DESTINO"); src, dst = Where(A[0]), Where(A[1]); b = src.read()
        old = dst.read(must=False); dst.write(b)
        print(f"{src.text} «{name_of(b)}» -> {dst.text}" + (f" (sustituye a «{name_of(old)}»)" if old else ""))
    elif a.cmd == "dump":
        need(2, "dump PACK DIR"); pack, out = Path(A[0]), Path(A[1]); out.mkdir(parents=True, exist_ok=True); k = 0
        for n in range(64):
            pad = read_slot(pack, n)
            if state(pad) != "ok": continue
            (out / f"{n:02d}_{safe(name_of(pad)) or 'sin nombre'}.ctm").write_bytes(norm(pad)); k += 1
        print(k, "patches en", out)
    elif a.cmd == "clear":
        need(1, "clear PACK:N"); w = Where(A[0])
        if not w.pack: sys.exit("clear PACK:N")
        pad = read_slot(w.pack, w.n)
        if state(pad) == "empty": sys.exit(f"{w.text}: ya está vacío")
        write_slot(w.pack, w.n, b"\xFF" * min(len(pad), REC - PSZ)); print(f"{w.text}: vaciado")
    elif a.cmd == "fxdiag":                                                           # the marks of the SC40D diagnostic (tools/fxdiag.py): records 64..127
        need(1, "fxdiag PACK"); pack = Path(A[0]); k = 0
        for n in range(64):
            f = bank_file(pack, (64 + n) // PER)
            pad = record(f.read_bytes(), (64 + n) % PER)[1] if f else b""
            if pad[:4] != b"FXD1": continue
            ok = len(pad) >= 16 and bytes(x ^ 0xFF for x in pad[:8]) == pad[8:16] and pad[7] == 0xA5
            print(f" proyecto {n + 1:2d} (registro {64 + n}): {'marca bien' if ok else 'marca DAÑADA'}, guardados vistos {pad[4]}, proyecto {pad[5] + 1}, pack {pad[6] + 1}"); k += 1
        print(k, "marcas del diagnóstico SC40D")
    elif a.cmd == "sessdiag":                                                         # the marks of the SC402D diagnostic (tools/taildiag.py): the last 1000 bytes of every project
        need(1, "sessdiag PACK"); pack = Path(A[0]); d = pack / "Sessions" if (pack / "Sessions").is_dir() else pack; k = 0
        for f in sorted(d.glob("*.ncs")):
            data = f.read_bytes()
            if len(data) != 0x2740C: print(f" {f.name}: {len(data)} bytes (se esperaban 160780)"); continue
            t = data[0x27024:]; used = sum(1 for c in t if c)
            if t[:4] == b"TAIL": txt = f"marca TAIL, guardados vistos {t[4]}, marca final {'bien' if t[-4:] == b'END!' else 'FALTA'}"; k += 1
            else: txt = "sin marca" + ("" if not used else f"; ¡{used} bytes distintos de cero en la cola!")
            print(f" {f.name}: {txt}")
        print(k, "proyectos con la marca del diagnóstico SC402D")
    elif a.cmd == "patdiag":                                                          # the marks of the SC403D diagnostic (tools/patdiag.py): bytes 4..39 of the settings of every pattern
        need(1, "patdiag PACK"); pack = Path(A[0]); d = pack / "Sessions" if (pack / "Sessions").is_dir() else pack
        import patdiag as PD
        names = ["Synth 1", "Synth 2", "MIDI 1", "MIDI 2", "Drum 1", "Drum 2", "Drum 3", "Drum 4"]
        want = lambda i: bytes([PD.ID | i, PD.TAG]) + bytes(range(PD.FIRST + 2, PD.SET_LEN))
        for f in sorted(d.glob("*.ncs")):
            data = f.read_bytes()
            if len(data) != 0x2740C: print(f" {f.name}: {len(data)} bytes (se esperaban 160780)"); continue
            st = [data[PD.settings_offset(i) + PD.FIRST:PD.settings_offset(i) + PD.SET_LEN] for i in range(PD.N_PAT)]
            if not any(any(x) for x in st): print(f" {f.name}: sin marcas"); continue
            own = sum(1 for i in range(PD.N_PAT) if st[i] == want(i)); print(f" {f.name}: {own} de {PD.N_PAT} patrones con su marca intacta")
            for i in range(PD.N_PAT):
                if st[i] == want(i): continue
                who = f"{names[i // 8]} patrón {i % 8 + 1}"
                if not any(st[i]): print(f"   {who}: a cero (borrado)"); continue
                src = st[i][0] & 0x3F
                if st[i] == want(src): print(f"   {who}: lleva la marca de {names[src // 8]} patrón {src % 8 + 1} (copiado)"); continue
                bad = [PD.FIRST + k for k in range(len(st[i])) if st[i][k] != want(i)[k]]
                print(f"   {who}: bytes cambiados {bad}: {st[i].hex(' ')}")
    # ---- the stock synth patches: list, rename, dump (Components does the rest)
    elif a.cmd == "slist":
        need(1, "slist PACK"); bk = banks(Path(A[0]))
        print(" idx  pág pad  nombre            modo")
        for b in sorted(bk):
            data = bk[b].read_bytes()
            for s in range(PER):
                p, _ = record(data, s)
                if p is None: continue
                n = b * PER + s
                print(f" {n:3d}   {n // 32 + 1}   {n % 32 + 1:2d}  {'(vacío)' if sempty(p) else sname_of(p):<16}  {'' if sempty(p) else MODES.get(p[32], '? %d' % p[32])}")
    else:
        need(2, 'sname PACK:N "NOMBRE"  |  sdump PACK:N FICHERO.bin'); m = re.match(r"^(.*):(\d+)$", A[0])
        if not m: sys.exit("PACK:N")
        pack, n = Path(m.group(1)), int(m.group(2))
        if not 0 <= n < 128: sys.exit("patch 0..127")
        f = bank_file(pack, n // PER)
        p = record(f.read_bytes(), n % PER)[0] if f else None
        if sempty(p): sys.exit(f"patch de sinte {n}: vacío")
        if a.cmd == "sdump": Path(A[1]).write_bytes(p); print(f"patch de sinte {n} «{sname_of(p)}» -> {A[1]} ({len(p)} bytes)"); return
        new = A[1]
        if not 1 <= len(new) <= 16 or any(not 32 <= ord(c) < 127 for c in new): sys.exit("nombre: 1-16 caracteres ASCII")
        data = f.read_bytes(); backup(f); o = REC * (n % PER)
        f.write_bytes(data[:o] + new.ljust(16).encode("ascii") + data[o + 16:]); print(f"patch de sinte {n}: «{sname_of(p)}» -> «{new}»")


if __name__ == "__main__":
    main()
