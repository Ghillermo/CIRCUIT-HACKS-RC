# SC23.4 — SC23.3 + correcciones tras probar (editor de CC v2, Master FX, pads de drums)

`circuittracks-4486-SC23.4.syx` — SHA-256 `45d838631e5b12fe24fb2a4edb15bcaaaa5fc8e73f3ab3f438646c11f1d454ea`
Marca `SC23.4`. Es SC23.3 con las correcciones de abajo. **Aviso:** en SC23.3 los modos VCA-VCF / OSC no tenían efecto en el sonido en el aparato (informado); esta build no toca el DSP, así que seguirá igual hasta localizar la causa (ver al final).

## Editor de CC (pad 25 en la vista Preset de MIDI 1 / 2)
- **El número de CC elige el tipo:** el primer campo de cada knob es el número de CC. **99, 98 o 6 = NRPN de 7 bits** (campos: número, MSB, LSB, mínimo, máximo); **38 = NRPN de 14 bits** (número, MSB, LSB, mínimo MSB / LSB, máximo MSB / LSB: seis campos tras el número). Cualquier otro número = CC (número, mínimo, máximo). Al cambiar de tipo, el parámetro y el rango se reinician (7 bits 0-127, 14 bits 0-16383).
- **Octave ▼ / ▲** recorren los campos. **Después del último campo hay un paso «guardar»**: no se dibuja ningún número, el pad **Save (el pad junto al pad 25, el 26)** parpadea en verde y se encienden los dos Octave; **otro Octave ▼ guarda** (y deselecciona el knob); Octave ▲ vuelve al último campo.
- **El pad Save guarda en cualquier momento.** Con el editor apagado ese pad es el patch flip de siempre.
- **Los botones de vista descartan, incluido el de la propia pista** (MIDI 1 en la pista 1, MIDI 2 en la 2): vuelven los valores guardados y salen del editor. También descartan el pad 25 apagado y los pads de plantilla.
- LEDs de Octave: primer campo solo ▼; campos intermedios ambos; último campo solo ▲ (▼ sigue pasando al paso guardar).
- Prueba: knob 1 → gira hasta 99 (NRPN): Octave ▼ recorre MSB, LSB, mínimo, máximo; otro ▼: el pad Save parpadea; otro ▼: guardado. Comprueba en Components que la plantilla tiene el NRPN.

## Master FX
- **Pad 8** en blanco (brillante si hay algo que borrar, tenue si no).
- **Tramo del song pointer:** el paso menor es siempre el inicio y el mayor el fin, da igual el orden en que se toquen (dos pasos mantenidos, o con el inicio fijado con Shift un toque por debajo = nuevo inicio y el anterior pasa a fin). Si se elige un fin que el song pointer ya ha pasado, salta al inicio en el siguiente paso.
- **Salto con el pad 7:** el paso destino se enciende (amarillo) mientras el salto esté pendiente o se repita. **Shift + pad 7 fija** el modo; **tocar el pad 7 fijado lo suelta**.
- **Pendiente:** el cabezal (LED del paso que suena) no se mueve en el aparato; sin cambios aquí.

## Drums, vista Note
Pads 25-28 en espejo: **25 = drum 4, 26 = drum 3, 27 = drum 2, 28 = drum 1** (el 28 queda junto al 29 = drum 1).

## Para localizar el fallo de los modos VCA-VCF / OSC
1. Flashea **SC23.2** (defaults antiguos: pasa todo sin tocar nada): modo VCA-VCF encendido (pad 29), mueve FILT (K5): ¿se oye el filtro en la entrada externa de esa pista?
2. Si no: **SC22.3** y **SC21.4** / **SC21.3**: dime la primera que falla.
3. Con SC23.3 / SC23.4: el estado neutro cierra el VCA sin tecla: el sonido externo de esa pista debe callar hasta que pulses una nota de la pista (aunque sea del secuenciador). Si lo oyes siempre, el DSP no recibe el modo.
Dime también si el Setup tiene activo reverb → tira 3 / delay → tira 4.

## Pruebas de emulación
`emu_sc23_4_ed.py` (editor v2), `emu_sc23_4_gfx.py` (Master FX), `emu_sc23_4_notes.py` (pads de drums), y `emu_sc23_3.py` / `emu_sc23_3_fx.py` / `emu_sc23_3_dsp.py` sobre esta imagen.
