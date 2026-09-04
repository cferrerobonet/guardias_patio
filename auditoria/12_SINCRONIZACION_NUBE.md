---
tags:
  - gestion-centro
  - auditoria
  - sincronizacion
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 1-urgente
tipo: referencia
---

# Auditoría del subsistema de sincronización en la nube

## 1. Objetivo pedido

> Cualquier usuario, desde cualquier equipo, usando el mismo usuario y contraseña, maneja la misma información sin perder datos y sin transportar copias de seguridad a mano.

> [!NOTE] Modelo de uso decidido por CarlosFB (2026-09-04)
> **Varias cuentas, cada una con sus propios datos.** Dentro de cada cuenta trabaja una sola
> persona, que a veces cambia de equipo. No hay edición simultánea de una misma cuenta.
>
> Para la mecánica de sincronización esto no cambia nada: la nube es la copia buena de cada
> cuenta y el flujo es descargar, editar, subir. Se descarta la Fase 3, la fusión real.
>
> Lo que sí cambia es la prioridad de la Fase 2. Con varias cuentas, que la contraseña proteja
> de verdad los datos deja de ser una mejora y pasa a ser un requisito: hoy la carpeta remota
> depende solo del nombre de usuario, así que cualquiera puede registrar el nombre de otro en
> su equipo, con la contraseña que quiera, y quedarse con sus datos (SYNC-009).

**Veredicto: el diseño actual no puede cumplirlo, y además falla en silencio.** No es un problema de ajustes: hay tres barreras de fondo. Las cuentas viven en cada ordenador, la fusión de datos empareja registros por un número que cada equipo genera por su cuenta, y las bajas no se propagan. Encima, cuando la subida no ocurre, la aplicación no lo dice.

## 2. Cómo funciona hoy

### Identidad y destino

| Elemento | Dónde está | Consecuencia |
| --- | --- | --- |
| Cuentas y contraseñas | `data/users.json` de **cada equipo** (`sync_manager.py:662`), nunca se exporta | Un usuario creado en un equipo no existe en otro |
| Carpeta en el servidor | `users/<sha256(usuario)[:16]>/` (`sync_manager.py:415-419`) | El destino depende solo del **nombre**, no de la contraseña |
| Base de datos local | `data/users/<mismo hash>/guardias_patio.db` | Una por equipo y usuario |
| Fichero sincronizado | `guardias_patio_data.json`, exportación completa | Reemplazo total en cada subida |

Comprobado: la carpeta `0db13e2857239ed8` que aparece en el servidor es exactamente `sha256("Jefatura_FpBach")[:16]`.

### Los tres momentos de sincronización

1. **Al abrir** (`sync_manager.py:419-513`): si el remoto es más reciente que el local según fecha de modificación, se descarga a un temporal, se compara el número de registros y, si el remoto no tiene menos, sustituye al local y se importa a la base de datos con `clear_existing=False`.
2. **Cada 30 minutos** (`ccleaner_main_window.py:262-270`): lanza `SyncWorker`, que llama a `sync_on_shutdown`. **Solo sube. Nunca descarga.**
3. **Al cerrar** (`main.py:378-415`): exporta toda la base de datos a JSON y lo sube reemplazando el remoto.

### Control de concurrencia

Un fichero `session.lock` dentro de la carpeta del usuario, con señal de vida cada 30 segundos y caducidad de 30 (`session_lock.py:28-52`). Impide dos sesiones simultáneas **del mismo nombre de usuario**.

## 3. Hallazgos

### [SYNC-001] La aplicación cae a modo local en silencio · P0

- **Ubicación:** `sync/backend_factory.py:64-82`.
- **Qué pasa:** si la configuración no es válida o falla al crear el backend, `get_default_backend()` captura el error, deja una línea en el registro y **devuelve un backend local**. La aplicación funciona con total normalidad: guarda, sincroniza y cierra sin un solo aviso. Los datos van a una carpeta del propio ordenador.
- **Por qué importa:** es la explicación de lo observado. Hay usuarios trabajando sin errores cuyos datos nunca han llegado al servidor.
- **Cómo detectarlo hoy:** en el registro del equipo, `Usando backend local como fallback` frente a `Creando SFTPSyncBackend`.
- **Arreglo:** si hay configuración de servidor, un fallo de conexión no puede degradarse a local sin consentimiento explícito. O se avisa y se trabaja en modo local declarado, sin pretender que hay nube, o no se arranca.

### [SYNC-002] La configuración se da por buena sin probar la conexión · P1

- **Ubicación:** `config/sftp_config.py:50-62`, `presentation/dialogs/initial_config_dialog.py:641-665`.
- **Qué pasa:** solo se comprueba que los campos no estén vacíos. Una contraseña mal escrita pasa el control de primer arranque y el usuario cree que quedó configurado.
- **Arreglo:** probar conexión y escritura real antes de aceptar la configuración.

### [SYNC-003] Si la descarga inicial falla, solo se escribe en el registro · P1

- **Ubicación:** `main.py:309-312`.
- **Qué pasa:** `sync_on_startup` devuelve `False` y la aplicación continúa con los datos viejos del equipo. El usuario trabaja sobre una foto antigua sin saberlo.
- **Consecuencia encadenada:** al cerrar, esa foto antigua se sube y reemplaza el trabajo bueno de otro.
- **Arreglo:** si no se pudo descargar, avisar de forma visible y **prohibir la subida** de esa sesión.

### [SYNC-004] Si la subida final falla, la aplicación ya se está cerrando · P1

- **Ubicación:** `main.py:378-415`, `presentation/widgets/sync_progress_dialog.py:34-47`.
- **Qué pasa:** el resultado se refleja en un diálogo que aparece durante el cierre. No hay reintento posterior ni marca de "pendiente de subir" que se recupere en el siguiente arranque.
- **Arreglo:** cola de pendientes persistente: si la subida falla, se marca y se reintenta al abrir, antes de dejar trabajar.

### [SYNC-005] La fusión empareja registros por el identificador local · P0

- **Ubicación:** `sync/data_exporter.py:219, 252, 285…` (`filter_by(id=…)` en cada entidad).
- **Qué pasa:** los identificadores son autoincrementales de cada base de datos. El equipo A crea la zona 1 «Patio Principal» y el equipo B crea la zona 1 «Cafetería». Al fusionar, son el mismo registro: uno sobrescribe al otro y las guardias que apuntaban a esa zona cambian de significado.
- **Por qué importa:** mientras los identificadores se generen localmente, **cualquier fusión entre dos equipos mezcla entidades distintas**. Es el obstáculo de fondo para el objetivo pedido.
- **Arreglo:** identificador estable y global por registro, generado al crearlo y respetado en todas partes.

### [SYNC-006] Las bajas no se propagan y reaparecen · P0

- **Ubicación:** `sync_manager.py:505` (`clear_existing=False`).
- **Qué pasa:** la importación solo crea y actualiza. Nunca borra. Si el equipo A elimina un profesor y sube, el equipo B sigue teniéndolo; y cuando B suba, el profesor eliminado vuelve al servidor.
- **Arreglo:** registrar las bajas como tales, con marca de borrado y fecha, en lugar de deducirlas por ausencia.

### [SYNC-007] La subida no es atómica · P1

- **Ubicación:** `sync_manager.py:290-303` (`sftp.put` directamente sobre la ruta final).
- **Qué pasa:** si la conexión se corta a mitad, el fichero remoto queda truncado. Y es la única copia.
- **Arreglo:** subir a un nombre temporal y renombrar al final, que en SFTP es atómico.

### [SYNC-008] No hay copias ni versiones en el servidor · P1

- **Ubicación:** copias solo locales, en `database/db_manager.py`.
- **Qué pasa:** una subida mala sustituye el único fichero bueno. No hay vuelta atrás desde otro equipo.
- **Arreglo:** rotar unas cuantas versiones antes de reemplazar. Es barato y salva el día.

### [SYNC-009] La contraseña no protege los datos, y las cuentas no viajan · P1

- **Ubicación:** `sync_manager.py:650-700` (clase `UserAuth`), `sync_manager.py:415-419`.
- **Qué pasa:** dos cosas a la vez. Un usuario creado en un equipo **no existe** en otro, así que hoy no se puede cumplir «mismo usuario y contraseña desde cualquier equipo». Y como la carpeta remota depende solo del nombre, cualquiera que instale la aplicación y registre ese mismo nombre, con la contraseña que quiera, accede a esos datos.
- **Arreglo:** que la cuenta viva junto a los datos del usuario en el servidor y se valide contra ella al entrar.

### [SYNC-010] El bloqueo de sesión falla abierto · P2

- **Ubicación:** `main.py:290-292`.
- **Qué pasa:** si no se puede adquirir el bloqueo **y** tampoco leer su información, se sale del bucle y la aplicación continúa **sin bloqueo**.
- **Arreglo:** ante la duda, no dejar pasar.

### [SYNC-011] El bloqueo no cubre el trabajo sin red · P2

Protege de dos sesiones simultáneas conectadas, no de una sesión aislada que luego sube encima. Se resuelve con SYNC-003 y SYNC-004.

### [SYNC-012] La guarda de descarga solo cuenta registros · P2

- **Ubicación:** `sync_manager.py:459-466`.
- **Qué pasa:** rechaza el remoto si tiene menos registros que el local. Evita traerse un fichero vacío, pero también **rechaza borrados legítimos**, y no protege en el sentido contrario: la subida nunca compara nada.

### [SYNC-013] Las credenciales viajan al servidor y no sirven en otro equipo · P2

- **Ubicación:** `sync/data_exporter.py:66-68`, `data_exporter_helpers.py:25-36, 118-127, 214-222`.
- **Qué pasa:** el JSON incluye la configuración de correo y de servidor, cifrada con una clave **propia de cada equipo** (`~/.guardias_patio_key`). En otro ordenador no se puede descifrar, así que ni sirve ni debería estar ahí.
- **Arreglo:** sacar las credenciales del fichero de datos.

### [SYNC-014] La sincronización automática solo sube · P2

- **Ubicación:** `presentation/ccleaner_main_window.py:262-270`, que llama a `sync_on_shutdown`.
- **Qué pasa:** cada 30 minutos se reemplaza el fichero del servidor con el estado local, sin haber comprobado antes si alguien cambió algo. Una sesión larga machaca repetidamente el trabajo ajeno.

### [SYNC-015] La decisión de descargar depende de los relojes · P3

- **Ubicación:** `sync_manager.py:440-447`.
- **Qué pasa:** compara la fecha de modificación local con la remota. Si el reloj de un equipo va adelantado, deja de descargar.
- **Arreglo:** decidir por un número de versión que crezca en cada subida, no por fechas.

## 4. Escenarios de pérdida, con lo que hay hoy

1. **El silencioso.** Alguien configura mal el servidor. Trabaja meses. Nadie ve un error. Sus datos nunca salieron del equipo (SYNC-001, SYNC-002).
2. **El del portátil sin cobertura.** Abre sin red, no descarga, trabaja con datos de la semana pasada y al cerrar sube. El trabajo de los demás desaparece (SYNC-003, SYNC-004).
3. **El de las zonas cruzadas.** Dos equipos crean zonas distintas que reciben el número 1. Al fusionar, las guardias quedan asignadas a la zona equivocada (SYNC-005).
4. **El del profesor zombi.** Se da de baja a un profesor en un equipo. Otro equipo lo resucita en la siguiente subida (SYNC-006).
5. **El del corte a mitad.** Se corta la conexión durante la subida. El único fichero del servidor queda a medias y no hay copia (SYNC-007, SYNC-008).

## 5. Diseño objetivo

Con el modelo decidido —un usuario, un conjunto de datos, un equipo cada vez— la solución es
**reemplazo, no fusión**: la copia de la nube es la buena y el flujo es descargar, editar, subir.

Esto tiene una consecuencia importante y favorable. Los dos hallazgos más profundos, la colisión
de identificadores (SYNC-005) y las bajas que resucitan (SYNC-006), **nacen de intentar fusionar**
dos conjuntos de datos divergentes. Si al abrir la base de datos local se reconstruye a partir del
fichero de la nube, no hay dos linajes que fusionar: los identificadores vienen dados y las bajas
se propagan solas. Ambos dejan de ser un problema de diseño y pasan a resolverse con el mismo
cambio que el resto.

### Fase 1 — La nube es la copia buena

| Cambio | Efecto |
| --- | --- |
| Nunca caer a modo local en silencio | El usuario sabe siempre si está trabajando contra la nube |
| Probar conexión y escritura al configurar | No se acepta una configuración que no funciona |
| Al abrir: descargar y **reconstruir** la base de datos local con ese contenido | Las bajas se propagan y los identificadores dejan de chocar |
| Si la descarga falla: avisar y **prohibir la subida** de esa sesión | Se acaba el escenario del portátil sin cobertura |
| Número de versión que crece en cada subida | Se detecta si alguien subió algo entremedias, sin depender de relojes |
| Antes de subir, comprobar que la versión remota es la que se descargó | Si no coincide, no se sobrescribe: se avisa |
| Subida atómica, a temporal y renombrado | Nunca queda un fichero a medias |
| Rotación de unas cuantas versiones en el servidor | Siempre hay a dónde volver |
| Cola de pendientes que se reintenta al abrir | Una subida fallida no se pierde |
| Bloqueo de sesión que falla cerrado | Ante la duda, no se entra |
| La sincronización automática comprueba antes de subir | Deja de machacar a ciegas |

Con esto, cambiar de equipo funciona: cierras en uno, abres en otro y tienes lo tuyo.

### Fase 2 — Que la cuenta sea de verdad (requisito, no mejora)

Con varias cuentas en juego, esta fase deja de ser opcional: es lo único que separa los datos de
una persona de los de otra. Guardar la ficha de la cuenta junto a los datos del usuario en el servidor, con la contraseña
cifrada como ya se hace en el registro local, y validar contra ella al entrar. Así el mismo usuario
y contraseña funcionan desde cualquier equipo, que es lo pedido, y la contraseña pasa a proteger
algo. Además hay que sacar las credenciales de correo y servidor del fichero de datos (SYNC-013).

### Fase 3 — Descartada

Fusión real con identificadores estables, marcas de última modificación y de baja. Solo haría falta
para edición simultánea, que se ha descartado. Si algún día dos personas tuvieran que editar a la
vez la misma cuenta, habría que retomarla.

## 6. Pruebas que deberían existir

- Dos equipos simulados sobre carpetas distintas: crear en A, sincronizar, comprobar en B; borrar en A, comprobar que desaparece en B.
- Subida interrumpida a mitad: el fichero remoto sigue siendo válido.
- Arranque sin red: la sesión no puede subir al cerrar.
- Servidor mal configurado: la aplicación lo dice, no finge.
- Relojes desajustados: la descarga sigue decidiéndose bien.
- Identificadores que colisionan entre equipos: la fusión no mezcla entidades.

## 7. Decisiones

1. ~~¿Uno cada vez, o varios a la vez?~~ **Resuelto 2026-09-04: uno cada vez.** Fases 1 y 2; Fase 3 descartada.
2. ~~¿Cuentas compartidas o individuales?~~ **Resuelto 2026-09-04: individuales**, una por persona, cada una con sus datos.
   Queda por decidir la transición: hoy todo el mundo entra como `Jefatura_FpBach` y comparte un único conjunto de datos. Hay que definir quién se queda con ese conjunto y cómo arrancan las demás cuentas, y hacerlo **antes** de repartir credenciales nuevas, porque en cuanto alguien entre con un nombre distinto empezará con una carpeta vacía.
3. **Pendiente: ¿qué hacer si no hay servidor?** Bloquear el arranque, o permitir trabajo local declarado, visible y sin sincronización. Recomendado lo segundo, con aviso permanente en la ventana.
