# Beta 5.44 = Beta 5.43 (= SC55.8) + ocho pasos de Amount y el final de escena con listas mutadas

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.44/circuittracks-4486-B5.44.syx` | `499f8e322898146bc5e0c706d82e3a9e7ca22d9a70f97d0ff7c7c9c622433766` | `B5.44` |

**Lo nuevo** (el usuario, 2026-11-10: «make 8 amounts and mutated patterns end the scene, like Remix just did», el RH88 de Remix),
sobre el mutate de patrones de la 5.43 (`tools/patmut.py`, `patmut.use_v2()`):
- **Amount en ocho pasos** en la página de ajustes (Shift + Duplicate mantenido en Patterns): **columnas 4 y 5** = todo, 7/8, 6/8 … 1/8 de
  los huecos de la cadena cambian (columna 4 de arriba abajo los cuatro primeros, columna 5 los otros cuatro); **Repeats pasa a la columna 6,
  Keep slot 1 a la 7**; la 8 apagada.
- **Una lista mutada termina la escena:** para una pista que muta, el final de su cadena es **el último hueco de su lista** (antes valía la
  regla del stock, pasar por el último patrón de la cadena, que podía caer a mitad de la lista o no llegar nunca). Con escenas encadenadas, la
  escena cambia cuando la lista termina entera; las pistas sin lista siguen la regla del stock (y las de `patchain`, la suya).
- Los ajustes guardados con la 5.43 cambian de forma (el Amount ocupa un bit más): un proyecto guardado con la 5.43 puede abrir con otro
  Amount / Repeats. La 5.43 no se publicó.

## Qué probar
1. Página de ajustes: toca los ocho pads de Amount (columnas 4-5); el elegido brillante, el resto tenue; con poco Amount la lista se parece a
   la cadena, con todo es al azar. Repeats (columna 6) y Keep slot 1 (columna 7) como antes.
2. **Escenas:** dos escenas encadenadas (escena 1 con cadenas de 4 patrones, escena 2 con otras). En la 1, Length 6 exacta (columna 2, fila 2;
   tipo: columna 3, fila 2), muta y guarda la escena 1. ¿Pasa a la 2 justo al acabar los 6 de la lista, ni antes ni nunca?
3. Una lista sin el último patrón de la cadena (Length 3, varias semillas): ¿la escena cambia igual al acabar la lista?
4. Clear + Duplicate y vuelve a encadenar: cambia como en el stock.
5. Todo lo de la 5.43 sigue igual (`firmware/b5.43/PRUEBA.md`).

## Verificación en emulación
- `emu_patmut.py` contra SC55.7: además de lo de la 5.43, los ocho pasos de Amount (valor y LED), Repeats / Keep slot 1 en sus columnas, la
  lista con Amount 1/8 = el modelo, y **el `bl` de `0x0802C65E` (`c_pmend`) como lo usa el stock**: una lista de 6 que pasa por el último
  patrón de la cadena a mitad termina solo en su 6.º hueco; una pista sin lista, la regla del stock. SC55.8 y Beta 5.43 siguen pasando.
- `verify_builds.py`: SC55.8 / Beta 5.43 sin cambios.
