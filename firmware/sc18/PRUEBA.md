# SC18 — controles nuevos de los drums y grabación cromática paso a paso

`circuittracks-4486-SC18.syx` — SHA-256 `e6b3d3dc5defbfe97425be4d860bd4f552abed76257dfd19f0d7fea8043b4186`
Imagen de 0x5a4b8 bytes, CRC 0xa7f356f9, marca `SC18`.

Es **SC17.8** con dos cambios:
1. el modo cromático de los drums ya no pisa los tonos al grabar;
2. controles nuevos en los knobs de los drums.

La reserva de RAM del ARM no crece (el estado nuevo vive en el DSP y en 3 bytes libres de cada drum).

## 1. Modo cromático: cada golpe guarda su tono en su paso
Antes, al grabar en modo cromático (Shift + Preset en un drum), el último tono tocado acababa en todo el compás:
- el grabador de automatización deja el parámetro Pitch «armado»;
- en cada paso siguiente escribía «sin automatización»;
- así borraba los tonos anteriores en la vuelta siguiente.

Ahora, en un drum en modo cromático, el tono de cada golpe se graba **solo en el paso del golpe**.
- Los knobs (incluido el de Pitch) siguen grabando como en stock.
- Fuera del modo cromático, todo es como en stock.
- En modo cromático, girar el knob de Pitch mientras se graba solo escribe en los pasos donde lo giras (no borra los siguientes).

## 2. Knobs de los drums
Con un **drum seleccionado**, los 8 knobs:

| Knob | Sin Shift | Con Shift |
|---|---|---|
| **K1** | **Pitch envelope**: derecha = el golpe empieza más agudo y baja; izquierda = empieza más grave y sube (hasta ±24 semitonos) | — |
| K2 | Pitch (stock, SC09–SC12) | como antes |
| **K3** | **Hold / Gate**: 0 = apagado; cuanto más a la derecha, más corto se corta el sonido (de ~2 s a casi nada) | — |
| K4 | Decay (stock). **Más allá de 0 hacia la izquierda: start point** (el sample empieza 1/16 … 15/16 más adelante) | — |
| **K5** | **LFO**: derecha = trémolo (volumen), izquierda = vibrato (±2 semitonos) | **velocidad del LFO** (0,1–20 Hz) |
| K6 | Distortion (stock). **Más allá de 0 hacia la izquierda: bitcrush** (15 niveles) | — |
| **K7** | **Envolvente → corte del filtro** (±): el golpe abre o cierra el filtro DJ y vuelve en ~100 ms | — |
| **K8** | **Filtro DJ** en lugar del EQ: centro = sin filtro; izquierda = paso bajo; derecha = paso alto | **resonancia** del filtro |

- **K1, K3, K5, K7, Shift + K5 y Shift + K8** empiezan en «apagado» al encender (pitch envelope 0, hold 0, LFO 0, envolvente → corte 0, velocidad media ~1,4 Hz, resonancia mínima).
  - No se guardan con el proyecto. Al girarlos, se suman al valor que tienen (no tienen posición fija).
- **K4 / K6:** cuando el valor de stock llega a 0, seguir girando a la izquierda cuenta el start point / bitcrush (de 1 a 15 clics). Girando a la derecha, primero vuelve a 0 y después sigue el valor de stock.
- **K8:** usa el mismo valor que el EQ de stock, así que **sí se guarda**. Un proyecto con el EQ movido sonará ahora con el filtro.
- **K7** solo actúa si el filtro está activo (K8 fuera del centro). Con K8 en el centro y K7 negativo, el golpe cierra un paso bajo.
- **Límite:** el pitch envelope hacia arriba se recorta si el drum ya va muy agudo (el incremento del sample tiene tope).
- Los LEDs de K1/K3/K5/K7 no muestran estos valores.

## Cómo está hecho (resumen; detalle en `docs/NOTAS.md`)
- **ARM:**
  - el slot 4 del manejador de macros de cada drum va a `c_dk18`;
  - el estado está en 3 bytes libres del objeto, que un gancho del constructor pone a 0;
  - el servicio del DSP envía un mensaje por drum (buzón con etiqueta) a X:$3A80 + 32·d;
  - la grabación cromática se arregla con el gancho `c_rstep` en 0x0803FF02.
- **DSP (núcleo 0):**
  - control por bloque en P:$20A4 (buzón, envolvente, LFO, tono, filtro);
  - disparo en P:$20E0 (incremento base, reinicio, hold, start point);
  - por muestra sobre X:$2C02 en P:$218E: gate → bitcrush → filtro SVF → trémolo, y luego el sidechain de SC16;
  - el EQ de stock queda plano (P:$2129).
  - El programa llega a P:$305E; antes el límite que nos habíamos puesto era $3000, pero el núcleo tiene al menos 16K palabras.

## Verificación en emulación
- `emu_sc18.py` (ARM):
  - grabación cromática por la ruta real (pad → grabador → oyente de pasos): cada golpe en su paso, sin borrar los siguientes; SC17.8 sí los borraba;
  - knobs de los 4 drums por el controlador real;
  - rangos extendidos de K4/K6;
  - los demás knobs, igual que SC17.8;
  - envío al DSP desde el servicio;
  - gancho del constructor.
- `emu_sc18_dsp.py` (DSP):
  - cada etapa (gate, bitcrush, filtro LP/HP, trémolo y la cadena entera) exacta al bit frente a un modelo;
  - buzón (etiqueta, límites, códigos);
  - envolvente, LFO, índices y resonancia del filtro;
  - pitch envelope y vibrato (relación de tono con error < 0,3 %);
  - disparo: hold, start point y −24 semitonos.
- Núcleo completo con golpes reales desde el ARM:
  - el incremento sube bloque a bloque y el gate cierra la voz;
  - coste: +500 instrucciones por bloque con todo apagado, +3800 con todo encendido en los 4 drums (~4,5 %);
  - pila igual que SC17.8 (6);
  - tabla de voces intacta;
  - solo escribe memoria nueva en X:$3A80–$3AFF.
- **Batería completa** (`bash tools/run_tests.sh full`): **todo OK**:
  - las pruebas de SC17, SC17.5–SC17.8 sobre la imagen de SC18;
  - las de Master FX DSP, núcleo completo y captura de delay/reverb (las que comparan memoria y coste ahora cuentan con los bloques X:$3A80–$3AFF de SC18);
  - SC18 ARM y DSP.
  - Todos los builds anteriores se siguen generando idénticos.

## Pruebas en el aparato
1. Envía SC18. Comprueba que todo lo de SC17.8 sigue igual (Master FX, song pointer, modos del sinte).
2. **Grabación cromática:** en un drum, Shift + Preset (modo cromático). Graba 3–4 golpes con tonos distintos y deja grabando un par de compases. Los tonos deben mantenerse.
3. **K8:** gira a la izquierda (paso bajo) y a la derecha (paso alto). Con **Shift + K8**, sube la resonancia.
4. **K1:** a la derecha, el golpe "cae" de tono (bombo/tom electrónico). A la izquierda, sube.
5. **K3:** a la derecha, el sonido se corta antes.
6. **K5:** a la derecha, trémolo; a la izquierda, vibrato. **Shift + K5** cambia la velocidad.
7. **K7** con K8 en paso bajo: el golpe abre el filtro.
8. **K4** todo a la izquierda y sigue girando: el sample empieza más tarde. **K6** igual: bitcrush.
9. Dime cualquier ruido, clic o cuelgue, y qué rangos (tiempos, profundidades) te gustaría cambiar.

## Volver atrás
Envía SC17.8.
