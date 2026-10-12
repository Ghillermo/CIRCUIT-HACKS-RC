# SC21.3 — SC21.2 + los cuadros de los drums también al principio de la fila (vista Note de los drums)

`circuittracks-4486-SC21.3.syx` — SHA-256 `9091bd1f9cfcc24d556add67894738e156b37fba509162fa48a5a1cf58af43ec`
Imagen de 0x5d480 bytes, marca `SC21.3`. Es SC21.2 con un cambio pequeño; si falla, vuelve a SC21.2.

## Qué hace
En la vista **Note de un drum** (botón Note con un drum seleccionado) la fila de abajo muestra hoy los **cuatro cuadros de colores de los drums 1-4 a la derecha** (pads 29-32). Ahora aparecen **también al principio de la fila** (pads 25-28), con los mismos colores, y **suenan, graban y se sueltan igual** que los de la derecha (pad 25 = drum 1 … pad 28 = drum 4). Los de la derecha no cambian.

## Prueba
1. Selecciona Drum 1 (o 2, 3, 4) y pulsa Note: la fila de abajo debe tener los cuatro cuadros a la izquierda y los cuatro de siempre a la derecha, de los mismos colores.
2. Pulsa los pads 25-28: cada uno toca su drum (y graba si estás grabando), igual que el pad 29-32 correspondiente. Los cuadros de ambos lados se iluminan a la vez al pulsar.
3. Las demás vistas (Preset, Velocity) no cambian.

## Notas técnicas
- `tools/drumnote.py`: la clase de la vista Note de los drums (vtable `0x0805AD44`, un objeto en `[contenedor + 0xAC]` para los cuatro drums; el objeto del drum va incrustado). Slots 0 / 1 (pulsar / soltar): los pads 24-27 se reenvían como 28-31; slot 7 (LEDs): el getter de stock y luego copia las entradas 28-31 a 24-27 en cada llamada (el búfer es persistente).
