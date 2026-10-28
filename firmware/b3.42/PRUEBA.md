# SC48.5 / Beta 3.42 = SC48.4 / Beta 3.41 + MIDI otra vez = Preset, limitador de voces, poly por defecto

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc48.5/circuittracks-4486-SC48.5.syx` | `a61642b129a346c8eb275b49d0ba87e73a747e276278ce5dcad1716bb06076be` | `SC48.5` |
| `firmware/b3.42/circuittracks-4486-B3.42.syx` (**Beta 3.42**) | `d44a5fe4e38bd01361d515231c588bfc13e250aa69a3322ec831531dd7790105` | `B3.42` |

El usuario (2026-10-28): «midi second press is not working. it activates on a short double tap, but i want the view to open if the midi note
view is opened and we tap midi once again»; con S484D en el aparato: «save goes white when crackling», «up until red the sound was OK», «red is
pretty much ok, so push towards the red-white limit», «the clear button only ever reaches green, so you can relax the volume limiter»; «also
polyphony shold be default mode».

**Lo que dijo S484D:** el traqueteo es el DSP quedándose sin tiempo (el anillo de salida se vacía: Save blanco), no el recorte de la suma de las
voces (el medidor del pico nunca pasó de verde). Rojo = un bloque tardó más de lo que dura, pero aún suena limpio.

## Qué probar
1. **MIDI otra vez = Preset:** MIDI 1 (su vista Note). Espera un par de segundos y pulsa **MIDI 1 otra vez**: su vista Preset (sin prisa: ya no
   hay ventana de tiempo). Desde Velocity / Gate / la Note ampliada, MIDI 1 lleva a la Note (lo de stock) y otra vez a Preset. Desde Mixer o FX,
   MIDI 1 = su Note, no Preset. Igual con MIDI 2. Shift + MIDI = Preset como antes.
2. **Limitador de voces:** MIDI 1 con FM poly y un patch de release largo (los que traqueteaban). Toca notas sueltas una tras otra, muchas, y
   acordes de 6 mantenidos: **no debería traquetear**. Cuando el DSP va a quedarse sin tiempo se apaga la voz que ya suelta y suena más bajo
   (casi no se nota); si no hay ninguna soltándose, la nota mantenida más antigua se corta (como un robo de voz). Después el limitador se queda
   con las voces que caben (una nota nueva apaga antes la que se suelta más baja) y cada 2 s sin problemas prueba con una más. **En unísono**
   igual: el unísono toca como mucho las voces que caben.
3. **Volumen de los acordes:** un acorde de 2 notas suena ahora a nivel completo cada nota; de 6, cada una a 0,58 (antes 0,41): los acordes
   suenan más fuertes. **El unísono** con la misma regla (2 voces a nivel completo, 4 a 0,71, 6 a 0,58; antes 2 a ¾ y más a ½). Si llega a
   recortar, dímelo.
4. **Poly por defecto:** un proyecto nuevo (o uno en el que nunca elegiste modo de voz): MIDI 1 / 2 en **poly** (pad 32 de su Preset: magenta).
   Un modo que elegiste y guardaste se queda; un patch con su modo lo trae.

Para ver el DSP mientras pruebas: **S485D** (`firmware/s485d/`) = esto + los medidores de S484D (Save no debería ponerse blanco).

## Verificación en emulación
- `emu_midipre.py`: MIDI 1 una vez = Note (19), otra vez 2 s después = Preset (18); Preset → MIDI 1 = Note; Velocity → MIDI 1 = Note, otra vez =
  Preset; Note ampliada (24) y Mixer (69) → MIDI 1 = Note; MIDI 2 dos veces = su Preset (27); Synth 1 dos veces no es nuestro; pad 27 gris con el
  motor apagado.
- `emu_vguard.py`: proyecto sin modo = poly en las dos pistas; oscilador poly 1-4 notas × 256 / 256 / 209 / 181, FM seis notas × 148; sin voces
  no se lee el margen; seis mantenidas con margen 200 = nada; tres soltadas (envolventes puestas por la prueba), margen 50 = la más baja fuera,
  2 ms después nada, margen 20 a los 4 ms = la siguiente, 12 ms después la última soltada, 12 ms después (ninguna soltada) la mantenida más
  antigua, anillo vacío a los 4 ms = la siguiente más antigua; margen 200 durante 40 ms = nada más; los objetivos del DSP de las liberadas a 0,
  la que queda a nivel completo; el tope = las voces que quedan (2 como mínimo): con una voz, una nota = la segunda; otra nota = la mantenida
  más antigua fuera antes; 2 s sin liberar = tope 3, 2 s más = 4; unísono FM con tope 3 = tres voces × 209 (√(2 / 3)); margen 50 = una fuera,
  tope 2; la siguiente nota del unísono, dos voces a nivel completo.
- Las pruebas de SC48.4 sobre SC48.5: ver la lista de la sesión. `emu_polygain.py` (1 / √n) no vale sobre SC48.5.
