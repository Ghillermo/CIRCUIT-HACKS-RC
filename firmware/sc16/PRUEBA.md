# SC16 — Sidechain en los drums (SC13 rehecho) — plan de prueba

`circuittracks-4486-SC16.syx` — SHA-256 `1c145040bba47475022421e842d37256dcef8f69a5e48ecd4b4157dad6ac3be5`
Imagen de 0x56314 bytes, CRC 0xC011E7BA, marca `SC16`.

Se basa en **SC15** (todo lo anterior, entrada de línea incluida). **Cambia cómo se carga el programa del DSP: la primera prueba, con el volumen bajo y teniendo a mano el modo bootloader.**

## Qué hace
Cada drum puede duckarse con otro drum, como hacen los sintes en stock. Por ejemplo, el hi-hat se aparta cuando suena el bombo.

**Vista Sidechain (Shift + FX).** Con ▼ ahora hay dos páginas más:

| Página | Fila 3 | Fila 4 |
|---|---|---|
| Sintes (stock) | Synth 1 | Synth 2 |
| MIDI (stock) | MIDI 1 | MIDI 2 |
| **Drums 1-2** | Drum 1 | Drum 2 |
| **Drums 3-4** | Drum 3 | Drum 4 |

En las páginas de drums:
- **Filas 3 y 4:** pad 1 = OFF (rojo); pads 2-8 = los mismos 7 presets que en stock. El pad del preset activo se ilumina brillante, en el color del drum.
- **Fila 1, pads 5-8:** eligen qué drum dispara el sidechain. Se aplica al drum de la última fila que tocaste; al llegar a la página, al primer drum de la página. El pad del drum disparador se ilumina en el color del drum afectado.
- Las filas 1 y 2 no tienen más funciones.
- ▲ / ▼ se iluminan cuando hay página en esa dirección.

**Atajo:** si entras con Shift + FX teniendo seleccionado un drum, se abre directamente su página.

**Funcionamiento:**
- El ducking afecta a todo el drum: el sonido seco y los envíos a reverb y delay.
- La envolvente es la de stock y empieza en el golpe del drum disparador, aunque el drum afectado esté en silencio en ese momento.
- Si silencias el drum disparador, no dispara, igual que en stock.
- **No se guarda:** al apagar, todo vuelve a OFF y el disparador vuelve a ser el drum 1. Cambiar de proyecto no lo reinicia.

## Qué ha cambiado respecto a SC13 (que entraba en bucle de reinicio)
- **Causa de SC13:** guardaba sus datos del DSP en X:$EB–$10F y la borraba al arrancar. Esa zona es la tabla de voces del DSP: la voz 0 saltaba a la dirección 0 y el DSP se reiniciaba.
- **SC16:**
  - Los datos de los drums van a **X:$3A10 + 9·k**, en la zona de memoria libre comprobada. El flag de SC10 sigue en X:$3A00 (SC14.2).
  - El código nuevo del DSP ya **no ocupa los vectores P:$54–$7F**. Va justo después del programa de stock (P:$2A5E–$2ACD). Para eso, el bloque de arranque del núcleo 0 se copia al final de la imagen con más palabras y se cambia el puntero de carga (0x08029700). El stub de arranque de stock activa el modo de conmutación de memoria, que da al menos 16K palabras de programa (el programa ocupa ahora $2ACE).
  - Del hook de fin de voz (P:$21AB, una sola palabra) se salta a un trampolín de 2 palabras en P:$FD.
  - El estado ARM ya **no está en 0x2004E000** (posible zona de pila de arranque). Va en una reserva real en lo alto del heap: la de SC14 se amplía 16 bytes (SC14 en 0x20044E28 y SC16 justo después). Si no hubiera sitio, el sidechain de drums queda desactivado y la vista funciona como stock.
  - Las subrutinas `getblk` y `advance` van ahora dentro de cada hook: 2 niveles menos de pila del DSP. El borrado del arranque usa un bucle `do` en lugar de `rep`.

## Verificación en emulación
- `emu_sc16_dsp.py` (27 pruebas, el conjunto de SC13 con las direcciones nuevas):
  - arranque: X:$3A00–$3A33 a 0 y las vecinas intactas;
  - con depth 0, señal y mezcla idénticas a stock;
  - con depth > 0, señal × envolvente del sidechain de stock **exacta** durante 12 bloques con 2 disparos, en los 4 drums;
  - salida de voz en silencio, drum silenciado y `func_00208a` completa.
- `emu_sc16.py` (40 pruebas ARM):
  - páginas, pads, LEDs, ▲▼ y entrada a la vista con un drum seleccionado;
  - manejador del grupo 5 (los 4×4 parámetros) y disparos;
  - con el heap sin sitio, todo como stock;
  - el límite del heap baja a 0x20044E28.
- `emu_sc16_core.py`, **DSP con el núcleo completo** (lo que no se probó en SC13): el programa reubicado arranca con el init real; tras el init y 60 bloques con el sidechain activo, la tabla de voces es idéntica a SC15.
  - SC16 solo toca de más X:$3A00–$3A33 y el scratch Y:$2028–$204C.
  - Coste: +57 instrucciones por bloque con todo apagado y +305 por cada drum atenuado (de ~53 800). Unos +0,4 % por drum.
  - Pila: máximo de 9 niveles en la ruta de drums, 11–13 con interrupciones anidadas (de 15). SC13 llegaba a 10.
- Regresiones: SC15 (con DSP completo), SC14.2, SC14 (ARM y DSP) y SC10 DSP pasan. Las antiguas dan el mismo resultado que SC14.2.

## Pruebas en el aparato (volumen bajo)
1. Envía SC16. **Lo primero, comprueba que arranca** y que suena como SC15: sintes, drums, FX, Master FX y entrada de línea.
2. Selecciona el Drum 2 (por ejemplo, un hi-hat) y pulsa Shift + FX: se abre la página Drums 1-2.
3. Fila 4, pad 8 (preset 7) → el Drum 2 se atenúa con el disparador (Drum 1 por defecto). Pon un patrón con bombo en el Drum 1 y hi-hat continuo en el Drum 2: el hi-hat debe "respirar" con el bombo.
4. Prueba los presets 1–7 y OFF (pad 1 de la fila).
5. Cambia el disparador (fila 1, pads 5–8) y comprueba que lo dispara el drum elegido.
6. ▼ / ▲ entre las 4 páginas. Las páginas de sintes y MIDI deben funcionar como siempre.
7. Si al arrancar entra en bucle de reinicio o el DSP queda mudo: **Scales + Preset + Note** y envía SC15. Dime en qué paso pasó.

## Volver atrás
Envía SC15 (o SC14.2) con el cargador.
