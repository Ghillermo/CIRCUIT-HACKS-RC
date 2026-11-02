# SC50.4 / Beta 5.7 / RC4.06 / RC4.06S

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc50.4/circuittracks-4486-SC50.4.syx` | `422551588d5d7e0f7c7da842fff9497806adb17fd2194522173724e26cc5f14e` | `SC50.4` |
| `firmware/b5.7/circuittracks-4486-B5.7.syx` (**Beta 5.7**) | `5cb71481214e3fe4d775ce8ea83a17869e1c1a2d749087e75492e1e710bf677b` | `B5.7` |
| `firmware/r406/circuittracks-4486-R406.syx` (**RC4.06**) | `df43b135d4a562eadde7050b1adac7eb4b000560cf94df97888ad75c70f04e8f` | `R406` |
| `firmware/r406s/circuittracks-4486-R406S.syx` (**RC4.06S**) | `dcbf6903592f2a9a36e58a69ce551424637924203ea9f8f2980352a85c59a548` | `R406S` |

## Qué probar (todas salvo lo marcado)
Pantalla de acordes: Note ampliada de una pista de notas, Shift + pad 8. Arpegiador encendido: Pattern Settings, Shift + pad 25.

1. **Mute:** Play, silencia la pista en el Mixer y mantén un acorde: el arpegio suena completo y a tiempo; la secuencia de esa pista sigue callada.
2. **Dos acordes con notas comunes** (Do y Mi menor, por ejemplo), con el arpegiador: suelta uno; el arpegio conserva todas las notas del otro. Sin arpegiador: ninguna nota se queda colgada al soltar los dos.
3. **Más de 6 notas:** dos acordes de 4 notas sin notas comunes: las que no caben no entran y no vuelven al soltar el otro. Es el límite del arpegio.
4. **Cuenta atrás como esclavo** de un reloj MIDI a otro tempo: los clics van al tempo del reloj.
5. **Rollers parados** (vista Note de un drum) **y arpegio de drums parado:** siguen el tempo del proyecto, por ejemplo a 80 BPM.
6. **Solo Beta 5.7, pad 16:** Do mayor suena Fa, La♭, Do; verde encendido; cambia al momento con un acorde mantenido; suelta y para. Shift + fundamental sigue fijando el acorde.
7. **Solo Beta 5.7, destello:** volumen del clic a 0 (Tempo / Swing, K5): Clear destella en naranja en cada clic de la cuenta atrás y del metrónomo; con el clic por encima de 0, o con Shift, no.

## Sin reproducir
- **LED de la octava inferior:** en emulación cada nota enciende su pad, en todas las escalas. Un acorde de la fila de abajo que llega a la de arriba la enciende con razón. Falta el caso exacto.
- **Sidechain:** en emulación los knobs cambian con cada preset, en las cuatro páginas. Falta el caso exacto.
