# Hoja de ruta

*[English version](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Roadmap) · [Inicio](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home#en-español) · [Preguntas frecuentes](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/FAQ-ES) · [Cambios](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/blob/main/docs/CHANGELOG.md) · [Discussions](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/discussions)*

Actualizada el 2026-11-09. Versiones actuales: **RC4.11 / RC4.11S** (arreglos) y la **Beta 5.41** (funciones nuevas; las betas que amplían RC4 se numeran 5.x).

El mod ha crecido deprisa. La etapa siguiente va de **calidad más que de cantidad**: que lo que ya existe suene mejor, sea más fácil de usar, sea sólido y esté bien documentado. Las funciones nuevas grandes esperan hasta entonces.

## En marcha

- **Morph de patches** (Beta 5.38; probado en el aparato en la Beta 5.39): mantén dos o más patches en la vista Preset de Synth 1 / 2 o de MIDI 1 / 2 y K1 pasa de uno al siguiente, con LFO, azar y una envolvente en K2-K8.
- **Patches en el color de su categoría** (Beta 5.38; Bass en azul acero desde la Beta 5.40): la vista Preset de Synth 1 / 2 enseña cada patch en el color de su categoría de Components, y K1 elige la categoría al guardar.
- **FM de 8 operadores** (Beta 5.20, probado en el aparato; listas e instrumentos desde la Beta 5.21): envolventes al estilo DX7, 56 algoritmos, 48 instrumentos en dos páginas (la segunda, con pianos, cuerdas, vientos y sonidos largos, desde la Beta 5.33), patches del DX7 importados con la app de la tarjeta.
- **Funciones propias del modo de un oscilador** (Beta 5.32, por probar en el aparato): sub-oscilador y ruido, con su envolvente y su LFO.
- **Vista de flip** (Beta 5.32, por probar en el aparato): el pad 26 abre una vista para elegir patch flip (PGM seq) o step flip y su destino.
- **Motor wavetable** (Betas 5.24-5.28, por probar en el aparato): las 16 wavetables de stock, o una tabla propia de hasta 9 cuadros hecha con ellas y con los samples del pack, con la posición en K3.
- **Los dos osciladores reordenados y más limpios** (Beta 5.27, por probar en el aparato): FM con centro (en los dos sentidos, los dos en los extremos), sync clásico, LFO / envolvente → FM, ring y mix, menos ruido en FM, sync y bitwise.
- **Interfaz nueva del random-mutate** (Beta 5.4; dinámicas rehechas en la Beta 5.12): una botonera por paso para la nota, la octava, las dinámicas (ghost, accent staccato, longitud; en los drums más suave con roller o más fuerte) y los micropasos, y un factor en Octave (×0, ×1, ×2, ×4, ×8) para toda la pista, en notas y drums.
- **Solo y solo flip en el Mixer** (Beta 5.12, por probar en el aparato): pad 16 + pistas = un solo que se queda hasta un toque al pad 16; un toque sin solo = flip, donde las pistas que mantienes suenan solas hasta que las sueltas.
- **Vista de automatización de los drums** (Beta 5.0, por probar en el aparato): la vista Velocity con Shift de un drum funciona como en las pistas de sinte: los pasos con automatización en amarillo, Shift + un paso amarillo = escuchar sus valores, Shift + otro paso = una marca donde los knobs del drum vuelven a los valores del proyecto, Clear + paso = borrar su automatización; además el carril extra de automatización de los drums, los bloqueos de estado y las rampas.
- **Parejas estéreo de drums** (Betas 3.36 / 3.37, por probar en el aparato): mantén Drum 1 y pulsa Drum 2 (o Drum 3 + Drum 4). Drum 1 / 3 toca su sample a la izquierda y Drum 2 / 4 el sample siguiente a la derecha, los dos con los controles y el patrón de Drum 1 / 3. Los knobs de Drum 2 / 4 ajustan la apertura estéreo, la desafinación y pequeñas desviaciones. Se guarda con el proyecto; el mismo gesto vuelve a dos drums separados.

## Ahora

### 1. Mejorar las funciones de sonido que ya existen
- **Hacer sitio para las mejoras.** Desde la Beta 5.11 los programas del motor de sonido van comprimidos, lo que liberó unos 22 KB de memoria del firmware; en la Beta 5.28 ya estaban ocupados (la Beta 5.33 recupera algo comprimiendo los instrumentos FM), así que lo siguiente es desempaquetar al arrancar el código que se usa poco en la memoria interna rápida; al motor de sonido en sí le queda poco espacio, así que lo primero es ordenar lo que hay.
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
- **Patches de demostración:** un juego de patches listos para usar que enseñen lo que hace el mod.

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

### Sonido
- **Importar wavetables externas:** ficheros de wavetable hechos en el ordenador (fotogramas de 2048 muestras, el formato de los sintes de wavetable por software más comunes) cargados en un pack con la app de la tarjeta, para el futuro oscilador de wavetables del sinte de MIDI 1 / 2.

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
