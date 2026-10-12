"""One-off packaging of SC23.5."""
import json
from pathlib import Path
R = Path(__file__).resolve().parents[1]
m = json.loads((R / "firmware/sc23.5/manifest.json").read_text())
sha = m["syx_sha256"]; size = m["image_size"]
print(sha, size)


def rw(p, f):
    path = R / p
    s = path.read_text(encoding="utf-8")
    n = f(s)
    assert n != s, p
    path.write_text(n, encoding="utf-8", newline="")


def known(s):
    k = s.index('  "45d83863'); j = s.index("\n", k)
    return s[:j + 1] + f'  "{sha}": "4486 + SC23.5: SC23.4 + cabezal del song pointer desde el tick, pad 8 = bypass, K8 de drums bipolar, Clear en las dos capas, limite de ritmo + latido + refresco de los mensajes del DSP, LED del boton Save (prueba)",\n' + s[j + 1:]


rw("tools/ct_uploader.html", known)
rw("tools/verify_builds.py", lambda s: s.replace('    ("sc23.4", "build_sc23_4.py", []),\n', '    ("sc23.4", "build_sc23_4.py", []),\n    ("sc23.5", "build_sc23_5.py", []),\n'))
for f in ("tools/emu_sc17.py", "tools/emu_sc17_8.py", "tools/emu_sc19.py", "tools/emu_sc20_1.py"):
    rw(f, lambda s: s.replace('"SC23.3", "SC23.4")', '"SC23.3", "SC23.4", "SC23.5")'))


def rt(s):
    s = s.replace("F234=firmware/sc23.4\n", "F234=firmware/sc23.4\nF235=firmware/sc23.5\n")
    k = 'run python3 tools/emu_sc23_4_notes.py "$F234/circuittracks-4486-SC23.4.bin" "$F234/manifest.json"\n'
    add = ('run python3 tools/emu_sc23_3.py "$IMG9" "$F235/circuittracks-4486-SC23.5.bin" "$MAN9" "$F235/manifest.json"\n'
           'run python3 tools/emu_sc23_3_fx.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"\n'
           'run python3 tools/emu_sc23_4_notes.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"\n'
           'run python3 tools/emu_sc23_5.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"\n'
           'run python3 tools/emu_sc23_5_gfx.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"\n'
           'run python3 tools/emu_sc23_5_drums.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"\n'
           'run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F235/circuittracks-4486-SC23.5.bin" "$MAN9" "$F235/manifest.json"\n'
           'run python3 tools/emu_sc23_5_dsp.py "$F235/circuittracks-4486-SC23.5.bin" "$F235/manifest.json"\n')
    return s.replace(k, k + add)


rw("tools/run_tests.sh", rt)
rw("README.md", lambda s: s[:s.index("| SC23.4 |")] + "| SC23.5 | SC23.4 + **correcciones tras probar**: el LED del song pointer sigue los 16 pasos en blanco (lo calcula el gancho del tick), pad 8 igual que el bypass de FX, K8 de drums con brillo mínimo sin efecto y creciente hacia el bitcrush o la distorsión, **Clear + knob borra las dos capas** (VCA-VCF, OSC y drums), **mensajes al DSP como mucho uno cada 2 ms por voz, latido de ACT / NOTE / VEL / GATE, refresco de todos los valores cada ~1 s** y la envolvente arranca con la puerta alta aunque se pierda el disparo (notas que no siempre sonaban), el botón **Save** de la fila superior parpadea en el paso guardar | ⏳ pendiente de probar |\n" + s[s.index("| SC23.4 |"):])


def rc(s):
    i = s.index("- **SC23.4** (`firmware/sc23.4/`")
    new = ("- **SC23.5** (`firmware/sc23.5/`, pendiente de probar) = SC23.4 + (opciones): `build_sc17.use_spcache()` (el gancho del tick `c_sptick` guarda en la palabra T0 del conjunto 2 `S_SPS` = (reloj HAL / 64) << 8 | paso; `c_spcur` lo lee y apaga el cabezal si lleva > 2 s; `SP_HEAD` = blanco `0x01`), `use_clear_copy()` (`CLR_COPY`: pad 8 = copia de la entrada 24 de la vista FX), `persist19.K8_BRIGHT` (K8 plano = max(distorsión, bitcrush) como brillo), `persist19.CLEAR_BOTH` + `vcf21.use_clearboth()` (Clear + knob = las dos capas: `c_dzero`, `c_vclr1`; con Shift el botón Clear no hace nada), `vcf21.use_ratelimit()` (`c_vsend`: como mucho un mensaje por voz cada 2 ms; sello de 5 bits en los bits 3-7 de `RT_TAG`, que sigue al reloj mientras no hay nada que enviar) + `vcf21.use_heartbeat()` (`sd_hb`: cada ~8 ms marca ACT / NOTE / VEL / GATE de nuevo, cada ~1 s todos los valores con el modo encendido; velocidad inicial 100) + `vcf21_dsp.use_gatefix()` (puerta alta con la envolvente parada la arranca), `vcf21.use_saveled()` (LED 57 del panel = botón Save). Pruebas `emu_sc23_5*.py`. **Motivo:** con los defaults neutros un mensaje perdido deja el VCA cerrado.\n")
    return s[:i] + new + s[i:]


rw("CLAUDE.md", rc)


def rn(s):
    i = s.index("### SC23.4 = SC23.3 + ")
    t = ("### SC23.5 = SC23.4 + **cabezal del song pointer, pad 8, K8, Clear en las dos capas, notas que no siempre sonaban, botón Save** — ⏳ pendiente de probar\n"
         "- Informes del usuario sobre SC23.3 / SC23.4 (2026-10-06): (1) iluminar también el botón **Save** de la fila superior (entre Duplicate y Projects) en el paso guardar; (2) pad 8 de Master FX «en blanco fijo (ahora parpadea)», igual que el bypass de FX (pad 25) de la vista FX; (3) el song pointer debe seguir el compás de 1 a 16 linealmente («la información está bien, solo hay que encender el pad»); (4) brillo de K8 de drums: mínimo en el centro (sin efecto), creciente hacia la izquierda (bitcrush) o la derecha (distorsión); (5) el modo VCA-VCF / OSC «funciona ahora» pero las notas no siempre se disparan; (6) con Shift el botón Clear pierde su función: el clear de la capa Shift se hace a la vez que el de la capa sin Shift.\n"
         "- **LED del botón Save:** LED 57 del panel (tabla `0x08059438`: entrada 57 = fuente 5, elemento 0, justo detrás de Duplicate = 56); parpadea con el pad Save (`HAL_TICK >> 8`) en el paso guardar.\n"
         "- **Pad 8:** los códigos `0x19` / `0x46` (aspecto «FX off») no son fijos: la tarea de LEDs (`0x08033E1A(ctrl, x, ctrl-time)`) indexa una tabla de 96 pasos con un contador (`r4 = tiempo − base`, `< 0x60`): hay códigos que **laten**. Ahora el pad 8 copia la entrada 24 (pad 25 de la vista FX) en cada refresco.\n"
         "- **Cabezal:** el gancho del tick (`c_sptick`, el mismo que hace el bucle y el salto, que el usuario da por bueno) calcula `(ticks + 1) / 6 mod 16` y lo guarda con la hora; la rutina de LEDs ya no lee el almacén del motor ni el del transporte (`0x20011034`). Visible mientras el último tick sea de hace < 2 s; sello de 24 bits (no «rebota» a fresco). Blanco (`0x01`), como el paso que suena de las vistas de paso de stock. El LED se vuelve a calcular en cada sondeo: la tarea de LEDs (0x08033E1A) se llama periódicamente con un contador, no por eventos.\n"
         "- **K8 de drums** (`persist19.K8_BRIGHT`): el LED plano de K8 deja de ser el código dinámico de stock y lleva (max(distorsión macro 2, nibble de bitcrush × 8 + nibble / 2) + 2) << 8 | color del drum. **Los demás knobs bidireccionales (K1 pitch, K5 EQ, K3) siguen con el LED de stock; por aclarar cuáles quiere el usuario con el mismo criterio.**\n"
         "- **Clear en las dos capas:** VCA-VCF / OSC (`vcf21.use_clearboth`: `c_vclr1` resetea la posición de la tabla `k` y `k + 8` de la página mostrada) y drums (`persist19.CLEAR_BOTH`: con Clear pulsado y un knob sin Shift se pone a 0 el código de la capa Shift de ese knob: pitch env, ring mod amount, env shape, modo de filtro, velocidad del LFO y tipo de distorsión). Pruebas: `emu_sc23_5.py`, `emu_sc23_5_drums.py`.\n"
         "- **Notas que no siempre sonaban:** hipótesis (no demostrada en el aparato): el DSP lee el buzón de cada voz **una vez por bloque de audio** y solo ve la **última palabra escrita**; con una marca de 1 bit, un número par de escrituras entre dos lecturas **no se nota** (la marca vuelve a ser igual a la anterior) y se pierden las dos. El servicio puede ir más deprisa que los bloques y un golpe de nota son 4 mensajes (el encendido del modo, 28), así que se perdían al azar: valores del oscilador que nunca llegaban (el sonido «errático») y puertas que no abrían (con los defaults neutros un VCA sin puerta no suena). Remedios, todos con opción: `vcf21.use_ratelimit()` (como mucho **un mensaje por voz cada 2 ms**, `RATE_MS`; sello de 5 bits en `RT_TAG` bits 3-7 que sigue al reloj mientras no hay nada que enviar, para que 32 ms de calma no den la vuelta a «ahora mismo»), `vcf21.use_heartbeat()` (cada ~8 ms una de las cuatro marcas ACT / NOTE / VEL / GATE de nuevo, cada ~1 s **todos los valores** con el modo encendido; velocidad inicial 100) y `vcf21_dsp.use_gatefix()` (puerta alta + envolvente parada = disparo). **Si el fallo persiste, subir `RATE_MS` (hasta 16) o la causa es otra** (la cadencia de bloques frente a ticks no está medida). Pruebas: `emu_sc23_5.py` (huecos de ≥ 2 ms con ticks de 1 ms, encendido completo en ~150 ms, refresco, sello sin vuelta).\n"
         f"- Marca `SC23.5`, `firmware/sc23.5/` ({size} B), SHA-256 `{sha}`. Reserva SC23.4.\n\n")
    return s[:i] + t + s[i:]


rw("docs/NOTAS.md", rn)
