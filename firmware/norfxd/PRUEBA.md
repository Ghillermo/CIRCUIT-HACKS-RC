# NORFXD — diagnóstico (2026-11-24)

Firmware de stock + `tools/rdiag.py` con `NOR`: órdenes 18 / 19 / 20 para borrar, escribir y leer bloques de 4 KB de la memoria NOR interna con el dispositivo del propio firmware; borrar y escribir solo dentro de la partición del sistema de ficheros (NOR 0xD4000..). Sirve para reparar el sistema de ficheros interno del aparato del usuario (sector de arranque, FAT y directorio raíz pisados; el disco USB es de solo lectura). `tools/norfix.py check | write DUMP REPARADA`. Después, instalar la versión normal en modo bootloader.

Emulación: `python tools/emu_norfix.py firmware/norfxd`.
