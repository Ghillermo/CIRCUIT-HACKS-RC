# SC41.1 / Beta 1.1 — Master FX ya no pisa la memoria de otros módulos; opción random del secuenciador de efectos

`circuittracks-4486-SC41.1.syx` — SHA-256 `8037cba2ad720e42e1f1535e4ab306dabbb3bb3f2bf8fd24dfa1de1f8cd93ac4`, marca `SC41.1`.
`firmware/b1.1/circuittracks-4486-B1.1.syx` — SHA-256 `f9c8e2ea32c048fa2d6cae1354d01eb5cc7b5f920132f04adf25e91198ac48f2`: el mismo código con la marca `B1.1` (**Beta 1.1**; antes de publicarse era SC41 y no llegó a probarse así).

Es SC41 (los knobs del step-drummer, `firmware/sc41/PRUEBA.md`) con:

1. **Arreglo: la vista Master FX dejaba de pisar el estado de otras funciones.** Con la vista en pantalla, sus LEDs se dibujan en cada fotograma en un búfer de 84 B que varias funciones usaban como memoria «ociosa»: la marca de las cadenas de patrones (su estado en marcha y el orden fractal se reiniciaban una y otra vez), los contadores de la frecuencia por paso, el estado de los knobs del Sidechain, de los patches propios, del guardado de patches, de la copia de proyectos, del editor de macros y la fuente del granular. Lo que se pisaba dependía de lo que estuviera encendido (por eso pasaba «con muchas cosas sonando» y afectaba a Synth 2). El búfer va ahora en la cola del proyecto cargado.
2. **Secuenciador de efectos: valor «random».** Un séptimo valor del knob selector (el LED en **blanco**) = en cada paso con nota se elige al azar uno de la lista: los huecos de la fila inferior con efecto asignado y el gesto mecánico del pad 31; la elección dura todo el paso y cambia en cada vuelta.

## Qué probar
1. El caso de antes: muchas pistas sonando (Synth 1, Synth 2, el sinte propio, drums), entra en Master FX y quédate un rato: Synth 2 (y todo lo demás) sigue sonando. Lo mismo con cadenas de patrones y una pista en orden fractal: siguen su recorrido.
2. Asigna efectos a dos o tres huecos de la fila inferior de Master FX. En el secuenciador de efectos de MIDI 1 gira un knob hasta el final (blanco): en cada paso suena uno de esos efectos al azar.
3. Los knobs de pitch del step-drummer (SC41).

## Verificación en emulación
`emu_sc41_1.py`: la vista Master FX dibujada varias veces: los 84 B de antes y el estado en marcha de las cadenas intactos, los LEDs en la cola (SC41: pisados); el valor 7: bit 6 y una semilla que se mantiene dentro del paso y cambia entre pasos; `c_fsqfx` da siempre el efecto de uno de los dos huecos asignados y salen los dos; LED blanco; en SC41 el valor 7 no existe. `emu_sc41.py` sobre SC41.1.
