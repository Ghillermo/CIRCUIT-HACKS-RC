# SC51.7 = SC51.6 + FM de 8 operadores (igual que la Beta 5.20 salvo la marca)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc51.7/circuittracks-4486-SC51.7.syx` | `b29909bf72eb5dd9243b178507e0eaeaf5d30adc3a650206a4eb344946d8e36b` | `SC51.7` |

**Qué cambia** (el usuario, 2026-11-04 / 05): el FM del sinte propio de MIDI 1 / 2 pasa a **8 operadores** con envolventes como las del DX7 (4 rates, 4 niveles) y **48 algoritmos** (los 16 de antes + los 32 del DX7); el FM de 4 operadores desaparece y sus patches se cargan convertidos. Página FM = pad 7 (con la fila de motores cerrada): pads 9-16 = operador 1-8, pad 17 = envolvente de pitch; K1 ratio, K2 fino, K3 nivel, K4 velocity, K5-K8 R1-R4; Shift: K1 algoritmo (16 clics por paso), K2 feedback, K3 rate scaling, K4 level scaling, K5-K8 L1-L4. Guardado: el FM de cada patch propio en una ranura extra del mismo banco (después de sus 8 patches, el banco hasta 8 KB); el del proyecto en los bytes 8-39 de los ajustes de los patrones de Synth 1 / 2. **Components:** el aparato devuelve los patches propios y el FM a cada banco después de «Send patches» / «Send pack».

**Usar con una copia de la tarjeta.** Escribe en los bancos de patches (ranuras extra) y en las sesiones.

## Qué probar
1. MIDI 1, vista Preset, pad 27, **pad 24** (violeta): FM encendido; pad 27 cierra la fila; **pad 7** = página FM. Los pads 9-16 encendidos según el algoritmo (verde = portador, azul claro = modulador), pad 17 ámbar. Toca: suena.
2. **Shift + K1** = algoritmo: cada 16 clics uno; los pads enseñan los algoritmos 1,5 s. Prueba uno del DX7 (6 operadores: pads 9-14 encendidos) y uno antiguo.
3. Elige un operador (pad 9-16) y mueve K1-K8 y Shift + K3-K8: ratio, fino, nivel, velocity, rates, rate / level scaling, niveles. Pad 17: transposición (K1), ruido (K3, K4), envolvente de pitch.
4. **Pad 7 mantenido** = los 16 algoritmos antiguos; **pad 8 mantenido** = los sonidos de partida.
5. **Un patch de la Beta 5.19** (FM de 4 operadores) cargado aquí: el mismo sonido.
6. **Guardar un patch propio** (Clear + pad dos veces): apagar, encender, cargarlo: vuelve el FM entero. Con la tarjeta en el PC: el banco de ese patch crece hasta la ranura de su FM (`NN_PATCHBANK.cpb`, hasta 8 KB).
7. **Proyecto:** guarda un proyecto con el FM, cambia el FM, carga el proyecto: vuelve.
8. **Components** (en un pack de prueba con patches propios): «Send patches»; después cargar los patches propios: siguen con su FM. Mandar un patch suelto: nada se pierde.
9. Poly FM, unísono, glide como en la 5.19; muchas voces de 8 operadores: el límite apaga voces sin traqueteo.

## Verificación en emulación
- `emu_fm8_core1.py` (el núcleo 1, N = 4 bit a bit con SC51.4), `emu_fm8_core0.py`, `emu_fm8arm.py` (el motor ARM contra el modelo de `fm8.py`, la conversión de los patches antiguos en 93 juegos), `emu_fm8.py` (el firmware entero: panel, pads, knobs), `emu_fm8poly.py` (6 voces, escrituras al DSP por tick), `emu_fm8store.py` (patches en el banco, proyecto, intercambio / copia, el protocolo de ficheros de stock con Components: 19 comprobaciones): ALL PASS.
