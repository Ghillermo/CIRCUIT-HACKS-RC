# SC35D9 — DIAGNÓSTICO REMOTO + borrar un elemento del pack

`circuittracks-4486-SC35D9.syx` — SHA-256 `aa3425b6fecebf49c1c129b1883d10b936c5a0f97a85da690766201134f8eb15`
Imagen de 0x5bcd8 bytes, CRC 0x628966a2, marca `SC35D9`.

**No es un build de uso.** Es SC35D8 (el diagnóstico remoto que ya funciona) con una orden más: **borrar un elemento del pack** (un sample, una sesión, un patch…). Borrar un pack entero sigue bloqueado. Con él puedo hacer las pruebas yo mismo desde este ordenador, sin que pulses pads ni captures nada.

Para volver, envía SC34.1 o SC34.2.

## Qué necesito de ti
1. Envía SC35D9 y comprueba que el aparato arranca y suena.
2. **Deja el Circuit Tracks conectado por USB a este ordenador.**
3. **Cierra cualquier programa que use sus puertos MIDI:** monitor MIDI, Novation Components, el DAW, la página del lector. En Windows cada puerto solo lo puede abrir un programa.
4. Avísame. A partir de ahí lanzo yo las pruebas con `tools/ctremote.py`.

Para las pruebas de **escritura**:
- ten una copia de la tarjeta;
- **carga un pack duplicado**;
- dime qué pack es.

Antes de cada escritura te diré exactamente qué voy a escribir y dónde, y no escribiré nada sin tu permiso.

## Qué puedo hacer con él
- `ping`: comprobar que responde y la versión.
- `mem`: **leer** memoria del ARM. Solo flash y RAM, y solo lectura.
- `info` / `read` / `dump`: **leer** samples, sesiones y patches del pack por la vía del firmware original. Por ejemplo, copiar un `.wav` entero al PC para compararlo.
- `write` / `put`: **escribir** en un elemento del pack.
- `del`: **borrar** un elemento del pack.

Las escrituras y los borrados solo los haré con tu permiso y en el pack de prueba.

Prueba prevista en `30_PACK`:
1. borrar `PCM/05_Kick 4.wav`;
2. comprobar que ya no está;
3. volver a escribir su contenido desde la copia. Debe aparecer `PCM/05_PCM.wav`, con el mismo tamaño y contenido;
4. recargar el pack y escucharlo.

Todo pasa por SysEx con una cabecera propia (`F0 7D 43 54`), que el firmware original no usa. El resto de mensajes MIDI siguen igual.

## Verificación en emulación
`emu_sc35d8.py … --delete`, por la entrada real de SysEx del firmware:
- un SysEx ajeno sigue su camino normal;
- una petición mal formada se descarta sin responder;
- el ping responde por el mismo puerto;
- la lectura de memoria funciona dentro de flash / RAM y se rechaza fuera;
- `info`, `read` y `write` llegan a la vía de la tarjeta con los argumentos exactos;
- una orden desconocida se rechaza;
- el borrado llega a la vía de la tarjeta para los tipos 2-6;
- el pack entero (tipo 1) y los demás tipos se rechazan;
- el protocolo de `ctremote.py`, probado contra el propio firmware.

## Volver atrás
Envía SC34.1 o SC34.2.
