# Beta 1.29 (B1.29) = SC43.9 = SC43.8 + formas del LFO del sinte propio + el programa del DSP compactado

`circuittracks-4486-SC43.9.syx` — SHA-256 `d6a9565a2ba562ebeaaa3f042c50860bbc8878169ef11a30ab026ad9d8245040`, marca `SC43.9`.
`firmware/b1.29/circuittracks-4486-B1.29.syx` — SHA-256 `090ca6a0a575ff41b00de99d4b6f09b9153e1f9d30073cdd913ddf1562dc5035`: el mismo código con la marca `B1.29` (**Beta 1.29**).

El usuario (2026-10-17): «Start with the DSP compaction (short x:(rn+d) forms), then add the LFO waveshapes on page 5 Shift + K8».

- **Formas del LFO** del sinte propio de MIDI 1 / 2: página 5 de knobs, **Shift + K8**: diente de sierra inverso (naranja, la de siempre), diente de sierra (magenta), triángulo (verde), cuadrada (roja), seno (cian), sample & hold (blanco). Un paso cada 4 clics. Con el proyecto y en el patch propio.
- **El programa del DSP compactado:** el mismo sonido, 441 palabras menos; quedan 372 libres en el núcleo 0.

## Qué probar
1. Todo lo de antes suena igual (drums, sintes, Master FX, el sinte propio y el granular): la compactación no debe cambiar nada.
2. MIDI 1 con el oscilador, página 5: K6 (LFO → filtro) o K5 / K7 con un poco de cantidad; Shift + K8 por las seis formas: el LED cambia de color y la modulación de forma (la cuadrada salta, el sample & hold cambia a saltos al azar en cada vuelta).
3. Guardar el proyecto, cargar otro y volver: la forma vuelve. Guardar un patch propio con una forma y cargarlo en la otra pista: la misma forma.

## Verificación en emulación
- `emu_sc43_9_dsp.py` (frente a SC43.8): en la parte de stock del programa solo cambian los destinos de los cuatro ganchos; 441 movimientos de una palabra más; el tráfico real del motor propio (358 mensajes), golpes de drums y notas de Synth 1 / 2 sobre el núcleo 0 entero de las dos builds: X e Y `0..$3FFF` idénticas en los bloques 60, 150, 230 y 300; las formas 1-5 en MIDI 1: el LV de cada bloque igual al modelo (diente de sierra, triángulo, cuadrada, seno en coma fija con el limitador, sample & hold con un valor nuevo en cada vuelta y solo entonces).
- `emu_sc43_9.py`: Shift + K8 en la página 5: 3 clics nada, el cuarto la forma 1; hasta 5 y hasta 0 sin vuelta; el byte de MIDI 2 intacto; K8 sin Shift sigue siendo LFOP; el LED con Shift en el color de la forma a todo brillo; el ACT de MIDI 1 lleva la forma en los bits 13-15; el patch: versión 2 con la forma; uno de versión 1 carga la de siempre, uno de versión 2 su forma.
