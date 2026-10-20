# RC2.03 / RC2.03S (R203 / R203S) = RC2.02 + el arreglo de la cuenta atrás

`firmware/r203/circuittracks-4486-R203.syx` — SHA-256 `d5f3fd6036801d15d7e966641cc999adbcc7a3e68c3884a5e92f73f772beceda`, marca `R203` (**RC2.03**).
`firmware/r203s/circuittracks-4486-R203S.syx` — SHA-256 `738783ed5b8bf080b92ac5ce70a4997059eb94c336a140f8dfe7ba8a658da519`, marca `R203S` (**RC2.03S**).

**Arreglo:** la cuenta atrás (Shift + Clear: solo cuenta atrás / cuenta atrás y metrónomo, con Record armado y Play) tomaba el tempo de un parámetro que no es el del proyecto (p1 del almacén `0x20011404`; el tempo es p0, el que cambia el knob de la vista Tempo / Swing): con un proyecto que no estuviera a 120 BPM (o lo que guardara p1) los 4 clics iban a otra velocidad. Ahora siguen el tempo del proyecto. Nada más cambia respecto a RC2.02 (`countin.use_bpm0()`, una instrucción). RC2.03S = RC2.03 + `rodisk.use_allpacks()`, como RC2.02S.

## Qué probar
1. Un proyecto a un tempo distinto de 120 (p. ej. 90 BPM): Shift + Clear hasta la cuenta atrás, Record armado, Play: los 4 clics a 90 BPM y el transporte arranca a tiempo.
2. Lo demás, como RC2.02 (`firmware/r202/PRUEBA.md`).

## Verificación en emulación
- `emu_countin_bpm.py` (p0 = 100, p1 = 120: clics cada 600 ms; RC2.02 los daba cada 500); `emu_countin.py` (con p0 = p1 = 120).
