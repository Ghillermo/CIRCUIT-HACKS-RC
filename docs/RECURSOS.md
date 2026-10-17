# Recursos del Circuit Tracks: límites, lo descubierto y lo usado

*English version below: [Resources](#resources).*

Cifras de **RC0** (= SC36.2) sobre el firmware oficial 1.2.1 (build 4486). Salen de los manifiestos de los builds, de las pruebas en emulación y de los builds de diagnóstico probados en el aparato (SC17D, SC21D, SC32D, SC35D-SC35DB); el detalle de cada medida está en [`NOTAS.md`](NOTAS.md). Las cifras marcadas «≈» son estimaciones. **RC0.1** (= SC37.4) cambia poco: imagen 0x65A3C B (+4 596 B), núcleo 0 con 20 palabras libres, el núcleo 1 igual; RC0.1S (0x6417C B) = RC0S + 176 B. **RC0.2** (= SC37.5, 0x65B48 B) añade la sobrecarga del Glitch en el núcleo 1, que queda en **2047 de 2048 palabras de programa** (1 libre), y el LED de Clear en el ARM. **RC0.3** (= SC38, 0x65E8C B, +836 B) y **RC0.3S** (0x64398 B = RC0.2S + 380 B) solo cambian el ARM: el DSP es el de RC0.2. **SC38.1** (stretch del granular) añade 340 B de ARM; sin RAM ni DSP. SC38.2 (captura armada desde Play) +80 B; **SC38.3** (MIDI Thru Merge / Filter) +296 B y usa los bits 30 / 31 del parámetro 2 de los ajustes (máscara de guardado `0xFF07FFFF`). **RC0.4** (0x66010 B = RC0.3 + 388 B), **RC0.4S** (0x64478 B = RC0.3S + 224 B) y **BETA0** (= SC38.7, 0x663D0 B: quedan 39 984 B de flash) solo cambian el ARM; sin RAM nueva. **SC38.8** (0x665E8 B, +536 B): los modos de voz de la página en el búfer de LEDs ocioso de Master FX (sin RAM nueva); lee la SD (4 bancos) al cambiar de pack / página / patch y cada 4 s con la vista Preset del sinte en pantalla. **SC38.9** (0x66820 B, +568 B): el teclado partido usa tres bits libres del byte de estado de SC14; sin RAM nueva.

## Resumen

| Recurso | Límite | Libre en el firmware original | Usado por el mod (RC0) | Queda |
|---|---|---|---|---|
| Flash de la aplicación (ARM) | 0x70000 B = 448 KB (lo que acepta el bootloader) | 143 908 B (140,5 KB) tras la imagen de 0x4CDDC B | 96 876 B | **47 032 B (45,9 KB)** |
| RAM del ARM (heap) | límite del heap `0x20044E58` | 240 B (el stock nunca más reserva tras arrancar) | 236 B | **4 B** |
| Guardado por proyecto | 65 B reservados en los bloques de la sesión | 65 B | 65 B | ≈ 7 bits |
| Guardado global (ajustes) | 75 B finales del registro de ajustes | 75 B | 75 B | 0 |
| Programa del DSP, núcleo 0 | `P:$0000–$3FFF` = 16 384 palabras | 5 538 palabras (`$2A5E–$3FFF`) + `P:$80–$FF` | 5 515 + 125 palabras | **23 palabras** (SC37: 19; SC37.1: 17; RC0.1: 20) |
| Datos internos del DSP, núcleo 0 | X / Y 16 K palabras cada uno | X / Y:`$3339–$3BFF` (2 247 cada uno) + X:`$3D00–$3FFF` (768) | X ≈ 2 100; Y ≈ 300 | X ≈ 900, Y ≈ 1 900 palabras |
| CPU del DSP, núcleo 0 | ≈ 166 000 instrucciones por bloque de 32 muestras (0,67 ms) | ≈ 118 000 (≈ 70 %) | ≈ 20 000 con todo encendido | ≈ 55–60 % |
| Pila del DSP | 15 niveles | 9 (el stock usa 6) | 0 niveles nuevos | 9 |
| Programa del DSP, núcleo 1 | `P:$0000–$07FF` = 2 048 palabras | 1 684 (el stock usa 364) | 1 630 | **54 palabras** (RC0.2: 1) |
| CPU del DSP, núcleo 1 | (servidor de lecturas del núcleo 0) | ≥ 976 vueltas libres por bloque (≈ 25 000 instrucciones) | tareas de ≤ 1 173 instrucciones, una por vuelta | la mayor parte |
| Ancho de banda de la memoria externa | lecturas del núcleo 1 por bloque | limpio hasta 3 584, chasquidos desde ≈ 4 000, ralentiza desde ≈ 5 800 | ≤ 2 048 (granular) | ≈ 1 500 |
| Memoria externa del DSP (16 bits por palabra) | 16 M palabras (`$000000–$FFFFFF`) | `$337000–$57EFFF` + `$E80000–$FFEFFF` ≈ 4 M palabras (≈ 82 s mono a 48 kHz) | ≈ 1,75 M | **≈ 2,2 M palabras (≈ 45 s)** |
| Tarjeta SD | la de la tarjeta | — | ficheros `PCM/NN_PCM.wav` del pack al guardar (solo RC0; RC0S nada) | — |

## ARM (STM32F745, Cortex-M7)

### Flash
- SC44 / Beta 1.30 (0x6FB90 B): **1136 B de flash libres** (1 828 B para el modo muestra: el ARM del motor y el selector). **DSP núcleo 0: termina en `P:$3F29`, 215 palabras libres** (157 para el modo muestra). RAM: la cola `+ 953` / `+ 997` (el flip pendiente de MIDI 1 / 2): **la cola del proyecto ya no tiene bytes libres**; el estado del selector en los bytes 14 / 15 del bloque de SC16. Guardado: los flips en el carril de nivel de la pista MIDI (`0x80 | s`).
- SC43.9 / Beta 1.29 (0x6F46C B): **2 964 B de flash libres** (la compactación del DSP ahorra 1 323 B de la imagen; las formas del LFO, el ARM y el patch, el resto). **DSP núcleo 0: termina en `P:$3E8C`, 372 palabras libres** (441 recuperadas con la forma de una palabra de `x:(rn+d)`, 76 para las formas del LFO). RAM: la cola `+ 561..563` (la forma del LFO por pista y el acumulador del knob); libres `+ 953`, `+ 997`.
- SC43.8 / Beta 1.28 (0x6F768 B): **2 200 B de flash libres** (636 B menos que SC43.7: el sidechain de drums con Synth / MIDI 152 B, el guardado del motor propio el resto). RAM: la de SC43.7. Guardado: los códigos 27..34 y los bits de los pads 28 / 29 en los bytes de estado en marcha de la copia del registro de ajustes que se escribe (`O_RT`, `O_SAVED`, `O_ED` / `+ 1`).
- SC43.7 / Beta 1.27 (0x6F4EC B): **2 836 B de flash libres** (1 232 B menos que SC43.6: el pitch de drums nuevo ocupa menos; gate retrigger 248 B, step-drummer 300 B, rollers en pistas silenciadas 228 B, cuantizar 616 B, arpegiador en MIDI 1 / 2 y resolución ~56 B). RAM: la de SC43.6 (`+ 54..58` de la cola) y `+ 159` (gate retrigger), `+ 177` (el step-drummer de sinte que vuelve), `+ 939` (Shift + Play). Guardado: los pasos cromáticos en el carril de pitch de cada drum (ya no en el de panorama).
- SC43.6 / Beta 1.26 (0x6F01C B): **4 068 B de flash libres** (SC43.5: 0x6EB24 B; +1 272 B: el carril cromático de drums ≈ 420 B, el modo cue ≈ 1 220 B, los arreglos del sinte propio 52 B). RAM: la cola del proyecto `+ 54..58` (pasos cromáticos), `+ 59..63` / `+ 155..158` (envíos de cue y mutes principales); libres en la cola: `+ 159`, `+ 177`, `+ 561..563`, `+ 939`, `+ 953`, `+ 997`. Ajustes: byte 3 del parámetro 3 (el modo cue). DSP: ninguna palabra nueva (el modo cue cambia los valores de nivel / panorama / envíos que leen 32 llamadas de los grupos, con la ley de panorama del stock). CPU: una lectura del carril 7 por drum y paso.
- La imagen oficial ocupa `0x08010000–0x0805CDDB` (0x4CDDC B). El bootloader acepta imágenes de hasta 0x70000 B y ninguna carga de literal del stock apunta más allá del final: **143 908 B libres** que el original no usa.
- SC39.9 (0x68888 B): 30584 B de flash libres (328 B más que SC39.8); sin RAM; la envolvente de Digitise usa la palabra `X:VN_ST` del DSP (del Vinyl) y una lectura + dos escrituras del DSP por tick mientras Digitise está activo con K4 fuera del centro.
- SC39.8 (0x68740 B): 30912 B de flash libres; el envío al delay ocupa 696 B de ARM, sin RAM (cuatro palabras X del DSP que eran del Vinyl: `VN_CR`, `VN_HISS`, `VN_LPK`, `VN_HPK`).
- SC39.7 (0x68488 B): 31608 B de flash libres; el gesto mecánico ocupa 408 B de ARM, sin RAM (un bit del byte K4 del Glitch) y sin código DSP: usa el motor del Glitch (núcleo 1) y la palabra `X:VN_T` del Vinyl, que deja de usarse. Una lectura del DSP por tick solo mientras hay un gesto.
- SC40.9 / Beta 1.0 (0x6a244 B): 23996 B de flash libres; añade 1 004 B. RAM: 1 B más de la zona de trabajo de la cola (`+ 104`), 2 B del relleno de la vista Setup (`+ 0x26`); guardado: 27 B de la cola del proyecto (`+ 128`). RC0.7 0x66060 B, RC0.7S 0x644c8 B.
- SC40.8 (0x69e58 B): 25000 B de flash libres; añade 1 008 B (Nudge y órdenes de reproducción). RAM: 8 B de la zona de trabajo de la cola del proyecto (`+ 96..103`); guardado: byte 7 de los ajustes de cada patrón.
- SC40.7 (0x69a68 B): 26008 B de flash libres; SC40.6 añade 364 B (interfaz de las cadenas) y SC40.7 452 B (copia de patches propios entre packs); sin RAM nueva (el clip va en `X:PCLIPW` del DSP). **Escribe en la SD** (64 B por patch copiado).
- SC40.5 (0x69738 B): 26824 B de flash libres; las cadenas de patrones ocupan 1 952 B de código, **el último byte libre del búfer de LEDs ocioso** (`c_gst() + 143`) y, en el proyecto, 3 B de los ajustes de cada patrón (bytes 4-6) + 48 B guardados y 64 B de estado en la cola del registro (`0x27024`; **la cola en RAM es la nueva fuente de RAM: quedan ≈ 870 B**). CPU: al final de cada patrón, dos lecturas de regla por pista.
- SC40.4 (0x68f98 B): 28776 B de flash libres; los contadores de vueltas ocupan 200 B de código y **40 B del búfer de LEDs ocioso de Master FX** (`c_gst() + 148..184` y `+ 140..142`: **ese búfer queda lleno**, `+ 143` y `+ 185` aparte). CPU: una lectura de almacén y una división por unidad y micropaso con frecuencia puesta.
- SC40.3 (0x68ed0 B): 28976 B de flash libres; la frecuencia por paso y las dinámicas ocupan ≈ 1,1 KB y 2 B del búfer de LEDs ocioso de Master FX (`c_gst() + 146`; libres ahí: + 148…+ 184); usan el byte [3] de cada paso de las pistas de notas (el [2] es del random-mutate); sin RAM nueva, sin DSP, sin SD. CPU: por unidad y micropaso con frecuencia puesta, tres lecturas de almacén y dos divisiones.
- SC39.6 (0x682f0 B): 32016 B de flash libres; la copia de proyectos ocupa 744 B y 8 B del búfer de LEDs ocioso de Master FX (`c_gst() + 132`). **Escribe en la SD** (el fichero entero del proyecto, 160 780 B, en 40 trozos de 4 KB).
- SC39.5 (0x68008 B): 32760 B de flash libres; los LEDs de tipo ocupan 224 B, sin RAM.
- SC39.4 (0x67f28 B): 32984 B de flash libres; el guardado de patches ocupa 1456 B y 8 B del búfer de LEDs ocioso de Master FX (`c_gst() + 124`); sin RAM nueva, sin DSP. **Escribe en la SD** (340 B del patch de sinte en su hueco del banco; 64 B por patch en los intercambios del sinte propio).
- SC39.3 (0x67978 B): 34440 B de flash libres; el editor de destinos de macro ocupa 1328 B (280 de tablas) y 4 B del búfer de LEDs ocioso de Master FX (`c_gst() + 120`); sin RAM nueva, sin DSP, sin SD.
- RC0.5 / SC39.2: el núcleo 0 del DSP termina en `P:$3FED` (**19 palabras libres**; `$3FE7` en RC0.5S): el sample delante de los efectos costó una palabra.
- SC39.1 / BETA2 (0x67444 B): 35772 B de flash libres; los patches del sinte propio no usan RAM nueva (18 B del búfer de LEDs ocioso de Master FX) y viven en el relleno de los patches de sinte del pack (42 de 172 B por registro).
- SC39.9 (0x68888 B): 30584 B of flash free (328 B more than SC39.8); no RAM; Digitise's envelope uses the DSP word `X:VN_ST` (Vinyl's) and one DSP read + two writes per tick while Digitise is on with K4 off the middle.
- SC39.8 (0x68740 B): 30912 B of flash free; the delay throw takes 696 B of ARM, no RAM (four X words of the DSP that were Vinyl's: `VN_CR`, `VN_HISS`, `VN_LPK`, `VN_HPK`).
- SC39.7 (0x68488 B): 31608 B of flash free; the mechanical gesture takes 408 B of ARM, no RAM (one bit of the Glitch's K4 byte) and no DSP code: it uses the Glitch engine (core 1) and the Vinyl word `X:VN_T`, no longer used. One DSP read per tick only while a gesture runs.
- SC39.6 (0x682f0 B): 32016 B of flash free; the project copy takes 744 B and 8 B of the Master FX block's idle LED buffer (`c_gst() + 132`). **It writes to the SD** (the whole project file, 160 780 B, in 40 pieces of 4 KB).
- SC39.5 (0x68008 B): 32760 B of flash free; the type LEDs take 224 B, no RAM.
- SC39.4 (0x67f28 B): 32984 B of flash free; the patch save takes 1456 B and 8 B of the Master FX block's idle LED buffer (`c_gst() + 124`); no new RAM, no DSP. **It writes to the SD** (the 340 B of the synth patch into its slot of the bank; 64 B per patch in the own-synth exchanges).
- SC39.3 (0x67978 B): 34440 B of flash free; the macro destination editor takes 1328 B (280 of tables) and 4 B of the Master FX block's idle LED buffer (`c_gst() + 120`); no new RAM, no DSP, no SD.
- RC0.5 / SC39.2: DSP core 0 ends at `P:$3FED` (**19 words free**; `$3FE7` in RC0.5S): the sample in front of the effects cost one word.
- SC39.1 / BETA2 (0x67444 B): 35772 B of flash free; the own-synth patches use no new RAM (18 B of the Master FX block's idle LED buffer) and live in the padding of the pack's synth patches (42 of 172 B per record).
- SC39 / BETA1 (0x66a4c B) añade 105 584 B (38 324 B libres); el random-mutate son 556 B de código ARM  sin RAM nueva (1 byte libre del paso).
- RC0 (0x64848 B) añade 96 876 B:

  | Bloque | Bytes |
  |---|---|
  | Código ARM de las primeras versiones (cueva desde `0x0805CDE0`) | 4 608 |
  | Programa del núcleo 0 del DSP **reubicado** (stock + nuestro, 16 360 palabras × 3 B) | 49 088 |
  | Código ARM nuevo + tablas de Master FX (8 704 B) | 37 188 |
  | Programa del núcleo 1 del DSP (1 994 palabras × 3 B) | 5 988 |

- La copia original del programa del núcleo 0 (32 544 B en `0x080101F0–0x0801810F`) sigue en la imagen pero ya no se carga: es espacio que se podría recuperar (sin comprobar).

### RAM
- El asignador de bloques (`0x0801D7D8`) nunca libera; el stock reserva al arrancar y deja **240 B** entre el heap y su límite. `0x20044E58–0x2004FE00` **no** es libre (pila de arranque: SC13 se colgaba).
- El mod baja el límite del heap y usa 236 B: estado de SC14 / SC16 (40 B), bloque de Master FX (196 B, con los valores volátiles del motor de las pistas MIDI). **Margen: 4 B.**
- Además reutiliza bytes que el stock no usa: el final del registro de ajustes (75 B, guardado), los bytes reservados del proyecto (65 B, guardados), el búfer de LEDs ocioso de Master FX (84 B, copia de seguridad del editor de CC), bytes de relleno de objetos de vista (Preset de drums `+0x51..+0x53`, vista de packs) y bits de bytes de stock (`T0` de Vinyl, `S_JF`, el hueco 7).
- Sin comprobar: la ITCM de 16 KB (`0x00000000`) y la SRAM de respaldo de 4 KB (`0x40024000`) podrían estar libres.

### CPU
- No se ha medido el tiempo del ARM; no se han observado retrasos. Reglas para no cargarlo: trabajo acotado en el tick del servicio del DSP (y nunca tomar su semáforo), como mucho **un mensaje por voz cada 2 ms** al DSP (más un latido cada ~8 ms / ~1 s para que un mensaje perdido no deje una voz muda) y el envío MIDI desde la tarea de la interfaz se corta a 64 mensajes por pulsación.

## DSP (DSP56724: dos núcleos DSP56300 con memoria externa compartida)

### Núcleo 0 (el del audio de stock)
- **Programa:** el stock carga 0x2A5E = 10 846 palabras desde `P:0` (con `P:$80–$FF` libre en la tabla de vectores). Se creyó que el límite era `$3800`; el diagnóstico SC21D comprobó que la RAM llega a `P:$3FFF` (**+2 048 palabras**). El mod usa `$2A5E–$3FE8` (5 515 palabras) y `$80–$FC` (125). **Quedan 23 palabras**: es el recurso más escaso.
- **Datos internos:** libres y verificados X / Y:`$3339–$3BFF` y X:`$3D00–$3FFF`. Usados: X:`$3400–$37FF` (comb de los drums), `$38C0–$39FF` (registros guardados, bloques de los osciladores), `$3A00–$3BFF` (Master FX, drums, voces de las pistas MIDI), `$3D00–$3D24` (sampler, Glitch); Y:`$3A00–$3AFF` (entradas de línea, capturas de los retornos). La tabla de voces `X:$EB–$15A` es del stock y no se toca.
- **CPU:** ≈ 166 000 instrucciones por bloque; SC19.9 (stock + Master FX + los drums nuevos) medía ≈ 54 200, así que el stock solo ronda las 48 000. Lo añadido después cuesta poco: dos voces de las pistas MIDI ≈ 2 700, VA-drum +626, lado del núcleo 0 del granular / Glitch 929, drums con todo encendido ≈ +10 000, cadena de Master FX 5 957; con todo apagado los ganchos cuestan unas decenas de instrucciones.
- **Pila:** 15 niveles; el stock usa 6 y el mod no anida `jsr` / `do` nuevos encima (las pruebas comparan `SPMAX`).

### Núcleo 1 (sin usar por el original, salvo un servicio de lecturas)
- **Programa:** 2 048 palabras (SC35D.1). El stock carga 364: un bucle que sirve la lista de lecturas de la memoria externa que pide el núcleo 0. **Libres: 1 684.** El mod (granular + Glitch) llega a `$7C9`: **quedan 54**.
- **Datos internos:** X 12 K, Y entre 8 K y 10 K (SC35D.1); el estado del mod va en la memoria compartida (`X:$37000…`).
- **CPU:** el bucle de stock da **≥ 976 vueltas libres por bloque**. Pero el núcleo 0 espera a que ese bucle le sirva sus lecturas: si el núcleo 1 tarda, se frena todo el audio. Por eso el trabajo va en **tareas cortas, una por vuelta** (la más larga, 1 173 instrucciones).
- **Ancho de banda (SC35DB):** limpio hasta 3 584 lecturas externas por bloque, chasquidos desde ≈ 4 000, el audio entero se ralentiza desde ≈ 5 800. Presupuesto del granular: **≤ 2 048** (16 granos por pista × 2 pistas con interpolación).

### Memoria externa (SDRAM compartida, 16 bits útiles por palabra de 24)
- El stock carga los samples del pack seguidos desde `Y:$580000` hasta como mucho `$E7FFFF` (≈ 9,4 M palabras, ≈ 196 s mono; más allá: «Sample Memory Exceeded») y usa zonas bajas (la lista de lecturas del núcleo 1 llega a `X:$30882`).
- **Descubierto libre** (SC35D2 / SC35D3: memoria real, sin espejo, nadie la escribe): `$337000–$57EFFF` (≈ 2,4 M palabras) y `$E80000–$FFEFFF` (≈ 1,6 M).
- **Usado:** búfer circular estéreo del master para el Glitch en `$340000` / `$360000` (2 × 128 K palabras, 2,7 s), captura del sample en `$E80000` (3,46 s) y 8 ranuras de sustitución de drums en `$EA8800–$FEC7FF` (≈ 1,33 M). SC37 carga ahí, uno detrás de otro, los samples que llegan de otro pack al intercambiarlos (`X:$3D26` = la siguiente dirección). **Libre:** sobre todo `$380000–$57EFFF` (≈ 2,1 M palabras), más restos en `$337000–$33FFFF` y `$FEC800–$FFEFFF` (≈ 2,2 M en total).
- El ARM solo llega a ella con direcciones de 16 bits por el puerto de host: las copias van por órdenes al DSP (ventana `Y:$3B40`).

## Almacenamiento
- **Proyecto (fichero de sesión en la SD):** los 65 B reservados de los bloques de la sesión guardan drums, huecos de Master FX, fuente de los sintes y reverb / delay; quedan ≈ 7 bits.
- **Ajustes del aparato:** los 75 B finales del registro guardan el motor de las pistas MIDI y el step-drummer; llenos.
- **Pack en la SD:** RC0 escribe al guardar `PCM/NN_PCM.wav` (capturas usadas como drums), intercambia samples y borra packs; RC0.1 además copia samples y patches entre packs (`PCM/NN_*.wav`, `Patches/NN_PATCHBANK.cpb`); **RC0S / RC0.1S no escriben nada en la SD**. Los patrones del step-drummer y del secuenciador de efectos usan los carriles del patrón de stock (sin espacio nuevo).
- La flash NOR de 32 MB (samples, sesiones, actualizaciones) no se toca.

## Cómo se ha optimizado para que quepa más
1. **Buscar sitio antes de recortar:** diagnósticos en el aparato encontraron +2 048 palabras de programa en el núcleo 0, el núcleo 1 entero, ≈ 4 M palabras de memoria externa y los bytes reservados del proyecto y de los ajustes.
2. **Reubicar el programa del núcleo 0** al final de la imagen (SC16), con sitio para crecer hasta `$3FFF`.
3. **Llevar lo pesado al núcleo 1:** el sinte granular y el Glitch viven allí (≈ 1 600 palabras y casi toda su CPU, que el núcleo 0 no tenía); al núcleo 0 solo le cuesta recoger el audio (929 instrucciones por bloque) y la tabla de samples se le copia por cuartos.
4. **Tareas cortas en el núcleo 1** para no frenar al núcleo 0, y un presupuesto de lecturas externas medido en el aparato.
5. **Tablas compactas o calculadas:** `drums2_dsp.COMPACT` libera 123 palabras con el mismo sonido (bit a bit); la ventana del granular se calcula en lugar de tabularse para caber en 2 K; los decays reutilizan `TDEC` al cuadrado.
6. **Código parametrizado:** OSC 1 y OSC 2 comparten código (el bloque va en un registro), el orden de la cadena se elige con banderas sin duplicar código, los knobs de tipo calculan zona y posición en el buzón.
7. **Estado empaquetado y reutilizado:** bits del byte de firma (VA-drum, velocity), bits del byte 179, valores volátiles en el bloque de Master FX, bytes muertos de stock, el búfer de LEDs ocioso como copia de seguridad; el granular comparte los valores guardados con la página del oscilador; el secuenciador de efectos usa los carriles del step-drummer.
8. **Coste casi nulo apagado:** cada gancho mira una bandera y vuelve.
9. **Búferes grandes en la memoria externa**, no en la interna.
10. **Builds con opciones:** cada versión nueva deja idénticas las anteriores (`verify_builds.py`), así que una optimización nunca rompe una versión ya probada.

---

<a id="resources"></a>
# Circuit Tracks resources: limits, what was found and what is used

Figures of **RC0** (= SC36.2) on the official firmware 1.2.1 (build 4486). They come from the build manifests, the emulation tests and the diagnostic builds tested on the device (SC17D, SC21D, SC32D, SC35D-SC35DB); the detail of every measurement is in [`NOTAS.md`](NOTAS.md) (Spanish). Figures marked “≈” are estimates. **RC0.1** (= SC37.4) changes little: image 0x65A3C B (+4,596 B), core 0 with 20 free words, core 1 unchanged; RC0.1S (0x6417C B) = RC0S + 176 B. **RC0.2** (= SC37.5, 0x65B48 B) adds the Glitch overload on core 1, which is left at **2,047 of 2,048 program words** (1 free), and the Clear LED on the ARM. **RC0.3** (= SC38, 0x65E8C B, +836 B) and **RC0.3S** (0x64398 B = RC0.2S + 380 B) only change the ARM: the DSP is RC0.2's. **SC38.1** (granular stretch) adds 340 B of ARM code; no RAM, no DSP. SC38.2 (armed capture from Play) +80 B; **SC38.3** (MIDI Thru Merge / Filter) +296 B and uses bits 30 / 31 of settings parameter 2 (save mask `0xFF07FFFF`). **RC0.4** (0x66010 B = RC0.3 + 388 B), **RC0.4S** (0x64478 B = RC0.3S + 224 B) and **BETA0** (= SC38.7, 0x663D0 B: 39,984 B of flash left) only change the ARM; no new RAM. **SC38.8** (0x665E8 B, +536 B): the voice modes of the page in Master FX's idle LED buffer (no new RAM); it reads the SD card (4 banks) when the pack / page / patch changes and every 4 s while the synth Preset view is shown. **SC38.9** (0x66820 B, +568 B): the split keyboard uses three free bits of the SC14 state byte; no new RAM.

## Summary

| Resource | Limit | Free in the original firmware | Used by the mod (RC0) | Left |
|---|---|---|---|---|
| Application flash (ARM) | 0x70000 B = 448 KB (what the bootloader accepts) | 143,908 B (140.5 KB) after the 0x4CDDC B image | 96,876 B | **47,032 B (45.9 KB)** |
| ARM RAM (heap) | heap limit `0x20044E58` | 240 B (stock never allocates again after boot) | 236 B | **4 B** |
| Per-project storage | 65 B reserved in the session blocks | 65 B | 65 B | ≈ 7 bits |
| Global storage (settings) | last 75 B of the settings record | 75 B | 75 B | 0 |
| DSP program, core 0 | `P:$0000–$3FFF` = 16,384 words | 5,538 words (`$2A5E–$3FFF`) + `P:$80–$FF` | 5,515 + 125 words | **23 words** (SC37: 19; SC37.1: 17; RC0.1: 20) |
| DSP internal data, core 0 | X / Y 16 K words each | X / Y:`$3339–$3BFF` (2,247 each) + X:`$3D00–$3FFF` (768) | X ≈ 2,100; Y ≈ 300 | X ≈ 900, Y ≈ 1,900 words |
| DSP CPU, core 0 | ≈ 166,000 instructions per 32-sample block (0.67 ms) | ≈ 118,000 (≈ 70 %) | ≈ 20,000 with everything on | ≈ 55–60 % |
| DSP stack | 15 levels | 9 (stock uses 6) | no new levels | 9 |
| DSP program, core 1 | `P:$0000–$07FF` = 2,048 words | 1,684 (stock uses 364) | 1,630 | **54 words** (RC0.2: 1) |
| DSP CPU, core 1 | (read server for core 0) | ≥ 976 free loops per block (≈ 25,000 instructions) | tasks of ≤ 1,173 instructions, one per loop | most of it |
| External memory bandwidth | core-1 reads per block | clean up to 3,584, clicks from ≈ 4,000, slows down from ≈ 5,800 | ≤ 2,048 (granular) | ≈ 1,500 |
| DSP external memory (16 bits per word) | 16 M words (`$000000–$FFFFFF`) | `$337000–$57EFFF` + `$E80000–$FFEFFF` ≈ 4 M words (≈ 82 s mono at 48 kHz) | ≈ 1.75 M | **≈ 2.2 M words (≈ 45 s)** |
| SD card | the card’s | — | `PCM/NN_PCM.wav` pack files on save (RC0 only; RC0S nothing) | — |

## ARM (STM32F745, Cortex-M7)

### Flash
- The official image takes `0x08010000–0x0805CDDB` (0x4CDDC B). The bootloader accepts images up to 0x70000 B and no stock literal load points past the end: **143,908 free bytes** the original does not use.
- SC39 / BETA1 (0x66a4c B) adds 105,584 B (38,324 B free); random-mutate is 556 B of ARM code, no new RAM (1 free byte of the step).
- RC0 (0x64848 B) adds 96,876 B:

  | Block | Bytes |
  |---|---|
  | ARM code of the first versions (cave from `0x0805CDE0`) | 4,608 |
  | Core-0 DSP program, **relocated** (stock + ours, 16,360 words × 3 B) | 49,088 |
  | New ARM code + Master FX tables (8,704 B) | 37,188 |
  | Core-1 DSP program (1,994 words × 3 B) | 5,988 |

- The original copy of the core-0 program (32,544 B at `0x080101F0–0x0801810F`) is still in the image but no longer loaded: space that could be recovered (not checked).

### RAM
- The block allocator (`0x0801D7D8`) never frees; stock allocates at boot and leaves **240 B** between the heap and its limit. `0x20044E58–0x2004FE00` is **not** free (boot stack: SC13 hung).
- The mod lowers the heap limit and uses 236 B: SC14 / SC16 state (40 B), the Master FX block (196 B, with the volatile values of the MIDI track engine). **Margin: 4 B.**
- It also reuses bytes stock does not use: the end of the settings record (75 B, saved), the reserved bytes of the project (65 B, saved), the idle Master FX LED buffer (84 B, backup of the CC editor), padding bytes of view objects (Drum Preset `+0x51..+0x53`, packs view) and bits of stock bytes (Vinyl `T0`, `S_JF`, slot 7).
- Not checked: the 16 KB ITCM (`0x00000000`) and the 4 KB backup SRAM (`0x40024000`) may be free.

### CPU
- ARM time has not been measured; no delays have been seen. Rules to keep it light: bounded work in the DSP service tick (and never taking its semaphore), at most **one message per voice every 2 ms** to the DSP (plus a heartbeat every ~8 ms / ~1 s so a lost message cannot leave a voice silent), and MIDI sent from the UI task is capped at 64 messages per press.

## DSP (DSP56724: two DSP56300 cores with shared external memory)

### Core 0 (the stock audio core)
- **Program:** stock loads 0x2A5E = 10,846 words from `P:0` (with `P:$80–$FF` free in the vector table). The limit was believed to be `$3800`; the SC21D diagnostic proved the RAM goes up to `P:$3FFF` (**+2,048 words**). The mod uses `$2A5E–$3FE8` (5,515 words) and `$80–$FC` (125). **23 words left**: the scarcest resource.
- **Internal data:** verified free X / Y:`$3339–$3BFF` and X:`$3D00–$3FFF`. Used: X:`$3400–$37FF` (drum comb), `$38C0–$39FF` (saved registers, oscillator blocks), `$3A00–$3BFF` (Master FX, drums, MIDI track voices), `$3D00–$3D24` (sampler, Glitch); Y:`$3A00–$3AFF` (line inputs, return captures). The voice table `X:$EB–$15A` belongs to stock and is never touched.
- **CPU:** ≈ 166,000 instructions per block; SC19.9 (stock + Master FX + the new drums) measured ≈ 54,200, so stock alone is around 48,000. What came later is cheap: two MIDI track voices ≈ 2,700, VA-drum +626, core-0 side of the granular / Glitch 929, drums with everything on ≈ +10,000, Master FX chain 5,957; with everything off the hooks cost a few dozen instructions.
- **Stack:** 15 levels; stock uses 6 and the mod nests no new `jsr` / `do` on top (the tests compare `SPMAX`).

### Core 1 (unused by the original, except for a read service)
- **Program:** 2,048 words (SC35D.1). Stock loads 364: a loop serving the external-memory read list core 0 asks for. **Free: 1,684.** The mod (granular + Glitch) reaches `$7C9`: **54 left**.
- **Internal data:** X 12 K, Y between 8 K and 10 K (SC35D.1); the mod’s state lives in shared memory (`X:$37000…`).
- **CPU:** the stock loop gives **≥ 976 free loops per block**. But core 0 waits for that loop to serve its reads: if core 1 is late, all audio slows down. So the work goes in **short tasks, one per loop** (the longest, 1,173 instructions).
- **Bandwidth (SC35DB):** clean up to 3,584 external reads per block, clicks from ≈ 4,000, all audio slows down from ≈ 5,800. Granular budget: **≤ 2,048** (16 grains per track × 2 tracks with interpolation).

### External memory (shared SDRAM, 16 useful bits per 24-bit word)
- Stock loads the pack samples back to back from `Y:$580000` up to at most `$E7FFFF` (≈ 9.4 M words, ≈ 196 s mono; beyond: “Sample Memory Exceeded”) and uses low zones (the core-1 read list reaches `X:$30882`).
- **Found free** (SC35D2 / SC35D3: real memory, no mirror, nobody writes it): `$337000–$57EFFF` (≈ 2.4 M words) and `$E80000–$FFEFFF` (≈ 1.6 M).
- **Used:** stereo circular buffer of the master for the Glitch at `$340000` / `$360000` (2 × 128 K words, 2.7 s), the sample capture at `$E80000` (3.46 s) and 8 drum replacement slots at `$EA8800–$FEC7FF` (≈ 1.33 M). SC37 loads there, one after another, the samples that come from another pack in a swap (`X:$3D26` = the next address). **Free:** mainly `$380000–$57EFFF` (≈ 2.1 M words), plus leftovers at `$337000–$33FFFF` and `$FEC800–$FFEFFF` (≈ 2.2 M in all).
- The ARM only reaches it with 16-bit addresses through the host port: copies go through DSP commands (window `Y:$3B40`).

## Storage
- **Project (session file on the SD card):** the 65 reserved bytes of the session blocks keep drums, Master FX slots, synth source and reverb / delay; ≈ 7 bits left.
- **Device settings:** the last 75 B of the record keep the MIDI track engine and the step-drummer; full.
- **Pack on the SD card:** on save RC0 writes `PCM/NN_PCM.wav` (captures used as drums), swaps samples and deletes packs; RC0.1 also copies samples and patches between packs (`PCM/NN_*.wav`, `Patches/NN_PATCHBANK.cpb`); **RC0S / RC0.1S write nothing to the SD card**. The step-drummer and FX sequencer patterns use the lanes of the stock pattern (no new space).
- The 32 MB NOR flash (samples, sessions, updates) is never touched.

## How it was optimised to fit more
1. **Look for room before cutting:** diagnostics on the device found +2,048 program words on core 0, the whole of core 1, ≈ 4 M words of external memory and the reserved bytes of the project and the settings.
2. **Relocate the core-0 program** to the end of the image (SC16), with room to grow up to `$3FFF`.
3. **Move the heavy work to core 1:** the granular synth and the Glitch live there (≈ 1,600 words and nearly all its CPU, which core 0 did not have); core 0 only pays for collecting the audio (929 instructions per block) and the sample table is copied to it a quarter at a time.
4. **Short tasks on core 1** so core 0 is never stalled, and an external-read budget measured on the device.
5. **Compact or computed tables:** `drums2_dsp.COMPACT` frees 123 words with the same sound (bit for bit); the granular window is computed instead of tabulated to fit in 2 K; the decays reuse `TDEC` squared.
6. **Parametrised code:** OSC 1 and OSC 2 share code (the block is in a register), the chain order is chosen with flags without duplicating code, the type knobs compute zone and position in the mailbox.
7. **Packed and reused state:** bits of the signature byte (VA-drum, velocity), bits of byte 179, volatile values in the Master FX block, dead stock bytes, the idle LED buffer as a backup; the granular shares its saved values with the oscillator page; the FX sequencer uses the step-drummer lanes.
8. **Nearly zero cost when off:** every hook checks a flag and returns.
9. **Large buffers in external memory**, not in internal memory.
10. **Builds with options:** every new version leaves the older ones identical (`verify_builds.py`), so an optimisation never breaks a version already tested.
