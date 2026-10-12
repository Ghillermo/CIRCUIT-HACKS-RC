# SC07 — SC06 + correcciones del patch flip — plan de prueba

`circuittracks-4486-SC07.syx` — SHA-256 `68f845d31baf2701ff2a091f00d7bf33ba390c67211ed46d3861dd5db11dd666`
Imagen de 0x4D14C bytes, CRC 0x09BB8B3D, marca `SC07`.

Incluye todo SC06 sin cambios de comportamiento, más dos correcciones.

## 1. El LED del pad 25 se ve nada más entrar en la vista Preset
- **Causa:** la vista Preset se dibuja una sola vez al arrancar y luego solo al cambiar de plantilla. En el arranque los ajustes globales aún no están disponibles, así que el pad 25 quedaba sin pintar hasta el primer cambio de plantilla.
- **Arreglo:** cada vez que el sistema lee los LEDs de esa vista, el pad 25 se actualiza con el estado real del toggle.

## 2. El toggle se guarda
- **Causa:** el firmware decide si guardar los ajustes globales comparando el parámetro de flags con la última copia guardada, pero **solo mira los bits 0–18**. Los bits 24–27 (Ch16 y patch flip) se ignoraban, así que cambiar solo esos nunca provocaba un guardado.
- **Arreglo:** la comparación mira también los bits 24–27. El resto queda igual que en stock (los bits 19–23 siguen ignorados).
- **Efecto extra:** el toggle Ch16 del pad 16 en Setup también se guarda de forma fiable, aunque sea lo único que hayas cambiado.
- El guardado lo hace el propio firmware, en el mismo momento en que guarda los ajustes de stock, normalmente al cambiar de vista. No hay escrituras nuevas en flash: solo cambia la decisión de cuándo guardar.

## Verificación en emulación (volcado en marcha)
- **LED:** con el pad 25 borrado del búfer, la lectura de LEDs de la vista lo pinta: encendido con patch flip activo y tenue con él inactivo, en MIDI 1 y MIDI 2. Devuelve el mismo búfer y el resto de pads no cambia. En SC06 se quedaba sin pintar.
- **Detector de cambios:**

  | Cambio en los flags | SC06 | SC07 |
  |---|---|---|
  | Note Tx, bit 11 | guarda | guarda |
  | Patch flip MIDI 1 / MIDI 2, Ch16 | no guarda | **guarda** |
  | Bit 20, bit 28 | no guarda | no guarda |
  | Ningún cambio | no guarda | no guarda |

- **De punta a punta:** copia sincronizada → pulsar el pad 25 en MIDI 2 → comprobación de guardado. SC07 guarda, y la copia incluye el bit 27; SC06 no guarda.
- Todas las pruebas de SC06 y las regresiones de SC05 y SC04 pasan sobre SC07.
- El cargador web reconoce el SHA y la transferencia simulada es idéntica al archivo.

## Pruebas en el aparato
1. Envía SC07 con `tools/ct_uploader.html`.
2. Ve directamente a MIDI 1 → Preset sin tocar nada: el pad 25 debe verse **tenue desde el primer momento**.
3. Actívalo y cambia de vista: vuelve a Note View y entra de nuevo en Preset. Debe seguir encendido.
4. **Persistencia:** con el toggle activo, cambia a otra vista, espera unos segundos, apaga y enciende. Entra en MIDI 1 → Preset: debe seguir encendido, y las notas deben seguir enviando cambios de programa.
   - Si no se mantiene, prueba a entrar y salir de Setup antes de apagar, y dime qué ha pasado en cada caso.
5. Haz lo mismo con MIDI 2 y con el toggle Ch16 de Setup.

## Volver atrás
Envía SC06 (o anterior) con el cargador. Si no arrancara, enciende con Scales + Preset + Note.
