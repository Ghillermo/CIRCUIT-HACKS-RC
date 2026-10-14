# SC40.5 — cadenas de patrones

`circuittracks-4486-SC40.5.syx` — SHA-256 `50b5ca80aae3ea2a1d6536241a5da2a99f43336b5d3f7a2709c0f1045a43d759`
Imagen de 0x69738 bytes, CRC 0x110016e5, marca `SC40.5`.

Es SC40.4 más las cadenas de patrones. Cada patrón de cada pista (las ocho, drums incluidos) puede llevar una regla: **«suena n veces, luego salta a B; la vez siguiente, a C»**. B y C suenan una vez y la pista vuelve al patrón que la mandó.

| Forma | Regla en A |
|---|---|
| AAAB AAAC | n = 3, B, C |
| AAAAAAAAB | n = 8, B, sin C |
| ABAC | n = 1, B, C |

## Cómo se programa (vista Patterns)
1. **Shift + Octave ▲** entra en la edición de cadenas (Octave ▲ se queda blanco). **Shift + Octave ▼**, o cualquier botón de vista, sale.
2. Pulsa un patrón: es **A** (amarillo). Se selecciona como siempre y su pista pasa a seguir las reglas.
3. Pulsa **A otra vez** por cada reproducción más (hasta 8). Los LEDs de los knobs cuentan n.
4. Pulsa **otro patrón de la misma pista**: es **B** (verde). El siguiente que pulses es **C** (rojo).
5. **Clear + patrón** (en la edición) quita su regla sin borrar el patrón.
6. Los patrones con regla se ven en blanco (tenue si su pista sigue la cadena del original).

Fuera de la edición todo es como siempre, con dos cambios: una pulsación normal de un patrón devuelve esa pista a la cadena del original (sus reglas se conservan, pero no corren hasta que vuelvas a tocar la pista en la edición), y Clear + patrón borra también su regla.

## Escenas
- Al **guardar una escena** (como siempre) se guarda también, por pista, si sigue las reglas o la cadena del original. Al entrar la escena cada pista toma lo suyo.
- La escena termina cuando terminan todas las pistas; una pista con regla termina al volver del último salto (de C, o de B si no hay C).
- **Repetir una escena:** guárdala varias veces seguidas (menos de 1,5 s entre una y otra): cada guardado extra es una repetición más, hasta 8. Guardarla una sola vez la deja en una.
- Copiar una escena copia también lo nuestro.

## Qué probar
1. Synth 1: A = patrón 1, tres pulsaciones, B = patrón 2, C = patrón 3. Play: 1 1 1 2 1 1 1 3 y vuelta.
2. Un drum con AB sin C y otra pista con una cadena normal del original a la vez: cada una va por su lado.
3. Sal de la edición y pulsa un patrón de Synth 1: la pista vuelve a la cadena del original. Vuelve a la edición y toca A: las reglas corren de nuevo.
4. Guarda, apaga, enciende y carga: las reglas y las pistas que las siguen vuelven.
5. Duplica un patrón con regla: la copia lleva la regla. Bórralo con Clear: la regla desaparece.
6. Dos escenas con cadenas distintas, la primera guardada tres veces seguidas: suena tres veces y pasa a la segunda.
7. Lo de SC40.4 (frecuencia, dinámicas, pad 25) sigue igual.

## Límites
- La regla vive en el patrón: si A manda a B y B tiene su propia regla, manda la de B (la pista no vuelve a A hasta que algo la devuelva).
- Las reglas se cuentan desde que el patrón empieza por una selección o una escena; parar no las borra, cargar un proyecto sí.
- Sin indicación fuera de la edición de qué pistas siguen las reglas.

## Verificación en emulación
- `emu_sc40_5.py`: el avance de pista del original, final de patrón tras final de patrón, contra un modelo (AAAB AAAC, AAAAAAAAB, ABAC, regla dentro de regla, drums, reglas no válidas, cadena del original); la llamada de previsión no cambia nada; reinicio forzado; marca por escena; fin de cadena; repeticiones de escena (solo cuenta la llamada que confirma); guardado de escena con el gesto del original; la vista Patterns por el controlador (edición, bytes escritos, LEDs, Clear, salida); carga de proyecto.
- **Sin comprobar en emulación:** el secuenciador en marcha con el reloj real y el cambio de escena completo (cada pieza se prueba por separado).
