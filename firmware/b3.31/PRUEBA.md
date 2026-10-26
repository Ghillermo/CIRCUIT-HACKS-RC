# SC47.4 / Beta 3.31 = SC47.3 / Beta 3.30 + polifonía en FM

`firmware/sc47.4/circuittracks-4486-SC47.4.syx` — SHA-256 `37da08806c22a709e43496a45a4171870fe6b4e85cfe94bef85fdc61fe450b04`, marca `SC47.4`.
`firmware/b3.31/circuittracks-4486-B3.31.syx` — SHA-256 `f16d77ca190ae1e0d6e8ad8c75d8b22ab0ed6a7e91507ccdc3a8607c4c74cbc8`, marca `B3.31` (**Beta 3.31**, el mismo código).

El usuario (2026-10-26): «add polyphony to the remaing voices»; decisión: **FM con 4 voces en total** entre MIDI 1 y MIDI 2. Con esto quedan en poly todos los motores del sinte propio salvo el granular (vive en el núcleo 1 del DSP: una voz).

## Qué probar
1. MIDI 1 en **FM** (fila de motores, pad 24), **Shift + pad 29** hasta **poly** (magenta): acordes de hasta 4 notas; cada nota con sus cuatro operadores, sus envolventes y su ruido (una nota nueva no reinicia las otras).
2. Soltar una nota con otras pulsadas: suena entera con su release (no se corta). Con un release largo, tocar 5 notas: la más antigua deja su voz (con un fundido corto).
3. Algoritmos percusivos (bombo, caja, metal) en poly: cada golpe con su caída de pitch y su ruido; golpes seguidos se solapan.
4. **MIDI 2 también en FM poly:** cada pista con 2 voces (la tercera nota de una pista quita la más antigua de esa pista). Al poner o quitar la segunda pista en FM poly, las notas que suenan de la otra se cortan una vez (las voces se reparten de nuevo).
5. Mover los knobs del FM (ratios, niveles, algoritmo, feedback, ruido) con un acorde sonando: cambian todas las voces.
6. Lo de antes (oscilador, dos osciladores, VA-drum, modo muestra, FM de una voz sin poly, granular) suena igual que en la Beta 3.30.
7. CPU: FM poly en las dos pistas con drums y Master FX: escuchar si hay chasquidos (cada voz FM es la más cara del motor).

## Verificación en emulación
- `emu_poly3_dsp.py` frente a SC47.3: una voz FM igual que antes (el anillo y los bloques de operadores bit a bit); dos voces FM (48 / 55) en sus bloques `X:$3C00` / `$3C30` = la suma de dos voces sueltas × las ganancias, bloque a bloque; el estado de cada voz en sus bloques, los de la pista intactos; el ruido de la voz desde su registro + 10.
- `emu_poly3.py`: MIDI 1 en FM poly (la base escrita, 4 voces; fmeng deja los bloques de la pista, la bandera de FM sigue a 1); dos notas = una voz cada una con `PV_FMB` = `X:$3C00 + 48 v` antes de su objetivo, R / AMP en sus bloques, AMP_s / y[n − 2] a 0 al empezar, el ruido en el registro + 10; soltar 60 con 64 pulsada: su objetivo sigue mientras suena el release y se libera cuando sus envolventes bajan (35 ms con release 0); MIDI 2 en FM poly: 2 voces cada una (las 2 / 3 de MIDI 1 calladas al momento), las notas de MIDI 2 en `$3C60` / `$3C90`, una tercera nota en MIDI 1 quita la más antigua de sus 2; MIDI 2 fuera de FM: MIDI 1 vuelve a 4.
- `emu_fmeng2.py` (FM de una voz), `emu_poly2_dsp.py` / `emu_poly2.py` (dos osciladores, VA-drum, modo muestra): bien. `emu_poly_dsp.py`: el fallo por diseño de SC47.3 («dos osciladores = una voz»).
