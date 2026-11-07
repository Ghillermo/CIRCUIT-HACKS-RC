# Beta 5.33 = Beta 5.32 (= SC52.9) + segunda página de instrumentos FM

SHA-256 del `.syx`: `0b22fddc0aad2631852a4761f29cfd1cc75faaefaeb7c399f2ff4e0b729b4b42`.

Con FM (pad 24 de la fila de motores), **pad 8 mantenido = los instrumentos; Octave ▼ / ▲ mientras se mantiene = página 1 / 2** (como las páginas de algoritmos del pad 7). Página 2, 24 nuevos: pianos (Grand Piano, Mellow Piano, Honky-Tonk, Tine Piano, Toy Piano), cuerdas (Slow Strings, Ensemble, Cello, Violin, Pizzicato, String Swell), vientos en verde azulado (Clarinet, Oboe, Bassoon, Alto Sax, French Horn, Trumpet, Pan Flute, Recorder, Harmonica) y largos (Cathedral, Bowed Glass, Evolving Pad, Long Bell). En la página 1, releases más largos (pianos eléctricos, cuerdas, pads, coro, flauta, metales, arpa, nylon, campana, bajos). La tabla va comprimida y se descomprime una vez en la ITCM.

1. **Arranque en frío:** instalar, apagar y encender. MIDI 1, motor FM.
2. **Pad 8 mantenido:** los 24 de siempre; Octave ▼ encendido. Tocar E.Piano: suena; al soltar, el release dura más que en la 5.32.
3. **Octave ▼** (con el pad 8 mantenido): la página 2 (vientos en verde azulado); Octave ▲ encendido. Tocar Grand Piano, Slow Strings, Clarinet, Trumpet, Cathedral: cada uno suena y el pad elegido brilla.
4. **Octave ▲:** vuelve la página 1.
5. **Notas largas:** Slow Strings, String Swell, Evolving Pad y Cathedral con notas mantenidas y soltadas: entrada lenta y release de varios segundos.
6. Guardar un patch con uno de la página 2 y cargarlo: suena igual.
