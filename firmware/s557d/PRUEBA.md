# S557D (diagnóstico) = Beta 5.57 + `rdiag` (lectura de la memoria externa del DSP por USB)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s557d/circuittracks-4486-S557D.syx` | `b007de782d8d4a8fad4fb5ced033352fcc078932d2c2fbb5489026e72f488e2d` | `S557D` |

**Para qué:** más carriles de automatización para el sinte propio (25 destinos, 2 valores por paso) necesitan ≈ 3,2 KB para los dos patrones que suenan y en la RAM del ARM no queda sitio. Candidata: la memoria externa del DSP `Y:$337000-$33FFFF` (36 864 palabras), sin usar en SC35D3. Este diagnóstico comprueba que sigue sin usarse con todo lo de la Beta 5.57.

**Qué hace:** todo lo de la Beta 5.57 y, por USB, `rdiag` (lectura de la memoria externa del DSP). En esta build la caja negra y la pregunta de versión no contestan por USB (`rdiag` atiende antes esos mensajes); lo demás, igual.

## Qué probar
1. Instala S557D, conecta el aparato por USB y cierra Components y las apps (puertos MIDI libres).
2. `python tools/dspsnap.py start` (lee la zona: ≈ 1 minuto).
3. Usa el aparato un buen rato: reproducción; el sinte propio de MIDI 1 / 2 con todos los motores (oscilador, FM, granular, wavetable, muestra); Sample Rec y el bucle capturado; **el Glitch** (pad 6 de Master FX); cambia de proyecto y de pack; guarda; si quieres, una sesión de la app de la tarjeta.
4. Sin apagar, con el aparato conectado: `python tools/dspsnap.py end`.
5. Resultado: «candidate … (untouched)» = la zona sirve. El bloque de control (el anillo del Glitch) debe cambiar si se usó el Glitch (comprueba que la lectura ve cambios).

## Verificación en emulación
- `emu_sc35d8.py --dspx`: todo pasa (la entrada de SysEx: lo nuestro a `rdiag`, lo demás a la caja negra y al stock).
