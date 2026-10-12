# SC23.5 — SC23.4 + correcciones tras probar (notas que no siempre sonaban, cabezal del song pointer, pad 8, K8, Clear, botón Save)

`circuittracks-4486-SC23.5.syx` — SHA-256 `aa0b95b260ee31d76d7b03dcdcc7e9e0f6470f29f32c1333737295b6cc99782e`
Marca `SC23.5`. Reserva: SC23.4. Todo lo de abajo está probado en emulación; **nada de esto está probado en el aparato**.

## 1. Notas que no siempre se disparaban (modos OSC / VCA-VCF)
Hipótesis (no demostrada): el DSP lee el buzón de cada voz **una vez por bloque de audio** y solo ve la **última palabra escrita**; con una marca de 1 bit, dos escrituras entre dos lecturas **no se notan** y se pierden las dos. Un golpe de nota son 4 mensajes (el encendido del modo, 28), así que se perdían al azar: valores que nunca llegaban (sonido «errático») y puertas que no abrían (con los defaults neutros un VCA sin puerta no suena).

Remedios (los tres a la vez):
- **Como mucho un mensaje por voz cada 2 ms** (`vcf21.use_ratelimit()`, `RATE_MS`).
- **Latido:** cada ~8 ms el ARM vuelve a marcar ACT / NOTE / VEL / GATE; cada ~1 s, con el modo encendido, **todos los valores**. La velocidad inicial es 100 (una velocidad 0 con VCA neutro = silencio).
- **DSP** (`vcf21_dsp.use_gatefix()`): puerta alta con la envolvente parada = disparo.

Prueba: modo VCA-VCF (pad 29) y OSC (pad 28) encendidos en MIDI 1; toca notas del secuenciador y a mano, 30–50 veces, con y sin entrada externa: **¿suenan todas?** Apaga y enciende el modo (pad 28 / 29) varias veces: los valores del oscilador deben seguir ahí.
**Si el fallo persiste, dímelo con el patrón (cada cuántas notas, si depende del modo, de la velocidad, del tempo):** la cadencia real de bloques frente a ticks del servicio no está medida; se puede subir `RATE_MS` (hasta 16) o hay otra causa.

## 2. Master FX
- **Song pointer = cabezal de 16 pasos:** el pad del paso que suena se enciende en **blanco**, de 1 a 16 linealmente (como el paso que suena en un secuenciador). Se apaga si el secuenciador lleva parado > 2 s.
- **Pad 8** = igual que el bypass de FX (pad 25 de la vista FX): ya no parpadea.
- Los demás cambios de SC23.4 (tramo ordenado, salto pasado el fin, LED del salto, pad 7 se suelta) siguen igual.

## 3. Drums
- **K8 (bitcrusher ← 0 → distorsión):** brillo mínimo en el centro (sin efecto), crece hacia la izquierda (bitcrush) o la derecha (distorsión).
  *Pendiente de aclarar:* los demás knobs bidireccionales (K1 tono, K5 EQ…) siguen con el LED de stock.
- **Clear + knob:** borra **las dos capas** del knob (la normal y la de Shift) a la vez, en VCA-VCF, OSC y drums. Con Shift el botón Clear no hace nada (por eso se borran juntas).

## 4. Editor de CC
- El botón **Save** de la fila superior (entre Duplicate y Projects, LED 57) parpadea con el pad Save en el paso guardar. Si no se enciende, dímelo: el LED 57 es una deducción de la tabla de LEDs.

## Sin hacer / sin aclarar
- «Solo los knobs permanecen en la vista Shift, sin que Shift sea sticky»: no está claro qué pasa exactamente; necesito saber en qué vista y con qué secuencia de botones.
- El secuenciador no automatiza los parámetros de OSC / VCA-VCF (se sigue mandando CC).

## Pruebas de emulación
`emu_sc23_5.py` (huecos ≥ 2 ms con ticks de 1 ms, encendido completo en ~150 ms, latido, refresco, sello sin vuelta, Clear en las dos capas), `emu_sc23_5_gfx.py`, `emu_sc23_5_drums.py`, `emu_sc23_5_ed.py`, `emu_sc23_5_dsp.py` (puerta, seno, instrucciones por bloque), y `emu_sc23_3.py` / `emu_sc23_3_fx.py` / `emu_sc23_4_notes.py` sobre esta imagen.
