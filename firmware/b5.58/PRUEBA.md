# Beta 5.58 = SC57.3 con la marca de la beta

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.58/circuittracks-4486-B5.58.syx` | `8fd25ca9f978aad9cb918b653da72fe2a49023807100cb674cffd229ec333d23` | `B5.58` |

**Lo nuevo** (sin probar en el aparato):
- **Carriles extra del sinte propio de MIDI 1 / 2:** cada parámetro del motor que no está en los knobs secuenciables tiene su propio carril (hasta 25 por patrón, dos valores por paso).
- **Destinos con Duplicate + knob** en lugar de Shift + knob.
- **Sin los 48 instrumentos FM** (pad 8 mantenido): están como Parches demo en la app.

## Qué probar
1. MIDI 1 con el sinte propio (oscilador). En la página OSC 1, con Record + Play, gira K3 (forma de onda): se graba y se oye en la reproducción. Gira otros knobs que no están en la página 1 (knobs secuenciables).
2. Para y vuelve a reproducir: suenan. Cambia de patrón y vuelve.
3. Guarda el proyecto, apaga, enciende y cárgalo: los carriles siguen. En la vista Projects el proyecto no se ve tenue.
4. Guarda en otro hueco y carga ese: los carriles están.
5. Duplicate de un patrón de MIDI 1 a otro (vista Patterns): los carriles van con él. Clear de un patrón: se borran.
6. Clear + K3 a la izquierda: se borra su automatización. Record + paso (foto). Nudge (pad 26 de Pattern Settings). Shift + paso en Velocity (suelta la automatización).
7. Duplicate + knob: en la página 1 (knobs secuenciables) deja el hueco libre; en OSC 1, Duplicate + K3 lo pone en ese hueco.
8. FM: el pad 8 abre la página FM; mantenerlo no abre ninguna lista.
9. Si puedes: Components, «enviar» el mismo proyecto a su hueco; los carriles siguen.

## Verificación en emulación
- `emu_xlanes.py`: guardado / carga / proyecto nuevo, cabecera y suma, pegar / borrar patrones, Components (el mismo proyecto vuelve con carriles, otro no, una cola del anfitrión se respeta), grabación y reproducción (micropasos 0 / 3), Clear + knob, paso marcado, foto, Nudge, la comprobación de la vista Projects.
- `emu_p4dup.py`: Duplicate + knob.
- `emu_fm8v2.py`: sin lista de instrumentos.
