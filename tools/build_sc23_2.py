"""Circuit Tracks 4486 — SC23.2 = SC23.1 + the toggles of the MIDI Preset view as asked: pad 27 only switches the start of the VCA / VCF chain (line in <-> oscillator, lit = oscillator);
pad 28 opens the oscillator parameters and pad 29 the VCA / VCF parameters (each lit while selected); the mode is on while one of them is selected and goes off when the lit one is pressed again.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import build_sc23_1 as b231  # noqa: E402
import linein3  # noqa: E402
vcf21.use_pads2()
b23 = b231.b23
b223 = b231.b223

NAME = "SC23.2"

if __name__ == "__main__":
    linein3.main(NAME, b223.b22.b182.b18.b6.b5.build, b223.b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=b223.b22.b214.b213.extra)
