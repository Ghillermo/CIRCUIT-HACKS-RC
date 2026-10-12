# SC17.5 — delay y reverb como fuente del sinte + teclas de la vista FX

`circuittracks-4486-SC17.5.syx` — SHA-256 `fbb1818de5a71937cc1db30c50ca544500292131f686eaa400c20c1099a28002`
Imagen de 0x59120 bytes, CRC 0xaf0f59b9, marca `SC17.5`.

Es **SC17.4** (Mixer → Mixer = Master FX, LEDs de knobs, entrada de línea v2) más dos cosas nuevas.

## 1. Delay y reverb como entrada externa del sinte (pads 30 y 31)
En la vista **Preset** del Synth 1 o 2, manteniendo **Shift**, fila 4:

| Pad | Modo |
|---|---|
| 25 | Noise (stock) |
| 26 | Entrada 1 |
| 27 | Entrada 2 |
| 28 | Entrada 1 (el otro signo) |
| 29 | Entrada 2 (el otro signo) |
| **30** | **Retorno del delay** |
| **31** | **Retorno de la reverb** |

- El sinte oye la salida del delay (o de la reverb) en lugar del noise, igual que con la entrada de línea: nivel de noise del patch (CC 56 = 127 para el máximo), filtro, envolventes y FX. Solo suena mientras tocas notas.
- La señal es la suma L + R de la salida del efecto, tal como sale del efecto (con la saturación del DSP si se pasa).
- Llega con **un bloque de retraso** (32 muestras, unos 0,7 ms).
- Hace falta que el delay o la reverb tengan señal: sube los envíos de alguna pista (vista FX, ver abajo) y toca algo, o usa la entrada de línea.
- Se puede realimentar: un sinte con sus propios ecos (envío del propio sinte al delay). La ganancia del lazo queda muy por debajo de 1 con los niveles normales.
- Mientras mantienes Shift, los 7 pads muestran el modo (el elegido brillante). No se guarda: al encender, Noise.
- Si queda bajo de nivel, dímelo: se puede añadir ganancia como en la entrada de línea v2.

## 2. Teclas de la vista FX
Solo con la vista **FX** abierta (botón FX). En cualquier otra vista, los botones hacen lo de siempre.

| Botón | Qué hace |
|---|---|
| **Octave ▲** | los 8 knobs pasan a ser los **envíos de delay** de las 8 pistas |
| **Octave ▼** | los 8 knobs pasan a ser los **envíos de reverb** |
| **botón 16 (1-16 / 17-32)** | **reset**: ver abajo |

Octave ▲/▼ eligen la misma página que el firmware elegía al tocar un pad de delay o de reverb, pero sin cambiar el preset.

**Reset** (botón 16, estando en la vista FX):
- los 16 envíos (8 de delay + 8 de reverb) a 0;
- filtro master al centro (valor 64 = sin filtro); la resonancia no se toca;
- Master FX apagado: pads mantenidos o fijos del Gater y el Auto-Filter de la vista FX, y los de la vista Master FX.

Los knobs de las dos páginas siguen coherentes: al girar uno después del reset, empieza en 0.
Los envíos y el filtro master son parámetros del proyecto: si guardas después, se guardan a 0.
No toca los parámetros del delay y de la reverb (tiempo, feedback, decay…) ni el resto del master (compresor, ganancia).

## Duda que me gustaría confirmar con el aparato
**¿El botón «1-16 / 17-32» es el que dispara el reset?** Lo identifiqué por el código (id 16 del firmware; es el que conmuta la página de pasos). Si no lo es, dime qué botón es y lo cambio.

## Cómo está hecho
- **DSP:** el programa del núcleo 0 ya tiene un gancho en el retorno de FX (P:$D21, de SC10). Ahora salta antes a `fx_cap`, que, solo si algún sinte está en el modo 5 o 6, copia L + R de la salida del delay (Y:$9C0) y de la reverb (Y:$880) a Y:$3A80 y Y:$3AC0. Con los modos 0–4 solo gasta 7 instrucciones por bloque. `l3_hook` (en P:$9C3) es el `l2_hook` de la entrada de línea con una rama más: en los modos 5 y 6 la voz lee esos búferes.
- **ARM:** `tools/fxkeys.py`. Tres ganchos en el manejador de botones (casos 19, 20 y 16/17): si la vista activa es la FX, cambian la página (el store `[vista+0x20]`) o hacen el reset; si no, ejecutan las dos instrucciones desplazadas y siguen con el código de stock. El reset fija los parámetros por el mismo camino que usa el MIDI para los parámetros de proyecto (`0x08034D92`), así que el almacén, la pantalla y el DSP los siguen.
- **Memoria:** RAM del ARM sin cambios (196 B bajo el heap). DSP: P:$2C54–$2D06 (código), Y:$3A80–$3ADF (búferes de captura).

## Verificación en emulación
- `emu_sc17_5_dsp.py` (núcleo DSP completo; el delay y la reverb emulados no suenan, así que se sustituyen por patrones conocidos en Y:$9C0 / Y:$880):
  - los búferes capturados = L + R saturada de cada salida, en cada bloque;
  - mezcla de la voz en modo 5 / 6 = retorno × nivel de noise (error 0), en los dos sintes, y el otro sinte no cambia;
  - modos 0–4 y bloque de salida final **idénticos a SC17.4** (24 bloques); sin captura no hay ni un acceso nuevo a memoria;
  - con captura, solo Y:$3A80–$3ADF; coste +7 instrucciones por bloque sin captura y +271 con ella (de unas 55 000).
- `emu_sc17_5.py` (ARM, por la ruta real del controlador `0x08033320`):
  - Octave ▲ / ▼ → página delay / reverb, y el knob va a la página correcta;
  - en pistas, Mixer, Master FX, Preset y Patterns los botones 19, 20, 16 y 17 dejan todo **exactamente como SC17.4**; en la vista FX el 17 también;
  - reset: 16 envíos a 0 y filtro 64, el resto de parámetros (resonancia incluida) sin tocar, Master FX apagado; el DSP recibe los 16 envíos a 0 y X:$CF = $400000, y X:$D0 conserva su valor;
  - Shift + pads 25–31: modos 0–6, LEDs, y 32 sin cambios.
- `emu_sc17.py`, `emu_sc17_core.py`: pasan. SC17.4 y todos los anteriores se siguen generando idénticos.

## Pruebas en el aparato
1. Envía SC17.5. Comprueba que arranca y que Mixer, Master FX, FX y la entrada de línea siguen como en SC17.4.
2. FX → Octave ▲: gira un knob; debe moverse el envío de delay de esa pista. Octave ▼: envío de reverb. Comprueba que no se cambia ningún preset.
3. FX → mueve varios envíos y activa un pad de Master FX fijo (Shift + pad) → botón 16: envíos a 0, Master FX apagado, filtro master al centro.
4. Otra vista (Mixer, Preset…) → botones Octave y 16: lo de siempre.
5. Synth 1 → Preset → Shift + pad 30. Sube el noise del patch (CC 56 = 127). Pon el delay con envíos de drums o de la entrada de línea y toca una nota: el sinte debe filtrar y dar forma de envolvente a los ecos. Igual con la reverb y el pad 31.
6. Dime qué tal el nivel, y si el botón 16 era el bueno.

## Volver atrás
Envía SC17.4 (o SC17.3).
