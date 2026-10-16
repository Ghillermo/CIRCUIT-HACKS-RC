# R0901S = RC0.9S + el filtro por defecto de los drums = el EQ de stock

`circuittracks-4486-R0901S.syx` — SHA-256 `fc851f4a44cc4f456ca1ae5a52f156a600436582402a541064d4d827bbff8e0f`, marca `R0901S`.
Es **RC0.9.1S** (ficheros y marca `R0901S`).

**El filtro por defecto de los drums es el EQ de stock.** El modo de filtro (Shift + K5) se guarda como un valor 0-4 y el 0, el que tiene todo proyecto nuevo o que nunca lo tocó, era nuestro filtro DJ, que además anulaba el EQ tilt de stock: K5 no hacía lo mismo que en un Circuit original y el sonido podía cambiar. Ahora el 0 es el EQ de stock (exactamente el del original, sin resonancia, que no se aplica en ese modo) y el filtro DJ pasa al 4; paso banda, notch y comb siguen en 1, 2 y 3. Orden con Shift + K5: EQ de stock → paso banda → notch → comb → DJ. Un proyecto guardado con el DJ elegido a propósito sonará con el EQ de stock (no se distingue del valor por defecto); uno guardado con «EQ tilt» elegido sonará con el DJ.

**Revisado, sin cambios:** con todo a cero, los demás parámetros nuevos de los drums no tocan el sonido (envolvente de tono y de filtro, ring mod, LFO, resonancia, forma de la envolvente, bitcrush, start point, tipo de distorsión = el de stock).

## Qué probar
1. Proyecto nuevo, un drum con un sample conocido: K5 (Filter frequency) se comporta como en el Circuit original (EQ tilt) y el sonido es el mismo.
2. Shift + K5: el LED pasa por verde (EQ de stock), amarillo (paso banda), magenta (notch), violeta (comb), blanco (DJ) (Beta 1.4; en la RC el brillo).
3. Un proyecto antiguo que nunca tocó el modo de filtro: ahora suena como en el original.

## Verificación en emulación
`emu_fsel.py`: para los valores guardados 0-4 de un drum, el servicio del DSP manda los modos 4, 1, 2, 3, 0 (la versión anterior: 0, 1, 2, 3, 4).
