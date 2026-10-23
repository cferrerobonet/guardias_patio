/* Pantalla de guardias de patio. ES5 a propósito: los navegadores de las smart TV son viejos.
   Solo lee: pide api/hoy.php cada minuto y pinta según la hora del servidor. */
(function () {
  var MANANA = [8 * 3600, 12 * 3600 + 15 * 60];   // de 8:00 a 12:15
  var TARDE = [15 * 3600, 19 * 3600 + 15 * 60];   // de 15:00 a 19:15
  var REFRESCO_MS = 60 * 1000;
  var DIAS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
  var MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
    'septiembre', 'octubre', 'noviembre', 'diciembre'];
  var PARTICULAS = { de: 1, del: 1, la: 1, las: 1, los: 1, y: 1, i: 1, el: 1 };
  var FRASES = [
    'Educar no es llenar un recipiente, es encender una llama.',
    'Cada niño que aprende a leer abre una puerta que nadie podrá cerrar.',
    'Enseñar es sembrar hoy lo que otros recogerán mañana.',
    'Un buen maestro deja huella donde nadie la ve y se nota toda la vida.',
    'La educación es el arma más poderosa para cambiar el mundo.',
    'Aprender es el único tesoro que nadie te puede quitar.',
    'Detrás de cada alumno que brilla hay un profesor que creyó en él.',
    'Los niños no recuerdan lo que les enseñamos, sino cómo les hicimos sentir.',
    'Enseñar con cariño es la forma más hermosa de enseñar.',
    'El futuro se construye hoy, en cada aula y en cada patio.',
    'Educar es confiar en que lo mejor de cada persona está por llegar.',
    'Una sonrisa a tiempo también es una lección.',
    'Quien enseña aprende dos veces.',
    'Cuidar a los niños en el patio también es educar.',
    'Cada día en la escuela es una oportunidad para empezar de nuevo.',
    'La paciencia del maestro es la semilla de la confianza del alumno.',
    'No hay mejor inversión para un país que sus escuelas.',
    'Enseñar es el arte de ayudar a descubrir.',
    'Hoy puedes cambiar la vida de alguien con una palabra amable.',
    'La curiosidad es el motor del aprendizaje: cuídala.',
    'Educar es acompañar, no empujar.',
    'Gracias por hacer que cada día cuente en la vida de los alumnos.'
  ];

  var datos = null;     // última respuesta buena
  var baseSeg = 0;      // segundos del día del servidor cuando llegó la respuesta
  var baseMs = 0;       // Date.now() en ese momento
  var el = function (id) { return document.getElementById(id); };

  function segundosAhora() {
    var s = baseSeg + Math.floor((new Date().getTime() - baseMs) / 1000);
    return s % 86400;
  }

  // Token de la pantalla: llega una vez en la dirección (?t=…) y la tele lo recuerda.
  var TOKEN = (function () {
    var m = /[?&]t=([^&#]+)/.exec(window.location.search);
    if (m) {
      try { window.localStorage.setItem('guardias_t', decodeURIComponent(m[1])); } catch (e) { /* sin almacenamiento */ }
      return decodeURIComponent(m[1]);
    }
    try { return window.localStorage.getItem('guardias_t') || ''; } catch (e) { return ''; }
  })();

  function pedir() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'api/hoy.php?t=' + encodeURIComponent(TOKEN) + '&_=' + new Date().getTime(), true);
    xhr.timeout = 15000;
    xhr.onload = function () {
      // Sin el código de acceso la API responde 403: se dice en pantalla en vez de quedarse en espera sin explicación
      // (2026-10-21: la pantalla abierta con la dirección corta en un navegador que no lo había guardado).
      sinPermiso = xhr.status === 403;
      if (xhr.status !== 200) { pintar(); return; }
      try {
        datos = JSON.parse(xhr.responseText);
        baseSeg = datos.segundos_del_dia;
        baseMs = new Date().getTime();
        pintar();
      } catch (e) { /* se queda con lo último que había */ }
    };
    xhr.send();
  }

  function nombreBonito(n) {
    var partes = String(n || '').replace(/\s*\([^)]*\)/g, '').split(',');
    var texto = partes.length > 1 ? partes[1] + ' ' + partes[0] : partes[0];
    var palabras = texto.replace(/\s+/g, ' ').replace(/^ | $/g, '').toLowerCase().split(' ');
    for (var i = 0; i < palabras.length; i++) {
      if (i > 0 && PARTICULAS[palabras[i]]) { continue; }
      palabras[i] = palabras[i].charAt(0).toUpperCase() + palabras[i].slice(1);
    }
    return palabras.join(' ');
  }

  function aSegundos(hhmm) {
    var p = String(hhmm || '').split(':');
    return p.length < 2 ? null : parseInt(p[0], 10) * 3600 + parseInt(p[1], 10) * 60;
  }

  function dosDigitos(n) { return (n < 10 ? '0' : '') + n; }

  function textoFecha() {
    var p = datos.hoy.split('-');
    return DIAS[datos.dia_semana] + ', ' + parseInt(p[2], 10) + ' de ' + MESES[parseInt(p[1], 10) - 1] +
      ' de ' + p[0];
  }

  function turnoActual(seg) {
    if (seg >= MANANA[0] && seg < MANANA[1]) { return 'mañana'; }
    if (seg >= TARDE[0] && seg < TARDE[1]) { return 'tarde'; }
    return null;
  }

  function celda(clase, html) {
    var d = document.createElement('div');
    d.className = clase;
    d.innerHTML = html;
    return d;
  }

  function escapar(t) {
    return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // Cada turno llega en su bloque, de la cuenta que reparte ese turno (sus zonas y recreos no se mezclan).
  function bloqueDe(turno) {
    return (datos.turnos && datos.turnos[turno]) || null;
  }

  function pintarTabla(turno, seg) {
    var bloque = bloqueDe(turno);
    if (!bloque) { return false; }
    var guardias = bloque.guardias.filter(function (g) { return g.turno === turno; });
    var ids = {}, zonasIds = {};
    guardias.forEach(function (g) { ids[g.recreo] = 1; zonasIds[g.zona_id] = 1; });
    var recreos = bloque.recreos.filter(function (r) { return ids[r.id]; })
      .sort(function (a, b) { return a.id - b.id; });
    var zonas = bloque.zonas.filter(function (z) { return zonasIds[z.id]; })
      .sort(function (a, b) { return String(a.nombre).localeCompare(String(b.nombre)); });
    if (!guardias.length || !recreos.length || !zonas.length) { return false; }

    var proximo = null;
    recreos.forEach(function (r) {
      var h = aSegundos(r.hora);
      r.seg = h;
      if (h !== null && seg < h + 30 * 60 && proximo === null) { proximo = r.id; }
    });

    var tabla = el('tabla');
    tabla.innerHTML = '';
    tabla.style.gridTemplateColumns = '18rem repeat(' + recreos.length + ',1fr)';
    tabla.style.gridTemplateRows = 'auto repeat(' + zonas.length + ',minmax(0,1fr))';
    tabla.appendChild(celda('', ''));
    recreos.forEach(function (r) {
      var activo = r.id === proximo;
      var enCurso = activo && r.seg !== null && seg >= r.seg;
      var cls = 'cabecera' + (activo ? ' ahora' : '') + (!activo && r.seg !== null && seg >= r.seg + 30 * 60 ? ' pasado' : '');
      tabla.appendChild(celda(cls,
        '<span class="etiqueta">' + escapar(r.etiqueta || 'Recreo') + '</span>' +
        '<span class="hora">' + escapar(r.hora || '') + '</span>' +
        (activo ? '<span class="marca">' + (enCurso ? 'AHORA' : 'PRÓXIMO') + '</span>' : '')));
    });
    zonas.forEach(function (z) {
      tabla.appendChild(celda('zona', '<b>' + escapar(z.nombre) + '</b>' +
        (z.descripcion ? '<small>' + escapar(z.descripcion) + '</small>' : '')));
      recreos.forEach(function (r) {
        var nombres = guardias.filter(function (g) { return g.recreo === r.id && g.zona_id === z.id; })
          .map(function (g) { return escapar(nombreBonito(g.profesor)); });
        var pasado = r.seg !== null && seg >= r.seg + 30 * 60 ? ' pasado' : '';
        tabla.appendChild(nombres.length
          ? celda('celda' + pasado, nombres.join('<br>'))
          : celda('celda vacia' + pasado, 'Sin asignar'));
      });
    });
    el('turno').innerHTML = 'Turno de ' + turno;
    return true;
  }

  var ultimaFrase = -1;
  function pintarFrase(seg) {
    var i = (datos ? datos.dia_del_anio * 7 : 0) + Math.floor(seg / 45);
    i = i % FRASES.length;
    if (i === ultimaFrase) { return; }
    ultimaFrase = i;
    var p = el('frase');
    p.className = 'frase oculto';
    setTimeout(function () { p.innerHTML = FRASES[i]; p.className = 'frase'; }, 800);
  }

  var claveTabla = '';
  var sinPermiso = false;
  function pintar() {
    var seg = segundosAhora();
    if (!datos || sinPermiso) {
      document.body.className = 'espera';
      el('mensaje').innerHTML = sinPermiso
        ? (TOKEN ? 'El código de acceso de esta pantalla no es válido.' : 'Falta el código de acceso de esta pantalla.') +
          '<br>Ábrela una vez con su dirección completa (guardiasdepatio.epla.es/?t=…).'
        : '';
      pintarFrase(seg);
      return;
    }
    var h = Math.floor(seg / 3600), m = Math.floor((seg % 3600) / 60);
    var fecha = textoFecha();
    el('fecha').innerHTML = fecha;
    el('fecha-espera').innerHTML = fecha;
    el('reloj').innerHTML = dosDigitos(h) + ':' + dosDigitos(m);

    var turno = turnoActual(seg);
    if (turno) {
      var bloque = bloqueDe(turno);
      var clave = turno + '|' + (bloque ? bloque.publicado : '') + '|' + Math.floor(seg / 60);
      if (clave !== claveTabla) {
        if (pintarTabla(turno, seg)) {
          claveTabla = clave;
          document.body.className = 'guardias';
          return;
        }
        el('mensaje').innerHTML = 'Hoy no hay guardias de patio en el turno de ' + turno;
      } else {
        document.body.className = 'guardias';
        return;
      }
    } else {
      el('mensaje').innerHTML = '';
    }
    claveTabla = '';
    document.body.className = 'espera';
    pintarFrase(seg);
  }

  function pantallaCompleta() {
    var d = document.documentElement;
    var pedir = d.requestFullscreen || d.webkitRequestFullscreen || d.mozRequestFullScreen || d.msRequestFullscreen;
    if (pedir && !(document.fullscreenElement || document.webkitFullscreenElement)) {
      try { var r = pedir.call(d); if (r && r.catch) { r.catch(function () {}); } } catch (e) { /* sin permiso */ }
    }
  }

  // Los navegadores solo dejan entrar en pantalla completa tras un gesto: se intenta ya
  // y, si no cuela, con la primera tecla o pulsación del mando.
  pantallaCompleta();
  ['click', 'keydown', 'touchstart'].forEach(function (ev) {
    document.addEventListener(ev, pantallaCompleta);
  });
  try { if (navigator.wakeLock) { navigator.wakeLock.request('screen').catch(function () {}); } } catch (e) { /* opcional */ }

  pintarFrase(0);
  pedir();
  setInterval(pedir, REFRESCO_MS);
  setInterval(pintar, 1000);
  setTimeout(function () { location.reload(); }, 6 * 3600 * 1000);
})();
