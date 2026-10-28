# Hoja de ruta

*[English version](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Roadmap) · [Inicio](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home#en-español) · [Preguntas frecuentes](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/FAQ-ES) · [Cambios](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/blob/main/docs/CHANGELOG.md) · [Discussions](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/discussions)*

Actualizada el 2026-10-28. Versiones actuales: **RC2.11 / RC2.11S** y **Beta 3.41 / 3.41S**.

El mod ha crecido deprisa. La etapa siguiente va de **calidad más que de cantidad**: que lo que ya existe suene mejor, sea más fácil de usar, sea sólido y esté bien documentado. Las funciones nuevas grandes esperan hasta entonces.

## En marcha

- **Parejas estéreo de drums** (Betas 3.36 / 3.37, por probar en el aparato): mantén Drum 1 y pulsa Drum 2 (o Drum 3 + Drum 4). Drum 1 / 3 toca su sample a la izquierda y Drum 2 / 4 el sample siguiente a la derecha, los dos con los controles y el patrón de Drum 1 / 3. Los knobs de Drum 2 / 4 ajustan la apertura estéreo, la desafinación y pequeñas desviaciones. Se guarda con el proyecto; el mismo gesto vuelve a dos drums separados.

## Ahora

### 1. Mejorar las funciones de sonido que ya existen
- **Hacer sitio para las mejoras.** Al motor de sonido le queda poco espacio, así que lo primero es ordenar lo que hay para dejar sitio a las mejoras de abajo.
- **Filtro más suave con envolventes rápidas.** Los barridos rápidos del filtro del sinte de MIDI 1 / 2 pueden dejar un leve zumbido escalonado: que sean suaves.
- **Wavefold más brillante y limpio en los agudos.** Desde la Beta 3.35 el pliegue se suaviza en las notas agudas para evitar tonos ásperos; otro método conservaría el brillo sin ellos.
- **Conocer los límites reales.** Probar en el aparato las combinaciones más pesadas (dos pistas polifónicas con supersaw, todos los drums, Master FX) y fijar con eso el número de voces.
- **Revisar de oído cada motor:** niveles entre motores, clics al cambiar de nota, rangos de las envolventes, los modos granular y muestra, Master FX.

### 2. Mejorar la interfaz
- **Las mismas reglas en todas partes:** con Shift, lo disponible en amarillo y la opción elegida en otro color; Clear + knob = valor por defecto (lavanda) o borrar la automatización (rojo); Duplicate + A + B = intercambiar o copiar; todo modo propio con un indicador visible. Revisar cada vista con estas reglas.
- **Ordenar las vistas más cargadas,** primero la vista Preset de MIDI 1 / 2, donde la mayoría de los pads 25-32 son interruptores sueltos (ver las ideas de abajo).
- **Enseñar los valores ocultos,** como el número exacto de un knob, el modo elegido o si hay cambios sin guardar (ver las ideas de abajo).

### 3. Arreglar y mantener
- **Pruebas en el aparato** de todo lo marcado «sin probar» en los cambios, y pasar lo probado de la beta a la siguiente RC.
- **Todo arreglo va a la RC y a la beta,** y cada RC mantiene su gemela más segura «S».
- **La estabilidad primero:** ninguna función nueva puede volver inestable el tempo ni dar chasquidos.
- **Issues y preguntas frecuentes:** responder a los informes y añadir a las [preguntas frecuentes](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/FAQ-ES) lo que se repita.

### 4. Un manual de verdad
- **Un solo manual** en español e inglés: primeros pasos (instalar, empezar), después vista por vista, después datos y guardado, MIDI y problemas frecuentes. Hoy está repartido entre la [guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html), la [lista de características](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html), la [guía en palabras sencillas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/sencilla.html) y la [referencia MIDI](https://ghillermo.github.io/CIRCUIT-HACKS-RC/midi.html).
- **Un dibujo de cada vista:** qué hace cada pad, knob y color.
- **Marcas de versión más sencillas** (solo «desde RC…» y «solo beta»).
- **Un PDF para imprimir,** hecho de la misma fuente que las páginas web.
- **Esta wiki:** las secciones ([Vistas](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Views-ES), [Datos](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Data-ES), [Funciones](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Features-ES), [DSP](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/DSP-ES), [Usabilidad](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Usability-ES), [MIDI](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/MIDI-ES)), las preguntas frecuentes y los problemas frecuentes, al día con el manual.

## Ideas abiertas

Nada de esto está decidido: los comentarios son bienvenidos en [Discussions](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/discussions).

### Control y usabilidad
- **Transponer el patrón por MIDI:** las notas que llegan por el canal de una pista de sinte transponen el patrón que suena (transposición desde un teclado, como la entrada de un arpegiador), en vez de tocar el sinte.
- **Lectura del valor:** mientras gira un knob, su valor exacto como número en los pads (el mod ya enseña números así en algunos sitios), como opción.
- **Deshacer la última edición destructiva** (cuantizar, Nudge, Clear de un patrón, la foto de Record + paso): un nivel.
- **«Cambios sin guardar» en el LED de Save,** para saber cuándo hace falta Save dos veces.
- **Recogida suave** (opción): tras cargar un proyecto o un patch, un knob no cambia nada hasta pasar por el valor guardado, para que nada salte.
- **Copiar el sinte propio entre MIDI 1 y MIDI 2** (Duplicate + botón de pista).
- **Cargar un patch del sinte propio con Program Change** por el canal de la pista.
- **Una vista Preset de MIDI 1 / 2 más clara:** los pads 25-32 agrupados por función, de modo que el mismo sitio haga siempre el mismo tipo de cosa: sonido (motor, modo de voz), editores (CC, matriz) y directo (patch flip, step-drummer).
- **MIDI para lo que aún no lo tiene:** la matriz de modulación, el FM, el modo de voz y los destinos de la página 4 por NRPN, para controlarlos desde un DAW.
- **Instantáneas por escena** de los knobs de Master FX, que vuelvan con la escena.

### Reordenar los datos guardados
- **Un solo sitio para el sinte de MIDI 1 / 2:** el proyecto. Hoy sus valores están en los ajustes del aparato (los mismos para todos los proyectos) y, en la beta, también en el proyecto; los ajustes del aparato solo darían el sonido inicial de un proyecto nuevo.
- **Ajustes del patrón que viajen con el patrón:** el arpegiador (encendido, orden, resolución) se guarda en el proyecto por número de patrón, así que duplicar un patrón no lo copia. Podría ir dentro del propio patrón.
- **Guardar con el proyecto el filtro master y su resonancia** (el original no lo hace).
- **Una forma más ordenada de guardar los datos del mod en los proyectos,** con sitio para funciones nuevas y los proyectos antiguos convertidos solos al cargarlos.
- **Todos los ajustes del aparato propios del mod en un solo sitio,** fáciles de reiniciar.
- **Copias de seguridad por USB:** exportar / importar los patches del sinte propio y los ajustes del mod desde el ordenador, no solo sacando la tarjeta.

## Descartado
- Beat repeat, reverser, el efecto vinilo y el crackle lo-fi.
- El Circuit Rhythm: ver el proyecto aparte [Circuit Remix](https://github.com/Ghillermo/CIRCUIT-REMIX).

## Cómo participar
- **Ideas y votos:** [Discussions](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/discussions).
- **Fallos:** un [issue](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues) con la versión, los pasos y, si se puede, el proyecto o una grabación.
- **Pruebas:** instala la beta y cuenta qué funciona y qué no.
