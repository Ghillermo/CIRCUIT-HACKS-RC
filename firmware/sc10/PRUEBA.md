# SC10 — Retorno de FX por las tiras 3 y 4 del mixer — plan de prueba

`circuittracks-4486-SC10.syx` — SHA-256 `d96468ecbb9bedab4afa5ff3732e29edc26c3938103b1a032c626123c21b84b2`
Imagen de 0x4D628 bytes, CRC 0xCEF64D02, marca `SC10`.

Incluye todo SC09. **Es el primer firmware que modifica el programa del DSP: haz las primeras pruebas con el volumen bajo.**

## Qué hace
Dos toggles nuevos en **Setup View**:

| Pad | Encendido | Efecto |
|---|---|---|
| **22** (fila 3, columna 6) | brillante | El **retorno de reverb** pasa por la **tira 3** del mixer (Audio In 1) |
| **23** (fila 3, columna 7) | brillante | El **retorno de delay** pasa por la **tira 4** del mixer (Audio In 2) |

Con un toggle activo, la tira correspondiente controla el retorno de ese efecto:
- **Nivel:** 127 = como en stock; 100 ≈ −2 dB; 0 = sin retorno.
- **Pan:** actúa como balance entre los canales izquierdo y derecho del efecto.
- **Sidechain** de esa tira (Shift + FX): el retorno se ducka con el drum elegido.
- **Mute** de la tira: silencia el retorno.

**La entrada de audio de esa tira queda muda**, tanto en directo como en sus envíos. Así no hay forma de realimentar la reverb consigo misma ni el delay consigo mismo.

Los toggles se guardan con los ajustes globales.

## Cómo está hecho
- **DSP núcleo 0** (programa en `0x080101F0`; el código nuevo va en los vectores de interrupción libres P:$80–$D8, 89 palabras):
  - **P:$10B:** al arrancar el DSP se pone a 0 el flag X:$EC.
  - **P:$23C:** antes de la mezcla principal se anulan las muestras de la entrada 1 o 2 del bloque si su toggle está activo. Así queda muda en directo y en los envíos.
  - **P:$D21:** antes de sumar los retornos, el retorno de reverb (Y:$880) se multiplica por las ganancias de la tira 3 y el de delay (Y:$9C0) por las de la tira 4. Esas ganancias ya incluyen nivel × pan × envolvente del sidechain, por muestra (X:$20C/$24C), y se aplican ×16. Después va la suma de stock.
  - Solo se usan las interrupciones ESAI y SHI (IPRP = 9), así que los vectores reutilizados no se disparan nunca.
- **ARM:**
  - pads 22 y 23 → bits 28/29 del parámetro 2, y se reenvía el grupo de parámetros de Audio In;
  - el manejador de ese grupo (`0x08028EEC`) escribe además X:$EC;
  - LEDs mediante el slot 7 de la vtable de Setup;
  - máscara de guardado ampliada a 0x3F07FFFF.

## Verificación
- **DSP** (intérprete dsp56kEmu, fragmentos stock frente a parche):
  - con los toggles apagados, retornos y entradas son idénticos a stock;
  - con cada combinación de toggles, el retorno es el esperado (error ≤ 14 LSB de 24 bits);
  - la mezcla principal con un toggle activo es idéntica a la de stock con esa entrada en silencio;
  - el flag se limpia al arrancar.
- **ARM** (volcado en marcha):
  - el grupo Audio In escribe X:$EC = bits 28/29 y lo demás igual que en stock;
  - los pads 22 y 23 conmutan su bit y reenvían el grupo;
  - el resto de pads de Setup, como en stock;
  - LEDs correctos en las 4 combinaciones;
  - el detector de guardado incluye los bits 28 y 29.
- Regresiones de SC09, SC08, SC06, SC05 y SC04: pasan. La de SC04 se hace sin los pads 22 y 23, que ahora tienen función.
- La comprobación de SC07 "el bit 28 no se guarda" ya no aplica, porque ahora el bit 28 se guarda a propósito.

## Pruebas en el aparato (volumen bajo)
1. Envía SC10. Pon un patrón con reverb y delay audibles: sube los envíos en la vista FX.
2. Setup → pulsa el **pad 22**: brillante. Sal de Setup.
3. Mixer: mueve el **nivel de la tira 3**. La cola de reverb debe subir y bajar; a 0 desaparece.
4. Activa el **sidechain** de la tira 3 con un drum: la reverb debe duckarse con el bombo.
5. Lo mismo con el **pad 23**, la tira 4 y el delay.
6. Con algo conectado a la entrada 1 y el toggle del pad 22 activo, no debe oírse. Al desactivarlo, vuelve.
7. Apaga y enciende: los toggles deben mantenerse.
8. **Si oyes ruido, clics o distorsión, apaga el toggle y dime qué pasaba.**

## Volver atrás
Envía SC09 (o anterior) con el cargador. Si no arrancara, enciende con Scales + Preset + Note.
