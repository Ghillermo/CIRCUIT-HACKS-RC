# Lista de comprobación en el aparato (2026-10-06)

Reúne lo que el `README.md` / `CLAUDE.md` marcan como **pendiente de probar** (⏳), agrupado por función y no por build. Marca cada casilla con lo que ya has comprobado: `[x]` bien, `[!]` falla (anota qué ves), `[ ]` sin probar. La columna «prueba» es la acción mínima; el detalle está en el `PRUEBA.md` de la build.

Confirmado ya (no hace falta repetir): SC02–SC16 (incluido el sidechain), SC17.3, SC17.6 / SC17.7 (song pointer), SC20D.1 (los modos 5 y 6 funcionan), SC21D (la RAM del programa del DSP llega a `P:$3FFF`).

## 0. Arranque y base
- [x] Una build reciente (la última que flashees) **arranca con normalidad** y no se cuelga al encender (el arreglo es `FIX_LOCK`, SC19.3 en adelante).
- [x] Tras apagar y encender, **los ajustes guardados vuelven** (SC19.4: copia del registro de sesión al cargar un proyecto; cambio de parche).

## 1. Drums
| Estado | Función (build) | Prueba |
|---|---|---|
| [x] | Grabación cromática por paso: cada tono solo en su paso (SC18) | grabar un compás en cromático y dejarlo grabando |
| [x] | Knobs de drums según el panel: K1 pitch … K8 FX (SC19.8) y su **brillo por valor** (SC19.6) | girar cada knob, con y sin Shift |
| [x] | Tipo de distorsión por drum (Shift + FX) (SC19.9) | cambiar de tipo y guardar / cargar el proyecto |
| [x] | Escala en tres filas; K1 = sesgo del tono; **Clear** en los knobs nuevos (SC20.1) | vista de escala; Clear + knob (rojo / azul) |
| [x] | Cuadros de los drums duplicados en la vista Note (SC21.3) | pads 25-28 = drums 1-4 |
| [x] | Ajustes de drums, asignaciones de Master FX y modos del sinte **por PACK o session** (SC19) | guardar, apagar, cargar; copiar proyecto; proyecto nuevo limpio |

## 2. Master FX y vista FX
| Estado | Función (build) | Prueba |
|---|---|---|
| [x] | LEDs de los knobs correctos en Master FX (SC17.4) y brillo por valor (SC19.9) | abrir Master FX |
| [x] | Pad 8: apaga los efectos retenidos y el song pointer (SC17.8, SC18.1) | retener un efecto y pulsar |
| [x] | Pad 7: salto instantáneo que repite el paso mientras se pulsa (SC19.7 / SC19.9) | pulsar y mantener; Shift + pad 7 fija |
| [x] | Estado encendido y song pointer a 0 al cargar / arrancar (SC19) | cargar un proyecto con Master FX activo desactiva master fx|
| [x] | Vista FX: Octave ▲ / ▼ = envíos de delay / reverb, **LEDs de Octave, Duplicate y 1-16/17-32 encendidos** (SC18.2 / SC18.3) | botón FX |
| [x] | Vista FX: Duplicate = reset de envíos; 1-16/17-32 = resonancia del filtro master (SC17.5 / SC19) | pulsarlos |
| [x] | **Shift + knob en la vista FX = parámetros de reverb y delay** (SC21.2) | páginas reverb y delay, LEDs por brillo con Shift |
| [x] | Retornos de FX del Setup (pad 22 / 23) llegan a la fuente del sinte (SC19.5) | Setup, retorno a tira 3 / 4, fuente del sinte 1-4 |
| [x] | Feedback de los retornos (SC21.1) | retorno en la tira 3 / 4 y subir su envío |

## 3. Fuente del sinte y entrada de línea
| Estado | Función (build) | Prueba |
|---|---|---|
| [x] | Entrada de línea ×2 y modos en fase invertida (SC16.1) | pads 26-29: confirmar cuál es la señal invertida |
| [x] | Vista de la fuente del sinte: pulsar Synth 1 / 2 dos veces abre los pads 25-29; cualquier botón la cierra; Shift + pads de stock (SC19.1) | ídem |
| [x] | Modos 5 / 6 (retorno de delay / reverb) en el build normal | decidir si se devuelven (ahora solo en el diagnóstico SC20D.1) |

## 4. Modo VCA / VCF / FX de MIDI 1 / 2 (SC20 → SC23.2)
| Estado | Función (build) | Prueba |
|---|---|---|
| [x] | La entrada de línea de MIDI 1 / 2 pasa por VCF / VCA; el estado **se guarda con la firma** (SC20 / SC20.1) | activar, apagar y encender |
| [x] | **SC20.2** (sin el modo): sirve para saber si el fallo de las entradas externas es del VCF | solo si SC20 falló |
| [x] | Knobs reordenados según el panel; tipos de filtro; FX suave / dura / plegado / wavefold (SC21) | recorrer los 16 valores |
 [x] | Filtros LP / HP de 12 y 24 dB (SC21.4) | Shift + K5 |
#=====| [x] | FX ring mod / comb / chorus; K3 y Shift + K3 bipolares (SC22) | Shift + K8; K3 a ambos lados |
#=====| [x] | Oscilador: página B, pitch, forma, morph, sends de env / LFO (SC22.1 → SC22.3)
#=====| [x] | Pads de la fila de abajo: 25 CC, 26 patch flip, 27 fuente, 28 vista OSC, 29 vista VCA-VCF; colores distintos (SC22.4 / SC23.2) | el modo se activa al tocar 28 o 29 y se apaga al pulsar el encendido |
#=====| [x] | Gate: las notas de los pads y del secuenciador abren / cierran el VCA aunque la vista no esté en pantalla | tocar con otra vista en pantalla |

## 5. Editor de CC (SC23 / SC23.1)
| Estado | Función | Prueba |
|---|---|---|
| [x] | Tocar un knob muestra su CC con los 32 pads; girar lo cambia en vivo | pad 25 |
| [x ] | **Octave ▼ / ▲ ciclan los campos** (CC → inicio → fin, con vuelta), sin guardar | |

| [x] | **Cualquier botón de vista, pad 25 o pad de plantilla descarta** | cambiar y salir con Mixer |
| [] | NRPN / RPN de 7 y 14 bits: cuatro / seis campos | plantilla creada en Components |
| [x] | Con el editor apagado, Octave y el botón de la pista son de stock | |
#=====| [x] | Dibujo: los dígitos (centenas en dos columnas) se leen bien; **quedan LEDs sucios al salir** (informado, pendiente de arreglo en SC23.3) | |

## 6. Abierto (informado por ti, aún sin resolver o sin publicar)
#=====- [x] **Oscilador erráticamente ruidoso**: en emulación el seno de SC22.3 llevaba ~4 % de armónicos (parábola sin refinar); SC23.3 lo baja a ~1 % y fija el estado neutro (gate básico, seno sin modulación). Por confirmar en el aparato cuando salga SC23.3.
#=====- [x] **Estado neutro por defecto + Clear + knob en rojo** (SC23.3, en desarrollo).
#=====- [x] **LEDs de Octave del editor** (▼ al empezar, ambos en medio, ▲ al final) (SC23.3, en desarrollo).
#=====- [xE] **Tope de los envíos a la mitad con «Efectos a line in»** (SC23.3, en desarrollo; el cambio está implementado y se está probando en emulación).
#=====- [x] **LEDs sucios al salir del editor de CC** (SC23.3, en desarrollo).
#=====- [x] **El secuenciador automatiza los parámetros de OSC / VCA-VCF en lugar de mandar CC** (pedido; **no implementado**: requiere enganchar el emisor de CC de los macros y la grabación de automatización; estudio pendiente).
#=====- [ ] Toggle de las pistas MIDI para reverb / delay + NRPN propios (pedido antiguo, sin empezar).
- [x] VCA con saturación + VCF bipolar para la entrada externa: **hecho** en SC20+; falta confirmarlo (sección 4).

## 7. Cosas que no son del aparato
#=====- [x] `git push` de las ramas locales (necesita tu aprobación en la ventana de credenciales).

## Correcciones pedidas para la próxima build (anotadas 2026-10-07; la del pad 27 está hecha en SC25, pendiente de probar)
| Build | Fallo | Causa probable / arreglo previsto |
|---|---|---|
| SC24 | Al desactivar el modo VCA-VCF por completo con el pad 27 (oscilador → apagado), la fila superior (pads 1-8) **no vuelve a mostrar los presets CC** (las plantillas MIDI). | La vista Preset de stock solo dibuja su fila de plantillas al construirse y al cambiar de plantilla (`T_DRAW = 0x0804D5CA`). Con el modo encendido `c_vleds` escribe en los pads 1-8 la fila de páginas (y 0 en los pads 4-8); al apagar no se repinta lo de stock. Arreglo: cuando el modo está apagado y el editor de CC inactivo, `c_vleds` llama a `T_DRAW(vista)` justo después de `c_tleds` (como ya hace `c_edclean`), o al menos en `tr_off` de `vp_tri`; así vale también si el modo se apaga por otra vía (p. ej. al encender el patch flip). Prueba en emulación: leer el búfer de LEDs tras el ciclo del pad 27 y comprobar que los pads 1-8 son los de la plantilla elegida. |
| SC26 | Al salir del modo step-drummer no se borran las filas de LEDs (pasos 9-16 y destinos). | **Hecho en SC27** (pendiente de probar): con la vista cerrada `c_sdleds` escribe 0 en los pads 9-24 (el búfer de la vista es el de stock y nadie lo repintaba). Prueba: `emu_sc27.py`. |

## Pedidos para la próxima build (anotados 2026-10-08) — **hechos en SC33** (pendiente de probar; el botón de grabar quedó: mantener / pulsación corta / Shift = un compás)
| Dónde | Pedido | Notas |
|---|---|---|
| Step-drummer (MIDI 1 / 2, Synth 1 / 2) | **Grabación en tiempo real:** con la grabación activa y el transporte en marcha, tocar un pad de las filas 1-2 (los pasos, que suenan al tocarlos) **graba una nota en el paso que está sonando, con su micropaso** (el momento exacto dentro del paso, como la grabación en vivo de stock). | La nota es la que suena al tocar ese pad (la de su paso, `c_sdnnote`). Falta decidir: ¿sustituye la nota del paso o se añade como otra unidad (hoy el step-drummer deja una nota por paso)?; ¿velocity = la del pad o la del par? Paso actual = parámetro 1 del almacén de la pista; micropaso a partir del tick (parámetro 2). |
| Master FX, sample capturado | **El pad 6 sigue siendo Vinyl** (cambia el rediseño: ya no se sustituye). **Pad 7 = disparo** del sample. **Pad 32 = grabar** (rojo, mientras se mantiene graba la salida máster). | El pad 32 deja de ser un hueco asignable de la fila inferior. El sample necesita su propio conjunto de 4 parámetros (pitch, modo, start, end): hoy hay 5 conjuntos × 4 knobs y Vinyl conserva el suyo → 4 B más de RAM (el bloque de Master FX tiene 4 B de margen desde SC24). Antes: la zona del búfer, según SC32D.1. |

## Pendiente de probar en el aparato: SC27, SC28, SC29 (2026-10-07)
Por orden; cada `PRUEBA.md` tiene la lista numerada.
- **SC27** (`firmware/sc27/PRUEBA.md`): filas apagadas al cerrar el step-drummer; Octave ▲ / ▼ y 1-16 / 17-32 iluminados; knob del par que suena en blanco; páginas 4 / 5 de knobs; step-drummer en Synth 1 / 2 (botón del sinte dos veces → pad 30).
- **SC28** (`firmware/sc28/PRUEBA.md`): NRPN de drums (canal 10, MSB 5-8) y de Master FX (canal 16, MSB 9) con un monitor MIDI; entrada desde un DAW; filtros CC Tx / Rx de Setup.
- **SC29** (`firmware/sc29/PRUEBA.md`): cuarto estado del pad 27 (VA-drum); golpe de un disparo; DEC / SUS / REL = decays de VCA / pitch / filtro, independientes; LRATE = ruido; pad 31; el estado se conserva al apagar; el oscilador normal suena como antes.

## Pedidos para SC35 (anotados 2026-10-09) — guardar el sample en la SD del pack
- **Guardar la captura en la SD** sobre un sample del pack (carpeta `PCM/`, vale para todas las sesiones del pack), con confirmación. Vía: la API de contenido de la tarea de almacenamiento (op 7 = escribir); SC35D4 / SC35D5 comprueban la lectura.
- **Intercambiar la posición de dos samples** del pack (p. ej. el 3 y el 10): leer los dos ficheros y escribirlos cruzados por la misma API, o renombrarlos si el stock tiene una operación para eso. Hace falta un búfer en la RAM del ARM o pasar por la memoria externa del DSP.
- **Borrar un pack por completo.** Es destructivo y no se puede deshacer, así que llevará una confirmación clara en el aparato (doble pulsación o mantener) y nunca se aplicará al pack en uso sin aviso. Pista: la cadena `DeleteItem: %s` (`0x080267B8`) y las operaciones de la API que aún no conocemos (2, 3, 5, 8). Primero un diagnóstico que lo pruebe sobre un pack duplicado de prueba.
- **Importar un sample o un patch de otro pack** (anotado 2026-10-09). La API de contenido lleva el número de pack en cada elemento (`0xFF` = el actual), así que se puede leer el elemento de otro pack (PCM = tipo 4, Patches = tipo 3) y escribirlo en el pack actual. Un sample es un fichero entero (`NN_*.wav`). Un patch vive dentro de un `NN_PATCHBANK.cpb` (16 por pack): habrá que averiguar su formato para copiar un solo patch y no el banco entero. Falta elegir la interfaz: pack de origen, elemento y destino.
- **Nombre de los samples generados en el aparato: `CAP` + un identificador** (anotado 2026-10-09), es decir `PCM/NN_CAP<ID>.wav`, con `NN` = la posición. Por resolver:
  - el identificador: **número correlativo de 2 cifras** (`NN_CAP01.wav`, `NN_CAP02.wav`…; decisión del usuario, 2026-10-09). Por decidir de dónde sale: el siguiente libre mirando los `CAP` del pack o un contador guardado;
  - cómo poner el nombre: la API de contenido construye la ruta con `%s/%02d%s` y el sufijo fijo `_PCM.wav`, así que crearía `NN_PCM.wav`. Para escribir `NN_CAP<ID>.wav` hay que ver si el stock busca los ficheros por el prefijo `NN_` (lo dirá SC35D5) y cómo los renombra o crea Components (la ruta de SysEx lleva el nombre del sample).
  - Al sustituir un sample hay que quitar el `NN_*.wav` anterior para que no queden dos ficheros con la misma posición.
