# SC56.2 = SC56.1 + el aparato dice qué firmware lleva

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc56.2/circuittracks-4486-SC56.2.syx` | `0aa0b5a2cf14f06d2336f0d1bdc1eb2b51db1239c9f35d0b220eb88c64f7e619` | `SC56.2` |

**Lo nuevo** (el usuario, 2026-11-11: «In the app, if the device is stock / an unknown custom build, support only stock-compatible features»;
elegido: una pregunta de versión, para los dos aparatos), `tools/fwid.py`:
- El aparato contesta a `F0 7D 43 54 00 seq 00×7 F7` (14 bytes) con `F0 7D 43 54 40 seq 01 m0..m5 F7`: `m` = la marca de la versión (los 6 bytes
  del bloque de versión, `SC56.2` / `B5.47`). El firmware oficial no contesta (la respuesta de identidad, `… 01 01 23 06`, es la misma en todas las
  versiones: no sirve para distinguirlas). En el sitio del gancho de `rdiag` (la entrada de SysEx `0x0801EB30`); con `rdiag` instalado antes
  (diagnósticos) sigue hacia él. 164 B al final de la imagen (`0x6FED0`, 304 B libres al final).
- **Las apps:** `sd_app.html` (y por ella las vistas de `hr_app.html`) pregunta al conectar el aparato; sin respuesta (oficial o anterior a esta)
  esconde Parches custom (e Importar DX7), el sinte propio de Sonidos del proyecto y los campos propios del editor de patrones; un selector
  «Firmware: automático / solo stock / Hacks» lo fija a mano. El Editor de patches pregunta igual y, sin respuesta, no envía nada.

## Qué probar
1. Con esta versión: la app de la tarjeta, **Aparato…** → el aviso de arriba dice «Firmware: SC56.2» y están todas las pestañas.
2. Nada cambia en el aparato (Components, la identidad y el resto del SysEx como antes).

## Verificación en emulación
- `emu_fwid.py`: la respuesta por el enrutador de stock (puertos 0 / 1), los mensajes que no son la pregunta pasan sin tocar; por el anillo USB
  y el analizador real (`emu_sdsysex`) la build contesta y la imagen oficial calla.
- `sd_app_test.html?device=1` (puente con la imagen oficial): 86 / 86, `fw = null`; la app con el puente oficial esconde Parches custom, con el
  de la Beta 5.47 (preview `sd-bridge-b5.47`) contesta «B5.47» y lo enseña todo.
