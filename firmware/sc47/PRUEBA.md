# SC47 / Beta 3.27 = SC46.9 / Beta 3.26 + polifonía del sinte propio (fase 1) + los lados del sample estéreo

`firmware/sc47/circuittracks-4486-SC47.syx` — SHA-256 `f134d2ca60720b071402a084d0f54fd489a6365ca3a0a62d47b08c42e1919cd6`, marca `SC47`.
`firmware/b3.27/circuittracks-4486-B3.27.syx` — SHA-256 `6d7e69e9f76cb944c5ad0df47c44cf3ca15731175cf847983da4d47cd9ffb2fe`, marca `B3.27` (**Beta 3.27**, el mismo código).

El usuario (2026-10-25): «Polifonía: todos los modos de MIDI, 4 voces si es posible. Voice stealing idealmente en la más antigua de su propio canal. En caso de vcavcf compartidos, nueva nota abre Gate de nuevo. Noteoff desactiva el pitch correspondiente y cierra Gate cuando no quedan pitchs activos.» Fase 1: el oscilador (un oscilador, también la supersaw) y el modo muestra (también en estéreo). FM, dos osciladores, VA-drum y granular siguen con una voz.

## Qué probar
1. MIDI 1 con el sinte propio en **oscilador**, vista Preset: **Shift + pad 29** pasa por retrigger (verde) → legato (amarillo) → **poly (magenta)** → retrigger. Se guarda con el proyecto.
2. En poly, tocar acordes en los pads o desde el secuenciador: hasta **4 notas a la vez**, cada una con su velocity; la envolvente, el filtro y el efecto son los de la pista (una nota nueva vuelve a disparar la envolvente).
3. **Soltar una nota con otras pulsadas** la apaga (un fundido muy corto); **la última** suena con el release de la envolvente; una nota nueva después de soltarlas todas corta la que sonaba.
4. **Una quinta nota** quita la voz de la nota más antigua (con un fundido de ~2 ms antes).
5. La **supersaw** (SHAPE a la derecha con la sierra) en acordes; el **modo muestra** en acordes, con flips por paso y en **estéreo** (WAVE > 0): cada nota su sample.
6. Poly en FM, dos osciladores, VA-drum o granular: suenan como siempre (una voz). Con retrigger o legato, todo como antes.
7. CPU: 4 voces de supersaw en las dos pistas a la vez, con drums y Master FX: escuchar si hay chasquidos.
8. **El sample estéreo** (el usuario, 2026-10-26: «con wave a la derecha completamente, dos samples por los dos canales … ¿su rango no está llegando a 127?»): con WAVE a la derecha del todo, **el sample elegido solo por la izquierda y el segundo solo por la derecha** (antes salían al revés); a medio recorrido, abiertos a medias.
9. Lo de SC46.9 / Beta 3.26 sigue igual (la introducción manual de notas, el FM).

## Verificación en emulación
- `emu_smswap_dsp.py` frente a SC46.9 / Beta 3.26, en el núcleo 0 entero (las mezclas L / R tras `smp_post`, con la rampa del nivel del mezclador ya hecha): WAVE 0 = el primer sample igual a los dos lados (la referencia m); WAVE 126 solo el primero = L ≈ m, R ≈ 0 (2,6 %); solo el segundo = R ≈ m, L ≈ 0; WAVE 64 entre medias; en SC46.9 el primero salía por la derecha (el fallo reproducido). Igual del continuo al Nyquist (medido aparte).
- `emu_poly_dsp.py` frente a SC46.9 / Beta 3.26: con una voz, el anillo, el búfer de lados y los bloques OSC1 iguales (seno, sierra, supersaw, muestra mono y estéreo); el oscilador con dos voces (notas 48 / 55) = la suma de dos ejecuciones de una voz × la ganancia que va de 0 al objetivo en el primer bloque, la voz 1 apagándose en el bloque 3 (luego en silencio, su registro quieto) y otra vez en el bloque 5 con la nota 60 desde sus fases; las voces 2 / 3 sin tocar; el bloque OSC1 vuelve a lo suyo tras cada bloque; la muestra con dos voces (TV 1 = el sample de la pista, TV $107 = el 7) mono y estéreo (el centro y el lado de las sumas), bit a bit; con dos osciladores, el camino de una voz.
- `emu_poly.py`: Shift + pad 29 (los tres estados, magenta); el flanco (los registros desde cero, luego la base); cuatro notas, una voz cada una (NOTE, TV, el objetivo = velocity << 16, TRIG), VEL del motor 127; la quinta quita la más antigua (objetivo 0, arranque 2 ticks después); note-off con otras pulsadas; la última sigue; una nota nueva sin ninguna pulsada; el flip pendiente (TV $107, sin gastarlo); velocity 0; dos osciladores / poly apagado = la base a 0.
- Sobre SC47 como antes: `emu_fm2_dsp`, `emu_fmeng2`, `emu_smst`, `emu_smst2_dsp`, `emu_kbin`, `emu_risig`, `emu_dupnote` (todo bien); `emu_shortimm_dsp` (solo «el programa más corto»: crece) y `emu_arp` (11 fallos, los mismos que en SC46.9: no vale desde SC45.3) por diseño.
