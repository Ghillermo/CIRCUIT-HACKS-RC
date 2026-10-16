# SC41.5 = SC41.4 + canales de Program Change (escucha / salida) + Synth 1 / 2 en la vista Setup

`circuittracks-4486-SC41.5.syx` — SHA-256 `fe1e02142c30ac3a7823c5b48f6041bf548530cca3bd85f67e7fe72f4f25c459`, marca `SC41.5`.
`firmware/b1.5/circuittracks-4486-B1.5.syx` — SHA-256 `68f6f9d8d9a98548f1dee87b518a8207e3b934c9db6b1f3fbc5e94fa794ab262`: el mismo código con la marca `B1.5` (**Beta 1.5**).

## Canales de Program Change (solo Beta 1.5)
El usuario: «implementa un canal de escucha y envío a PGM. Cuando se toca el pad de PGM Rx, se ilumina el canal de escucha, y cuando se toca el de Tx, se ilumina el de salida. Por defecto, 16. Además de escuchar / recibir en esos canales, se hace forward de los mensajes entrantes al canal de salida».

En la vista **Setup** (no en Advanced Setup):
- **Pad 29 (PGM Rx)**, primer toque: los pads 1-16 enseñan el **canal de escucha** (blanco = el elegido, blanco tenue = el resto); PGM Rx no cambia. **Un pad de canal** lo elige. Tocar el pad 29 otra vez = encender / apagar PGM Rx, como siempre.
- **Pad 30 (PGM Tx)**: lo mismo con el **canal de salida**.
- Un botón de pista u otro pad: los pads 1-16 vuelven a ser los canales de las pistas.
- Por defecto los dos son el **16** (como el original). Se guardan con los ajustes del aparato; con el firmware original vuelven a 16.

Qué hacen:
- **Recepción** (con PGM Rx): un Program Change en el canal de escucha elige el proyecto, como el canal 16 del original. Si el canal de escucha es otro, el 16 ya no elige proyectos. Si coincide con el canal de Synth 1, Synth 2 o los drums, el Program Change va a esa pista (como en el original).
- **Reenvío**: con PGM Tx encendido, el Program Change recibido en el canal de escucha sale otra vez por el canal de salida (el original no lo reenvía; un proyecto pedido por MIDI no se vuelve a enviar).
- **Envío** (con PGM Tx): el Program Change de un proyecto elegido en el panel sale por el canal de salida. Los CC del proyecto siguen en el canal 16.

## Arreglo: Synth 1 / 2 en la vista Setup
Desde SC19.1, pulsar Synth 1 / 2 con su vista en pantalla abre la vista de la fuente del sinte (la «segunda pulsación»). La vista Setup no cambia la vista de pista que se veía antes: si se entraba en Setup desde la vista de Synth 1 (o Synth 2), su botón llegaba a Setup como Preset y **ese sinte no se podía elegir para ver o cambiar su canal MIDI**. Ahora en Setup los botones Synth 1 / 2 eligen la pista como en el original; fuera de Setup la segunda pulsación sigue abriendo la vista de la fuente.

## Qué probar
1. Entra en Setup **desde la vista de Synth 1**. Pulsa Synth 1: los pads enseñan el canal de Synth 1 (antes no respondía). Igual con Synth 2.
2. Pad 29 (PGM Rx): los pads 1-16 en blanco tenue, el 16 en blanco; el pad 29 no cambia de color. Pulsa el pad 5: el 5 en blanco.
3. Pad 29 otra vez: PGM Rx se apaga / enciende como siempre (los pads siguen enseñando el canal de escucha).
4. Pad 30 (PGM Tx): enseña el canal de salida (16); elige el 10.
5. Un botón de pista: los pads vuelven a los canales de la pista. Sal de Setup y vuelve: los pads de canal son los de la pista.
6. Apaga y enciende: en Setup, pad 29 / 30 enseñan 5 / 10.
7. Con un secuenciador externo: Program Change en el canal 5 → cambia el proyecto; en el 16, no. Con PGM Tx, el aparato manda ese Program Change por el canal 10.
8. Elige un proyecto en el panel con PGM Tx: sale un Program Change por el canal 10.
9. Vuelve a poner los dos en 16: todo como el original.

## Verificación en emulación
- `emu_pgmch.py`: pads por el controlador en el modo 8 (estado, LEDs del fotograma, bytes 1 / 2 del parámetro 3, bit de PGM Rx), botón de pista, otro pad, Advanced, salida de Setup; el «¿han cambiado?» de stock (`0x0802D300`) ve los dos bytes y el guardado de stock (con la escritura del fichero anulada) los lleva al registro; recepción por el despachador real `0x08051720` (canal de escucha = proyecto + reenvío por el canal de salida, canal 16 nada, canal de Synth 1 a Synth 1, sin PGM Tx sin reenvío); envío por `0x0802A018`; la build anterior: canal 16 = proyecto.
- `emu_setupfix.py`: en Setup, Synth 1 / 2 llegan a la vista como pistas 0 / 1 (la anterior: Preset); fuera de Setup la segunda pulsación sigue siendo Preset.

