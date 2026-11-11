# SC56 = SC55.9 con más sitio en la flash (nada cambia en el uso)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc56/circuittracks-4486-SC56.syx` | `6e7a8506f2c9946ead938ba5829263011013efa322fa6d4fb8c121c7f815ee06` | `SC56` |

**Lo nuevo** (el usuario, 2026-11-10: «build 1 and then 2», el punto 1 del análisis de optimización): **5 792 B más de flash libre**
(1 679 → 7 471 B en total), sin quitar nada.
- **Los dos programas del DSP empaquetados con LZ + codificación aritmética** (`dspz.use_v2()`, formato `DZ2`) en lugar del LZSS:
  32 646 → 26 808 B (núcleo 0 27 873 → 23 044, núcleo 1 4 773 → 3 764); el desempaquetador ocupa 792 B. Al enviarlos usa la ITCM
  `0x2000-0x2D93` (las probabilidades) y `0x3000-0x3FFF` (la ventana de 4 KB), solo mientras dura el envío, como antes.
  **Desempaquetar tarda más:** ≈ 11,7 M instrucciones del ARM en lugar de 1,2 M, unos 50 ms más al encender (y cuando el aparato vuelve a
  cargar el DSP), mientras el DSP se está cargando.
- **Código al que ya no llegaba nada, fuera:** `mixsolo` v1 (172 B; la v2 de SC50.9 lo sustituyó), el knob, el número y la curva de
  `velcurve` (desde SC51.2 `velglob` se traga K1 de Advanced Setup; queda `c_vcadv`, que usan `ingain` y `velglob`) y el Octave del panel del
  morph (`c_mzpanel`, sin uso con `use_nocur`).
- `morphz` llena el final de la imagen el último (el primer hueco de `dspz` es ahora más grande que el final).

## Qué probar
1. **Encender:** el aparato arranca y suenan Synth 1 / 2, drums y el sinte propio de MIDI 1 / 2 (oscilador, FM, granular, muestra): los dos
   programas del DSP llegan bien.
2. Algo que haga volver a cargar el DSP (salir de un envío de Components, por ejemplo): vuelve a sonar.
3. Lo tocado: Mixer pad 16 (solo y solo flip), Setup K1 / K2 (velocity), Advanced Setup K3 (ganancia de entrada), el morph de patches.

## Verificación en emulación
- `emu_dspz.py` SC55.9 / SC56: el envío al DSP (modos 0 y 1) **manda los mismos bytes** que SC55.9 (115 trozos, 56 766 B en el modo 0) con el
  desempaquetador nuevo; la ITCM baja como la de SC55.9.
- El empaquetador del instalador (`dzPack2`, JavaScript) da los mismos bytes que el de Python (comprobado en el navegador).
- `emu_mixsolo2.py`, `emu_velglob.py`, `emu_ingain.py`, `emu_morph.py --clear --sus --nocur`, `emu_patmut.py` (contra SC55.7): pasan.
- `emu_tabpack.py`, `emu_loadcache.py`, `emu_fm8dest.py`, `emu_osc1x_dsp.py` dan los mismos fallos con SC55.9 / SC55.8 (comparan con la
  build anterior a su función).
