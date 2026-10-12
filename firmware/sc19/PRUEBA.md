# SC19 — los ajustes se guardan en el proyecto + arreglos del botón 1-16/17-32, la vista cromática y los modos del sinte

`circuittracks-4486-SC19.syx` — SHA-256 `424cc79344e331075ffb9818f380e7b8e271518e8d83fdb25361e68f8aff6205`
Imagen de 0x5b4cc bytes, CRC 0xa8e698a2, marca `SC19`.

Es **SC18.3** más tres cosas. La reserva de RAM no crece (220 B, margen de unos 20 B).

## 1. Qué se guarda **en el proyecto**
Se guarda con el proyecto (Save), sigue a «guardar como copia», vuelve al cargarlo y cada proyecto tiene lo suyo:
- **Drums, los 4:** K1 envolvente, Shift + K1 cantidad al tono, K3 frecuencia del ring mod, Shift + K3 cantidad, K5 LFO, Shift + K5 velocidad,
  K7 env → corte, Shift + K7 modo de filtro, Shift + K8 resonancia, y los valores «extendidos» de K4 (start point) y K6 (bitcrush).
- **Asignaciones de Master FX a la fila inferior** (qué efecto, con su modo y su copia de parámetros, hay en cada hueco).
- **Asignación noise / entrada de línea de cada sinte.**

**No se guarda** (y se apaga al cargar un proyecto, al crear uno nuevo y al encender): el estado encendido de los Master FX (los retenidos con Shift y los
mantenidos) y el song pointer (inicio, final, salto). Los efectos originales de la fila inferior también se apagan.

- **Proyecto nuevo:** empieza limpio (todo por defecto). En stock, un proyecto nuevo **no** borra los bytes reservados; SC19 los limpia a propósito.
- **Proyectos antiguos** (guardados por stock o por una versión anterior): sin datos nuestros = valores por defecto.
- **Proyectos con las marcas de la sonda** (SC182D / SC183D): llevan números en esos bytes. SC19 los reconoce porque no llevan su firma y los trata como vacíos
  (y los limpia al cargarlos). Después de guardarlos con SC19 quedan limpios.

## 2. Arreglos
- **Botón 1-16 / 17-32** (entre Octave ▲ y Tempo/Swing): ahora **él** sube la resonancia del filtro master de 32 en 32 (127 → 0) en la vista FX y **él** se enciende
  de verde. Antes lo había puesto, por error mío, en **Record** (id 16, LED 48). Ahora Record y Play (ids 16 y 17) son los de stock.
  Los ids que he confirmado en emulación: 16 = Record (LED 48), 17 = Play (LED 49), 21 = 1-16/17-32 (LED 53).
- **Vista cromática de drums:** vuelven a verse **las cuatro filas** en una sola página (SC18.1 apagaba las filas 1-2; se quita).
- **Modos de la fuente del sinte:** solo **0-4** (noise, entrada 1, entrada 2, y las dos invertidas). Los modos de retorno de delay / reverb **se han descartado**: los
  pads 30 y 31 de Shift + Preset vuelven a ser de stock. **El conmutador sigue de momento en Shift + pads 25-29 de la vista Preset del sinte** (provisional hasta que elijas el
  nuevo gancho).

## Pruebas en el aparato
1. Envía SC19. Comprueba que todo lo de SC18.3 sigue (Master FX, FX, song pointer, drums).
2. **Drums:** elige un drum y mueve K1, K3, K5, K7, Shift + K1/K3/K5/K7/K8 y K4 / K6 hacia la izquierda pasando de 0. **Guarda**, apaga del todo (10 s), enciende y carga: debe sonar igual.
3. **Asignaciones:** en Master FX, mantén un FX de arriba y pulsa un pad de la fila inferior. **Guarda**, apaga, carga: el hueco sigue asignado y suena igual.
4. **Modos del sinte:** pon el Synth 1 en una entrada (Shift + pad 26 en su vista Preset), guarda, apaga, carga.
5. **Por proyecto:** haz algo distinto en dos proyectos A y B, guarda ambos, cárgalos alternando (sin apagar): cada uno conserva lo suyo, y lo no guardado se descarta como en stock.
6. **Copia:** «guardar como copia» en un slot nuevo y cárgalo.
7. **Proyecto nuevo:** debe empezar con los drums neutros, los huecos vacíos y los sintes en noise.
8. **Estado encendido:** retén un Master FX con Shift y pon un song pointer; cambia de proyecto y comprueba que quedan apagados. Igual al encender.
9. **Botón 1-16/17-32 (vista FX):** sube la resonancia de 32 en 32 y su LED es verde. **Record** y **Play** funcionan como siempre.
10. **Vista cromática de drums:** las cuatro filas encendidas.

## Cómo está hecho
- **Zona de datos (XMEM):** 65 bytes de los bloques de sesión que ningún descriptor de parámetros cubre. Se vio con las sondas que viajan con el proyecto (SC182D / SC183D).
  Reparto: huecos de Master FX 28 B, drums 4 × 9 B, modos 1 B. El byte 43 de los drums no se usa. Firma de 5 bits en el byte 8 del drum 0: sin ella, la zona se lee como vacía y se limpia.
- **Drums:** el ARM guarda los valores en esos bytes (valor en 7 bits, complemento a dos en los bipolares; los 8 bits «extendidos» van en el bit 7 de los 8 bytes de valor) y manda al
  DSP el valor **absoluto**. El DSP cambia de «sumar un incremento» a «guardar el valor» (opción `drums2_dsp.ABS`; el resto del DSP es el de SC18.3, mismo coste).
- **Ganchos:** final de la «aplicación» de la sesión de stock (`0x0802F5B8`: carga, proyecto nuevo y arranque), final de los valores por defecto del proyecto nuevo (`0x0802F5FA`) y la
  llamada al guardado de stock (`0x0802FE5E`): justo antes se copian a la zona las ranuras y los modos (la RAM sigue siendo su estado de trabajo).
- **Trabajo diferido:** lo hace el servicio del DSP, no el gancho: cuando existen los cuatro manejadores de drums se limpia la zona (proyecto nuevo o sin firma), se pasa de la zona a la RAM (ranuras y modos, con
  validación: efecto > 5 o modo > 4 = por defecto), se marcan todos los valores de los drums para reenviarlos (un mensaje por drum y por tick), y se apagan los Master FX y el song pointer.

## Verificación en emulación
`emu_sc19.py` (146 comprobaciones, con el objeto de sesión y el registro reales y las funciones de stock de guardado, carga y proyecto nuevo) y `emu_sc19_dsp.py` (mensajes absolutos, etapas bit a bit,
núcleo completo: 61695 instrucciones por bloque con 4 drums, igual que SC18.3 con los controles apagados).

## Volver atrás
Envía SC18.3 (o la anterior). Los bytes reservados que SC19 haya escrito en un proyecto no afectan a otros firmware (stock los ignora).
