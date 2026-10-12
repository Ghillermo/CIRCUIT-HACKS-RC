# SC342D — SC34.2 con el diagnóstico remoto (tarjeta SD y memoria del DSP)

`circuittracks-4486-SC342D.syx` — SHA-256 `12dce7c82f3c47e68c879107f6d7c47895ecc7a8813b51dce0730fdfc36cd3e1`
Imagen de 0x6268c bytes, CRC 0x143a6129, marca `SC342D`.

Es **SC34.2 completo**, usable con normalidad: sample capturado, modo frase, etc. Lleva además el canal de diagnóstico remoto de SC35D9 y una novedad: puedo leer desde el PC la memoria del DSP, **incluida la captura**. Es la última pieza que falta para SC35 (guardar la captura en la tarjeta).

## Qué necesito de ti
1. Envía SC342D y comprueba que arranca y suena.
2. Deja el aparato conectado por USB, con los puertos MIDI libres.
3. Elige el pack 30 (o el 31).
4. En Master FX, **graba una captura** con el pad 32 (un par de segundos de algo reconocible) y avísame. Es la única pulsación que necesito.

Después lo hago yo:
1. descargo la captura al PC como `.wav` y te la dejo para que la escuches;
2. si está bien, la escribo como sample 5 del pack de prueba;
3. tú recargas el pack y la escuchas desde el aparato.

## Cómo funciona
El ARM no puede leer directamente la memoria externa del DSP, donde está la captura. Así que aprovecho la copia por bloques que ya usa la sustitución de drums de SC34: le pido al DSP que copie 48 muestras a una pequeña ventana de su memoria interna, y el ARM las lee desde ahí. No hay código DSP nuevo. Mientras usa el puerto del DSP, el ARM toma el mismo semáforo que el firmware original, para no chocar con el servicio de audio.

## Verificación en emulación
- `emu_sc342d.py`: todas las pruebas del diagnóstico remoto (SC35D9) y las del DSP simulado:
  - lectura de palabras X / Y;
  - orden exacto de las escrituras de la copia;
  - muestras devueltas;
  - el semáforo siempre tomado durante los accesos;
  - los casos «copia en curso» y «copia que no termina».
- `emu_sc34_2.py` pasa también sobre SC342D: todo SC34.2 sigue igual.

## Volver atrás
Envía SC34.2.
