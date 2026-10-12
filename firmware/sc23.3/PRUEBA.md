# SC23.3 — SC23.2 + estado neutro (gate básico), Clear + knob, LEDs de Octave y de limpieza del editor, tope de envíos con «Efectos a line in»

`circuittracks-4486-SC23.3.syx` — SHA-256 `7d30f1b6d0a113af374b5409cd4280d7aa335b087319c096346f9f9ba4426b37`
Imagen de 0x5e9b4 bytes, marca `SC23.3`. **Los valores guardados de SC23.x del modo VCA-VCF / OSC se reinician** al flashear (otra firma). Si falla, vuelve a SC23.2 (o SC23.1).

## 1. Estado neutro: gate básico
Valores por defecto (los que tiene el modo al empezar y a los que vuelve Clear + knob):

| Página A (VCA-VCF) | Valor | Página B (OSC) | Valor |
|---|---|---|---|
| FILT / RES | 0 (abierto) / 0 | TUNE / FINE | 0 / 0 |
| ENVF / LFOF | 0 / 0 | WAVE | 0 = **seno** |
| ATK / DEC / REL | 0 / 0 / 0 | SHAPE | 50 (centro) |
| SUS | 127 | LFOP / ENVP / ENVW / LFOW / ENVM / LFOM | 0 |
| GAIN | 0 (cerrado sin envolvente) | | |
| ENVA (envolvente → VCA) | **+63** (al máximo, escalado por la velocity) | | |
| LFOV / FXAMT | 0 / 0 (sin tremolo, sin efecto) | | |
| LRATE / FXTYPE / FXMOD / FTYPE | 40 / 0 / 64 / 0 | | |

Resultado: **al pulsar una tecla de MIDI 1 / 2 se abre el sonido (× velocity) y al soltarla se cierra, sin modificarlo**; la liberación con REL 0 dura ~2 ms. El oscilador por defecto es un seno puro a la altura de la nota (A4 = 440 Hz), sin modulación. El pad 27 (fuente) solo cambia entre entrada de línea y oscilador; ya no toca GAIN / ENVA.
- Prueba: modo encendido (pad 29), entrada de línea sonando: silencio sin tecla, la señal pasa mientras la tecla está pulsada. Pad 27: lo mismo con el oscilador (seno). Notas del secuenciador y de los pads: igual aunque otra vista esté en pantalla. Después mueve los knobs uno a uno para localizar qué hace sonar mal al oscilador.

## 2. Clear + knob
Con el modo VCA-VCF / OSC encendido, **mantén Clear y mueve un knob** (cualquier sentido, también con Shift y en la página B): su valor vuelve al por defecto de la tabla anterior y el knob se ve **rojo mientras Clear esté pulsado**; al soltar, vuelve su color normal. Con el modo apagado Clear es el de stock.

## 3. Editor de CC (pad 25)
- **LEDs de Octave:** en cuanto salen los números se enciende Octave ▼ (hay campo siguiente); en los campos intermedios, ▼ y ▲; en el último, solo ▲ (con el color del campo).
- **LEDs sucios:** al guardar, descartar o salir del editor ya no quedan pads encendidos de los números en la vista Preset (se limpian al cuadro siguiente, y a la vez al salir).

## 4. Envíos de las tiras con «Efectos a line in»
Si el Setup tiene activo **reverb → tira 3** (pad 22) y/o **delay → tira 4** (pad 23), en la vista FX los knobs **K3 (MIDI 1)** / **K4 (MIDI 2)**, en las dos páginas (delay y reverb), tienen **tope 63** y **medio paso por clic** (dos clics = +1). Un envío que estuviera por encima baja a 63 al primer toque. Los demás knobs, Shift + knob (parámetros del efecto) y Clear son los de siempre.
- Prueba: activar el retorno de reverb a la tira 3, vista FX, K3: sube más despacio y se para en 63. Sin el retorno, K3 llega a 127 como siempre.

## No incluido (pendiente)
- El secuenciador automatizando los parámetros de OSC / VCA-VCF en lugar de mandar CC (requiere estudiar el emisor de CC de los macros y la grabación de automatización; ver `docs/NOTAS.md`).

## Pruebas de emulación
`tools/emu_sc23_3.py` (batería ARM: pads, knobs, defaults neutros, Clear + knob, notas con cualquier vista en pantalla), `emu_sc23_3_ed.py` (LEDs de Octave y limpieza de pads), `emu_sc23_3_fx.py` (tope y medio paso), `emu_sc23_3_dsp.py` (gate de la entrada de línea, seno del oscilador por todas las notas, liberación, coste), y `emu_sc23_1_ed.py` sobre esta imagen.
