# SC402D — diagnóstico: ¿están libres los últimos 1000 bytes de un proyecto?

`circuittracks-4486-SC402D.syx` — SHA-256 `881fcc6854dc7447b1621cc3631b17d71bab21c116b0cfa75b28090065c22e4d`
Imagen de 0x68b1c bytes, CRC 0x12d29341, marca `SC402D`.

Es SC40.2 (sidechain y compresor incluidos) con una sonda. Un proyecto ocupa 160 780 bytes y los últimos 1000 parecen no usarse. Si es así y viajan con el proyecto, ahí se puede guardar Master FX por sesión (y más) sin que el mod escriba nada por su cuenta en la tarjeta.

**Qué hace:** justo antes de que el aparato guarde un proyecto, pone dos marcas en esos 1000 bytes. El **botón Save se queda en verde mientras el proyecto cargado las lleve** (rojo si solo lleva una).

**Usa un pack de pruebas:** los proyectos que guardes con esta build llevan las marcas. Son inofensivas si esos bytes no se usan, que es lo que se comprueba.

## Qué hacer
1. Carga un proyecto de pruebas. Save apagado (normal). Guárdalo: **Save se pone verde** y se queda.
2. Apaga y enciende. Carga ese proyecto: **¿verde?** Es la respuesta principal.
3. Comprueba que el proyecto suena y se comporta igual que antes (patrones, escenas, mixer, patches).
4. Carga un proyecto que no hayas guardado con esta build: Save normal (no verde).
5. Proyecto nuevo (Clear en la vista Projects): Save normal.
6. Guarda el proyecto verde en otro hueco: la copia, al cargarla, verde.
7. Duplica el pack y carga en el duplicado el proyecto marcado: verde.
8. Si puedes, con la tarjeta en el PC:
```bash
python tools/patchtool.py sessdiag E:/NN_PACK
```
   Lista los proyectos con marca, y avisa si algún proyecto **sin** marca tiene esos bytes distintos de cero (querría decir que el aparato sí los usa).
9. Dime el color en cada paso y lo que lista el paso 8.

## Verificación en emulación
- `emu_sc402d.py`: la cola del registro está a cero en el volcado; al guardar se escriben las dos marcas y nada más del registro cambia; el guardado del original sigue corriendo; LED verde / rojo / normal según las marcas.
- **Sin comprobar en emulación:** lo que pregunta el diagnóstico (que el aparato guarde, cargue y respete esos bytes).
