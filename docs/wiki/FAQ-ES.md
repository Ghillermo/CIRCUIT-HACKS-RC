# Preguntas frecuentes

*[English version](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/FAQ) · [Inicio](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home#en-español) · [Hoja de ruta](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Roadmap-ES) · [Guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html) · [Cambios](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/blob/main/docs/CHANGELOG.md)*

Versiones actuales (2026-10-27): **RC2.10**, **RC2.10S** y **Beta 3.37**.

## Instalar

**1. ¿Qué es CIRCUIT-HACKS?**
Un conjunto de parches para el firmware oficial 1.2.1 (build 4486) del **Novation Circuit Tracks**. El instalador toma el firmware oficial que descargas de Novation, lo parchea en el navegador y lo envía al aparato. Añade funciones en todas las vistas: un sinte en las pistas MIDI, controles nuevos de drums, Master FX, arpegiador, escalas y acordes, y más. Ver la [lista de características](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html) y la [guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html).

**2. ¿Es seguro? ¿Puedo volver al firmware original?**
El bootloader de Novation no se toca nunca: siempre se puede enviar otra vez el firmware oficial. Si el aparato no arranca, mantén **Scales + Preset + Note** al encenderlo: es el modo bootloader de Novation, y desde ahí se puede enviar cualquier firmware. **Haz una copia de la tarjeta SD antes de instalar** cualquier versión. Ver [Instalar y volver atrás](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#instalar).

**3. RC, RC «S» o Beta: ¿cuál instalo?**
- **RC** (versión candidata, ahora RC2.10): las funciones probadas en conjunto.
- **RC S** (RC2.10S): lo mismo, pero el mod nunca escribe ficheros propios en la tarjeta SD (sin guardar patches propios, samples ni copias entre packs). La opción más segura.
- **Beta** (ahora Beta 3.37): la RC + las funciones más nuevas. Todo arreglo va a la RC y a la beta; las funciones nuevas, primero a la beta.

**4. ¿Funciona en el Circuit original o en el Circuit Rhythm?**
No: CIRCUIT-HACKS es solo para el **Circuit Tracks** (firmware 1.2.1, build 4486). Para el **Circuit Rhythm** hay un proyecto aparte, [Circuit Remix](https://github.com/Ghillermo/CIRCUIT-REMIX), que lleva estas funciones y añade otras propias.

**5. ¿Cómo se instala?**
1. Descarga [`rc_uploader.zip`](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader.zip), descomprímelo y abre `rc_uploader.html` en **Chrome o Edge** (admiten Web MIDI con SysEx).
2. Descarga el firmware oficial 1.2.1 (build 4486) de [Novation Components](https://components.novationmusic.com/api/v2/firmwares/168/file) y cárgalo en la página.
3. Conecta el Circuit Tracks por USB, elige la versión y envía.

**6. El instalador no encuentra el aparato o rechaza el fichero.**
Usa Chrome o Edge y permite el acceso a MIDI / SysEx cuando lo pida el navegador. Cierra cualquier programa que tenga el puerto MIDI abierto (Components, un DAW). El fichero tiene que ser exactamente el `.syx` oficial 1.2.1 build 4486: el instalador lo comprueba y rechaza cualquier otro.

## Guardar y datos

**7. ¿Qué se guarda y dónde?**
En cinco sitios: el **patrón**, el **proyecto** (los dos, al guardar el proyecto), el **pack** (se escribe al momento en la tarjeta), los **ajustes del aparato** (para todos los proyectos) y ninguno (se pierde al apagar). Las tablas completas están en [Qué vuelve tras reiniciar](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#guardado).

**8. Cambié un sonido y al apagar se perdió.**
- Pulsa **Save dos veces** antes de apagar o de cargar otro proyecto, como en el original.
- Un knob girado sin Record cambia el sonido del proyecto, no el patrón. Para que cambie a lo largo del patrón, grábalo.
- El sinte de MIDI 1 / 2 guarda sus valores en los ajustes del aparato; para conservar un sonido, guárdalo como patch (vista Preset de MIDI, Clear + pad dos veces).
- Para el secuenciador y espera dos segundos antes de apagar, y apaga con el botón de encendido.

Detalles: [Qué guarda un patrón y cómo asegurarte de que se guarda](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#datos-patron) y [Qué se pierde al reiniciar](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#datos-perdido).

**9. ¿Por qué se pone rojo el LED de Save?**
El mod no ha querido escribir en la tarjeta. O el pack es el de la **memoria interna** (sin tarjeta SD: solo lectura para el mod), o usas una versión **S**. Los proyectos se guardan igual, como en el original.

**10. ¿Funciona sin tarjeta SD?**
Sí. Las funciones del mod que guardan cosas propias (patches, samples, copias) no escriben en la memoria interna, así que guarda tu trabajo importante en una tarjeta. Con las versiones que no acaban en «S», no guardes proyectos importantes en la memoria interna.

**11. ¿Los proyectos y packs hechos con el mod funcionan en el firmware original?**
Sí. El mod guarda lo suyo en partes de los ficheros que el original no usa, y el original no las lee.

**12. ¿Puedo seguir usando Novation Components?**
Sí, como siempre. Components no conoce los patches del sinte propio (MIDI 1 / 2), que van dentro de los ficheros de patches del pack; [`tools/patchtool.py`](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/blob/main/tools/patchtool.py) los lista y los copia en el ordenador. Haz una copia de la tarjeta antes de sincronizar packs.

## Sonido y comportamiento

**13. Oigo un zumbido o una realimentación que late.** ([#5](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/5))
En la vista **Setup** (no en Advanced Setup), los **pads 22 / 23** llevan los retornos de reverb / delay por las pistas 3 / 4 del mixer. Con envíos de efecto en esas pistas, la señal vuelve sobre sí misma: es a propósito. Apaga los pads 22 / 23 si no la quieres. Ver [Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#setup).

**14. Los samples de los drums no suenan como en un Circuit original.** ([#7](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/7))
Arreglado desde RC2 (Beta 1.16): los proyectos nuevos o sin tocar suenan como en el original. Si un proyecto antiguo sigue sonando distinto, pon el modo de filtro del drum (**Shift + K5**) en el EQ tilt de stock. Ver [Vista de pista de un drum](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#drum-pista).

**15. El delay tartamudea al mover los knobs del sinte de MIDI.** ([#6](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/6))
Arreglado desde RC2 (los ajustes se escriben en la tarjeta solo con el transporte parado). Actualiza a la RC o la beta actual.

**16. ¿Cómo encuentro los atajos?**
Mantén **Shift**: todo lo que tiene atajo en la vista se ilumina en **amarillo**, y la opción ya elegida en otro color. **Clear + knob** vuelve el knob a su valor por defecto (lavanda) o borra su automatización (rojo). Ver [Botones que funcionan en todas las vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#botones).

**17. ¿Puedo cambiar de patch en cada paso (como un «modo AFX»)?** ([#11](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/11))
Sí, con el **patch flip**. En la vista Setup, pon una pista MIDI en el canal del sinte. Después enciende el pad 26 en su vista Preset: las notas de esa pista pasan a ser Program Change, así que los cambios de patch se secuencian como notas. Ver [Vista Preset de MIDI 1 / 2](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-preset).

**18. ¿Cuántas voces toca el sinte de MIDI 1 / 2?**
Beta 3.35: hasta 4 notas por pista; con FM, 6 voces compartidas entre las dos pistas (3 + 3 si las dos usan FM). El motor granular es de una voz. Las RC todavía no tienen esta polifonía. Las combinaciones más pesadas (dos pistas poly con supersaw, todos los drums y Master FX) aún no se han medido en el aparato: si el audio se ralentiza o da chasquidos, avísanos.

## MIDI

**19. ¿Qué CC y NRPN controlan las funciones nuevas?**
Ver [MIDI: comportamientos propios, CC y NRPN nuevos](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi) y la [referencia MIDI](https://ghillermo.github.io/CIRCUIT-HACKS-RC/midi.html). Los parámetros de stock siguen con los números de la [Programmer's Reference Guide](https://fael-downloads-prod.focusrite.com/customer/prod/downloads/circuit_tracks_programmer_s_reference_guide_v3.pdf) de Novation.

**20. Mi teclado externo no toca el sinte de MIDI 1 / 2 ni el arpegiador.** ([#13](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/13), [#14](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/14))
Desde RC2.08, las notas que llegan por el canal de MIDI 1 / 2 tocan su sinte. Para que pasen por el arpegiador, enciende el **botón Note de la vista Setup** (Beta 3.37; en las Betas 3.35 / 3.36, el pad 22 de Advanced Setup; apagado de fábrica, para que no choque con un teclado que tenga su propio arpegiador). Ver [Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#setup).

**21. ¿Puedo tener la entrada MIDI DIN en el ordenador por USB?** ([#10](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/10))
Sí: **pad 23 de Advanced Setup** (fusión USB, Beta 3.35). Sin el reloj del DIN con Clock Tx encendido, y sin SysEx.

**22. ¿Qué son la matriz de modulación y los destinos de los macros?**
Ver [Matriz de modulación y destinos de los macros](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#destinos): la matriz y los macros de stock de Synth 1 / 2 (con la lista de los 70 destinos de macro) y la matriz propia de MIDI 1 / 2.

## El proyecto

**23. ¿Cómo informo de un fallo?**
Abre un [issue](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues) con la versión (por ejemplo RC2.10 o Beta 3.35), lo que hiciste paso a paso, lo que esperabas y lo que pasó. Si puedes, adjunta el proyecto o el pack, o una grabación corta.

**24. ¿Cómo propongo una función?**
En [Discussions](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/discussions) o con un issue. Mira antes la [hoja de ruta](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Roadmap-ES): las propuestas sobre control, usabilidad y cómo se guardan los datos son especialmente bienvenidas.

**25. ¿Tiene relación con Novation?**
No. Es un proyecto independiente. El firmware que parchea es de Novation y es propietario: el instalador solo instala en un Circuit Tracks.

**26. ¿Cómo puedo apoyar el proyecto?**
[PayPal](https://PayPal.me/ghillermo), informes de fallos con pasos claros y probar las betas.
