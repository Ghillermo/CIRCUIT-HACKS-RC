# S721D2 (marca `S721D2`) — diagnóstico

= S721D sin las trampas en el código que el arranque alcanza por sus tablas relativas (`stocktrap.use_boot()`): S721D se colgaba al
encender (trampa en `0x0801A7EA`, el borrado de la RAM del arranque de C). Quedan 8 trozos del stock que siguen sin alcanzarse con esas
tablas (348 B) + los 36 B finales del manejador de disco cortado. Emulado desde el vector de reset: sin trampas hasta la espera del reloj.

    python tools/bbread.py --clear
    python tools/scenestress_dev.py 3600 --seed 7
    python tools/panelstress_dev.py 1800

y uso normal; al final `python tools/bbread.py --firmware S721D2`: estado 0 = ningún trozo ejecutado. Si no aparece por USB al encender:
modo bootloader (Scales + Preset + Note), instalar la Alpha 7.22 y leer la caja negra sin borrarla.
