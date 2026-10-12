# SC36 — sinte granular, Glitch y secuenciador de efectos

`circuittracks-4486-SC36.syx` — SHA-256 `0a429c329fb38176223fbf785d692c168c65000576f9e68b46044c0751104a07`
Imagen de 0x64a7c bytes, CRC 0x6eedcfa1, marca `SC36`.

Es SC35 más tres funciones nuevas que corren en el segundo núcleo del DSP. Todo lo de SC35 sigue igual: guardar capturas en el pack, intercambiar samples, borrar packs y el diagnóstico remoto por USB.

## 1. Sinte granular (MIDI 1 / 2)

En la vista Preset de MIDI 1 o 2, el **pad 27** recorre estos estados:

| Estado | Color del pad 27 |
|---|---|
| apagado | apagado |
| entrada de línea | amarillo |
| oscilador | verde |
| VA-drum | rojo |
| **granular** | **magenta** |
| **secuenciador de efectos** | **azul** |

Después del último vuelve a apagado.

En el estado granular, el pad 2 de la fila superior abre la página del granular (la del OSC1). El pad 1 sigue siendo la página VCA / VCF, que se aplica igual que con el oscilador.

| Knob | Sin Shift | Con Shift |
|---|---|---|
| K1 | tono, ± 24 semitonos | fino, ± 1 semitono |
| K2 | posición en el sample | dispersión de la posición |
| K3 | scan: centro = congelado; a la derecha avanza y a la izquierda retrocede, más rápido hacia los extremos | probabilidad de grano al revés |
| K4 | tamaño del grano, 5–500 ms | dispersión del tono, hasta ± 12 semitonos |
| K5 | densidad, 1–16 granos solapados | ventana: izquierda rectangular, centro triangular, derecha percusiva |
| K6 | longitud de la zona que recorre el scan | modo de nota: izquierda = tono, derecha = slicer |
| K7 | LFO → posición | LFO → tamaño |
| K8 | envolvente → posición | **fuente**: un paso por giro; sample 1–64 del pack y, del todo a la izquierda, la captura |

- **Notas en modo tono:** cambian la altura de los granos. Con dos notas pulsadas, los granos se reparten entre las dos.
- **Notas en modo slicer:** la nota elige una de las 16 partes del sample, contando desde el C de la octava 2.
- **Valores compartidos:** los knobs del granular usan los mismos valores que la página del oscilador. Si cambias de motor, los valores se reinterpretan. Se guardan los de los knobs sin Shift y la fuente; el resto se pierde al apagar, como los del OSC2.
- **Captura:** como fuente funciona directamente.
- **Aviso:** una pista que en una versión anterior estaba en oscilador con el pad 31 encendido aparece aquí como granular. Pulsa el pad 27 para cambiarla.

## 2. Glitch (pad 31 de Master FX y de la vista FX)

- **Funcionamiento:** mientras mantienes el pad 31, la salida master se sustituye por una cabeza de cinta que lee el audio de hace un momento. Es el «romper y retrasar» de las pruebas de SC35DB.
- **Knobs:** al pulsar el pad 31 en Master FX, los knobs K1–K4 son los del Glitch.

| Knob | Función |
|---|---|
| K1 | velocidad: arriba del todo = normal; al bajar frena como una cinta; en el centro, parada; por debajo, hacia atrás |
| K2 | tamaño de la repetición; al máximo, sin repetición (retraso continuo) |
| K3 | retraso, hasta unos 2,6 s |
| K4 | caos: saltos atrás, cortes y cambios de sentido al azar |

- **El pad 31 ya no es un hueco asignable.** Si tenías un efecto asignado ahí, se ignora.
- **LED:** el pad 31 se ilumina mientras el Glitch suena.

## 3. Secuenciador de efectos

1. En MIDI 1 / 2, pasa el pad 27 al estado **azul**. Se activa el step-drummer de esa pista.
2. Abre su vista con el pad 30. Pon notas en los pasos con Shift + pad.
3. Con cada knob (un par de pasos), elige el efecto:

| Valor del knob | Efecto |
|---|---|
| 0 | ninguno |
| 1–19 | pad 1 |
| 20–37 | pad 2 |
| 38–55 | pad 3 |
| 56–74 | pad 4 |
| 75–92 | pad 5 |
| 93–110 | pad 6 |
| 111–127 | Glitch |

4. Con el secuenciador en marcha, ese efecto se enciende sobre el master durante los pasos que tienen nota. Usa los knobs actuales de cada efecto en Master FX.

Ten en cuenta:
- Las notas de esa pista siguen saliendo por MIDI.
- La pista no suena en el DSP.
- Al salir del estado azul, el step-drummer de la pista se apaga.

## Qué probar y contarme

1. **Que SC36 arranca y todo lo de SC35 funciona.**
2. **Granular:**
   - todos los knobs;
   - con densidad alta (K5 a la derecha) y en las dos pistas a la vez, si aparecen chasquidos o se ralentiza el audio. Si pasa, dime con qué ajustes.
3. **Glitch:**
   - los cuatro knobs;
   - que al soltar el pad vuelve el audio normal.
4. **Secuenciador de efectos:** con varios efectos y el Glitch.
5. **Uso remoto:** si dejas el aparato conectado por USB, puedo leer el estado del segundo núcleo desde el PC con `ctremote.py`.

## Verificación en emulación
- **Núcleo 1:** `emu_gran_core1.py` comprueba:
  - el búfer circular del master;
  - las voces apagadas;
  - la envolvente del grano;
  - el tono interpolado (± 12 semitonos);
  - el reverso, la densidad y el slicer;
  - el Glitch: retraso, velocidad, reverso y repetición;
  - la vuelta más larga: 1 173 instrucciones.
- **Núcleo 0 y comparación con SC35:** `emu_sc36_dsp.py` comprueba:
  - las copias para el núcleo 1 y el Glitch sustituyendo el master;
  - el contador de bloques;
  - la voz granular a través de su cadena;
  - las notas nuevas;
  - el bit del buzón;
  - el coste: 929 instrucciones por bloque;
  - las voces normales y los drums idénticos a SC35.
- **ARM, por las rutas reales:** `emu_sc36.py` comprueba:
  - el pad 27, sus LEDs y el mensaje ACT;
  - la página de knobs del granular;
  - el secuenciador de efectos;
  - el Glitch en Master FX y en la vista FX.
- **Regresiones de SC25, SC28, SC30, SC31 y SC33** (step-drummer) sobre SC36.

## Volver atrás
Envía SC35.
