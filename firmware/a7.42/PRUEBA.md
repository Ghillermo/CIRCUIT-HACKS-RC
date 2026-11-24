# Alpha 7.42 — qué probar

Instalar `circuittracks-4486-A7.42.syx` (modo bootloader: Scales + Preset + Note al encender). Es la Alpha 7.41 + **carriles de automatización para los 8 knobs de Macros 2** de Synth 1 / 2 (como los de los macros: 2 valores por paso, al principio y a mitad de paso).

Antes: en la vista alternativa de Synth 1, asigna dos o tres parámetros a Macros 2 (Duplicate + knob en una página de sección; Shift + pad 1 = Macros 2 en los knobs).

1. **Grabar:** Record + Play, gira un knob de Macros 2 mientras suena: en la vuelta siguiente el parámetro se mueve solo como lo grabaste (dos valores por paso).
2. **Mientras grabas** el knob que estás girando no se pelea con lo grabado.
3. **Paso mantenido** (vista Note de Synth 1, mantén uno o dos pasos) + knob de Macros 2: ese valor en esos pasos (en la página 17-32 también). Parado: el sonido cambia al girar, y al darle a Play esos pasos tienen el valor.
4. **Clear + knob de Macros 2 a la izquierda** = su automatización borrada en el patrón que editas; **a la derecha** = el parámetro vuelve al valor del patch.
5. **Guarda el proyecto, carga otro y vuelve:** la automatización de Macros 2 vuelve. Apaga y enciende: también. Un proyecto nuevo empieza sin ella.
6. **Duplicar un patrón** de Synth 1 (Duplicate en la vista Patterns) lleva su automatización de Macros 2; **borrar el patrón** la borra; **Nudge** (Pattern Settings, pad 26) la mueve con los pasos.
7. Lo mismo en **Synth 2**.
8. Escucha si al reproducir muchos carriles a la vez hay chasquidos o el tempo se arrastra.

## A tener en cuenta

- Si cambias qué parámetro tiene un knob de Macros 2, su automatización sigue siendo la del knob (mueve el parámetro nuevo).
- Una escritura de Components de ese proyecto pierde los carriles de Macros 2 (como las cadenas de escenas).
- Con el arranque Easy Start (el aparato como unidad USB) los carriles quedan apagados hasta apagar y encender.

## Si algo falla

Dime qué y cuándo. Si Save parpadea en violeta, no apagues: es la caja negra; se lee desde la app (vista Hacks → Caja negra…).
