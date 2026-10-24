# RC2.07 / RC2.07S (R207 / R207S) = RC2.06 / RC2.06S + el arreglo de la longitud fija

`firmware/r207/circuittracks-4486-R207.syx` — SHA-256 `44cb3da51ebe2fe8d756075d9511877115106f8da7e3bc3e3372e9500ba07794`, marca `R207` (**RC2.07**).
`firmware/r207s/circuittracks-4486-R207S.syx` — SHA-256 `2371c41f227623cd4adf1a8bd802e3cf1564dddc4ebf03bbc736f586b3c8d54e`, marca `R207S` (**RC2.07S**).

**Arreglo de la longitud fija** (`stepgate.use_v4()`; el usuario, 2026-10-24: «en la funcion de fixed length, cambiar el length no actualiza los leds ni cierra la vista. ademas el length no se aplica a todos los pasos, especialmente el paso 1 o los pasos que han sido previamente escritos y borrados»):
- **Los LEDs:** el búfer de LEDs de la vista Micro Step es del stock y solo se redibuja cuando el stock cambia algo; el selector escribía encima y, al elegir una longitud (o tocar el pad 31 / 32, o salir de la vista), los pads 17-30 se quedaban como los había dejado el selector. Ahora, tras cada pulsación nuestra, el stock redibuja la vista (`0x0804CB30`), y también cuando la tarea de LEDs cierra el selector.
- **La longitud:** se ponía al soltar el primer pad, pero soltar un pad de paso no pasa por la vista de pista (los pasos son objetos aparte, clase `0x0805ADB4`): si se soltaba antes el paso, o se pulsaba la nota antes que el paso, la nota se quedaba con el gate del stock (6, o el más largo del paso: en un paso con notas, como el paso 1 de muchos proyectos, el de esas notas); de un acorde, solo la última nota la recibía. Ahora la longitud se pone al añadir cada nota (`0x0804B094` llamado como subrutina desde su cabeza; la unidad de esa nota en el paso mantenido a 6 × la longitud, su ligadura conservada). El gate por pulsación (pad 32) también termina al soltar el pad de paso (cabeza de la ranura 1 de los pasos).

## Qué probar
1. Synth 1, vista Micro Step (Gate dos veces): pad 31 abre el selector; elige 4 pasos (pad 20): el selector se cierra y los pads 17-30 vuelven a enseñar los micropasos al momento; el pad 31 naranja.
2. Con la longitud fija encendida, en la vista Note: mantén un paso y toca una nota, y suelta primero el **paso**: la nota dura 4 pasos. Lo mismo pulsando primero la nota y luego el paso, en el paso 1, en un paso borrado con Clear y con un acorde (dos notas: las dos de 4 pasos).
3. Abre el selector y sal de la vista sin elegir: al volver, la vista Micro Step se ve normal.
4. Pad 32 (gate por pulsación): mantén paso + nota y suelta primero el paso: el gate es el tiempo que la mantuviste.
5. Lo demás, como RC2.06 (`firmware/r206/PRUEBA.md`).

## Verificación en emulación
- `emu_sc46_1.py` (el selector y sus LEDs, el cierre por la tarea de LEDs, la longitud en todos los órdenes de pulsación, el paso 1, un paso borrado, un acorde, el gate por pulsación con el paso soltado primero; RC2.06: los LEDs del selector se quedan, el paso soltado primero y la primera nota del acorde con el gate del stock).
