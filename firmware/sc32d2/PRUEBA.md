# SC32D2 — DIAGNÓSTICO: zonas libres de la memoria externa del DSP (corregido), con volcado por MIDI

`circuittracks-4486-SC32D2.syx` — SHA-256 `8a3e353e698e270bdb28da059b66af78927f07503a6d80c0d950f864eedc3db3`
Imagen de 0x5c2a4 bytes, CRC 0x2298d1eb, marca `SC32D2`. **No es un build de uso.** Misma cadena que SC32D / SC32D.1. Úsalo con un proyecto de prueba; no guarda nada. Para volver: envía SC32 (o SC31).

## Qué cambia respecto a SC32D
SC32D.1 mostró dos cosas:
- **La memoria externa guarda 16 bits por palabra:** el byte bajo se relee como 0. El patrón de SC32D (`5A5A00 + zona`) solo tenía el byte bajo a cero en la zona 0; por eso las demás salían «la escritura no se relee» sin estar mal.
- **M0 = `$FFFF` en el gancho:** las 32 lecturas de cada zona se quedaban dentro de una ventana de 64 K.

Ahora:
- el patrón es `5A5A00 + zona × 256` (byte bajo a 0);
- las lecturas van en modo lineal y recorren toda la zona; M0 se restaura al salir;
- el rojo es rojo de verdad (0x53).

El resto es como SC32D:
- 38 áreas: 30 zonas de stock y 8 direcciones más allá;
- una zona por bloque de audio;
- una palabra por zona escrita y restaurada enseguida.

## Prueba
1. Envía SC32D2 y conecta el aparato por **USB**.
2. Enciende y **cambia de sesión** a un proyecto de prueba que tenga samples en los drums (al cargar se meten sus samples en sus zonas).
3. Después pon una canción sonando con drums, **delay y reverb al máximo**, y déjala **un minuto** (un retardo en silencio solo contiene ceros y parecería libre). Las marcas se acumulan desde el encendido: solo sale «LIBRE» lo que siempre ha estado a cero.
4. Abre `tools/sc32d1_reader.html` en Chrome o Edge y pulsa «Permitir MIDI y escuchar». También vale tu debugger o un monitor MIDI; pega su salida en la página.
5. Pulsa Synth 1 dos veces para abrir la vista de la fuente. Pulsa el **pad 9** (zonas 0-18) y después el **pad 10** (zonas 19-37): cada uno manda 42 mensajes CC por el **canal 16**, y la página junta las dos tandas. (Van en dos tandas porque en SC32D.1 el volcado se cortaba siempre a los 64 mensajes.)
6. Mándame el texto que da la página. Púlsalo otra vez al cabo de un rato: si el número de vueltas sube, el sondeo sigue vivo.

Los LEDs siguen enseñando las páginas de SC32D, con estos colores (rojo = 0x53):

| Color | Significado |
|---|---|
| verde | libre |
| amarillo | contenido fijo |
| magenta | cambia |
| azul claro | espejo |
| rojo | falla |

## Formato del volcado (canal 16)
- CC 20 = 127: inicio.
- Por cada área k (pad 9: 0..18; pad 10: 19..37): CC 21 = k, CC 22 = sus banderas:

  | Bit | Significado |
  |---|---|
  | 0 | visitada |
  | 1 | algo distinto de cero |
  | 2 | cambia entre vueltas |
  | 3 | escritura bien |
  | 4 | espejo |

- CC 23 / CC 24 = número de vueltas (7 + 7 bits).
- CC 20 = 0: fin.

## Volver atrás
Envía SC32 (o SC31).
