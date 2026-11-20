# S717D (marca `S717D`) — diagnóstico

= Alpha 7.17 + `blackbox.use_memrd()` + `tools/sxpanel.py`, sin `tools/fxstep.py` (sitio). La vista de macros global probada en el aparato desde el PC:

    python tools/gmview_dev.py

No guarda nada: devuelve los niveles y envíos que mueve y quita los enlaces.

**Probado 2026-11-20:** con el Mixer en panorama, K3 subió a la vez el nivel de Synth 1, el envío de reverb de Synth 2 y el de delay de MIDI 2 (5 cada uno; el nivel ya estaba en 127), el Mixer siguió en panorama, los enlaces se quitaron, la vista se cerró con Mixer solo, la caja negra vacía. Después se instaló la Alpha 7.17 (contesta `A7.17`).
