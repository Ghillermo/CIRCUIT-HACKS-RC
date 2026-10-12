# SC11 — Knob Pitch como afinación en el modo cromático — plan de prueba

`circuittracks-4486-SC11.syx` — SHA-256 `476063e4e9993641228de11cded9008fe2311b54c62b211b577e479de8a5414c`
Imagen de 0x4D79C bytes, CRC 0xC6CD07D9, marca `SC11`.

Incluye todo SC10.

## Qué hace
En el modo cromático de drums (Shift + Preset), el **mando Pitch (macro 2)** funciona como **afinación del teclado**: un desplazamiento en semitonos que se suma a todas las notas de los pads.

- **Al activar el modo**, la posición actual del Pitch pasa a ser la referencia. Por ejemplo, con el Pitch en +3, la tónica de los pads suena 3 semitonos por encima del sample original. Así puedes afinar antes de entrar.
- **Al girar el mando dentro del modo**, el Pitch cambia como siempre (se oye al momento y se graba como automatización) y la afinación del teclado se desplaza lo mismo. Las notas siguientes de los pads mantienen el ajuste.
- Si el sample no está en Do, sube o baja el Pitch hasta que la tónica coincida con la del proyecto.
- El ajuste es por drum, como el modo. No se guarda al apagar.
- Los demás mandos y el Pitch fuera del modo cromático funcionan igual que antes.

## Cómo está hecho
- La afinación va en el byte +0x52 de la vista Preset de cada drum. El constructor lo pone a 0, junto con el flag del modo.
- El mando Pitch de los drums (slot 4 de la vtable 0x0805AADC) hace lo de stock y suma a la afinación el cambio realmente aplicado, si ese drum está en modo cromático.
- Pad en modo cromático: Pitch = nota de la escala + afinación, limitado a 0–127.
- La vista se localiza desde el mando así: `[[[0x200069E4]+0x40]+0x2C]`, el contenedor de vistas, más 0x8C + 4·drum, comprobando la vtable.

## Verificación en emulación
- Al activar el modo, la afinación vale Pitch − 64 en cada drum (probado con 64, 67, 52 y 64). El pad 0x13 suena a nota + afinación.
- Girar el mando +3, −5 y +9: el Pitch se escribe igual que en stock y la afinación lo sigue (3, −2, 7). El siguiente pad suena 7 semitonos más alto.
- Fuera del modo cromático, el mando no toca la afinación. Los mandos 4, 6 y 8 funcionan igual que en stock.
- Desactivar el modo restaura los colores de stock. Shift + Preset con un sinte sigue igual que en stock.
- Regresiones de SC10 (ARM y DSP), SC09, SC08, SC06, SC05 y SC04: pasan.
- Solo cambian dos comprobaciones antiguas, a propósito: el constructor pone a 0 cuatro bytes en lugar de dos, y el bit 28 ya se guarda (SC10).

## Pruebas en el aparato
1. Envía SC11. Elige un drum, pon el Pitch en 64 y pulsa Shift + Preset.
2. Toca la tónica (fila 2 desde abajo, primer pad). Gira el Pitch +2: suena 2 semitonos más agudo al momento. Toca otros pads: todos suenan 2 semitonos más agudos y la escala sigue correcta.
3. Sal del modo (Shift + Preset), pon el Pitch en otro valor y vuelve a entrar: la tónica parte de ese valor.

## Volver atrás
Envía SC10 (o anterior) con el cargador. Si no arrancara, enciende con Scales + Preset + Note.
