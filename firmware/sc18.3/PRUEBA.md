# SC18.3 — SC18.2 con los colores de Octave elegidos por el usuario

`circuittracks-4486-SC18.3.syx` — SHA-256 `4b0fe7b9e5954ba0e0887e9595a038c2911150a15cafd06e171d6d3fe67136bf`
Imagen de 0x5ae58 bytes, CRC 0xd6b29407, marca `SC18.3`.

Es **SC18.2** (ver `firmware/sc18.2/PRUEBA.md`, y `firmware/sc18.1/PRUEBA.md` para los knobs de drums, el pad 7 y el pad 8) con un solo cambio en la vista FX:

| Botón | Función | Color |
|---|---|---|
| Octave ▲ | envíos de delay | **melocotón = el color del pad 1** de la vista FX (código 0x6B) |
| Octave ▼ | envíos de reverb | **crema = el color del pad 17** de la vista FX (código 0x2A) |
| Duplicate | reset de todos los FX | como SC18.2 (0x09, color del MIDI 1; vale cualquiera que no sea blanco) |
| 1-16 / 17-32 | resonancia del filtro master | como SC18.2 (0x20, color del Synth 2; ídem) |

Los códigos de los pads 1 y 17 son los que pinta la vista FX de stock al entrar (pads sin seleccionar), leídos en emulación.

## Verificación en emulación
- `emu_sc18_2.py` sobre SC18.3: lo mismo que en SC18.2, más la comprobación de que Octave ▲ / ▼ tienen exactamente el código del pad 1 / pad 17 en la vista FX.
- Batería completa (`run_tests.sh full`, 15 conjuntos): TODO OK.

## Pruebas en el aparato
1. Envía SC18.3.
2. **FX**:
   - Octave ▲ debe verse como el pad 1 y Octave ▼ como el pad 17;
   - Duplicate y 1-16/17-32 deben estar encendidos y no en blanco.
3. El resto, como en los `PRUEBA.md` de SC18.2 y SC18.1.

## Volver atrás
Envía SC18.2, SC18.1 o SC18.
