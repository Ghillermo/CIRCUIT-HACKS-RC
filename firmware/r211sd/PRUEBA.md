# R211SD (diagnóstico) = RC2.11S + la herramienta remota por USB

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/r211sd/circuittracks-4486-R211SD.syx` | `fb19cba966dc755019c7f31c167dfc5df9d2b620b5291f564de98db3c8719ef1` | `R211SD` |

El usuario (2026-10-28): «I'm unable to write to slot 0 (internal memory) with Components, I think this happened after some experimental build
corrupted it»; «wont read or write on components, other packs work fine»; «not working on stock either». El contenido del pack de la memoria interna
(pack 0) está dañado. Antes de RC0.9 (2026-10-14) el mod podía escribir en él cuando era el pack cargado (ficheros `NN_SC34D.bin` de SC34D, samples
capturados `PCM/NN_PCM.wav` de SC35, intercambios de SC37, registros de patch 64+ de SC40D, patches del sinte propio).

Es RC2.11S (nada del mod escribe en la SD ni en la memoria interna) + `tools/rdiag.py` en la zona libre: lee los elementos de un pack por las
mismas llamadas que usa Components y, **solo con órdenes que mande Claude desde el PC y con el permiso del usuario**, borra o escribe elementos.

**Usada el 2026-10-28:** las sesiones 0-14 y 17 del pack 0 eran los ficheros `NN_SC34D.bin` de SC34D (16 B, `SC34DTST`), que la API devolvía en lugar de las sesiones; borrados (con permiso), las 18 sesiones vuelven a verse enteras. Los packs de la tarjeta, sin el problema.

## Pasos
1. Carga en el aparato **un pack de la tarjeta SD** (que el pack 0 no sea el cargado).
2. Instala R211SD con el instalador.
3. Conecta el USB y **cierra Components**, el DAW y cualquier monitor MIDI (en Windows un puerto solo se abre una vez).
4. Avisa a Claude: `python tools/ctremote.py ping` y `python tools/ctremote.py scan 0` listan lo que hay en el pack 0 (sesiones, patches,
   samples, meta, efectos con su tamaño); `dump` lee un elemento entero para compararlo con el formato del stock.
5. Reparación, con permiso: `del KIND IDX 0 --yes` borra un elemento suelto; `delpack 0 --yes` vacía el pack 0 entero (solo si no es el cargado).
   Después, reiniciar y volver a enviar el pack con Components.

## Verificación en emulación
- `emu_sc35d8.py --delete`: el protocolo (ping, mem, info, read, write, del) igual que en SC35DA (los dos fallos esperados: la versión con borrado
  de packs y el borrado de packs permitido).
- Un borrado en el pack 0 mandado desde el PC llega al borrado de stock (la herramienta vuelve desde la zona libre, por debajo de `0x0805CDDC`:
  el guardián de `rodisk` lo deja pasar); el borrado del pack entero rechaza el pack cargado.
