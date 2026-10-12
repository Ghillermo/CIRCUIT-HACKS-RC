# SC34.2 — SC34.1 + modo frase del song pointer

`circuittracks-4486-SC34.2.syx` — SHA-256 `bb86322df4bbf5019b64bd7859ac89df81d0cd7fe11d075f65f4fe12ca437c6d`
Imagen de 0x621e0 bytes, CRC 0xd7d8a1f3, marca `SC34.2`. Probado en emulación; **nada probado en el aparato**. Todo lo de SC34.1 sigue igual: búfer del sample fuera de la memoria de samples y loop solo mientras se mantiene el pad.

## Qué cambia: el modo frase (Master FX, pads 9-24 = pasos 1-16)
- **Shift + un paso** entra en el **modo frase** con ese paso como **inicio**. El final queda en el paso 16 hasta que toques otro. El pad 9 se pone **blanco**.
- **En el modo frase:**
  - **Tocar un paso** lo pone como **final** de la frase.
  - Si tocas un paso **anterior al inicio**, ese paso pasa a ser el inicio y el inicio anterior, el final.
  - **No hay retrigger** ni frase momentánea: mantener un paso solo fija el final.
  - **Shift + otro paso** mueve el **inicio** a ese paso. Si el final quedaba antes del nuevo inicio, vuelve al paso 16.
- **Salir del modo frase:** **pad 9 (blanco)** o **Shift + el paso de inicio**. El pad 8 también la borra, como antes.
- **Fuera del modo frase** todo es como en SC32: un paso mantenido hace retrigger y dos pasos mantenidos hacen una frase momentánea.

Dos cosas que he decidido yo:
- al entrar en el modo, el final es el paso 16;
- el paso 1 no puede ser el final de una frase, porque su pad sale del modo.

Si prefieres otra cosa, dímelo.

## Pruebas en el aparato
1. Envía SC34.2. Pon en marcha un patrón y abre Master FX.
2. Shift + paso 5: la reproducción va del paso 5 al 16 en bucle y el pad 9 se pone blanco.
3. Toca el paso 12: el bucle pasa a ser 5-12. Mantén un paso dentro del bucle: no hay retrigger, solo cambia el final.
4. Shift + paso 8: el bucle pasa a ser 8-12.
5. Pulsa el pad 9 (o Shift + paso 8): sales del modo frase. Un paso mantenido vuelve a hacer retrigger.
6. Repite las pruebas de SC34.1 (sample capturado) si no las has hecho.

## Verificación en emulación
`emu_sc34_2.py`: todas las pruebas de SC34.1, y además las del modo frase por las rutas reales:
- entrar en el modo y fijar el final;
- tocar un paso antes del inicio;
- mover el inicio;
- el bucle en el tick del secuenciador;
- salir con Shift + el inicio, con el pad 9 y con el pad 8;
- fuera del modo, el retrigger y la frase momentánea de SC32.

Además, `verify_builds.py` da ALL IDENTICAL.

## Volver atrás
Envía SC34.1.
