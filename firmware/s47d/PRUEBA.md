# S47D (diagnóstico) = SC47 / Beta 3.27 + lectura remota del DSP por USB

`firmware/s47d/circuittracks-4486-S47D.syx` — SHA-256 `fad712fc90aeac6537717edca3023239d969e539f11e525a8c5dd09764e4e0c9`, marca `S47D`.

El usuario (2026-10-26), con la Beta 3.27: «sigue oyéndose por los dos lados lo mismo» (el modo muestra estéreo). En la emulación del núcleo 0 entero los dos samples salen cada uno por su lado; esta build deja que Claude lea desde el PC (`tools/ctremote.py dspr / dspw`) la memoria del DSP mientras suena una nota: el búfer de lados, los niveles del mezclador, la ganancia del VCA, la anchura.

## Cómo
1. Instalar S47D (funciona como la Beta 3.27). Dejar el aparato conectado por USB a este PC y cerrar Components / navegador con el uploader / DAW (el puerto MIDI solo se abre una vez).
2. MIDI 1 en el modo muestra, WAVE (K7 de OSC 1) a la derecha del todo, dos samples distintos (Shift + el elegido para el segundo).
3. Hacer sonar notas largas (mantener un pad o un patrón en marcha) y avisar: Claude lee el DSP.
