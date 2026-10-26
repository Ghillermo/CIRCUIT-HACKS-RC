# SC47.8 / Beta 3.35 = SC47.7 / Beta 3.34 con menos aliasing en el oscilador del sinte propio de MIDI 1 / 2

`firmware/sc47.8/circuittracks-4486-SC47.8.syx` — SHA-256 `0ba8cc428e83a7b9a568c2ee589c23d4c94b0b14b11ca512a3b7e280520abfa8`, marca `SC47.8`.
`firmware/b3.35/circuittracks-4486-B3.35.syx` — SHA-256 `ab4ca6da4be8caf42a79937826e05773d5c99be188c579d72bf65a530a6f9af7`, marca `B3.35` (**Beta 3.35**, el mismo código).

El usuario (2026-10-26): «Estudia cómo reducir el aliasing y el ruido»; del estudio (`docs/NOTAS.md`, «Estudio … aliasing y ruido»), la opción 1: «Ok a todo».

**Probada en el aparato (el usuario, 2026-10-26): «3.35 tested and working».**

## Qué probar
1. **Sierra, cuadrada y supersaw en notas agudas** (MIDI 1 / 2, motor oscilador, WAVE 84 / 126, SHAPE de la sierra a la izquierda y a la derecha): sin los tonos metálicos que no pertenecen a la nota (comparar con la Beta 3.34 desde el do 5 hacia arriba). En graves, igual que antes.
2. **Wavefold** (seno o triángulo, SHAPE a la derecha del todo): en notas graves y medias igual que antes; en las agudas pliega menos (más limpio, menos brillante).
3. **El seno y el triángulo sin pliegue** suenan exactamente igual.
4. **Carga del DSP:** dos pistas en poly con la supersaw, acordes de 6 notas, drums y Master FX a la vez: el audio no debe ralentizarse ni dar chasquidos (la corrección cuesta ≈ 1 600-2 400 instrucciones por bloque y voz).
5. Los dos osciladores con el sync suave: el oscilador 2 cuando va hacia atrás no se corrige (queda como antes).

## Verificación en emulación
- `emu_blep_dsp.py` frente a SC47.7: el seno, el triángulo, el seno plegado del todo en la nota 60 y el morph seno / triángulo bit a bit; aliasing bajo 8 kHz: sierra nota 96 y 72, pulso nota 96 por debajo de −55 dB, supersaw nota 96 por debajo de −50 dB; el seno plegado del todo en la nota 96 de −24 a −35 dB (objetivo −30); la pila del sistema con el tráfico del motor.
- `emu_vorder.py`, `emu_vmode.py`, `emu_poly3.py`, `emu_poly2.py`, `emu_fmspi.py`, `emu_kbin.py`, `emu_fmeng2.py`, `emu_arpx.py` frente a SC47.1: bien.
