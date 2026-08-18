# DA Debug HUD — arquitectura

Consola visual de desarrollo y QA de Dark Angels. Vive aparte del gameplay: el juego no
depende de ella y ella no cambia el comportamiento del juego salvo cuando tú pulsas algo.

## 1. Cómo abrirlo

Tecla **`.`** (Period) o el **`.` del teclado numérico** (Decimal), en PIE o en build de
desarrollo.

**No es F8**: en PIE F8 es el Eject/Possess del editor, y F1-F10 las captura el viewport para
los modos de vista. Se cierra con la misma tecla o con `CLOSE DEBUG HUD`.

Mientras está abierto: cursor visible, input del pawn desactivado (para que clicar no ataque) y
los widgets UMG de DCS escondidos (Slate los pinta siempre por encima del canvas del HUD, así
que la única forma de que el panel se lea es apagarlos; se restauran al cerrar y sólo los que
estaban visibles).

## 2. Estructura

```
BP_DA_HUD  (el AHUD del juego, ya existía)
   │  dibuja objetivo, banner de zona, diálogo y el salto por NumPad
   │  se le añadieron SÓLO dos funciones vacías, DbgTick y DbgDibujar,
   │  y sus dos llamadas a la cabeza de EventTick y ReceiveDrawHUD
   ▼
BP_DA_DebugHUD  (/Game/DarkAngels/Debug/)   ← aquí vive TODO el Debug HUD
      sobreescribe esas dos funciones; hereda intacto lo que dibuja el padre

DA_DA_DebugDestinos   destinos de teleport
DA_DA_DebugEnemigos   tipos de enemigo, encounter presets y bosses
BP_DA_DebugZonas      actor del nivel; instala el HUD por referencia BLANDA
```

**`BP_DA_DebugHUD` es generado.** Lo escribe `Tools/MCP/debughud_montar.py` y se **regenera
entero** en cada pasada: lo que toques a mano dentro se pierde. Los datos, en cambio, viven en
los Data Assets y son tuyos.

No se sobreescriben `ReceiveDrawHUD`/`EventTick` directamente porque en UE 5.8 no existe nodo
*call to parent function*: hacerlo perdería lo que dibuja el HUD del juego.

Cada pestaña son tres piezas con el mismo patrón: `filas_<tab>()` (geometría y acciones),
`dsl_tab_<tab>()` (dibujado) y `dsl_click_<tab>()` (clics). Las dos últimas salen de la primera,
así que dibujado y zonas de clic **no pueden descuadrarse**.

## 3. Cómo crear una herramienta nueva

En `debughud_montar.py`:

1. Escribe `dsl_mi_accion()` devolviendo el DSL de la función.
2. Regístrala en la lista `grafos` de `run()` — **antes** de quien la llame.
3. Añade una fila a `filas_<tab>()`: `(x, ancho, "ETIQUETA", "(CallFunction|DbgMiAccion)", encendido)`.
4. Relanza `node ue.mjs script debughud_montar.py` con **PIE parado**.

Trampas del DSL que te ahorran una tarde: los argumentos de `CallFunction` van **con nombre**
(`:Indice i`), `(return (CallFunction|Otra …))` **devuelve vacío** (hay que hacer el trabajo en
línea), un parámetro no puede ser un array, y los nodos multi-exec como `IsValid` **terminan el
flujo** (nada detrás).

## 4. Añadir un Teleport

Una línea en el array `Destinos` de `DA_DA_DebugDestinos`:

```
Nombre | Categoria | X=-59649 Y=-60004 Z=138 | P=0 Y=90 R=0 | Descripcion | 3
```

El **sexto campo es opcional**: si lo pones, al llegar deja el `ObjectiveIndex` del HUD en ese
valor — es el "state preset" (llegar al boss con el objetivo ya puesto). `COPY TRANSFORM` en
WORLD imprime la línea entera lista para pegar.

## 5. Registrar un enemigo

Una línea en `Tipos` de `DA_DA_DebugEnemigos`:

```
Nombre visible | /Game/Ruta/BP_Enemigo.BP_Enemigo_C
```

Ojo al sufijo **`_C`**: es la clase, no el blueprint. Debe heredar de `BP_BaseAI` para que sea
IA de DCS y no un prop.

## 6. Encounter Presets

Una línea en `Encuentros`:

```
Nombre | indiceDeTipo:cantidad, indiceDeTipo:cantidad
```

El índice es la posición en `Tipos` (0 = el primero).

## 7. Integrar un Boss

Una línea en `Bosses`, mismo formato que los tipos. Para que su **vida** funcione, el boss debe
llevar el `BP_StatsManagerComponent` de DCS: es la única vía alcanzable. Si no lo lleva, el
panel te lo dice en vez de fallar en silencio.

Para que las **fases** dejen de estar apagadas, el boss necesita una función tipo
`EnterPhase(N)` que ejecute la transición de verdad. Escribir sus banderas desde fuera pondría
el flag sin ejecutar nada.

## 8. Añadir Story Flags

Hoy el único flag **global** del proyecto es el objetivo del HUD (`ObjectiveIndex`), y es
alcanzable porque el Debug HUD hereda de `BP_DA_HUD`.

El resto del estado narrativo está **repartido por actor** (`HasFired` de cada
`BP_DA_ZoneTrigger`, `Abierto` de los interactuables, `bDone` del portal…) y **no es
alcanzable**: haría falta una referencia tipada al actor, y esta API no ofrece casts a clases
del proyecto.

Para exponerlos habría que centralizarlos: un `BP_DA_GameState` (o un componente en el
GameMode) con los flags y funciones `GetFlag`/`SetFlag`. En cuanto exista, la pestaña STORY
puede leerlo y escribirlo igual que hace con el objetivo.

## 9. Que no aparezca en Shipping

Tres capas, de más fuerte a más débil:

1. **`/Game/DarkAngels/Debug` está en `DirectoriesToNeverCook`** (`Config/DefaultGame.ini`): en
   un build empaquetado **estos assets no existen**. Es más fuerte que cualquier `if`.
2. **El nivel no tiene referencia dura**: `BP_DA_DebugZonas` pide la clase con
   `LoadClassAssetBlocking` sobre una ruta blanda y, si no está, se cae al HUD normal del juego.
3. **`DbgHabilitado`** en el CDO: interruptor manual por el que pasa toda acción.

No se usó `GetBuildConfiguration` porque **no se puede cablear desde Blueprint** por esta API
(probado de tres formas, incluida la conexión manual).

## 10. Qué depende de sistemas futuros

| Sección | Estado |
|---|---|
| WORLD | Funcional |
| PLAYER — vida, god mode, movimiento, info | Funcional |
| PLAYER — abilities | Sólo *Infinite Resource*; DCS no tiene desbloqueo ni cooldowns |
| COMBAT — multiplicadores, velocidad, trazas | Funcional |
| COMBAT — log | Observa vida; no puede dar atacante, ataque, block, parry ni crítico |
| AI | Funcional |
| BOSS — selección, vida, info | Funcional (si el boss lleva StatsManager) |
| BOSS — fases, stagger, finisher, cinemáticas, QTE | **No existen**: preparados y apagados |
| STORY — objetivo y checkpoints | Funcional |
| STORY — puzzles y collectibles | **No existen**: preparados y apagados |

## Revisión final

- **Tick**: `DbgTick` hace tres lecturas de bool y sale si no hay nada activo. `DbgMantener`,
  `DbgLogTick` y `DbgOlvidarTick` tienen salida temprana. El dibujado sólo corre con el panel
  abierto.
- **Delegates**: no se bindea ninguno, así que **no hay fugas posibles**.
- **Referencias fuertes**: enemigos y bosses se cargan por ruta **blanda**; el nivel no conoce
  la carpeta de debug. Los dos Data Assets sí son referencia dura, pero viven dentro de /Debug.
- **UMG**: ninguno. Todo es canvas del HUD, así que no hay widget gigante que mantener.
- **Level Travel**: `RESTART LEVEL` destruye el mundo y el HUD se reconstruye, así que **el
  estado de debug se pierde** (god mode, multiplicadores, log). Es lo deseable: no arrastras
  trampas a la sesión nueva. Los enemigos generados mueren con el nivel.
- **Pause / Input**: no se pausa el juego a propósito (DCS depende del tick). Si reinicias el
  nivel **con el panel abierto**, el pawn nuevo nace con el input activo mientras el panel sigue
  dibujado: ciérralo antes de reiniciar.
- **Null**: las acciones comprueban el pawn con `IsValid`. El dibujado no, porque sólo corre con
  el panel abierto; durante un reinicio puede colarse un aviso suelto en el log.
- **Duplicación**: el troceo de líneas está repetido en cuatro funciones. **No es descuido**: es
  obligado, porque delegar en otra función devuelve vacío por esta API.

## ⚠️ La regeneración es todo o nada

`debughud_montar.py` **borra y recrea el blueprint entero**, grafo a grafo y en el orden de
la lista `grafos`. Tarda unos **35 minutos** y durante ese rato el editor va lentísimo, porque
recompila una vez por grafo.

Un corte a mitad **no deja "lo de antes más lo nuevo"**: deja el asset sin las funciones del
final de la lista, que son justo `DbgClick`, `DbgTick` y `DbgDibujar` — la tecla y el dibujado.
Es decir, **el panel deja de existir** aunque todo lo demás esté.

Mientras corre, entonces: **ni Play, ni cerrar el editor, ni abrir un segundo editor.**

- **Play** hace fallar el último paso, que recompila `BP_DA_HUD` (el editor rechaza compilar en
  modo juego). Los ganchos quedan puestos pero sin compilar.
- **Cerrar el editor** es el caso malo: pasó el 2026-08-18 y dejó el panel sin `DbgTick` ni
  `DbgDibujar`. Se arregla con una pasada completa, no hay que reparar nada a mano.
- **Abrir un segundo editor** rompe el MCP: el primero no suelta el puerto 8000 al morir y el
  nuevo arranca con `HttpListener unable to bind to 127.0.0.1:8000`, o sea sin servidor. Hay
  que matar el proceso viejo y relanzar `ModelContextProtocol.StartServer` **con el puerto ya
  libre**; si se lanza antes, falla en silencio.

Antes de lanzarlo, dos comprobaciones que salen gratis y evitan la pasada perdida: que el
Python compila (`ast.parse`) y que **el DSL generado cuadra de paréntesis**, importando el
módulo y llamando a las `dsl_*` nuevas sin tocar el editor.

### Los setters de otro blueprint van con `:self`

Escribir una variable de **otro** blueprint es `Class|<BP>|Set<Var>`, y **hay que nombrar los
dos pines**:

```
(Class|BPDADebugConfig|SetDilatacion :self cfg :Dilatacion (Variables|Default|GetFinDilatacion))
```

Posicional **no vale**: el DSL reserva el pin `self`, así que los argumentos empiezan después y
el objeto se va al pin del valor. El síntoma es
*"Could not connect pin AsBP DA Debug Config to Dilatacion"*, y **tumba la pasada entera**.

Los **getters** sí aceptan el objeto posicional (`Class|BPDAHUD|GetFinDilatacion hud`), que es
lo que despista: el mismo patrón funciona para leer y falla para escribir.

> **Y una advertencia sobre la verificación en seco:** comprobar que el Python compila y que el
> DSL cuadra de paréntesis **no detecta esto**. El texto era sintácticamente correcto; el fallo
> solo aparece al conectar los pines dentro del editor, a mitad de la regeneración, con el
> blueprint ya borrado. Antes de una pasada larga con nodos nuevos, conviene probar **un solo
> grafo suelto** en un blueprint de usar y tirar y ver que compila.
