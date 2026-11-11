"""Example patches of the own synth of MIDI 1 / 2, after classic and popular synth sounds (the user, 2026-11-10: «Build example patches based
on traditional and popular synth patches. assign pertinent macro destinations to new and existing patches»; chosen: the own synth of MIDI 1 / 2,
patch files for the card).

    python tools/make_examples.py [OUT_DIR]          (default docs/patches/): NN_Name.ctm for every patch + README.md / LEEME.md (the list)

A .ctm here is a custom patch as tools/sd_app.html reads and uploads it (Parches custom → Subir): the record's padding (172 bytes,
tools/patchtool.py's layout) + the 8-operator FM record (224 bytes; 0xFF = none).  Every patch carries:
  * the engine and its 33 values (codes 1..34, vcf21's knob values: 0..127, or -64..63 for the bipolar ones), the LFO shape;
  * page 4's destinations (the 8 sequenceable knobs, p4dest, padding + 88) and the non-sequenceable page's (Shift + pad 4, padding + 130):
    the «macro» knobs of each sound, chosen for it (a bass: cutoff, resonance, envelope amount, decay …; a pad: attack, release, LFO …);
  * the voice mode (vmode, padding + 126), the one-oscillator sub / noise (oscmod.use_solo, + 142) or the two oscillators' LFO / envelope depths
    (oscmod, + 163), the FM block (+ 100: version 3, FM on only for the 8-operator ones).
The existing patches (the 48 instruments of the 8-operator FM, tools/fm8inst.py) come out too, with the destinations of their family
(FAM_DEST, the same table the firmware applies when an instrument is loaded from the pad 8 list: tools/fm8dest.py).
Values per knob: tools/patchtool.py PARAMS; the filter: types (DJ, LP 12, HP 12, BP, notch, LP 24, HP 24) by zone, the cutoff = (FILT + 64) / 2 of
64 steps of 8 per octave (with a type other than DJ), + ENVF steps at the envelope's top, + the key follow of the type's zone."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fm8inst as FI  # noqa: E402

PADN, RECN = 172, 224
NAME_AT, NAME_LEN = 44, 16
FM_AT, P4_AT, VM_AT, NS_AT, SO_AT, OM_AT = 100, 88, 126, 130, 142, 163
# code numbers (patchtool.PARAMS)
FILT, RES, ENVF, LFOF, ATK, DEC, SUS, REL, FXAMT, GAIN, LRATE, LFOV, FXTYPE, NOTE2, ENVA, FTYPE = range(1, 17)
TUNE, FINE, WAVE, SHAPE, LFOP, ENVP, ENVW, LFOW, ENVM, LFOM, TUNE2, FINE2, WAVE2, SHAPE2, MIX, BITSYNC, FM, RING = range(17, 35)
BIPOLAR = {FILT, ENVF, LFOF, LRATE, LFOV, ENVA, TUNE, FINE, LFOP, ENVP, ENVW, LFOW, ENVM, LFOM, TUNE2, FINE2}   # modmx.ranges() of SC55.6
HI100 = {SHAPE, SHAPE2}
NAMES = {FILT: "Filter", RES: "Resonance", ENVF: "Env > filter", LFOF: "LFO > filter", ATK: "Attack", DEC: "Decay", SUS: "Sustain", REL: "Release",
         FXAMT: "FX amount", GAIN: "VCA gain", LRATE: "LFO speed", LFOV: "LFO > level", FXTYPE: "FX type", ENVA: "Env > level", FTYPE: "Filter type",
         TUNE: "Tune", FINE: "Fine", WAVE: "Wave", SHAPE: "Shape", LFOP: "LFO > pitch", ENVP: "Env > pitch", ENVW: "Env > shape", LFOW: "LFO > shape",
         ENVM: "Env > morph", LFOM: "LFO > morph", TUNE2: "OSC 2 ratio", FINE2: "OSC 2 detune", WAVE2: "Wave 2", SHAPE2: "Shape 2", MIX: "Mix 1 / 2",
         BITSYNC: "Sync / bitwise", FM: "FM", RING: "Ring"}
NAMES_ES = {FILT: "Filtro", RES: "Resonancia", ENVF: "Env > filtro", LFOF: "LFO > filtro", ATK: "Ataque", DEC: "Decay", SUS: "Sustain", REL: "Release",
            FXAMT: "Efecto", GAIN: "Ganancia VCA", LRATE: "Velocidad LFO", LFOV: "LFO > nivel", FXTYPE: "Tipo de efecto", ENVA: "Env > nivel",
            FTYPE: "Tipo de filtro", TUNE: "Tono", FINE: "Fino", WAVE: "Onda", SHAPE: "Forma", LFOP: "LFO > tono", ENVP: "Env > tono", ENVW: "Env > forma",
            LFOW: "LFO > forma", ENVM: "Env > morph", LFOM: "LFO > morph", TUNE2: "Ratio OSC 2", FINE2: "Detune OSC 2", WAVE2: "Onda 2", SHAPE2: "Forma 2",
            MIX: "Mezcla 1 / 2", BITSYNC: "Sync / bitwise", FM: "FM", RING: "Ring"}
DEFAULTS = (0, 0, 0, 0, 0, 0, 127, 0, 0, 0, 20, 0, 0, 60, 63, 0, 0, 0, 0, 50, 0, 0, 0, 0, 0, 0) + (0, 0, 0, 50, 64, 0, 64, 0)   # vcf21.DEFAULTS + DEFAULTS_V2 (SC55.6)
LANE_TAB = (TUNE, REL, ENVA, ENVF, FILT, RES, LRATE, FXAMT)            # vcf21.LANE_TAB: page 4's factory destinations
NS_DEF = (ATK, DEC, SUS, SHAPE, LFOF, ENVP, MIX, GAIN)                  # vcf21.NS_DEF
ENGINES = {"osc": 0b0011, "va-drum": 0b0111}                           # patchtool.ENGINES (flags bits 0-3); bit 4 = two oscillators
SINE, TRI, SAW, SQUARE = 0, 42, 84, 126                                # WAVE (morph)
LS = {"rsaw": 0, "saw": 1, "tri": 2, "square": 3, "sine": 4, "sh": 5, "slew": 6}   # the LFO shapes (page 5, Shift + K8)
VMODE = {"retrig": 0, "legato": 1, "glide": 2, "poly": 3, "uni": 4, "uni legato": 5, "uni glide": 6, "uni always": 7}   # vmode's codes
DEST_DIV = 4


def zone(t, f=64, n=7):
    """a type knob (filter type, FX type, BITSYNC): zone t (0..n - 1) and its position f (0..127) -> the knob value p (7 p >> 7 = t, 7 p & 127 = f)"""
    p = (128 * t + f + 6) // 7
    assert (7 * p) >> 7 == t, (t, f, p)
    return min(p, 127)


# the filter types (zone) and the effect types
DJ, LP12, HP12, BP, NOTCH, LP24, HP24 = range(7)
SOFT, HARD, FOLD, WFOLD, RINGFX, COMB, CHORUS = range(7)
SYNC = 1                                                               # BITSYNC's sync zone


def ratio(r):
    """vcf21.r2_ratio inverted: OSC 2's TUNE value for ratio r (0.25, 0.5, 1, 2 .. 31)"""
    if r == 1: return 0
    if r == 0.5: return -16
    if r == 0.25: return -48
    v = next(v for v in range(1, 64) if 2 + (v - 1) * 30 // 63 == r)
    return v


def patch(name, cat, engine="osc", dual=False, lfo="tri", vm=("poly", 30, 40), p4=LANE_TAB, ns=NS_DEF, sub=None, noise=None, dep=None, fm8=None,
          desc="", desc_es="", **codes):
    v = list(DEFAULTS)
    for k, x in codes.items():
        c = globals()[k.upper()]
        v[c - 1] = x
    assert len(p4) == 8 and len(ns) == 8, name
    return dict(name=name, cat=cat, engine=engine, dual=dual, lfo=lfo, vm=vm, values=v, p4=tuple(p4), ns=tuple(ns), sub=sub, noise=noise, dep=dep,
                fm8=fm8, desc=desc, desc_es=desc_es)


# ---------------------------------------------------------------- the destinations by family (page 4 = sequenceable, page 8 = Shift + pad 4)
D_BASS = ((FILT, RES, ENVF, DEC, TUNE, FXAMT, REL, ENVA), (ATK, SUS, SHAPE, FTYPE, LFOF, LRATE, ENVP, GAIN))
D_ACID = ((FILT, RES, ENVF, DEC, TUNE, FXAMT, ENVA, LFOF), (SHAPE, ATK, SUS, REL, FTYPE, FXTYPE, LRATE, GAIN))
D_LEAD = ((FILT, RES, ENVF, LFOP, TUNE, FXAMT, REL, LRATE), (ATK, DEC, SUS, SHAPE, FINE2, MIX, ENVP, GAIN))
D_SYNC = ((BITSYNC, FILT, ENVF, LFOP, TUNE, FXAMT, REL, RES), (ENVW, SHAPE, TUNE2, FINE2, MIX, ATK, DEC, GAIN))
D_PAD = ((FILT, ATK, REL, LFOF, LRATE, FXAMT, SHAPE, RES), (DEC, SUS, ENVF, LFOW, FINE2, MIX, LFOV, GAIN))
D_PWM = ((FILT, SHAPE, LFOW, LRATE, ATK, REL, FXAMT, RES), (DEC, SUS, ENVF, LFOF, ENVW, FINE2, LFOV, GAIN))
D_BRASS = ((FILT, ENVF, ATK, DEC, RES, FXAMT, REL, LFOP), (SUS, SHAPE, FINE2, MIX, LRATE, ENVP, FTYPE, GAIN))
D_KEYS = ((FILT, DEC, REL, ENVF, RES, FXAMT, SHAPE, TUNE), (ATK, SUS, LFOP, LRATE, MIX, FINE2, FTYPE, GAIN))
D_BELL = ((RING, DEC, REL, FILT, TUNE2, FXAMT, FM, TUNE), (ATK, SUS, MIX, FINE2, LFOP, LRATE, RES, GAIN))
D_ORGAN = ((MIX, LFOP, LRATE, FILT, FXAMT, TUNE2, LFOV, REL), (ATK, DEC, SUS, WAVE, WAVE2, FINE2, RES, GAIN))
D_WOBBLE = ((LRATE, LFOF, FILT, RES, FXAMT, TUNE, ENVF, LFOV), (SHAPE, FINE2, MIX, FXTYPE, ATK, REL, FTYPE, GAIN))
D_DRUM = ((TUNE, DEC, ENVP, SUS, FILT, REL, LRATE, FXAMT), (ENVF, RES, FTYPE, WAVE, SHAPE, FXTYPE, ATK, GAIN))
D_FX = ((ENVP, TUNE, DEC, FILT, RES, LRATE, FXAMT, LFOP), (ATK, SUS, REL, ENVF, SHAPE, WAVE, FXTYPE, GAIN))
D_STRING = ((FILT, ATK, REL, FXAMT, LFOP, LRATE, SHAPE, RES), (DEC, SUS, ENVF, LFOF, FINE2, MIX, LFOV, GAIN))
# the 8-operator FM's families (tools/fm8inst.FAM / FAM2): the FM voices have their own envelopes (the VCA is open), the track's filter, effect,
# LFO and tune stay; so the knobs that matter are those (and the track envelope only through Env > filter)
FAM_DEST = {
    "keys": ((FILT, RES, ENVF, FXAMT, LFOP, LRATE, TUNE, GAIN), (DEC, SUS, REL, ATK, LFOF, FXTYPE, FTYPE, LFOV)),
    "bass": ((FILT, RES, ENVF, DEC, TUNE, FXAMT, GAIN, LFOF), (ATK, SUS, REL, FTYPE, FXTYPE, LRATE, LFOP, LFOV)),
    "lead": ((FILT, LFOP, LRATE, RES, FXAMT, TUNE, ENVF, GAIN), (ATK, DEC, SUS, REL, LFOF, FXTYPE, FTYPE, LFOV)),
    "pad": ((FILT, LFOF, LRATE, FXAMT, RES, LFOV, ENVF, GAIN), (ATK, DEC, SUS, REL, LFOP, FXTYPE, FTYPE, TUNE)),
    "pluck": ((FILT, ENVF, DEC, RES, FXAMT, TUNE, LFOP, GAIN), (ATK, SUS, REL, LFOF, LRATE, FXTYPE, FTYPE, LFOV)),
    "perc": ((TUNE, FILT, RES, FXAMT, ENVF, DEC, GAIN, LFOP), (ATK, SUS, REL, LFOF, LRATE, FXTYPE, FTYPE, LFOV)),
    "bell": ((FILT, FXAMT, LFOP, LRATE, TUNE, RES, LFOV, GAIN), (ATK, DEC, SUS, REL, ENVF, LFOF, FXTYPE, FTYPE)),
    "wind": ((FILT, LFOP, LRATE, FXAMT, RES, ENVF, LFOV, GAIN), (ATK, DEC, SUS, REL, LFOF, TUNE, FXTYPE, FTYPE)),
}

LP24K, LP12K, BPK, HP24K, HP12K = zone(LP24, 64), zone(LP12, 64), zone(BP, 64), zone(HP24, 64), zone(HP12, 64)
FX_SOFT, FX_HARD, FX_CHORUS, FX_FOLD, FX_COMB = zone(SOFT, 50), zone(HARD, 40), zone(CHORUS, 70), zone(FOLD, 60), zone(COMB, 64)

PATCHES = [
    # ---- basses
    patch("Ladder Bass", "bass", dual=True, vm=("legato", 0, 0), p4=D_BASS[0], ns=D_BASS[1],
          wave=SAW, shape=0, wave2=SQUARE, shape2=50, tune2=ratio(0.5), fine2=6, mix=56, ftype=LP24K, filt=-34, res=40, envf=38, atk=0, dec=46, sus=70, rel=18,
          fxtype=FX_SOFT, fxamt=24, desc="Two saws and a square an octave down into a 24 dB low-pass with a snappy envelope: the classic monophonic bass.",
          desc_es="Dos sierras y una cuadrada una octava abajo por un paso bajo de 24 dB con una envolvente seca: el bajo monofónico clásico."),
    patch("Acid Line", "bass", vm=("glide", 22, 0), p4=D_ACID[0], ns=D_ACID[1],
          wave=SAW, shape=0, ftype=LP24K, filt=-40, res=104, envf=44, atk=0, dec=34, sus=0, rel=10, fxtype=FX_SOFT, fxamt=46,
          desc="One saw, a resonant low-pass and a short decay, with glide on tied notes: the squelchy acid line (turn Filter, Resonance and Env > filter while it plays).",
          desc_es="Una sierra, paso bajo resonante y decay corto, con glide en las notas ligadas: la línea ácida (gira Filtro, Resonancia y Env > filtro mientras suena)."),
    patch("Reese Bass", "bass", dual=True, vm=("legato", 0, 0), p4=D_BASS[0], ns=(FINE2, ATK, SUS, SHAPE, LFOF, LRATE, MIX, GAIN),
          wave=SAW, shape=0, wave2=SAW, shape2=0, fine2=22, mix=64, ftype=LP24K, filt=-18, res=20, envf=8, atk=0, dec=60, sus=110, rel=24,
          lrate=8, lfof=6, fxtype=FX_SOFT, fxamt=30, desc="Two saws detuned against each other, slowly phasing: the drum & bass Reese (OSC 2 detune on Shift + pad 4).",
          desc_es="Dos sierras desafinadas entre sí que se mueven despacio: el Reese del drum & bass (detune del OSC 2 en Shift + pad 4)."),
    patch("Sub Bass", "bass", vm=("legato", 0, 0), sub=(90, 0, 0), p4=D_BASS[0], ns=D_BASS[1],
          wave=SINE, shape=50, ftype=LP12K, filt=20, res=0, atk=2, dec=60, sus=120, rel=20, fxtype=FX_SOFT, fxamt=18,
          desc="A sine with the sub-oscillator below: deep and clean, a touch of saturation to be heard on small speakers.",
          desc_es="Un seno con el sub-oscilador debajo: profundo y limpio, con algo de saturación para oírse en altavoces pequeños."),
    patch("Square Bass", "bass", vm=("retrig", 0, 0), sub=(60, 0, 0), p4=D_BASS[0], ns=D_BASS[1],
          wave=SQUARE, shape=38, ftype=LP24K, filt=-26, res=30, envf=30, atk=0, dec=40, sus=60, rel=14,
          desc="A slightly narrow pulse with the sub below and a plucked filter: the eighties poly-synth bass.",
          desc_es="Un pulso algo estrecho con el sub debajo y un filtro pellizcado: el bajo de los polifónicos de los ochenta."),
    patch("Wobble Bass", "bass", dual=True, lfo="sine", vm=("legato", 0, 0), p4=D_WOBBLE[0], ns=D_WOBBLE[1],
          wave=SAW, shape=30, wave2=SQUARE, tune2=ratio(0.5), mix=60, ftype=LP24K, filt=-30, res=70, lfof=44, lrate=-40, atk=0, dec=60, sus=127, rel=16,
          fxtype=FX_HARD, fxamt=40, desc="The LFO, synced to the tempo, sweeps a resonant low-pass: the dubstep wobble (LFO speed sets the division).",
          desc_es="El LFO, sincronizado al tempo, barre un paso bajo resonante: el wobble del dubstep (Velocidad LFO elige la división)."),
    patch("2-Op FM Bass", "bass", dual=True, vm=("retrig", 0, 0), p4=(FM, FILT, DEC, ENVF, TUNE, FXAMT, RES, REL), ns=(TUNE2, ATK, SUS, ENVA, FINE2, MIX, SHAPE, GAIN),
          wave=SINE, wave2=SINE, tune2=ratio(1), fm=84, mix=0, dep=(0, 0, 0, 0, 0, 40), ftype=LP12K, filt=10, res=10, envf=20, atk=0, dec=44, sus=40, rel=16,
          desc="A sine modulated by another sine, the FM falling with the envelope: the punchy digital bass of the eighties.",
          desc_es="Un seno modulado por otro seno, con la FM cayendo con la envolvente: el bajo digital con pegada de los ochenta."),
    # ---- leads
    patch("Classic Lead", "lead", dual=True, vm=("glide", 30, 0), lfo="tri", p4=D_LEAD[0], ns=D_LEAD[1],
          wave=SAW, shape=0, wave2=SAW, shape2=0, fine2=10, mix=64, ftype=LP24K, filt=4, res=30, envf=16, atk=2, dec=50, sus=100, rel=26, lrate=30, lfop=0,
          desc="Two saws slightly detuned into a warm low-pass, with glide: the monophonic lead of a thousand solos (LFO > pitch for vibrato).",
          desc_es="Dos sierras algo desafinadas por un paso bajo cálido, con glide: el solo monofónico de siempre (LFO > tono para el vibrato)."),
    patch("Hard Sync Lead", "lead", dual=True, vm=("legato", 0, 0), p4=D_SYNC[0], ns=D_SYNC[1],
          wave=SAW, shape=0, wave2=SAW, shape2=0, bitsync=zone(SYNC, 60), mix=96, ftype=LP12K, filt=30, res=10, envf=10, atk=0, dec=60, sus=110, rel=24,
          fxtype=FX_SOFT, fxamt=20, desc="OSC 2 hard-synced to OSC 1 and tuned up: the tearing sync lead (sweep Sync / bitwise).",
          desc_es="El OSC 2 sincronizado con el OSC 1 y afinado hacia arriba: el solo sync rasgado (barre Sync / bitwise)."),
    patch("Supersaw Lead", "lead", vm=("poly", 0, 0), p4=D_LEAD[0], ns=D_LEAD[1],
          wave=SAW, shape=100, ftype=LP12K, filt=36, res=8, envf=6, atk=0, dec=60, sus=110, rel=40, fxtype=FX_CHORUS, fxamt=40,
          desc="The seven-saw supersaw with chorus: the trance lead (Shape sets how wide the saws spread).",
          desc_es="La supersaw de siete sierras con chorus: el solo de trance (Forma abre o cierra las sierras)."),
    patch("Chip Lead", "lead", vm=("retrig", 0, 0), lfo="square", p4=(SHAPE, FILT, LFOP, LRATE, TUNE, REL, FXAMT, DEC), ns=(ATK, SUS, ENVP, LFOW, FTYPE, RES, ENVF, GAIN),
          wave=SQUARE, shape=24, ftype=DJ, filt=0, atk=0, dec=40, sus=110, rel=8, lrate=46, lfop=0,
          desc="A narrow pulse with no filter: the game console lead (LFO > pitch with the square LFO makes the trill).",
          desc_es="Un pulso estrecho sin filtro: el solo de consola (LFO > tono con el LFO cuadrado hace el trino)."),
    patch("Rave Hoover", "lead", dual=True, vm=("uni always", 50, 110), p4=(TUNE, FILT, ENVP, FXAMT, FINE2, REL, RES, LRATE), ns=(ATK, DEC, SUS, SHAPE, MIX, ENVF, LFOP, GAIN),
          wave=SAW, shape=60, wave2=SAW, shape2=40, fine2=30, mix=64, envp=-10, ftype=LP12K, filt=40, res=10, atk=0, dec=40, sus=110, rel=30,
          fxtype=FX_CHORUS, fxamt=60, desc="Detuned saws in unison that always slide, with a small pitch dip: the rave hoover.",
          desc_es="Sierras desafinadas en unísono que siempre deslizan, con una pequeña caída de tono: el hoover del rave."),
    patch("Whistle Lead", "lead", vm=("glide", 40, 0), lfo="sine", p4=D_LEAD[0], ns=D_LEAD[1],
          wave=SINE, shape=50, ftype=LP12K, filt=20, atk=10, dec=60, sus=120, rel=30, lrate=34, lfop=3, fxtype=FX_CHORUS, fxamt=20,
          desc="A pure sine with glide and a gentle vibrato: the portamento lead of the seventies.",
          desc_es="Un seno puro con glide y un vibrato suave: el solo con portamento de los setenta."),
    patch("Fold Lead", "lead", vm=("legato", 0, 0), p4=(SHAPE, ENVW, FILT, LFOW, LRATE, FXAMT, REL, TUNE), ns=(ATK, DEC, SUS, RES, LFOP, ENVF, FXTYPE, GAIN),
          wave=SINE, shape=90, envw=-20, ftype=LP12K, filt=40, atk=0, dec=50, sus=90, rel=24, fxtype=FX_FOLD, fxamt=20,
          desc="A wavefolded sine that opens and closes with the envelope: the west-coast lead.",
          desc_es="Un seno plegado (wavefold) que se abre y cierra con la envolvente: el solo de la costa oeste."),
    # ---- pads and strings
    patch("String Machine", "pad", vm=("poly", 0, 0), lfo="tri", p4=D_STRING[0], ns=D_STRING[1],
          wave=SAW, shape=0, ftype=LP12K, filt=26, res=0, atk=50, dec=60, sus=110, rel=60, fxtype=FX_CHORUS, fxamt=90, lrate=22,
          desc="A saw with a slow attack through a strong chorus: the string machine.",
          desc_es="Una sierra con ataque lento por un chorus fuerte: la máquina de cuerdas."),
    patch("Analog Pad", "pad", dual=True, vm=("poly", 0, 0), lfo="tri", p4=D_PAD[0], ns=D_PAD[1],
          wave=SAW, shape=10, wave2=SAW, shape2=10, fine2=12, mix=64, ftype=LP24K, filt=-6, res=14, envf=10, lfof=6, lrate=10,
          atk=64, dec=80, sus=110, rel=76, fxtype=FX_CHORUS, fxamt=50, desc="Two detuned saws, a dark low-pass breathing with a slow LFO, slow attack and release.",
          desc_es="Dos sierras desafinadas, paso bajo oscuro que respira con un LFO lento, ataque y release lentos."),
    patch("PWM Pad", "pad", vm=("poly", 0, 0), lfo="tri", p4=D_PWM[0], ns=D_PWM[1],
          wave=SQUARE, shape=50, lfow=24, lrate=14, ftype=LP12K, filt=20, res=6, atk=50, dec=60, sus=110, rel=70, fxtype=FX_CHORUS, fxamt=60,
          desc="A square whose width the LFO moves: the lush pulse-width pad.",
          desc_es="Una cuadrada cuyo ancho mueve el LFO: el pad de pulso modulado."),
    patch("Trance Pad", "pad", vm=("poly", 0, 0), p4=D_PAD[0], ns=D_PAD[1],
          wave=SAW, shape=90, ftype=LP12K, filt=20, res=10, lfof=4, lrate=12, atk=40, dec=80, sus=120, rel=80, fxtype=FX_CHORUS, fxamt=50,
          desc="A wide supersaw with slow attack and long release: the euphoric pad.",
          desc_es="Una supersaw ancha con ataque lento y release largo: el pad eufórico."),
    patch("Sweep Pad", "pad", dual=True, vm=("poly", 0, 0), p4=(FILT, ENVF, ATK, DEC, RES, REL, FXAMT, LFOF), ns=(SUS, LRATE, LFOW, SHAPE, FINE2, MIX, LFOV, GAIN),
          wave=SAW, shape=20, wave2=SQUARE, fine2=8, mix=56, ftype=LP24K, filt=-44, res=60, envf=54, atk=90, dec=100, sus=60, rel=90,
          fxtype=FX_CHORUS, fxamt=40, desc="A slow envelope sweeps a resonant low-pass open and shut: the filter-sweep pad.",
          desc_es="Una envolvente lenta abre y cierra un paso bajo resonante: el pad de barrido de filtro."),
    patch("Ring Glass Pad", "pad", dual=True, vm=("poly", 0, 0), lfo="sine", p4=D_BELL[0], ns=D_BELL[1],
          wave=SINE, wave2=SINE, tune2=ratio(2), fine2=4, mix=50, ring=40, ftype=LP12K, filt=40, atk=40, dec=90, sus=90, rel=90,
          lrate=16, fxtype=FX_CHORUS, fxamt=60, desc="Two sines an octave apart with some ring modulation and chorus: a glassy, airy pad.",
          desc_es="Dos senos a una octava con algo de ring y chorus: un pad cristalino y aireado."),
    # ---- brass, keys, plucks
    patch("Synth Brass", "brass", dual=True, vm=("poly", 0, 0), lfo="tri", p4=D_BRASS[0], ns=D_BRASS[1],
          wave=SAW, shape=0, wave2=SAW, shape2=0, fine2=8, mix=64, ftype=LP24K, filt=-28, res=12, envf=40, atk=14, dec=56, sus=90, rel=30, lrate=30,
          fxtype=FX_CHORUS, fxamt=30, desc="Two saws, the low-pass swelling with the envelope's attack: the eighties synth brass.",
          desc_es="Dos sierras con el paso bajo que se abre con el ataque de la envolvente: los metales sintéticos de los ochenta."),
    patch("Rave Stab", "brass", vm=("poly", 0, 0), p4=(FILT, DEC, RES, ENVF, FXAMT, SHAPE, REL, TUNE), ns=D_BRASS[1],
          wave=SAW, shape=80, ftype=LP12K, filt=24, res=20, envf=30, atk=0, dec=36, sus=0, rel=24, fxtype=FX_CHORUS, fxamt=40,
          desc="A short, bright supersaw chord: the rave stab (play it as a chord).",
          desc_es="Un acorde corto y brillante de supersaw: el stab del rave (tócalo como acorde)."),
    patch("Poly Pluck", "keys", vm=("poly", 0, 0), p4=D_KEYS[0], ns=D_KEYS[1],
          wave=SAW, shape=10, ftype=LP12K, filt=-20, res=30, envf=44, atk=0, dec=30, sus=0, rel=30, fxtype=FX_CHORUS, fxamt=30,
          desc="A saw whose filter snaps shut: the plucked poly sound of house and pop.",
          desc_es="Una sierra cuyo filtro se cierra de golpe: el sonido pellizcado del house y el pop."),
    patch("Arp Pluck", "keys", vm=("retrig", 0, 0), sub=(40, 0, 0), p4=D_KEYS[0], ns=D_KEYS[1],
          wave=SQUARE, shape=40, ftype=LP24K, filt=-16, res=40, envf=36, atk=0, dec=26, sus=0, rel=14,
          desc="A short square with a resonant filter blip: made for the arpeggiator.",
          desc_es="Una cuadrada corta con un golpe de filtro resonante: hecha para el arpegiador."),
    patch("Drawbar Organ", "keys", dual=True, vm=("poly", 0, 0), lfo="sine", p4=D_ORGAN[0], ns=D_ORGAN[1],
          wave=SINE, wave2=SINE, tune2=ratio(2), mix=52, ftype=DJ, filt=0, atk=2, dec=60, sus=127, rel=8, lrate=40, lfop=1, fxtype=FX_SOFT, fxamt=20,
          desc="Two sines a fundamental and an octave up with a light vibrato: a simple drawbar organ (Mix sets the drawbars, OSC 2 ratio the footage).",
          desc_es="Dos senos, fundamental y octava, con un vibrato suave: un órgano sencillo (Mezcla son los registros, Ratio OSC 2 el pie)."),
    patch("Pulse Clav", "keys", vm=("poly", 0, 0), p4=D_KEYS[0], ns=D_KEYS[1],
          wave=SQUARE, shape=12, ftype=HP12K, filt=-24, res=20, envf=0, atk=0, dec=34, sus=10, rel=10, fxtype=FX_SOFT, fxamt=30,
          desc="A very narrow pulse through a high-pass with a short decay: a funky clavinet.",
          desc_es="Un pulso muy estrecho por un paso alto con decay corto: un clavinet funky."),
    patch("Ring Bell", "bell", dual=True, vm=("poly", 0, 0), p4=D_BELL[0], ns=D_BELL[1],
          wave=SINE, wave2=SINE, tune2=ratio(3), ring=110, mix=30, ftype=LP12K, filt=50, atk=0, dec=70, sus=0, rel=70, fxtype=FX_CHORUS, fxamt=30,
          desc="Two sines a ratio of 3 apart through the ring modulator: a metallic bell (OSC 2 ratio changes the metal).",
          desc_es="Dos senos a ratio 3 por el modulador en anillo: una campana metálica (Ratio OSC 2 cambia el metal)."),
    # ---- drums and effects (VA-drum)
    patch("Boom Kick", "drum", engine="va-drum", vm=("poly", 0, 0), p4=D_DRUM[0], ns=D_DRUM[1],
          wave=SINE, tune=-24, envp=40, sus=30, dec=80, rel=20, lrate=-64, ftype=LP12K, filt=30, fxtype=FX_SOFT, fxamt=30,
          desc="A sine with a falling pitch envelope and a long decay: the classic drum-machine kick (Decay = its length, Env > pitch = the punch).",
          desc_es="Un seno con envolvente de tono descendente y decay largo: el bombo de caja de ritmos clásico (Decay = su largo, Env > tono = la pegada)."),
    patch("Tom", "drum", engine="va-drum", vm=("poly", 0, 0), p4=D_DRUM[0], ns=D_DRUM[1],
          wave=SINE, tune=0, envp=24, sus=40, dec=50, lrate=-50, ftype=LP12K, filt=40,
          desc="A tuned sine drum with a short pitch drop: an electronic tom (play it on several notes).",
          desc_es="Un tambor de seno afinado con una caída corta de tono: un tom electrónico (tócalo en varias notas)."),
    patch("Analog Snare", "drum", engine="va-drum", vm=("poly", 0, 0), p4=(LRATE, DEC, TUNE, ENVP, FILT, REL, ENVF, FXAMT), ns=D_DRUM[1],
          wave=TRI, tune=12, envp=20, sus=20, dec=36, rel=30, lrate=40, ftype=HP12K, filt=-40, envf=10, fxtype=FX_HARD, fxamt=20,
          desc="A short triangle body and white noise through a high-pass: an analogue snare (LFO speed = the noise level).",
          desc_es="Un cuerpo corto de triángulo y ruido blanco por un paso alto: una caja analógica (Velocidad LFO = el nivel del ruido)."),
    patch("Analog Hat", "drum", engine="va-drum", vm=("poly", 0, 0), p4=(DEC, FILT, LRATE, RES, REL, TUNE, FXAMT, ENVF), ns=D_DRUM[1],
          wave=SQUARE, tune=36, sus=10, dec=18, rel=20, lrate=63, ftype=HP24K, filt=30, res=20, fxtype=FX_HARD, fxamt=10,
          desc="Noise and a high square through a 24 dB high-pass with a very short decay: a closed hi-hat (a longer Decay opens it).",
          desc_es="Ruido y una cuadrada aguda por un paso alto de 24 dB con un decay muy corto: un charles cerrado (más Decay lo abre)."),
    patch("Laser Zap", "fx", engine="va-drum", vm=("poly", 0, 0), p4=D_FX[0], ns=D_FX[1],
          wave=SAW, tune=24, envp=63, sus=36, dec=46, lrate=-64, ftype=LP12K, filt=50, res=40, fxtype=FX_CHORUS, fxamt=30,
          desc="A saw that falls several octaves in an instant: the laser zap.",
          desc_es="Una sierra que cae varias octavas en un instante: el disparo láser."),
    patch("Noise Sweep", "fx", vm=("poly", 0, 0), lfo="tri", noise=(100, 0, 0), sub=None, p4=(FILT, LFOF, LRATE, RES, ATK, REL, FXAMT, ENVF),
          ns=(DEC, SUS, FTYPE, FXTYPE, LFOV, SHAPE, WAVE, GAIN),
          wave=SINE, ftype=BPK, filt=-10, res=80, lfof=40, lrate=6, atk=80, dec=90, sus=127, rel=90, enva=63, gain=0, fxtype=FX_CHORUS, fxamt=40,
          desc="Noise through a resonant band-pass swept by a slow LFO: a wind / riser effect (the oscillator's level, Shift + pad 4 K8, at 0 for pure noise).",
          desc_es="Ruido por un paso banda resonante que barre un LFO lento: un efecto de viento / subida."),
]


def solo_block(sub, noise):
    """oscmod.use_solo (padding + 142): 0xC5, the 6 values in oscmod.SO_MAP's order (LFO > sub, LFO > noise, noise level, env > noise, sub level,
    env > sub; the levels stored -64..63 = 0..127), a check byte"""
    sl, sd, se = sub or (0, 0, 0)                                       # (level 0..127, LFO depth, env depth)
    nl, nd, ne = noise or (0, 0, 0)
    vals = [sd, nd, nl - 64, ne, sl - 64, se]
    b = bytes([0xC5] + [v & 0xFF for v in vals])
    return b + bytes([(0x5A + sum(b)) & 0xFF])


def dep_block(dep):
    """oscmod (padding + 163): 0xC4, the 6 depths (LFO > mix, env > mix, LFO > ring, env > ring, LFO > FM, env > FM), a check byte"""
    b = bytes([0xC4] + [v & 0xFF for v in (dep or (0,) * 6)])
    return b + bytes([(0x5A + sum(b)) & 0xFF])


def dest_block(tag, codes):
    b = tag.encode("ascii") + bytes([1]) + bytes(codes)
    return b + bytes([(0x5A + sum(b)) & 0xFF])


def fm_block(on):
    b = bytes([0x46, 0x4D, 3, 1 if on else 0]) + bytes(16)
    return b + bytes([(0x5A + sum(b)) & 0xFF])


def fm8_record(params):
    """fm8store's record of a slot (4096 + 512 (n & 7) of the bank): "FM8", 1, the 216 parameters, their 16-bit sum (0x5A38 + the bytes), 0xFF to 224"""
    r = bytearray(b"\xFF" * RECN)
    r[0:4] = b"FM8\x01"; r[4:4 + len(params)] = params
    s = (0x5A38 + sum(params)) & 0xFFFF
    r[4 + len(params)], r[5 + len(params)] = s & 0xFF, s >> 8
    return bytes(r)


def build(p):
    pad = bytearray(b"\xFF" * PADN)
    pad[0:4] = b"CTM1"
    pad[4] = ENGINES[p["engine"]] | (0x10 if p["dual"] else 0)
    pad[5] = 0
    for c in range(1, 35):
        v = p["values"][c - 1]
        lo, hi = (-64, 63) if c in BIPOLAR else (0, 100 if c in HI100 else 127)
        assert lo <= v <= hi, (p["name"], NAMES[c], v)
        pad[5 + c] = v & 0xFF
    pad[40] = sum(pad[4:40]) & 0xFF
    pad[41], pad[42] = 2, LS[p["lfo"]]
    nm = p["name"][:NAME_LEN].ljust(NAME_LEN)
    pad[NAME_AT:NAME_AT + NAME_LEN] = nm.encode("ascii")
    pad[P4_AT:P4_AT + 12] = dest_block("P4", p["p4"])
    pad[NS_AT:NS_AT + 12] = dest_block("NS", p["ns"])
    pad[FM_AT:FM_AT + 21] = fm_block(p["fm8"] is not None)
    mode, tm, det = p["vm"]
    pad[VM_AT:VM_AT + 4] = bytes([0xB6, 0x50 | VMODE[mode], tm, det])
    if p["engine"] == "osc" and not p["dual"]: pad[SO_AT:SO_AT + 8] = solo_block(p["sub"], p["noise"])
    pad[OM_AT:OM_AT + 8] = dep_block(p["dep"])                           # always: without it a build converts code 33 (FM) from the old 0..127 scale
    assert len(pad) == PADN
    rec = fm8_record(p["fm8"]) if p["fm8"] is not None else b"\xFF" * RECN
    return bytes(pad) + rec


def fm8_patches():
    """the 48 instruments of the 8-operator FM as custom patches: the oscillator with FM on, poly (the SD app's DX7 import: vmode poly, 48, 40),
    the track's filter open, the destinations of their family"""
    FI.use_v2()
    out = []
    for i, x in enumerate(FI.INST):
        p4, ns = FAM_DEST[x["fam"]]
        out.append(patch(x["name"], "fm-" + x["fam"], vm=("poly", 48, 40), p4=p4, ns=ns, fm8=FI.inst_full(i),
                         desc=f"The 8-operator FM instrument «{x['name']}» (pad 8 list, family {x['fam']}).",
                         desc_es=f"El instrumento FM de 8 operadores «{x['name']}» (lista del pad 8, familia {x['fam']})."))
    return out


def readme(rows, es):
    T = (lambda e, s: s) if es else (lambda e, s: e)
    N = NAMES_ES if es else NAMES
    out = [f"# {T('Example patches of the own synth (MIDI 1 / 2)', 'Patches de ejemplo del sinte propio (MIDI 1 / 2)')}", "",
           T("Made by `tools/make_examples.py`. Upload them with the card app (`tools/sd_app.html`: **Custom patches → Upload .ctm**) into free slots "
             "of a pack, then load them from the MIDI 1 / 2 Preset view (pads 9-24, Octave for the pages). Each one sets its engine, its values and "
             "the destinations of **page 4** (the 8 sequenceable knobs, the ones you can record) and of **Shift + pad 4** (8 non-sequenceable knobs): "
             "the knobs worth turning for that sound. The firmware needs Beta 5.42 or later for the FM instruments' destinations to change when "
             "you load one from the pad 8 list; the files work on any build with the own synth's patches (the parts a build does not know are ignored).",
             "Hechos por `tools/make_examples.py`. Súbelos con la app de la tarjeta (`tools/sd_app.html`: **Parches custom → Subir .ctm**) a huecos "
             "libres de un pack y cárgalos desde la vista Preset de MIDI 1 / 2 (pads 9-24, Octave para las páginas). Cada uno pone su motor, sus "
             "valores y los destinos de la **página 4** (los 8 knobs secuenciables, los que se graban) y de **Shift + pad 4** (8 knobs no "
             "secuenciables): los knobs que merece la pena girar en ese sonido. Para que los instrumentos FM cambien sus destinos al cargarlos desde "
             "la lista del pad 8 hace falta la Beta 5.42 o posterior; los ficheros funcionan en cualquier versión con los parches del sinte propio "
             "(lo que una versión no conoce se ignora)."), "",
           f"| # | {T('Patch', 'Patch')} | {T('Engine', 'Motor')} | {T('Page 4 (K1-K8)', 'Página 4 (K1-K8)')} | {T('Shift + pad 4 (K1-K8)', 'Shift + pad 4 (K1-K8)')} | {T('Sound', 'Sonido')} |",
           "|---|---|---|---|---|---|"]
    for i, (fn, p) in enumerate(rows):
        eng = "FM 8" if p["fm8"] is not None else {"osc": T("2 osc", "2 osc") if p["dual"] else T("oscillator", "oscilador"), "va-drum": "VA-drum"}[p["engine"]]
        out.append(f"| {i + 1} | [{p['name']}]({fn}) | {eng} | {', '.join(N[c] for c in p['p4'])} | {', '.join(N[c] for c in p['ns'])} | "
                   f"{p['desc_es'] if es else p['desc']} |")
    return "\n".join(out) + "\n"


def main(out_dir="docs/patches"):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    rows = []
    allp = PATCHES + fm8_patches()
    assert len({p["name"] for p in allp}) == len(allp)
    for i, p in enumerate(allp):
        fn = f"{i + 1:02d}_{p['name'].replace(' ', '_').replace('.', '').replace('/', '-')}.ctm"
        (out / fn).write_bytes(build(p))
        rows.append((fn, p))
    (out / "README.md").write_text(readme(rows, False), encoding="utf-8")
    (out / "LEEME.md").write_text(readme(rows, True), encoding="utf-8")
    print(f"{len(rows)} patches ({len(PATCHES)} new, {len(rows) - len(PATCHES)} FM instruments) in {out}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
