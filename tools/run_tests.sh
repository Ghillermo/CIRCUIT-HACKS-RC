#!/usr/bin/env bash
# Pruebas de la cadena actual (SC20, con SC19.9 / SC19.8 / SC19.7 / SC19.6 / SC19.4 / SC19.5 / SC19.3 y SC20D.1; SC19, SC19.1, SC19.2 y SC20D se cuelgan al encender y solo se comprueban en verify_builds).  bash tools/run_tests.sh [quick|full]
#   quick (por defecto): builds idénticos + pruebas ARM de SC17.x sobre SC19, las de SC18.x sobre SC18.3 y las de SC19 (~60 min)
#   full: además DSP exacto de Master FX, núcleo DSP completo, entrada de línea, drums de SC18 / SC18.1 y mensajes absolutos de SC19 y fuzz de botones / pads / knobs de SC19.1 (~30 min más)
set -uo pipefail
cd "$(dirname "$0")/.."
ST=stock/circuittracks-firmware-4486-STOCK.bin
F=firmware/sc20.1; IMG=$F/circuittracks-4486-SC20.1.bin; MAN=$F/manifest.json
F20P=firmware/sc20; IMG20P=$F20P/circuittracks-4486-SC20.bin; MAN20P=$F20P/manifest.json
F21D=firmware/sc21d
F211=firmware/sc21.1
F212=firmware/sc21.2
F213=firmware/sc21.3
F214=firmware/sc21.4
F22=firmware/sc22
F221=firmware/sc22.1
F222=firmware/sc22.2
F223=firmware/sc22.3
F224=firmware/sc22.4
F23=firmware/sc23
F231=firmware/sc23.1
F232=firmware/sc23.2
F233=firmware/sc23.3
F234=firmware/sc23.4
F235=firmware/sc23.5
F236=firmware/sc23.6
F24=firmware/sc24
F25=firmware/sc25
F26=firmware/sc26
F27=firmware/sc27
F28=firmware/sc28
F29=firmware/sc29
F30=firmware/sc30
F31=firmware/sc31
F32=firmware/sc32
F33=firmware/sc33
F34=firmware/sc34
F34D=firmware/sc34d
F35D=firmware/sc35d
F341=firmware/sc34.1
F342=firmware/sc34.2
F35D1=firmware/sc35d.1
F35D2=firmware/sc35d2
F35D3=firmware/sc35d3
F35D4=firmware/sc35d4
F35D5=firmware/sc35d5
F35D6=firmware/sc35d6
F35D7=firmware/sc35d7
F35D8=firmware/sc35d8
F35D9=firmware/sc35d9
F342D=firmware/sc342d
F35DA=firmware/sc35da
F35=firmware/sc35
F35DB=firmware/sc35db
F36=firmware/sc36
F361=firmware/sc36.1
F361S=firmware/sc361s
F362=firmware/sc36.2
F362S=firmware/sc362s
FRC0=firmware/rc0
FRC0S=firmware/rc0s
F37=firmware/sc37
F371=firmware/sc37.1
F372=firmware/sc37.2
F373=firmware/sc37.3
F374=firmware/sc37.4
FRC01=firmware/rc0.1
FRC01S=firmware/rc0.1s
F375=firmware/sc37.5
FRC02=firmware/rc0.2
FRC02S=firmware/rc0.2s
F376=firmware/sc37.6
F377=firmware/sc37.7
F378=firmware/sc37.8
F379=firmware/sc37.9
F38=firmware/sc38
FRC03=firmware/rc0.3
FRC03S=firmware/rc0.3s
F381=firmware/sc38.1
F382=firmware/sc38.2
F383=firmware/sc38.3
F384=firmware/sc38.4
F385=firmware/sc38.5
F386=firmware/sc38.6
F387=firmware/sc38.7
F388=firmware/sc38.8
F389=firmware/sc38.9
F39=firmware/sc39
F391=firmware/sc39.1
FB2=firmware/beta2
F392=firmware/sc39.2
F393=firmware/sc39.3
F394=firmware/sc39.4
F395=firmware/sc39.5
F396=firmware/sc39.6
F397=firmware/sc39.7
F398=firmware/sc39.8
F399=firmware/sc39.9
F40=firmware/sc40
FB3=firmware/beta3
FB4=firmware/beta4
FB5=firmware/beta5
FRC05=firmware/rc0.5
FRC05S=firmware/rc0.5s
FB1=firmware/beta1
FSEQW=firmware/seqwatch
FRC04=firmware/rc0.4
FRC04S=firmware/rc0.4s
FB0=firmware/beta0
F32D=firmware/sc32d
F32D1=firmware/sc32d.1
F32D2=firmware/sc32d2
F21=firmware/sc21; IMG21=$F21/circuittracks-4486-SC21.bin; MAN21=$F21/manifest.json
F9=firmware/sc19.9; IMG9=$F9/circuittracks-4486-SC19.9.bin; MAN9=$F9/manifest.json
F8=firmware/sc19.8; IMG8=$F8/circuittracks-4486-SC19.8.bin; MAN8=$F8/manifest.json
F7=firmware/sc19.7; IMG7=$F7/circuittracks-4486-SC19.7.bin; MAN7=$F7/manifest.json
F6=firmware/sc19.6; IMG6=$F6/circuittracks-4486-SC19.6.bin; MAN6=$F6/manifest.json
F5=firmware/sc19.5; IMG5=$F5/circuittracks-4486-SC19.5.bin; MAN5=$F5/manifest.json
F4=firmware/sc19.4; IMG4=$F4/circuittracks-4486-SC19.4.bin; MAN4=$F4/manifest.json
F3=firmware/sc19.3; IMG3=$F3/circuittracks-4486-SC19.3.bin; MAN3=$F3/manifest.json
F19=firmware/sc19; IMG19=$F19/circuittracks-4486-SC19.bin
F20=firmware/sc20d.1; IMG20=$F20/circuittracks-4486-SC20D.1.bin; MAN20=$F20/manifest.json
F191=firmware/sc19.1; MAN191=$F191/manifest.json
F183=firmware/sc18.3; IMG183=$F183/circuittracks-4486-SC18.3.bin; MAN183=$F183/manifest.json
REF18=firmware/sc18/circuittracks-4486-SC18.bin
REF181=firmware/sc18.1/circuittracks-4486-SC18.1.bin
REF182=firmware/sc18.2/circuittracks-4486-SC18.2.bin
REF8=firmware/sc17.8/circuittracks-4486-SC17.8.bin
REF=firmware/sc17.4/circuittracks-4486-SC17.4.bin; REF5=firmware/sc17.5/circuittracks-4486-SC17.5.bin; REF6=firmware/sc17.6/circuittracks-4486-SC17.6.bin; REF7=firmware/sc17.7/circuittracks-4486-SC17.7.bin
fails=0
run() { echo; echo "### $*"; "$@" || fails=$((fails+1)); }
run python3 tools/verify_builds.py
run python3 tools/emu_sc17.py "$ST" "$IMG" "$MAN"
run python3 tools/emu_sc17_5.py "$ST" "$REF" "$IMG" "$MAN"
run python3 tools/emu_sc17_6.py "$ST" "$REF5" "$IMG" "$MAN"
run python3 tools/emu_sc17_7.py "$ST" "$REF6" "$IMG" "$MAN"
run python3 tools/emu_sc17_8.py "$ST" "$REF7" "$IMG" "$MAN"
run python3 tools/emu_sc18.py "$REF8" "$IMG183" "$MAN183"
run python3 tools/emu_sc18_1.py "$REF8" "$IMG183" "$MAN183"
run python3 tools/emu_sc18_2.py "$REF181" "$IMG183" "$MAN183"
run python3 tools/emu_sc19.py "$ST" "$IMG183" "$IMG" "$MAN" "$REF8"
run python3 tools/emu_sc19_1.py "$ST" "$IMG19" "$IMG" "$MAN"
run python3 tools/emu_sc19_3.py "$F191/circuittracks-4486-SC19.1.bin" "$IMG3" "$MAN3" "$MAN191"
run python3 tools/emu_sc19_4.py "$IMG3" "$IMG" "$MAN" "$MAN3"
run python3 tools/emu_sc19_6.py "$ST" "$IMG5" "$IMG6" "$MAN5" "$MAN6"
run python3 tools/emu_sc19_7.py "$IMG6" "$IMG7" "$MAN6" "$MAN7"
run python3 tools/emu_sc19_8.py "$IMG7" "$IMG8" "$MAN7" "$MAN8"
run python3 tools/emu_sc19_9.py "$IMG8" "$IMG" "$MAN8" "$MAN"
run python3 tools/emu_sc20.py "$IMG9" "$IMG" "$MAN9" "$MAN"
run python3 tools/emu_sc20_1.py "$IMG20P" "$IMG" "$MAN20P" "$MAN"
run python3 tools/emu_sc21.py "$IMG9" "$IMG21" "$MAN9" "$MAN21"
run python3 tools/emu_sc21_1.py "$IMG9" "$F211/circuittracks-4486-SC21.1.bin" "$MAN9" "$F211/manifest.json"
run python3 tools/emu_sc21_2.py "$F211/circuittracks-4486-SC21.1.bin" "$F212/circuittracks-4486-SC21.2.bin" "$F211/manifest.json" "$F212/manifest.json"
run python3 tools/emu_sc21_3.py "$F212/circuittracks-4486-SC21.2.bin" "$F213/circuittracks-4486-SC21.3.bin" "$F212/manifest.json" "$F213/manifest.json"
run python3 tools/emu_sc21_4.py "$IMG9" "$F214/circuittracks-4486-SC21.4.bin" "$MAN9" "$F214/manifest.json"
run python3 tools/emu_sc22.py "$IMG9" "$F22/circuittracks-4486-SC22.bin" "$MAN9" "$F22/manifest.json"
run python3 tools/emu_sc22_1.py "$IMG9" "$F221/circuittracks-4486-SC22.1.bin" "$MAN9" "$F221/manifest.json"
run python3 tools/emu_sc22_2.py "$IMG9" "$F222/circuittracks-4486-SC22.2.bin" "$MAN9" "$F222/manifest.json"
run python3 tools/emu_sc22_3.py "$IMG9" "$F223/circuittracks-4486-SC22.3.bin" "$MAN9" "$F223/manifest.json"
run python3 tools/emu_sc22_4.py "$IMG9" "$F224/circuittracks-4486-SC22.4.bin" "$MAN9" "$F224/manifest.json"
run python3 tools/emu_sc23.py "$IMG9" "$F23/circuittracks-4486-SC23.bin" "$MAN9" "$F23/manifest.json"
run python3 tools/emu_sc23_ed.py "$IMG9" "$F23/circuittracks-4486-SC23.bin" "$MAN9" "$F23/manifest.json"
run python3 tools/emu_sc23.py "$IMG9" "$F231/circuittracks-4486-SC23.1.bin" "$MAN9" "$F231/manifest.json"
run python3 tools/emu_sc23_1_ed.py "$IMG9" "$F231/circuittracks-4486-SC23.1.bin" "$MAN9" "$F231/manifest.json"
run python3 tools/emu_sc23_2.py "$IMG9" "$F232/circuittracks-4486-SC23.2.bin" "$MAN9" "$F232/manifest.json"
run python3 tools/emu_sc23_1_ed.py "$IMG9" "$F232/circuittracks-4486-SC23.2.bin" "$MAN9" "$F232/manifest.json"
run python3 tools/emu_sc23_3.py "$IMG9" "$F233/circuittracks-4486-SC23.3.bin" "$MAN9" "$F233/manifest.json"
run python3 tools/emu_sc23_1_ed.py "$IMG9" "$F233/circuittracks-4486-SC23.3.bin" "$MAN9" "$F233/manifest.json"
run python3 tools/emu_sc23_3_ed.py "$IMG9" "$F233/circuittracks-4486-SC23.3.bin" "$MAN9" "$F233/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F233/circuittracks-4486-SC23.3.bin" "$F233/manifest.json"
run python3 tools/emu_sc23_3_dsp.py "$F233/circuittracks-4486-SC23.3.bin" "$F233/manifest.json"
run python3 tools/emu_sc23_3.py "$IMG9" "$F234/circuittracks-4486-SC23.4.bin" "$MAN9" "$F234/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F234/circuittracks-4486-SC23.4.bin" "$F234/manifest.json"
run python3 tools/emu_sc23_3_dsp.py "$F234/circuittracks-4486-SC23.4.bin" "$F234/manifest.json"
run python3 tools/emu_sc23_4_ed.py "$IMG9" "$F234/circuittracks-4486-SC23.4.bin" "$MAN9" "$F234/manifest.json"
run python3 tools/emu_sc23_4_gfx.py "$F234/circuittracks-4486-SC23.4.bin" "$F234/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F234/circuittracks-4486-SC23.4.bin" "$F234/manifest.json"
run python3 tools/emu_sc23_3.py "$IMG9" "$F235/circuittracks-4486-SC23.5.bin" "$MAN9" "$F235/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"
run python3 tools/emu_sc23_5.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F235/circuittracks-4486-SC23.5.bin" "$MAN9" "$F235/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"
run python3 tools/emu_sc23_3.py "$IMG9" "$F236/circuittracks-4486-SC23.6.bin" "$MAN9" "$F236/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc23_5.py "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F236/circuittracks-4486-SC23.6.bin" "$MAN9" "$F236/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc23_6.py "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json" "$F235/circuittracks-4486-SC23.5.bin"
run python3 tools/emu_sc23_3_fx.py "$F24/circuittracks-4486-SC24.bin" "$F24/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F24/circuittracks-4486-SC24.bin" "$F24/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F24/circuittracks-4486-SC24.bin" "$F24/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F24/circuittracks-4486-SC24.bin" "$F24/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F24/circuittracks-4486-SC24.bin" "$MAN9" "$F24/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F24/circuittracks-4486-SC24.bin" "$F24/manifest.json"
run python3 tools/emu_sc23_6.py "$F24/circuittracks-4486-SC24.bin" "$F24/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F24/circuittracks-4486-SC24.bin" "$F24/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F24/circuittracks-4486-SC24.bin" "$F24/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F24/circuittracks-4486-SC24.bin" "$F24/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F25/circuittracks-4486-SC25.bin" "$F25/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F25/circuittracks-4486-SC25.bin" "$F25/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F25/circuittracks-4486-SC25.bin" "$F25/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F25/circuittracks-4486-SC25.bin" "$F25/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F25/circuittracks-4486-SC25.bin" "$MAN9" "$F25/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F25/circuittracks-4486-SC25.bin" "$F25/manifest.json"
run python3 tools/emu_sc23_6.py "$F25/circuittracks-4486-SC25.bin" "$F25/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F25/circuittracks-4486-SC25.bin" "$F25/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F25/circuittracks-4486-SC25.bin" "$F25/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F25/circuittracks-4486-SC25.bin" "$F25/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc25.py "$F25/circuittracks-4486-SC25.bin" "$F25/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F26/circuittracks-4486-SC26.bin" "$MAN9" "$F26/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json"
run python3 tools/emu_sc23_6.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc25.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json"
run python3 tools/emu_sc26.py "$F26/circuittracks-4486-SC26.bin" "$F26/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F27/circuittracks-4486-SC27.bin" "$MAN9" "$F27/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json"
run python3 tools/emu_sc23_6.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc25.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json"
run python3 tools/emu_sc26.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json"
run python3 tools/emu_sc27.py "$F27/circuittracks-4486-SC27.bin" "$F27/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F28/circuittracks-4486-SC28.bin" "$MAN9" "$F28/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc23_6.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc25.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc26.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc27.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc28.py "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F29/circuittracks-4486-SC29.bin" "$MAN9" "$F29/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc23_6.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc25.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc26.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc27.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc28.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc29.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json"
run python3 tools/emu_sc29_dsp.py "$F29/circuittracks-4486-SC29.bin" "$F29/manifest.json" "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F30/circuittracks-4486-SC30.bin" "$MAN9" "$F30/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc23_6.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc25.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc26.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc27.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc28.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc29.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json"
run python3 tools/emu_sc29_dsp.py "$F30/circuittracks-4486-SC30.bin" "$F30/manifest.json" "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc30.py "$F29/circuittracks-4486-SC29.bin" "$F30/circuittracks-4486-SC30.bin" "$F29/manifest.json" "$F30/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F31/circuittracks-4486-SC31.bin" "$MAN9" "$F31/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc23_6.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc25.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc28.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc29.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc29_dsp.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json" "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc30.py "$F29/circuittracks-4486-SC29.bin" "$F31/circuittracks-4486-SC31.bin" "$F29/manifest.json" "$F31/manifest.json"
run python3 tools/emu_sc31.py "$F31/circuittracks-4486-SC31.bin" "$F31/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F32/circuittracks-4486-SC32.bin" "$MAN9" "$F32/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc23_6.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc25.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc28.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc29.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc29_dsp.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json" "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc30.py "$F29/circuittracks-4486-SC29.bin" "$F32/circuittracks-4486-SC32.bin" "$F29/manifest.json" "$F32/manifest.json"
run python3 tools/emu_sc31.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc32.py "$F32/circuittracks-4486-SC32.bin" "$F32/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F33/circuittracks-4486-SC33.bin" "$MAN9" "$F33/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc23_6.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc25.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc28.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc29.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc29_dsp.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json" "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc30.py "$F29/circuittracks-4486-SC29.bin" "$F33/circuittracks-4486-SC33.bin" "$F29/manifest.json" "$F33/manifest.json"
run python3 tools/emu_sc31.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc33.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc33_sd.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc33_dsp.py "$F33/circuittracks-4486-SC33.bin" "$F33/manifest.json"
run python3 tools/emu_sc23_3_fx.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc23_4_notes.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc23_5_drums.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F34/circuittracks-4486-SC34.bin" "$MAN9" "$F34/manifest.json"
run python3 tools/emu_sc23_5_dsp.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc23_6.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc23_6_dsp.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json" "$F236/circuittracks-4486-SC23.6.bin"
run python3 tools/emu_sc24.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc24_dsp.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json" "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"
run python3 tools/emu_sc25.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc28.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc29.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc29_dsp.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json" "$F28/circuittracks-4486-SC28.bin" "$F28/manifest.json"
run python3 tools/emu_sc30.py "$F29/circuittracks-4486-SC29.bin" "$F34/circuittracks-4486-SC34.bin" "$F29/manifest.json" "$F34/manifest.json"
run python3 tools/emu_sc31.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc33_sd.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc34.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc34_dsp.py "$F34/circuittracks-4486-SC34.bin" "$F34/manifest.json"
run python3 tools/emu_sc34d.py "$F34D/circuittracks-4486-SC34D.bin" "$F34D/manifest.json"
run python3 tools/emu_sc34_1.py "$F341/circuittracks-4486-SC34.1.bin" "$F341/manifest.json"
run python3 tools/emu_sc34_2.py "$F342/circuittracks-4486-SC34.2.bin" "$F342/manifest.json"
run python3 tools/emu_sc35d.py "$F35D/circuittracks-4486-SC35D.bin" "$F35D/manifest.json"
run python3 tools/emu_sc35d_1.py "$F35D1/circuittracks-4486-SC35D.1.bin" "$F35D1/manifest.json"
run python3 tools/emu_sc35d2.py "$F35D2/circuittracks-4486-SC35D2.bin" "$F35D2/manifest.json"
run python3 tools/emu_sc35d3.py "$F35D3/circuittracks-4486-SC35D3.bin" "$F35D3/manifest.json"
run python3 tools/emu_sc35d4.py "$F35D4/circuittracks-4486-SC35D4.bin" "$F35D4/manifest.json"
run python3 tools/emu_sc35d4.py "$F35D5/circuittracks-4486-SC35D5.bin" "$F35D5/manifest.json" --kind 4
run python3 tools/emu_sc35d4.py "$F35D6/circuittracks-4486-SC35D6.bin" "$F35D6/manifest.json" --kind 4 --writeback
run python3 tools/emu_sc35d4.py "$F35D7/circuittracks-4486-SC35D7.bin" "$F35D7/manifest.json" --kind 4 --wbpads
run python3 tools/emu_sc35d8.py "$F35D8/circuittracks-4486-SC35D8.bin" "$F35D8/manifest.json"
run python3 tools/emu_sc35d8.py "$F35D9/circuittracks-4486-SC35D9.bin" "$F35D9/manifest.json" --delete
run python3 tools/emu_sc342d.py "$F342D/circuittracks-4486-SC342D.bin" "$F342D/manifest.json"
run python3 tools/emu_sc342d.py "$F35DA/circuittracks-4486-SC35DA.bin" "$F35DA/manifest.json" --delpack
run python3 tools/emu_sc35.py "$F35/circuittracks-4486-SC35.bin" "$F35/manifest.json"
run python3 tools/emu_sc35db.py "$F35DB/circuittracks-4486-SC35DB.bin" "$F35DB/manifest.json"
run python3 tools/emu_sc36_dsp.py "$F36/circuittracks-4486-SC36.bin" "$F36/manifest.json" "$F35/circuittracks-4486-SC35.bin" "$F35/manifest.json"
run python3 tools/emu_sc36.py "$F36/circuittracks-4486-SC36.bin" "$F36/manifest.json"
run python3 tools/emu_sc25.py "$F36/circuittracks-4486-SC36.bin" "$F36/manifest.json"
run python3 tools/emu_sc28.py "$F36/circuittracks-4486-SC36.bin" "$F36/manifest.json"
run python3 tools/emu_sc31.py "$F36/circuittracks-4486-SC36.bin" "$F36/manifest.json"
run python3 tools/emu_sc33_sd.py "$F36/circuittracks-4486-SC36.bin" "$F36/manifest.json"
run python3 tools/emu_sc30.py "$F29/circuittracks-4486-SC29.bin" "$F36/circuittracks-4486-SC36.bin" "$F29/manifest.json" "$F36/manifest.json"
run python3 tools/emu_sc36_1.py "$F361/circuittracks-4486-SC36.1.bin" "$F361/manifest.json"
run python3 tools/emu_sc25.py "$F361/circuittracks-4486-SC36.1.bin" "$F361/manifest.json"
run python3 tools/emu_sc36_1.py "$F361S/circuittracks-4486-SC361S.bin" "$F361S/manifest.json"
run python3 tools/emu_sc36_1.py "$F362/circuittracks-4486-SC36.2.bin" "$F362/manifest.json"
run python3 tools/emu_sc25.py "$F362/circuittracks-4486-SC36.2.bin" "$F362/manifest.json"
run python3 tools/emu_sc36_1.py "$F362S/circuittracks-4486-SC362S.bin" "$F362S/manifest.json"
run python3 tools/emu_sc36_1.py "$FRC0/circuittracks-4486-RC0.bin" "$FRC0/manifest.json"
run python3 tools/emu_sc25.py "$FRC0/circuittracks-4486-RC0.bin" "$FRC0/manifest.json"
run python3 tools/emu_sc36_1.py "$FRC0S/circuittracks-4486-RC0S.bin" "$FRC0S/manifest.json"
run python3 tools/emu_sc35.py "$F37/circuittracks-4486-SC37.bin" "$F37/manifest.json"
run python3 tools/emu_sc36_1.py "$F37/circuittracks-4486-SC37.bin" "$F37/manifest.json"
run python3 tools/emu_sc25.py "$F37/circuittracks-4486-SC37.bin" "$F37/manifest.json"
run python3 tools/emu_sc36_dsp.py "$F37/circuittracks-4486-SC37.bin" "$F37/manifest.json" "$F35/circuittracks-4486-SC35.bin" "$F35/manifest.json"
run python3 tools/emu_sc35.py "$F371/circuittracks-4486-SC37.1.bin" "$F371/manifest.json"
run python3 tools/emu_sc36_1.py "$F371/circuittracks-4486-SC37.1.bin" "$F371/manifest.json"
run python3 tools/emu_sc25.py "$F371/circuittracks-4486-SC37.1.bin" "$F371/manifest.json"
run python3 tools/emu_sc35.py "$F372/circuittracks-4486-SC37.2.bin" "$F372/manifest.json"
run python3 tools/emu_sc36_1.py "$F372/circuittracks-4486-SC37.2.bin" "$F372/manifest.json"
run python3 tools/emu_sc25.py "$F372/circuittracks-4486-SC37.2.bin" "$F372/manifest.json"
run python3 tools/emu_sc35.py "$F373/circuittracks-4486-SC37.3.bin" "$F373/manifest.json"
run python3 tools/emu_sc36_1.py "$F373/circuittracks-4486-SC37.3.bin" "$F373/manifest.json"
run python3 tools/emu_sc25.py "$F373/circuittracks-4486-SC37.3.bin" "$F373/manifest.json"
run python3 tools/emu_sc35.py "$F374/circuittracks-4486-SC37.4.bin" "$F374/manifest.json"
run python3 tools/emu_sc36_1.py "$F374/circuittracks-4486-SC37.4.bin" "$F374/manifest.json"
run python3 tools/emu_sc25.py "$F374/circuittracks-4486-SC37.4.bin" "$F374/manifest.json"
run python3 tools/emu_sc37_4.py "$F374/circuittracks-4486-SC37.4.bin" "$F373/circuittracks-4486-SC37.3.bin"
run python3 tools/emu_sc37_4_dsp.py "$F374/circuittracks-4486-SC37.4.bin" "$F374/manifest.json" "$F373/circuittracks-4486-SC37.3.bin" "$F373/manifest.json"
run python3 tools/emu_sc35.py "$FRC01/circuittracks-4486-RC0.1.bin" "$FRC01/manifest.json"
run python3 tools/emu_sc36_1.py "$FRC01/circuittracks-4486-RC0.1.bin" "$FRC01/manifest.json"
run python3 tools/emu_sc25.py "$FRC01/circuittracks-4486-RC0.1.bin" "$FRC01/manifest.json"
run python3 tools/emu_sc36_1.py "$FRC01S/circuittracks-4486-RC0.1S.bin" "$FRC01S/manifest.json"
run python3 tools/emu_sc37_4.py "$FRC01S/circuittracks-4486-RC0.1S.bin" "$FRC0S/circuittracks-4486-RC0S.bin"
run python3 tools/emu_sc37_4_dsp.py "$FRC01S/circuittracks-4486-RC0.1S.bin" "$FRC01S/manifest.json" "$FRC0S/circuittracks-4486-RC0S.bin" "$FRC0S/manifest.json"
run python3 tools/emu_sc37_5_core1.py
run python3 tools/emu_sc35.py "$F375/circuittracks-4486-SC37.5.bin" "$F375/manifest.json"
run python3 tools/emu_sc36_1.py "$F375/circuittracks-4486-SC37.5.bin" "$F375/manifest.json"
run python3 tools/emu_sc25.py "$F375/circuittracks-4486-SC37.5.bin" "$F375/manifest.json"
run python3 tools/emu_sc37_4.py "$F375/circuittracks-4486-SC37.5.bin" "$F374/circuittracks-4486-SC37.4.bin"
run python3 tools/emu_sc35.py "$FRC02/circuittracks-4486-RC0.2.bin" "$FRC02/manifest.json"
run python3 tools/emu_sc36_1.py "$FRC02/circuittracks-4486-RC0.2.bin" "$FRC02/manifest.json"
run python3 tools/emu_sc36_1.py "$FRC02S/circuittracks-4486-RC0.2S.bin" "$FRC02S/manifest.json"
run python3 tools/emu_sc37_4.py "$FRC02S/circuittracks-4486-RC0.2S.bin" "$FRC0S/circuittracks-4486-RC0S.bin"
run python3 tools/emu_sc35.py "$F376/circuittracks-4486-SC37.6.bin" "$F376/manifest.json"
run python3 tools/emu_sc36_1.py "$F376/circuittracks-4486-SC37.6.bin" "$F376/manifest.json"
run python3 tools/emu_sc37_6.py "$F376/circuittracks-4486-SC37.6.bin" "$F376/manifest.json" "$F375/circuittracks-4486-SC37.5.bin" "$F375/manifest.json"
run python3 tools/emu_sc35.py "$F377/circuittracks-4486-SC37.7.bin" "$F377/manifest.json"
run python3 tools/emu_sc36_1.py "$F377/circuittracks-4486-SC37.7.bin" "$F377/manifest.json"
run python3 tools/emu_sc37_6.py "$F377/circuittracks-4486-SC37.7.bin" "$F377/manifest.json"
run python3 tools/emu_sc35.py "$F378/circuittracks-4486-SC37.8.bin" "$F378/manifest.json"
run python3 tools/emu_sc36_1.py "$F378/circuittracks-4486-SC37.8.bin" "$F378/manifest.json"
run python3 tools/emu_sc37_9.py "$F379/circuittracks-4486-SC37.9.bin" "$F379/manifest.json"
run python3 tools/emu_sc23_5_gfx.py "$F379/circuittracks-4486-SC37.9.bin" "$F379/manifest.json"
run python3 tools/emu_sc35.py "$F379/circuittracks-4486-SC37.9.bin" "$F379/manifest.json"
run python3 tools/emu_sc36_1.py "$F379/circuittracks-4486-SC37.9.bin" "$F379/manifest.json"
run python3 tools/emu_sc38.py "$F38/circuittracks-4486-SC38.bin" "$F38/manifest.json" "$F379/circuittracks-4486-SC37.9.bin" "$F379/manifest.json"
run python3 tools/emu_sc37_9.py "$F38/circuittracks-4486-SC38.bin" "$F38/manifest.json"
run python3 tools/emu_sc35.py "$F38/circuittracks-4486-SC38.bin" "$F38/manifest.json"
run python3 tools/emu_sc36_1.py "$F38/circuittracks-4486-SC38.bin" "$F38/manifest.json"
run python3 tools/emu_sc35.py "$FRC03/circuittracks-4486-RC0.3.bin" "$FRC03/manifest.json"
run python3 tools/emu_sc36_1.py "$FRC03/circuittracks-4486-RC0.3.bin" "$FRC03/manifest.json"
run python3 tools/emu_sc36_1.py "$FRC03S/circuittracks-4486-RC0.3S.bin" "$FRC03S/manifest.json"
run python3 tools/emu_sc37_4.py "$FRC03S/circuittracks-4486-RC0.3S.bin" "$FRC0S/circuittracks-4486-RC0S.bin"
run python3 tools/emu_sc37_6.py "$FRC03S/circuittracks-4486-RC0.3S.bin" "$FRC03S/manifest.json"
run python3 tools/emu_sc37_9.py "$FRC03S/circuittracks-4486-RC0.3S.bin" "$FRC03S/manifest.json"
run python3 tools/emu_sc38.py "$FRC03S/circuittracks-4486-RC0.3S.bin" "$FRC03S/manifest.json" "$FRC02S/circuittracks-4486-RC0.2S.bin" "$FRC02S/manifest.json"
run python3 tools/emu_sc38_1.py "$F381/circuittracks-4486-SC38.1.bin" "$F381/manifest.json" "$F38/circuittracks-4486-SC38.bin" "$F38/manifest.json"
run python3 tools/emu_sc38_1_core1.py
run python3 tools/emu_sc36_1.py "$F381/circuittracks-4486-SC38.1.bin" "$F381/manifest.json"
run python3 tools/emu_sc35.py "$F381/circuittracks-4486-SC38.1.bin" "$F381/manifest.json"
run python3 tools/emu_sc38_2.py "$F382/circuittracks-4486-SC38.2.bin" "$F382/manifest.json" "$F381/circuittracks-4486-SC38.1.bin" "$F381/manifest.json"
run python3 tools/emu_sc38_1.py "$F382/circuittracks-4486-SC38.2.bin" "$F382/manifest.json" "$F38/circuittracks-4486-SC38.bin" "$F38/manifest.json"
run python3 tools/emu_sc38_3.py "$F383/circuittracks-4486-SC38.3.bin" "$F383/manifest.json"
run python3 tools/emu_sc38_2.py "$F383/circuittracks-4486-SC38.3.bin" "$F383/manifest.json" "$F381/circuittracks-4486-SC38.1.bin" "$F381/manifest.json"
run python3 tools/emu_sc37_4.py "$F383/circuittracks-4486-SC38.3.bin" "$F382/circuittracks-4486-SC38.2.bin"
run python3 tools/emu_sc38_4.py "$F384/circuittracks-4486-SC38.4.bin" "$F384/manifest.json" "$F383/circuittracks-4486-SC38.3.bin" "$F383/manifest.json"
run python3 tools/emu_sc35.py "$F384/circuittracks-4486-SC38.4.bin" "$F384/manifest.json"
run python3 tools/emu_sc38_3.py "$F384/circuittracks-4486-SC38.4.bin" "$F384/manifest.json"
run python3 tools/emu_sc38_2.py "$F384/circuittracks-4486-SC38.4.bin" "$F384/manifest.json" "$F381/circuittracks-4486-SC38.1.bin" "$F381/manifest.json"
run python3 tools/emu_sc38_5.py "$F385/circuittracks-4486-SC38.5.bin" "$F385/manifest.json" "$F384/circuittracks-4486-SC38.4.bin" "$F384/manifest.json"
run python3 tools/emu_sc35.py "$F385/circuittracks-4486-SC38.5.bin" "$F385/manifest.json"
run python3 tools/emu_sc38_4.py "$F385/circuittracks-4486-SC38.5.bin" "$F385/manifest.json" "$F383/circuittracks-4486-SC38.3.bin" "$F383/manifest.json"
run python3 tools/emu_sc35.py "$F386/circuittracks-4486-SC38.6.bin" "$F386/manifest.json"
run python3 tools/emu_sc38_5.py "$F386/circuittracks-4486-SC38.6.bin" "$F386/manifest.json" "$F384/circuittracks-4486-SC38.4.bin" "$F384/manifest.json"
run python3 tools/emu_sc38_7.py "$F387/circuittracks-4486-SC38.7.bin" "$F387/manifest.json" "$F386/circuittracks-4486-SC38.6.bin" "$F386/manifest.json"
run python3 tools/emu_sc38_1.py "$F387/circuittracks-4486-SC38.7.bin" "$F387/manifest.json" "$F38/circuittracks-4486-SC38.bin" "$F38/manifest.json"
run python3 tools/emu_sc38_8.py "$F388/circuittracks-4486-SC38.8.bin" "$F388/manifest.json" "$F387/circuittracks-4486-SC38.7.bin" "$F387/manifest.json"
run python3 tools/emu_sc35.py "$F388/circuittracks-4486-SC38.8.bin" "$F388/manifest.json"
run python3 tools/emu_sc38_9.py "$F389/circuittracks-4486-SC38.9.bin" "$F389/manifest.json" "$F388/circuittracks-4486-SC38.8.bin" "$F388/manifest.json"
run python3 tools/emu_sc38_8.py "$F389/circuittracks-4486-SC38.9.bin" "$F389/manifest.json" "$F387/circuittracks-4486-SC38.7.bin" "$F387/manifest.json"
run python3 tools/emu_sc39.py "$F39/circuittracks-4486-SC39.bin" "$F39/manifest.json" "$F389/circuittracks-4486-SC38.9.bin" "$F389/manifest.json"
run python3 tools/emu_sc38_9.py "$F39/circuittracks-4486-SC39.bin" "$F39/manifest.json" "$F388/circuittracks-4486-SC38.8.bin" "$F388/manifest.json"
run python3 tools/emu_sc39.py "$FB1/circuittracks-4486-BETA1.bin" "$FB1/manifest.json" "$F389/circuittracks-4486-SC38.9.bin" "$F389/manifest.json"
run python3 tools/emu_sc39_1.py "$F391/circuittracks-4486-SC39.1.bin" "$F391/manifest.json" "$F39/circuittracks-4486-SC39.bin" "$F39/manifest.json"
run python3 tools/emu_sc39_1_gr.py "$F391/circuittracks-4486-SC39.1.bin" "$F391/manifest.json" "$F39/circuittracks-4486-SC39.bin" "$F39/manifest.json"
run python3 tools/emu_sc39.py "$F391/circuittracks-4486-SC39.1.bin" "$F391/manifest.json" "$F389/circuittracks-4486-SC38.9.bin" "$F389/manifest.json"
run python3 tools/emu_sc38_9.py "$F391/circuittracks-4486-SC39.1.bin" "$F391/manifest.json" "$F388/circuittracks-4486-SC38.8.bin" "$F388/manifest.json"
run python3 tools/emu_sc39_1_reg.py "$F391/circuittracks-4486-SC39.1.bin" "$F391/manifest.json" "$F38/circuittracks-4486-SC38.bin" "$F38/manifest.json"
run python3 tools/emu_sc39_1.py "$FB2/circuittracks-4486-BETA2.bin" "$FB2/manifest.json" "$F39/circuittracks-4486-SC39.bin" "$F39/manifest.json"
run python3 tools/emu_sc39_2_dsp.py "$F392/circuittracks-4486-SC39.2.bin" "$F392/manifest.json" "$F391/circuittracks-4486-SC39.1.bin" "$F391/manifest.json"
run python3 tools/emu_sc39_2_dsp.py "$FB3/circuittracks-4486-BETA3.bin" "$FB3/manifest.json" "$FB2/circuittracks-4486-BETA2.bin" "$FB2/manifest.json"
run python3 tools/emu_sc39_2_dsp.py "$FRC05/circuittracks-4486-RC0.5.bin" "$FRC05/manifest.json" "$FRC04/circuittracks-4486-RC0.4.bin" "$FRC04/manifest.json"
run python3 tools/emu_sc39_2_dsp.py "$FRC05S/circuittracks-4486-RC0.5S.bin" "$FRC05S/manifest.json" "$FRC04S/circuittracks-4486-RC0.4S.bin" "$FRC04S/manifest.json"
run python3 tools/emu_sc38_5.py "$FRC05/circuittracks-4486-RC0.5.bin" "$FRC05/manifest.json" "$FRC03/circuittracks-4486-RC0.3.bin" "$FRC03/manifest.json"
run python3 tools/emu_sc38_5.py "$FRC05S/circuittracks-4486-RC0.5S.bin" "$FRC05S/manifest.json" "$FRC03S/circuittracks-4486-RC0.3S.bin" "$FRC03S/manifest.json"
run python3 tools/emu_rc0_6.py firmware/rc0.6/circuittracks-4486-RC0.6.bin firmware/rc0.6/manifest.json "$FRC05/circuittracks-4486-RC0.5.bin" "$FRC05/manifest.json"
run python3 tools/emu_rc0_6.py firmware/rc0.6s/circuittracks-4486-RC0.6S.bin firmware/rc0.6s/manifest.json "$FRC05S/circuittracks-4486-RC0.5S.bin" "$FRC05S/manifest.json"
run python3 tools/emu_sc38_5.py firmware/rc0.6/circuittracks-4486-RC0.6.bin firmware/rc0.6/manifest.json "$FRC03/circuittracks-4486-RC0.3.bin" "$FRC03/manifest.json"
run python3 tools/emu_sc38_5.py firmware/rc0.6s/circuittracks-4486-RC0.6S.bin firmware/rc0.6s/manifest.json "$FRC03S/circuittracks-4486-RC0.3S.bin" "$FRC03S/manifest.json"
run python3 tools/emu_sc39_1.py "$F392/circuittracks-4486-SC39.2.bin" "$F392/manifest.json" "$F39/circuittracks-4486-SC39.bin" "$F39/manifest.json"
run python3 tools/emu_sc39_3.py "$F393/circuittracks-4486-SC39.3.bin" "$F393/manifest.json" "$F392/circuittracks-4486-SC39.2.bin" "$F392/manifest.json"
run python3 tools/emu_sc39_1.py "$F393/circuittracks-4486-SC39.3.bin" "$F393/manifest.json" "$F39/circuittracks-4486-SC39.bin" "$F39/manifest.json"
run python3 tools/emu_sc39_4.py "$F394/circuittracks-4486-SC39.4.bin" "$F394/manifest.json" "$F393/circuittracks-4486-SC39.3.bin" "$F393/manifest.json"
run python3 tools/emu_sc39_3.py "$F394/circuittracks-4486-SC39.4.bin" "$F394/manifest.json" "$F392/circuittracks-4486-SC39.2.bin" "$F392/manifest.json"
run python3 tools/emu_sc39_4.py "$FB4/circuittracks-4486-BETA4.bin" "$FB4/manifest.json" "$FB3/circuittracks-4486-BETA3.bin" "$FB3/manifest.json"
run python3 tools/emu_sc39_5.py "$F395/circuittracks-4486-SC39.5.bin" "$F395/manifest.json" "$F394/circuittracks-4486-SC39.4.bin" "$F394/manifest.json"
run python3 tools/emu_sc39_4.py "$F395/circuittracks-4486-SC39.5.bin" "$F395/manifest.json" "$F393/circuittracks-4486-SC39.3.bin" "$F393/manifest.json"
run python3 tools/emu_sc39_6.py "$F396/circuittracks-4486-SC39.6.bin" "$F396/manifest.json" "$F395/circuittracks-4486-SC39.5.bin" "$F395/manifest.json"
run python3 tools/emu_sc39_6.py "$FB5/circuittracks-4486-BETA5.bin" "$FB5/manifest.json" "$FB4/circuittracks-4486-BETA4.bin" "$FB4/manifest.json"
run python3 tools/emu_sc39_7.py "$F397/circuittracks-4486-SC39.7.bin" "$F397/manifest.json" "$F396/circuittracks-4486-SC39.6.bin" "$F396/manifest.json"
run python3 tools/emu_sc39_6.py "$F397/circuittracks-4486-SC39.7.bin" "$F397/manifest.json" "$F395/circuittracks-4486-SC39.5.bin" "$F395/manifest.json"
run python3 tools/emu_sc39_8.py "$F398/circuittracks-4486-SC39.8.bin" "$F398/manifest.json" "$F397/circuittracks-4486-SC39.7.bin" "$F397/manifest.json"
run python3 tools/emu_sc39_7.py "$F398/circuittracks-4486-SC39.8.bin" "$F398/manifest.json" "$F396/circuittracks-4486-SC39.6.bin" "$F396/manifest.json"
run python3 tools/emu_sc39_9.py "$F399/circuittracks-4486-SC39.9.bin" "$F399/manifest.json" "$F398/circuittracks-4486-SC39.8.bin" "$F398/manifest.json"
run python3 tools/emu_sc39_8.py "$F399/circuittracks-4486-SC39.9.bin" "$F399/manifest.json" "$F397/circuittracks-4486-SC39.7.bin" "$F397/manifest.json"
run python3 tools/emu_sc40.py "$F40/circuittracks-4486-SC40.bin" "$F40/manifest.json" "$F399/circuittracks-4486-SC39.9.bin" "$F399/manifest.json"
run python3 tools/emu_sc39_9.py "$F40/circuittracks-4486-SC40.bin" "$F40/manifest.json" "$F398/circuittracks-4486-SC39.8.bin" "$F398/manifest.json"
run python3 tools/emu_sc40d.py firmware/sc40d/circuittracks-4486-SC40D.bin firmware/sc40d/manifest.json
run python3 tools/emu_sc40_1.py firmware/sc40.1/circuittracks-4486-SC40.1.bin firmware/sc40.1/manifest.json "$F40/circuittracks-4486-SC40.bin" "$F40/manifest.json"
run python3 tools/emu_sc40_2.py firmware/sc40.2/circuittracks-4486-SC40.2.bin firmware/sc40.2/manifest.json firmware/sc40.1/circuittracks-4486-SC40.1.bin firmware/sc40.1/manifest.json
run python3 tools/emu_fsel.py firmware/r0901/circuittracks-4486-R0901.bin firmware/r0901/manifest.json firmware/rc0.9/circuittracks-4486-RC0.9.bin firmware/rc0.9/manifest.json
run python3 tools/emu_fsel.py firmware/r0901s/circuittracks-4486-R0901S.bin firmware/r0901s/manifest.json firmware/rc0.9s/circuittracks-4486-RC0.9S.bin firmware/rc0.9s/manifest.json
run python3 tools/emu_fsel.py firmware/sc41.4/circuittracks-4486-SC41.4.bin firmware/sc41.4/manifest.json firmware/sc41.3/circuittracks-4486-SC41.3.bin firmware/sc41.3/manifest.json
run python3 tools/emu_pgmch.py firmware/sc41.5/circuittracks-4486-SC41.5.bin firmware/sc41.5/manifest.json firmware/sc41.4/circuittracks-4486-SC41.4.bin firmware/sc41.4/manifest.json
run python3 tools/emu_setupfix.py firmware/sc41.5/circuittracks-4486-SC41.5.bin firmware/sc41.5/manifest.json firmware/sc41.4/circuittracks-4486-SC41.4.bin firmware/sc41.4/manifest.json
run python3 tools/emu_setupfix.py firmware/r0902/circuittracks-4486-R0902.bin firmware/r0902/manifest.json firmware/r0901/circuittracks-4486-R0901.bin firmware/r0901/manifest.json
run python3 tools/emu_setupfix.py firmware/r0902s/circuittracks-4486-R0902S.bin firmware/r0902s/manifest.json firmware/r0901s/circuittracks-4486-R0901S.bin firmware/r0901s/manifest.json
run python3 tools/emu_pgmch_pf.py firmware/sc41.6/circuittracks-4486-SC41.6.bin firmware/sc41.6/manifest.json firmware/sc41.5/circuittracks-4486-SC41.5.bin firmware/sc41.5/manifest.json
run python3 tools/emu_pgmch.py firmware/sc41.6/circuittracks-4486-SC41.6.bin firmware/sc41.6/manifest.json firmware/sc41.4/circuittracks-4486-SC41.4.bin firmware/sc41.4/manifest.json
run python3 tools/emu_k3split.py firmware/sc41.7/circuittracks-4486-SC41.7.bin firmware/sc41.7/manifest.json firmware/sc41.6/circuittracks-4486-SC41.6.bin firmware/sc41.6/manifest.json
run python3 tools/emu_k3split_dsp.py firmware/sc41.7/circuittracks-4486-SC41.7.bin firmware/sc41.7/manifest.json firmware/sc41.6/circuittracks-4486-SC41.6.bin firmware/sc41.6/manifest.json
run python3 tools/emu_clrmod.py firmware/sc41.7/circuittracks-4486-SC41.7.bin firmware/sc41.7/manifest.json
run python3 tools/emu_countin.py firmware/sc41.8/circuittracks-4486-SC41.8.bin firmware/sc41.8/manifest.json
run python3 tools/emu_countin.py firmware/b1.8/circuittracks-4486-B1.8.bin firmware/b1.8/manifest.json
run python3 tools/emu_clrmod.py firmware/sc41.8/circuittracks-4486-SC41.8.bin firmware/sc41.8/manifest.json
run python3 tools/emu_arp.py firmware/sc41.9/circuittracks-4486-SC41.9.bin firmware/sc41.9/manifest.json
run python3 tools/emu_arp.py firmware/b1.9/circuittracks-4486-B1.9.bin firmware/b1.9/manifest.json
run python3 tools/emu_countin.py firmware/sc41.9/circuittracks-4486-SC41.9.bin firmware/sc41.9/manifest.json
run python3 tools/emu_clrmod.py firmware/sc41.9/circuittracks-4486-SC41.9.bin firmware/sc41.9/manifest.json
run python3 tools/emu_stutdiag.py firmware/sc419d/circuittracks-4486-SC419D.bin firmware/sc419d/manifest.json
run python3 tools/emu_s419d2.py firmware/s419d2/circuittracks-4486-S419D2.bin firmware/s419d2/manifest.json
run python3 tools/emu_lazysave.py firmware/sc42/circuittracks-4486-SC42.bin firmware/sc42/manifest.json
run python3 tools/emu_lazysave.py firmware/b1.10/circuittracks-4486-B1.10.bin firmware/b1.10/manifest.json
run python3 tools/emu_lazysave.py firmware/r0903/circuittracks-4486-R0903.bin firmware/r0903/manifest.json
run python3 tools/emu_lazysave.py firmware/r0903s/circuittracks-4486-R0903S.bin firmware/r0903s/manifest.json
run python3 tools/emu_lazysave.py firmware/sc42.1/circuittracks-4486-SC42.1.bin firmware/sc42.1/manifest.json
run python3 tools/emu_playhold.py firmware/sc42.1/circuittracks-4486-SC42.1.bin firmware/sc42.1/manifest.json firmware/sc42/circuittracks-4486-SC42.bin
run python3 tools/emu_playhold.py firmware/b1.11/circuittracks-4486-B1.11.bin firmware/b1.11/manifest.json
run python3 tools/emu_s419d2.py firmware/s421d/circuittracks-4486-S421D.bin firmware/s421d/manifest.json
run python3 tools/emu_s419d2.py firmware/r0903d/circuittracks-4486-R0903D.bin firmware/r0903d/manifest.json
run python3 tools/emu_cscale.py firmware/sc42.2/circuittracks-4486-SC42.2.bin firmware/sc42.2/manifest.json firmware/sc42.1/circuittracks-4486-SC42.1.bin
run python3 tools/emu_cscale.py firmware/b1.12/circuittracks-4486-B1.12.bin firmware/b1.12/manifest.json
run python3 tools/emu_arprate.py firmware/sc42.3/circuittracks-4486-SC42.3.bin firmware/sc42.3/manifest.json
run python3 tools/emu_arprate.py firmware/b1.13/circuittracks-4486-B1.13.bin firmware/b1.13/manifest.json
run python3 tools/emu_sc42_4.py firmware/sc42.4/circuittracks-4486-SC42.4.bin firmware/sc42.4/manifest.json
run python3 tools/emu_sc42_4.py firmware/b1.14/circuittracks-4486-B1.14.bin firmware/b1.14/manifest.json
run python3 tools/emu_sc42_5.py firmware/sc42.5/circuittracks-4486-SC42.5.bin firmware/sc42.5/manifest.json
run python3 tools/emu_sc42_5.py firmware/b1.15/circuittracks-4486-B1.15.bin firmware/b1.15/manifest.json
run python3 tools/emu_sc42_6.py firmware/sc42.6/circuittracks-4486-SC42.6.bin firmware/sc42.6/manifest.json firmware/sc42.5/circuittracks-4486-SC42.5.bin firmware/sc42.5/manifest.json
run python3 tools/emu_sc42_6.py firmware/b1.16/circuittracks-4486-B1.16.bin firmware/b1.16/manifest.json
run python3 tools/emu_sc42_7.py firmware/sc42.7/circuittracks-4486-SC42.7.bin firmware/sc42.7/manifest.json
run python3 tools/emu_sc42_7.py firmware/b1.17/circuittracks-4486-B1.17.bin firmware/b1.17/manifest.json
run python3 tools/emu_sc42_8.py firmware/sc42.8/circuittracks-4486-SC42.8.bin firmware/sc42.8/manifest.json
run python3 tools/emu_sc42_8.py firmware/b1.18/circuittracks-4486-B1.18.bin firmware/b1.18/manifest.json
run python3 tools/emu_sc42_9.py firmware/sc42.9/circuittracks-4486-SC42.9.bin firmware/sc42.9/manifest.json
run python3 tools/emu_sc42_9.py firmware/b1.19/circuittracks-4486-B1.19.bin firmware/b1.19/manifest.json
run python3 tools/emu_sc43.py firmware/sc43/circuittracks-4486-SC43.bin firmware/sc43/manifest.json firmware/sc42.9/circuittracks-4486-SC42.9.bin firmware/sc42.9/manifest.json
run python3 tools/emu_sc43.py firmware/b1.20/circuittracks-4486-B1.20.bin firmware/b1.20/manifest.json
run python3 tools/emu_sc42_9.py firmware/sc43/circuittracks-4486-SC43.bin firmware/sc43/manifest.json
run python3 tools/emu_sc42_8.py firmware/sc43/circuittracks-4486-SC43.bin firmware/sc43/manifest.json
run python3 tools/emu_sc42_7.py firmware/sc43/circuittracks-4486-SC43.bin firmware/sc43/manifest.json
run python3 tools/emu_sc43_1.py firmware/sc43.1/circuittracks-4486-SC43.1.bin firmware/sc43.1/manifest.json firmware/sc43/circuittracks-4486-SC43.bin firmware/sc43/manifest.json
run python3 tools/emu_sc43_1.py firmware/b1.21/circuittracks-4486-B1.21.bin firmware/b1.21/manifest.json
run python3 tools/emu_sc43.py firmware/sc43.1/circuittracks-4486-SC43.1.bin firmware/sc43.1/manifest.json
run python3 tools/emu_sc42_9.py firmware/sc43.1/circuittracks-4486-SC43.1.bin firmware/sc43.1/manifest.json
run python3 tools/emu_sc42_8.py firmware/sc43.1/circuittracks-4486-SC43.1.bin firmware/sc43.1/manifest.json
run python3 tools/emu_sc42_7.py firmware/sc43.1/circuittracks-4486-SC43.1.bin firmware/sc43.1/manifest.json
run python3 tools/emu_sc43_2.py firmware/sc43.2/circuittracks-4486-SC43.2.bin firmware/sc43.2/manifest.json firmware/sc43.1/circuittracks-4486-SC43.1.bin firmware/sc43.1/manifest.json
run python3 tools/emu_sc43_2.py firmware/b1.22/circuittracks-4486-B1.22.bin firmware/b1.22/manifest.json
run python3 tools/emu_sc43_3.py firmware/sc43.3/circuittracks-4486-SC43.3.bin firmware/sc43.3/manifest.json
run python3 tools/emu_sc43_3.py firmware/b1.23/circuittracks-4486-B1.23.bin firmware/b1.23/manifest.json
run python3 tools/emu_sc43_4.py firmware/sc43.4/circuittracks-4486-SC43.4.bin firmware/sc43.4/manifest.json
run python3 tools/emu_sc43_4.py firmware/b1.24/circuittracks-4486-B1.24.bin firmware/b1.24/manifest.json
run python3 tools/emu_sc44.py firmware/sc44/circuittracks-4486-SC44.bin firmware/sc44/manifest.json
run python3 tools/emu_sc44.py firmware/rc2/circuittracks-4486-RC2.bin firmware/rc2/manifest.json
run python3 tools/emu_sc44.py firmware/rc2s/circuittracks-4486-RC2S.bin firmware/rc2s/manifest.json
run python3 tools/emu_rodisk.py firmware/rc2/circuittracks-4486-RC2.bin firmware/rc2/manifest.json firmware/sc41.2/circuittracks-4486-SC41.2.bin firmware/sc41.2/manifest.json
run python3 tools/emu_rodisk.py firmware/rc2s/circuittracks-4486-RC2S.bin firmware/rc2s/manifest.json firmware/sc41.2/circuittracks-4486-SC41.2.bin firmware/sc41.2/manifest.json
run python3 tools/emu_sc44.py firmware/b1.30/circuittracks-4486-B1.30.bin firmware/b1.30/manifest.json
run python3 tools/emu_sc44_dsp.py firmware/sc44/circuittracks-4486-SC44.bin firmware/sc44/manifest.json firmware/sc43.9/circuittracks-4486-SC43.9.bin firmware/sc43.9/manifest.json
run python3 tools/emu_sc43_9.py firmware/sc43.9/circuittracks-4486-SC43.9.bin firmware/sc43.9/manifest.json
run python3 tools/emu_sc43_9.py firmware/b1.29/circuittracks-4486-B1.29.bin firmware/b1.29/manifest.json
run python3 tools/emu_sc43_9_dsp.py firmware/sc43.9/circuittracks-4486-SC43.9.bin firmware/sc43.9/manifest.json firmware/sc43.8/circuittracks-4486-SC43.8.bin firmware/sc43.8/manifest.json
run python3 tools/emu_sc43_8.py firmware/sc43.8/circuittracks-4486-SC43.8.bin firmware/sc43.8/manifest.json
run python3 tools/emu_sc43_8.py firmware/b1.28/circuittracks-4486-B1.28.bin firmware/b1.28/manifest.json
run python3 tools/emu_sc43_7.py firmware/sc43.7/circuittracks-4486-SC43.7.bin firmware/sc43.7/manifest.json
run python3 tools/emu_sc43_7.py firmware/b1.27/circuittracks-4486-B1.27.bin firmware/b1.27/manifest.json
run python3 tools/emu_sc43_4.py firmware/sc43.7/circuittracks-4486-SC43.7.bin firmware/sc43.7/manifest.json
run python3 tools/emu_sc43.py firmware/sc43.7/circuittracks-4486-SC43.7.bin firmware/sc43.7/manifest.json
run python3 tools/emu_sc42_7.py firmware/sc43.7/circuittracks-4486-SC43.7.bin firmware/sc43.7/manifest.json
run python3 tools/emu_sc43_6.py firmware/sc43.6/circuittracks-4486-SC43.6.bin firmware/sc43.6/manifest.json
run python3 tools/emu_sc43_6.py firmware/b1.26/circuittracks-4486-B1.26.bin firmware/b1.26/manifest.json
run python3 tools/emu_sc43_5.py firmware/sc43.6/circuittracks-4486-SC43.6.bin firmware/sc43.6/manifest.json
run python3 tools/emu_sc43_4.py firmware/sc43.6/circuittracks-4486-SC43.6.bin firmware/sc43.6/manifest.json
run python3 tools/emu_sc43.py firmware/sc43.6/circuittracks-4486-SC43.6.bin firmware/sc43.6/manifest.json
run python3 tools/emu_sc42_7.py firmware/sc43.6/circuittracks-4486-SC43.6.bin firmware/sc43.6/manifest.json
run python3 tools/emu_sc43_5.py firmware/sc43.5/circuittracks-4486-SC43.5.bin firmware/sc43.5/manifest.json
run python3 tools/emu_sc43_5.py firmware/b1.25/circuittracks-4486-B1.25.bin firmware/b1.25/manifest.json
run python3 tools/emu_sc43_4.py firmware/sc43.5/circuittracks-4486-SC43.5.bin firmware/sc43.5/manifest.json
run python3 tools/emu_sc43.py firmware/sc43.5/circuittracks-4486-SC43.5.bin firmware/sc43.5/manifest.json
run python3 tools/emu_sc42_7.py firmware/sc43.5/circuittracks-4486-SC43.5.bin firmware/sc43.5/manifest.json
run python3 tools/emu_sc43_2.py firmware/sc43.4/circuittracks-4486-SC43.4.bin firmware/sc43.4/manifest.json
run python3 tools/emu_sc43_1.py firmware/sc43.4/circuittracks-4486-SC43.4.bin firmware/sc43.4/manifest.json
run python3 tools/emu_sc43.py firmware/sc43.4/circuittracks-4486-SC43.4.bin firmware/sc43.4/manifest.json
run python3 tools/emu_sc42_7.py firmware/sc43.4/circuittracks-4486-SC43.4.bin firmware/sc43.4/manifest.json
run python3 tools/emu_sc43_2.py firmware/sc43.3/circuittracks-4486-SC43.3.bin firmware/sc43.3/manifest.json
run python3 tools/emu_sc43_1.py firmware/sc43.3/circuittracks-4486-SC43.3.bin firmware/sc43.3/manifest.json
run python3 tools/emu_sc43.py firmware/sc43.3/circuittracks-4486-SC43.3.bin firmware/sc43.3/manifest.json
run python3 tools/emu_sc42_7.py firmware/sc43.3/circuittracks-4486-SC43.3.bin firmware/sc43.3/manifest.json
run python3 tools/emu_sc43_1.py firmware/sc43.2/circuittracks-4486-SC43.2.bin firmware/sc43.2/manifest.json
run python3 tools/emu_sc43.py firmware/sc43.2/circuittracks-4486-SC43.2.bin firmware/sc43.2/manifest.json
run python3 tools/emu_sc42_9.py firmware/sc43.2/circuittracks-4486-SC43.2.bin firmware/sc43.2/manifest.json
run python3 tools/emu_sc42_8.py firmware/sc43.2/circuittracks-4486-SC43.2.bin firmware/sc43.2/manifest.json
run python3 tools/emu_sc42_8.py firmware/sc42.9/circuittracks-4486-SC42.9.bin firmware/sc42.9/manifest.json
run python3 tools/emu_sc42_7.py firmware/sc42.8/circuittracks-4486-SC42.8.bin firmware/sc42.8/manifest.json
run python3 tools/emu_sc41.py firmware/sc42.7/circuittracks-4486-SC42.7.bin firmware/sc42.7/manifest.json firmware/sc40.9/circuittracks-4486-SC40.9.bin firmware/sc40.9/manifest.json
run python3 tools/emu_sc42_5.py firmware/sc42.6/circuittracks-4486-SC42.6.bin firmware/sc42.6/manifest.json
run python3 tools/emu_sc41.py firmware/sc42.6/circuittracks-4486-SC42.6.bin firmware/sc42.6/manifest.json firmware/sc40.9/circuittracks-4486-SC40.9.bin firmware/sc40.9/manifest.json
run python3 tools/emu_rodisk.py firmware/sc41.3/circuittracks-4486-SC41.3.bin firmware/sc41.3/manifest.json firmware/sc41.2/circuittracks-4486-SC41.2.bin firmware/sc41.2/manifest.json
run python3 tools/emu_rodisk.py firmware/rc0.9/circuittracks-4486-RC0.9.bin firmware/rc0.9/manifest.json firmware/rc0.8/circuittracks-4486-RC0.8.bin firmware/rc0.8/manifest.json
run python3 tools/emu_rodisk.py firmware/b1.3/circuittracks-4486-B1.3.bin firmware/b1.3/manifest.json firmware/sc41.2/circuittracks-4486-SC41.2.bin firmware/sc41.2/manifest.json
run python3 tools/emu_sc41_2.py firmware/sc41.2/circuittracks-4486-SC41.2.bin firmware/sc41.2/manifest.json firmware/sc41.1/circuittracks-4486-SC41.1.bin firmware/sc41.1/manifest.json
run python3 tools/emu_sc40_9.py firmware/b1.2/circuittracks-4486-B1.2.bin firmware/b1.2/manifest.json firmware/sc40.8/circuittracks-4486-SC40.8.bin firmware/sc40.8/manifest.json
run python3 tools/emu_sc41_1.py firmware/b1.2/circuittracks-4486-B1.2.bin firmware/b1.2/manifest.json firmware/sc41/circuittracks-4486-SC41.bin firmware/sc41/manifest.json
run python3 tools/emu_sc41_1.py firmware/sc41.1/circuittracks-4486-SC41.1.bin firmware/sc41.1/manifest.json firmware/sc41/circuittracks-4486-SC41.bin firmware/sc41/manifest.json
run python3 tools/emu_sc41.py firmware/sc41.1/circuittracks-4486-SC41.1.bin firmware/sc41.1/manifest.json firmware/sc40.9/circuittracks-4486-SC40.9.bin firmware/sc40.9/manifest.json
run python3 tools/emu_sc41.py firmware/sc41/circuittracks-4486-SC41.bin firmware/sc41/manifest.json firmware/sc40.9/circuittracks-4486-SC40.9.bin firmware/sc40.9/manifest.json
run python3 tools/emu_sc40_9.py firmware/b1.1/circuittracks-4486-B1.1.bin firmware/b1.1/manifest.json firmware/sc40.8/circuittracks-4486-SC40.8.bin firmware/sc40.8/manifest.json
run python3 tools/emu_sc41.py firmware/rc0.8/circuittracks-4486-RC0.8.bin firmware/rc0.8/manifest.json firmware/rc0.7/circuittracks-4486-RC0.7.bin firmware/rc0.7/manifest.json
run python3 tools/emu_sc41.py firmware/rc0.8s/circuittracks-4486-RC0.8S.bin firmware/rc0.8s/manifest.json firmware/rc0.7s/circuittracks-4486-RC0.7S.bin firmware/rc0.7s/manifest.json
run python3 tools/emu_sc40_9.py firmware/sc40.9/circuittracks-4486-SC40.9.bin firmware/sc40.9/manifest.json firmware/sc40.8/circuittracks-4486-SC40.8.bin firmware/sc40.8/manifest.json
run python3 tools/emu_sc40_9.py firmware/b1.0/circuittracks-4486-B1.0.bin firmware/b1.0/manifest.json firmware/sc40.8/circuittracks-4486-SC40.8.bin firmware/sc40.8/manifest.json
run python3 tools/emu_sc40_8.py firmware/sc40.9/circuittracks-4486-SC40.9.bin firmware/sc40.9/manifest.json firmware/sc40.7/circuittracks-4486-SC40.7.bin firmware/sc40.7/manifest.json
run python3 tools/emu_sc40_3.py firmware/sc40.9/circuittracks-4486-SC40.9.bin firmware/sc40.9/manifest.json firmware/sc40.2/circuittracks-4486-SC40.2.bin firmware/sc40.2/manifest.json
run python3 tools/emu_rc0_7.py firmware/rc0.7/circuittracks-4486-RC0.7.bin firmware/rc0.7/manifest.json firmware/rc0.6/circuittracks-4486-RC0.6.bin firmware/rc0.6/manifest.json
run python3 tools/emu_rc0_7.py firmware/rc0.7s/circuittracks-4486-RC0.7S.bin firmware/rc0.7s/manifest.json firmware/rc0.6s/circuittracks-4486-RC0.6S.bin firmware/rc0.6s/manifest.json
run python3 tools/emu_sc40_8.py firmware/sc40.8/circuittracks-4486-SC40.8.bin firmware/sc40.8/manifest.json firmware/sc40.7/circuittracks-4486-SC40.7.bin firmware/sc40.7/manifest.json
run python3 tools/emu_sc40_3.py firmware/sc40.8/circuittracks-4486-SC40.8.bin firmware/sc40.8/manifest.json firmware/sc40.2/circuittracks-4486-SC40.2.bin firmware/sc40.2/manifest.json
run python3 tools/emu_sc40_5.py firmware/sc40.8/circuittracks-4486-SC40.8.bin firmware/sc40.8/manifest.json firmware/sc40.4/circuittracks-4486-SC40.4.bin firmware/sc40.4/manifest.json
run python3 tools/emu_sc40_7.py firmware/sc40.7/circuittracks-4486-SC40.7.bin firmware/sc40.7/manifest.json firmware/sc40.6/circuittracks-4486-SC40.6.bin firmware/sc40.6/manifest.json
run python3 tools/emu_sc40_3.py firmware/sc40.7/circuittracks-4486-SC40.7.bin firmware/sc40.7/manifest.json firmware/sc40.2/circuittracks-4486-SC40.2.bin firmware/sc40.2/manifest.json
run python3 tools/emu_sc40_5.py firmware/sc40.7/circuittracks-4486-SC40.7.bin firmware/sc40.7/manifest.json firmware/sc40.4/circuittracks-4486-SC40.4.bin firmware/sc40.4/manifest.json
run python3 tools/emu_sc40_5.py firmware/sc40.6/circuittracks-4486-SC40.6.bin firmware/sc40.6/manifest.json firmware/sc40.4/circuittracks-4486-SC40.4.bin firmware/sc40.4/manifest.json
run python3 tools/emu_sc40_5.py firmware/sc40.5/circuittracks-4486-SC40.5.bin firmware/sc40.5/manifest.json firmware/sc40.4/circuittracks-4486-SC40.4.bin firmware/sc40.4/manifest.json
run python3 tools/emu_sc40_3.py firmware/sc40.5/circuittracks-4486-SC40.5.bin firmware/sc40.5/manifest.json firmware/sc40.2/circuittracks-4486-SC40.2.bin firmware/sc40.2/manifest.json
run python3 tools/emu_sc40_3.py firmware/sc40.4/circuittracks-4486-SC40.4.bin firmware/sc40.4/manifest.json firmware/sc40.2/circuittracks-4486-SC40.2.bin firmware/sc40.2/manifest.json
run python3 tools/emu_sc40_3.py firmware/sc40.3/circuittracks-4486-SC40.3.bin firmware/sc40.3/manifest.json firmware/sc40.2/circuittracks-4486-SC40.2.bin firmware/sc40.2/manifest.json
run python3 tools/emu_sc40_2.py firmware/sc40.3/circuittracks-4486-SC40.3.bin firmware/sc40.3/manifest.json firmware/sc40.1/circuittracks-4486-SC40.1.bin firmware/sc40.1/manifest.json
run python3 tools/emu_sc402d.py firmware/sc402d/circuittracks-4486-SC402D.bin firmware/sc402d/manifest.json
run python3 tools/emu_sc403d.py firmware/sc403d/circuittracks-4486-SC403D.bin firmware/sc403d/manifest.json
run python3 tools/emu_sc39_5.py "$F396/circuittracks-4486-SC39.6.bin" "$F396/manifest.json" "$F394/circuittracks-4486-SC39.4.bin" "$F394/manifest.json"
run python3 tools/emu_seqwatch.py "$FSEQW/circuittracks-4486-SEQWD.bin" "$FSEQW/manifest.json"
run python3 tools/emu_sc35d8.py "$FSEQW/circuittracks-4486-SEQWD.bin" "$FSEQW/manifest.json" --dspx
run python3 tools/emu_sc35.py "$FRC04/circuittracks-4486-RC0.4.bin" "$FRC04/manifest.json"
run python3 tools/emu_sc38_4.py "$FRC04/circuittracks-4486-RC0.4.bin" "$FRC04/manifest.json" "$FRC03/circuittracks-4486-RC0.3.bin" "$FRC03/manifest.json"
run python3 tools/emu_sc38_5.py "$FRC04/circuittracks-4486-RC0.4.bin" "$FRC04/manifest.json" "$FRC03/circuittracks-4486-RC0.3.bin" "$FRC03/manifest.json"
run python3 tools/emu_sc38_4.py "$FRC04S/circuittracks-4486-RC0.4S.bin" "$FRC04S/manifest.json" "$FRC03S/circuittracks-4486-RC0.3S.bin" "$FRC03S/manifest.json"
run python3 tools/emu_sc38_5.py "$FRC04S/circuittracks-4486-RC0.4S.bin" "$FRC04S/manifest.json" "$FRC03S/circuittracks-4486-RC0.3S.bin" "$FRC03S/manifest.json"
run python3 tools/emu_sc36_1.py "$FRC04S/circuittracks-4486-RC0.4S.bin" "$FRC04S/manifest.json"
run python3 tools/emu_sc38_7.py "$FB0/circuittracks-4486-BETA0.bin" "$FB0/manifest.json" "$F386/circuittracks-4486-SC38.6.bin" "$F386/manifest.json"
run python3 tools/emu_sc32d.py "$F32D/circuittracks-4486-SC32D.bin" "$F32D/manifest.json"
run python3 tools/emu_sc32d_1.py "$F32D1/circuittracks-4486-SC32D.1.bin" "$F32D1/manifest.json"
run python3 tools/emu_sc32d_2.py "$F32D2/circuittracks-4486-SC32D2.bin" "$F32D2/manifest.json"
run python3 tools/emu_sc21d.py "$IMG20" "$F21D/circuittracks-4486-SC21D.bin" "$MAN20" "$F21D/manifest.json"
run python3 tools/emu_sc20_1.py "$IMG" "$IMG21" "$MAN" "$MAN21"
run python3 tools/emu_sc20d.py "$ST" "$IMG3" "$IMG20" "$MAN20" "$MAN3"
run python3 tools/emu_sc182d.py "$ST" "$REF182" firmware/sc182d/circuittracks-4486-SC182D.bin firmware/sc182d/manifest.json
run python3 tools/emu_sc183d.py "$ST" "$IMG183" firmware/sc183d/circuittracks-4486-SC183D.bin firmware/sc183d/manifest.json
if [ "${1:-quick}" = full ]; then
  run python3 tools/emu_masterfx_dsp.py "$ST"
  run python3 tools/emu_sc17_core.py firmware/sc16/circuittracks-4486-SC16.bin "$IMG" "$MAN"
  run python3 tools/emu_sc17_5_dsp.py "$REF" "$IMG" "$MAN"
  run python3 tools/emu_sc18_dsp.py "$REF18" firmware/sc18/manifest.json "$REF8"
  run python3 tools/emu_sc18_1_dsp.py "$IMG183" "$MAN183" "$REF18"
  run python3 tools/emu_sc19_dsp.py "$IMG" "$MAN" "$IMG183"
  run python3 tools/emu_sc19_fuzz.py "$F191/circuittracks-4486-SC19.1.bin" "$MAN191" "$IMG" "$MAN" 12 80
  run python3 tools/emu_sc19_5_dsp.py "$IMG4" "$IMG5" "$MAN5"
  run python3 tools/emu_sc19_9_dsp.py "$IMG8" "$IMG" "$MAN" "$MAN8"
  run python3 tools/emu_sc20_dsp.py "$IMG9" "$IMG20P" "$MAN20P"
  run python3 tools/emu_sc21_dsp.py "$IMG9" "$IMG21" "$MAN21"
  run python3 tools/emu_sc21_1_dsp.py "$IMG9" "$F211/circuittracks-4486-SC21.1.bin" "$F211/manifest.json"
  run python3 tools/emu_sc21_4_dsp.py "$IMG9" "$F214/circuittracks-4486-SC21.4.bin" "$F214/manifest.json"
  run python3 tools/emu_sc22_dsp.py "$IMG9" "$F22/circuittracks-4486-SC22.bin" "$F22/manifest.json"
  run python3 tools/emu_sc22_1_dsp.py "$IMG9" "$F221/circuittracks-4486-SC22.1.bin" "$F221/manifest.json"
  run python3 tools/emu_sc22_2_dsp.py "$IMG9" "$F222/circuittracks-4486-SC22.2.bin" "$F222/manifest.json"
  run python3 tools/emu_sc22_3_dsp.py "$IMG9" "$F223/circuittracks-4486-SC22.3.bin" "$F223/manifest.json"
  run python3 tools/emu_sc20d_dsp.py "$IMG3" "$IMG20" "$MAN20"
fi
echo; [ $fails -eq 0 ] && echo "TODO OK" || echo "$fails conjuntos de pruebas fallan"
exit $fails
