# SC21.4 — SC21.3 + filtros paso bajo y paso alto de 12 y 24 dB en la lista del VCF

`circuittracks-4486-SC21.4.syx` — SHA-256 `cbd4115afc763bc3d7834b3c5b9d67f7957f810e75bcdc5db4f088e88014a0c7`
Imagen de 0x5d4e0 bytes, marca `SC21.4`. Es SC21.3 con tipos de filtro nuevos; si falla, vuelve a SC21.3 o SC21.2.

## Qué hace
La lista de tipos de filtro del modo VCF (Shift + K5, un paso por giro, con vuelta) pasa a siete:

| Tipo | Filtro | K5 (sin Shift) |
|---|---|---|
| 0 | **DJ** (el de siempre) | bipolar: izquierda paso bajo, derecha paso alto, centro = sin filtro |
| 1 | **paso bajo 12 dB** | frecuencia de corte |
| 2 | **paso alto 12 dB** | frecuencia de corte |
| 3 | paso banda | frecuencia de corte |
| 4 | notch | frecuencia de corte |
| 5 | **paso bajo 24 dB** | frecuencia de corte |
| 6 | **paso alto 24 dB** | frecuencia de corte |

Con los tipos 1-6 K5 es la frecuencia de corte (de grave a agudo), y la resonancia, la envolvente → filtro, el LFO → filtro y el seguimiento de la nota actúan igual que antes. El de 24 dB es el mismo filtro de variable de estado ejecutado **dos veces** (segunda etapa con su propio estado). El LED del Shift + K5 enseña el tipo por brillo.

## Prueba (volumen bajo)
1. MIDI 1 → Preset → pad 26 (azul): modo VCF encendido, con una entrada de línea sonando.
2. Shift + K5 gira por los tipos; K5 (sin Shift) barre el corte en los tipos 1-6. Compara 12 y 24 dB con el mismo corte: el de 24 dB corta mucho más fuerte por encima / por debajo.
3. Con la resonancia (K6) alta el filtro resuena en cada tipo; en 24 dB algo más.
4. Puede notarse un pequeño ruido al mover el corte rápido (el coeficiente salta por bloque de 32 muestras).

## Notas técnicas
- `vcf21_dsp.SLOPES`: `FMODE` = el tipo (1 LP12, 2 HP12, 3 paso banda, 4 notch, 5 LP24, 6 HP24); los modos 5 / 6 repiten el lazo de paso bajo / alto con `r2` como puntero de la segunda etapa (`X:$3800 + 48 t + 2 c`: dos palabras por canal; en el retorno de FX L y R tienen cada uno el suyo); `r2` se guarda y restaura. El estado guardado lleva la firma 0xA8: al flashear sobre SC21.1-SC21.3 el estado del modo VCF se reinicia (los números de los tipos cambian).
- El programa del DSP **termina en `P:$37FE`** (quedan 2 palabras hasta `$3800`).
