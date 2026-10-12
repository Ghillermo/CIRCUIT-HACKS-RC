# SC182D — sonda de persistencia (build de DIAGNÓSTICO)

`circuittracks-4486-SC182D.syx` — SHA-256 `8078051785482baea66d9b2bb92f559b655d2fe4402332beb7e3ec3c80d02c7e`
Imagen de 0x5b324 bytes, CRC 0x466d2269, marca `SC182D`.

Es **SC18.2** (todo igual) con una sonda para decidir cómo guardar nuestros valores en el proyecto. **No es para uso normal.**
Úsala con una **ranura de proyecto de prueba** (o una copia), no con un proyecto importante.

## Qué comprueba
El firmware de stock copia al guardar y cargar el proyecto cuatro bloques enteros (parche del Synth 1, parche del Synth 2, los 4 drums y los
parámetros de proyecto). Algunos bytes de esos bloques no los usa ningún parámetro (valen 0). La sonda escribe una marca en 15 de ellos y
enseña, con LEDs, cuáles sobreviven a:
- **Guardar → apagar → cargar** el proyecto,
- **cambiar de proyecto**,
- **cambiar el parche** de un sinte o de un drum.

La emulación ya ha confirmado que el guardado y la carga de stock llevan esos bytes a ida y vuelta (con el código real, sobre el volcado de RAM).
Lo que **solo se puede ver en el aparato** es si el registro en memoria se escribe entero en la flash y si un cambio de parche los borra.

## Cómo se usa
En la vista **Master FX** (Mixer → Mixer), las filas 2 y 3 (pads 9–24) **muestran la sonda** en lugar del song pointer:

| Pads | Qué es | Marcas |
|---|---|---|
| 9–12 | drums 1–4, primer byte reservado de cada drum | 0xA1–0xA4 |
| 13–16 | drums 1–4, último byte reservado de cada drum | 0xB1–0xB4 |
| 17–18 | Synth 1, bytes 18 y 115 del parche | 0xC1, 0xC2 |
| 19–20 | Synth 2, bytes 18 y 115 del parche | 0xC3, 0xC4 |
| 21–23 | bloque de proyecto, bytes 11, 15 y 30 | 0xD1–0xD3 |
| 24 | se enciende cuando ha saltado algún gancho de carga desde el arranque | — |

Colores de cada pad (provisionales): **brillante** = la marca está; **tenue** = el byte vale 0; **otro color (rojo)** = tiene otro valor
(alguien lo ha reescrito); **apagado** = no se encuentra el bloque.

Los **LEDs de los 8 knobs** son dos contadores en binario desde el arranque: knobs 1–4 = veces que se ha creado un **proyecto nuevo**
(`0x0802F5BC`), knobs 5–8 = veces que se ha **cargado** un proyecto (`0x0802EEFE`). Cuentan hasta 15.

**Shift + pad 8** (el último de la fila 1, el de «apagar todo») **escribe las 15 marcas**; si la primera ya está, las **borra**.
Sin Shift, el pad 8 sigue siendo el de apagar todo.

## Pruebas
**A. Guardar → apagar → cargar**
1. Envía SC182D y carga tu proyecto de prueba. Abre Master FX: los pads 9–23 deben estar tenues (los bytes valen 0).
   **Anota** el estado de los LEDs de los knobs (¿se ha contado una carga al arrancar?).
2. **Shift + pad 8**: los pads 9–23 se encienden.
3. **Guarda el proyecto** como siempre.
4. Apaga y enciende. Abre Master FX y mira los pads; luego **carga el proyecto de prueba** y vuelve a mirar. **Anota qué pads están encendidos**
   (por grupos: drums 9–16, Synth 1 17–18, Synth 2 19–20, proyecto 21–23).
5. Carga **otro** proyecto: los pads deberían quedar tenues (los valores van con el proyecto). Vuelve al de prueba: encendidos otra vez.

**B. Qué borra un cambio de parche** (con las marcas escritas y *sin* guardar)
1. Cambia el **parche del Synth 1** (vista Preset, otro parche): ¿siguen encendidos los pads 17–18? ¿y los del Synth 2 (19–20)?
2. Cambia el **parche / sample de un drum**: ¿siguen los pads 9–16? ¿se borran solo los de ese drum o los de todos?
3. Mueve los knobs de los drums y los de FX; cambia de pattern, tempo, etc.: ¿cambia alguno de los 23 pads?

**C. Contadores**
Con la vista Master FX abierta, anota cuándo suben los contadores (cada uno de estos gestos): arrancar, cargar un proyecto, cambiar de proyecto,
y si existe un gesto de «proyecto nuevo» en tu aparato.

## Qué decidiremos con el resultado
- Si los pads 9–23 sobreviven a guardar / apagar / cargar → se puede guardar por proyecto en esos bytes.
- Si un cambio de parche borra los de los sintes (17–20) o los de los drums (9–16) → hay que proteger la copia o usar solo los bytes que no se borran.
- Los contadores dicen si el gancho de «proyecto cargado» se dispara al arrancar y al cambiar de proyecto (para poner a 0 el estado encendido y el
  song pointer al cargar, y reenviar los valores al DSP).

## Cómo está hecho
- `tools/probe19.py` (ARM, sin DSP): `c_pr_ptr` localiza el byte a partir del objeto de sesión (`[0x200069B4]`) comprobando la vtable de los
  almacenes (0x0805BBAC) y su tamaño antes de tocar nada; solo se escriben los 15 bytes de la tabla `PROBES`.
- Ganchos: slots 0 y 7 de la vista Mixer (encadenados con los manejadores de SC18.2), el `pop.w` final de la carga (`0x0802F5B8`) y el `b.w`
  final del proyecto nuevo (`0x0802F5FA`).
- El contador está en el byte 179 del bloque de Master FX (libre): nibble bajo = proyecto nuevo, alto = carga.
- **No escribe en la flash**: el guardado es el de stock.

## Verificación en emulación
`emu_sc182d.py`: marcas escritas y borradas en los 15 bytes y en ningún otro, colores de los pads, bloque inválido = no se escribe nada,
pad 8 sin Shift y Mixer como antes, ganchos de carga con las funciones reales de stock (nuevo proyecto y carga, el `0x08029A00` final sigue
ejecutándose), ida y vuelta guardar → carga de las marcas, y los LEDs del Mixer normal idénticos a SC18.2.

## Volver atrás
Envía SC18.2 (o SC18.1, SC18, SC17.8). Para dejar limpio el proyecto de prueba: **Shift + pad 8** otra vez (borra las marcas) y guárdalo.
