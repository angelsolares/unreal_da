# Dark Angels POC — notas de trabajo

Documento de traspaso entre sesiones. Última actualización: 2026-08-01 (paso 7 completado).

> **Copia de seguridad:** `_Backups/DarkAngels_Checkpoint_Paso7_2026-08-01/` — estado íntegro
> al cerrar el paso 7, con hashes SHA256 verificados. Instrucciones de restauración en el
> `LEEME.md` de esa carpeta. El proyecto no está bajo control de versiones: esa copia es la
> única red. Repetirla antes de empezar cambios grandes.

## Contexto del proyecto

- Proyecto: `DynamicCombatSystem.uproject`, Unreal Engine **5.8**
- Ruta: `D:\Game Projects\Unreal DA\DarkAngelsPOC 5.8`
- Base: asset **Dynamic Combat System (DCS)** en `Content/DynamicCombatSystem`
- Se sigue una guía por pasos. Los pasos 4, 5, 6 y 7 están **completados y verificados**.

**Regla fundamental de la guía:** `Content/DynamicCombatSystem` es referencia original intacta.
Todo el trabajo nuevo vive en `Content/DarkAngels`. No mover archivos de DCS a DarkAngels.

## Estado actual

### Paso 4 — estructura de carpetas ✅

Creada en `Content/DarkAngels`:

```
DarkAngels/
├── Blueprints/{Characters, Bosses, Combat, World}
├── Maps
├── Materials
├── Meshes
├── Animations
├── UI
├── Audio
├── VFX
└── Data
```

### Paso 5 — mapa duplicado ✅

- `Content/DarkAngels/Maps/L_DA_SeraphArena_POC.umap`
- Origen: `Content/DynamicCombatSystem/Demo/DemoRoom/DemoLevel.umap` (único `.umap` del proyecto)
- Hecho con `File > Save Current Level As`. El original sigue intacto.
- No se copió el `DemoLevel_BuiltData`. Si la iluminación se ve rara: `Build > Build Lighting Only`.

### Paso 6 — personaje hijo ✅

- `Content/DarkAngels/Blueprints/Characters/BP_DA_PlayerCharacter.uasset` (~40 KB)
- Padre verificado dentro del `.uasset`: `/Game/DynamicCombatSystem/DCS/Blueprints/BP_CombatCharacter.BP_CombatCharacter_C`
- Es un hijo real, no una copia (el padre pesa 4,4 MB).
- Sin redirectors sueltos en `DCS/Blueprints`.

**Nombre real del personaje de DCS:** `BP_CombatCharacter`. Los nombres que sugería la guía
(`BP_DCSCharacter`, `BP_PlayerCharacter`, `BP_DCS_Player`) **no existen** en este proyecto.

**Ojo:** `BP_CombatCharacter` no es solo el jugador. `BP_BaseAI` hereda de él, y de ahí salen
`BP_WarriorAI` y `BP_TreningDummy`. Es la clase base compartida jugador/enemigos: cualquier
cambio directo sobre ella afecta también a todos los enemigos.

### GameMode — sin tocar (correcto)

`BP_DCSGameMode` tiene `DefaultPawnClass = BP_CombatCharacter_C`. **No cambiar todavía**,
la guía lo pide explícitamente. `BP_DA_PlayerCharacter` aún no es el pawn por defecto.

## Paso 7 — arena graybox ✅

Ejecutado por MCP sobre `L_DA_SeraphArena_POC` y guardado. El `DemoLevel` original se
comprobó tras guardar: `is_dirty = false`, sigue intacto.

### Inventario real del nivel — 18 actores

**Borrar:**

| Actor | Qué es |
|---|---|
| `BP_DemoDisplay4` / `BP_DemoDisplay5` / `BP_DemoDisplay6` | Paneles de texto informativos del demo |
| `BP_PickupActor` | Objeto de inventario recogible |
| `BP_AIOSpawner_TreningDummies` | Spawner de muñecos en (-600, -554, -50) |

**Conservar:**

| Actor | Por qué |
|---|---|
| `PlayerStart` | Punto de aparición |
| `BP_AIOSpawner2` | **Enemigo de prueba.** Spawnea `BP_WarriorAI`, que sí ataca. Está en (3705, 1000, -50) |
| `BP_PatrolPath3` | `BP_AIOSpawner2` lo referencia por GUID. Borrarlo rompe la ruta de patrulla |
| `BP_DemoRoom` | **Es el suelo.** Sin él no hay piso |
| `Light Source`, `SkySphere`, `Atmospheric Fog`, `SpotLight`, `SpotLight2`, `PostProcessVolume` | Iluminación |
| `NavMeshBoundsVolume`, `RecastNavMesh-Default` | NavMesh |
| `InstancedFoliageActor` | Se autogestiona, inofensivo |

Se conserva `BP_AIOSpawner2` y no el de dummies porque el paso 8 exige verificar
"morir y volver a ejecutar", y los muñecos de entrenamiento no atacan.

### Coordenadas reales del mapa

Confirmadas por MCP (`get_actor_transform` + `trace_world`), ya no son estimaciones.

- **PlayerStart (original):** `(-605.09, -20.85, -71.45)`, yaw -87.24°
- **Nivel del suelo:** Z = **-176.5** — medido con trazas verticales en 6 puntos.
  La estimación previa de -163 era **incorrecta**.
- **NavMeshBoundsVolume (original):** centro `(1041, 781, -77)`, escala `(36, 20, 1)`
  → cubría X: -2559 a 4641 · Y: -1219 a 2781 · Z: -177 a +23
- **BP_DemoRoom:** bounds `(-2423, -1082, -314)` a `(4527, 2918, 711)`
- **Techo:** hay geometría a Z = 711. Las trazas desde arriba chocan con ella;
  para medir el suelo hay que empezar por debajo (p. ej. Z = 400).
- **Límite del suelo en -Y:** la sala acaba en Y ≈ -1082. En `(0, -1200)` **no hay suelo**.

### Identidad real de los dos spawners

| Nombre interno | Label en el Outliner | Posición original |
|---|---|---|
| `BP_AIOSpawner_C_2` | `BP_AIOSpawner2` (el que se conserva) | `(3705, 1000, -50)` |
| `BP_AIOSpawner_C_3` | `BP_AIOSpawner_TreningDummies` (borrado) | `(-600, -554, -50)` |

Los sufijos `_C_2` / `_C_3` **no** siguen el orden de los labels. Comprobar con `get_label`
antes de borrar.

### Por qué los valores de la guía no sirven

La guía dice poner el cilindro de la arena en `Location 0,0,0`. En este mapa eso deja la
plataforma flotando ~160 unidades sobre el suelo, con el `PlayerStart` enterrado dentro, y su
cara superior (Z=+25) sobresale del techo del `NavMeshBoundsVolume` (Z=+23) → **no se genera
NavMesh sobre la arena y el enemigo no puede caminar por ella**, que es justo lo que hay que
probar en el paso 8.

### Paredes de la sala — la arena de 25 m NO cabe en el origen

Medido con `trace_world` horizontal desde `(0, 0, 300)`:

| Dirección | Pared en |
|---|---|
| -Y | **Y = -944.5** |
| +X | **X = +1044.5** |
| +Y | Y = +2780 |
| -X | X = -2398 |

La sala **no está centrada en el origen**. El radio máximo de un disco centrado en (0,0) es
por tanto **944**, no 1250. La arena de 25 m que pide la guía no cabe ahí: se metía 305 uu
dentro de la pared -Y y 205 uu dentro de la +X, y dejaba 4 de los 8 cubos empotrados en muros.

**Decisión tomada:** encoger la arena a **radio 900 (18 m)** en el origen, en vez de recentrar
el disco. Así no hay que mover nada ya verificado y queda holgura contra las dos paredes.

### Valores aplicados realmente

El pivote del `/Engine/BasicShapes/Cylinder` está **en el centro**, verificado por bounds.

1. **`SM_DA_ArenaFloor`** — `/Engine/BasicShapes/Cylinder`
   - `Location` = `0, 0, -201.5` · `Scale` = `18, 18, 0.5`
   - Bounds: X/Y de -900 a 900, Z de -226.5 a **-176.5**
   - Cara superior exactamente a ras del suelo del demo. Sin escalón.
2. **NavMeshBoundsVolume**
   - `Location` = `1041, 765.5, -100` · `Scale` = `36, 20.2, 3`
   - Cubre X: -2559 a 4641 · Y: -1254.5 a 2785.5 · Z: -400 a 200
   - **No** se usó el `0,0,-100` / `20,20,3` de la nota anterior: ver más abajo.
3. **PlayerStart** → `0, -550, -71.5`, yaw `90` (mira hacia +Y)
4. **BP_AIOSpawner2** → `0, 400, -50`, yaw `-90` (enfrentado al jugador, a 950 uu)
5. **BP_PatrolPath3** → `131.2, 64.9, -176.5`, yaw `90`, **escala 0.6**
   - Sin encoger, sus puntos se salían del disco y cruzaban la pared -Y
6. **8 cubos `SM_DA_ArenaEdge_1..8`** — `/Engine/BasicShapes/Cube`
   - Radio **730**, cada 45° empezando en 22.5°, `Scale` = `3, 3, 6`, `Z` = `123.5`
   - Yaw de cada uno = su ángulo polar, así la cara exterior queda perpendicular al radio
   - Esquina más lejana a radio 892 < 900 (disco) y < 944.5 (pared). Ninguno toca muro
   - El desfase de 22.5° es a propósito: con el reparto a 0° un cubo caía junto al `PlayerStart`
7. **`SM_BoxPlaceholder`** — `/Engine/BasicShapes/Cube`
   - `Location` = `0, 2300, 423.5` · `Scale` = `5, 5, 12`
   - Bounds: X -250..250, Y 2050..2550, Z **-176.5 a 1023.5** (base a ras del suelo)
   - **Movido desde Y = -1900**, donde quedaba tapado: ver más abajo

Organizados en el Outliner: `DarkAngels/Arena`, `DarkAngels/Arena/Edges`,
`DarkAngels/Placeholders`.

### Por qué el placeholder del boss no puede ir en -Y

En `Y = -1900` la caja quedaba **detrás del muro de Y = -944**, que llega a Z = 711. Solo
asomaba ~1° de arco por encima: invisible desde la arena. Confirmado por traza (la línea de
visión chocaba con el muro a 1878 uu) y por captura de viewport (se veía cielo, no la caja).

Reubicada en `Y = +2300`, dentro de la sala (la pared +Y está a 2780) y sin techo encima
(trazas verticales desde Z=2500 en `(0,0)`, `(0,1900)` y `(0,2300)` llegan todas al suelo).

Verificación final: dos trazas desde el ojo del jugador `(0, -550, 10)` hacia la caja impactan
en **Y = 2050** — su cara frontal — a Z ≈ 428 y Z ≈ 769, sin obstáculos. Se ve entera.

### Trampa de `set_actor_transform`

La documentación de la tool dice que los campos sin valor "no cambian" al modificar un actor
existente. **Es falso: se resetean a identidad.** Pasar solo `location` dejó los 9 cubos a
escala 1 y rotación 0. Hay que **pasar siempre `location` + `rotation` + `scale` completos**.

### Por qué el NavMesh no se encogió a 20×20

`BP_PatrolPath3` estaba en `(3220, 1172, -176.5)` con bounds de X 2270 a 3732 — **entero
fuera** de un volumen de -2000 a 2000. Encogerlo ahí y mover el spawner a la arena habría
dejado al `BP_WarriorAI` patrullando hacia puntos sin NavMesh a 3 km.

Solución aplicada: se mantuvo la huella X original del volumen, se bajó su centro en Y a
765.5 para tapar el borde -Y de la arena (-1250, que el original no alcanzaba: llegaba a
-1219) y se subió la escala Z a 3. Además se trasladó `BP_PatrolPath3` a la arena, dejando
el centro de sus bounds en el centro del disco (offset origen→centro de bounds =
`(-218.6, -108.2)`, de ahí la posición `218.6, 108.2`).

## Paso 8 (PENDIENTE) — primer checkpoint

`Ctrl + Shift + S` (Save All), luego Play (`Alt + P`).

El nivel ya está guardado tras el paso 7, pero **el NavMesh aún no se ha reconstruido ni
visto**. Antes de Play: `Build > Build Paths` (o `Build All`) y **pulsar `P` en el viewport**
para pintarlo. Si la superficie de la arena no aparece en verde, el enemigo no la pisará
→ revisar el `NavMeshBoundsVolume`.

**Falta construir la iluminación.** Tras el paso 7 el Message Log da
`MapCheck: Error: WorldSettings_1 Maps need lighting rebuilt`. Es el error esperado: el mapa
se duplicó sin su `BuiltData`. Se quita con `Build > Build Lighting Only`. Mientras no se
haga, todo se ve blanco plano y los cubos completamente negros.

### Verificado en PIE ✅

Consultado el mundo `UEDPIE_0_L_DA_SeraphArena_POC` en vivo:

| Actor | Posición | Radio desde el centro |
|---|---|---|
| `BP_CombatCharacter_C_0` (pawn del jugador) | `(199.9, -35.8, -78.3)` | 203 |
| `BP_WarriorAI_C_0` (enemigo) | `(208.2, 78.0, -78.3)` | 222 |

Ambos dentro del disco (radio 900) y ambos a `Z = -78.3` = suelo de la arena (-176.5) más la
media altura de la cápsula → **de pie sobre el círculo**, ni flotando ni hundidos.

El `BP_WarriorAI` spawnea en el spawner `(0, 400)` y se desplaza solo hasta el jugador
(~340 uu recorridos, acabaron a 114 uu uno de otro): **la IA detecta y persigue**.

Nota: el pawn es `BP_CombatCharacter`, el de DCS — correcto, el GameMode aún no se toca.
`BP_DA_PlayerCharacter` todavía no es el pawn por defecto.

### Trampa: el NavMesh no se construye durante PIE

```
LogNavigation: Warning: UNavigationSystemV1::Build Navigation NOT building
because navigation build is locked (flags: 0x20)
```

`Build > Build Paths` **se ignora en silencio mientras PIE está corriendo**. Hay que parar PIE
antes. Aparece en el log cada vez que se intentó con el juego en marcha.

### Causa raíz del NavMesh vacío — encontrada

En el log de arranque limpio (`Saved/Logs/DynamicCombatSystem.log`):

```
LogNavigation: Warning: Recreating dtNavMesh instance (RecastNavMesh-Default) due mismatch
in number of bytes required to store serialized maxTiles
(serialized: 320, 9 bits) vs calculated required (120, 7 bits)
```

El nivel arrastra el NavMesh horneado del `DemoLevel` original, dimensionado para **320
tiles**. Al reducir el `NavMeshBoundsVolume` en el paso 7, ahora solo hacen falta **120**.
No coinciden → Unreal **descarta los datos horneados y recrea la instancia vacía**. De ahí
los cero tiles y el `Failed to create navmesh of size 0`.

**Arreglo:** `Build > Build Paths` con PIE parado **y guardar el nivel**. Sin guardar, los
tiles nuevos no se serializan y al reabrir vuelve a pasar exactamente lo mismo.

Es prerrequisito de la POC v2: la IA del Giant usa un Behaviour Tree con MoveTo, y sin
NavMesh no se mueve.

### NavMesh RESUELTO ✅

Se puso `RecastNavMesh-Default.RuntimeGeneration = Dynamic` (era `Static`) y se guardó el
nivel. Verificado en PIE:

- Bounds reales del NavMesh: **X -2964..4940 · Y -988..2964 · Z -170..-140** (antes: sin
  superficie). Malla generada justo sobre el suelo de -176.5.
- Desaparece el `LogCrowdFollowing: Unable to find RecastNavMesh instance`, que salía en
  todos los arranques de PIE anteriores.
- El `BP_WarriorAI` recorrió 910 uu desde el spawner `(0, 400)` hasta `(-82.8, -507.7)`.

**Por qué Dynamic y no arreglar el horneado:** el Build seguía rebotando con
`Navigation NOT building because navigation build is locked (flags: 0x20)` **incluso con PIE
parado** — un lock del editor atascado, no el de PIE. Y aunque se desatascara, con `Static`
cualquier cambio futuro de los límites vuelve a invalidar el horneado. `Dynamic` lo genera en
runtime y elimina el problema de raíz. Reversible desde el panel Details del actor.

### Sección histórica: el NavMesh era Static y no tenía tiles

Propiedades reales de `RecastNavMesh-Default` (leídas con `ObjectTools.get_properties`):

| Propiedad | Valor |
|---|---|
| `RuntimeGeneration` | **`Static`** |
| `TilePoolSize` | 1024 |
| `TileSizeUU` | 1000 |
| `AgentRadius` / `AgentHeight` / `AgentMaxSlope` | 35 / 144 / 44 |

`Static` significa que **no se regenera en runtime**: el NavMesh tiene que estar horneado en
el nivel y guardado, o en PIE no hay por dónde pathfindear. Y todas las reconstrucciones del
editor acaban en `ProcessTileTasks build time: 0.00s` — cero tiles — más
`ConstructTiledNavMesh: Failed to create navmesh of size 0` al arrancar PIE.

Que el `BP_WarriorAI` se acerque al jugador **no demuestra** que haya NavMesh: puede ser la
conducta de corta distancia de DCS. Queda por confirmar con `P` en el viewport tras parar PIE
y hacer Build Paths.

Si tras eso el disco no sale en verde, la vía es revisar por qué el volumen no genera tiles
(o poner `RuntimeGeneration = Dynamic`, que resolvería el gameplay pero no es lo que la guía
pide).

### Pendiente de vista humana

- Que el disco de la arena quede en verde de NavMesh hasta el borde (parar PIE antes)
- Combate completo: atacar, bloquear, esquivar, lock-on, morir y volver a ejecutar

Ya verificado por traza, no hace falta comprobarlo a ojo: `SM_BoxPlaceholder` se ve entero
desde el `PlayerStart`, y ningún cubo ni el disco tocan las paredes.

Verificar que se puede: entrar a la arena, moverse, atacar, bloquear, esquivar, fijar al
enemigo (lock-on), ver el placeholder gigante del fondo, morir y volver a ejecutar.

Si el enemigo no aparece tras mover el spawner, revisar su configuración (puede tener
parámetros ligados a la zona lejana donde estaba).

## POC v2 — Giant Boss contra jugador DCS

### El asset ya está instalado

`Content/GiantBossProject/` — 213 archivos, **407 MB**. Es un tercer asset de terceros, así
que **aplica la misma regla que DCS: no tocarlo, crear hijos en `Content/DarkAngels`.**

### Qué trae de verdad

| Bloque | Contenido |
|---|---|
| Pawn | `Blueprint/BP_Giant` |
| Controller | `Blueprint/Controller/BP_GiantAI_Controller` |
| IA | `AI/BossBehaviourTree`, `BossBlackboard`, `BossEnum`, `BP_BossAttack`, `BP_BossChase`, `BP_BossChooseStateSevice`, `BP_BossRandomPatrol` |
| Animación | `Anims/ABP_Giant`, blend space `GiantBS`, locomoción, **18 montages de ataque**, daño y muerte |
| Notifies | Camera shakes de pisada y rugido |
| Mapas demo | `GiantAIShowcaseMap`, `ShowcaseMap` |

### Hallazgo importante: el Giant NO tiene modelo propio

Extraído de los `.uasset`:

- `BP_Giant` usa como malla `/Game/GiantBossProject/Demo/Characters/Mannequins/Meshes/SKM_Manny`
- `ABP_Giant` apunta al esqueleto `SK_Mannequin` (el de UE5)
- El único otro esqueleto del proyecto es el maniquí de UE4

**El "Giant" es el maniquí de UE5 escalado**, con un set de animaciones y una IA propias.
No es un modelo de criatura. Para la POC sirve — es el placeholder hasta que entre el
Serafín — pero conviene saberlo antes de esperar un monstruo en pantalla.

Consecuencia útil: cuando toque meter el Serafín, si se rigea al esqueleto de UE5 Manny,
**todas las animaciones del Giant valen tal cual**, sin retargeting.

### Peso muerto

De los 407 MB, unos 380 son relleno de demo que la POC no usa: maniquíes UE4 y UE5 con sus
texturas, plantilla ThirdPerson (`BP_ThirdPersonCharacter`, `BP_ThirdPersonGameMode`) y dos
mapas de showcase. **No borrar todavía**: `BP_Giant` depende de `SKM_Manny`, que vive dentro
de `Demo/`. Solo se podrá limpiar cuando el Giant tenga malla propia.

### Sistema de daño de DCS — investigado a fondo

**DCS NO usa el sistema estándar de Unreal.** `Event AnyDamage` nunca se dispara, así que la
prueba del `Print String` no habría enseñado nada útil. Leído de
`BP_CombatCharacter:TakeDamage` con `read_graph_dsl`:

```
fn TakeDamage (HitData)                      ← función de INTERFAZ, no Event AnyDamage
  ...
  Interface|TakeDamage (GetStatsManager) (DamageToApply) (WasBlocked)
```

| Elemento | Qué es |
|---|---|
| Interfaz de daño | **`I_CanBeAttacked`** → `TakeDamage(HitData)` + `IsAlive()` |
| Payload | struct **`FHitData`**, no un float |
| Vida | componente **`BP_StatsManagerComponent`** |
| Traces del arma | componente **`BP_CollisionHandlerComponent`** |
| Lock-on | interfaz aparte **`I_IsTargetable`** → `IsTargetable` / `OnSelected` / `OnDeselected` |

`TakeDamage` además consulta GameplayTags (`HitData.CanBeHeadShot`, `HitData.CanStun`),
el `StateManager` (actividades tipo `Activity.CanParryHit`) y el `CombatComponent` para
bloqueo y parry. Rutas en `DCS/Blueprints/Interfaces/`.

### BP_DA_GiantBoss — creado

`/Game/DarkAngels/Blueprints/Bosses/BP_DA_GiantBoss`, hijo de `BP_Giant`.

`BP_Giant` deriva directamente de `Character`, no tiene ninguna relación con DCS y su única
variable es `Death`. Sin vida de ningún tipo. Añadidas al hijo: `MaxHealth` (float),
`CurrentHealth` (float), `IsDead` (bool).

### Segundo límite del MCP: no puede añadir Blueprint Interfaces

`ObjectTools` resuelve la ruta de un Blueprint a su **CDO**, así que no alcanza la propiedad
`ImplementedInterfaces` del asset. Y no existe herramienta dedicada.

**Paso manual:** abrir `BP_DA_GiantBoss` → `Class Settings` → `Interfaces` → `Add` →
`I_CanBeAttacked` e `I_IsTargetable`. Después de eso sí puedo escribir los grafos de
`TakeDamage`, `IsAlive` e `IsTargetable` por MCP con `write_graph_dsl`.

**Ojo:** no crear una función suelta llamada `TakeDamage` antes de añadir la interfaz —
colisiona con la de la interfaz. (Se creó una por error al probar y se eliminó.)

### Interfaces añadidas e implementadas ✅

Las dos interfaces se añadieron a mano (`Class Settings > Interfaces`). Firmas reales:

```
fn TakeDamage (HitData) -> (bool, enum)     ← DOS valores de retorno
fn IsAlive () -> bool
fn IsTargetable () -> bool
fn OnSelected () / fn OnDeselected ()
```

Campos de `FHitData`: `Damage` (float), `DamageCauser` (Actor), `HitFromDirection` (Vector),
`HitResult`, `HitTags` (GameplayTagContainer). En el DSL, `BreakFHitData` usado como
expresión devuelve el **primer** campo, `Damage`.

Grafos escritos por MCP y compilados sin errores:

- **`IsAlive`** y **`IsTargetable`** → `return (not IsDead)`
- **`TakeDamage`** → si está muerto o `Damage <= 0` devuelve `false`/`NewEnumerator1`; si no,
  resta vida, imprime la vida restante, y al llegar a 0 pone `CurrentHealth = 0`,
  `IsDead = true` y **`Death = true`** (la variable heredada de `BP_Giant`, que es la que
  consume `ABP_Giant` para la animación de muerte). Devuelve `true`/`NewEnumerator0`
- **`EventBeginPlay`** → `MaxHealth = 1000`, `CurrentHealth = 1000`, `IsDead = false`

Valores del enum de retorno, deducidos de `BP_CombatCharacter:TakeDamage`:
`NewEnumerator0` = golpe normal · `NewEnumerator1` = sin daño · `NewEnumerator2` = bloqueado ·
`NewEnumerator3` = parry.

### Colisión del Giant — ya era correcta

No hubo que tocar nada. `CharacterMesh0.bodyInstance`:

| Propiedad | Valor |
|---|---|
| `collisionEnabled` | `QueryOnly` |
| `collisionProfileName` | `CharacterMesh` |
| `objectType` | `ECC_Pawn` |
| `physicsAssetOverride` | `None` (usa el de `SKM_Manny`) |

### Instancia del nivel cambiada

`BP_Giant_C_0` eliminado, `BP_DA_GiantBoss_C_0` colocado en su lugar: misma transform
`(0, 600, 93.74)` yaw -90, misma carpeta `DarkAngels/Boss`, bounds idénticos. Verificado:
`AIControllerClass = BP_DA_GiantAI_Controller_C`, `AutoPossessAI = PlacedInWorld`,
`bCanBeDamaged = true`.

**El nivel ya no referencia `BP_Giant` directamente.**

### El Tick de BP_Giant ES la secuencia de muerte

```
EventTick: si Death == true →
  StopMovement · StopLogic(BrainComponent) ·
  SetCollisionEnabled(mesh, QueryAndPhysics) · SetCollisionObjectType(mesh, ECC_PhysicsBody) ·
  SetCollisionEnabled(capsule) · Delay 1.2s · SetSimulatePhysics(mesh, true)
```

O sea que poner `Death = true` **ya dispara parar movimiento, apagar la IA y ragdoll**. Lo que
pedía el paso 14 de la guía (stop movement / disable collision / death animation) viene hecho.

**Por eso NO se debe reescribir el EventGraph de `BP_DA_GiantBoss`:** contiene
`EventTick → Parent: Tick`, y **el DSL no puede crear nodos `Parent:`** (`|Parent:Tick does not
exist`). Reescribir el grafo borraría esa llamada y rompería la muerte del boss.

Consecuencia práctica: el print de vida va dentro de `TakeDamage` con `Key` fija y
`Duration 9999`, no en Tick. Se queda permanente en pantalla desde el primer impacto.

### BP_CollisionHandlerComponent — configuración real

`DoTraceTest` usa uno de dos caminos según `UseObjectTypesforTraceTest`. Valores del CDO:

| Propiedad | Valor |
|---|---|
| `UseObjectTypesforTraceTest` | `true` → usa `MultiSphereTraceForObjects` |
| `ObjectTypestoCollideWith` | `["ObjectTypeQuery3"]` = **Pawn** |
| `TraceChanneltoCollideWith` | `TraceTypeQuery1` (sin usar) |
| `IgnoredClasses` | **vacío** |
| `TraceRadius` | **0** |
| `Debug` | `false` — ponerlo a `true` dibuja los traces en pantalla |

El mesh del Giant es `ECC_Pawn` con `QueryOnly`, así que **sobre el papel el trace sí debería
impactarlo**. `PerformTrace` traza entre posiciones de socket del arma, descarta actores ya
golpeados y clases ignoradas, y llama a `OnHit`.

### Componentes de DCS montados en el Giant ✅

Añadidos a `BP_DA_GiantBoss` con `ActorTools.add_component`:

| Componente | Config |
|---|---|
| `TeamRelations` (`BP_TeamRelationsComponent`) | `Team = "Team.Bots"`, `Relations = [{Team.Players → Hostile}]` |
| `MeleeCollisionHandler` (`BP_CollisionHandlerComponent`) | pendiente de configurar sockets |

Los valores de equipo se copiaron **literalmente** de `BP_BaseAI`, que es lo que usan los
enemigos que sí funcionan. Verificado por lectura tras escribir.

### API del BP_CollisionHandlerComponent

```
SetCollisionMeshes(CollComps)  · SetCollisionMesh(CollidingComp)
ActivateCollision(CollisionPartTag)  ·  DeactivateCollision
EventTick → si activo: PerformTrace
OnHit (event dispatcher, devuelve HitResult)
```

`FCollisionComponent` = `{ Component: PrimitiveComponent, Sockets: [Name] }`.

**Sockets del Giant:** `SKM_Manny` solo trae `weapon_r_muzzle`, `foot_r_Socket` y
`foot_l_Socket` — ninguno en las manos. **No hace falta modificar la malla de terceros:**
`GetSocketLocation` acepta nombres de hueso, y `hand_r` / `hand_l` existen (padre
`lowerarm_r` / `lowerarm_l`, verificado). Se usan los huesos directamente.

### Lo que falta para que el Giant haga daño

1. En `BeginPlay` de `BP_DA_GiantBoss`: `SetCollisionMeshes` con
   `{Component: Mesh, Sockets: ["hand_l", "hand_r"]}`
2. Bindear `OnHit` → construir un `FHitData` → llamar a `I_CanBeAttacked.TakeDamage`
   sobre el actor golpeado
3. **AnimNotifyState en los montages de ataque** que llame a `ActivateCollision` al empezar
   la ventana de golpe y `DeactivateCollision` al terminar

El punto 3 **no es automatizable por MCP**: no existe toolset de montages ni de AnimNotifies.

**Cuidado con el EventGraph:** si se reescribe con un `EventTick` propio se pierde la llamada
`Parent: Tick` (el DSL no puede crear nodos `Parent:`) y con ella la secuencia de muerte. La
alternativa segura es escribir el EventGraph **sin ningún `EventTick`**: al no sobrescribir el
evento, el Tick del padre se ejecuta igualmente.

### CAUSA RAÍZ del "no le hago daño" — confirmada nodo a nodo

`read_graph_dsl` no lee composites, pero **`find_nodes` + `get_node_infos` sí funcionan sobre
ellos**. Así se pudo reconstruir `BP_CombatCharacter > Weapon Collision Events`:

```
OnHit(HitResult)
  → BreakHitResult → HitActor
  → DCS|Utility|IsEnemy(Querier: self, TargetActor: HitActor)
  → Branch
     └─ true → CanBeAttacked|TakeDamage(HitData)   ← la llamada de interfaz
```

**El daño solo se aplica si `IsEnemy` devuelve true.** Y `IsEnemy` (en `BP_DCSLibrary`) es:

```
fn IsEnemy (Querier TargetActor)
  si IsAlive(TargetActor):
    relation = GetRelationTowardsActor(Querier, TargetActor)
    return relation == Hostile
  si no: return false
```

`GetRelationTowardsActor` coge el `BP_TeamRelationsComponent` **del atacante** y consulta la
relación hacia el equipo del objetivo. Si el objetivo no tiene componente de equipo → Neutral
→ **sin daño**. Eso es exactamente lo que pasaba: el Giant no tenía el componente.

Configuración del jugador (`BP_CombatCharacter`):

```
Team: "Team.Players"   ·   Relations: [{ Team.Bots → Hostile }]
```

Por eso al Giant se le puso `Team = "Team.Bots"`: es la etiqueta que el jugador tiene marcada
como hostil. Con eso la cadena cierra y el daño debe aplicarse.

### TRAMPA CRÍTICA: los componentes añadidos por MCP no llegan a instancias ya colocadas

Con el print de diagnóstico en `IsAlive` se confirmó que **el trace sí impactaba** y que
`IsEnemy` se evaluaba. El fallo estaba en el paso siguiente. Al leer la instancia del nivel:

```
BP_DA_GiantBoss_C_0.TeamRelations →  Team: "None"   Relations: []
BP_DA_GiantBoss_C  .TeamRelations →  Team: "Team.Bots"   Relations: [Team.Players → Hostile]
```

**La clase tenía los valores; la instancia colocada no.** El componente se añadió al Blueprint
*después* de colocar el actor, y la instancia existente no recogió ni el componente ni sus
valores por defecto. `ObjectTools.set_properties` sobre el componente de la instancia
**falla** (`the following properties could not be set`).

**Solución:** borrar el actor del nivel y volver a colocarlo. La instancia nueva
(`BP_DA_GiantBoss_C_1`) sí trae `Team.Bots` y las relaciones. Verificado.

**Regla general:** si se añade un componente a un Blueprint por MCP y ese Blueprint ya tiene
instancias en el nivel, **hay que recolocarlas**. Comprobarlo siempre leyendo las propiedades
del componente *en la instancia*, no en la clase.

**Técnica de diagnóstico que funcionó:** las funciones de interfaz impuras (con pin de
ejecución, como `IsAlive`) admiten un `PrintString`. Instrumentar la **primera** comprobación
de una cadena de condiciones parte el problema en dos mitades comprobables.

**Truco reutilizable:** para leer un composite, `find_nodes(graph, title:"")` lista sus nodos
y `get_node_infos([...])` da tipo, pines y conexiones de cada uno. Se reconstruye el grafo a
mano, pero funciona.

**Limitación encontrada:** `read_graph_dsl` **no puede leer subgrafos de nodos Composite**
(`TypeError: Cannot cast type 'K2Node_Composite' to 'Blueprint'`). El manejo real del impacto
vive en `BP_CombatCharacter:EventGraph > Weapon Collision Events`, que es un composite, así que
esa parte queda sin leer.

### JUGADOR → GIANT: FUNCIONANDO ✅

Confirmado en pantalla: `20.0` de daño por golpe, vida bajando `1000 → 780`. La cadena
completa de DCS (trace del arma → `IsEnemy` → `TakeDamage` por interfaz → resta de vida)
opera sobre el Giant.

El print de diagnóstico de `IsAlive` se retiró; se conservan los de `TakeDamage`, que
muestran daño entrante y vida restante de forma permanente.

**Balance a revisar:** 20 de daño por golpe contra 1000 de vida son **50 golpes** para
matarlo. Para probar el ciclo completo de muerte conviene bajar `MaxHealth` (p. ej. 200) o
subir el daño del arma. La guía decía 1000, pero eso hace la prueba tediosa.

### POC v2 — estado final del combate ✅

| Objetivo de la guía | Estado |
|---|---|
| Giant colocado en la arena | ✅ |
| Giant caminando hacia el jugador | ✅ |
| Giant atacando | ✅ |
| Jugador dañando al Giant | ✅ 25 por golpe |
| Jugador recibiendo daño del Giant | ✅ 25 por golpe |
| Barra de vida del boss | ✅ `WB_AIStatBars` sobre su cabeza |
| Victoria (muerte del boss) | ✅ ragdoll + disolución + destroy |
| Derrota | ⏳ sin probar |

**Falta:** variedad de ataques. El nodo `BP_DA_BossAttack` del árbol tiene sus 14 entradas
apuntando todas a `SmashAttack1_Montage`, el único montage con `ANS_HitBox`. Ver más abajo.

### Secuencia de muerte — hecha a mano, NO se usa la del padre

`BP_Giant.EventTick` tiene su propia secuencia de muerte, pero **no se usa**: no ponemos
`Death = true`. Motivo: ese Tick **no tiene guarda de ejecución única**, así que mientras
`Death` sea true relanza su secuencia cada frame, incluido `SetSimulatePhysics(true)` decenas
de veces por segundo. Eso acumulaba impulso y **lanzaba al Giant por los aires**.

Nuestra versión, dentro de `TakeDamage`, se ejecuta una sola vez:

```
CurrentHealth = 0 · IsDead = true
SetVisibility(StatBarsWidget, false)      ← si no, la barra queda flotando
StopAnimMontage                            ← el root motion del ataque lo arrastraba
StopLogic(BrainComponent) · StopMovement(controller)
StopMovementImmediately + DisableMovement
Capsula → NoCollision
Mesh → ECC_PhysicsBody + QueryAndPhysics + SimulatePhysics(true)
StartDissolve(Mesh)
```

Y `OnDissolveFinished` (dispatcher del `BP_DissolveComponent`) → **`DestroyActor`**. Así el
actor se libera justo al acabar el efecto, sin temporizadores a ojo.

**Coste asumido:** al no activar `Death`, `ABP_Giant` no reproduce su animación de muerte;
pasa directo a ragdoll. Si se quisiera la animación, habría que reproducir `Death1` y
ragdollizar al terminar.

### Componentes de DCS montados en BP_DA_GiantBoss

| Componente | Config |
|---|---|
| `TeamRelations` | `Team.Bots`, hostil a `Team.Players` |
| `MeleeCollisionHandler` | `TraceRadius = 70`, sockets `hand_r/l`, `foot_r/l` |
| `StatsManager` | `Stat.Health = 200`, `Stat.Damage = 25` |
| `StatBarsWidget` | `WB_AIStatBars`, Z=300, 200x34 |
| `DissolveEffect` | `MI_DissolveEffect`, speed 0.4 |

**`TraceRadius = 70` fue clave.** Con 0 (el valor de DCS, pensado para hojas de espada) el
puño del Giant pasaba rozando al jugador sin registrar impacto.

### Para restaurar la variedad de ataques

`Montage to Play_Short` en el **nodo** `BP_DA_BossAttack` de `BT_DA_Boss` (no en la clase)
tiene 14 copias de `SmashAttack1_Montage`. Lista original, por si hay que reponerla:

```
SingleMediumAttack · DoubleMediumAttack · SmashAttack1 · SmashAttack2 ·
HitTheGroundAttack · HeavyGoundHitL · HeavyGoundHitR · HeavyGoundHitTriple ·
SmashAttackLong · CatchAndThrow · TurningAttack · GroundFallAttack (x2) · LowAttack
```

Para cada montage que se quiera reactivar: abrirlo, añadir un **`ANS_HitBox`** en una pista
de notifies nueva, cubriendo la ventana del golpe. Truco: el notify de camera shake que ya
trae el pack marca dónde está el impacto.

`CatchAndThrow` y los `Throw_*` no funcionan con un trace simple — son agarres y proyectiles.

**La variable `Montage to Play_Short` se marcó como `Instance Editable`**; sin eso no aparece
en el panel Details del nodo del árbol ni se puede escribir por MCP.

### El trabajo real de la POC v2

Los objetivos "jugador dañando al Giant" y "Giant dañando al jugador" son el hueso: DCS trae
su propio sistema de daño y el pack del Giant el suyo. Hay que **puentear los dos sistemas**.
Colocarlo y que camine es lo fácil; que se hagan daño mutuamente es lo que lleva tiempo.

### Giant colocado en la arena ✅

`BP_Giant_C_0` en `(0, 600, 93.74)`, yaw -90, carpeta `DarkAngels/Boss`. Apoyado a ras con
`snap_to_ground`. Bounds: X -111..117 · Y 360..751.7 · Z **-176.5 a 357.7**.

**Mide 534 uu de alto (≈5,3 m)** — unas 2,8 veces el jugador. Ojo: el `SM_BoxPlaceholder`
que pusimos en el paso 7 mide 1200 uu, más del doble que el Giant real. Habrá que decidir
cuál es la escala buena del Serafín.

Configuración verificada, toda correcta:

| Propiedad | Valor |
|---|---|
| `AIControllerClass` | `BP_GiantAI_Controller` |
| `AutoPossessAI` | `PlacedInWorld` |
| `CharMoveComp.MaxWalkSpeed` | 300 |
| `CharMoveComp.bOrientRotationToMovement` | `true` |
| `bUseControllerRotationYaw` | `false` |
| Malla / AnimBP | `SKM_Manny` / `ABP_Giant` |

En PIE el controller posee al pawn y existen `BehaviorTreeComponent_0`,
`BlackboardComponent` y `PathFollowingComponent`. **Cero errores de Behaviour Tree.**

### PROBLEMA ABIERTO: el Giant no persigue

Se queda en Idle. Probado teletransportando el pawn del jugador a 1208, 550 y 245 uu de
distancia: en los tres casos igual.

**La prueba concluyente es el yaw.** En seis muestras seguidas vale exactamente
`-90.000000000000014`, bit a bit el valor con que se colocó. Con
`bOrientRotationToMovement = true`, cualquier movimiento dirigido lo cambiaría. El vaivén de
±60 uu que se observa en Y es **root motion de las animaciones de idle/giro**
(`IdleTurnLeft` / `IdleTurnRight`), no locomoción de IA.

Lo que **no** es la causa, ya descartado:

- No es el NavMesh: está generado y el `BP_WarriorAI` navega por él sin problema
- No es acoplamiento al personaje del demo: `BP_BossChooseStateSevice` usa `GetPlayerPawn`
  genérico con `PlayerIndex`, así que **sí ve el pawn de DCS**
- No es que el árbol no arranque: el `BehaviorTreeComponent` existe, o sea que se llamó a
  `RunBehaviorTree`
- No es configuración del pawn: movimiento, controller y auto-possess están bien

`BossEnum` tiene tres estados: **Idle, Chase, Attack**. El servicio nunca sale de Idle.

### CAUSA ENCONTRADA — leyendo los grafos con `BlueprintTools.read_graph_dsl`

El MCP sí lee grafos de Blueprint: `list_graphs` + `read_graph_dsl` devuelven la lógica como
S-expresiones. No hace falta abrir nada a mano.

**`BP_GiantAI_Controller`** — correcto:
```
EventBeginPlay → RunBehaviorTree("/Game/GiantBossProject/AI/BossBehaviourTree")
```

**`BP_BossChooseStateSevice`** (servicio, tickea) — umbrales:
```
distancia = |pos_boss − pos_jugador|      (usa GetPlayerPawn 0, ve el pawn de DCS)
distancia >= 3000              → State = 0  Idle
distancia <= random(200..1000) → State = 2  Attack
resto                          → State = 1  Chase
```
`KeyName = "State"`, que coincide con la clave real del Blackboard. Correcto.

**`BP_BossRandomPatrol`** — deambula a un punto aleatorio en radio 500. Esto es el vaivén de
±60 uu que se observaba.

**`BP_BossChase`** — **PROBLEMA 1**:
```
AIMoveTo(pawn, jugador.location, jugador, AcceptanceRadius = random(700..1000))
```
El radio de aceptación es de **700 a 1000 uu**. La arena tiene radio **900**. En casi toda la
arena `AIMoveTo` considera que ya ha llegado y **el boss no da un paso**.

**`BP_BossAttack`** — **PROBLEMA 2, un bug del pack**:
```
si distancia <= 700: PlayMontage(corto) → OnCompleted → FinishExecute(true)
si no:               PlayMontage(largo) → OnCompleted → (NADA)
```
La rama `else` **nunca llama a `FinishExecute`**. Si el boss entra en Attack estando a más de
700 uu — posible, porque Attack se activa por debajo de `random(200..1000)` — la tarea no
termina nunca y **el Behaviour Tree se cuelga permanentemente**.

Las montages de ataque llevan root motion: eso explica el desplazamiento con el yaw
congelado.

### Diagnóstico de fondo

Esta IA está calibrada para un mapa de showcase grande y abierto. Sus distancias (aceptación
700-1000, idle a partir de 3000, patrulla de 500) son del orden del **tamaño entero de
nuestra arena de 18 m**. No es que esté rota: es que no cabe.

### Qué habría que tocar

| Asset | Cambio |
|---|---|
| `BP_BossChase` | Bajar `AcceptanceRadius` a ~150-250 |
| `BP_BossAttack` | Añadir el `FinishExecute` que falta en la rama larga |
| `BP_BossChooseStateSevice` | Reescalar los umbrales al tamaño de la arena |

**Regla del proyecto:** `GiantBossProject` es asset de terceros. Los cambios van en copias
dentro de `Content/DarkAngels`, con un Behaviour Tree propio que apunte a las tareas
copiadas. No editar los originales.

### Opción A ejecutada — copias en DarkAngels

`AssetTools.duplicate` sobre la carpeta `/Game/GiantBossProject/AI` →
`/Game/DarkAngels/Blueprints/Bosses/AI` (7 assets), más
`BP_GiantAI_Controller` → `BP_DA_GiantAI_Controller`.

**Originales verificados intactos:** el `BP_BossChase` de GiantBossProject sigue con su
`RandomFloatInRange 700..1000`.

Grafos corregidos en las copias con `write_graph_dsl`:

| Asset (copia) | Cambio |
|---|---|
| `BP_BossChase` | `AcceptanceRadius`: `random(700..1000)` → **200** |
| `BP_BossAttack` | Añadido `FinishExecute` en la rama larga (el bug) **y** en `CastFailed`, que tenía el mismo fallo |
| `BP_BossChooseStateSevice` | Idle: `>=3000` → **>=1500**. Attack: `random(200..1000)` → **random(250..400)** |
| `BP_DA_GiantAI_Controller` | `RunBehaviorTree` apunta al `BossBehaviourTree` copiado |
| `BossBehaviourTree` (copia) | `blackboardAsset` apunta al `BossBlackboard` copiado |

Los umbrales nuevos están calibrados para la arena de radio 900: el chase cierra a 200 y el
attack se dispara entre 250 y 400, dejando solape para que no haya banda muerta.

Instancia `BP_Giant_C_0` en el nivel: `AIControllerClass` = `BP_DA_GiantAI_Controller_C`.
Es propiedad de instancia, así que **no modifica `BP_Giant`**.

### Lo que el MCP NO puede hacer — paso manual pendiente

`AssetTools.duplicate` **no remapea referencias**: los nodos del árbol copiado siguen siendo
instancias de las clases **originales** (verificado con `get_class`:
`BossChase_C_0` → `/Game/GiantBossProject/AI/BP_BossChase.BP_BossChase_C`).

La clase de un nodo de Behaviour Tree no es una propiedad, es el tipo del objeto: no se puede
cambiar con `set_properties` y no hay toolset de Behaviour Trees en el MCP.

**Hasta que se haga este paso, las correcciones de arriba no tienen efecto.**

**Trampa de nombres (corregida):** al duplicar la carpeta, las copias conservaron los mismos
nombres que los originales. En el editor del árbol se veía `BP_BossChase` y parecía correcto,
pero era la clase original — imposible distinguirlas a ojo. Las copias se renombraron con
prefijo `_DA_`:

| Copia en DarkAngels | Original en GiantBossProject |
|---|---|
| `BP_DA_BossChase` | `BP_BossChase` |
| `BP_DA_BossAttack` | `BP_BossAttack` |
| `BP_DA_BossChooseState` | `BP_BossChooseStateSevice` |
| `BP_DA_BossRandomPatrol` | `BP_BossRandomPatrol` |
| `BT_DA_Boss` | `BossBehaviourTree` |
| `BB_DA_Boss` | `BossBlackboard` |

**Lección:** al duplicar assets de terceros para modificarlos, **renombrarlos siempre**. Con
nombres idénticos no hay forma de saber cuál se está arrastrando en el editor.

Estructura de `BT_DA_Boss`, con el decorador de cada rama sobre la clave `State`:

```
ROOT (BB_DA_Boss)
└── Selector
    ├── servicio: BP_BossChooseStateSevice   ← sustituir por BP_DA_BossChooseState
    ├── [State == Idle]   Sequence → BP_BossRandomPatrol  ← por BP_DA_BossRandomPatrol
    ├── [State == Chase]  Sequence → BP_BossChase         ← por BP_DA_BossChase
    └── [State == Attack] Sequence → BP_BossAttack        ← por BP_DA_BossAttack
                                   → Wait 1.00s           (dejar)
```

Los decoradores `Blackboard Based Condition` y el `Wait` no se tocan. El servicio tiene
`Interval 0.5` / `Random Deviation 0.1`, valores que también se conservan.

### Sustitución COMPLETADA ✅

Hecha a mano en el editor. Verificada leyendo `BT_DA_Boss.uasset` en disco:

```
/Game/DarkAngels/Blueprints/Bosses/AI/BP_DA_BossAttack        ✓
/Game/DarkAngels/Blueprints/Bosses/AI/BP_DA_BossChase         ✓
/Game/DarkAngels/Blueprints/Bosses/AI/BP_DA_BossChooseState   ✓
/Game/DarkAngels/Blueprints/Bosses/AI/BP_DA_BossRandomPatrol  ✓
/Game/DarkAngels/Blueprints/Bosses/AI/BB_DA_Boss              ✓
```

**Trampa del editor:** si se renombran assets con el editor del Behaviour Tree abierto, el
menú de nodos sigue mostrando la lista cacheada y **la búsqueda no encuentra los nombres
nuevos**. Hay que cerrar y reabrir el árbol, o reiniciar Unreal.

Dependencias residuales hacia `GiantBossProject`, **inofensivas** y de solo lectura:

- `BB_DA_Boss` tipa la clave `State` con el `BossEnum` original
- Los decoradores guardan un puntero al `BossBlackboard` original
- `BP_DA_BossAttack` castea a `BP_Giant`

Los nombres de clave y los valores del enum coinciden, así que resuelve correctamente. La
copia de `BossEnum` en DarkAngels quedó **huérfana** — nadie la referencia, se puede borrar.

## No hacer todavía (lista de la guía)

Importar el Serafín · cambiar el esqueleto del personaje · quitar inventario · crear IA de boss ·
comprar otro framework · modificar Blueprints internos de DCS · integrar Game Animation Sample ·
activar combate direccional · cambiar el GameMode.

Primero: confirmar que DCS corre estable en Unreal 5.8.

## MCP de Unreal — conectado

UE 5.8 trae servidor MCP de primera mano (experimental). Estado verificado:

- Plugins habilitados en el `.uproject`: `ModelContextProtocol` y `EditorToolset`
- Servidor en `http://127.0.0.1:8000/mcp`, dentro del proceso del editor
- `.mcp.json` en la raíz del proyecto
- 19 toolsets registrados

Toolsets útiles para esta POC: `SceneTools` (colocar/eliminar actores), `ActorTools`
(transforms, labels), `ObjectTools` (propiedades), `EditorAppToolset` (selección, viewport,
control de Play-In-Editor), `ProgrammaticToolset` (encadenar tools con Python sandboxeado).

**Si el puerto 8000 no responde:** el servidor no arranca solo salvo que esté marcado
`Editor Preferences > Model Context Protocol > Auto Start Server`. Lanzarlo a mano desde la
consola de Unreal con `ModelContextProtocol.StartServer`.

Se eligió `EditorToolset` en vez de `All Toolsets` a propósito: el agregador arrastra 21
plugins experimentales innecesarios para este trabajo.
