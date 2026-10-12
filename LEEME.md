# CIRCUIT-HACKS — formato de actualización y seguridad

Firmware de referencia: **Circuit Tracks 1.2.1, build 4486** (la última publicada en Components). English below.

## Contenido
- El firmware oficial **no se incluye**. Descárgalo de Novation ([circuittracks-firmware-4486.syx](https://components.novationmusic.com/api/v2/firmwares/168/file)); `stock/SHA256SUMS.txt` guarda sus SHA-256 y `tools/patch_official.py` lo comprueba y lo copia a `stock/`.
- `tools/ct_fw.py` — convierte .syx ↔ .bin y recalcula el CRC (Python 3, sin dependencias).
  - `python tools/ct_fw.py OFICIAL.syx` → decodifica y comprueba el CRC y la ida y vuelta.
  - `python tools/ct_fw.py imagen.bin -o salida.syx` → codifica.

## Formato de actualización (verificado)
| Mensaje | Contenido |
|---|---|
| `71` UPDATE_INIT | `01 64` (Circuit Tracks) + versión de protocolo 0x572 |
| `7C` UPDATE_HEADER | versión, **tamaño** (8 nibbles), **CRC-32/MPEG-2** (8 nibbles) |
| `72` UPDATE_WRITE ×N | bloques de 32 bytes en 37 bytes de 7 bits, desde el bloque 1 |
| `73` UPDATE_FINISH | bloque 0 (tabla de vectores) |

## Seguridad: lo que hace el bootloader (analizado en el volcado público de userx14)
1. Al arrancar lee 150 ms los botones. **Scales + Preset + Note** → se queda en modo bootloader (USB-MIDI) y **no ejecuta la aplicación**.
2. La actualización se guarda primero en la flash NOR externa. Solo se copia a la flash interna si el producto coincide y el **CRC de la imagen guardada es correcto**. Un envío cortado o corrupto no se instala.
3. Solo borra los sectores 2–5 (0x08010000–0x0807FFFF). **El bootloader (0x08000000–0x0800FFFF) nunca se toca.**
4. Tamaño máximo aceptado: 0x70000 bytes (448 KB). La 4486 ocupa 0x4CDDC → quedan ~140 KB para código nuevo.
5. La aplicación de stock no contiene las claves de desbloqueo de la flash interna: no puede reescribir el bootloader.

**Conclusión:** aunque un firmware modificado se cuelgue al arrancar, encender con Scales + Preset + Note y reinstalar el firmware oficial desde Components lo recupera.

## Reglas de trabajo
- Nunca enviar nada que no salga de `ct_fw.py` con el CRC verificado.
- Nunca escribir en la flash interna ni en las option bytes desde código propio.
- Antes de cada prueba en hardware, tener a mano el firmware oficial y Components.

---

# CIRCUIT-HACKS — update format and safety (English)

Reference firmware: **Circuit Tracks 1.2.1, build 4486** (the latest one published in Components).

## Contents
- The official firmware is **not included**. Download it from Novation ([circuittracks-firmware-4486.syx](https://components.novationmusic.com/api/v2/firmwares/168/file)); `stock/SHA256SUMS.txt` keeps its SHA-256 and `tools/patch_official.py` checks it and copies it to `stock/`.
- `tools/ct_fw.py` — converts .syx ↔ .bin and recomputes the CRC (Python 3, no dependencies).
  - `python tools/ct_fw.py OFFICIAL.syx` → decodes and checks the CRC and the round trip.
  - `python tools/ct_fw.py image.bin -o out.syx` → encodes.

## Update format (verified)
| Message | Content |
|---|---|
| `71` UPDATE_INIT | `01 64` (Circuit Tracks) + protocol version 0x572 |
| `7C` UPDATE_HEADER | version, **size** (8 nibbles), **CRC-32/MPEG-2** (8 nibbles) |
| `72` UPDATE_WRITE ×N | 32-byte blocks in 37 bytes of 7 bits, from block 1 |
| `73` UPDATE_FINISH | block 0 (vector table) |

## Safety: what the bootloader does (analysed in userx14’s public dump)
1. At power-on it reads the buttons for 150 ms. **Scales + Preset + Note** → it stays in bootloader mode (USB-MIDI) and **does not run the application**.
2. The update is first stored in the external NOR flash. It is only copied to the internal flash if the product matches and the **CRC of the stored image is correct**. A cut or corrupt transfer is not installed.
3. It only erases sectors 2–5 (0x08010000–0x0807FFFF). **The bootloader (0x08000000–0x0800FFFF) is never touched.**
4. Largest accepted size: 0x70000 bytes (448 KB). 4486 takes 0x4CDDC → ~140 KB left for new code.
5. The stock application does not hold the unlock keys of the internal flash: it cannot rewrite the bootloader.

**Conclusion:** even if a modified firmware hangs at power-on, powering on with Scales + Preset + Note and reinstalling the official firmware from Components recovers it.

## Working rules
- Never send anything that does not come out of `ct_fw.py` with a verified CRC.
- Never write the internal flash or the option bytes from our own code.
- Before every hardware test, keep the official firmware and Components at hand.
