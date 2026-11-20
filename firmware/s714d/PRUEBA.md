# S714D (marca `S714D`) — diagnóstico, sin publicar

= Alpha 7.14 + `tools/patscan.py` + `blackbox.use_memrd()`. Imagen `0x6fe3c`.

**Qué busca:** quién deja un valor imposible en un patrón (probabilidad de un paso > 7, máscara de unidades con los bits 6-7, velocity de una unidad > 127, velocity de un drum > 127: los valores de los cuelgues de las 5.63 / 5.64, que `paintguard` se salta). Cada fotograma de LEDs revisa un patrón (los 64 en ≈ 1 s); al primero que encuentra, **congela la caja negra** (estado `0x85`, Save violeta) con la etiqueta 3, el valor, su dirección y **los 12 últimos mensajes MIDI de entrada** (anillo propio en la entrada MIDI). `bbread.py --mem` lee la RAM en marcha.

## Probar
1. Usar el aparato como siempre, con cadenas, escenas, mutate, saltos, grabación; y `python tools/midistress_dev.py 600 200` (MIDI al azar desde el PC: CC, NRPN, notas, pitch bend; para al congelarse y enseña el registro).
2. Si Save se pone violeta: no apagar; leer con `python tools/bbread.py --firmware S714D` (o el script de arriba).

Prueba `emu_patscan.py`.
