# SC35 — samples del pack en la tarjeta: guardar la captura, intercambiar samples, borrar un pack

`circuittracks-4486-SC35.syx` — SHA-256 `3eae83c6562aa5e12b2d04d822c97df384b1b126e91eabf68335e5aa2a25fb94`
Imagen de 0x62de8 bytes, CRC 0x138da116, marca `SC35`. Probado en emulación; **nada probado en el aparato todavía**.

Es **SC34.2** con tres funciones nuevas que **escriben en la tarjeta SD**. **Haz una copia de la tarjeta antes de probarlo**, y empieza con los packs de prueba (30 / 31).

## 1. Guardar la captura en el pack (con Save)
1. Graba una captura en Master FX (pad 32).
2. En la vista Preset de un drum, **Shift + pad dos veces** (como en SC34): ese sample suena con la captura.
3. Pulsa **Save** (guardar el proyecto). Además del proyecto, el aparato **guarda ese sample en el pack** como `PCM/NN_PCM.wav`: el antiguo se borra y el nuevo puede ser más largo o más corto.
   - Tarda unos segundos (más cuanto más larga sea la captura).
   - Solo se guarda si cabe en la memoria de samples del pack (~196 s en total). Si no cabe, no se escribe y el sample sigue sustituido solo hasta apagar.
   - Un segundo Save no vuelve a escribirlo si no ha cambiado.
4. Comprueba que se conserva: cambia de pack y vuelve, o apaga y enciende, y toca ese sample.

## 2. Intercambiar dos samples
En la vista Preset de un drum:
1. **Mantén Duplicate** y toca el **pad A**: parpadea en azul.
2. Toca el **pad B**: los dos samples se intercambian en el pack (los ficheros) y en lo que suena, al momento. Los dos ficheros pasan a llamarse `NN_PCM.wav`.

Tocar A otra vez cancela. Soltar Duplicate también cancela. Funciona entre las dos páginas de samples.

## 3. Borrar un pack
En la vista de packs (donde los pads eligen el pack), **Clear se enciende en blanco tenue**:
1. **Mantén Clear** y toca el pad del pack: ese pad y Clear parpadean en rojo.
2. Suelta y **pulsa Clear otra vez** antes de 5 s: el pack se borra.
- El pack cargado no se puede borrar.
- **Shift + Clear** sigue siendo el metrónomo.
- Si pasan más de 5 s, la pregunta se anula.
- Como con el firmware de stock, el pad del pack borrado sigue encendido y **el hueco se puede reutilizar después de apagar y encender**.

## Pruebas en el aparato (en los packs 30 / 31)
1. Guardar: captura → Shift + pad dos veces → Save → apagar y encender → el sample suena con la captura.
2. Intercambiar: Duplicate + pad 1 + pad 2 → suenan cambiados; tras apagar y encender siguen cambiados.
3. Borrar: carga el pack 31, borra el 30 → reinicia → el hueco 30 queda libre y se puede duplicar el 31 en él.
4. Dime si algo tarda demasiado o se comporta raro. Con el aparato conectado por USB lo puedo comprobar yo desde el PC (el diagnóstico remoto va incluido).

## Verificación en emulación
`emu_sc35.py`:
- todas las pruebas de SC34.2;
- **guardar:** fichero exacto (cabecera + muestras) en uno y en varios trozos; no se repite tras guardarse; no se escribe si no cabe; el tick marca la ranura como «sin guardar» al sustituir;
- **intercambiar:** por la ruta real de pads, con basura en la memoria de estado; ficheros y tabla cambiados; cancelar; sin Duplicate no hace nada;
- **borrar pack:** por las rutas reales de pad y botón; la pregunta caduca a los 5 s; Shift + Clear no borra; el pack actual nunca; LED de Clear y del pad.

## Volver atrás
Envía SC34.2.
