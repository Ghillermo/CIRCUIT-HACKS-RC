"""Alpha 7.14 / RC4.20 / RC4.20S (a fix; the user, 2026-11-20: a black box record from A7PROT «while receiving midi from a Circuit Rhythm, no
operation on the Tracks», «on Rhythm sample record view and just toggled -12dB trim»; reproduced on the device: one CC 27 on channel 16 from the
PC crashed it): **a stock firmware crash.**  The master group (type 0x21) has a 13th parameter (descriptor 0x080598E8: id 0x14, 0 / 1, CC 27 on
the project channel; on the Circuit Rhythm, which shares the table, the sample record's -12 dB trim: it sends NRPN 1:27 = 1 / 0 on channel 16, seen on its USB port); setting it marks it pending with
0x08022094 (index 12 -> bit 3 of [0x20006A0C + 1]), and the main loop's sender 0x08021578 calls table[3] at 0x080215B8 + 12, which is not an
address but the code after the table (0xD0002800): an instruction access fault (PC 0xD0002800, LR 0x08021595), as the record shows.  The Rhythm's
own firmware maps that index to a real handler (indices 12-16); the Tracks has none.

The fix: the sender's last `bmi #0x0802158A` (bit 3 set: call table[3]) at 0x080215B2 -> `bmi #0x08021594`: the bit is cleared (r5 = 0xF7) and
nothing called.  Two bytes of stock code, no flash.  The parameter itself still goes into the store (it does nothing on the Tracks)."""
SITE, OLD, NEW = 0x080215B2, bytes.fromhex("ead4"), bytes.fromhex("efd4")      # bmi #0x0802158A -> bmi #0x08021594


def patch(img, report):
    import ct_fw
    o = SITE - ct_fw.APP_BASE
    assert bytes(img[o:o + 2]) == OLD, f"cc27fix: {bytes(img[o:o + 2]).hex()} at {SITE:#x}"
    img[o:o + 2] = NEW
    report["cc27fix"] = dict(site=hex(SITE), old=OLD.hex(), new=NEW.hex())
