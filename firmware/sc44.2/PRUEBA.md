# SC44.2 / Beta 1.31 (B1.31) = SC44.1 + matriz de modulación del sinte propio + teclado partido con cualquier par + el ARM compactado

`circuittracks-4486-SC44.2.syx` — SHA-256 `73eafc6cede38b11e9769967eaeab5dc90f1e959cca9e6e05e16a0526d7468f3`, marca `SC44.2`.
`firmware/b1.31/circuittracks-4486-B1.31.syx` — SHA-256 `082945f6c2a150a0dbbd23289d955852e734958bf0a0f4e2e91dfd9e601569e0`: el mismo código con la marca `B1.31` (**Beta 1.31**).

El usuario (2026-10-18): «Design a light mod matrix for the own synth» · «modw and aftertouch are not supported» · «Add all exposed parameters as destination. Give them colors and make them slow knobs» · «Each Knob 1-8 represents a source, the knob state is the destination. Moving inside a destination range controls the amount» · «add split keyboard for any two tracks».

- **Matriz** (pad 6 de la vista Preset de MIDI 1 / 2, con el motor encendido): K1 velocity, K2 nota, K3 azar por nota, K4 LFO 2, K5 envolvente 2, K6 golpe de un drum, K7 posición en el patrón, K8 azar por pasos. La posición del knob = destino (33 parámetros, un tramo de 16 pasos cada uno, 2 clics por paso) y cantidad.
- **Teclado partido:** cualquier par de Synth 1, Synth 2, MIDI 1, MIDI 2; arriba la pista mantenida primero.
- **Flash:** el ARM compactado (`thumb.COMPACT`): sin cambios de comportamiento (comprobado instrucción a instrucción con `compact_check.py`).

## Qué probar
1. MIDI 1 con el motor encendido (oscilador), Preset: el pad 6 azul claro tenue; tocarlo = brillante (la matriz); los pads 1-5 vuelven a sus páginas.
2. Girar K1 despacio a la derecha: el LED se enciende en naranja (página 1) y va subiendo de brillo; cada 16 pasos (32 clics) cambia de destino y vuelve a empezar oscuro. Mientras giras: el pad de la página y el pad del destino brillan en los pads 9-24 (K1-K8 arriba, Shift abajo); 1,5 s después vuelven los patches.
3. Con K1 en el filtro (5.º tramo, pad 13 brillante), tocar notas suaves y fuertes: el filtro se abre con la velocity; el valor de la página 1 no cambia.
4. K4 (LFO 2) a la resonancia o al morph: se mueve solo; **Shift + K4**: el color = la forma (verde, amarillo, rojo, violeta), girar = más rápido dentro de cada forma.
5. K5 (envolvente 2) a un destino: un golpe en cada nota; Shift + K5 cambia ataque / caída. K6: elegir un drum con Shift + K6 y llevarlo al filtro: cada golpe del drum abre el filtro. K7: una rampa a lo largo del patrón (en marcha). K8: valores al azar por pasos.
6. Clear + K1: apagado (oscuro); Clear + pad 6: todo apagado.
7. Guardar un patch del sinte propio (Clear + pad 9-24 dos veces), apagar la matriz, cargar el patch: la matriz vuelve. Un patch antiguo: la matriz apagada. Duplicate + A + B: la matriz viaja con el patch.
8. Teclado partido: mantener MIDI 1 y pulsar Synth 1: arriba MIDI 1, abajo Synth 1 (cada uno con su escala y octava); MIDI 2 + MIDI 1, Synth 2 + MIDI 2; un botón de pista solo lo cierra; Play / Octave no. Drum 1 + Synth 1: nada especial.
9. Todo lo demás como RC2.01 (el código entero cambió de sitio por la compactación).

## Verificación en emulación
- `emu_sc44_2.py`: el pad 6 por el controlador (página 5 de vcf21, LED `0x13`); la RAM de la matriz con su firma; K1: 1 clic nada, 2 = un paso, 160 clics = el filtro entero; su LED naranja a brillo máximo; el mapa de los pads (pad 1 y pad 13 brillantes, los otros parámetros tenues); una pulsación en los pads 9-24 tragada con el mapa, después no; una nota con velocity 127 / 32: el filtro al DSP 63 / 31 con el valor guardado 0; K4 en la resonancia: 23 valores en 58 mensajes; Shift + K4 triángulo / sierra; Clear + K1: el filtro vuelve a 0; en el modo muestra, K3 (azar) al código 25 = números de sample de −1 a 63; el patch: «MX», las posiciones y los parámetros en el relleno + 64; aplicar un patch con matriz la restaura y sin ella la apaga; Clear + pad 6. Teclado partido: MIDI 1 + Synth 1, Synth 1 + MIDI 2, MIDI 2 + Synth 2: las notas de cada mitad, sus note-off, los LEDs, Play lo deja, un botón solo lo cierra; Drum 1 + Synth 1 nada.
- `compact_check.py build_sc44_2.py`: 938 cargas, 8 161 saltos, 36 parches posteriores y lo de fuera de los bloques iguales a la build sin compactar (que ya no cabe en la flash: solo como referencia).
- `emu_sc44.py`, `emu_rodisk.py`, `emu_sc43_9.py` … sobre SC44.2 (ver NOTAS).
