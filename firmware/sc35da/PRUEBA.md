# SC35DA — DIAGNÓSTICO: borrar un pack entero desde el PC

`circuittracks-4486-SC35DA.syx` — SHA-256 `9a2d4eed83bf5b4babc1aea7f96f414355ae42c25bf48a9f014ddaa0a0b96e3d`
Imagen de 0x626ec bytes, CRC 0xbf51025d, marca `SC35DA`.

Es **SC342D** (SC34.2 completo + diagnóstico remoto) con una orden más: **borrar un pack entero**.
- Nunca borra el pack que está cargado.
- Después del borrado, el firmware original deja la tarjeta «sin pack seleccionado». Para que se pueda seguir guardando con normalidad, el diagnóstico vuelve a seleccionar el pack en uso.

Es la pieza más delicada de SC35 y quiero probarla aquí, en remoto, antes de ponerla en un botón.

## Prueba
1. Envía SC35DA y carga el **pack 31**. Déjalo conectado por USB, con los puertos MIDI libres.
2. Avísame. Con tu permiso para los packs 30 y 31:
   1. borro el **pack 30** (carpeta `29_PACK`);
   2. compruebo que el pack 31 sigue respondiendo;
   3. compruebo que el 30 ya no tiene samples.
3. Después, en el aparato:
   - **guarda un proyecto** (Save) y vuelve a cargarlo;
   - mira la vista de packs: el 30 debería verse vacío o sin pack;
   - cambia a otro pack y vuelve al 31.

   Dime si algo se comporta raro.

## Verificación en emulación
`emu_sc342d.py … --delpack`:
- todo SC342D sigue igual;
- el pack actual y el `0x7F` («actual») se rechazan sin llamar a la tarjeta;
- un pack explícito: borrado (operación 5, tipo 1) y después `exists` sobre el pack actual para volver a seleccionarlo.

## Volver atrás
Envía SC34.2.
