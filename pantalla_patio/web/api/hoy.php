<?php
// Solo lectura: devuelve las guardias de hoy de cada turno. No escribe nada.
// Cada turno sale de su cuenta (una hace el reparto de la mañana y otra el de la tarde): cada cuenta
// tiene su propia base, así que sus zonas y recreos van en su bloque y no se mezclan.
date_default_timezone_set('Europe/Madrid');
require __DIR__ . '/../config.php';
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function responder($datos, $codigo = 200)
{
    http_response_code($codigo);
    echo json_encode($datos, JSON_UNESCAPED_UNICODE);
    exit;
}

// Quién vigila cada zona hoy no es público: sin el token de config.php, 403.
// Falla cerrado: un TOKEN vacío o sin definir también deniega.
$token = isset($_GET['t']) ? (string) $_GET['t'] : '';
if (!defined('TOKEN') || TOKEN === '' || !hash_equals(TOKEN, $token)) {
    responder(array('error' => 'sin_permiso'), 403);
}

$dir = __DIR__ . '/../datos/';
$hoy = date('Y-m-d');
$turnos = array('mañana' => 'CUENTA_MANANA', 'tarde' => 'CUENTA_TARDE');

// Resúmenes publicados por la app (datos/<cuenta>.json), del más reciente al más antiguo.
$ficheros = glob($dir . '*.json') ?: array();
usort($ficheros, function ($a, $b) {
    return filemtime($b) - filemtime($a);
});
$leidos = array();
function leer($fichero)
{
    global $leidos;
    if (!array_key_exists($fichero, $leidos)) {
        $datos = json_decode((string) file_get_contents($fichero), true);
        $leidos[$fichero] = is_array($datos) ? $datos : null;
    }
    return $leidos[$fichero];
}

// ¿La cuenta reparte guardias de este turno? (en cualquier fecha: un día sin guardias no la descarta)
function tieneTurno($datos, $turno)
{
    foreach ((isset($datos['guardias']) ? $datos['guardias'] : array()) as $g) {
        if (isset($g['turno']) && $g['turno'] === $turno) {
            return true;
        }
    }
    return false;
}

// La cuenta de cada turno: la fijada en config.php o, si está vacía, la que publicó más
// recientemente guardias de ese turno.
function ficheroDelTurno($turno, $constante, $ficheros, $dir)
{
    $fijada = defined($constante) ? constant($constante) : '';
    if (preg_match('/^[0-9a-f]{16}$/', $fijada)) {
        return is_file($dir . $fijada . '.json') ? $dir . $fijada . '.json' : null;
    }
    foreach ($ficheros as $f) {
        $datos = leer($f);
        if ($datos !== null && tieneTurno($datos, $turno)) {
            return $f;
        }
    }
    return null;
}

$bloques = array();
foreach ($turnos as $turno => $constante) {
    $f = ficheroDelTurno($turno, $constante, $ficheros, $dir);
    $datos = $f === null ? null : leer($f);
    if ($datos === null) {
        $bloques[$turno] = null;
        continue;
    }
    $guardias = array();
    foreach ((isset($datos['guardias']) ? $datos['guardias'] : array()) as $g) {
        if (isset($g['fecha'], $g['turno']) && $g['fecha'] === $hoy && $g['turno'] === $turno) {
            $guardias[] = $g;
        }
    }
    $recreos = array();
    foreach ((isset($datos['recreos']) ? $datos['recreos'] : array()) as $r) {
        if (!isset($r['turno']) || $r['turno'] === $turno) {
            $recreos[] = $r;
        }
    }
    $bloques[$turno] = array(
        'cuenta' => basename($f, '.json'),
        'publicado' => isset($datos['publicado']) ? $datos['publicado'] : null,
        'recreos' => $recreos,
        'zonas' => isset($datos['zonas']) ? $datos['zonas'] : array(),
        'guardias' => $guardias,
    );
}

if ($bloques['mañana'] === null && $bloques['tarde'] === null) {
    responder(array('error' => 'sin_datos'), 503);
}

responder(array(
    'hoy' => $hoy,
    'dia_semana' => (int) date('w'),
    'dia_del_anio' => (int) date('z'),
    'segundos_del_dia' => (int) date('G') * 3600 + (int) date('i') * 60 + (int) date('s'),
    'turnos' => $bloques,
));
