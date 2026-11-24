# Alpha 7.43 — prueba

Alpha 7.43 = Alpha 7.42 + `tools/noinapp.py` (arreglo, 2026-11-24): **el firmware en marcha ignora una instalación; solo el bootloader instala.**

En el Circuit del usuario, instalaciones enviadas con el firmware en marcha escribieron trozos de las imágenes sobre los primeros 0x4D000 bytes del sistema de ficheros interno (pack 0 y ajustes perdidos). El actualizador del firmware en marcha usa la misma cola de peticiones a la memoria NOR que el sistema de ficheros y el disco USB; con dos a la vez una petición puede ejecutarse con la dirección o el búfer de otra. Ahora la cabecera de la actualización (`0x7C`, manejador `0x08039088`) se ignora: no se borra ni se escribe nada.

Instalar **solo en modo bootloader** (Scales + Preset + Note al encender).

## Probar
1. Instalar en modo bootloader: debe entrar como siempre.
2. Con el aparato encendido de forma normal, intentar enviar una versión con Components o con un instalador antiguo: no debe pasar nada (sin «pulsa Play», sin reinicio); el aparato sigue con la versión instalada.
3. Comprobar que el pack 0 y los ajustes siguen ahí.

Emulación: `python tools/emu_noinapp.py firmware/a7.43 firmware/a7.42`.
