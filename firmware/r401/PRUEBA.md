# RC4.01 / RC4.01S = RC4 + los arreglos desde RC4

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/r401/circuittracks-4486-R401.syx` (**RC4.01**) | `fb17bf34acb501f89298a753270b3f24e9c6448531c010aa0a3331b5fdbba9ce` | `R401` |
| `firmware/r401s/circuittracks-4486-R401S.syx` (**RC4.01S**) | `a18d5c86e9013891d32087d35d973d67ad7c52ac700ea9028298b6b7204baa96` | `R401S` |

= SC48.7 (sin editor de CC con el sinte propio encendido, issue #15; pad 31 solo con el VA-drum; VA-drum + pad 31 en la fila de motores) +
`autorel.use_init()` (el usuario, 2026-10-29, en RC4: «the shift step doesn't revert previous automation back to init», «the cleared
automation must go to Project init»). RC4.01S = RC4.01 + `rodisk.use_allpacks()` (como RC4S).

## Qué probar
1. Synth 1: girar un macro, Record mantenido + paso 1 (foto), Play; marcar el paso 5 (Velocity + Shift + paso 5, rojo): en el paso 5 el
   macro vuelve al valor guardado en el proyecto.
2. Lo mismo en MIDI 1 / 2 con el sinte propio encendido (el sonido guardado con el proyecto; un proyecto sin él, los valores por defecto).
3. Lo de SC48.7 (`firmware/sc48.7/PRUEBA.md`).

## Pruebas en emulación
`emu_sc49_1.py` sobre R401 frente a RC4 (ALL PASS: RC4 devolvía el knob).
