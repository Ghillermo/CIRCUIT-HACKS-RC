# SC12 — Afinación fina en cents de los drums — plan de prueba

`circuittracks-4486-SC12.syx` — SHA-256 `0c4993a91b7f32f49d087301bee15d38a3de7aeff400651b59052f1834bac93b`
Imagen de 0x4DBCC bytes, CRC 0xE669FA76, marca `SC12`.

Incluye todo SC11.

## Qué hace
Cada drum tiene una **afinación fina** de **−100 a +100 cents**, en pasos de 1 cent. Sirve para reafinar un sample que no está en ningún tono.

- La afinación fina se aplica **siempre** a ese drum: pads, secuenciador, modo normal y modo cromático. Se suma al Pitch de semitonos.
- **En el modo cromático (Shift + Preset):**
  - **Mando Pitch:** ajusta la afinación fina, 1 cent por paso, y se oye al momento. No cambia el Pitch ni graba automatización.
  - **Shift + mando Pitch:** desplaza en semitonos, como en SC11.
- Fuera del modo cromático, el mando Pitch funciona como siempre. La afinación fina se mantiene.
- Llega al tope en ±100 cents. Para mover más de un semitono, usa Shift + Pitch.
- **No se guarda:** al apagar vuelve a 0 y no queda en el proyecto. Es por drum, no por pista ni por patrón.

## Cómo está hecho
- **Almacenamiento:** los cents se guardan con signo en el byte +0x53 de la vista Preset de cada drum. El constructor lo pone a 0 desde SC11.
- **Conversión:** los cuatro manejadores DSP de los drums llaman a un envoltorio en lugar de a la conversión de SC09. El envoltorio calcula: palabra = tabla de semitonos[Pitch] × 2^(cents/1200). Usa una tabla Q16 de 201 entradas, `umull`, y limita a 0x7FFFFF.
- **Mando:** la vtable 0x0805AADC, slot 4, apunta a un nuevo manejador. En modo cromático y sin Shift suma el giro a los cents y marca como sucio el grupo DSP de ese drum, `0x0803BDCC(0x10, 2+7·drum)`, para que se reenvíe. Con Shift llama al manejador de SC11.

## Verificación en emulación
- **Palabra DSP:**
  - Para los 4 drums, Pitch 0/30/64/100/127 con 0 cents: idéntica a SC11.
  - Con ±1, 37, −50 y ±100 cents: coincide con el cálculo exacto.
  - Precisión de 1 cent: error menor de 0,03 cents.
  - Un valor fuera de rango se ignora.
  - Los cents de un drum no afectan a otro.
- **Mando en modo cromático, los 4 drums:**
  - Giros +7, −20, +300, −500 y +100 dan 7, −13, +100 (tope), −100 (tope) y 0.
  - Sin escritura de Pitch. Se reenvía el grupo del drum. La afinación de semitonos no cambia.
- **Shift + mando:** igual que SC11.
- **Fuera del modo:** el mando funciona como stock y los cents se conservan. Los mandos 4, 6 y 8 funcionan como stock.
- **Regresiones:** SC11, SC10 (ARM y DSP), SC09, SC08, SC06/07 y SC04 pasan.
- **Fallos que cambian a propósito:**
  - el giro del Pitch sin Shift en modo cromático ahora es afinación fina, no la de SC11;
  - el constructor pone a 0 cuatro bytes;
  - el bit 28 se guarda desde SC10.

## Pruebas en el aparato
1. Envía SC12. Elige un drum con un sample de tono claro (un bajo o un tom), pon el Pitch en 64 y pulsa Shift + Preset.
2. Mantén pulsado un pad o lanza un patrón y gira el Pitch despacio. El tono debe moverse muy poco a poco: +100 pasos equivalen a 1 semitono.
3. Afina contra otra pista (un sinte tocando la tónica) hasta que deje de "batir".
4. Mantén Shift y gira el Pitch: salta por semitonos como en SC11.
5. Sal del modo cromático (Shift + Preset). El secuenciador y los pads normales siguen afinados.
6. Apaga y enciende: la afinación fina vuelve a 0.

## Volver atrás
Envía SC11 (o anterior) con el cargador. Si no arrancara, enciende con Scales + Preset + Note.
