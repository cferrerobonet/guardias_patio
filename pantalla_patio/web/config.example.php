<?php
// Copiar como config.php (fuera de git) y rellenar. scripts/deploy.sh lo sube con la web.
// Cuenta de la app que reparte cada turno: los 16 caracteres hexadecimales de su carpeta de usuario en el
// servidor. De 8:00 a 12:15 la pantalla enseña la de la mañana y de 15:00 a 19:15 la de la tarde
// (assets/app.js). Vacío = automático: la cuenta que publicó más recientemente guardias de ese turno.
define('CUENTA_MANANA', '');
define('CUENTA_TARDE', '');
// Token de la pantalla: api/hoy.php solo responde si la petición lo trae (?t=…).
// La tele abre la dirección de la pantalla con ?t=<token> una vez y lo recuerda.
// Nunca en un repositorio; si se filtra, se cambia en config.php y en la tele.
define('TOKEN', '');
