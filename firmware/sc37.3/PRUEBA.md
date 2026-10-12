# SC37.3 — intercambios sin clic: los ficheros se mueven tal cual

`circuittracks-4486-SC37.3.syx` — SHA-256 `7b20bf336faff2dc0c4133047ddcb702663877605d3a54af36ab758efe5f56d8`
Imagen de 0x657d0 bytes, CRC 0x70b9158d, marca `SC37.3`.

Es SC37.2 con el arreglo del **clic al final de los samples intercambiados**.

**Causa:** el mod reconstruía el sample a partir de la memoria del DSP. Pero el aparato solo carga cada fichero hasta su último bloque completo de 512 bytes y empieza 2 muestras más tarde. El fichero reescrito perdía las 2 primeras muestras y terminaba con un corte seco a cero: el clic. Comprobado en tu SD: `29_PACK/PCM/09_PCM.wav` frente a `00_Circuit Tracks Factory Pack/PCM/09_HousePercB3.wav`, y `30_PACK/PCM/11_PCM.wav` frente al 13 de DLR.

**Ahora** los intercambios (dentro del pack y entre packs) mueven los **ficheros exactos**, byte a byte. La memoria libre del DSP sirve de almacén temporal: el fichero A se copia allí, el fichero B se copia sobre A y la copia de A se escribe en B. Si algo falla, se vuelven a poner los ficheros desde las copias. El sample que llega de otro pack suena al momento, con silencio de relleno detrás, como hace el aparato.

- Un drum sustituido por la captura (SC34) que aún no se ha guardado se intercambia como antes (desde la memoria del DSP).
- Los ficheros que ya escribieron SC35–SC37.2 siguen con el clic: vuelve a copiarlos desde tu copia de la SD si te molesta.

## Qué probar (packs 29 / 30, con copia de la SD)
1. Intercambia dos samples dentro del pack: no debe haber clic al final, ni al momento ni tras recargar el pack.
2. Entre packs (Duplicate + pad, cargar el otro pack, Duplicate + pad): lo mismo.
3. En el PC: cada fichero intercambiado debe ser **idéntico** al original que le corresponde (mismo tamaño y contenido).
