# RC0.4 — quinta versión candidata

`circuittracks-4486-RC0.4.syx` — SHA-256 `3d1f116dbad45289264e1504fbc0abce4080a1cd0eccecf88a380991fbcd2276`
Imagen de 0x66010 bytes, CRC 0x6525e9f9, marca `RC0.4`.

Es **RC0.3 + los arreglos** de SC38.2-SC38.6, sin sus funciones nuevas (esas van en BETA0). Detalle: [`CHANGELOG.md`](../../CHANGELOG.md).

## Qué probar
1. Parado: Shift + pad 32 (Master FX), Play: la captura empieza en el primer pulso y dura ese compás (`firmware/sc38.4/PRUEBA.md`).
2. Shift + pad 7: el sample sigue en bucle al soltar, también fuera de Master FX; el 7 otra vez (o el pad 8) lo para; el modo loop (K2 azul) solo suena mientras se mantiene (`firmware/sc38.5/PRUEBA.md`).
3. Duplicate entre packs a un pad vacío: samples (Preset de drums) y patches (Preset de sinte); un patch lejos del final del banco deja vacíos los huecos de en medio (`firmware/sc38.6/`).
4. Vista de packs (Shift + Projects): Clear blanco fijo al abrirla; Clear, pack, Clear borra como antes.
