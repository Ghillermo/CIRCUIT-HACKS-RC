# SC55.3 / Beta 5.38 — patches por categoría, la tarjeta leída solo cuando hace falta

Vista Preset de Synth 1 / 2:
- Cada patch en el color de su **categoría** (la que pone Components): Arp verde azulado, Bass rojo, Bell azul claro, Classic ámbar,
  Drum naranja, Keyboard crema, Lead amarillo, Movement lavanda, Pad azul, Poly verde, SFX rosa, String melocotón, User arena,
  Voc azul violeta. **None** = el color de la pista. **Hueco vacío** = blanco tenue. El patch elegido en blanco (como el original).
- La tarjeta se lee al entrar en la vista, al cambiar de página y tras guardar (Clear / Duplicate), nunca en el segundo que sigue a tocar un pad.
- **Guardar con categoría:** Clear + pad (el hueco parpadea): los knobs se apagan salvo K1, que va en el color de la categoría; girar K1 la cambia
  (4 clics por categoría; el hueco parpadea en ese color). Clear + el mismo pad: se guarda con esa categoría.

Prueba:
1. Tocar patches deprisa y despacio, parado y con Play: siempre carga el patch tocado (nunca el inicial); ningún pad parpadea.
2. Los colores coinciden con las categorías de Components; los huecos vacíos se distinguen de los None.
3. Guardar un patch eligiendo otra categoría con K1: tras guardar, el pad sale en ese color (y Components lo ve con esa categoría).
4. Lo mismo en Synth 2. Cambiar de página y de pack: los colores de cada uno.
