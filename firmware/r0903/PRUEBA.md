# RC0.9.3 (`R0903`) = RC0.9.2 + guardado de ajustes del mod diferido (stutter del delay)

`circuittracks-4486-R0903.syx` — SHA-256 `4e313be9edb4d2ff34baf44c158b07e8da4b6c98a2d0921d54d8a7b786d810a1`.

**Arreglo del stutter del delay** (el usuario, 2026-10-15: «sigue habiendo stutter audibles (de ritmo) sobre el delay al cambiar entre modos de sinte o mover sus perillas»; con S419D2 el stutter venía con Duplicate **azul** = un acceso a la tarjeta del firmware original durante un retraso del bucle principal).
- **Causa:** el motor propio de MIDI 1 / 2 guarda su estado en el registro de ajustes del aparato, y el mod lo guardaba con el guardado de ajustes de stock (`0x0802D2AC`), que escribe el fichero de ajustes en la tarjeta y espera: cada ~0,7 s mientras se giraba un knob del motor, y al momento en cada toggle (pad 27 y los demás) o al cargar / guardar un patch del sinte propio. Durante la escritura el bucle principal no atiende al DSP ni a la interfaz y el delay, sincronizado al tempo, tropieza.
- **Arreglo (`tools/lazysave.py`):** cuando el que pide guardar es el mod, el guardado queda **pendiente** y se escribe desde la tarea de LEDs **con el transporte parado y 2 s después del último cambio**. El guardado del propio firmware (ajustes del Setup) sigue igual.
- Límite: si se apaga el aparato mientras suena, sin haber parado, se pierden los últimos cambios del motor (vuelven los de antes).

## Qué probar
1. Proyecto con delay audible, Play. En MIDI 1 / 2 con el motor propio: girar sus knobs y cambiar de modo (pad 27 y los demás toggles), cargar un patch del sinte propio: **sin stutter en el delay**.
2. Parar, esperar 3 s, apagar y encender: el motor vuelve con los últimos cambios.
3. Cambiar algo del motor mientras suena y apagar sin parar: vuelven los valores anteriores (esperado).

## Verificación en emulación
- `emu_lazysave.py`: pad 27 de MIDI 1 por el controlador sonando = nada escrito y el guardado pendiente; 5 s después, sonando, nada; parado, nada a 1 s, una escritura a 2,1 s, nada después; el guardado llamado desde el código original se escribe al momento; la build anterior escribía al momento con el toggle.
