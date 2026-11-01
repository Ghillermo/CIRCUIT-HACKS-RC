# RC4.04 / RC4.04S = RC4.03 / RC4.03S + el Nudge nuevo + Record solo en la pista de la vista

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/r404/circuittracks-4486-R404.syx` | `b94f5b74438c35cf48b81fbd8cbb9324957dc7933d57dc0cd2e6fa0a7f2d11f2` | `R404` |
| `firmware/r404s/circuittracks-4486-R404S.syx` | `90da7a75c839a76fbdc4b38b5c784c7ce5cf1c97d83c8b1421df545461875655` | `R404S` |

RC4.03 / RC4.03S no se publicaron: estas las incluyen (el guardado diferido como interruptor).

El usuario (2026-11-01): «el nudge sólo cambia inicio y fin, pero no arrastra el contenido de los pasos»; «sería mejor mover el contenido sin arrastrar el puntero de principio y fin».

## Qué cambia
- **Pad 26 de Pattern Settings** = el contenido del tramo (primer a último paso) un paso atrás; **Shift + pad 26** = un paso adelante. Lo que sale por un extremo del tramo entra por el otro. El primer y el último paso no se mueven.
- La vista lo enseña al momento, sin Play, en notas y drums (antes rotaba en memoria y la vista no se enteraba).

## Qué probar
1. MIDI 1 o Synth 1: notas en los pasos 7, 8 y 10, tramo 7-13. Pattern Settings, pad 26. Vuelve a la vista Note, sin Play: notas en 7, 9 y 13; el tramo sigue en 7-13.
2. Pad 26 otra vez: 8, 12 y 13. Shift + pad 26: vuelve a 7, 9 y 13.
3. Con la automatización de un knob en un paso: viaja con el paso.
4. Drum 1, lo mismo; después edita un paso (probabilidad o velocity): lo movido sigue ahí.
5. Sonando: el patrón suena con el contenido movido y sin saltos de tramo.

## Pruebas en emulación
`emu_nudge2.py` (R404, R404S, SC50, B5.3), con la vista Note de MIDI 1 y de Drum 1; `verify_builds.py`.
