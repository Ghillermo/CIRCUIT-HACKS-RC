# SC50.2 = SC50.1 + los tres modos del LFO que no sonaban + knobs de tipos más lentos + filtro, VCA, efecto de fábrica + secuenciador de saltos revisado

| SHA-256 del `.syx` | Marca |
|---|---|
| `759164aba99285c20d5a121a7d33e38481c445e3ded1ad8aacd5eedef8258235` | `SC50.2` |

## Qué cambia

- **Arreglo: las formas de LFO seno, sample & hold y sample & hold suavizado** (verde azulado, blanco, violeta) dejaban el motor sin su valor ACT en el DSP. También en RC4.05.
- **Knobs de tipos:** al menos 16 clics por tipo: forma del LFO (antes 4), algoritmo FM (antes 8), modo de nota del granular (antes 1). Los demás ya pasaban de 16.
- **Orden de la cadena:** de fábrica filtro, VCA, efecto; pad 29 encendido, VCA, efecto, filtro. Un proyecto o patch guardado conserva el pad, así que su orden se invierte.
- **Secuenciador de saltos:** con el transporte parado, un pad hace sonar ese paso de la pista destino mientras lo mantienes, sin saltar (drums: su golpe con el sample elegido); el pad 27 parpadea en el color del destino; apuntar apaga el motor y encender un motor deja de apuntar.
- **Fila de motores:** el pad 23 apagado en azul tenue de verdad (`0x0F`; antes `0x0A`, casi igual de brillante que el encendido). También en RC4.05.

## Qué probar

1. MIDI 1 con el oscilador, página 5, Shift + K8: las siete formas suenan y mueven lo que el LFO tenga asignado; con las tres últimas el motor sigue sonando.
2. Ese knob cambia de forma cada 16 clics, en los dos sentidos.
3. FM, Shift + K5: un algoritmo cada 16 clics. Granular, Shift + K6: un modo cada 16 clics.
4. Pad 29 apagado: con resonancia alta, la saturación del VCA va después del filtro; encendido, antes.
5. Fila de motores: el pad 23 se distingue encendido de apagado.
6. MIDI 1 con un motor, fila de motores, pad 13 (Drum 1): el motor se apaga y el pad 27 parpadea. Encender un motor (pads 18-24): la pista deja de apuntar y el pad 27 deja de parpadear.
7. MIDI 1 apuntando a Synth 1 con notas en los pasos, transporte parado, vista Note: cada pad hace sonar su paso mientras lo mantienes, sin mover nada. Apuntando a un drum, su golpe con la velocity del paso; un paso vacío, nada.
8. En marcha, una nota de MIDI 1 en el paso 5 que salte al 10 de una pista de la misma longitud: **solo se nota la primera vez**, porque en las vueltas siguientes el destino ya va por ahí. Con otra longitud o con dos saltos en el patrón se oye en cada vuelta.

## Pruebas en emulación

`emu_sc50_2.py` (knobs, orden, pad 23), `emu_actfix_dsp.py` (la ranura ACT y el LFO con las siete formas; en RC4.04 falla con las tres últimas), `emu_jumpseq.py` (parpadeo, exclusión, escucha parado en notas y drums).
