# SC40D — diagnóstico: escribir en la tarjeta después de guardar un proyecto

`circuittracks-4486-SC40D.syx` — SHA-256 `26e5261e2f4d13a92bfdc2d0838ef9e7449210a3912c5f5984f4921d8bc45d95`
Imagen de 0x68acc bytes, CRC 0x320c46dd, marca `SC40D`.

Es SC40 con una sonda. **No añade ninguna función**: comprueba si el mod puede escribir en la tarjeta justo después de que el aparato guarde un proyecto, que es lo que necesita «Master FX por sesión».

**Escribe en la tarjeta: úsalo con un pack de pruebas y ten copia.** Cada guardado de proyecto añade una marca de 16 bytes en el pack (en el hueco libre detrás del patch de sinte número 65 + proyecto; si ese patch no existe, lo crea vacío). No toca los proyectos, los samples, los patches de sinte ni los patches del sinte propio.

## Qué hacer
1. Carga un pack de pruebas. Guarda el proyecto (Save). Un segundo después el **botón Save se pone verde ~3 s**: escrito y releído bien. **Rojo** = falló. Si no cambia de color, la sonda no se disparó.
2. Guarda otra vez el mismo proyecto: verde otra vez.
3. Guarda el proyecto en otro hueco («guardar como»): verde.
4. Apaga y enciende. Carga los proyectos guardados: deben estar bien, con todo lo suyo (patrones, drums, huecos de Master FX).
5. **Duplica el pack** en un hueco vacío (vista de packs, Duplicate + pad). Carga el duplicado: **deben estar todos sus proyectos**. (Esto es lo que rompió un diagnóstico antiguo, SC34D.)
6. Cambia de pack y guarda un proyecto allí: verde.
7. Si puedes, con la tarjeta en el PC:
```bash
python tools/patchtool.py fxdiag E:/NN_PACK
```
   Debe listar una marca por proyecto guardado, con su contador (2 para el que guardaste dos veces).
8. Dime: los colores que viste en cada paso, si algún proyecto o pack quedó mal, y lo que lista el paso 7.

## Verificación en emulación
- `emu_sc40d.py`: el guardado del original sigue corriendo; nada se escribe durante el primer segundo; después se crea el registro con `0xFF`, se escribe la marca y se relee; segundo guardado = contador 2 con una sola escritura; un banco con patches solo cambia en el relleno de ese registro; una tarjeta que no guarda da LED rojo.
- **Sin comprobar en emulación:** justo lo que pregunta el diagnóstico (la convivencia con el guardado real y con el duplicado de packs).
