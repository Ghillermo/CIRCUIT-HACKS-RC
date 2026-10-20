# SC45 / Beta 3.7 = SC44.9 + soltar la automatización en un paso + fila de motores del pad 27

`firmware/sc45/circuittracks-4486-SC45.syx` — SHA-256 `d575671f5b607ae484d75098b713d67e2b053c092071eca9caf86883f2694940`, marca `SC45`.
`firmware/b3.7/circuittracks-4486-B3.7.syx` — SHA-256 `be0ca9e7a903f35c5a4b44fc936c589852cb9095db65448f02bdb1f1348e7f51`, marca `B3.7` (**Beta 3.7**, el mismo código).

El usuario (2026-10-19): «En velocity view, shift+pad hace que deje de aplicarse automatización (posición de knob + init en lugar de posición + valor previo de automatización)» (Synth 1 / 2 y MIDI 1 / 2); «En selector de modo sinte midi (pad 27) tras un toque, abrir vista en row 3 con opciones (mantener colores) tocar el pad 27 otra vez cierra la vista y recupera lista de parches» (elegir deja la fila abierta).

**Soltar la automatización en un paso** (Synth 1 / 2, MIDI 1 / 2):
- Vista **Velocity** de la pista, **Shift + pad de paso** (pads 1-16; con 17-32, los pasos 17-32): ese paso queda marcado; otra vez lo desmarca. Con Shift, los pads de paso se ven amarillos y los marcados rojos.
- En un paso marcado no suena ningún carril (aunque tenga valores) y cada parámetro que la automatización había movido vuelve a la posición de su knob: la que tenía antes de que sonara la automatización. Girar el knob a mano fija una posición nueva.
- La marca se guarda con el patrón.

**Pad 27 de la vista Preset de MIDI 1 / 2:**
- Un toque abre la fila de motores en los pads 17-23: apagado (blanco), entrada de línea, oscilador, VA-drum, granular, muestra, secuenciador de efectos, en sus colores; el actual brillante.
- Tocar uno lo elige; la fila sigue abierta. El pad 27 otra vez la cierra y vuelve la lista de patches (mientras está abierta, los pads 9-24 no cargan nada).
- Shift + pad 27 sigue pasando al motor siguiente.

## Qué probar
1. Synth 1 con automatización de un macro en el paso 2 (Record + Play girando el macro 1). Vista Velocity, Shift + pad 4: el pad 4 rojo. Play: en el paso 2 el macro se mueve; en el paso 4 vuelve a la posición del knob. Sin marca, se queda en el valor automatizado como en el stock.
2. Lo mismo en MIDI 1 con el motor (oscilador) y un carril de la página 4.
3. Gira el knob a mano durante la reproducción: en el paso marcado vuelve a esa posición nueva.
4. Pad 27: la fila de motores; elegir granular, oscilador, apagado; pad 27 otra vez: los patches. Sal de la vista con la fila abierta: al volver está cerrada.
5. Lo de SC44.9 (destinos de la página 4, Record + paso) sigue igual.

## Verificación en emulación
- `emu_autorel.py`: la fila de motores (colores, elegir, pads tragados, cerrar, Shift + pad 27 = el ciclo); la marca (vista Velocity de MIDI 1, Shift + pad 4 / página 17-32, LEDs, sin Shift = stock); **la reproducción de stock `0x08031AFC` llamada como la llama el secuenciador**: Synth 1 carril 0 = 100 en el paso 2 → el almacén de macros a 100, paso 4 marcado (con un 50 en el carril) → vuelve a 127 (la posición del knob), paso 2 otra vez → 100; el knob a mano borra la bandera; MIDI 1 carril 4: el almacén vuelve al valor del motor (como valor de carril) en el paso marcado.
- `emu_p4dest.py` sobre SC45: igual que SC44.9. `emu_sc44.py`, `emu_sc44_2.py` (modo muestra), `emu_sc41.py`, `emu_sc42_6.py`, `emu_sc43_8.py` y el pad 27 de `emu_lazysave.py` pulsan el pad 27 para cambiar de motor: no valen sobre SC45.
- **Duda anotada:** el guardia del flip de sample (`smpick`) está en la escucha del paso, no en la reproducción; no se ha localizado quién reproduce el carril 8 (nivel) de las pistas de notas.
