# SC48.1 / Beta 3.38 = SC48 / Beta 3.37 + el metrónomo solo en el cue

`firmware/sc48.1/circuittracks-4486-SC48.1.syx` — SHA-256 `e441b13242871add9fe2d3af2244990b0aa2afc57aa2dd27cd66aebfb5dc0bdd`, marca `SC48.1`.
`firmware/b3.38/circuittracks-4486-B3.38.syx` — SHA-256 `5260c452f119c8cdf521f469ddfa4b511a4eebdb8f0a40021bf7a5220db6e90c`, marca `B3.38` (**Beta 3.38**, el mismo código).

El usuario (2026-10-27): «Add metronome on Cue listen only (when metronome and Cue listen are enabled)». Con el modo cue del Mixer encendido, el clic
del metrónomo (y el de la cuenta atrás) suena solo por la salida derecha (el cue); la izquierda (la mezcla) sale sin clic. Sin el modo cue, como
siempre. El clic lo hace el DSP al final de cada bloque, sobre las dos salidas: hace falta tocar el núcleo 0 (`tools/cueclk.py`) y, para que
quepa, `dsp56.use_shortmsb()` (18 instrucciones del código propio en su forma de una palabra, el mismo valor).

## Qué probar
1. **Sin modo cue:** el metrónomo (Shift + Clear: verde) suena por las dos salidas como en la Beta 3.37; la cuenta atrás igual.
2. **Modo cue:** Mixer, página de panorama (Octave ▼), Shift + knob a la derecha (Octave ▼ rosa). Con Play y el metrónomo: el clic **solo por la
   salida derecha**; por la izquierda, la mezcla sin clic. Con cascos en el jack de salida, el clic solo en un lado.
3. La cuenta atrás (Shift + Clear: magenta / cian, Record armado, Play) en el modo cue: los 4 clics solo por la derecha.
4. Apagar el modo cue (Shift + knob a la izquierda) con el metrónomo sonando: el clic vuelve a las dos salidas (en unos milisegundos).
5. **Todo lo demás** del sonido como en la Beta 3.37 (el programa del DSP se ha compactado): sintes propios (oscilador, FM, muestra, granular),
   drums (con sus knobs nuevos), el sample capturado de Master FX, Master FX.

## Verificación en emulación
- `emu_cueclk_dsp.py` frente a SC48 / Beta 3.37: el programa (la parte de stock solo cambia en el clic y en los destinos de los saltos); el núcleo 0
  entero con el tráfico del motor, FM y modo muestra: X e Y iguales en cuatro puntos; con el clic: sin la bandera igual que SC48 palabra por palabra;
  con la bandera, en el bloque del clic y en su cola, L = sin clic y R = con clic; el bloque del anillo de salida en un límite de 64 palabras.
- `emu_cueclk.py`: la cabeza de la cadena del servicio del DSP escribe la bandera al cambiar el modo cue y cada 250 ticks.
- `emu_cueprev`, `emu_stripg_dsp`, `emu_lfoscan_dsp`, `emu_blep_dsp` sobre SC48.1: bien; `emu_sc44_1_dsp` (con la base de la captura en su forma
  corta) y `emu_countin`: lo mismo que SC48 (fallos por diseño, anteriores).
