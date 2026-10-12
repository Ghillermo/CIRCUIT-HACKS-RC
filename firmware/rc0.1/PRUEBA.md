# RC0.1 — segunda versión candidata

`circuittracks-4486-RC0.1.syx` — SHA-256 `dea625dda36e48ed494839063671996f60d92a889072a52eb72f3fdcd2f68244`
Imagen de 0x65a3c bytes, CRC 0x5c91a23a, marca `RC0.1`.

Es **SC37.4** con otro nombre: el mismo código, solo cambia la marca. Qué probar: [`../sc37.4/PRUEBA.md`](../sc37.4/PRUEBA.md).

Novedades frente a RC0:
1. **Duplicate en la vista Preset de Synth 1 / 2 y de drums** (en RC0 no se encendía ni se podía mantener en esas vistas).
2. **Copiar samples y patches de sinte entre packs**: Duplicate + pad A en un pack, Duplicate + pad B en otro; el pack de A no cambia. Dentro del mismo pack, Duplicate + A + B intercambia.
3. **Borrar un pack con pulsaciones**: vista de packs, Clear, el pack, Clear (en RC0 no funcionaba). El LED de Clear no se enciende durante el borrado.
4. **Intercambios de samples sin clic** (los ficheros se mueven tal cual).
5. **Cambiar de motor (pad 27) con una nota mantenida sin clic**; girar SUS con la nota mantenida se desliza.
6. **Pad 28** (uno / dos osciladores) apagado salvo con oscilador o VA-drum.
7. **Dos huecos con Glitch** a la vez ya no se copian los knobs.
8. **Colores:** Vinyl en melocotón; en Setup, pad 22 (reverb → tira 3) crema y pad 23 (delay → tira 4) melocotón.

**Haz una copia de la tarjeta SD antes de instalar.** Si no quieres arriesgarla, usa RC0.1S.
