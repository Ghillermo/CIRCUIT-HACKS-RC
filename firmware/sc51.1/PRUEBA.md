# SC51.1 = SC51 + el bucle del sample capturado sigue al cargar otro proyecto o pack

SHA-256 del `.syx`: `616db68f0a7769eb48e75546a25d3f362b37f3df94c5eaafd939120276982aea`. Pendiente de probar en el aparato. Si no arranca: Scales + Preset + Note e instalar la Beta 5.12.

1. Master FX: graba una captura (pad 32) y engánchala en bucle (Shift + pad 7). Para el transporte.
2. Carga otro pack (o otro proyecto del mismo pack). **El bucle sigue sonando** igual (tono, inicio y fin), también durante la carga. *Lo que hay que mirar: si durante la carga de los samples del pack el sonido se corta un momento; en emulación no se puede ver.*
3. Pulsa **Play**: no arranca enseguida. Play parpadea en verde, el bucle termina su vuelta y **entonces** empieza el proyecto nuevo, en el primer tiempo; el bucle deja de sonar.
4. El pad 7 ya no toca nada (la captura se ha descartado) hasta grabar otra. Los knobs del sample (pad 7 elegido) son los del proyecto nuevo.
5. Repite 1-2 y pulsa **Play dos veces**: la segunda corta el bucle y el proyecto empieza al momento.
6. Repite 1-2 y para el bucle con el pad 7 (o el pad 8) antes de Play: se para, Play arranca como siempre.
7. Sin bucle enganchado: cargar un proyecto y Play funcionan como siempre (el bucle no enganchado, o el modo loop de K2 mantenido, se paran al cargar como antes).
8. Un pack con un drum sustituido por una captura y guardado: se carga como siempre y su drum suena con esa captura; el bucle que venía sonando no cambia.
9. Con la cuenta atrás encendida y Record armado, el Play final pasa por la cuenta atrás.
10. Todo lo de `firmware/sc51/PRUEBA.md` sigue igual.
