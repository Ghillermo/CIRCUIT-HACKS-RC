# RC0.9 = RC0.8 + pack de la memoria interna de solo lectura

`circuittracks-4486-RC0.9.syx` — SHA-256 `832de165feb4523c680d47e75db96b03da13db1faeabbca828b8886828fc3238`, marca `RC0.9`.

**El pack de la memoria interna es de solo lectura para el mod.** Nada del mod escribe ni borra en él: guardar el sample capturado con el proyecto, los intercambios y copias de samples y patches hacia él, guardar patches del sinte o del sinte propio en él, copiar proyectos a él o borrarlo desde la vista de packs se niegan, y el LED de Save se enciende en rojo 1,5 s. Se puede seguir leyendo de él y copiar desde él a un pack de la tarjeta. Los guardados del propio aparato (Save de un proyecto, los patches que guarda el firmware original) no cambian.

## Qué probar
1. Carga el pack de la memoria interna (el primero de la vista de packs). Intenta guardar un patch del sinte propio (Clear + hueco dos veces) o del sinte (Clear + pad dos veces): no se guarda y el LED de Save parpadea en rojo un momento.
2. En ese pack, Duplicate + un hueco (A); carga un pack de la tarjeta y Duplicate + un hueco (B): la copia se hace (lectura del interno, escritura en la tarjeta).
3. Al revés (de la tarjeta al interno): no se hace, LED rojo.
4. Save de un proyecto en el pack interno: se guarda como siempre (es el guardado del aparato).

## Verificación en emulación
`emu_rodisk.py`: la escritura y el borrado del firmware original llamados desde la zona del mod: pack 0, o «el cargado» con el pack 0 cargado, se niegan con `0xFFFFFFFD` sin llegar al código original; un pack de la tarjeta (3, 31), o «el cargado» con uno de la tarjeta, llega; LED de Save rojo 1,5 s; la versión anterior lo deja pasar todo.
