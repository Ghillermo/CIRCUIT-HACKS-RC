# SC52.2

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc52.2/circuittracks-4486-SC52.2.syx` | `5163c345783642b83fbf4f5a5f1dfeaf24d4771b3f24b13556643f26bd852c00` | `SC52.2` |

**Qué cambia** respecto a la 5.24 / SC52.1 (el usuario, 2026-11-05):
- **Latch en la vista Note:** con Shift y notas fijadas los pasos ya no se ponen amarillos; Shift + paso (escribe las notas fijadas) pone ese paso en verde azulado (0x4D, el color del latch) mientras se mantiene.
- **Página OSC 2** (oscilador, VA-drum, wavetable; el granular sigue como antes): K1 = **ratio de OSC 2 respecto a su nota** (centro 1; izquierda ½ / ¼; derecha 2 … 31), K2 = **detune** ±50 cents, K3 SHAPE 2, K4 MIX, K5 FM, K6 BITSYNC, K7 WAVE 2, K8 RING. Con dos notas, OSC 2 = la segunda × su ratio. La matriz de modulación conserva sus destinos guardados.
- **Wavetable, pad 8:** los ciclos de sample se copian de verdad (en la 5.24 el cuadro se marcaba sin copiarse).
- **Arreglo:** con la fila de motores abierta (o un modo flip), la superposición de destinos de las páginas 4 / 8 (Shift + knob) y de la matriz quedaba tapada (se dibujaba antes que la fila); ahora se dibuja la última y los pads 9-24 no hacen nada mientras se ve.
- **Arreglo:** con la fila de motores abierta, los pads 7 / 8 (apagados) ya no hacen nada con el FM apagado (antes apagaban el pad 21 y desviaban la fila a las listas del FM).

**Usar con una copia de la tarjeta.**

## Qué probar
1. Synth 1, vista Note: Shift + una tecla (latch). Con Shift, los pasos conservan sus colores; mantén Shift + el paso 3: verde azulado mientras lo mantienes; al soltar vuelve a su color con las notas escritas.
2. MIDI 1, sinte propio con dos osciladores (pad 28), página OSC 2 (pad 3): K1 en el centro = unísono; a la derecha 2, 3, 4… (armónicos); a la izquierda ½ y ¼. K2 = detune (batido lento cerca del centro). K3 SHAPE 2, K4 MIX, K5 FM.
3. Igual con la wavetable (pad 21 de la fila de motores) y con el VA-drum. Con el granular, la página 3 como antes.
4. Dos notas a la vez: OSC 2 sigue la segunda nota con su ratio.
5. Wavetable sonando: mantén el pad 8 y toca un sample: tras un momento su ciclo suena como un cuadro más (K7 para llegar a él).
6. Fila de motores abierta (pad 27) con la wavetable: pulsa / mantén los pads 7 y 8: no pasa nada y el pad 21 sigue encendido.
7. Fila de motores abierta, página 4 (u 8 con Shift + pad 4): Shift + girar un knob = los pads 9-24 enseñan su destino (como la matriz) durante 1,5 s; lo mismo girando un knob de la matriz (página 6).
8. Lo de la Beta 5.24 (wavetable, sinte propio sonando): ver `firmware/b5.24/PRUEBA.md`.

## Verificación en emulación
`emu_latchstep.py --heldcue`, `emu_osc2pg2.py --ratio` (disposición, envío del ratio, granular igual, destinos de la matriz), `emu_ratio2_dsp.py` (frecuencia de OSC 2 a cada ratio, detune), `emu_wtui.py --smpcyc`, `emu_p4ovl.py --top`, `emu_fm8v2.py`, `emu_wt_dsp.py`, `emu_wtcopy_core1.py`, `emu_gentab_dsp.py --xtab`, `emu_dx7imp.py`.
