# S715D2 (marca `S715D2`) — diagnóstico

= S715D + vigilancia DWT de `0x20043610` (legítimo `0x0805ADA8`) y `0x20042988` (legítimo `0x0805ACC8`). Imagen `0x6ffb0`.

Con el aparato por USB, en el pack de usar y tirar:

    python tools/scenestress_dev.py 3600 --seed 1

Si una escritura deja mal una de las dos palabras, la caja negra se congela como fallo del vector 12 con el PC / LR de quien escribió (la herramienta lo enseña al final). Después el aparato puede colgarse o reiniciarse: el registro queda.
