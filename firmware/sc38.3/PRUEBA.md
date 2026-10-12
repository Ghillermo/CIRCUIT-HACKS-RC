# SC38.3 — MIDI Thru: Merge y Filter

`circuittracks-4486-SC38.3.syx` — SHA-256 `767901bc21ea94463405777bbfb1a434688d8c377eb9bd73f612fd02bb27c85e`
Imagen de 0x66158 bytes, CRC 0x3250fcb, marca `SC38.3`.

Es SC38.2 con dos modos más para el jack **MIDI Thru**. Se eligen en **Advanced Setup** (mantener Shift al encender) con el botón **Duplicate**, que ahora recorre cuatro modos:

| Duplicate | Modo | Qué sale por el jack Thru |
|---|---|---|
| Rojo tenue | **Thru** (por defecto) | Copia del MIDI In por hardware, como siempre |
| Verde | **Out 2** | El MIDI del aparato, como el MIDI Out |
| Amarillo | **Merge** | El MIDI In + el MIDI del aparato |
| Azul | **Filter** | El MIDI In salvo los canales en los que escucha el Circuit (Synth 1 / 2, MIDI 1 / 2, Drums, canal 16 del proyecto) |

Merge y Filter copian por software los mensajes del **MIDI In (DIN / TRS)**, no los del USB. El SysEx no se copia.

## Qué probar
1. Advanced Setup: Duplicate cambia el color en el orden de la tabla y vuelve a rojo tenue; Play guarda; al apagar y encender se mantiene el modo.
2. **Merge:** un teclado en el MIDI In y un sinte en el Thru. El sinte recibe lo del teclado y también las notas del secuenciador de MIDI 1 / 2.
3. **Filter:** con Synth 1 en el canal 1, las notas del teclado en el canal 1 no llegan al sinte del Thru; en el canal 6 sí. El aparato no manda nada propio por el Thru.
4. **Thru y Out 2** funcionan como antes.
5. En Merge, si el Circuit sigue el reloj del MIDI In, conviene apagar Clock Tx para no duplicar el reloj en el Thru.
