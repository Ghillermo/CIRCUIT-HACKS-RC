# SC37.7 — copias entre packs en su sitio y memoria de importación que se reinicia

`circuittracks-4486-SC37.7.syx` — SHA-256 `976432efddbe146c17922e20a38a76c8c118a48c525d8b12e8efc65f30613f88`
Imagen de 0x65cf0 bytes, CRC 0xfba09786, marca `SC37.7`.

Es SC37.6 con:

1. **La copia de un sample desde otro pack va al sitio del sample que sustituye** cuando cabe (igual o más corto que lo que el aparato reservó para él). Entonces no gasta nada de la memoria de importación (≈ 44 s por sesión). Si el nuevo es más largo, va a esa memoria como antes.
2. **Esa memoria se vacía sola** cuando ya ningún drum la usa, por ejemplo tras recargar el pack.

En la tarjeta no cambia nada: la copia se escribe en la SD en el momento, como antes.

## Qué probar (packs de prueba, con copia de la SD)
1. Copia entre packs un sample sobre otro más largo (Duplicate + pad en un pack, Duplicate + pad en el otro): suena al momento, sin clic al final; al recargar el pack suena igual.
2. Copia un sample sobre otro más corto: también suena al momento (este va a la memoria de importación).
3. Haz muchas copias seguidas (más de 44 s de audio en total, sobre samples más largos o iguales): no debe dejar de copiar.
