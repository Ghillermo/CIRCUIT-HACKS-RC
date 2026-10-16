# SC42.3 = SC42.2 + resolución del arpegiador, gate por pulsación y colores del metrónomo

`circuittracks-4486-SC42.3.syx` — SHA-256 `4a6ab673ea3b8fff61607b67a2ff6dea8ace00df243967492fe563b0a174c322`, marca `SC42.3`.
`firmware/b1.13/circuittracks-4486-B1.13.syx` — SHA-256 `f4841675ff5dc822e41467c1b79518be79d4515c615ce8a69f9d9db638dade4c`: el mismo código con la marca `B1.13` (**Beta 1.13**).

Pedidos del usuario (2026-10-16):
- **Arpegiador: Shift + pads 17-24 de Pattern Settings = su resolución**, distinta del sync rate de la pista (1/32T, 1/32, 1/16T, 1/16, 1/8T, 1/8, 1/4T, 1/4; el mismo pad otra vez = la de la pista). Con Shift, amarillos y el elegido verde. Por pista y patrón, con el proyecto.
- **Gate por pulsación** («when manually inputting a sequence, the time you keep the pad held becomes the gate length»): con un paso mantenido + un pad de nota (o una nota mantenida + un pad de paso), el tiempo que se mantiene el pad = el gate de la nota (al tempo del proyecto y al sync rate de la pista, 1 micropaso … 16 pasos); termina al soltar el primero de los dos. **Encendido / apagado por pista con el pad 32 de la vista Micro Step** (Gate dos veces; verde / tenue; con el proyecto). El pad 25 de esa vista es, en stock, la primera nota del paso.
- **Longitud fija: pad 31 de la vista Micro Step** (el usuario: «pad 31 is fixed length … that length is default for any manually introduced step (not live recorded)»): apagada, pulsarla la enciende y abre el selector (pads 17-32 = 1 … 16 pasos; elegir uno lo cierra); encendida, corta = selector, mantener ~1 s = apagada. Naranja encendida. Excluye al pad 32 (y al revés). Por pista, con el proyecto.
- **El arpegiador usa esos gates**: cada nota del acorde dura el suyo (como mucho lo que queda del acorde); las notas de la entrada duran un paso de arpegio.
- **Metrónomo** (Shift + Clear, LED de Clear con Shift): sin clic rojo, clic verde, solo cuenta atrás magenta, las dos cian. El volumen del clic es el de stock (Tempo/Swing + K5).

## Qué probar
1. Pattern Settings de Synth 1: Shift → pads 17-24 amarillos; Shift + pad 18 (1/32) → verde; un acorde en la secuencia con el arpegiador encendido suena a 1/32 aunque la pista vaya a 1/16. Shift + pad 18 otra vez → vuelve al sync rate de la pista.
2. La entrada del arpegiador (dos notas mantenidas), parado y en marcha, a la resolución elegida.
3. Vista Micro Step (Gate dos veces): pad 32 tenue; pulsarlo → verde. Vista Note: mantener un paso, mantener un pad de nota ~medio segundo, soltar: la nota queda con ese gate (verlo en la vista Gate). Con el pad 32 apagado, el gate de stock.
4. Un acorde introducido así con gates distintos y el arpegiador: cada nota dura lo suyo.
5. Micro Step: pad 31 → selector, pad 20 = 4 pasos; introducir notas a mano → gate de 4 pasos; pad 31 mantenido 1 s → apagada; pad 32 apaga el 31.
6. Shift: Clear rojo / verde / magenta / cian según el estado del metrónomo.

## Verificación en emulación
- `emu_arprate.py`: Shift + pads 17-24 y sus LEDs (el orden y el pad 25 conservan la resolución); la secuencia a 1/32 (cada 3 ticks), a 1/8 (cada 12) y a la de la pista con los gates de cada nota; la entrada parada (250 ms a 1/8 y 120 BPM) y en marcha (cada 3 ticks); la vista Micro Step (Gate dos veces) y su pad 32; paso + nota mantenida 375 ms = gate 18, 2 s = 96; apagado = el de stock; los colores del metrónomo.
- `emu_arp.py` sobre SC42.3: el orden y el ritmo como antes; las duraciones cambian (cada nota su gate).
- `emu_arprate.py` también: el pad 31 (selector, 4 pasos = gate 24, corta = selector, 1,2 s = apagada, el pad 32 la apaga).
- No probado en emulación: el orden «nota mantenida + pad de paso» (el gate termina al soltar el paso).
