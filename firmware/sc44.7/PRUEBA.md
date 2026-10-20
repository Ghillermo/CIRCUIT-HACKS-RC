# SC44.7 / Beta 3.4 = SC44.6 + granular en estéreo

`firmware/sc44.7/circuittracks-4486-SC44.7.syx` — SHA-256 `4093fa418db3d8a2d279bdb3b7a2950ac0a2682df42f642f39246a77aa496150`, marca `SC44.7`.
`firmware/b3.4/circuittracks-4486-B3.4.syx` — SHA-256 `b870d9514a564920fb5c588e2d9398c3300e7e5bd5174e3c3b2e7807eb470794`, marca `B3.4` (**Beta 3.4**, el mismo código).

El usuario (2026-10-19): «haz que la dispersion granular sea stereo» · «el valor de paneo de pista controla la proporción/probabilidad de izquierda/derecha» · «mantén sk2 dispersión de la posición (centro) y sk4 dispersion stereo» · «junta en sk3 bipolar dispersion tono (+-24) y probabilidad reverse» (izquierda reverso, derecha tono; los lados solo con la envolvente, el nivel y el mute de la pista).

En el motor **granular** de MIDI 1 / 2 (página 2 de knobs):
- **Shift + K4 = dispersión estéreo:** cada grano sale a la izquierda o a la derecha, más separado cuanto más alto el knob. **El panorama de la pista** (Mixer) decide la proporción: al centro mitad y mitad, del todo a la derecha todos a la derecha.
- **Shift + K3 bipolar:** a la izquierda del centro, la probabilidad de grano al revés (hasta 100 %); a la derecha, la dispersión del tono (hasta ±24 semitonos). Al centro, nada.
- Shift + K2 sigue siendo la dispersión de la posición.
- La parte estéreo (lo que difiere entre los dos lados) solo sigue el VCA y el nivel de la pista: el filtro y el efecto del motor, el panorama, los envíos y el sidechain actúan sobre el centro. Pasa por el filtro master y por Master FX.

## Qué probar
1. MIDI 1 en granular con un sample sostenido y densidad alta; Shift + K4 al máximo: con auriculares, granos a los dos lados.
2. Panorama de MIDI 1 en el Mixer del todo a la derecha / a la izquierda: los granos se van a ese lado; al centro, repartidos.
3. Shift + K4 a 0: el sonido de antes (mono, sin dispersión del tono).
4. Shift + K3 a la izquierda: granos al revés (del todo = todos); a la derecha: alturas al azar hasta ±24 st; el LED tenue al centro.
5. El filtro master y el nivel de la pista afectan a todo; con el VCA cerrado (sin nota) los lados callan con el centro.

## Verificación en emulación
- `emu_gst_core1.py` (núcleo 1: el centro igual que el motor mono, los lados = el centro × ±anchura según el panorama, granos a los dos lados con el panorama al centro, Shift + K3 de −64 a +63); `emu_gstereo_dsp.py` (núcleo 0: los lados a la mezcla antes del filtro master: un grano a la derecha deja L = 0 y R = 2 × el centro; sin voz granular, igual que SC44.6 bloque a bloque); `emu_gst_arm.py` (la tabla de la página del granular y el recorte de −64 a 63); `emu_mfhold.py` sobre SC44.7.
