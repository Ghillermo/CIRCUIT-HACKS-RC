# RC4.17 / RC4.17S (marcas `R417` / `R417S`) — pendientes de probar, sin publicar

= RC4.16 / RC4.16S + `tools/dbtoggle.py` (arreglo; el usuario, 2026-11-18: «Pages (shift+tracks 1-4) exit wrong when they are opened and shift+any track is pressed again» → «Toggle: exit»): **con la página de una pista en pantalla (la vista de la fuente de Synth 1 / 2, la Preset de MIDI 1 / 2), Shift + el mismo botón = su vista Note**; otra vez = la página; Shift + otro botón de pista = la página de esa pista (como antes). Antes Shift + el mismo botón volvía a abrir la página. 108 B al final de la imagen. RC4.17S = lo mismo sobre RC4.16S (no escribe en la tarjeta).

## Probar
1. Shift + Synth 1: su página; Shift + Synth 1 otra vez: vista Note; otra vez: la página. Lo mismo con Synth 2, MIDI 1, MIDI 2.
2. Con una página abierta, Shift + otra pista: la página de esa pista.

Prueba: `emu_dbtoggle.py` (RC4.16 falla las cuatro pistas).
