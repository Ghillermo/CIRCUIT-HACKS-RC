# SC22 — SC21.4 + efectos ring mod / comb / chorus, cadena VCA → FX → filtro y envíos bipolares

`circuittracks-4486-SC22.syx` — SHA-256 `a6d0f25669d578a19bf73d318dd66fa69495eb8ae596b7ae5f76d4f400586fa8`
Imagen de 0x5d844 bytes, marca `SC22`. Es SC21.4 con el programa del DSP ampliado hasta `P:$3FFF` (la RAM de programa es de 16 K palabras: resultado de SC21D). Si falla, vuelve a SC21.4 o SC21.2.

## Qué cambia en el modo VCF / VCA / FX de las pistas MIDI (pad 26 de la vista Preset de MIDI 1 / 2)

### 1. Cadena de señal: VCA → FX → filtro
Antes era filtro → FX → VCA. Ahora la entrada pasa primero por el **VCA** (con la saturación de GAIN > 64), después por el **efecto** y al final por el **filtro**. Consecuencias que se oyen: los efectos reaccionan a la envolvente / al tremolo (la saturación muerde más en el ataque), y el filtro (con su resonancia) actúa sobre la señal ya distorsionada.

### 2. Tres efectos nuevos (Shift + K8 = tipo; K8 = cantidad; Shift + K7 = parámetro)
| Tipo | Efecto | Cantidad (K8) | Parámetro (Shift + K7) |
|---|---|---|---|
| 0-3 | soft / hard / fold / wavefold (como antes) | drive | umbral / pliegue |
| 4 | **ring mod** | profundidad (0 = sin efecto) | frecuencia de la portadora |
| 5 | **comb** (filtro de peine con realimentación) | realimentación | tono: de grave (0) a agudo (127) |
| 6 | **chorus** | mezcla (hasta 50 % húmedo) | velocidad del LFO |

El LED de Shift + K8 enseña el tipo por brillo (siete pasos). El tipo da la vuelta en 7.

### 3. K3 y Shift + K3 bipolares
- **K3** (envolvente → VCA) y **Shift + K3** (LFO → VCA, tremolo) son ahora **bipolares**: en el centro (valor 0, el de por defecto) no hay envío; a la derecha el envío es positivo, a la izquierda negativo.
  - Envolvente negativa: la envolvente **cierra** el VCA (la ganancia baja con la envolvente; nunca invierte la señal, queda como mínimo en 0).
  - LFO negativo: el tremolo con la fase invertida.
- K4 y Shift + K4 (envolvente / LFO → filtro) ya eran bipolares. El LED de K3 / Shift + K3 muestra el valor absoluto, como los de K4.
- A la derecha del todo (63) el envío vale lo mismo que antes el valor 126.

### 4. Arreglo
SC21.4 guardaba `r2` encima del puntero del retorno (`RBUF`) cuando se usaba un filtro de 24 dB sobre un retorno de FX (entrada de las tiras 3 / 4 del Setup en reverb / delay): ese caso podía dar un retorno estropeado. SC22 mueve el área de guardado (`X:$38C0`).

El estado guardado lleva la firma 0xA9: **al flashear sobre SC21.x el estado del modo se reinicia** (cambian los números de los efectos y los envíos).

## Prueba (volumen bajo)
1. MIDI 1 → Preset → pad 26 (azul): modo encendido, con una entrada de línea (o un synth por el Setup) sonando.
2. **Ring mod**: Shift + K8 hasta el tipo 4; sube K8 (profundidad) y mueve Shift + K7: debe sonar metálico / campanas; con K8 a 0 no cambia nada.
3. **Comb**: tipo 5; K8 = realimentación, Shift + K7 = tono (un sonido «resonante» con altura). Con K8 alto y señal continua puede zumbar.
4. **Chorus**: tipo 6; K8 sube la mezcla, Shift + K7 la velocidad del vibrato.
5. **Orden**: tipo 1 (hard) con K8 alto y el filtro en paso bajo (Shift + K5 = tipo 1, K5 = corte bajo): ahora el filtro suaviza los armónicos de la distorsión.
6. **K3 / Shift + K3**: con notas en la pista (gate), K3 a la derecha abre el VCA con la envolvente; a la izquierda la cierra; Shift + K3 a ambos lados da el tremolo en una fase u otra. En el centro, sin efecto.
7. Comprueba que la entrada limpia sigue pasando al sinte y que con el modo apagado todo es de stock.

## Notas técnicas
- `build_sc22.py`: `build_sc16.CODE_P_END = 0x4000`, `vcf21_dsp.PLIMIT = 0x4000`, `FXMORE`, `BISEND`, `vcf21.FXTYPE_N = 7`, máscara bipolar con ENVA (código 15) y LFOV (código 12). El programa del DSP termina en `P:$3915`.
- Estado por voz de los FX en `X:$3840 + 48 t` (ring: seno / coseno; comb: índice de escritura; chorus: índice, fase del LFO, retardo, paso, base); búfer del comb en `Y:$3400 + 256 t`, del chorus en `Y:$3600 + 512 t`.
- Pruebas: `tools/emu_sc22_dsp.py` (los tres efectos bit a bit con sus estados y búferes, el orden de la cadena, K3 bipolar, los registros `r2` / `r3` / `r4` / `m2` / `m4` restaurados) y `tools/emu_sc22.py`.
