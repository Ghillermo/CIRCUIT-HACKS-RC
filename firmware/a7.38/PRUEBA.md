# Alpha 7.38 — qué probar

Instalar `circuittracks-4486-A7.38.syx` (modo bootloader: Scales + Preset + Note al encender). **Sin funciones nuevas**: es la Alpha 7.37 con dos cambios por dentro.

1. **El modo de prueba de fábrica ya no existe.** Los mensajes SysEx de prueba de Novation (`F0 00 20 29 01 63 …`, el mismo identificador que usa el Circuit Rhythm) se ignoran.
2. **La flash de los dos programas de DSP de ese modo (3,5 KB) es nuestra.** Las páginas de sección de Synth 1 / 2 viven ahora ahí; al final de la imagen quedan 2 588 B libres para lo siguiente (los carriles de Macros 2).

## Qué mirar

1. **Arranca y suena como siempre** (los programas del DSP se envían al encender, igual que antes).
2. **Synth 1 / 2, vista de la fuente**: páginas de sección (pads 1-8), Macros 2 (Shift + pad 1), ranuras de macro (pads 1 / 9 / 17 / 25), Duplicate + knob, editor de macros (pad 26), step-drummer (pad 32). Todo como en la 7.37: ese código es el que se ha movido.
3. **Uso normal un rato**: cargar proyectos y packs, Play, grabar, Master FX, las pistas MIDI con el sinte propio.
4. **Por USB**: Components o la app (`app.html`) leen y escriben como antes.

## Lo que prueba Claude por USB (con el aparato conectado)

- Los mensajes de prueba no hacen nada: sin respuesta, sin eco, y el aparato sigue contestando a la consulta de versión.

## Si algo falla

Dime qué y cuándo. Si Save parpadea en violeta, no apagues: es la caja negra; se lee desde la app (vista Hacks → Caja negra…).
