# Alpha 7.05 (marca `A7.05`) — pendiente de probar, sin publicar

= Alpha 7.04 + `poly.use_quarter()`: con 4 o más voces de FM en una pista, cada voz se manda al DSP cada 4 ms en lugar de 2 (S704D en el aparato: con 6 voces el FM se llevaba el 27 % de la CPU y las escrituras SPI al DSP el 8,6 %; el SPI2 ya está en su divisor más rápido). En emulación, −30 % de trabajo del FM por tick con 6 voces.
+ **Arreglo:** el aviso de cambio de la pista (algoritmo, parámetros: `B_DIRTY`) se borraba tras cada tick y una voz solo lo lee en su propio tick: las voces de la otra fase no veían el cambio (también con 2 ms, Alpha 7.04 y anteriores). Ahora se mantiene 2 / 4 ticks.
Sitio: `jumprnd` al final de la imagen (`dspz.use_move`).

## Probar
1. 6 voces de FM: tempo estable; las envolventes rápidas del FM sin escalones audibles.
2. Cambiar el algoritmo con un acorde sonando: todas las voces cambian.
3. Step flip con varias notas en un paso (jumprnd).

Pruebas: `emu_fm8poly.py`, `emu_jumprnd.py`, `emu_jumpfix.py` (pasan); `emu_poly3.py` falla igual que en 7.04 (prueba antigua).
