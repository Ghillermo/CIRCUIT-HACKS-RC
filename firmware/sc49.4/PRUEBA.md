# SC49.4 = SC49.3 sin el Vinyl que quedaba ni el modo comb de los drums

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc49.4/circuittracks-4486-SC49.4.syx` | `ce59641d54e0aa6d2ec768375770bc2e299d049af672be31dfd8d8b97fb749eb` | `SC49.4` |

El usuario (2026-10-29): «Vinyl leftovers», «Drum comb filter mode» (sitio para la fase 2 del carril extra). Sin beta (va en la siguiente con la
fase 2). Imagen `0x6F8FC`: **1 796 B libres** al final (SC49.3: 920 B), la zona libre igual (314 B); el programa del núcleo 0 del DSP termina en
`P:$3ECB` (**309 palabras libres**, antes 12).

## Qué cambia
- **El Vinyl** (descartado en SC39.7): su rutina del DSP seguía corriendo en cada bloque con algún efecto de Master FX encendido, y su rama de
  apagado ponía a cero `X:VN_ST..+3`, donde desde SC39.9 **Digitise guarda la hora de inicio de su envolvente (K4)**: con Digitise encendido la
  envolvente no llegaba a funcionar (la hora se borraba en el bloque siguiente). Fuera la rutina y su llamada (`masterfx_dsp.use_novinyl()`):
  **el K4 de Digitise vuelve a funcionar**. Este arreglo también afecta a RC4 (la RC lleva Digitise con K4).
- **El modo comb de los drums** (Shift + K5): fuera (`drums2_dsp.use_nocomb()`, `persist19.use_nocomb()`); Shift + K5 pasa por EQ tilt, paso
  banda, notch y DJ; un proyecto guardado con el comb suena con el EQ tilt (el DSP toma el modo 3 como el 4).

## Qué probar
1. Master FX, Digitise (pad 4) con K4 a la derecha: al encenderlo empieza entero y se va limpiando; a la izquierda, al revés.
2. Los demás efectos de Master FX suenan como antes.
3. Un drum, Shift + K5: cuatro modos (su color en el LED); los filtros suenan como antes. Un proyecto con un drum en comb: suena con el EQ tilt.

## Verificación en emulación
`emu_drop494_dsp.py` frente a SC49.3: drums sin filtro / LP / HP / paso banda / notch / ring mod / trémolo idénticos, el modo 3 del buzón = 4,
Master FX con Digitise idéntico y `X:VN_ST..+3` conservados (SC49.3 los ponía a cero). `emu_nocomb.py`: Shift + K5 = 0, 1, 2, 4.
