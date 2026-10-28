# RC4 / RC4S = SC48.6 con el nombre de la versión candidata 4

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/rc4/circuittracks-4486-RC4.syx` (**RC4**) | `23a9c2a366994aa3ddb44e96ed26d77e94bf6adbf3c8c8b54910196bac516eb2` | `RC4` |
| `firmware/rc4s/circuittracks-4486-RC4S.syx` (**RC4S** = sin escrituras propias en la SD) | `311862c48aea09da40ab05bfe383218a92f66459742ee7e8a015e8438207f94b` | `RC4S` |

El usuario (2026-10-28), tras probar SC48.6 en el aparato: «Works good, make public», «Make this version RC4. Explain in the manual the expected
behavior of the custom voices (voice limiting, Max polyphony...)».

**RC4** = SC48.6 (la imagen solo cambia en la marca) = RC2.11 + todo lo de las betas hasta la 3.43 (la Beta 3.43 no se publicó aparte).
**RC4S** = RC4 + `rodisk.use_allpacks()`: nada del mod escribe ni borra ficheros en la SD ni en la memoria interna (las funciones que escriben
fallan con el LED de Save rojo; los guardados del original pasan).

## Qué probar
Lo de `firmware/sc48.6/PRUEBA.md` (Synth 1 / 2 con un acorde poly del sinte propio) y, en general, lo marcado «desde RC4» en la guía. El
comportamiento de las voces del sinte propio (cuántas por modo y motor, el volumen de los acordes, el límite de voces y Synth 1 / 2) está en la
guía, «Voces del sinte propio» (`guia.html#midi-voces`).

## Verificación en emulación
- `emu_vguard.py` sobre RC4: lo de SC48.6 (todo bien). `emu_rodisk.py` sobre RC4S frente a SC41.2: todo rechazado en todos los packs (bien).
- `verify_builds.py`: ALL IDENTICAL.
