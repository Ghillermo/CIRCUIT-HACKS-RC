# Beta 5.64 = Beta 5.63 + el mute del secuenciador de efectos + el arreglo del cuelgue de las cadenas

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.64/circuittracks-4486-B5.64.syx` | `ef104bf687323c0c022cb5857fae2b0338d82354de4a4f761ebf5d5d6339d288` | `B5.64` |

= SC57.9 con la marca de la beta. Incluye la Beta 5.63 (sin publicar). Detalle en `docs/NOTAS.md` («SC57.9 / Beta 5.64») y en `docs/CHANGELOG.md`.

**El cuelgue de la 5.63** (reinicio al crear una cadena de grupos para una escena nueva): el código de la ranura 7 de la vista Note de drums (los
rollers / los cuadros duplicados) ya no toca nada cuando lo llaman con un objeto que no es esa vista. **La causa de fondo (un byte que cambia en
la barra de velocity de Drum 4) sigue sin encontrarse:** si el aparato vuelve a hacer algo raro con las cadenas, instala **S579D** (`firmware/s579d/`)
y repite lo que hacías: congela la caja negra en el momento del cambio; léela con la app (Caja negra…) y pásala.

## Qué probar
1. **Lo que se colgaba:** en la vista Patterns, modo cadena (Shift + Octave ▲), Shift + un pad dos veces, Shift + otro pad dos veces, salir de la
   vista; también después de guardar una escena nueva en el Mixer (Shift + pad de escena) y con el transporte parado unos segundos: sin reinicio
   (la 5.63 se reiniciaba 1,4 s después de salir). Si pasa algo, la caja negra (app) dirá qué.
2. **Mute del secuenciador de efectos:** MIDI 1 con «sin voz» (fila de motores) y el pad 31 encendido (secuenciador de efectos), la vista del
   step-drummer (pad 30), notas en algunos pasos; girar el knob de un par hasta el final (pasado el blanco del «al azar»): **LED rojo**; con Play, en
   esos pasos **todo el master se calla** (con un fundido corto), y vuelve al salir del paso. La captura de Master FX sigue grabando con sonido y el
   metrónomo (Shift + Clear) se oye.
3. Las vistas Note de los drums como siempre: los rollers (filas 1-3), los cuadros 25-28 copiando los 29-32, los pads de los drums.
4. **Secuenciador de saltos:** MIDI 1 apuntando a Synth 1 (fila de motores, pads 9-16) sigue saltando igual; nada cambia con un proyecto normal.
5. Lo de la Beta 5.63 (`firmware/b5.63/PRUEBA.md`), si no se probó.

## Verificación en emulación
`emu_vtguard.py` (los objetos falsos, la confirmación real con el estado del registro, la ruta legítima de la vista; `--expect-fault` sobre la 5.63
reproduce el fallo), `emu_fsqmute.py` / `emu_fsqmute_dsp.py` (el mute), las de la 5.63 sobre esta imagen (`emu_pgroups`, `emu_scnchain`,
`emu_jumpfix`, `emu_xlanes`); `verify_builds.py` → ALL IDENTICAL. Resultados en `docs/NOTAS.md` («Beta 5.64»).
