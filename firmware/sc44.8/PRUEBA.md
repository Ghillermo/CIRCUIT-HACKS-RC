# SC44.8 / Beta 3.5 = SC44.7 + LFO a tempo

`firmware/sc44.8/circuittracks-4486-SC44.8.syx` — SHA-256 `82c867aeed40d32e432ac5b74aaed46577e87f401f4d10068463aed514b4d24b`, marca `SC44.8`.
`firmware/b3.5/circuittracks-4486-B3.5.syx` — SHA-256 `569691e22a285604ebb776464c1fff369358229839287d6c6dc8cff5dd1ad976`, marca `B3.5` (**Beta 3.5**, el mismo código).

El usuario (2026-10-19): «en los lfo rate, hazlo bipolar (manten 0 dim y lados bright) hacia la derecha, lfo libre, izquierda, lfo a tempo con sync en beat 1»; elegido con él: los cuatro LFO, las divisiones con tresillos, lo guardado antes puede sonar distinto, el LFO 2 de la matriz por forma.

Los knobs de **velocidad de LFO** son bipolares: al centro el LED tenue; **a la derecha, LFO libre**; **a la izquierda, a tempo**, del centro hacia fuera 1/16T, 1/16, 1/8T, 1/8, 1/4T, 1/4, 1/2T, 1/2, 1 compás T, 1 compás, 2T, 2, 4T, 4, 8T, 8 compases (4 clics cada una), con el ciclo empezando en el primer tiempo del compás.
- **Motor de MIDI 1 / 2:** K7 de la página VCA-VCF (con VA-drum es el nivel del ruido: v + 64).
- **Matriz de modulación:** Shift + K4: en cada forma, la mitad izquierda de su tramo a tempo y la derecha libre.
- **Drums:** Shift + K7.
- **Master FX:** K1 del Auto-Filter y del Phaser.

## Qué probar
1. MIDI 1 con el motor (oscilador) y el LFO al filtro: K7 a la izquierda: el filtro sube y baja al tempo; con Play, el ciclo empieza en el primer tiempo de cada compás; cambia el tempo: el LFO lo sigue.
2. K7 a la derecha: el LFO libre de siempre; al centro el LED tenue.
3. Matriz: el LFO 2 (K4) a un destino; Shift + K4 en la mitad izquierda de una forma = a tempo.
4. Drums: Shift + K7 a la izquierda con el LFO a algo audible (K7): a tempo.
5. Master FX: Auto-Filter y Phaser con K1 a la izquierda = a tempo, alineados con el compás; a la derecha, libres.
6. Lo de SC44.7 (granular en estéreo) sigue igual.

## Verificación en emulación
- `emu_lfosync.py` (ARM: la cabeza nueva de la cadena del servicio del DSP; incremento = BPM × KQ[d] >> 8 y fase = $800000 + (tick mod d) × 2²⁴ / d para el motor y los drums; el avance y la fase del LFO 2 de la matriz; el periodo y la hora de inicio de Master FX), `emu_lfosync_dsp.py` (DSP: lado libre igual que la build anterior con el doble del valor; lado a tempo = el incremento del ARM; drums igual), `emu_sc44_2.py` (la matriz desde la zona libre).
