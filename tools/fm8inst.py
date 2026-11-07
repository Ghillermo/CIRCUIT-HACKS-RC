"""SC51.8 / Beta 5.21: the instruments of the 8-operator FM (pad 8 held, pads 9-32; the user, 2026-11-05: «A lot of pads are just bells? add more
interesting instruments instead. Also give pads color for their type», «24 on pads 9-32», «Track-style palette»).  They replace the 4-operator
starters (fmeng.STARTERS, converted) on pad 8.

Written in DX7 units (fm8's own); a compact record of ISZ bytes each (the ARM's c_fminst unpacks it, inst_full() here byte for byte):
  8 operators x 14: R1-R4, L1-L4, output level, coarse, fine, detune, KVS | RS << 3 | mode << 6, right depth (break point 39 = C3, the left depth,
  the curves (-LIN), AMS 0);  the pitch envelope R1-R4, L1-L4;  the algorithm (fm8's index: 0-15 the old 16, 16-47 the DX7's 1-32, 48-55 the
  eight-operator ones), feedback (0..127), key sync, transpose, noise, the noise's operator.
The colour of a pad = its family (bright = the one loaded)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fm8 as F  # noqa: E402

OPB_C = 14
ISZ = 8 * OPB_C + 8 + 6
FB_DX7 = F.FB_DX7                                     # the DX7's feedback 0..7 (the phase index doubles a step) -> fm8's (the coefficient ~ fb^2)
FAM = {"keys": (0x45, 0x46), "bass": (0x09, 0x0F), "lead": (0x53, 0x54), "pad": (0x17, 0x18), "pluck": (0x2D, 0x2E), "perc": (0x01, 0x02),
       "bell": (0x49, 0x4A)}                          # (bright, dim): orange, blue, red, green, yellow, white, violet (none animated)


def op(r=(99, 99, 99, 60), l=(99, 99, 99, 0), ol=0, crs=1, fine=0, det=7, kvs=0, rs=0, mode=0, rd=0):
    return dict(r=r, l=l, ol=ol, crs=crs, fine=fine, det=det, kvs=kvs, rs=rs, mode=mode, rd=rd)


OFF = op()


def dx(n):                                            # the DX7's algorithm n (1..32) -> fm8's index
    return 15 + n


def inst(name, fam, alg, fb, ops, peg=((99, 99, 99, 99), (50, 50, 50, 50)), trn=24, nz=0, nzop=0, sync=1):
    ops = list(ops) + [OFF] * (8 - len(ops))
    return dict(name=name, fam=fam, alg=alg, fb=fb, ops=ops, peg=peg, trn=trn, nz=nz, nzop=nzop, sync=sync)


K, M = (99, 99, 99, 0), None                          # (helpers for reading)
INST = [
    # ---- keys (orange)
    inst("E.Piano", "keys", dx(5), FB_DX7[6], [
        op((96, 25, 25, 67), (99, 75, 0, 0), 99, 1, kvs=2, rs=3),
        op((95, 50, 35, 78), (99, 75, 0, 0), 58, 14, kvs=7, rs=3, rd=30),
        op((95, 20, 20, 50), (99, 95, 0, 0), 99, 1, kvs=2, rs=3),
        op((95, 29, 20, 50), (99, 95, 0, 0), 86, 1, kvs=6, rs=3, rd=25),
        op((95, 20, 20, 50), (99, 95, 0, 0), 99, 1, det=10, kvs=2, rs=3),
        op((95, 29, 20, 50), (99, 95, 0, 0), 76, 1, det=4, kvs=6, rs=3, rd=25)]),
    inst("Bright EP", "keys", dx(5), FB_DX7[4], [
        op((98, 30, 25, 65), (99, 70, 0, 0), 99, 1, kvs=3, rs=3),
        op((98, 55, 35, 75), (99, 60, 0, 0), 68, 14, kvs=7, rs=3, rd=35),
        op((96, 25, 22, 55), (99, 90, 0, 0), 97, 1, det=9, kvs=3, rs=3),
        op((96, 35, 25, 55), (99, 85, 0, 0), 90, 1, kvs=6, rs=3, rd=30),
        op((96, 25, 22, 55), (99, 90, 0, 0), 90, 2, det=5, kvs=3, rs=3),
        op((96, 45, 30, 55), (99, 60, 0, 0), 70, 3, kvs=6, rs=3, rd=30)]),
    inst("Clav", "keys", dx(5), FB_DX7[5], [
        op((99, 45, 30, 85), (99, 50, 0, 0), 99, 1, kvs=3, rs=2),
        op((99, 60, 40, 85), (99, 30, 0, 0), 84, 3, kvs=6, rs=2),
        op((99, 45, 30, 85), (99, 50, 0, 0), 92, 2, kvs=3, rs=2),
        op((99, 65, 40, 85), (99, 25, 0, 0), 72, 5, kvs=6, rs=2),
        op((99, 45, 30, 85), (99, 50, 0, 0), 86, 1, det=9, kvs=3, rs=2),
        op((99, 60, 40, 85), (99, 30, 0, 0), 76, 1, kvs=5, rs=2)]),
    inst("Organ", "keys", dx(32), FB_DX7[2], [
        op((99, 99, 99, 85), K, 99, 1, rs=1),
        op((99, 99, 99, 85), K, 92, 0, rs=1),
        op((99, 99, 99, 85), K, 90, 2, rs=1),
        op((99, 99, 99, 85), K, 84, 3, det=8, rs=1),
        op((99, 99, 99, 85), K, 80, 4, rs=1),
        op((99, 99, 99, 85), K, 72, 6, det=6, rs=1)]),
    inst("Marimba", "keys", dx(5), 0, [
        op((99, 45, 30, 60), (99, 0, 0, 0), 99, 1, kvs=3, rs=3),
        op((99, 75, 40, 60), (99, 0, 0, 0), 72, 4, kvs=5, rs=3),
        op((99, 60, 40, 60), (99, 0, 0, 0), 76, 4, det=8, kvs=3, rs=3),
        op((99, 85, 50, 60), (99, 0, 0, 0), 50, 10, kvs=5, rs=3)]),
    inst("Vibes", "keys", dx(5), 0, [
        op((99, 30, 25, 40), (99, 60, 0, 0), 99, 1, kvs=3, rs=2),
        op((99, 50, 30, 40), (99, 40, 0, 0), 62, 4, kvs=5, rs=2),
        op((99, 40, 25, 40), (99, 0, 0, 0), 80, 4, det=8, kvs=3, rs=2),
        op((99, 45, 30, 40), (99, 0, 0, 0), 40, 1, kvs=4, rs=2)]),
    # ---- bass (blue)
    inst("FM Bass", "bass", dx(5), FB_DX7[5], [
        op((99, 40, 30, 70), (99, 80, 70, 0), 99, 0, kvs=2, rs=1),
        op((99, 55, 30, 70), (99, 50, 0, 0), 85, 0, kvs=4, rs=1),
        op((99, 40, 30, 70), (99, 80, 70, 0), 88, 0, det=9, kvs=2, rs=1),
        op((99, 60, 30, 70), (99, 30, 0, 0), 75, 1, fine=50, kvs=4, rs=1),
        op((99, 80, 50, 70), (99, 0, 0, 0), 70, 1, kvs=3, rs=1),
        op((99, 85, 60, 70), (99, 0, 0, 0), 50, 7, kvs=4, rs=1)]),
    inst("Synth Bass", "bass", 0, FB_DX7[6], [
        op((99, 50, 35, 70), (99, 85, 75, 0), 99, 0, kvs=2, rs=1),
        op((99, 60, 30, 70), (99, 55, 40, 0), 80, 0, kvs=5, rs=1),
        op((99, 70, 40, 70), (99, 30, 0, 0), 70, 1, kvs=5, rs=1),
        op((99, 80, 50, 70), (99, 0, 0, 0), 60, 1, kvs=5, rs=1)]),
    inst("Deep Bass", "bass", 4, FB_DX7[3], [
        op((90, 40, 30, 72), (99, 92, 85, 0), 99, 0, kvs=2),
        op((99, 45, 30, 72), (99, 40, 30, 0), 62, 0, kvs=4),
        op((90, 40, 30, 72), (99, 90, 80, 0), 80, 1, det=8, kvs=2),
        op((99, 55, 35, 72), (99, 30, 0, 0), 50, 2, kvs=4)]),
    # ---- leads and brass (red)
    inst("Brass", "lead", dx(22), FB_DX7[6], [
        op((60, 40, 30, 60), (99, 92, 88, 0), 99, 1, kvs=2, rs=2),
        op((55, 40, 30, 60), (99, 80, 75, 0), 82, 1, kvs=4, rs=2),
        op((60, 40, 30, 60), (99, 92, 88, 0), 95, 1, det=8, kvs=2, rs=2),
        op((60, 40, 30, 60), (99, 92, 88, 0), 95, 1, det=6, kvs=2, rs=2),
        op((60, 40, 30, 60), (99, 92, 88, 0), 90, 1, det=9, kvs=2, rs=2),
        op((55, 45, 30, 60), (99, 75, 70, 0), 78, 1, kvs=4, rs=2)], peg=((90, 60, 99, 99), (45, 50, 50, 50))),
    inst("Sync Lead", "lead", dx(2), FB_DX7[7], [
        op((99, 60, 40, 70), (99, 90, 85, 0), 99, 1, kvs=1, rs=1),
        op((99, 50, 35, 70), (99, 88, 80, 0), 85, 1, kvs=3, rs=1),
        op((99, 60, 40, 70), (99, 90, 85, 0), 80, 2, det=9, kvs=1, rs=1),
        op((99, 55, 35, 70), (99, 80, 70, 0), 70, 3, kvs=3, rs=1)]),
    inst("Flute", "lead", dx(5), FB_DX7[1], [
        op((65, 40, 30, 60), (99, 95, 92, 0), 99, 1, kvs=2, rs=1),
        op((60, 40, 30, 60), (99, 90, 85, 0), 55, 1, kvs=4, rs=1),
        op((70, 45, 30, 60), (99, 90, 85, 0), 70, 2, det=8, kvs=2, rs=1),
        op((60, 40, 30, 60), (99, 85, 80, 0), 40, 1, kvs=3, rs=1)], nz=18, nzop=0),
    # ---- pads and strings (green)
    inst("Strings", "pad", dx(1), FB_DX7[5], [
        op((45, 30, 25, 50), (99, 95, 92, 0), 99, 1, kvs=1, rs=1),
        op((45, 30, 25, 50), (99, 92, 90, 0), 72, 1, kvs=3, rs=1),
        op((45, 30, 25, 50), (99, 95, 92, 0), 97, 1, det=10, kvs=1, rs=1),
        op((45, 30, 25, 50), (99, 90, 88, 0), 60, 3, kvs=3, rs=1),
        op((45, 30, 25, 50), (99, 90, 88, 0), 55, 1, det=5, kvs=3, rs=1),
        op((45, 30, 25, 50), (99, 90, 88, 0), 50, 1, kvs=3, rs=1)]),
    inst("Warm Pad", "pad", dx(5), FB_DX7[3], [
        op((35, 25, 20, 40), (99, 95, 90, 0), 95, 1, det=4, kvs=1),
        op((30, 25, 20, 40), (99, 90, 85, 0), 60, 1, kvs=2),
        op((35, 25, 20, 40), (99, 95, 90, 0), 95, 1, det=10, kvs=1),
        op((30, 25, 20, 40), (99, 90, 85, 0), 50, 2, kvs=2),
        op((35, 25, 20, 40), (99, 95, 90, 0), 92, 1, det=7, kvs=1),
        op((30, 25, 20, 40), (99, 90, 85, 0), 55, 1, kvs=2)]),
    inst("Choir", "pad", dx(5), FB_DX7[2], [
        op((40, 30, 25, 45), (99, 92, 88, 0), 99, 1, kvs=1),
        op((40, 30, 25, 45), (99, 88, 85, 0), 55, 2, kvs=2),
        op((40, 30, 25, 45), (99, 92, 88, 0), 82, 3, det=8, kvs=1),
        op((40, 30, 25, 45), (99, 85, 80, 0), 50, 1, kvs=2),
        op((40, 30, 25, 45), (99, 92, 88, 0), 70, 4, det=6, kvs=1),
        op((40, 30, 25, 45), (99, 85, 80, 0), 45, 1, kvs=2)], nz=10, nzop=0),
    inst("Glass Pad", "pad", dx(5), FB_DX7[2], [
        op((40, 28, 22, 45), (99, 92, 88, 0), 99, 1, kvs=1),
        op((35, 25, 20, 45), (99, 85, 80, 0), 48, 7, kvs=3, rd=20),
        op((40, 28, 22, 45), (99, 92, 88, 0), 88, 2, det=9, kvs=1),
        op((35, 25, 20, 45), (99, 85, 80, 0), 42, 5, kvs=3, rd=20),
        op((40, 28, 22, 45), (99, 92, 88, 0), 85, 1, det=5, kvs=1),
        op((35, 25, 20, 45), (99, 80, 75, 0), 45, 1, kvs=2)]),
    # ---- plucks (yellow)
    inst("Harp", "pluck", dx(5), 0, [
        op((99, 40, 30, 40), (99, 0, 0, 0), 99, 1, kvs=3, rs=3),
        op((99, 55, 35, 40), (99, 0, 0, 0), 70, 1, kvs=5, rs=3),
        op((99, 45, 30, 40), (99, 0, 0, 0), 80, 2, det=8, kvs=3, rs=3),
        op((99, 60, 40, 40), (99, 0, 0, 0), 50, 4, kvs=5, rs=3)]),
    inst("Koto", "pluck", dx(5), FB_DX7[4], [
        op((99, 50, 35, 60), (99, 0, 0, 0), 99, 1, kvs=3, rs=3),
        op((99, 70, 40, 60), (99, 0, 0, 0), 82, 3, kvs=5, rs=3),
        op((99, 55, 35, 60), (99, 0, 0, 0), 85, 1, det=10, kvs=3, rs=3),
        op((99, 80, 50, 60), (99, 0, 0, 0), 60, 5, kvs=5, rs=3)]),
    inst("Nylon", "pluck", dx(5), FB_DX7[5], [
        op((99, 42, 30, 55), (99, 40, 0, 0), 99, 1, kvs=3, rs=2),
        op((99, 60, 40, 60), (99, 20, 0, 0), 75, 1, kvs=5, rs=2),
        op((99, 45, 30, 55), (99, 30, 0, 0), 85, 2, det=8, kvs=3, rs=2),
        op((99, 70, 45, 60), (99, 0, 0, 0), 55, 3, kvs=5, rs=2)]),
    # ---- percussion (white)
    inst("Kick", "perc", 8, 0, [
        op((99, 55, 35, 55), (99, 0, 0, 0), 99, 0, kvs=2),
        op((99, 85, 50, 60), (99, 0, 0, 0), 55, 0, kvs=4)], peg=((99, 62, 99, 99), (70, 50, 50, 50)), trn=12),
    inst("Snare", "perc", 9, 0, [
        op((99, 65, 40, 65), (99, 0, 0, 0), 95, 1, kvs=2),
        op((99, 80, 50, 65), (99, 0, 0, 0), 60, 1, fine=50, kvs=3)], peg=((99, 70, 99, 99), (58, 50, 50, 50)), nz=100, nzop=0),
    inst("Hi-Hat", "perc", 10, 0, [
        op((99, 80, 60, 80), (99, 0, 0, 0), 85, 7, kvs=2),
        op((99, 99, 99, 99), K, 85, 11, fine=41),
        op((99, 99, 99, 99), K, 80, 15, fine=2),
        op((99, 99, 99, 99), K, 80, 9, fine=78)], nz=70, nzop=0),
    # ---- bells and fx (violet)
    inst("Tubular Bell", "bell", dx(5), 0, [
        op((99, 30, 22, 30), (99, 0, 0, 0), 99, 1, kvs=2, rs=2),
        op((99, 35, 25, 30), (99, 0, 0, 0), 75, 3, fine=50, kvs=4, rs=2),
        op((99, 30, 22, 30), (99, 0, 0, 0), 85, 1, det=10, kvs=2, rs=2),
        op((99, 35, 25, 30), (99, 0, 0, 0), 70, 1, fine=41, kvs=4, rs=2)]),
    inst("Space Sweep", "bell", dx(5), FB_DX7[4], [
        op((30, 20, 15, 25), (99, 90, 80, 0), 99, 1),
        op((20, 15, 12, 25), (99, 70, 60, 0), 70, 1, fine=50),
        op((30, 20, 15, 25), (99, 90, 80, 0), 85, 2, det=11),
        op((20, 15, 12, 25), (99, 75, 60, 0), 60, 3)], peg=((20, 15, 99, 40), (80, 40, 50, 50)), nz=40, nzop=0),
]
assert len(INST) == 24 and len({x["name"] for x in INST}) == 24


def compact(x):
    out = bytearray()
    for o in x["ops"]:
        out += bytes(o["r"]) + bytes(o["l"]) + bytes((o["ol"], o["crs"], o["fine"], o["det"], o["kvs"] | o["rs"] << 3 | o["mode"] << 6, o["rd"]))
    out += bytes(x["peg"][0]) + bytes(x["peg"][1])
    out += bytes((x["alg"], x["fb"], x["sync"], x["trn"], x["nz"], x["nzop"]))
    assert len(out) == ISZ and max(out) <= 127
    return bytes(out)


def table():
    return b"".join(compact(x) for x in INST)


def colours():
    return bytes(c for x in INST for c in FAM[x["fam"]])


def inst_full(i):
    """The 216 parameters of instrument i (the ARM's c_fminst, byte for byte)."""
    c = compact(INST[i])
    out = bytearray(F.PLEN)
    for k in range(8):
        s, b = c[OPB_C * k:OPB_C * k + OPB_C], F.OPB * k
        out[b + F.O_R:b + F.O_R + 8] = s[0:8]
        out[b + F.O_OL], out[b + F.O_CRS], out[b + F.O_FINE], out[b + F.O_DET] = s[8], s[9], s[10], s[11]
        out[b + F.O_KVS], out[b + F.O_RS], out[b + F.O_MODE] = s[12] & 7, s[12] >> 3 & 7, s[12] >> 6
        out[b + F.O_RD], out[b + F.O_BP] = s[13], 39
    g = 8 * OPB_C
    out[F.PEG:F.PEG + 8] = c[g:g + 8]
    G = F.GLB
    out[G + F.G_ALG], out[G + F.G_FB], out[G + F.G_SYNC], out[G + F.G_TRN], out[G + F.G_NZ], out[G + F.G_NZOP] = c[g + 8:g + 14]
    return bytes(out)


# ---- (use_v2) the second page and longer releases (SC53, the user, 2026-11-07: «Pon algunos parches demo del FM más largos, como strings y winds,
#      también algún piano»; chosen: «Segunda página con Octave», «Cuerdas, Vientos, Pianos, Alargar los actuales»)
V2 = False
FAM2 = {"wind": (0x4D, 0x4E)}                         # teal (not animated)
LONGER = {"E.Piano": 48, "Bright EP": 48, "Clav": 70, "Organ": 62, "Vibes": 32, "Brass": 42, "Flute": 40, "Strings": 30, "Warm Pad": 26,
          "Choir": 28, "Glass Pad": 28, "Harp": 34, "Nylon": 42, "Tubular Bell": 24, "Sync Lead": 55, "FM Bass": 60, "Synth Bass": 60}   # R4 of every operator

CAR, MOD = None, None


def _wind_peg(scoop):                                 # a short scoop up into the note
    return ((99 - scoop, 70, 99, 99), (50 - scoop // 10, 50, 50, 50))


INST2 = [
    # ---- pianos (orange)
    inst("Grand Piano", "keys", dx(5), FB_DX7[3], [
        op((97, 32, 22, 45), (99, 82, 0, 0), 99, 1, kvs=3, rs=3),
        op((99, 48, 30, 48), (99, 62, 0, 0), 74, 1, kvs=7, rs=3, rd=30),
        op((97, 30, 20, 45), (99, 85, 0, 0), 92, 1, det=9, kvs=3, rs=3),
        op((99, 60, 35, 48), (99, 40, 0, 0), 62, 3, kvs=7, rs=3, rd=35),
        op((97, 34, 24, 45), (99, 80, 0, 0), 78, 2, det=5, kvs=3, rs=3),
        op((99, 55, 35, 48), (99, 45, 0, 0), 60, 1, kvs=6, rs=3, rd=30)]),
    inst("Mellow Piano", "keys", dx(5), FB_DX7[1], [
        op((96, 30, 20, 44), (99, 85, 0, 0), 99, 1, kvs=3, rs=3),
        op((99, 45, 28, 46), (99, 55, 0, 0), 60, 1, kvs=6, rs=3, rd=30),
        op((96, 30, 20, 44), (99, 85, 0, 0), 90, 1, det=9, kvs=3, rs=3),
        op((99, 50, 30, 46), (99, 45, 0, 0), 52, 2, kvs=6, rs=3, rd=30),
        op((96, 32, 22, 44), (99, 80, 0, 0), 70, 2, det=6, kvs=3, rs=3),
        op((99, 55, 30, 46), (99, 40, 0, 0), 45, 1, kvs=6, rs=3)]),
    inst("Honky-Tonk", "keys", dx(5), FB_DX7[3], [
        op((97, 34, 24, 46), (99, 80, 0, 0), 99, 1, det=3, kvs=3, rs=3),
        op((99, 50, 30, 48), (99, 60, 0, 0), 74, 1, kvs=7, rs=3, rd=30),
        op((97, 34, 24, 46), (99, 80, 0, 0), 97, 1, det=12, kvs=3, rs=3),
        op((99, 50, 30, 48), (99, 60, 0, 0), 72, 1, kvs=7, rs=3, rd=30),
        op((97, 36, 26, 46), (99, 75, 0, 0), 75, 2, det=7, kvs=3, rs=3),
        op((99, 60, 35, 48), (99, 40, 0, 0), 62, 3, kvs=6, rs=3)]),
    inst("Tine Piano", "keys", dx(5), FB_DX7[6], [
        op((96, 22, 18, 40), (99, 78, 0, 0), 99, 1, kvs=2, rs=3),
        op((95, 50, 35, 50), (99, 72, 0, 0), 58, 14, kvs=7, rs=3, rd=30),
        op((95, 18, 16, 40), (99, 95, 0, 0), 99, 1, kvs=2, rs=3),
        op((95, 28, 20, 42), (99, 92, 0, 0), 84, 1, kvs=6, rs=3, rd=25),
        op((95, 18, 16, 40), (99, 95, 0, 0), 97, 1, det=10, kvs=2, rs=3),
        op((95, 28, 20, 42), (99, 92, 0, 0), 76, 1, det=4, kvs=6, rs=3, rd=25)]),
    inst("Toy Piano", "keys", dx(5), 0, [
        op((99, 45, 30, 48), (99, 50, 0, 0), 99, 1, kvs=3, rs=3),
        op((99, 55, 40, 50), (99, 30, 0, 0), 70, 7, kvs=5, rs=3),
        op((99, 40, 28, 48), (99, 55, 0, 0), 86, 2, det=9, kvs=3, rs=3),
        op((99, 60, 40, 50), (99, 25, 0, 0), 60, 9, fine=50, kvs=5, rs=3)]),
    # ---- strings (green)
    inst("Slow Strings", "pad", dx(2), FB_DX7[6], [
        op((32, 28, 24, 28), (99, 96, 93, 0), 99, 1, det=6, kvs=1, rs=1),
        op((38, 30, 25, 28), (99, 90, 88, 0), 76, 1, kvs=3, rs=1),
        op((32, 28, 24, 28), (99, 96, 93, 0), 97, 1, det=9, kvs=1, rs=1),
        op((36, 30, 25, 28), (99, 90, 88, 0), 62, 1, kvs=3, rs=1),
        op((36, 30, 25, 28), (99, 88, 85, 0), 58, 3, kvs=3, rs=1),
        op((36, 30, 25, 28), (99, 85, 82, 0), 50, 1, det=10, kvs=3, rs=1)]),
    inst("Ensemble", "pad", dx(5), FB_DX7[5], [
        op((42, 30, 25, 32), (99, 95, 92, 0), 95, 1, det=4, kvs=1, rs=1),
        op((45, 30, 25, 32), (99, 90, 88, 0), 74, 1, kvs=3, rs=1),
        op((42, 30, 25, 32), (99, 95, 92, 0), 95, 1, det=10, kvs=1, rs=1),
        op((45, 30, 25, 32), (99, 90, 88, 0), 72, 1, kvs=3, rs=1),
        op((42, 30, 25, 32), (99, 95, 92, 0), 90, 2, det=7, kvs=1, rs=1),
        op((45, 30, 25, 32), (99, 88, 85, 0), 66, 1, kvs=3, rs=1)]),
    inst("Cello", "pad", dx(2), FB_DX7[6], [
        op((55, 35, 28, 38), (99, 94, 90, 0), 99, 1, kvs=2, rs=1),
        op((52, 35, 28, 38), (99, 90, 86, 0), 82, 1, kvs=4, rs=1),
        op((55, 35, 28, 38), (99, 94, 90, 0), 90, 1, det=9, kvs=2, rs=1),
        op((52, 35, 28, 38), (99, 85, 80, 0), 66, 2, kvs=4, rs=1),
        op((52, 35, 28, 38), (99, 85, 80, 0), 58, 1, kvs=4, rs=1),
        op((52, 35, 28, 38), (99, 80, 75, 0), 52, 3, kvs=4, rs=1)], trn=12),
    inst("Violin", "pad", dx(2), FB_DX7[7], [
        op((58, 35, 28, 40), (99, 94, 92, 0), 99, 1, kvs=2, rs=1),
        op((55, 35, 28, 40), (99, 92, 88, 0), 86, 1, kvs=4, rs=1),
        op((58, 35, 28, 40), (99, 94, 92, 0), 82, 1, det=8, kvs=2, rs=1),
        op((55, 35, 28, 40), (99, 85, 82, 0), 70, 3, kvs=4, rs=1),
        op((55, 35, 28, 40), (99, 85, 82, 0), 60, 2, kvs=4, rs=1),
        op((55, 35, 28, 40), (99, 80, 75, 0), 55, 4, kvs=4, rs=1)], peg=_wind_peg(15)),
    inst("Pizzicato", "pluck", dx(5), FB_DX7[2], [
        op((99, 45, 32, 45), (99, 0, 0, 0), 99, 1, kvs=3, rs=3),
        op((99, 60, 40, 48), (99, 0, 0, 0), 72, 1, kvs=5, rs=3),
        op((99, 45, 32, 45), (99, 0, 0, 0), 90, 1, det=9, kvs=3, rs=3),
        op((99, 65, 45, 48), (99, 0, 0, 0), 58, 3, kvs=5, rs=3)]),
    inst("String Swell", "pad", dx(5), FB_DX7[4], [
        op((24, 26, 22, 26), (99, 96, 94, 0), 95, 1, det=5, kvs=1),
        op((22, 26, 22, 26), (99, 92, 90, 0), 74, 1, kvs=2),
        op((24, 26, 22, 26), (99, 96, 94, 0), 95, 1, det=9, kvs=1),
        op((22, 26, 22, 26), (99, 92, 90, 0), 70, 1, kvs=2),
        op((24, 26, 22, 26), (99, 96, 94, 0), 88, 2, det=7, kvs=1),
        op((22, 26, 22, 26), (99, 90, 88, 0), 62, 1, kvs=2)]),
    # ---- winds (teal)
    inst("Clarinet", "wind", dx(5), FB_DX7[2], [
        op((62, 40, 30, 42), (99, 95, 93, 0), 99, 1, kvs=2, rs=1),
        op((60, 40, 30, 42), (99, 90, 88, 0), 78, 2, kvs=4, rs=1),
        op((62, 40, 30, 42), (99, 92, 90, 0), 60, 3, kvs=2, rs=1),
        op((60, 40, 30, 42), (99, 85, 82, 0), 50, 2, kvs=4, rs=1)], nz=8, nzop=0, peg=_wind_peg(8)),
    inst("Oboe", "wind", dx(5), FB_DX7[3], [
        op((64, 42, 30, 42), (99, 95, 92, 0), 99, 1, kvs=2, rs=1),
        op((62, 42, 30, 42), (99, 92, 90, 0), 86, 1, kvs=4, rs=1),
        op((64, 42, 30, 42), (99, 92, 90, 0), 74, 3, kvs=2, rs=1),
        op((62, 42, 30, 42), (99, 88, 85, 0), 62, 1, kvs=4, rs=1),
        op((64, 42, 30, 42), (99, 88, 85, 0), 55, 5, kvs=2, rs=1),
        op((62, 42, 30, 42), (99, 82, 80, 0), 48, 1, kvs=4, rs=1)], nz=6, nzop=0, peg=_wind_peg(8)),
    inst("Bassoon", "wind", dx(5), FB_DX7[3], [
        op((60, 40, 30, 42), (99, 94, 92, 0), 99, 1, kvs=2, rs=1),
        op((58, 40, 30, 42), (99, 90, 86, 0), 80, 2, kvs=4, rs=1),
        op((60, 40, 30, 42), (99, 92, 90, 0), 74, 1, det=8, kvs=2, rs=1),
        op((58, 40, 30, 42), (99, 86, 82, 0), 70, 1, kvs=4, rs=1)], trn=12, nz=6, nzop=0),
    inst("Alto Sax", "wind", dx(2), FB_DX7[5], [
        op((70, 45, 32, 45), (99, 94, 90, 0), 99, 1, kvs=2, rs=1),
        op((66, 45, 32, 45), (99, 92, 88, 0), 84, 1, kvs=5, rs=1),
        op((70, 45, 32, 45), (99, 92, 90, 0), 88, 1, det=8, kvs=2, rs=1),
        op((66, 45, 32, 45), (99, 85, 80, 0), 72, 1, kvs=5, rs=1),
        op((66, 45, 32, 45), (99, 82, 78, 0), 62, 2, kvs=4, rs=1),
        op((66, 45, 32, 45), (99, 78, 72, 0), 55, 3, kvs=4, rs=1)], nz=10, nzop=0, peg=_wind_peg(20)),
    inst("French Horn", "wind", dx(22), FB_DX7[3], [
        op((50, 38, 30, 40), (99, 94, 90, 0), 99, 1, kvs=2, rs=1),
        op((48, 38, 30, 40), (99, 80, 75, 0), 70, 1, kvs=4, rs=1),
        op((50, 38, 30, 40), (99, 94, 90, 0), 90, 1, det=8, kvs=2, rs=1),
        op((50, 38, 30, 40), (99, 94, 90, 0), 88, 1, det=6, kvs=2, rs=1),
        op((50, 38, 30, 40), (99, 92, 88, 0), 80, 2, kvs=2, rs=1),
        op((48, 40, 30, 40), (99, 75, 70, 0), 66, 1, kvs=4, rs=1)], peg=_wind_peg(10)),
    inst("Trumpet", "wind", dx(22), FB_DX7[6], [
        op((70, 42, 30, 48), (99, 94, 90, 0), 99, 1, kvs=2, rs=2),
        op((66, 42, 30, 48), (99, 86, 82, 0), 84, 1, kvs=5, rs=2),
        op((70, 42, 30, 48), (99, 94, 90, 0), 95, 1, det=8, kvs=2, rs=2),
        op((70, 42, 30, 48), (99, 94, 90, 0), 92, 1, det=6, kvs=2, rs=2),
        op((70, 42, 30, 48), (99, 92, 88, 0), 86, 2, kvs=2, rs=2),
        op((66, 45, 30, 48), (99, 82, 78, 0), 80, 1, kvs=5, rs=2)], peg=_wind_peg(25)),
    inst("Pan Flute", "wind", dx(5), FB_DX7[1], [
        op((58, 40, 30, 40), (99, 95, 92, 0), 99, 1, kvs=2, rs=1),
        op((55, 40, 30, 40), (99, 85, 80, 0), 42, 1, kvs=4, rs=1),
        op((58, 40, 30, 40), (99, 90, 88, 0), 55, 2, det=8, kvs=2, rs=1),
        op((55, 40, 30, 40), (99, 80, 75, 0), 30, 1, kvs=3, rs=1)], nz=30, nzop=0, peg=_wind_peg(10)),
    inst("Recorder", "wind", dx(5), 0, [
        op((66, 42, 30, 44), (99, 95, 93, 0), 99, 1, kvs=2, rs=1),
        op((64, 42, 30, 44), (99, 88, 85, 0), 50, 2, kvs=4, rs=1),
        op((66, 42, 30, 44), (99, 90, 88, 0), 40, 2, kvs=2, rs=1)], nz=12, nzop=0),
    inst("Harmonica", "wind", dx(5), FB_DX7[4], [
        op((72, 45, 32, 46), (99, 94, 90, 0), 99, 1, kvs=2, rs=1),
        op((70, 45, 32, 46), (99, 90, 86, 0), 80, 1, kvs=5, rs=1),
        op((72, 45, 32, 46), (99, 92, 90, 0), 80, 2, det=9, kvs=2, rs=1),
        op((70, 45, 32, 46), (99, 85, 80, 0), 70, 1, kvs=5, rs=1)], nz=8, nzop=0, peg=_wind_peg(12)),
    # ---- long ones
    inst("Cathedral", "keys", dx(32), FB_DX7[2], [
        op((80, 99, 99, 30), K, 99, 1, rs=1),
        op((80, 99, 99, 30), K, 90, 0, rs=1),
        op((80, 99, 99, 30), K, 88, 2, rs=1),
        op((80, 99, 99, 30), K, 82, 3, det=8, rs=1),
        op((80, 99, 99, 30), K, 78, 4, rs=1),
        op((80, 99, 99, 30), K, 74, 8, det=6, rs=1)]),
    inst("Bowed Glass", "pad", dx(5), FB_DX7[2], [
        op((30, 26, 22, 26), (99, 94, 90, 0), 99, 1, kvs=1),
        op((26, 24, 20, 26), (99, 88, 84, 0), 52, 3, fine=50, kvs=3),
        op((30, 26, 22, 26), (99, 94, 90, 0), 88, 2, det=9, kvs=1),
        op((26, 24, 20, 26), (99, 85, 80, 0), 46, 5, kvs=3),
        op((30, 26, 22, 26), (99, 92, 88, 0), 82, 1, det=5, kvs=1),
        op((26, 24, 20, 26), (99, 82, 78, 0), 40, 7, kvs=2)]),
    inst("Evolving Pad", "pad", dx(5), FB_DX7[4], [
        op((32, 24, 20, 24), (99, 94, 92, 0), 95, 1, det=5, kvs=1),
        op((18, 20, 18, 24), (99, 95, 90, 0), 78, 1, kvs=2),
        op((32, 24, 20, 24), (99, 94, 92, 0), 95, 1, det=9, kvs=1),
        op((16, 20, 18, 24), (99, 92, 88, 0), 70, 2, kvs=2),
        op((32, 24, 20, 24), (99, 92, 90, 0), 88, 2, det=7, kvs=1),
        op((14, 20, 18, 24), (99, 90, 85, 0), 62, 3, kvs=2)]),
    inst("Long Bell", "bell", dx(5), 0, [
        op((99, 24, 18, 22), (99, 0, 0, 0), 99, 1, kvs=2, rs=2),
        op((99, 28, 20, 22), (99, 0, 0, 0), 75, 3, fine=50, kvs=4, rs=2),
        op((99, 24, 18, 22), (99, 0, 0, 0), 85, 1, det=10, kvs=2, rs=2),
        op((99, 28, 20, 22), (99, 0, 0, 0), 70, 1, fine=41, kvs=4, rs=2),
        op((99, 22, 16, 22), (99, 0, 0, 0), 70, 2, det=5, kvs=2, rs=2),
        op((99, 26, 20, 22), (99, 0, 0, 0), 55, 5, fine=20, kvs=4, rs=2)]),
]
assert len(INST2) == 24 and len({x["name"] for x in INST + INST2}) == 48


def use_v2():
    """The 48 instruments: the 24 with longer releases (LONGER: R4 of every operator that sounds) and the second page (INST2)."""
    global V2, INST
    if V2: return
    V2 = True
    FAM.update(FAM2)
    for x in INST:
        r4 = LONGER.get(x["name"])
        if r4 is None: continue
        for o in x["ops"]:
            if o["ol"] > 0 and o is not OFF: o["r"] = o["r"][:3] + (min(o["r"][3], r4),)
    INST = INST + INST2


def lz(data, W=4095, MAXL=18):
    """The instruments' table packed for c_fiun: a flag byte (bit k = item k a match), a literal = 1 byte, a match = offset low, offset high << 4 | (length - 3)
    (offset 1..4095 back in the output, length 3..18)."""
    heads = {}
    out = bytearray(); i = 0; n = len(data)
    while i < n:
        fpos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= n: break
            best = (0, 0)
            for j in reversed(heads.get(data[i:i + 3], [])):
                if i - j > W: break
                l = 0
                while l < MAXL and i + l < n and data[j + l] == data[i + l]: l += 1
                if l > best[1]: best = (i - j, l)
                if l == MAXL: break
            step = best[1] if best[1] >= 3 else 1
            if best[1] >= 3:
                flags |= 1 << bit; o, l = best; out += bytes((o & 0xFF, (o >> 8) << 4 | (l - 3)))
            else:
                out.append(data[i])
            for k in range(i, i + step):
                heads.setdefault(data[k:k + 3], []).append(k)
            i += step
        out[fpos] = flags
    return bytes(out)


def unlz(p, n):
    out = bytearray(); i = 0
    while len(out) < n:
        f = p[i]; i += 1
        for bit in range(8):
            if len(out) >= n: break
            if f >> bit & 1:
                o = p[i] | (p[i + 1] >> 4) << 8; l = (p[i + 1] & 15) + 3; i += 2
                for _ in range(l): out.append(out[-o])
            else:
                out.append(p[i]); i += 1
    return bytes(out)


if __name__ == "__main__":
    print(len(table()), "B")
    for i, x in enumerate(INST):
        print(i + 9, x["name"], x["fam"], x["alg"], F.alg_of(F.algs(), x["alg"]) if x["alg"] < 48 else "")
