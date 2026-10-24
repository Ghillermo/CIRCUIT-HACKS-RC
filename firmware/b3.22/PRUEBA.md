# SC46.5 / Beta 3.22 = SC46.4 / Beta 3.21 + el arreglo de RC2.09 + el scan del inicio en el K7 de los drums

`firmware/sc46.5/circuittracks-4486-SC46.5.syx` — SHA-256 `efb6df13cdbdd8b547081517e6b11d9b987d7819ed55147a30b1c5f767506a50`, marca `SC46.5`.
`firmware/b3.22/circuittracks-4486-B3.22.syx` — SHA-256 `52ab530467802a7b701e67a9b0f4b530973fdb60caad5c15204c383576dffb3e`, marca `B3.22` (**Beta 3.22**, el mismo código).

- **Arreglo del inicio del sample de los drums** (`persist19.use_startfix()`; encontrado al estudiar el scan del LFO, 2026-10-24; el usuario eligió «A»): Shift + K3 a la izquierda llegaba al final del sample a un cuarto del recorrido (S = 32 de 120) y más allá el golpe sonaba un bloque y se callaba: el DSP cuenta la posición en unidades de 4 muestras, y `STARTF = S << 16` era S / 32 del sample. Ahora `STARTF = S << 14` = S / 128: el knob recorre todo el sample (hasta 120/128). Los proyectos guardados desde SC41.7 / RC2 que usaban el inicio lo tienen 4 veces más cerca del principio (la elección del usuario); el nibble antiguo (antes de SC41.7) se convierte en S = 8 s, que suena igual que antes. Probablemente es el «fallo en la fracción izquierda del knob de envelope (sample start)» que quedó abierto en SC41.4.
- **Scan del inicio** (`drums2_dsp.use_lfoscan()`; el usuario, 2026-10-24: «LFO amount afecta al sample start, no al pitch (como un scan)», «solo modo Drums»): el K7 de los drums a la izquierda, en lugar del vibrato, hace que cada golpe empiece donde está el LFO del drum: desde el inicio de Shift + K3 hasta |valor| / 64 del sample más allá, sin pasar nunca el corte (como mucho 15/16 − corte). Con el K7 a la izquierda el LFO ya no vuelve a empezar con cada golpe (corre libre o, a tempo, lo coloca `lfosync`: el primer tiempo cae en el inicio). A la derecha, el trémolo de siempre, sin cambios. El vibrato desaparece (el de `dtrig` ya era código muerto). Núcleo 0: −1 palabra (termina en `P:$3FF7`).

## Qué probar
1. **El inicio:** un drum con un sample largo, Shift + K3 a la izquierda poco a poco: el inicio avanza por todo el sample hasta el final del recorrido, sin silencios.
2. **El scan:** el mismo drum con un patrón de corcheas, K7 a la izquierda (más a la izquierda = más recorrido), Shift + K7 a la derecha para que el LFO vaya rápido: cada golpe empieza en otro sitio. Shift + K7 a la izquierda (a tempo): el recorrido se repite con el compás.
3. K7 a la derecha: el trémolo de siempre.
4. Lo de SC46.4 / Beta 3.21 sigue igual.

## Verificación en emulación
- `emu_startfix.py`: `c_k3w` escribe `STARTF = S << 14` (S 16 / 32 / 64 / 120), el corte igual; el núcleo entero con cuatro golpes: con el arreglo las voces siguen sonando con S = 64 y 120; con el valor viejo (S << 16) se callan (el fallo reproducido). La build anterior: S << 16.
- `emu_lfoscan_dsp.py` frente a SC46.4: el programa acaba en `$3FF7`; `dtrig` con LFO ≥ 0 idéntico; con LFO < 0, 180 combinaciones de L / corte / inicio / LFO / fase: la fase no se reinicia y el inicio = L × min(S/128 + (−LFO/128)(1 − TRI), 15/16 − E/128) ±4 muestras, siempre antes del corte; `dctl` sin vibrato (el incremento como con LFO 0) y con LFO > 0 idéntico; el núcleo entero con el K7 a la derecha idéntico, a la izquierda los golpes empiezan dentro del sample; la pila igual.
- `emu_k3split_dsp.py` comparaba un inicio por el nibble antiguo de la build anterior: con SC46.4 (que ya no lo lee) falla igual sobre SC46.4 frente a SC46.3; no vale para estas parejas.
