# SC46.9 / Beta 3.26 = SC46.8 / Beta 3.25 + dos arreglos de la RAM que dejan el encendido o una build anterior

`firmware/sc46.9/circuittracks-4486-SC46.9.syx` — SHA-256 `1adec4d25db9a9516959f6c632ccb59c94a2e1b2cd12abfddc46619e62673d55`, marca `SC46.9`.
`firmware/b3.26/circuittracks-4486-B3.26.syx` — SHA-256 `5a4c8967c2f4d89f5f0f8bcfe4c72a5d3e976d2914d4a6090ea74f8bc1a485ff`, marca `B3.26` (**Beta 3.26**, el mismo código).

El usuario (2026-10-26): «fm synth sounds clicky, with really short gates and no improvement» · «nevermind, they're ok after reboot» · «Manual note input doesnt work until somthing is recorded in realtime with rec on MIDI tracks» · «tested on midi 1 with fm on» · «replicates on midi 2» · «with all sound sources».

## Qué probar
1. **Introducción manual de notas** en MIDI 1 / 2 con el sinte propio encendido (cualquier modo), recién encendido el aparato y **sin tocar Record**: los pads de paso funcionan como siempre.
2. **Record mantenido + pad de paso** (la foto del motor en los carriles): sigue funcionando; al soltar Record, los pads de paso vuelven a ser los de siempre.
3. **FM tras instalar** (sin apagar): con una beta anterior a la 3.23 instalada, instalar esta y tocar el FM sin apagar: suena con sus ataques / decays normales (Shift + K1-K4 en el centro), no con clics y notas cortísimas.
4. Lo de SC46.8 / Beta 3.25 sigue igual.

## Verificación en emulación
- `emu_risig.py` frente a SC46.8 / Beta 3.25: con los bytes de `recinst` llenos de basura (tres patrones), en SC46.8 el pad de paso se traga (el fallo reproducido) y en SC46.9 llega al manejador de stock; Record + paso sigue siendo la foto, y después los pads son los de stock; un bloque FM de versión 1 («FME1», Shift + K1-K4 = 0) se vuelve a preparar («FME2», en el centro), en SC46.8 se quedaba.
- `emu_p4dest.py` (la foto) y `emu_fmeng2.py` sobre SC46.9: como en SC46.8 (los 3 fallos de `emu_p4dest` son de diseño desde SC45.x: las cadenas del guardado de patches y el relleno de 124 B).
