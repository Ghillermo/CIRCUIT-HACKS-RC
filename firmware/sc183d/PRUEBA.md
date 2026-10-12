# SC183D — sonda de persistencia v2 (build de DIAGNÓSTICO)

`circuittracks-4486-SC183D.syx` — SHA-256 `d85302f9f87ebeaa23dd7986b2c08fe5944faa7b5dbd56150fdd976a8505329f`
Imagen de 0x5b41c bytes, CRC 0xb35c90dd, marca `SC183D`.

Es **SC18.3** (todo igual) con una sonda mejorada. Sustituye a SC182D, cuyos resultados fueron ambiguos: con una marca fija por pad no se puede
distinguir si un byte viene del proyecto guardado en la tarjeta SD o se ha quedado en la RAM, ni qué «versión» de la marca es.
**No es para uso normal.** Úsala con **ranuras de proyecto de prueba**.

## Qué cambia respecto a SC182D
- Cada escritura pone un **número de generación** (1, 2, 3 … hasta 255) en los 15 bytes reservados. Así se ve **de qué escritura es** cada byte.
- Se puede mirar **el almacén vivo** o **el registro de sesión** (la imagen en RAM que el firmware guarda y carga).
- Los **knobs** muestran en binario el valor exacto de un byte elegido.
- Los contadores incluyen los **guardados**.

## Manejo (vista Master FX: Mixer → Mixer)
Las filas 2 y 3 (pads 9–24) son la sonda; la fila de abajo (pads 25–32) son los contadores. Todo con **Shift**:

| Gesto | Efecto |
|---|---|
| **Shift + pad 8** | escribe la generación siguiente (+1) en los 15 bytes vivos |
| **Shift + pad 7** | escribe 0 en los 15 bytes vivos (la generación no cambia) |
| **Shift + pad 9–23** | elige ese byte: su pad se pone de color «selección» y los **8 knobs muestran su valor en binario** (knob 1 = bit 0, knob 8 = bit 7) |
| **Shift + pad 24** | cambia el origen de lo que se ve: almacén vivo (pad 24 tenue) / registro de sesión (pad 24 brillante) |

Pads 9–23 (los no elegidos): **brillante** = el byte vale la generación actual; **rojo** = otro valor distinto de 0 (una generación anterior, o de otra
procedencia); **tenue** = vale 0; **apagado** = no se encuentra el bloque.
La generación actual vuelve a 0 al encender: justo después de arrancar, un byte con valor ≠ 0 sale en rojo y el número exacto se lee en los knobs.

Qué es cada pad: 9–12 drums 1–4 (primer byte reservado), 13–16 drums 1–4 (último), 17–18 Synth 1, 19–20 Synth 2, 21–23 bloque de proyecto.

**Contadores** (desde el encendido, binario, pad 25 = bit 0): pads 25–26 = **proyectos nuevos** (0–3), pads 27–29 = **cargas** (0–7), pads 30–32 = **guardados** (0–7).
Ejemplo: pads 27 y 30 encendidos = 1 carga y 1 guardado.

## Procedimiento sugerido (usa dos ranuras de prueba, A y B)
Anota **qué pads y qué valor en los knobs** ves en cada paso (con el origen «almacén vivo»; cuando se diga, también con «registro»).

1. Enciende, carga la ranura **A**. Entra en Master FX. Anota los pads y los contadores (¿cuántas cargas al arrancar?).
2. **Shift + pad 8** (generación 1). Los pads deben salir brillantes.
3. **Guarda** el proyecto en la ranura **A** como siempre. Mira los contadores (un guardado).
4. **Shift + pad 8** otra vez (generación 2) **sin guardar**. Cambia al origen «registro» (**Shift + pad 24**): ¿qué se ve? (el registro debe seguir con la
   generación 1 hasta el siguiente guardado). Elige un byte (p. ej. **Shift + pad 9**) y anota el valor de los knobs en cada origen.
5. **Apaga del todo** (interruptor, **espera 10 segundos**) y enciende. Carga la ranura **A**. Anota los pads (en rojo si ≠ 0) y el valor de los knobs de
   un byte de cada grupo (drums, Synth 1, Synth 2, proyecto). **Debería ser la generación 1** si todo lo guardado en la SD vuelve, y **0** si no.
6. Carga la ranura **B** (otro proyecto): ¿qué valen? Vuelve a **A**: ¿qué valen?
7. **Guarda A como copia en una ranura nueva (C)** y cárgala: ¿valen lo mismo que A?
8. Crea un **proyecto nuevo**: ¿qué pasa con los drums/proyecto (pads 9–16 y 21–23) y con los sintes (17–20)? ¿Cuánto marcan los contadores?
9. Con generación escrita y sin guardar: **cambia el parche** del Synth 1, el del Synth 2 y el de un drum. ¿Cambia algún byte?
10. Vuelve a la ranura **A** sin guardar lo anterior y repite la comparación entre **vivo** y **registro** después de cargarla.

11. **Repite lo que viste con SC182D**: escribe (generación N), **borra** con Shift + pad 7 (todo tenue), **guarda**, apaga del todo, enciende y carga la
    ranura. Con SC182D salieron encendidos otra vez los pads 9–23. Aquí el valor de los knobs dirá **de qué generación** son (¿N, anterior, o 0?).

Nota: el pad 24 ahora indica el origen de lo que se ve (tenue = almacén vivo). **Tras el arranque debe verse tenue**; si lo ves siempre encendido, avísame.

## Qué decidimos con esto
- **Persistencia real**: paso 5. Si tras apagar del todo vuelve la generación 1, los bytes reservados se guardan en el proyecto de la tarjeta SD.
- **Por proyecto**: pasos 6–7 (cada proyecto tiene sus bytes y la copia los arrastra).
- **Qué los borra**: pasos 8–9 (proyecto nuevo, cambio de parche).
- **Orden de los eventos**: contadores y registro vs. vivo (qué se carga y cuándo).

## Cómo está hecho
- `tools/probe20.py` (ARM, sin DSP). Mismos 15 bytes que SC182D, comprobando antes de escribir la vtable (0x0805BBAC) y el tamaño del almacén.
  Origen «registro»: `[0x2003D71C + 0x14]` + el desplazamiento del bloque (sinte 1 0x26D14, sinte 2 0x26E68, drums 0x26FBC, proyecto 0x26FE8) tras
  comprobar la vtable del gestor de sesión (0x08059CD0) y que el búfer está en RAM.
- Estado: 4 bytes extra del bloque de Master FX (generación, byte elegido, origen, contadores). La reserva de RAM pasa de 220 a 224 bytes (margen 16).
- Ganchos: slots 0 y 7 de la vista Mixer, el `pop.w` final de la carga (`0x0802F5B8`), el `b.w` final de proyecto nuevo (`0x0802F5FA`) y el `bl` al
  guardado de stock (`0x0802FE5E`).
- **No escribe en la tarjeta**: el guardado es el de stock.

## Volver atrás
Envía SC18.3 (o SC18.2). Para dejar limpia una ranura de prueba: **Shift + pad 7** y guárdala.
