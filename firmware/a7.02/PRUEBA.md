# Alpha 7.02 = Alpha 7.01 + los datos de cada patrón siguen al patrón que suena (cadenas y pattern mutate)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/a7.02/circuittracks-4486-A7.02.syx` | `2fbc20650d617b3aa5ccd626aa80de09e7a77c48cf01b7736b2de77674abdea1` | `A7.02` |

El usuario (2026-11-17): «Make pattern related data, like lanex, follows the current pattern at play, even with pattern chain and pattern mutate».
La auditoría previa (`tools/bytewatch.py`: un gancho de escritura sobre los patrones durante 27 pruebas de emulación) no encontró ningún código
nuestro que deje una probabilidad > 7 o una velocity > 127 en un paso. Lo que no seguía al patrón:

- **Frecuencia de los drums («1 de cada N»)** (`drumpat.use_patpass()`): contaba las pasadas por drum y volvía a 0 en cada cambio de patrón; con
  una cadena A → B → A (o una lista de pattern mutate), «1 de cada 2» en A sonaba en cada visita. Ahora cada patrón cuenta las suyas, como en las
  pistas de notas (RAM `0x2004FB40`, 64 B, a cero con el transporte parado; el borrado en `tools/patpass.py`, segundo hueco de `dspz`).
- **Carriles extra de MIDI 1 / 2** (`xlanes.use_late()`): el bloque de un patrón que acaba de empezar se lee del DSP en la tarea de LEDs (decenas
  de ms) y sus valores no sonaban hasta el medio paso siguiente. Ahora, al terminar la lectura, el micropaso siguiente toca el medio paso que se
  perdió (≈ un micropaso tarde; RAM `0x2004FB80`, 2 B).
- **Carril extra de los drums** (`lanex.use_patmask()`): el patrón que suena se toma & 7 (nunca el patrón de otro drum).

Sitio: imagen `0x6FFF8` (8 B libres), hueco 0 de `dspz` 13 B, hueco 1 3 B, hole 14 B.

## Qué probar
1. Drums: dos patrones con un golpe a «1 de cada 2» (vista de probabilidad, modo 1, fila 4) y una cadena A → B → A → B: A suena en su 2.ª y 4.ª
   visita, B igual; parar y volver a empezar: desde la 1.ª.
2. MIDI 1 / 2 con el sinte propio: carriles extra grabados en dos patrones encadenados: los valores del patrón nuevo desde su primer paso.
3. Lo de la Alpha 7.01 (Save violeta / caja negra) sigue igual.

Verificación en emulación: `emu_patfollow.py` (ALL PASS contra la Alpha 7.01).
