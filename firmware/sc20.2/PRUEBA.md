# SC20.2 — SC19.9 + los cambios de SC20.1, SIN el modo VCF / VCA

`circuittracks-4486-SC20.2.syx` — SHA-256 `a70565a1a8c4decf90d0dc0834068270df0b185d4a0c9c0a7baf510b17df3f33`
Imagen de 0x5c048 bytes, CRC 0xf9940fb8, marca `SC20.2`. Es SC19.9 con la escala en tres filas, K1 = sesgo en la vista cromática, Clear en los knobs nuevos de drums y el pad 7 de Master FX amarillo (ver `firmware/sc20.1/PRUEBA.md`), pero **sin ningún código del modo VCF / VCA** (ni el ARM de `vcf20.py` ni el DSP de `vcf20_dsp.py`).

## Para qué
Informe del usuario (2026-10-05): *las entradas de audio externas no funcionan en SC20*. En emulación, con el modo VCF apagado las entradas pasan bit a bit como en SC19.9, así que el fallo es de algo que la emulación no modela. Con este build y SC20.1 se separa la causa:

| Build | Entradas externas | Conclusión |
|---|---|---|
| SC19.9 (`firmware/sc19.9/`) | ¿funcionan? | si no: el fallo viene de SC18 / SC19.x, no del VCF |
| **SC20.2** (este) | ¿funcionan? | si funcionan aquí y no en SC20 / SC20.1: es el código del VCF (DSP o ARM) |
| SC20.1 | ¿funcionan? | si funcionan: era el estado sin validar de SC20 (ahora con firma) |

Prueba (volumen bajo, proyecto de prueba): Setup → entradas externas en las pistas de audio; comprobar la señal de la entrada de línea 1 / 2 en el mezclador (tiras 3 / 4), como fuente del sinte (vista de la fuente: pads 25-29) y el retorno de reverb / delay del Setup.
