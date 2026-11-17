# Beta 5.64 / SC57.9, RC4.15 / RC4.15S, S579D — verificación en emulación (2026-11-15)

Todas las pruebas sobre las imágenes construidas en `firmware/b5.64`, `firmware/sc57.9`, `firmware/r415`, `firmware/r415s`, `firmware/s579d`
(Unicorn; la RAM del arranque emulado). «Anterior» = la imagen con la que se compara.

| Prueba | Imagen | Anterior | Resultado |
|---|---|---|---|
| `emu_vtguard.py` (la ranura 7 con objetos ajenos: `[this + 4]` legible e ilegible, la confirmación real del almacén `0x2003bd90` con el estado del registro, la ruta legítima de la vista Note de drums bit a bit) | B5.64 | — | ALL PASS (la vista: búfer `543f681c5e6b371c`, el mismo que la 5.63) |
| `emu_vtguard.py` | R415 (los dos guardias) | — | ALL PASS |
| `emu_vtguard.py --expect-fault` (control positivo: el fallo del registro) | B5.63 | — | ALL PASS (falla en `c_nvl + 6` con r0 `0x1f020520`, como el aparato) |
| `emu_fsqmute_dsp.py` (el `mut` del DSP contra un modelo bit a bit) | núcleo 0 + el código | — | ALL PASS (9) |
| `emu_fsqmute.py` (el octavo valor: bits, `c_fxtick` real, LED rojo, la nota fuera del paso) | B5.64 | B5.63 | ALL PASS (7) |
| `emu_pgroups.py` (cadenas de grupos) | B5.64 | — | ALL PASS |
| `emu_scnchain.py` (cadenas por escena) | B5.64 | — | la misma tupla que la 5.63 |
| `emu_jumpfix.py` (los arreglos del step flip de la 5.63) | B5.64 | — | ALL PASS (10) |
| `emu_xlanes.py` (carriles extra) | B5.64 | — | ALL PASS (33) |
| `emu_cwatch.py` (S579D: nada con los objetos intactos, el fotograma de la 5.63, la corrupción congela una vez, la caja ya congelada) | S579D | B5.63 | ALL PASS (7) |
| `emu_arptime.py --ext` | R415 | — | ALL PASS (3) |
| `emu_nudge2.py` (playmode: el recorte de `c_pmnudge`) | R415 | — | ALL PASS (7) |
| `emu_edscratch.py` (vcf21: el recorte del editor v1) | R415 | — | ALL PASS (4) |
| `emu_rodisk.py` (packio: el recorte de `c_xswap`) | R415 | SC41.2 | ALL PASS (5) |
| `emu_capkeep.py` | R415 | R411 | ALL PASS (9; con R414 de anterior las 2 comprobaciones de «la anterior» no valen: R414 ya lleva capkeep) |
| `emu_fsel.py` (drums18: el recorte de `c_dk18`) | R415 | SC41.3 | ALL PASS (con R414 de anterior no vale: ya lleva `use_fselstock`) |
| `verify_builds.py` (todas las builds registradas, bit a bit) | — | — | pendiente |

Pruebas que no valen aquí: `emu_fm8.py` y `emu_jumpseq.py` (desde SC56.3 / SC57.3 fallan igual en todas las betas, por diseño).
