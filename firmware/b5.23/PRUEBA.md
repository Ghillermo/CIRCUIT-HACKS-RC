# Beta 5.23 = SC52 con la marca de la beta (incluye las 5.17-5.22)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.23/circuittracks-4486-B5.23.syx` | `19f30921883c1aa718185c114f05cbd5438a437975acabad685aa2bd0c2fb3e6` | `B5.23` |

**Qué cambia** respecto a la 5.22 (el usuario, 2026-11-05): «restore row 3 … on operator selection view» → «Engine mode (osc, fm, granular....)»: **en la página FM (fila de motores cerrada), los pads 17-24 = la fila de motores** (sin voz, VCA / VCF / FX, oscilador, VA-drum, wavetable apagado, muestra, granular, FM brillante); un toque cambia de motor (el FM se apaga con cualquiera menos el 24). Y «pad 7 stays lit after I choose my algorithm, make it dim after selection/not pressed»: **el pad 7 brillante solo mientras lo mantienes**, tenue el resto del tiempo.

**Usar con una copia de la tarjeta.**

## Qué probar
1. MIDI 1 con FM, página FM: pads 17-24 = la fila de motores, el 24 (FM) brillante; pads 9-16 los operadores, el pad 3 la envolvente de pitch.
2. Toca el pad 19 (oscilador): el FM se apaga, suena el oscilador. Vuelve con pad 27 → pad 24.
3. Pad 7: mantenido brillante con los algoritmos; al soltarlo, tenue.
4. Lo de la 5.22 / 5.21.

## Verificación en emulación
`emu_fm8.py`, `emu_fm8v2.py`: ALL PASS.
