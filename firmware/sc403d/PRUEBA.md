# SC403D — diagnóstico: ¿están libres los bytes de ajustes de cada patrón?

`circuittracks-4486-SC403D.syx` — SHA-256 `116167a5a6143bab40ff965c3248199ae583c8698cfa9b31d0fdf455cc427367`
Imagen de 0x68bf8 bytes, CRC 0x15be417e, marca `SC403D`.

Es SC402D (incluye su prueba de la cola del proyecto, LED de Save) con una segunda sonda para las **cadenas de patrones**. Cada patrón tiene un bloque de ajustes de 40 bytes del que el aparato solo usa 4 (primer paso, último paso, sync rate, dirección). Si los otros 36 viajan con el patrón, ahí caben las repeticiones y los dos patrones siguientes de cada cadena.

**Qué hace:** en el **primer** guardado de un proyecto marca esos 36 bytes en sus 64 patrones (8 pistas × 8), cada uno con su propio número. Los guardados siguientes no vuelven a marcar, así que se ve lo que el aparato hace con ellos. El **botón Octave ▼**: verde = los 64 patrones llevan su marca; rojo = solo algunos; normal = ninguno.

**Usa un pack de pruebas** (como con SC402D). Con esta build no hace falta instalar SC402D: sus pasos valen aquí.

## Qué hacer
1. Carga un proyecto de pruebas con notas en varios patrones. Guárdalo: **Save verde** (SC402D) y **Octave ▼ verde**.
2. Comprueba que suena igual: longitud de los patrones, dirección, sync rate, cadenas y escenas como antes.
3. Apaga y enciende, carga ese proyecto: **¿Octave ▼ verde?** (y Save verde).
4. Cambia en un patrón el último paso, la dirección y el sync rate; guarda; apaga, enciende y carga: ¿sigue verde?
5. **Duplica** un patrón sobre otro. ¿Verde o rojo? Guarda.
6. **Borra** un patrón. ¿Verde o rojo? Guarda.
7. Borra una pista entera o cambia de patch / sample si quieres: apunta si cambia el color.
8. Con la tarjeta en el PC:
```bash
python tools/patchtool.py patdiag E:/NN_PACK
```
   Dice, proyecto por proyecto, qué patrones conservan su marca, cuáles llevan la de otro (copiados), cuáles están a cero (borrados) y qué bytes ha cambiado el aparato.
```bash
python tools/patchtool.py sessdiag E:/NN_PACK
```
9. Dime los colores de cada paso y lo que listan los dos comandos.

**Lo que esperamos:** verde tras apagar (los bytes se guardan); al duplicar, el destino con la marca del origen (viajan con el patrón: rojo en el aparato, «copiado» en el PC); al borrar, a cero. Cualquier otra cosa también sirve: dice qué bytes no se pueden usar.

## Verificación en emulación
- `emu_sc403d.py`: las 64 direcciones coinciden con las que lee el original (`0x0803C6D6`); bytes 4..39 a cero en el volcado; el primer guardado escribe las marcas y nada más (salvo las de la cola); el segundo no las reescribe; LED verde / rojo / normal; `patchtool.py patdiag` sobre ese registro.
- **Sin comprobar en emulación:** lo que pregunta el diagnóstico (qué hace el aparato con esos bytes al cargar, duplicar y borrar).
