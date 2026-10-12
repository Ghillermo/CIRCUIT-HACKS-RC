# SC21.1 — SC21 sin tilt EQ y con feedback de los retornos de reverb / delay

`circuittracks-4486-SC21.1.syx` — SHA-256 `c1f81539627e12d35b869fa42512edce17b1fdf2057d4db54c2868f7dfe94b85`
Imagen de 0x5d27c bytes, CRC 0x45407aab, marca `SC21.1`. Es SC21 con dos cambios; si falla, vuelve a SC21 (`firmware/sc21/`), SC20.1 o SC20, y la última versión segura confirmada es SC17.7.

## Qué cambia
1. **Sin tilt EQ.** Los tipos de filtro (Shift + K5) son ahora **DJ, paso banda y notch** (tres, con vuelta). Shift + K5 siempre cambia de uno en uno.
2. **Feedback de los retornos de reverb / delay.** En stock-SC10, cuando el Setup manda el retorno de reverb a la tira 3 (pad 22 del Setup) y el de delay a la tira 4 (pad 23), la entrada de línea de esa tira se anula y el retorno se suma directamente a la mezcla final, **después** de construir los envíos: por eso subir los envíos de las pistas 3 y 4 no hacía nada. Ahora esa entrada del anillo lleva el retorno del bloque anterior (la captura de `fx_cap`, a nivel de una entrada de línea; solo 32 muestras = 0,7 ms de retardo), así que **los envíos de la tira lo vuelven a mandar al reverb y al delay**. La captura se toma *después* del VCF / FX / VCA de la voz de esa pista (modo VCF encendido en MIDI 1 / MIDI 2), de modo que filtro, saturación y ganancia caen dentro del lazo.
   - Los sintes siguen leyendo el retorno como antes (modos de la fuente 1-4) y ahora oyen el retorno ya procesado.
   - El retorno directo a la mezcla (SC10) no cambia. Para oír **solo** el feedback, deja el **nivel (dry) de la tira 3 / 4 a 0** y sube sus **envíos**; con el nivel arriba oirías el retorno dos veces.

## Cómo probarlo (volumen bajo, proyecto de prueba)
1. Setup: activa el pad 22 (reverb → tira 3) y/o el 23 (delay → tira 4).
2. Mezclador: nivel de la tira 3 / 4 a 0; pon sonido en un drum o un sinte con envío de reverb / delay > 0 para que haya retorno.
3. **Sube poco a poco el envío de reverb (o delay) de la pista 3 / 4** y escucha cómo la cola se alarga y se auto-oscila. Con los envíos al máximo el lazo se acerca a ganancia 1: puede dispararse; baja el volumen principal antes.
4. Con el **modo VCF de MIDI 1 / 2** encendido (pad 26 de la vista Preset): el filtro, la saturación (Shift + K8 / K8, Gain) y el gain actúan sobre el retorno dentro del lazo. Un filtro paso bajo en el lazo oscurece el feedback; la saturación lo acota.
5. Con los pads 22 / 23 apagados todo sigue como en SC21.

## Notas técnicas
- `vcf21_dsp.FB`: `vpre` termina en `pmfb` (el `premix` de SC10 con feedback: carga Y:$3AC0 / Y:$3A80 en el anillo en lugar de ceros) y la cadena de P:$D21 pasa a `vret → fx_cap → SC10 returns` (antes `fx_cap → vret → returns`). Programa del DSP: **termina en P:$37E0** (SC21: $37FF): quitar el tilt libera 63 palabras y el feedback gasta 32.
- La firma del estado guardado es 0xA7: al flashear SC21.1 sobre SC21 el estado del modo VCF se reinicia (un tipo de filtro 3 = tilt guardado dejaría de existir).
