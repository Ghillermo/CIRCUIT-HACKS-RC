# SC35D3 — DIAGNÓSTICO: zonas candidatas para el búfer del sample capturado

`circuittracks-4486-SC35D3.syx` — SHA-256 `f401d4ed95c365800471157991c694a8da68cdc317fb251279a993e88eda9b2a`
Imagen de 0x5c0c8 bytes, CRC 0x1f510219, marca `SC35D3`.

**No es un build de uso.** Usa la misma cadena que SC35D2, el mismo pad 9 y el mismo lector. **No toca la tarjeta SD**, no guarda nada y **no escribe en la memoria externa**: solo la lee. Para volver, envía SC34.

## Para qué
SC35D2 mostró que los samples del pack se cargan uno detrás de otro desde `Y:$580000`, con un límite en `$E80000`. El búfer del sample capturado de SC33 / SC34 (`$600000`) está dentro de esa zona. Hay que moverlo a una zona que el aparato no use. Hay dos candidatas:
- **Zona alta: `$E80000–$FFFFFF`**, por encima del límite de los samples. Son unos 32 s de audio.
- **Zona baja: `$337000–$57FFFF`**, entre las zonas que reserva el aparato y el primer sample.

## Qué hace
- En cada bloque de audio lee una de 24 direcciones, una tras otra:
  - 12 en la zona baja;
  - 10 en la zona alta;
  - 2 de control:
    - `$580000`, el primer sample, que debe cambiar al cambiar de pack;
    - `$840000`, que salió estable en SC35D2.
- Apunta qué direcciones cambian, igual que SC35D2.
- **Prueba de espejo:** en cada visita lee también la dirección situada `$800000` más arriba o más abajo. Si una dirección siempre vale lo mismo que su espejo, es la misma memoria vista dos veces y no se puede usar.

**Aviso:** es la primera vez que se lee por encima de `$8FF000`. Si esa memoria no existiera, el sonido podría pararse. En ese caso, apaga y enciende el aparato y envía SC34. No se escribe nada, así que no queda nada estropeado.

## Prueba
1. Envía SC35D3. Comprueba que el aparato suena con normalidad.
2. Usa el aparato unos minutos:
   - carga un proyecto;
   - **cambia de pack** al menos una vez, si puedes a uno con muchos samples o samples largos;
   - toca algo con delay y reverb altos.
3. Abre `tools/sc32d1_reader.html` en Chrome o Edge y pulsa «Permitir MIDI y escuchar», o abre el `.log` de tu monitor MIDI.
4. Pulsa Synth 1 dos veces. Cuando el **pad 9** esté **verde**, púlsalo.
5. La página muestra el mapa: para cada dirección, si es estable, si cambió alguna vez o si cambia de forma continua, y si es memoria real o un posible espejo. Mándame el texto de «Texto para copiar y mandar».

El control `$580000` debe salir «cambió alguna vez» después de cambiar de pack. Si es así, el método funciona.

## Verificación en emulación
`emu_sc35d3.py` comprueba:
- **En la imagen:** el código de los dos núcleos y el gancho.
- **El núcleo 1:** vueltas por bloque, lista más larga y que no escribe en la zona de la lista.
- **El núcleo 0:**
  - la primera vuelta solo apunta los valores y detecta las direcciones que coinciden con su espejo;
  - una dirección que cambia junto con su espejo sigue marcada como espejo;
  - un cambio posterior se registra;
  - la ventana se cierra cada 1024 bloques;
  - no se escribe ninguna dirección de la memoria externa;
  - la marca solo aparece cuando el núcleo 1 ha respondido.

## Volver atrás
Envía SC34. Mientras no se mueva el búfer, **no grabes samples con SC33 / SC34**.
