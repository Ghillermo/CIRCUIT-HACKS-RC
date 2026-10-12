# SC35D8 — DIAGNÓSTICO REMOTO: Claude lo maneja desde el PC por USB

`circuittracks-4486-SC35D8.syx` — SHA-256 `867834b651cb8bd39f34550c8f53971ae3158eca2cc897ee6f2da914cf9ecc50`
Imagen de 0x5bc8c bytes, CRC 0x73ba1238, marca `SC35D8`.

**No es un build de uso.** Es SC35D7 (con sus pads) y además un **canal de diagnóstico por SysEx USB**. Con él puedo hacer las pruebas yo mismo desde este ordenador, sin que pulses pads ni captures nada.

Para volver, envía SC34.1 o SC34.2.

## Qué necesito de ti
1. Envía SC35D8 y comprueba que el aparato arranca y suena.
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
- `write`: **escribir** en un elemento del pack. Solo la usaré con tu permiso y en el pack de prueba.

Todo pasa por SysEx con una cabecera propia (`F0 7D 43 54`), que el firmware original no usa. El resto de mensajes MIDI siguen igual.

## Verificación en emulación
`emu_sc35d8.py`, por la entrada real de SysEx del firmware:
- un SysEx ajeno sigue su camino normal;
- una petición mal formada se descarta sin responder;
- el ping responde por el mismo puerto;
- la lectura de memoria funciona dentro de flash / RAM y se rechaza fuera;
- `info`, `read` y `write` llegan a la vía de la tarjeta con los argumentos exactos;
- una orden desconocida se rechaza;
- el protocolo de `ctremote.py`, probado contra el propio firmware.

## Volver atrás
Envía SC34.1 o SC34.2.
