# Beta 5.63 = Beta 5.62 + los arreglos de la caza de fallos del 2026-11-14

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.63/circuittracks-4486-B5.63.syx` | `f9e46ddcd3fece487e14a782d3741e8b5bce45f94e4a2145accc4063ddfcc2c3` | `B5.63` |

= SC57.8 con la marca de la beta. Incluye las Betas 5.61 / 5.62 (sin publicar). Todo son opciones en `tools/fixes563.py`; detalle en
`docs/NOTAS.md` («RC4.14 / RC4.14S, SC57.8 / Beta 5.63») y en `docs/CHANGELOG.md`.

**Antes de instalar, si guardaste proyectos con las Betas 5.58-5.62:** su cola (carriles extra, cadenas de grupos) se escribía en el proyecto
*pack* del pack *hueco* (pack y hueco al revés). En el pack cuyo número es el hueco de tu proyecto puede haber un proyecto fantasma de unos 187 KB,
o un proyecto que ha crecido, con el número de tu pack: **bórralo con la app sin cargarlo** (la app muestra el tamaño de cada proyecto; uno normal
tiene 160 780 B, o 186 812 B con carriles extra).

## Qué probar
1. **Guardar y volver a cargar** un proyecto con carriles extra (Record + Play girando un knob que no es secuenciable en MIDI 1) y cadenas de grupos:
   tras apagar y encender, los carriles y las cadenas vuelven; **ningún otro proyecto ha cambiado** (mirar con la app: tamaños); Save no se pone
   rojo salvo en el pack interno (donde no se escribe nada).
2. **Grabar knobs del VA-drum** (MIDI 1 con el VA-drum, Record + Play, girar K1-K8 de OSC 1): antes se colgaba.
3. **Carriles extra parado:** con el transporte parado, Record mantenido + un paso en la vista de pista de MIDI 1 (con un parámetro fuera de su
   valor inicial que no está en los secuenciables), luego Play: el paso toca el valor; cambiar de patrón y volver: sigue.
4. **Clear + pad de escena** (Mixer) en una escena con cadenas de grupos: al elegirla de nuevo no trae cadenas ni se ve encadenada.
5. **Hueco secuenciable liberado:** Duplicate + knob sobre un knob de la página 4 (lo libera); con automatización grabada en ese carril, Play: el motor
   no se apaga y no sale ningún CC 0 por MIDI.
6. **Step flip:** (a) con MIDI 1 apuntando a Synth 1 a la mitad de velocidad, parar justo tras una nota de MIDI 1 y volver a dar Play sin que
   nada apunte: Synth 1 no salta; (b) parado, mantener un pad de MIDI 1 (suena el paso de Synth 1), dar Play y soltar: la nota se apaga; (c) con
   un drum destino, mantener un pad sobre un paso con flip y tocar otro sobre un paso sin flip: suena el sample elegido; (d) tras Play, el
   primer paso de MIDI 1 con una nota salta siempre.
7. **Arpegiador esclavo de un reloj MIDI externo** (Setup: Clock Rx), el patrón a 1/8 y el arpegio a 1/32: notas regulares a 150 y a 96 BPM del
   reloj; sin reloj, como antes.
8. **Captura fijada tras instalar:** con una captura fijada (pad 32 corto) sonando, instalar esta misma versión no vale (misma marca): instalar otra
   y volver; o provocar el reinicio de la caja negra. Tras el reinicio la captura vuelve a grabar de verdad (antes grababa en silencio).
9. **Las tablas del FM desde la ITCM** (exp / inc / bexp): los sonidos FM de 8 operadores y los patches de ejemplo suenan igual que en la 5.62
   (afinación, envolventes, brillo); también al volver del modo 1 (Components) al 0.
10. Lo de las Betas 5.61 / 5.62: el arpegio a 1/32 sobre un patrón a 1/8 sin swing; la captura sigue al cargar un proyecto; Play no cuelga.

## Verificación en emulación
Los resultados están en `firmware/b5.63/RESULTADOS.md` (los scripts, con sus argumentos, en `docs/NOTAS.md`).
