# SC56.3 = SC56.2 + el mapa del algoritmo del FM de 8 operadores

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc56.3/circuittracks-4486-SC56.3.syx` | `77180213ee4bc79fccfaef2bbe27ac3174fcf90d304253d93d33f04f0bbd98d1` | `SC56.3` |

**Lo nuevo** (el usuario, 2026-11-11: «cómo podemos mostrar de forma más clara qué hace un algoritmo FM? … algo con pads y colores que el usuario
pueda mover»), `tools/fmmap.py`, en la página FM de MIDI 1 / 2 (FM de 8 operadores encendido, la fila de motores cerrada):
- **Pad 7:** un toque fija el mapa (otro toque lo quita; pad 7 brillante mientras se ve); mantenido ½ s = el mapa solo mientras lo mantienes;
  desde otra página un toque abre la página FM. **Shift + pad 7 mantenido** = la lista de los 56 algoritmos (antes, el pad 7 mantenido).
- **El mapa (pads 9-32):** cada fila se lee de izquierda (moduladora) a derecha (portadora); un pad oscuro entre dos = no interactúan; un operador
  que modula a varios sale en cada cadena.
- **Color:** verde = ratio entero, verde azulado = x,5, naranja = otro (inarmónico), rojo = fijo, violeta = el operador del feedback; brillante =
  nivel de la mitad o más, tenue = menos; **el elegido late en todas sus copias**.
- **Un toque** = elegir el operador (los knobs lo editan). **Shift + operador** = callado mientras se ve el mapa (apagado). **Mantener uno y tocar
  otro** = el primero modula al segundo o deja de hacerlo (algoritmo propio; el mapa se redibuja al soltar); mientras se mantiene, sus destinos en
  blanco.

## Qué probar
1. FM encendido, página FM (pad 7), un toque al pad 7: el mapa. Probar varios algoritmos (Shift + K1 o Shift + pad 7): las cadenas tienen sentido.
2. Cambiar el ratio de un operador (K1 / K2): cambia de color (verde / verde azulado / naranja / rojo); K3 (nivel) por debajo de 50 lo atenúa.
3. **¿El elegido late en los cinco colores?** Sobre todo el rojo (código `0x5A`, sin confirmar): si parpadea o no late, decirlo.
4. Shift + un operador: se calla y se apaga; quitar el mapa (pad 7) o ir a otra vista: vuelve a sonar.
5. Mantener un operador y tocar otro: suena distinto, al soltar el mapa cambia; repetir el gesto lo deshace. Un enlace que haría un bucle no pasa.
6. Guardar el patch (Clear + pad en la vista Preset), cargar otro y volver: el algoritmo propio sigue. Guardar el proyecto, apagar, cargar: igual.
7. Mantener el pad 7 ½ s: el mapa mientras se mantiene; al soltar, los operadores de siempre en los pads 9-16.

## Verificación en emulación
- `emu_fmmap.py`: los 56 algoritmos frente al modelo (`fmmap.layout`, colores), elegir, callar (`c_mmol` = nivel 0, solo con el mapa reciente),
  enlace / bucle / desenlace (`c_fmalg` = `fmmap.custom_entry`), pad 7 toque / mantenido / Shift: todo bien.
- `emu_fm8arm`, `emu_fm8poly`, `emu_fm8store`: bien. `emu_fm8`, `emu_p4ovl`, `emu_morph`: los mismos fallos que en SC56.2. `emu_fm8v2`: además
  «pad 7 mantenido = la lista» (ahora Shift + pad 7, por diseño).
