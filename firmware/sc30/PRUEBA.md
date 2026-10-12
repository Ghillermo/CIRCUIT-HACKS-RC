# SC30 — SC29 + Master FX que se mantiene entre sesiones, y el guardado del proyecto arreglado

`circuittracks-4486-SC30.syx` — SHA-256 `c6ddb16e7b460df6726e03081b77bfcfc2467eba60dc76009794d1be73141e18`
Imagen de 0x613a8 bytes, CRC 0xf3bf5dbf, marca `SC30`. Reserva: **SC29**. Probado en emulación; **nada probado en el aparato**.
Sin RAM nueva, sin cambios en el DSP.

## 1. Master FX entre sesiones
- **Al cambiar de sesión** (cargar otro proyecto o empezar uno nuevo):
  - las **asignaciones de la fila inferior** (huecos, con su copia de parámetros) y los **parámetros de los efectos** (K1-K4 de cada efecto) **se mantienen**;
  - como antes, los efectos fijados y el song pointer se apagan.
- **Al apagar:**
  - las asignaciones se guardan con el proyecto, al guardarlo; al encender se cargan del proyecto con el que arranca el aparato;
  - los parámetros de la fila superior **no sobreviven al apagado** (vuelven a sus valores iniciales): no queda sitio libre en el proyecto ni en los ajustes del aparato.
- Lo demás sigue **por proyecto**: los knobs nuevos de drums y la fuente de los sintes.

## 2. Arreglo: el guardado del proyecto no guardaba lo nuestro (desde SC20)
Desde SC20, guardar un proyecto **no escribía** las asignaciones de Master FX, la fuente de los sintes ni la firma que marca el proyecto como nuestro.
- Al volver a cargarlo, el proyecto se leía como vacío y se borraban también los valores de los knobs nuevos de drums.
- **Causa:** el guardado se saltaba la copia si había cualquier bit puesto en un byte de estado, y desde SC20 el tick de VCF / VCA deja siempre puesto uno (el bit 3, «inicializado en esta sesión»). Ahora solo se salta mientras hay una carga pendiente.
- Los proyectos guardados con SC20–SC29 no llevan la firma: al cargarlos con SC30, los valores nuestros empiezan a cero. **Vuelve a guardarlos con SC30.**

## Verificación en emulación
`emu_sc30.py`: guardado de stock (por la llamada enganchada), carga de stock (`0x0802EEFE`), proyecto nuevo de stock y la cadena del servicio del DSP entera desde su cabeza, como en el aparato.
- **Guardado:** SC29 no copia nada tras un tick del servicio (el fallo); SC30 copia los huecos y la firma, y no copia nada si hay una carga pendiente.
- **Encendido:** huecos y drums se cargan del proyecto.
- **Cambio de sesión:**
  - huecos y parámetros se mantienen;
  - efectos y song pointer quedan apagados;
  - los drums son los del proyecto nuevo.
- **Proyecto sin firma:** huecos mantenidos, valores de drums a cero.
- **Proyecto nuevo:** huecos y parámetros mantenidos.
- **Guardar tras cambiar de sesión y volver a encender** con ese proyecto: vuelven los huecos.
- **SC29, como referencia:** al cambiar de sesión toma los huecos del proyecto.

Además, `verify_builds.py` (ALL IDENTICAL) y las pruebas de SC23.3–SC29 repetidas sobre SC30: todas pasan.

## Pruebas en el aparato
1. Envía SC30.
2. **Master FX:**
   - asigna efectos a la fila inferior y cambia parámetros de algún efecto;
   - **carga otra sesión:** deben seguir las asignaciones y los parámetros, con todo apagado;
   - **empieza un proyecto nuevo:** igual.
3. **Guardar:**
   - guarda un proyecto con huecos asignados y knobs de drums movidos;
   - **carga otra sesión y vuelve a él:** los drums deben volver;
   - **apaga y enciende** (arrancando con ese proyecto): deben volver los huecos y los drums.

## Volver atrás
Envía SC29.
