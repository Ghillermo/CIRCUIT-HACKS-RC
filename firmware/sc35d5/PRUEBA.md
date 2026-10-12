# SC35D5 — DIAGNÓSTICO: leer los samples del pack por la vía del firmware original (solo lectura)

`circuittracks-4486-SC35D5.syx` — SHA-256 `0d9c322edb5d99962beb42dd69d98c4bf5e94827ac5d95c46f03eb6a573124e6`
Imagen de 0x5b90c bytes, CRC 0x3aa6c846, marca `SC35D5`.

**No es un build de uso.** Es SC35D4 con un solo cambio: lee los **samples** (tipo 4). SC35D4 leía las sesiones: su tipo 2 resultó ser la carpeta `Sessions`. Usa la misma cadena que SC35D, el mismo lector y la vista de la fuente.
**Solo lee la tarjeta SD: no escribe ni borra nada.** Aun así, por costumbre, ten una copia de la tarjeta.

Para volver, envía SC34.1.

## Para qué
Es el primer paso para **guardar el sample capturado en la carpeta `PCM/` del pack**, sustituyendo un sample para todo el pack.

SC34D falló porque usaba directamente los objetos de fichero del aparato. Esta vez usamos la misma vía que Novation Components para subir samples: se le piden las operaciones (existe, tamaño, leer y, más adelante, escribir) a la tarea que gestiona la tarjeta. Esa tarea abre y cierra los ficheros por su cuenta.

Este diagnóstico solo **lee**, para comprobar tres cosas:
- que podemos llamar a esa vía sin colgar el aparato;
- que el sample N del pack actual se identifica como esperamos;
- qué nombre de fichero usa el aparato.

## Prueba
1. Envía SC35D5 y comprueba que el aparato arranca y suena.
2. Abre `tools/sc32d1_reader.html` en Chrome o Edge. Si ya la tenías abierta, **recárgala**: la versión anterior no reconoce este volcado. y pulsa «Permitir MIDI y escuchar». Cierra antes el monitor MIDI, Components y el DAW. Otra opción: graba con tu monitor MIDI y abre el `.log` en la página.
3. Pulsa Synth 1 dos veces para abrir la vista de la fuente. Los **pads 9 a 16** se encienden en verde.
4. Pulsa el **pad 9**: lee el sample 0 del pack actual y manda el resultado. La página muestra:
   - si existe;
   - su tamaño;
   - los primeros bytes del fichero, que deberían empezar por `RIFF` y seguir con `WAVEfmt`.

   Mándame el texto de «Texto para copiar y mandar».
5. Si puedes, pulsa también el **pad 10** (sample 1). Compara los tamaños con los ficheros `PCM/00_….wav` y `PCM/01_….wav` de ese pack en el ordenador.

**Si el aparato se queda colgado al pulsar un pad**, apágalo y enciéndelo y dímelo. Es un resultado útil y la tarjeta no corre peligro, porque no se escribe nada.

## Verificación en emulación
`emu_sc35d4.py … --kind 4`, con la vía de la tarjeta simulada:
- con la vista cerrada no hace nada;
- con la vista abierta, los pads 9 a 16 se encienden en verde;
- el pad 9 + k pide existe, tamaño y leer 21 bytes desde el principio del sample k del pack actual, de forma síncrona;
- **nunca** llama a la escritura;
- el volcado tiene las 14 palabras;
- el pad 17 no hace nada.

## Volver atrás
Envía SC34.1.
