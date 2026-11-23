# S737D — diagnóstico: ¿cuántas veces se envía el programa del DSP?

= Alpha 7.37 + un contador (palabra libre de la caja negra, `0x2004F1CC`) que sube en cada envío de los programas del DSP.
Sirve para saber si la mitad de la ITCM que usa el cargador (`0x2000-0x3FFF`) queda libre después de encender.

1. Instalar y dejar el aparato conectado por USB.
2. Claude lee el contador (valor de partida).
3. Usar el aparato con normalidad unos minutos: cambiar de pack, cargar proyectos, guardar, abrir la app y subir un sample o un patch, tocar con todo sonando.
4. Claude vuelve a leer. Si el contador no ha subido, el programa del DSP solo se envía al encender.

Todo lo demás es la Alpha 7.37.
