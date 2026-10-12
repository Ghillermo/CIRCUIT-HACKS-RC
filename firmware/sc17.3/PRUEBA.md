# SC17.3 — Master FX en el botón Mixer de verdad

`circuittracks-4486-SC17.3.syx` — SHA-256 `f4b20c2f9f9292c4bc84f7208528606532731d1b31c561a09e9f2d086d375145`
Imagen de 0x58ee0 bytes, CRC 0x6bd0351, marca `SC17.3`.

## Qué fallaba
El diagnóstico de SC17D lo dejó claro: la memoria estaba bien (pad 17 y 24 encendidos, 240 bytes libres), pero **mi código del botón nunca se ejecutaba** (pads 19 y 20 apagados).
SC17–SC17.2 se enganchaban al botón interno **13**, que no es Mixer. Mixer es el botón **14**: abre la vista con el silencio de pista en los pads 1–8 y los niveles en los knobs.
Shift + Mixer no llega nunca al código de los botones: el firmware de stock lo filtra. Por eso "no hacía nada".

## Uso (lo que pediste al principio)
- **Mixer** desde otra vista: Mixer normal.
- **Mixer otra vez** estando en el Mixer: vista **Master FX**.
- **Mixer otra vez**: vuelta al Mixer normal.
- Master FX, como en SC17:
  - pads 1–6 = Gater, Auto-Filter LP, Auto-Filter HP, Digitise, Phaser y Vinyl;
  - mantener = activo mientras lo mantienes; Shift + pad = fijo;
  - knobs 1–4 = parámetros del efecto seleccionado.
- En Master FX, los knobs 5–8 no hacen nada (en el Mixer normal siguen siendo niveles).
- Entrada de línea v2 como en SC17.1 (Shift + pads 25–29 en Preset).

## Verificación en emulación
- Botón 14:
  - entra en el Mixer y conmuta Master FX;
  - el pad 1 por la ruta real del controlador activa el Gater sin silenciar la pista;
  - con Master FX apagado, silencia como en stock;
  - el botón 13 queda en stock.
- DSP de núcleo completo y entrada de línea (5 modos, ×2): todo pasa. SC17–SC17.2 y SC17D se siguen generando idénticos.

## Si no funciona
Envía `firmware/sc173d/circuittracks-4486-SC173D.syx`. Es lo mismo con el panel de diagnóstico de SC17D (Preset + Shift):
- pad 19 = se conmutó Master FX estando en el Mixer;
- pad 20 = se entró en el Mixer desde otra vista.

## Volver atrás
Envía SC17.1 o SC16.1.
