# Beta 3.8 (B3.8) = SC45.1 = SC45 + banco de acordes: con Record de Setup en amarillo, nada se graba en una pista de notas silenciada en el Mixer

`firmware/sc45.1/circuittracks-4486-SC45.1.syx` — SHA-256 `bb687b1ccf3ef5b7207898fb25455c63f4e983f3f6d7d9f1b4748f90fded9c82`, marca `SC45.1`.
`firmware/b3.8/circuittracks-4486-B3.8.syx` — SHA-256 `435bc55d472171540258ea253a7f8c945fdcabbf3cf46f2f01feb2232178997a`, marca `B3.8` (**Beta 3.8**, el mismo código).

El usuario (2026-10-20): «ajuste: cuando el track está parado (desactivado mediante pad en mixer) y el modo Record amarillo, tocar los steps durante la grabación los reproduce y envía, pero no los escribe en la pista parada (sólo en la que está sonando). Esto permite usar la pista como Chord bank sin que se escriba nada en el banco».

**Banco de acordes:** con la grabación de los ruteos internos encendida (vista Setup, **Record en amarillo**), **nada se graba en una pista de notas (Synth 1 / 2, MIDI 1 / 2) silenciada en el Mixer** (su pad de pista apagado): ni notas ni automatización. Lo que suena en ella (los pasos que tocas, el teclado) sigue sonando y saliendo por su canal; si ese canal es el de Synth 1 / 2, el sinte lo recibe y lo graba (la pista que suena). Con Record de Setup apagado o la pista sin silenciar, todo como antes. Es una función nueva: solo en la beta (las RC siguen igual).

## Qué probar
1. MIDI 1 con el mismo canal que Synth 1 (Setup: canal de salida de MIDI 1 = el de Synth 1). En MIDI 1, unos acordes en varios pasos (el banco).
2. Mixer: apagar el pad de pista de MIDI 1 (silenciada). Setup: **Record en amarillo**.
3. Record + Play. En la vista de pista de MIDI 1, mantener un paso con un acorde: suena en Synth 1 y se graba en el patrón de Synth 1 en la posición que suena. Varios pasos seguidos = una progresión grabada en Synth 1.
4. Parar y mirar MIDI 1: sus pasos siguen como estaban (nada escrito ni movido; tampoco su automatización).
5. Sin silenciar MIDI 1 (pad de pista encendido), lo mismo de antes: los pasos tocados se graban también en MIDI 1.
6. Record de Setup apagado: como siempre (el sinte no graba lo que le llega por el canal compartido).

## Verificación en emulación
- `emu_mutebank.py` (frente a SC45): los tres ganchos (puertas del grabador → `mutebank` en la zona libre → `fxsess`); el mute por el pad de MIDI 1 del Mixer (manejador de stock `0x08046626`); las tres puertas en todas las combinaciones (toggle, bit «interno», MIDI 1 silenciada / Synth 1 / Drum 1 / automatización de MIDI 1 y de Synth 1): con el toggle y MIDI 1 silenciada no se graba nada en MIDI 1 (SC45 sí), todo lo demás igual que SC45; MIDI 1 sin silenciar igual que SC45; la escucha de un paso de MIDI 1 (`0x0804B07A` sobre su vista, como `0x0804B580`): suena igual que SC45 y no se graba en MIDI 1.
- **No cubierto en emulación:** la inyección en Synth 1 de la escucha (en el volcado la escucha suena sin salir por MIDI); la puerta del sinte con un mensaje interno y el toggle sí está probada.
- `emu_autorel.py` sobre SC45.1; `compact_check.py build_sc45_1.py`.
