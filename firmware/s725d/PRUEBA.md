# S725D (diagnóstico)

Alpha 7.25 + trampas (UDF) en los 392 B que quedan del código de la unidad USB (Easy Start) + prueba de la SRAM de respaldo (4 KB en `0x40024000`) en cada arranque + lectura de memoria por USB + gestos del panel por USB.

1. Vaciar la caja negra con la versión de antes (`python tools/bbread.py --clear`), luego instalar S725D.
2. `python tools/bkpcheck.py`: cabecera (`BKP1`, arranques, relojes y causa del reinicio) y el patrón: tras la instalación «no header: lost» es lo esperado (primer arranque).
3. Apagar y encender: `bkpcheck` otra vez. Patrón intacto = la SRAM de respaldo se conserva sin corriente (batería en VBAT); «lost» = se pierde al apagar (vale como RAM, no como almacén).
4. Uso normal / pruebas de estrés un rato: `bkpcheck` (nadie más escribe ahí = 0 palabras cambiadas) y `python tools/bbread.py --firmware S725D` (sin captura = el código de la unidad USB no se ejecuta nunca).

Una captura con el PC en uno de los tramos de `tools/usbtrap.py` = ese tramo está vivo.
