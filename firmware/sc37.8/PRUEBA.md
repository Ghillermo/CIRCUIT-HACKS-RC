# SC37.8 — vista de packs: borrar con los packs visibles y Clear fijo

`circuittracks-4486-SC37.8.syx` — SHA-256 `217de3d35c9a3686d305e088483eab3ed0ce443af144a5d5563cea6c48ef3e1b`
Imagen de 0x65d24 bytes, CRC 0x91cb3480, marca `SC37.8`.

Es SC37.7 con el arreglo de lo que viste en la vista de packs:
- **Clear:** blanco tenue en la vista de packs y **blanco fijo** mientras el borrado espera la confirmación.
- **Pads:** al tocar Clear, los packs que se pueden borrar **parpadean** (el cargado no) y **vuelven a su color** al confirmar, al cancelar o a los 5 s. Antes se apagaban y se quedaban apagados.

## Qué probar
1. Shift + Projects: Clear tenue.
2. Toca Clear: Clear fijo; parpadean los packs con contenido salvo el cargado.
3. Toca un pack: solo ese parpadea; Clear otra vez: se borra, los demás packs se ven normales y Clear vuelve a tenue.
4. Toca Clear y espera 5 s sin tocar nada: todo vuelve a verse normal.
