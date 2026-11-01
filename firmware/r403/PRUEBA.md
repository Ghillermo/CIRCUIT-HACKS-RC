# RC4.03 / RC4.03S = RC4.02 / RC4.02S + el guardado diferido como interruptor

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/r403/circuittracks-4486-R403.syx` | `212f2d414f0a9c4d1638ef590f7fb15f44073f15e0240afe17acff30575e23d0` | `R403` |
| `firmware/r403s/circuittracks-4486-R403S.syx` | `114ff29dbeb39aa9c967e41347bb15224f6bba132714003f65a35e68350b8472` | `R403S` |

## Qué cambia
- **Guardado diferido como interruptor** (`savedefer.use_toggle()`; el usuario, 2026-10-30: «Make the delayed save a toggle in advanced setup (stock save
  by default)»): **Advanced Setup, pad 22** (verde encendido, tenue apagado; bit 3 de las banderas de gmdrum, en los ajustes). Apagado, de fábrica, Save
  guarda al momento como el original. Encendido, como RC4.02.
- Imágenes `0X6FF14` / `0X6FF04` (236 / 252 B libres); DSP sin cambios.

## Qué probar
1. Play, Save dos veces: guarda al momento, como el original.
2. Advanced Setup, pad 22 verde: Play, Save dos veces: Save parpadea en amarillo y guarda al parar. Reiniciar: sigue verde.

## Verificación en emulación
`emu_savedefer.py` sobre R403.
