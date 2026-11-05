# S516D2 (diagnóstico) = S516D con las órdenes de la copia en X:$5FF0

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s516d2/circuittracks-4486-S516D2.syx` | `5f795c5a168fde22593bea27d268cdfaa37a6339573619b5108aa3e8f3b73940` | `S516D2` |

**S516D en el aparato (2026-11-04): la copia no empezaba nunca.** Sus órdenes iban en `X:$3FE8`, que es también donde el núcleo 0 copia en cada bloque los bloques tarde del núcleo 1 (`granular_dsp.FLATE_X`, desde SC51.4): el número de orden del PC quedaba pisado. Aquí van en `X:$5FF0..$5FF4` del núcleo 0 (`granular_dsp.ND_X2`, libre según S494D2). Lo demás, igual que S516D. **Probado (2026-11-04): la copia funciona** (7 zonas en `re/novadump/`).

## Cómo
1. Instalar S516D2. Conectar por USB, cerrar Components / uploader / DAW.
2. Claude: `python tools/novadump.py` (lee la marca y usa `X:$5FF0`). Las copias se quedan en `re/novadump/` (fuera de git, nunca públicas).
3. Volver a instalar la Beta 5.19.

## Verificación en emulación
- `emu_s516d.py` sobre S516D2: ALL PASS (la copia del núcleo 1 no cambia).
