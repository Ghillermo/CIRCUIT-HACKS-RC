# SC35DB — DIAGNÓSTICO: ¿cuánto granular cabe en el segundo núcleo del DSP?

`circuittracks-4486-SC35DB.syx` — SHA-256 `d45b6feaa0cfe3bee2272918d0e2eab0b0f1ee189610543f2f08c33d67377e9b`
Imagen de 0x5c6b4 bytes, CRC 0xdecb07d5, marca `SC35DB`.

**No es un build de uso.** Lleva la cadena de SC35D9, con el diagnóstico remoto.
- **Núcleo 1:** prepara en cada bloque de audio un bloque de prueba, después de hacer una carga de W «granos» simulados que leen la memoria de samples.
- **Núcleo 0:** lo recoge y cuenta los bloques que llegan tarde o mal.

Yo subo W desde el PC hasta ver dónde empieza a fallar. Así sabremos cuántos granos puede mover el sinte granular. No toca la tarjeta. No se oye nada distinto: el bloque de prueba no se mezcla con el audio.

## Qué necesito de ti
1. Envía SC35DB y comprueba que arranca y suena normal.
2. Déjalo conectado por USB, con los puertos MIDI libres. Si quieres, toca algo con varias pistas para que la prueba sea realista.
3. Avísame. Lo demás lo hago yo desde el PC.

## Verificación en emulación
`emu_sc35db.py`:
- **la imagen:** el programa del núcleo 1 cabe en sus 2 K palabras;
- **el núcleo 1:** escribe cada bloque correcto en su búfer, con y sin carga;
- **el núcleo 0:** detecta bloques bien, tarde y corruptos; el reinicio; el caso sin núcleo 1;
- **la orden remota de escritura;**
- **las pruebas de SC35D9.**

## Volver atrás
Envía SC35 (o SC34.2).
