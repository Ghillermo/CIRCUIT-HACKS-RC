# SC35D2 — DIAGNÓSTICO: mapa de la memoria externa del DSP (solo lectura)

`circuittracks-4486-SC35D2.syx` — SHA-256 `7ce523e79f56f6189c8716960cfe1bce32e8bed062a779212ea76628c20cd774`
Imagen de 0x5c08c bytes, CRC 0xafe73b90, marca `SC35D2`.

**No es un build de uso.** Usa la misma cadena que SC35D / SC35D.1, el mismo pad 9 y el mismo lector. **No toca la tarjeta SD**, no guarda nada y **no escribe en la memoria externa**: solo la lee. Para volver: envía SC34.

## Para qué
SC35D.1 descubrió dos cosas:
- **El aparato escribe en `Y:$600000` después del arranque.** Ahí empiezan el búfer del sample capturado de SC33 / SC34 (`$600000`) y las copias de la sustitución de samples (`$640000…`).
- **Con un pack grande, la lista de lecturas del segundo núcleo crece** y pisó las variables del diagnóstico.

SC35D2 averigua qué zonas de la memoria externa usa el aparato y cuáles quedan libres, para mover allí el búfer del sample capturado.

## Qué hace
- **Núcleo 0:** en cada bloque de audio lee una de 24 direcciones, una tras otra:
  - dos de control, dentro de las zonas de samples: `$337000` y `$5BE000`;
  - 22 entre `$5C0000` y `$8F0000`.

  Apunta qué direcciones han cambiado desde el arranque y cuáles cambian de forma continua, en ventanas de 1024 bloques.
- **Núcleo 1:**
  - mide sus vueltas libres por bloque;
  - mide la lista de lecturas más larga que ha servido;
  - guarda sus variables al final de la memoria compartida, donde la lista no llega.

## Prueba
1. Envía SC35D2. Comprueba que el aparato suena con normalidad.
2. Usa el aparato como siempre durante unos minutos:
   - carga un proyecto;
   - **cambia de pack** al menos una vez;
   - toca una canción **con delay y reverb altos** y con drums, sintes y samples sonando.
3. Abre `tools/sc32d1_reader.html` en Chrome o Edge y pulsa «Permitir MIDI y escuchar».
   - En Windows, cierra antes el monitor MIDI, Components y el DAW.
   - Otra opción: graba con tu monitor MIDI y abre el `.log` en la página.
4. Pulsa Synth 1 dos veces para abrir la vista de la fuente. Cuando el **pad 9** esté **verde**, púlsalo.
5. La página reconoce SC35D2 y muestra un **mapa de las 24 direcciones**:
   - **estable:** candidata a libre;
   - **cambió alguna vez:** se escribe al cargar algo;
   - **cambia:** está en uso continuo.

   Mándame el texto de «Texto para copiar y mandar».
6. Si puedes, repite el paso 4 después de otro cambio de pack.

Las dos direcciones de control (bits 0 y 1) deberían salir «cambió alguna vez» después de cambiar de pack. Si es así, el método funciona.

El aparato corta cada pulsación a 64 mensajes, así que los valores 12 y 13 no llegan. Son secundarios.

## Verificación en emulación
`emu_sc35d2.py` comprueba:
- **En la imagen:** el programa del núcleo 1 cabe en sus 2 K palabras y el gancho del núcleo 0 está en su sitio.
- **El núcleo 1:**
  - vueltas por bloque;
  - lista más larga;
  - no escribe nada en la zona de la lista;
  - no toca `r5` / `m5`.
- **El núcleo 0:**
  - la primera vuelta solo apunta los valores;
  - un cambio posterior marca su dirección;
  - la ventana se cierra cada 1024 bloques;
  - las direcciones de la memoria externa solo se leen;
  - la marca solo aparece cuando el núcleo 1 ha respondido.

## Volver atrás
Envía SC34. Mientras no se mueva el búfer, **no grabes samples con SC33 / SC34**.
