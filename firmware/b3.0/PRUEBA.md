# Beta 3.0 (B3.0) = SC44.3 = RC2.01 + matriz de modulación del sinte propio + teclado partido con cualquier par + LFO con triángulo por defecto y sample & hold suavizado

`firmware/b3.0/circuittracks-4486-B3.0.syx` — SHA-256 `e1399cdee28e2604fd842b56ed802727396d1de097d401f48026a76e1bc7c1f7`, marca `B3.0`: el código de SC44.3 (`firmware/sc44.3/`) con la marca de la beta (6 bytes distintos).

El usuario (2026-10-18): «publish as beta 3.0» (SC44.3, con el sample & hold suavizado). Reúne Beta 1.31 (SC44.2) y Beta 1.32 (SC44.3), que no se publicaron. Sin versión «S»: solo las RC la llevan (el usuario, 2026-10-18).

- **Matriz de modulación** (pad 6 de la vista Preset de MIDI 1 / 2, con el motor encendido): K1 velocity, K2 nota, K3 azar por nota, K4 LFO 2, K5 envolvente 2, K6 golpe de un drum, K7 posición en el patrón, K8 azar por pasos. La posición del knob = destino (33 parámetros, un tramo de 16 pasos cada uno, 2 clics por paso) y cantidad. Shift + K4 / K5 / K6 / K8 = sus parámetros. Se guarda con los patches del sinte propio.
- **Teclado partido:** cualquier par de Synth 1, Synth 2, MIDI 1, MIDI 2; arriba la pista mantenida primero.
- **LFO del motor** (página 5, Shift + K8): siete formas: diente de sierra inverso (naranja), diente de sierra (magenta), triángulo (verde), cuadrada (roja), seno (cian), sample & hold (blanco), **sample & hold suavizado (violeta)**; **sin forma guardada, el triángulo**.
- **LFO 2 de la matriz** (Shift + K4): triángulo (verde, el inicial), diente de sierra (magenta), cuadrada (roja), sample & hold (blanco), sample & hold suavizado (violeta).
- **Flash:** el código del ARM compactado (`thumb.COMPACT`), sin cambios de comportamiento (comprobado instrucción a instrucción con `compact_check.py`). **RAM:** la matriz y el teclado partido guardan su estado encima del heap (`0x20045000–0x200450CF`), una zona que el propio firmware cuenta como libre; aún sin probar en el aparato: si algo falla con esta beta, sospechar esto primero.

## Qué probar
1. MIDI 1 con el motor encendido (oscilador), Preset: el pad 6 azul claro tenue; tocarlo = brillante (la matriz); los pads 1-5 vuelven a sus páginas.
2. Girar K1 despacio a la derecha: el LED se enciende en naranja (página 1) y va subiendo de brillo; cada 16 pasos (32 clics) cambia de destino y vuelve a empezar oscuro. Mientras giras: el pad de la página y el pad del destino brillan en los pads 9-24; 1,5 s después vuelven los patches.
3. Con K1 en el filtro, tocar notas suaves y fuertes: el filtro se abre con la velocity; el valor de la página 1 no cambia.
4. K4 (LFO 2) a la resonancia o al morph: se mueve solo; **Shift + K4**: verde → magenta → rojo → blanco → violeta; con el violeta el destino se desliza, con el blanco salta.
5. K5 (envolvente 2): un golpe en cada nota; Shift + K5 cambia ataque / caída. K6: elegir un drum con Shift + K6 y llevarlo al filtro: cada golpe del drum abre el filtro. K7: una rampa a lo largo del patrón (en marcha). K8: valores al azar por pasos.
6. Clear + K1: apagado; Clear + pad 6: todo apagado.
7. Guardar un patch del sinte propio (Clear + pad 9-24 dos veces), apagar la matriz, cargar el patch: la matriz vuelve. Un patch antiguo: la matriz apagada. Duplicate + A + B: la matriz viaja con el patch.
8. LFO del motor: un proyecto nuevo, el LFO al filtro (página 5): triángulo (Shift + K8: LED verde); hasta el final, tras el blanco el violeta (azar deslizándose). Un proyecto guardado con otra forma la conserva; un patch propio de antes de las formas: diente de sierra inverso.
9. Teclado partido: mantener MIDI 1 y pulsar Synth 1: arriba MIDI 1, abajo Synth 1; MIDI 2 + MIDI 1, Synth 2 + MIDI 2; un botón de pista solo lo cierra; Play / Octave no. Drum 1 + Synth 1: nada especial.
10. Todo lo demás como RC2.01 (el código entero cambió de sitio por la compactación).

## Verificación en emulación
- `emu_sc44_3.py` y `emu_sc44_2.py` sobre B3.0 (las formas del LFO, la matriz, el teclado partido); `emu_sc44_3_dsp.py` (SC44.3 frente a SC44.2); `compact_check.py build_sc44_3.py`. Detalle en `firmware/sc44.2/PRUEBA.md`, `firmware/sc44.3/PRUEBA.md` y `docs/NOTAS.md`.
