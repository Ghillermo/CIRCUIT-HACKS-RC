# SC41.8 = SC41.7 + metrónomo en cuatro estados con cuenta atrás

`circuittracks-4486-SC41.8.syx` — SHA-256 `423b09854128f766a1be3d9d119d433485b03d88c41e60b62b97f4e3fc6c8ed3`, marca `SC41.8`.
`firmware/b1.8/circuittracks-4486-B1.8.syx` — SHA-256 `edc087da36ab8c17a2314153f8d371805436bf7e1ce74bb5aadf4a90608dbadd`: el mismo código con la marca `B1.8` (**Beta 1.8**).

**Metrónomo con cuenta atrás** (el usuario: «usa un toggle en el metrónomo: sin metrónomo, con metrónomo, sólo countdown, countdown y metrónomo»; issue #2 del repositorio público).
- **Shift + Clear** (cualquier vista) recorre: sin metrónomo → metrónomo → solo cuenta atrás → cuenta atrás y metrónomo → sin metrónomo. El metrónomo es el ajuste de stock (el mismo parámetro que encendía Shift + Clear).
- **LED de Clear con Shift pulsado** = el estado: amarillo (sin), verde (metrónomo), naranja (solo cuenta atrás), azul (las dos).
- Con la cuenta atrás, **Record armado + Play desde parado**: 4 clics (el clic de stock, al tempo del proyecto), Record parpadea en rojo, y al terminar el compás el aparato pulsa Play él mismo: arranca grabando. **Play durante la cuenta** la cancela. Sin Record armado, Play arranca al momento.
- La cuenta atrás se guarda con el proyecto (2 bytes con firma en la cola del registro de la sesión); los bytes de la cuenta en marcha se ponen a cero en cada carga.

## Qué probar
1. Shift pulsado: el LED de Clear enseña el estado. Shift + Clear cuatro veces: amarillo → verde → naranja → azul → amarillo. En verde y azul el metrónomo suena al reproducir; en naranja no.
2. Naranja o azul, Record armado, Play parado: 4 clics al tempo con Record parpadeando, luego arranca grabando. Cambiar el tempo y repetir.
3. Play durante la cuenta: se cancela, no arranca. Play otra vez: nueva cuenta.
4. Sin Record armado: Play arranca al momento, sin cuenta.
5. Guardar, apagar, cargar: el estado de la cuenta atrás vuelve. Un proyecto de stock carga sin cuenta atrás.

## Verificación en emulación
- `emu_countin.py`: los cuatro estados por el controlador (parámetro del metrónomo y bytes propios), LED de Clear con Shift por la llamada real de la tarea de LEDs, la cuenta (clics a 0 / 500 / 1000 / 1500 ms a 120 BPM, Record parpadeando, arranque a los 2 s), cancelar, sin cuenta / sin Record, y la carga de stock (`0x0802EEFE`) con bytes ajenos en la cola.
