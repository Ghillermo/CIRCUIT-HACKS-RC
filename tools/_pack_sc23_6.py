"""One-off packaging of SC23.6."""
import json
from pathlib import Path
R = Path(__file__).resolve().parents[1]
m = json.loads((R / "firmware/sc23.6/manifest.json").read_text())
sha = m["syx_sha256"]; size = m["image_size"]
print(sha, size)


def rw(p, f):
    path = R / p
    s = path.read_text(encoding="utf-8")
    n = f(s)
    assert n != s, p
    path.write_text(n, encoding="utf-8", newline="")


def known(s):
    k = s.index('  "aa0b95b2'); j = s.index("\n", k)
    return s[:j + 1] + f'  "{sha}": "4486 + SC23.6: SC23.5 + knobs de tipo (FX, filtro, forma de onda) sin vuelta, con zonas anchas, color por modo y brillo por parametro interno (morph, key follow)",\n' + s[j + 1:]


rw("tools/ct_uploader.html", known)
rw("tools/verify_builds.py", lambda s: s.replace('    ("sc23.5", "build_sc23_5.py", []),\n', '    ("sc23.5", "build_sc23_5.py", []),\n    ("sc23.6", "build_sc23_6.py", []),\n'))
for f in ("tools/emu_sc17.py", "tools/emu_sc17_8.py", "tools/emu_sc19.py", "tools/emu_sc20_1.py"):
    rw(f, lambda s: s.replace('"SC23.4", "SC23.5")', '"SC23.4", "SC23.5", "SC23.6")'))


def rt(s):
    s = s.replace("F235=firmware/sc23.5\n", "F235=firmware/sc23.5\nF236=firmware/sc23.6\n")
    k = 'run python3 tools/emu_sc23_5_dsp.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"\n'
    B = '"$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"'
    add = (f'run python3 tools/emu_sc23_3.py "$IMG9" "$F236/circuittracks-4486-SC23.6.bin" "$MAN9" "$F236/manifest.json"\n'
           f'run python3 tools/emu_sc23_3_fx.py {B}\n'
           f'run python3 tools/emu_sc23_4_notes.py {B}\n'
           f'run python3 tools/emu_sc23_5.py {B}\n'
           f'run python3 tools/emu_sc23_5_gfx.py {B}\n'
           f'run python3 tools/emu_sc23_5_drums.py {B}\n'
           f'run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F236/circuittracks-4486-SC23.6.bin" "$MAN9" "$F236/manifest.json"\n'
           f'run python3 tools/emu_sc23_5_dsp.py {B}\n'
           f'run python3 tools/emu_sc23_6.py {B}\n'
           f'run python3 tools/emu_sc23_6_dsp.py {B} "$F235/circuittracks-4486-SC23.5.bin"\n')
    assert k in s
    return s.replace(k, k + add)


rw("tools/run_tests.sh", rt)
rw("README.md", lambda s: s[:s.index("| SC23.5 |")] + "| SC23.6 | SC23.5 + **knobs de tipo sin vuelta** (tipo de FX = Shift + K8, tipo de filtro = Shift + K5, forma de onda = K7 de la página del OSC): 0..127 pasos con tope en los dos extremos, ~18 clics por modo (FX y filtro: 7 modos), y dentro del modo la posición ajusta un parámetro (FX: el «morph» = FXMOD, que sale de Shift + K7; filtro: seguimiento de la nota en el corte; forma de onda: el morph de siempre); **color del LED = modo elegido, brillo = parámetro del modo** | ⏳ pendiente de probar |\n" + s[s.index("| SC23.5 |"):])


def rc(s):
    i = s.index("- **SC23.5** (`firmware/sc23.5/`")
    new = ("- **SC23.6** (`firmware/sc23.6/`, pendiente de probar) = SC23.5 + `vcf21.use_typezones()` / `vcf21_dsp.use_typezones()` (**knobs de tipo sin vuelta**): el tipo de FX (código 13, Shift + K8) y el de filtro (16, Shift + K5) son knobs 0..127 normales con tope; al DSP va p tal cual y el mailbox calcula zona `t = 7p >> 7` (en el slot del código) y posición `f = 7p & 127` (FX: slot de FXMOD; filtro: palabra `KEYF_OFF = 19` del bloque del oscilador, `X:OSB0 + 48 t + 19`, que sustituye al `KEYK` fijo del seguimiento de la nota); el código 14 (FXMOD) se ignora y Shift + K7 queda sin función; la forma de onda (código 19) no cambia (morph 0..126, formas puras cada 42). LEDs: `c_vtype` (color de `TCOL_FX / TCOL_FT / TCOL_WV` = el modo, brillo `TZ_MINB + f × 95 / 128` = el parámetro); firma `0xAE` (se descarta el estado de SC23.5). Pruebas `emu_sc23_6.py`, `emu_sc23_6_dsp.py`. La tabla del corte del filtro da 8 pasos por octava: seguimiento 1:1 = f ≈ 85.\n")
    return s[:i] + new + s[i:]


rw("CLAUDE.md", rc)


def rn(s):
    i = s.index("### SC23.5 = SC23.4 + ")
    t = ("### SC23.6 = SC23.5 + **knobs de tipo sin vuelta, con zonas y parámetro interno** — ⏳ pendiente de probar\n"
         "- Petición del usuario (2026-10-06, tras confirmar que el oscilador ya no falla): «los knobs de ajuste de tipo (tipo de efecto, forma de onda, tipo de filtro) son demasiado sensibles y ciclan: que hagan falta varios steps (resolución del estado del knob / número de opciones) para cambiar entre modos; dentro de cada modo, usa esos steps para ajustar un parámetro: waveform → morph, efectos → morph, tipo de filtro → note-on follow al cutoff»; después: «descarta también el ciclado; usa colores para señalizar la selección y brillo (o fusión entre colores si puedes ajustar RGB) para el parámetro interno».\n"
         "- **Interpretación.** El estado del knob es p = 0..127 sin vuelta (el tope ya existía en los demás knobs unipolares: `vk_uni`); el tipo es la **zona** `t = 7p >> 7` (7 modos de FX y de filtro: ~18 clics por modo) y la **posición dentro de la zona** `f = 7p & 127` (0..127) es el parámetro del modo. Forma de onda: sin cambios en el DSP; ya era un morph continuo (0 seno, 42 triángulo, 84 sierra, 126 cuadrada, K7 de la página B) con 42 clics entre formas, sin vuelta; solo se añade el LED.\n"
         "- **FX «morph» = FXMOD.** El parámetro propio de cada efecto (umbral de soft / hard / fold, sesgo del wavefold, frecuencia del ring mod, retardo del comb, velocidad del chorus) ya existía como FXMOD (Shift + K7); ahora lo da la posición dentro del modo del tipo y **Shift + K7 queda sin función** (el DSP ignora el código 14). Valor de partida de cada modo: f = 0 (antes FXMOD = 64: los efectos con parámetro empiezan en el extremo de su rango).\n"
         "- **Filtro «note-on follow».** `KEYK = 32` (0,25 pasos de tabla por semitono = 37 % de seguimiento) era fijo; ahora es la palabra `KEYF` = f (0..127) del bloque del oscilador (`X:OSB0 + 48 t + 19`; el bloque usa +0..+18): índice de tabla += (nota − 60) × f / 128. La tabla `TF` da **8 pasos por octava** del coeficiente: f ≈ 85 = una octava por octava; 127 = 1,5. Por defecto f = 0 (sin seguimiento; antes 37 %).\n"
         "- **DSP** (`vcf21_dsp.TYPEZONE`, `use_typezones()`): el mailbox, tras guardar el valor, para los códigos 13 / 16 calcula `7p`, guarda `t` en el slot del código y `f` en FXMOD / `KEYF`; ignora el código 14. +8 instrucciones por bloque (55 358 → 55 366 con las dos voces en la entrada de línea). El programa del DSP sigue por debajo de `$3FFF`.\n"
         "- **ARM** (`vcf21.use_typezones()`): los códigos 13 / 16 pasan por el camino de los knobs unipolares (se quita el paso por giro con vuelta `vk_shape`); `KNOB_CODES` Shift + K7 = 0; firma `0xAE` (se descarta el estado guardado). **LEDs** (`c_vtype`, llamado desde `c_vkleds` para los códigos 13 / 16 / 19): halfword = color del modo | (brillo + 2) << 8, brillo = `32 + f × 95 >> 7` (33 % … 98 %); colores en `TCOL_FX` (soft amarillo `0x2D`, hard naranja `0x2B`, fold rojo `0x45`, wavefold magenta `0x32`, ring violeta `0x49`, comb azul `0x09`, chorus verde azulado `0x4D`), `TCOL_FT` (DJ blanco `0x01`, LP 12 verde `0x17`, HP 12 azul claro `0x13`, paso banda amarillo `0x2D`, notch magenta `0x32`, LP 24 verde azulado `0x4D`, HP 24 azul `0x09`), `TCOL_WV` (seno azul claro, triángulo verde, sierra amarillo, cuadrada rojo `0x45`). **No hay RGB libre:** la tabla de colores de la placa (`0x20003804`, RAM) se indexa por código de paleta; la «fusión» entre modos habría que hacerla con entradas intermedias de la paleta.\n"
         "- Pruebas: `emu_sc23_6.py` (121 clics reales por el controlador, tope arriba y abajo, LEDs, Shift + K7, mailbox, Clear), `emu_sc23_6_dsp.py` (zona y posición para todos los valores relevantes, el código 14 ignorado, el corte sigue la nota: índice 48 → 20, 72 → 43, 84 → 55 con f = 124; coste); las de SC23.5 sobre la imagen nueva (`emu_sc23_3.py` ya con `use_typezones` según la marca).\n"
         f"- Marca `SC23.6`, `firmware/sc23.6/` ({size} B), SHA-256 `{sha}`. Reserva SC23.5.\n\n")
    return s[:i] + t + s[i:]


rw("docs/NOTAS.md", rn)
