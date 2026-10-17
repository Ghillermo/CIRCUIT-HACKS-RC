# RC2.01 / RC2.01S (R201 / R201S) = SC44.1 = SC44 / RC2 + el sample capturado antes del filtro master

`firmware/sc44.1/circuittracks-4486-SC44.1.syx` — SHA-256 `03d21f407274f03eedbd20e762a5e9347aa71a04fc9750b4d4b2105398ea59c8`, marca `SC44.1`.
`firmware/r201/circuittracks-4486-R201.syx` — SHA-256 `c8cec0b7d759a5574513c533334492baa25c60384f17300899eddf050ac5b541`, marca `R201` (**RC2.01**).
`firmware/r201s/circuittracks-4486-R201S.syx` — SHA-256 `c547d6e3c313c0d50e04506633debd17afe6552a6666c04b30ab7785ec42b788`, marca `R201S` (**RC2.01S**: + toda escritura o borrado del mod en la tarjeta rechazados, como RC2S).

El usuario (2026-10-17 / 18): «pon el master sampler detras del filtro» · «Todo antes del filtro» · «release as rc2.01».

- **El sample capturado de Master FX** (pad 32 graba, pad 7 / los huecos tocan) **va antes del filtro master**: el filtro master actúa sobre el sample que suena; la captura graba la mezcla sin el filtro (y sigue sin grabarse a sí misma). Antes iba después: la captura llevaba el filtro y el sample sonaba sin él. Los efectos de Master FX siguen detrás de los dos.

## Qué probar
1. Grabar unos compases (pad 32), tocar el sample (pad 7) y mover el filtro master: el sample se filtra como el resto.
2. Grabar con el filtro cerrado: la captura suena sin el filtro (abierta) al tocarla con el filtro en el centro.
3. Los niveles: el sample suena tan fuerte como antes con el filtro en el centro; Glitch y gesto mecánico como antes.
4. RC2.01S: lo de `firmware/rc2s/PRUEBA.md` (guardar un patch propio, copiar proyectos, borrar packs: LED de Save rojo, nada escrito).

## Verificación en emulación
- `emu_sc44_1_dsp.py` (frente a SC44): la lógica (la captura = (L + R) / 2 × 16 de la mezcla antes del filtro y nunca el sample que suena; la reproducción suma sample / 16 a L y R; r4 / r5 / r6 / m4 vuelven y r0 / r1 como los deja el bucle de la mezcla; `smp_tail` sigue a la cadena); `P:$D53` = `jsr smp_post`, `fx_hook` = `jmp smp_tail`; sin sample, el núcleo 0 entero como SC44 bloque a bloque salvo `X:$3D18..$3D1A`; un ruido sonando, leído tras el filtro (`P:$274`): con SC44 no está ahí (se suma después), con SC44.1 sí, cambiado por el filtro, con su nivel en el centro; la pila no más honda que SC44.
- `emu_sc44.py`, `emu_rodisk.py` en R201 / R201S.
