# SC41.4 = SC41.3 + el filtro por defecto de los drums = el EQ de stock

`circuittracks-4486-SC41.4.syx` — SHA-256 `1a15100f81d65fdca55d36b8373dc42b8e138be3fa3b742a5f257f5bef8a324d`, marca `SC41.4`.
`firmware/b1.4/circuittracks-4486-B1.4.syx` — SHA-256 `51baccb54d6758ae3e6f063da94e63d9900ba43515ef4d8eff34d036245f6627`: el mismo código con la marca `B1.4` (**Beta 1.4**).

**El filtro por defecto de los drums es el EQ de stock.** El modo de filtro (Shift + K5) se guarda como un valor 0-4 y el 0, el que tiene todo proyecto nuevo o que nunca lo tocó, era nuestro filtro DJ, que además anulaba el EQ tilt de stock: K5 no hacía lo mismo que en un Circuit original y el sonido podía cambiar. Ahora el 0 es el EQ de stock (exactamente el del original, sin resonancia, que no se aplica en ese modo) y el filtro DJ pasa al 4; paso banda, notch y comb siguen en 1, 2 y 3. Orden con Shift + K5: EQ de stock → paso banda → notch → comb → DJ. Un proyecto guardado con el DJ elegido a propósito sonará con el EQ de stock (no se distingue del valor por defecto); uno guardado con «EQ tilt» elegido sonará con el DJ.

**Revisado, sin cambios:** con todo a cero, los demás parámetros nuevos de los drums no tocan el sonido (envolvente de tono y de filtro, ring mod, LFO, resonancia, forma de la envolvente, bitcrush, start point, tipo de distorsión = el de stock).

## Qué probar
1. Proyecto nuevo, un drum con un sample conocido: K5 (Filter frequency) se comporta como en el Circuit original (EQ tilt) y el sonido es el mismo.
2. Shift + K5: el LED pasa por verde (EQ de stock), amarillo (paso banda), magenta (notch), violeta (comb), blanco (DJ) (Beta 1.4; en la RC el brillo).
3. Un proyecto antiguo que nunca tocó el modo de filtro: ahora suena como en el original.

## Verificación en emulación
`emu_fsel.py`: para los valores guardados 0-4 de un drum, el servicio del DSP manda los modos 4, 1, 2, 3, 0 (la versión anterior: 0, 1, 2, 3, 4).
