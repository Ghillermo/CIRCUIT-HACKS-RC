# SC38.2 — captura armada desde Play

`circuittracks-4486-SC38.2.syx` — SHA-256 `9d6ecebdda41e871472d6997eedafa66e7d8afab250f583df78d70b7cd5dd741`
Imagen de 0x66030 bytes, CRC 0xb3f50c65, marca `SC38.2`.

Es SC38.1 con la **captura armada** corregida: con el transporte parado, **Shift + pad 32** (Master FX o vista FX) arma la captura; al pulsar **Play** empieza a grabar en ese momento y termina **al final de ese compás**. Antes empezaba un compás tarde y terminaba al final del segundo.

## Qué probar
1. Parado: Shift + pad 32 (parpadea). Play: el pad 32 se ilumina al instante y se apaga al acabar el primer compás.
2. Toca el sample (pad 7) en loop: un compás exacto, desde el primer pulso.
3. Con el transporte en marcha, Shift + pad 32: espera a la siguiente línea de compás y graba un compás (como antes).
