# SC41.7 = SC41.6 + K3 de los drums partido (decay / ataque, inicio / corte) + Clear + pad 25 en Pattern Settings

`circuittracks-4486-SC41.7.syx` — SHA-256 `74f26e9cd1c8575cc6b7d53520b3f39684fe640615be00d0f71e0e79f9205bb3`, marca `SC41.7`.
`firmware/b1.7/circuittracks-4486-B1.7.syx` — SHA-256 `2e63828a3f8b88f2690d9e230f295f606954de184e1ecc7ca83414a5d0d40db1`: el mismo código con la marca `B1.7` (**Beta 1.7**).

**K3 de los drums partido** (el usuario: K3 «izquierda: decay, derecha: ataque, centro neutro»; Shift + K3 «izquierda: inicio, derecha: corte»). Antes el punto de inicio estaba a la izquierda del 0 del decay: solo sonaba con el decay más corto.
- **K3:** a la izquierda el decay de stock, igual que el original (mismo valor guardado, CC y automatización). Al llegar al máximo (127, el sample entero), seguir a la derecha = **ataque** (fundido de entrada, 1-127, hasta 1 s; el tiempo crece al cuadrado). Girando a la izquierda el ataque vuelve a 0 antes que el decay. **Centro neutro** = decay 127 y sin ataque.
- **Shift + K3:** a la izquierda el **inicio** avanza dentro del sample; a la derecha, un **corte** desde el final (hasta 120/128 cada uno); uno vuelve a 0 antes de que se mueva el otro. Centro = el sample entero.
- **Clear + K3** a la derecha: ataque, inicio y corte a 0 (el decay vuelve a su valor por defecto, como en el original).
- LED de K3: el ataque en blanco con su brillo; si no hay ataque, el decay de stock. Con Shift: el inicio en el color del drum, el corte en blanco, el centro blanco tenue.
- NRPN de los drums (MSB 5-8): LSB **10 = inicio (0-120)**, **13 = corte**, **14 = ataque**.
- Se guarda con el proyecto (cola del registro de la sesión, bloque `DRX1` con suma). Un proyecto de stock o anterior carga neutro y, si tenía el punto de inicio antiguo, lo conserva (inicio = 2 × el valor antiguo). Un proyecto nuevo, a 0.
- DSP: con todo a 0 el sonido es bit a bit el de SC41.6. El corte es seco (sin fundido).

**Clear + pad 25 en Pattern Settings** (el usuario: «en vista normal pattern settings, clear + pad 25 borra los random-mutate y dynamics»): con una pista de notas, borra el random-mutate y las dinámicas de los 32 pasos del patrón que suena; la frecuencia se queda. El pad 25 solo sigue abriendo el modo 2.

## Qué probar
1. Un drum, proyecto nuevo: K3 a la derecha hasta el final del decay; seguir girando: el golpe empieza con fundido (LED blanco). Volver a la izquierda: primero desaparece el ataque, luego baja el decay.
2. Shift + K3 a la izquierda: el sample empieza más adentro (LED del color del drum); a la derecha (pasando por el centro): el sample se corta antes (LED blanco).
3. Clear + K3 a la derecha: ataque, inicio y corte desaparecen.
4. Guardar, apagar, cargar: los tres valores vuelven. Un proyecto antiguo con punto de inicio: lo conserva.
5. Con todo neutro, un proyecto de stock suena igual que antes.
6. Pattern Settings de Synth 1 con dinámicas y random-mutate puestos: Clear + pad 25 los borra; la frecuencia se queda.

## Verificación en emulación
- `emu_k3split.py`: K3 / Shift + K3 por el controlador (decay = las mismas escrituras que SC41.6; ataque, inicio y corte sin escritura de stock), el bloque, Clear, el tick (AINC / STARTF / ENDC), carga con y sin bloque (conversión del inicio antiguo), proyecto nuevo, LED, NRPN de salida y entrada.
- `emu_k3split_dsp.py`: `dtrig` / `dctl` / `dstage` con el programa real: todo a 0 = SC41.6 bit a bit; el inicio = el inicio antiguo; el corte acorta la longitud; el ataque arranca en silencio y sube; núcleo completo con golpes reales; programa hasta `P:$3FF8`.
- `emu_clrmod.py`: Clear + pad 25 por el controlador.
