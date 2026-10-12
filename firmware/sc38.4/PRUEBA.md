# SC38.4 — arreglos tras probar SC37.4–SC38.3

`circuittracks-4486-SC38.4.syx` — SHA-256 `77b087fc1185649830d526d5f04c17babb517b8721d83c5be9a07f4609fcca0a`
Imagen de 0x66250 bytes, CRC 0xe7fb52a8, marca `SC38.4`.

Es SC38.3 con:
1. **Captura armada desde parado:** Shift + pad 32 y Play graba desde el primer pulso hasta el final de ese compás (SC38.2 aún empezaba en el segundo).
2. **Duplicate entre packs a un hueco vacío:** samples y patches. Un patch en un banco más corto rellena también los huecos vacíos anteriores con la misma copia (el banco no puede tener huecos).
3. **Vista de packs:** Clear blanco fijo desde que se abre; al preguntar y confirmar, como en SC37.8.

## Qué probar
1. Parado: Shift + pad 32, Play: el pad 32 se ilumina al instante y la captura es el primer compás.
2. Copiar un patch de otro pack a un hueco vacío (pad apagado) de la Preset del sinte: queda copiado y suena; los huecos vacíos anteriores de ese banco también se llenan.
3. Copiar un sample de otro pack a un hueco vacío de la Preset de drums.
4. Shift + Projects: Clear blanco fijo; Clear, pack, Clear borra como antes.
