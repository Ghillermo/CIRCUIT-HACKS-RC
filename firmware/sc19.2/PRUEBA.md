# SC19.2 (EXPERIMENTO) — ¿por qué SC19, SC19.1 y SC20D se cuelgan al encender?

`circuittracks-4486-SC19.2.syx` — SHA-256 `b2e0f44ced25f14674d6eb8ea409de0538932fc375d2b7159b680c8a500f4c98`
Imagen de 0x5b6b4 bytes, CRC 0x9edd3b74, marca `SC19.2`.

**No es un build de uso normal.** Es SC19.1 con el trabajo de «ajustes guardados en el proyecto» **escalonado después de encender**, para saber qué lo cuelga. Si se cuelga, reinicia en modo bootloader y flashea **SC17.7** (la última confirmada en tu aparato).

## Qué cambia respecto a SC19.1
SC19.1 hace al encender, por su cuenta, un trabajo diferido (carga los ajustes guardados, apaga Master FX y el song pointer, y manda al DSP todos los valores de los drums). SC19.2 lo escalona con el tiempo desde que se enciende:

| Desde que se enciende | Qué hace |
|---|---|
| menos de 15 s | **Nada.** Los tres ganchos del proyecto, el servicio del DSP y el código del DSP son los de SC19.1. |
| 15 s (etapa A) | Carga de los ajustes a la RAM, validación y apagado de Master FX y song pointer. **Sin ningún mensaje al DSP.** |
| 30 s (etapa B) | Los valores de los drums se mandan al DSP (valores absolutos). |

## Qué probar y anotar
1. Flashea SC19.2 y enciende. **¿Arranca?** (los LEDs y los botones responden).
2. Si arranca, **no toques nada** y mira el reloj: **¿se congela?** Anota cuántos segundos después de encender (≈ 15 s, ≈ 30 s, o nunca).
3. Si no se congela, prueba lo normal un par de minutos: vista cromática de drums, Master FX, y la vista de la fuente (Synth 1 dos veces). Mueve un knob de los drums. Guarda el proyecto, apaga y carga.

## Cómo leer el resultado
| Lo que pasa | Qué significa |
|---|---|
| **Se cuelga al encender** otra vez | El trabajo diferido no es la causa. Quedan el código nuevo del DSP de los drums, los gestores de macros y los ganchos nuevos de botones / LEDs (siguiente prueba: un build sin ellos). |
| Arranca y se cuelga a los **≈ 15 s** | Falla la etapa A: la carga de ajustes, la validación o el apagado de Master FX / song pointer. |
| Arranca y se cuelga a los **≈ 30 s** | Fallan los mensajes de los drums al DSP (valores absolutos) o el código del DSP que los recibe. |
| Arranca y **no se cuelga** | Era un problema de orden al arrancar: este build ya sirve (los ajustes se guardan a partir de los 30 s). |

## Qué no cambia
Todo lo demás es SC19.1 (vista de la fuente con doble pulsación, resonancia en el botón 1-16/17-32, etc.). Si se carga o se guarda un proyecto antes de los 30 s, el guardado de los ajustes de esa primera carga puede no llegar a hacerse: espera ese tiempo.

## Verificación en emulación
`tools/emu_sc19_2.py` (etapas: nada antes de 15 s, etapa A sin mensajes, nada hasta 30 s, etapa B con los mensajes, un knob antes de las etapas se manda igual, una carga a los 100 s abre las dos etapas) y `tools/emu_sc19.py` sobre esta imagen (la RAM del volcado lleva 107 s encendida, así que las dos etapas están abiertas). El programa del DSP es idéntico al de SC19.1.
La emulación **no reproduce** el cuelgue: por eso es un experimento.

## Volver atrás
SC17.7 (confirmada) o SC183D (diagnóstico que ya has probado).
