# SC41.3 / Beta 1.3 — pack de la memoria interna de solo lectura

`circuittracks-4486-SC41.3.syx` — SHA-256 `8256aa62f7082fb7f866c30aac6d39504164740a630c4f75785165a2c24b2df4`, marca `SC41.3`.
`firmware/b1.3/circuittracks-4486-B1.3.syx` — SHA-256 `6f07376b5983a5e0350d4883ae9ed57a69bc735320afde9f43ca75017b8e8736`: el mismo código con la marca `B1.3` (**Beta 1.3**).

Es SC41.2 (ver `firmware/sc41.2/PRUEBA.md`) con:

**El pack de la memoria interna es de solo lectura para el mod.** Nada del mod escribe ni borra en él: guardar el sample capturado con el proyecto, los intercambios y copias de samples y patches hacia él, guardar patches del sinte o del sinte propio en él, copiar proyectos a él o borrarlo desde la vista de packs se niegan, y el LED de Save se enciende en rojo 1,5 s. Se puede seguir leyendo de él y copiar desde él a un pack de la tarjeta. Los guardados del propio aparato (Save de un proyecto, los patches que guarda el firmware original) no cambian.

## Qué probar
1. Carga el pack de la memoria interna (el primero de la vista de packs). Intenta guardar un patch del sinte propio (Clear + hueco dos veces) o del sinte (Clear + pad dos veces): no se guarda y el LED de Save parpadea en rojo un momento.
2. En ese pack, Duplicate + un hueco (A); carga un pack de la tarjeta y Duplicate + un hueco (B): la copia se hace (lectura del interno, escritura en la tarjeta).
3. Al revés (de la tarjeta al interno): no se hace, LED rojo.
4. Save de un proyecto en el pack interno: se guarda como siempre (es el guardado del aparato).

## Verificación en emulación
`emu_rodisk.py`: la escritura y el borrado del firmware original llamados desde la zona del mod: pack 0, o «el cargado» con el pack 0 cargado, se niegan con `0xFFFFFFFD` sin llegar al código original; un pack de la tarjeta (3, 31), o «el cargado» con uno de la tarjeta, llega; LED de Save rojo 1,5 s; la versión anterior lo deja pasar todo.
