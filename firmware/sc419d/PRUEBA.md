# SC419D (diagnóstico) = SC41.9 + banco de pruebas del stutter del delay

`circuittracks-4486-SC419D.syx` — SHA-256 `ddd77df2573f8d1b5fb15c8580d35528475562988b64e84b609a10f10b5f8a63`, marca `SC419D`.

Para localizar los «stutter audibles (de ritmo) sobre el delay al cambiar entre modos de sinte o mover sus perillas» (el usuario, 2026-10-15). Es SC41.9 completo con tres testigos que se encienden **400 ms en el momento del fallo**:

| LED | Color | Qué ha pasado |
|---|---|---|
| **Save** | rojo | El DSP ha sacado bloques de audio más despacio de lo normal (menos del 95 % de su mejor ritmo en una ventana de 64 ms): el núcleo 0 se ha pasado de tiempo o el núcleo 1 ha tardado en servirle la memoria externa. |
| **Duplicate** | amarillo | El bucle principal del ARM se ha retrasado: más de 10 ms entre dos servicios del DSP (lecturas de la tarjeta, trabajo largo de la interfaz…). |
| **Play** | naranja | Con el transporte en marcha, el tick del secuenciador ha llegado más de 1,5 veces tarde (a 120 BPM, más de ~33 ms en lugar de 21). |

Fuera de esos momentos, Save, Duplicate y Play se ven como siempre.

## Qué probar
1. Proyecto con delay audible (envíos de delay altos en alguna pista), Play.
2. Sin tocar nada durante un rato: ningún testigo debería encenderse (si Save parpadea solo, apúntalo).
3. Repite lo que produce el stutter: cambiar de modo el sinte (¿cuál? pad 27 de MIDI 1 / 2, patch de Synth 1 / 2, modo mono / poly…) y mover sus knobs. Apunta **qué testigo se enciende justo cuando se oye el stutter**: Save, Duplicate, Play, varios o ninguno.
4. Si es posible, lo mismo con el sinte en cada motor (oscilador, VA-drum, granular) y con Synth 1 / 2 de stock.
5. Si ningún testigo se enciende con el stutter, el problema no es de tiempo (sería un parámetro que se reenvía); dímelo también.

## Verificación en emulación
- `emu_stutdiag.py`: el servicio real del DSP (`0x08021392`), el tick de stock del secuenciador (`0x0802C418`) y la llamada real de la tarea de LEDs, con la lectura del contador del DSP respondida por el arnés: ritmo estable sin eventos; una ventana al 84 % = Save rojo 400 ms; 15 ms entre servicios = Duplicate amarillo; ticks a 21 ms nada, a 40 ms Play naranja; parado, nada.
- El programa del DSP lleva `move a1,y:>$3b0f` tras el incremento de `CNT` (una vez).
