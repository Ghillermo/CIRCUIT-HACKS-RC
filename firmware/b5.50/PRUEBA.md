# Beta 5.50 = SC56.5 con la marca de la beta: morph lento, LFO cuadrado con slew y colores de K1 / K5

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.50/circuittracks-4486-B5.50.syx` | `56c108dd0bc8b9d9f142c5d0c23fb16f6c32160489c77f275358621cfd22e442` | `B5.50` |

**Lo nuevo** (el usuario, 2026-11-11), `morphz.use_slow()`, en la vista del morph:
- **K1** posición (en color: patch 1 rojo, 2 amarillo, 3 verde, 4 azul, con tonos intermedios); **K2** cantidad del LFO cuadrado; **K3** velocidad
  de los dos LFO; **K4** cantidad del LFO al azar (un valor nuevo en cada medio ciclo); **K5** destino del morph lento (en color); **K6** su
  duración (izquierda del todo = al momento; luego de ¼ a 32 compases); **K7 / K8** envolvente; **K8 suaviza también los LFO**.
- **Morph lento:** girar K5 y dejarlo quieto medio segundo: el sonido va de K1 a K5 en el tiempo de K6; al llegar, K1 = K5. Girar K5 otra vez
  cambia el destino desde donde está; girar K1 lo para ahí.
- El azar en cada paso de la pista desaparece.

## Qué probar
1. Entrar en el morph con 3 o 4 patches: K1 cambia de color al girarlo (rojo → amarillo → verde → azul); K5 igual.
2. K6 a la izquierda del todo, K5 a otro patch y soltar: medio segundo después el sonido salta ahí y K1 se pone en el color de K5.
3. K6 a la mitad (≈ 3 compases), K5 a otro patch: el sonido va despacio; K1 cambia de color mientras va; al llegar, K1 = K5.
4. Con la rampa en marcha: girar K5 otra vez (cambia de destino sin saltos); girar K1 (se para donde está).
5. K2 a la derecha, K3 a la mitad: el sonido salta entre dos sitios (cuadrado); K8 a la derecha: los saltos se suavizan.
6. K4 a la derecha: un valor al azar en cada medio ciclo, también suavizado por K8.
7. Con y sin Play, y con otro tempo: la duración de K6 sigue el tempo del proyecto.

## Verificación en emulación
- `emu_morph.py --clear --sus --nocur --four --slow`: los colores de K1 / K5, K6 = al momento, la rampa de ¼ de compás (monótona, K1 = K5 al
  final), K1 durante la rampa, K6 al final (lenta), re-apuntar a mitad, el cuadrado con sus dos topes y el slew de K8, el destino al azar; el resto
  de la prueba como en SC56.4.
