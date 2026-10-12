# SC23.1 — SC23 + editor de CC con otro manejo: Octave cicla, el botón de la pista guarda, cualquier botón de vista descarta

`circuittracks-4486-SC23.1.syx` — SHA-256 `8357544cc5a3a32b7fe88cbaef1f8061d8c4f4890ce9b9d1bf68b2e54e03858d`
Imagen de 0x5e59c bytes, marca `SC23.1`. Es SC23 con el flujo del editor de CC de los macros MIDI cambiado como se pidió. Si falla, vuelve a SC22.4 (o SC23).

## Cómo se usa
1. MIDI 1 (o MIDI 2) → botón **Preset**. Pad **25** (magenta) enciende / apaga el modo edición de CC de esa pista.
2. **Tocar un knob** lo selecciona y enseña su CC en los 32 pads (dígitos del display del tempo); **girarlo** cambia el valor (en vivo: ya manda el CC nuevo, pero **todavía no está guardado**).
3. **Octave ▼ / ▲** (los botones de octava) **ciclan los campos** del knob elegido: ▼ = siguiente, ▲ = anterior, con vuelta (CC → inicio → fin → CC…). No guardan nada. Colores: CC / MSB magenta, LSB rosa, inicio naranja (LSB amarillo), fin azul claro (LSB aguamarina). NRPN / RPN: MSB, LSB, y el rango (en dos mitades si el valor es de 14 bits: seis campos).
4. El botón de la propia pista (**MIDI 1** en la pista 1, **MIDI 2** en la 2) **guarda** la plantilla en el aparato y deselecciona el knob (los números desaparecen). Si no hay knob elegido ni cambios pendientes, el botón sale del editor y hace lo de siempre (pasa a la vista de la pista).
5. **Descartar** (se vuelve a los valores del último guardado, también en el emisor): cualquier botón que cambie la vista (**Synth, Drum, Preset, Mixer, FX, la MIDI de la otra pista**), **apagar el pad 25** o **pulsar un pad de plantilla (1-8)**. Se descartan los cambios de todos los knobs de la plantilla activa desde el último guardado. Record, Play y Shift no descartan.

## Prueba
1. Preset de MIDI 1 → pad 25 → knob 1: sale el CC (1). Gíralo a 20. Octave ▼: inicio del rango; gira; Octave ▼: fin; Octave ▼: otra vez el CC (con vuelta). Octave ▲ recorre al revés.
2. Pulsa **MIDI 1**: guarda (los números se van). Sal con otro botón, abre la vista de la pista y mueve el knob: manda el CC 20. Apaga y enciende el aparato: sigue (y Components lo ve).
3. Entra otra vez, cambia dos knobs y pulsa **Mixer** (o Note, Drum…): los dos vuelven a lo guardado (el knob manda el CC de antes).
4. Cambia un knob y pulsa un pad de plantilla (2): el cambio se pierde; la plantilla 2 se edita y se guarda con el botón de la pista.
5. Con el editor encendido y sin tocar nada, MIDI 1 te saca a la vista de la pista. Con el editor apagado, Octave es el de siempre.
6. NRPN (créalo en Components): seis o cuatro campos según el valor; vuelta al final. Prueba también MIDI 2.

## Notas técnicas
- `vcf21.use_cced2()` (`CCED2`); SC23 queda idéntica. Estado volátil de SC23 (`+71..+74` de la cola de ajustes).
- Descarte: antes del primer cambio, `c_edbak` copia los 8 registros de 10 B de la plantilla y su índice al búfer de LEDs de Master FX (`c_gfst() + 64`, `vcf21.S_SCR`; 84 B ociosos mientras esa vista no está activa; `c_gleds` lo reescribe entero al usarse). `c_eddiscard` los devuelve y re-elige la plantilla por el router. Si Master FX estuviera apagado (`c_gfst` = 0) no hay copia y descartar no hace nada.
- `c_vbtn` (delante de `c_bentry` en `0x08033320`): ids 19 / 20 con el editor encendido se consumen (el botón suelto va a stock). Ya no se guarda al cambiar de campo, de knob ni al salir.
- Pruebas: `tools/emu_sc23_1_ed.py` (ciclo, vuelta, copia que no se pisa, guardado único, descarte con ocho botones / pads distintos, NRPN de 7 y 14 bits, MIDI 2) y `tools/emu_sc23.py` con esta imagen. Limitación: el guardado ocurre desde el hilo de la interfaz (cola del almacén persistente), no probado en el aparato.
