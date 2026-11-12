# SC56.6 = SC56.5 + la caja negra

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc56.6/circuittracks-4486-SC56.6.syx` | `d518c5b85aed3d4a3a2c4b688b38370877717ef6b7723ad7f4eb3f9eb6016615` | `SC56.6` |

**Lo nuevo** (el usuario, 2026-11-12), `tools/blackbox.py`: si el panel se cuelga mientras suena (nada responde, las luces no cambian), a los
15 s el aparato apunta lo último (pulsaciones, vista, el TCB y la pila de la tarea del panel, su PC 8 veces) y se reinicia; al volver, Save
parpadea en violeta 30 s. La app de la tarjeta lo lee con **Caja negra…** (sin abrir la sesión: el panel no se bloquea) y lo guarda en un `.json`.

## Qué probar
1. Uso normal un buen rato, sonando y parado, cambiando de vista con y sin Shift: nada se reinicia, nada más lento.
2. La app, **Caja negra…** con el aparato conectado por USB (sin pulsar Aparato…): «Nada capturado: sigue apuntando», las últimas pulsaciones
   con sus vistas en orden.
3. **Capturar ahora**: «Capturado a mano», la tarea («LEDs» o el nombre que tenga), un PC; **Guardar…** escribe el `.json`; **Vaciar** lo borra.
4. Cargar packs y proyectos, copiar samples / proyectos entre packs, parado y sonando: nada se reinicia.
5. Si el panel se cuelga sonando: esperar 15 s; el aparato se reinicia y Save parpadea en violeta; leer la caja negra con la app y mandar el `.json`.

## Verificación en emulación
- `emu_blackbox.py`: los ganchos, las migas por las entradas reales (botón, pad, knob plegado), los fotogramas de la tarea de LEDs, nada parado /
  sonando desde después del último fotograma / a 14,995 s, congelado a 15 s con el TCB y la pila de prueba, 8 muestras de PC / LR, `SYSRESETREQ`,
  después del reinicio el registro igual y Save violeta / apagado; por SysEx los 16 trozos = el registro, vaciar, capturar, el resto a `fwid`;
  por el analizador USB real una lectura de 137 B.
- `sd_app_test.html?bb=1` (preview `sd-bridge-b5.51`): la app lee, captura, vacía y descifra el registro contra el firmware emulado.
- `emu_morph.py --clear --sus --nocur --four --slow`, `emu_fwid.py`: pasan.
