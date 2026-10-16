# R0903D (diagnóstico) = RC0.9.3 + los testigos de S419D2

`circuittracks-4486-R0903D.syx` — SHA-256 `205161dfe22d52bc9bb04df2d4b8356a90ea721270a216024da576c16b94d1c3`, marca `R0903D`.

La RC no tiene stutter (el usuario, 2026-10-16). Este diagnóstico pone en la RC los testigos de S419D2 para comparar: si la RC también enciende **Duplicate amarillo** mientras suena sin que se oiga nada, esos retrasos son del firmware original y no importan.

## Qué probar
1. El mismo proyecto y los mismos gestos que con S421D, con Play.
2. Apuntar el color de Duplicate (amarillo / otros) y si se oye algo.

## Verificación en emulación
- `emu_s419d2.py` sobre R0903D.
