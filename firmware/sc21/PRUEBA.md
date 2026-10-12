# SC21 — modo VCF / VCA / FX reordenado, con tipos de filtro, efectos y ganancia

`circuittracks-4486-SC21.syx` — SHA-256 `83d993e0dbba49296710e938ff2d30a395013512a020a234b63cc4387a0de2ba`
Imagen de 0x5d2c8 bytes, CRC 0x3be5c285, marca `SC21`. Es SC20.1 con el modo VCF / VCA rehecho; si falla, vuelve a SC20.1 (`firmware/sc20.1/`) o a SC20, y la última versión segura confirmada es SC17.7.

## Mandos (los 8 knobs de MIDI 1 / MIDI 2 con el modo encendido; los LEDs enseñan el valor con el brillo)

| Knob | Normal | Con Shift |
|---|---|---|
| **K1** OSC | Ataque | Sustain |
| **K2** OSC MOD | Release | Decay |
| **K3** Amp ENV | Envolvente → amp (0 … 127; 127 = la envolvente abre el VCA hasta la velocidad) | LFO → amp (trémolo) |
| **K4** F.ENV | Envolvente → filtro (bipolar) | LFO → filtro (bipolar) |
| **K5** Filter | Filtro bipolar (izquierda = paso bajo, derecha = paso alto, centro = sin filtro) | Tipo de filtro (un paso por giro): DJ, paso banda, notch, tilt EQ |
| **K6** Reso | Resonancia | **Gain** (VCA bias): 64 = ganancia ×1, a la izquierda hasta 0 = VCA cerrado, a la derecha hasta +18 dB con saturación suave |
| **K7** Modulation | Velocidad del LFO (solo rampa inversa) | **FX mod**: el parámetro propio del efecto (ver abajo) |
| **K8** FX | Cantidad del efecto (0 = apagado) | Tipo de efecto (un paso por giro): suave, dura, plegado, wavefold |

- **VCA**: abertura = Gain + (envolvente → amp) × envolvente × velocidad, por el trémolo; con Gain a 0 y sin envolvente ni LFO el VCA está cerrado. Con Gain = 64, sin envolvente ni trémolo el VCA no actúa (bypass exacto). Por encima de 64 la salida pasa por una saturación suave.
- **Siempre activos**: seguimiento de la nota → corte del filtro y velocidad → apertura del VCA; la nota inicial es 60 (sin desplazamiento).
- **Filtro**: en DJ el centro de K5 es bypass; en paso banda / notch K5 es la frecuencia de corte; en tilt EQ el corte es fijo y K5 elige el lado (izquierda: graves arriba, derecha: agudos arriba). La envolvente y el LFO mueven el corte en todos los tipos.
- **FX mod** según el tipo: suave = techo antes de la curva; dura = nivel de recorte; plegado = punto de plegado; wavefold = bias (64 = centro) con pliegue en 0,5. (El pedido «cuánto mueve el LFO la cantidad» no está: el FX mod es el parámetro del efecto.)

## Valores por defecto
Filtro al centro, resonancia 0, envolvente y LFO → filtro 0, ataque 0, decay 40, sustain 100, release 40, FX cantidad 0, Gain 64, velocidad del LFO 40, trémolo 0, tipo de efecto = suave, FX mod 64, envolvente → amp 0, tipo de filtro = DJ. Con todos ellos el modo es un bypass exacto.

## Pendiente de la fase 2 (necesita más espacio de programa del DSP; hoy sobra 1 palabra hasta `$3800`)
Comb, ring mod, chorus / delay / reverb como efectos y como tipos de filtro. Un build de diagnóstico (SC21D) debe confirmar si hay RAM de programa por encima de `$3800`.

## Estado guardado
Los valores siguen en la cola de los ajustes globales (no por proyecto), con otra firma que SC20.1: **al flashear SC21 sobre SC20 / SC20.1 el estado se reinicia** (valores por defecto, modos apagados), porque los valores de antes significaban otras cosas.

## Pruebas en el aparato (proyecto de prueba, volumen bajo)
1. Arranca como SC20.1. MIDI 1 → Preset → pad 26 (azul): modo encendido.
2. **Bypass**: sin tocar nada la entrada suena igual.
3. **Reparto**: gira cada knob con y sin Shift y comprueba la tabla de arriba (los LEDs cambian de brillo).
4. **Filtro**: K5 bipolar; Shift + K5 cambia a paso banda, notch y tilt (el LED cambia de brillo por paso).
5. **Gain / VCA**: Shift + K6 a 0: silencio; a 64: normal; hacia la derecha: más nivel y saturación. K3 a la derecha con notas de la pista: la envolvente abre el VCA (con Gain a 0 solo suena con la nota).
6. **FX**: K8 sube la cantidad; Shift + K8 cambia de efecto; Shift + K7 mueve su parámetro.
7. **LFO**: K7 (rampa inversa) con K4 Shift (LFO → filtro) o K3 Shift (trémolo).
