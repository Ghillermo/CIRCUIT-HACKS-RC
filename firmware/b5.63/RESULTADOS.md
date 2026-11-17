# Beta 5.63 / SC57.8 / RC4.14 / RC4.14S — resultados en emulación (2026-11-14)

Las pruebas de `docs/NOTAS.md` («RC4.14 / RC4.14S, SC57.8 / Beta 5.63»), corridas sobre las imágenes de `firmware/`. El aparato no se ha probado.

| Prueba | Qué comprueba | Resultado | Nota |
|---|---|---|---|
| `emu_xlfix.py B5.63` | XL-1 / 3 / 4 / 5 / 6: 14 casos de los carriles extra | ✅ pasa (15) |  |
| `emu_xlanes.py B5.63` | los carriles extra enteros (33 comprobaciones, la convención real del guardado) | ✅ pasa (33) |  |
| `emu_scsave.py firmware/b5.63` | SCR-1: el guardado de stock y la API real de la tarjeta (emu_sdsysex) | ✅ pasa (7) |  |
| `emu_scnclear.py firmware/b5.63` | SCR-3: Clear + escena por el controlador | ✅ pasa (7) |  |
| `emu_pgroups.py firmware/b5.63` | las cadenas de grupos (30) | ✅ pasa (30) |  |
| `emu_scnchain.py firmware/b5.63` | las cadenas por escena (sin veredicto propio: la salida igual que en 5.62) | ? firmware/b5.63 ([(0, '0001', '0001'), (1, '0203', '0203'), ( | imprime los recorridos; idénticos a los de la 5.62 |
| `emu_p4free.py B5.63` | JR-1 / JR-2: el hueco liberado | ✅ pasa (14) |  |
| `emu_jumpfix.py B5.63` | JR-4 / 5 / 6 / 7, XC-3: el step flip | ✅ pasa (10) | la primera pasada falló JR-7 (a) por el arnés: la cadena del volcado lleva Synth 1 al patrón 1 en la primera vuelta y el ritmo lento volvía al de fábrica; ahora el arnés escribe el sync rate en los 8 patrones |
| `emu_jumpseq.py B5.63` | el secuenciador de saltos (SC50.2) | ❌ 30 fallos (29 ok) | 29 ok / 30 fallos, los mismos en la 5.62 y en la 5.56: la prueba es anterior a la vista de flip de SC52.9 (pad 26, fila 3); lo vigente es `emu_jumpfix.py` |
| `emu_jumprnd.py B5.63 / B5.62` | el salto al azar (SC57.2) | ✅ pasa (3) | la prueba espera como «anterior» una build sin jumprnd (la 5.56); contra la 5.62 su tercera comprobación falla por diseño |
| `emu_arptime.py --ext B5.63` | ARP-1: esclavo a 150 / 96 BPM, no esclavo con un reloj medido | ✅ pasa (3) |  |
| `emu_arptime.py B5.63 / B5.60` | el arpegio a tiempo (RC4.12) | ✅ pasa (7) |  |
| `emu_capkeep.py B5.63 / B5.60` | CK-1 y la captura que sigue (RC4.12) | ✅ pasa (9) |  |
| `emu_patrev.py B5.63` | Clear + Duplicate dos veces (patrev en el hueco 0; la caché rellenada) | ✅ pasa (26) |  |
| `emu_tabpack.py B5.63 / B5.62` | las tablas rehechas al encender = las de la flash de la 5.62 (exp / inc / bexp incluidas) | ✅ pasa (7) |  |
| `emu_examples.py B5.63` | los 81 patches de ejemplo (678) | ✅ pasa (678) |  |
| `emu_fm8.py B5.63` | el FM de 8 operadores (prueba de SC51.7) | ❌ 2 fallos (18 ok) | las 2 que fallan (Clear + pad 7 = la voz del algoritmo; pad 8 + pad 12 = un instrumento) fallan igual en la 5.62: son gestos anteriores a SC56.3 / SC57.3 (`fm8ui.use_noinst`), no la 5.63 |
| `emu_fm8poly.py B5.63` |  | ✅ pasa (10) |  |
| `emu_fm8store.py B5.63` |  | ✅ pasa (19) |  |
| `emu_dx7imp.py B5.63` |  | ✅ pasa (4) |  |
| `emu_p4dup.py B5.63` |  | ✅ pasa (10) |  |
| `emu_dspz.py B5.62 / B5.63` | los mismos bytes al DSP | ✅ pasa (12) |  |
| `emu_arptime.py --ext R414` |  | ✅ pasa (3) |  |
| `emu_arptime.py R414 / R411` |  | ✅ pasa (7) |  |
| `emu_capkeep.py R414 / R411` |  | ✅ pasa (9) |  |
| `emu_arptime.py --ext R414S` |  | ✅ pasa (3) |  |
| `emu_arptime.py R414S / R411S` |  | ✅ pasa (7) |  |
| `emu_capkeep.py R414S / R411S` |  | ✅ pasa (9) |  |

`verify_builds.py` (todas las versiones anteriores reconstruidas): **ALL IDENTICAL**.
