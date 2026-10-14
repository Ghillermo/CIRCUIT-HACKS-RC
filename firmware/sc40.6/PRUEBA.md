# SC40.6 — cadenas de patrones, interfaz revisada

`circuittracks-4486-SC40.6.syx` — SHA-256 `e504b600f6f7834b60cb0177f1c62fbeecc9aeb9618bb9dafeea3238df66a55a`
Imagen de 0x698a4 bytes, CRC 0xa131056e, marca `SC40.6`.

Es SC40.5 con la interfaz de las cadenas corregida. **Sustituye a SC40.5.** La regla por patrón no cambia: «suena n veces, salta a B; la vez siguiente, a C» (AAAB AAAC, AAAAAAAAB, ABAC). Al terminar C (o B si no hay C) la pista da por terminada su cadena: si hay escenas, cuando todas las pistas han terminado se pasa a la escena siguiente; si no, la cadena empieza de nuevo.

## Lo nuevo respecto a SC40.5
- **Shift enseña lo que ofrece:** con Shift pulsado en la vista Patterns, el botón Octave que hace algo se pone **amarillo** (▲ fuera de la edición, ▼ dentro).
- **Indicador de modo:** en la edición de cadenas Octave ▲ está **verde**.
- **Vista Mixer (escenas):** una escena guardada con alguna pista en cadena se ve en **melocotón** (la actual, más brillante). Los pads de las pistas que están corriendo una cadena **parpadean**.
- **Repeticiones de escena: Shift + pads 9-16** = 1 a 8 repeticiones de la escena actual. Con Shift pulsado la segunda fila se pone amarilla y el número elegido verde. (Guardar la escena varias veces ya no cambia las repeticiones.)
- Mientras una escena se repite no se vuelve a aplicar: los mutes se quedan como los dejes y cada pista sigue por donde iba; solo la primera entrada de la escena reinicia las pistas.

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
- **Repetir una escena:** Shift + pads 9-16 en la vista Mixer (1 a 8 veces), para la escena que está sonando.
- Copiar una escena copia también lo nuestro.

## Qué probar
1. Synth 1: A = patrón 1, tres pulsaciones, B = patrón 2, C = patrón 3. Play: 1 1 1 2 1 1 1 3 y vuelta.
2. Un drum con AB sin C y otra pista con una cadena normal del original a la vez: cada una va por su lado.
3. Sal de la edición y pulsa un patrón de Synth 1: la pista vuelve a la cadena del original. Vuelve a la edición y toca A: las reglas corren de nuevo.
4. Guarda, apaga, enciende y carga: las reglas y las pistas que las siguen vuelven.
5. Duplica un patrón con regla: la copia lleva la regla. Bórralo con Clear: la regla desaparece.
6. Dos escenas con cadenas distintas; con la primera sonando, Shift + pad 11 (3 repeticiones): suena tres veces y pasa a la segunda. Durante las repeticiones cambia un mute: se queda.
8. Shift en Patterns: Octave ▲ amarillo; en la edición, ▲ verde y con Shift ▼ amarillo.
9. Mixer: la escena con cadenas en melocotón, los pads de sus pistas en cadena parpadean mientras suenan.
7. Lo de SC40.4 (frecuencia, dinámicas, pad 25) sigue igual.

## Límites
- La regla vive en el patrón: si A manda a B y B tiene su propia regla, manda la de B (la pista no vuelve a A hasta que algo la devuelva).
- Las reglas se cuentan desde que el patrón empieza por una selección o una escena; parar no las borra, cargar un proyecto sí.
- Sin indicación fuera de la edición de qué pistas siguen las reglas.

## Verificación en emulación
- `emu_sc40_5.py` sobre SC40.6: todo lo de SC40.5 más los LEDs de Octave con y sin Shift, Shift + pads 9-16 (valor, fila amarilla / verde, solo con Shift, no en la página de Master FX), el color de las escenas con cadenas, el parpadeo de las pistas (encendido / apagado por el reloj) y que guardar otra vez no cambia las repeticiones.
- **Sin comprobar en emulación:** el secuenciador en marcha con el reloj real y el cambio de escena completo.
