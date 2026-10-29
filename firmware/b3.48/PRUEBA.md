# SC49.5 / Beta 3.48 = SC49.4 + el carril extra de los drums, fase 2 (bloqueos de estado, rampas, la vista de automatización)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc49.5/circuittracks-4486-SC49.5.syx` | `0872a20c22f9882f76e98f7b9363d6c5e00dfb07741783a2aa4fbe749763b018` | `SC49.5` |
| `firmware/b3.48/circuittracks-4486-B3.48.syx` (**Beta 3.48**) | `2f01bbe2f29228251f92f56c296c141ed2bffb3133b9d59a65d0f77565548974` | `B3.48` |

El usuario (2026-10-29): «What if we made a mode that trades resolution on all knobs … but saved all of them?», «Can we interpolate sweeps
instead of saving every instance?» → «Both, per drum», «4-bit», «Ramps + draw by hand»; la vista de automatización: «shift held inside
velocity or velocity pressed twice», mantener el paso de inicio y tocar el final; «Record held + 1-16/17-32» para cambiar de modo. La Beta 3.48
incluye las 3.44-3.47 (no se publicaron) y SC49.3 / SC49.4 (sin código muerto, sin el Vinyl del DSP ni el comb de los drums).

## Qué cambia (`tools/slock.py`: sus primeras funciones en la zona libre, el resto al final de la imagen)
- **Record mantenido + 1-16/17-32** en cualquier vista de un drum: su carril extra pasa de **carril** (fase 1) a **bloqueos de estado** y al
  revés. Al cambiar, el carril se borra en los 8 patrones del drum; al volver lleva el pitch cromático. Record queda como estaba.
- **Bloqueos de estado:** en los mismos 7 bits de cada paso, 0 = nada, 1-80 = un **estado**, 127 = un paso **dentro de una rampa**.
  - Un estado = los **14 valores** de los knobs nuevos del drum: los 8 que puede llevar el carril (K2, K4, K6, K7, Shift + K1, K2, K4, K7),
    el modo de filtro (Shift + K5), el bitcrush (K8), el tipo de distorsión (Shift + K8) y el ataque / inicio / corte de K3; 4 bits cada uno
    (16 niveles: 0, 64 y 127 exactos).
  - **Hasta 80 estados por proyecto**, en bytes que no usa nada más: la cola del registro + 376 (20) y + 680 (28) y los bytes 2-3 de las 8
    entradas de pista de las 16 escenas (2 por escena: guardar, cargar, Duplicate y Clear de escena no los tocan). Los que ya no usa ningún
    paso se reutilizan; uno igual a otro en uso, se comparte.
  - **Al sonar** el paso (micropaso 0): un estado pone los 14 valores; un paso de rampa busca los estados de antes y de después en el patrón y
    pone los valores intermedios, otra vez en los micropasos 1-5 (el modo de filtro y el tipo de distorsión, los del primero hasta llegar).
  - **Grabando** (Record + Play), girar uno de esos knobs guarda un estado en el paso que suena; si los tres últimos de la pasada quedan en
    línea recta (cada valor a un nivel o menos de la recta, los de tipo iguales), el del medio y los pasos entre ellos se vuelven rampa.
  - **Record mantenido + un paso** (vista Note) = un estado con los valores de ahora. **Clear + un knob del carril a la izquierda** = el carril
    del patrón que suena borrado. **Record mantenido** = los 8 knobs en blanco.
- **Vista de automatización:** la vista Velocity de un drum con **Shift**, o fijada con **Velocity otra vez** (otra vez = fuera; salir de la
  vista también). Pasos con algo en el carril extra **amarillos** (`0x2D`); en bloqueos de estado, los de rampa **amarillo tenue** (`0x2E`) y
  **mantener un paso y tocar otro** = rampa entre los dos (el extremo sin estado toma uno con los valores de ahora). En los drums la velocity
  fija queda en Shift + Velocity; en las demás pistas, Velocity dos veces sigue siendo la velocity fija (`dblpress`).
- Para el sitio: `recinst.use_fold()` (los dos bucles de 8 carriles de la foto de MIDI 1 / 2, desenrollados por el builder: ≈ 450 B en la zona
  libre). Imagen `0x6FFBC` (**68 B libres**), zona libre 46 B.

## Qué probar
1. Un drum con algo grabado en su carril: Record mantenido + 1-16/17-32 → los 8 knobs blancos mientras mantienes Record; el carril, vacío.
2. Play + Record: girar K6 de arriba abajo poco a poco a lo largo de un compás; parar: al sonar, el barrido se repite (suave dentro de cada paso).
3. La vista Velocity del drum con Shift: pasos con estado amarillos, de rampa amarillo tenue. Soltar Shift: la vista normal.
4. Velocity otra vez en esa vista: se queda la vista de automatización; mantener un paso y tocar otro: rampa entre los dos (amarillo tenue en
   medio). Velocity otra vez: fuera.
5. Record mantenido + un paso en la vista Note: ese paso guarda los valores de ahora (amarillo en la vista de automatización).
6. Guardar el proyecto, apagar, cargar: los estados y las rampas suenan igual. Duplicar el patrón: la copia suena igual.
7. Record mantenido + 1-16/17-32 otra vez: el carril vuelve al pitch cromático (vacío).
8. La foto de MIDI 1 / 2 (Record mantenido + paso con el sinte propio) sigue igual.
9. Master FX: Digitise con K4 a la derecha empieza entero y se va limpiando (arreglo de SC49.4); Shift + K5 de un drum, sin comb.

## Verificación en emulación
`emu_slock.py`: el reparto de los 80 estados, la escala de 4 bits, el cambio de modo (carril borrado en los patrones 0 / 5), un estado que
vuelve al sonar, una rampa (micropaso 0 del paso del medio = mitad, micropaso 3 por la ranura 2 de los reproductores = 15 / 24), la grabación
(16 / 32 / 48 = rampa, 16 después = giro), K6 grabando, Clear + K6, la vista de automatización (fijar, LEDs, dibujar una rampa, quitar, salir,
Shift + Velocity del original), los knobs blancos, la foto en la vista Note, la vuelta al carril y la vista en un drum con carril (sus pasos
amarillos, Velocity dos veces fija la vista y no la velocity fija, sin rampas). `emu_lanex.py`, `emu_snapall.py`: igual que
SC49.4. `emu_p4dest.py`: la foto de MIDI 1 / 2 igual que SC49.4 (con `use_fold`).
