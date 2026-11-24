# Alpha 7.52 — prueba

Alpha 7.52 = Alpha 7.51 + `novasec.use_v12()` + `m2lanes.use_x2()` (el usuario: «2 destinations on all 8 knobs», «Like the macro slots»).

**Macros 2 de Synth 1 / 2 con dos destinos por knob:**
1. En Macros 2 (Shift + pad 1), girar un knob: durante 2 s los **pads 1 / 9** enseñan sus dos destinos (color del sinte brillante = puesto, tenue = libre).
2. **Pad 9 mantenido + ese knob** = su segundo destino elegido (pad 9 en blanco).
3. En una página de sección, **Duplicate + knob** escribe ese parámetro como segundo destino (el knob parpadea en blanco).
4. Girar el knob de Macros 2 mueve los dos: el segundo va al mismo sitio de su recorrido que el primero (la primera vez salta ahí). Los carriles de Macros 2 al reproducirse también mueven el segundo.
5. **Clear + pad 9** con los pads a la vista = el segundo fuera; **pad 1 mantenido + knob** = los dos fuera.
6. Se guarda con el proyecto (byte 6 de los ajustes de los patrones de Synth 1 / 2; a cero en las 192 sesiones comprobadas).

Emulación: `python tools/emu_m2x2.py firmware/a7.52`.
