# Alpha 7.39 — qué probar

Instalar `circuittracks-4486-A7.39.syx` (modo bootloader: Scales + Preset + Note al encender). Es la Alpha 7.38 (sin el modo de prueba de fábrica, 3,5 KB de flash más) + **un arreglo del morph de Synth 1 / 2**.

## El arreglo: el morph de Synth 1 / 2 ahora mueve todo el patch

Hasta ahora el morph (desde la Beta 5.34) se saltaba, por un error al leer la tabla de parámetros, **los osciladores, el mezclador, el filtro y la envolvente de amplitud** (y el destino de la primera ranura de cada macro): solo cambiaban las demás partes del patch. Ahora pasan todas (los indicadores de los LFO, que comparten byte, cambian a mitad de camino). **La octava del teclado no se mueve con el morph**: los botones Octave siguen funcionando con el morph sonando.

1. **Synth 1, vista Preset: mantén dos patches muy distintos** (por ejemplo un bajo y un pad) 0,4 s: la vista del morph.
2. **K1 de un extremo a otro**: el sonido tiene que pasar de un patch al otro también en el **tono y la forma de onda de los osciladores, el filtro (frecuencia y resonancia) y la envolvente** (ataque, release). Antes esos se quedaban como el patch de partida.
3. Los LFO del morph (K2 / K3) y la envolvente (pads 1 / 8): lo mismo, el movimiento se oye en el filtro y los osciladores.
4. **Escucha si hay chasquidos o un tempo que se arrastra** al disparar la envolvente (pad 1 / 8) con muchas notas: ahora el morph puede escribir 307 parámetros en vez de 246 (los que difieren entre los patches).
5. **Octave con el morph sonando** (vista Note de Synth 1): sube / baja la octava y se queda.
6. Mientras el morph está activo manda él: un knob de las páginas de sección (OSC, VCF…) o un CC entrante sobre esos parámetros vuelve al valor del morph enseguida (como ya pasaba con los macros).
7. Lo mismo en **Synth 2**.

## Lo de la 7.38 (sin cambios de uso)

8. Arranca y suena como siempre; páginas de sección (pads 1-8), Macros 2, ranuras de macro, editor de macros (pad 26), step-drummer (pad 32) como en la 7.37.
9. Components y la app (`app.html`) leen y escriben como antes.

## Lo que prueba Claude por USB (con el aparato conectado)

- Los mensajes de prueba de fábrica (`F0 00 20 29 01 63 …`) no hacen nada y el aparato sigue contestando a la consulta de versión.

## Si algo falla

Dime qué y cuándo. Si Save parpadea en violeta, no apagues: es la caja negra; se lee desde la app (vista Hacks → Caja negra…).
