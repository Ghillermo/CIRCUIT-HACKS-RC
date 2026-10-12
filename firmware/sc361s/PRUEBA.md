# SC361S — versión «más segura» de SC36.1 (sin escrituras propias en la SD)

`circuittracks-4486-SC361S.syx` — SHA-256 `f8d646fbb1788a855dfad14894054446e1f156199ae3496e26c951eb7b3d2bf3`
Imagen de 0x640cc bytes, CRC 0xaf7978be, marca `SC361S`.

Es **SC36.1 sin ninguna función que escriba ficheros en la tarjeta SD por su cuenta**.

**Se quita:**
- **guardar capturas en el pack:** Save vuelve a guardar solo lo de stock;
- **intercambiar samples:** Duplicate + pad + pad;
- **borrar packs:** Clear + pack, luego Clear;
- **el diagnóstico remoto por USB:** lectura, escritura y borrado de elementos de la SD.

**Se mantiene:**
- todo lo demás: sinte granular, Glitch, secuenciador de efectos, Master FX, drums, step-drummer y el resto;
- nuestros ajustes siguen guardándose en el proyecto. Van en los bytes reservados del formato de proyecto del stock, que escribe el **Save de stock**, como desde SC19.

Sustituir un drum por la captura (Shift + pad dos veces) sigue funcionando, pero solo en memoria: no se guarda en el pack.

## Cuándo usarla
Si quieres el mod pero prefieres no arriesgar los proyectos ni los samples de la tarjeta. No se han reportado fallos de las funciones quitadas, pero son las únicas que escriben, crean o borran ficheros por su cuenta.

## Verificación en emulación
- `emu_sc36_1.py` y regresiones de SC25 y SC31 sobre SC361S.
- `emu_sc36_dsp.py`: el DSP es el de SC36.
- El manifiesto no tiene `packio` ni `rdiag`.

## Volver atrás
Envía SC36.1 (con las funciones de la SD) o el firmware oficial.
