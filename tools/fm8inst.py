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


if __name__ == "__main__":
    print(len(table()), "B")
    for i, x in enumerate(INST):
        print(i + 9, x["name"], x["fam"], x["alg"], F.alg_of(F.algs(), x["alg"]) if x["alg"] < 48 else "")
