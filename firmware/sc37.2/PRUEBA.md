# SC37.2 — arreglo del intercambio entre packs y del borrado de packs

`circuittracks-4486-SC37.2.syx` — SHA-256 `4394d74b882c0fd2ae31522fcfc4a94106e9d5601324118d523e100d82c66d43`
Imagen de 0x650f0 bytes, CRC 0x67bae548, marca `SC37.2`.

Es SC37.1 con dos arreglos tras tu prueba. **SC37 y SC37.1 no deben usarse para intercambiar entre packs**: pueden borrar o mezclar samples y patches.

## 1. Intercambio entre packs (samples y patches)
**Fallo en SC37 / SC37.1:** al leer un fichero de otro pack, la tarea de almacenamiento del aparato cambia su «pack actual» a ese pack. El mod usaba «pack actual» para el pack cargado, así que, tras la primera lectura, borraba y escribía en el pack equivocado (de ahí los samples borrados o cambiados por otros).

**Ahora:**
- El pack cargado sale de la vista de packs y se nombra siempre por su número.
- La tarea de almacenamiento vuelve al pack cargado al terminar cada intercambio, y antes de un intercambio dentro del mismo pack.
- Si la copia falla después de borrar B, B se reescribe desde la memoria del DSP.

El gesto no cambia: Duplicate + pad A, cargar el otro pack, Duplicate + pad B. Lo copiado de otro pack parpadea en amarillo.

## 2. Borrar un pack: ahora solo con pulsaciones
**Fallo:** en la vista de packs el aparato no enciende Clear desde el mod y no guarda «Clear mantenido», así que la pregunta nunca se hacía.

**Ahora (vista de packs, Shift + Projects):**
1. **Toca Clear** (sin Shift): durante ~5 s parpadean en rojo los packs que se pueden borrar (nunca el cargado).
2. **Toca el pack**: solo ese parpadea; no se carga.
3. **Toca Clear otra vez** antes de 5 s: se borra. El hueco queda ocupado hasta reiniciar, como antes.
- Si dejas pasar 5 s, los pads vuelven a cargar packs como siempre. Shift + Clear sigue siendo el metrónomo.

## Qué probar (con copia de la SD y packs de prueba)
1. Samples entre packs: copia un sample del pack 30, carga el 31, Duplicate + otro pad. Debe sonar el del pack 30; vuelve al pack 30 y el sample copiado debe ser el antiguo del 31. **Ningún otro sample debe cambiar.**
2. Patches entre packs: lo mismo en la vista Preset del sinte.
3. Intercambio dentro del mismo pack, después de los anteriores: sigue funcionando.
4. Borrar el pack 30: Clear, pad del pack 30, Clear. Comprueba en el PC que la carpeta del pack 30 quedó vacía y que el 31 está intacto.

---

# SC37.2 — fixes for swaps between packs and for deleting packs (English)

SC37.1 with two fixes after the user's test. **Do not use SC37 / SC37.1 for swaps between packs** (they may delete or mix up samples and patches): reading an item of another pack switches the storage task's current pack, which the mod used for the loaded pack. Now the loaded pack is always named by its number and the storage task is put back on it; if the copy fails after deleting B, B is restored from the DSP's memory. Deleting a pack is now presses only (packs view): tap Clear (deletable packs blink red for ~5 s), tap the pack (only it blinks, not loaded), tap Clear again = deleted.
