# SC40.2 — ataque y release del compresor master

`circuittracks-4486-SC40.2.syx` — SHA-256 `cc48df64f54e12d24ac36f55427d398808c349c6a6324415334c8fc8b1a8bac2`
Imagen de 0x68a78 bytes, CRC 0xb4f4976d, marca `SC40.2`.

Es SC40.1 con una función nueva (solo ARM): **en la vista Setup, K1 y K2 ajustan el compresor master.**

| Knob | Parámetro |
|---|---|
| K1 | Ataque |
| K2 | Release |

- El compresor se sigue activando en Advanced Setup, como siempre. Estos dos valores existen en el aparato original pero están fijos a 0 y no tienen control.
- Los he identificado leyendo el programa del DSP, no de oído: **confírmalo en el aparato.** El umbral y la ratio son fijos en el DSP; no se pueden tocar.
- **No se guardan:** el aparato no guarda ese grupo con el proyecto. El ajuste dura hasta apagar (o quizá hasta cargar otro proyecto: dímelo).
- Los LEDs de K1 / K2 se encienden en blanco con su valor, solo en la vista Setup.

## Qué probar
1. Con el compresor activado y música con pegada, entra en Setup y gira K1: ¿cambia cuánto golpe inicial pasa? Gira K2: ¿cambia cuánto tarda en recuperar el volumen?
2. Si no se oye nada, o si K1 y K2 parecen hacer otra cosa, dímelo.
3. Carga otro proyecto: ¿se conservan los valores? ¿Y al apagar?
4. Los pads de Setup y Advanced Setup funcionan como siempre.
5. Todo lo de `firmware/sc40.1/PRUEBA.md`.

## Verificación en emulación
- `emu_sc40_2.py`: K1 / K2 mueven los valores 3 / 4 del grupo master con topes; los interruptores, el filtro y la ganancia no cambian; LEDs; en la página Advanced nada; las demás funciones de la vista intactas.
- **Sin comprobar en emulación:** el sonido, y abrir la vista con el gesto real (en la prueba se pone a mano).
