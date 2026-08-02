# Dark Angels POC — notas de trabajo

Documento de traspaso entre sesiones. Última actualización: 2026-08-02 (polish de combate:
knockdown snappy, i-frames, giro del Giant al atacar, traces de debug apagados).

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
| `Debug` | `false` por defecto — `true` dibuja esferas/líneas **rojas** (`ForDuration`,
  color `(1,0,0)`) en `DoTraceTest`. Ver sección *Traces de debug apagados* más abajo. |

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
| Giant caminando hacia el jugador | ✅ arreglado 2026-08-02 con Supported Agents — ver abajo |
| Giant atacando | ✅ (solo si el jugador entra a ≤400 uu por su cuenta) |
| Jugador dañando al Giant | ✅ 25 por golpe |
| Jugador recibiendo daño del Giant | ✅ 25 por golpe, medido 2026-08-02 |
| Barra de vida del boss | ✅ `WB_AIStatBars` sobre su cabeza |
| Victoria (muerte del boss) | ✅ ragdoll + disolución + destroy |
| Derrota | ✅ muerte + respawn a los 3 s, sin errores |

**Falta:** variedad de ataques. El nodo `BP_DA_BossAttack` del árbol tiene sus 14 entradas
apuntando todas a `SmashAttack1_Montage`, el único montage con `ANS_HitBox`. Ver más abajo.

## Derrota — ya venía en DCS, no hubo que añadir nada ✅

Igual que el lock-on: el ciclo completo de muerte y reaparición del jugador ya está montado
en `BP_CombatCharacter`. **No se escribió ni una línea.**

### La cadena, leída nodo a nodo

En el composite `EventGraph > Stats Events` (leído con `find_nodes` + `get_node_infos`,
porque `read_graph_dsl` sigue sin poder con composites):

```
OnStatChanged(StatsManager)
  → Switch on GameplayTag
     └─ Stat.Health.Current → Branch (StatValue <= 0)
          └─ true → Reactions|Kill
```

`fn Kill()`:

```
SetState(StateManager, "NewEnumerator6")      ← estado Dead; si ya lo estaba, no repite
  DisableCameraLock(DynamicTargeting)          ← suelta el lock-on
  DeactivateCollision(MeleeCollisionHandler)
  RemoveFromParent(InGameWidget)               ← quita el HUD
  SetCollisionProfileName(mesh, "Ragdoll") · SimulatePhysics(mesh, true)
  si Activity.IsInCombat: SimulatePhysics sobre las armas de ambas manos
  SetTimerByEvent(CreateEvent → Respawn, 3.0)
```

`fn Respawn()`:

```
L_Controller = GetController · UnPossess(L_Controller)
GameMode.RestartPlayer(L_Controller) · DestroyActor
```

El `CreateEvent` del timer apunta a `Respawn` — confirmado con
`BlueprintTools.get_create_event_function`, que devuelve `"Respawn"`. El nodo no lo enseña
en sus pines, hay que preguntárselo con esa tool.

**La guarda de ejecución única es el `SetState`**, no un booleano: `Kill` solo sigue si el
cambio de estado devolvió `HasChanged = true`. Por eso no pasa lo que pasaba con el
`EventTick` de `BP_Giant`, que relanzaba su secuencia cada frame.

### Verificado en PIE ✅

Prueba end-to-end sin tocar el teclado: se lanza PIE, el jugador se queda quieto en el
PlayerStart y el Giant hace el resto.

| Momento | Vida | `ReceivedHitCount` |
|---|---|---|
| Inicio | 100 / 100 | 0 |
| Primeras muestras | 50 | 3 |
| Antes de morir | 10 | 15 |
| Tras el respawn | **100** (pawn nuevo) | 0 |

El pawn `BP_CombatCharacter_C_0` **desaparece** del mundo y aparece `BP_CombatCharacter_C_1`
en `(0, -634.25, -78.35)`, yaw 90 — a ras del suelo de la arena (Z = -78.35 es el suelo de
-176.5 más la media cápsula, el mismo valor que el pawn original) y junto al PlayerStart.

**Cero errores en el log** durante toda la secuencia: ni `Accessed None`, ni
`Blueprint Runtime Error`, ni avisos de Behaviour Tree. El boss no se queda con una
referencia colgando del pawn destruido — era el riesgo real, y no se materializa porque
`BP_DA_BossChooseState` y `BP_DA_BossChase` resuelven el objetivo con `GetPlayerPawn(0)`
en cada evaluación, así que recogen el pawn nuevo solos.

### Detalle de balance a revisar

Sobre el pawn recién reaparecido se midió limpio: **1 golpe = 20 de daño**
(100 → 80, `ReceivedHitCount` 0 → 1). Pero durante la pelea el contador subió a 15 mientras
la vida solo bajaba 90, o sea que **muchos impactos registran sin aplicar daño completo** —
probablemente bloqueo (el jugador tiene `Stat.Block = 100`).

Las notas anteriores decían "25 por golpe" para el daño del Giant. El valor observado es 20.
No se ha investigado la diferencia; si el balance importa, empezar por ahí.

### Lo que queda por ver a ojo

La muerte y el respawn están probados por estado del mundo, no por vista. Falta confirmar en
pantalla dos cosas que el MCP no alcanza:

- Que el **HUD vuelve** tras reaparecer. `Kill` hace `RemoveFromParent(InGameWidget)`; el
  pawn nuevo debería recrearlo en su `BeginPlay`, pero no está verificado.
- Que el ragdoll de la muerte se ve bien y no sale disparado.

## Iluminación construida ✅

Hecho a mano (`Build > Build Lighting Only`) — **el MCP no puede lanzarlo**: no hay tool de
build ni de comando de consola en ningún toolset. Es un clic obligatoriamente humano.

Resultado leído del log:

```
Lightmass: 3.08 sec total [41/41 mappings]
L_DA_SeraphArena_POC_BuiltData: lightmap data for 41 meshes in 8 LightmapResourceClusters
Lightmap texture memory:  6.2 MB (8 texturas)
Shadowmap texture memory: 6.8 MB (3 texturas)
MapCheck: Map check complete: 0 Error(s), 0 Warning(s)
```

El error `WorldSettings_1 Maps need lighting rebuilt` **ya no aparece**.

### Por qué NO se puede pasar las luces a Movable

Fue la primera alternativa que se consideró, para no depender de un horneado que hay que
rehacer cada vez que se mueve un cubo del graybox. **No sirve en este proyecto:**

| Comprobación | Valor |
|---|---|
| `LightSource` / `SpotLight_1` / `SpotLight2` — `Mobility` | **Stationary** las tres |
| `r.DynamicGlobalIlluminationMethod` | **0 = None** (Lumen apagado) |
| `r.AllowStaticLighting` | 1 |
| `PostProcessVolume_1` → `bOverride_DynamicGlobalIlluminationMethod` | `false` (no fuerza nada) |

Con la GI dinámica en None, poner las luces en Movable deja la escena **sin rebote
indirecto**: se vería más plana y más oscura, no mejor. Este proyecto depende del horneado.

`Config/DefaultEngine.ini` **no tiene sección `[/Script/Engine.RendererSettings]`**, así que
el valor 0 no viene de ahí. No se ha rastreado su origen; lo que importa es que es el valor
efectivo en el editor.

### Mejora opcional pendiente

El build avisa: `No importance volume found, so the scene bounding box was used`. Añadir un
**`LightmassImportanceVolume`** alrededor de la arena concentraría la calidad y acortaría el
tiempo de horneado. No es un error, es una optimización.

### ⚠️ El horneado hay que GUARDARLO

`Content/DarkAngels/Maps/L_DA_SeraphArena_POC_BuiltData.uasset` en disco es de las
**01:31**, y el build se hizo a las **15:06**. Mientras no se haga `Ctrl+Shift+S`, el
horneado nuevo vive solo en memoria y al reabrir el nivel se pierde. Es el mismo fallo que
ya pasó con el NavMesh.

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

## Variedad de ataques — el nodo, leído de verdad

### El grafo de `BP_DA_BossAttack`

```
EventReceiveExecuteAI(OwnerController, ControlledPawn)
  cast ControlledPawn → BP_Giant           (CastFailed → FinishExecute(false))
  intermediate_distance = |boss − GetPlayerPawn(0)|
  si intermediate_distance <= 700 → PlayMontage(RandomArrayItem(Short))
  si no                          → PlayMontage(RandomArrayItem(Long))
     ambos: OnCompleted → FinishExecute(true) · OnInterrupted → FinishExecute(false)
```

Tres correcciones a lo que decían las notas anteriores:

1. **El nodo tiene TRES arrays, no uno:** `montage to Play_Short`, `_Mid` y `_Long`.
2. **`montage to Play_Mid` no se lee nunca.** El grafo solo usa `Short` y `Long`. Sus dos
   entradas (`LowAttack`, `GroundFallAttack`) son datos muertos.
3. **`Long` tampoco se dispara en esta arena.** `BP_DA_BossChooseState` solo entra en Attack
   por debajo de `random(250..400)`, siempre < 700. Sus entradas (`Throw_Dirt`,
   `Throw_Heavy_Rock`) son inalcanzables — y menos mal, porque son proyectiles sin implementar.

**Conclusión: solo `montage to Play_Short` importa.**

`intermediate_distance` **no es un umbral configurable**: es una variable que el grafo
*escribe* con la distancia medida en cada ejecución. Su valor guardado (0) es irrelevante.
El umbral de 700 está a fuego en el grafo.

Confirmado de paso que los arreglos anteriores siguen puestos: `FinishExecute` está en las
dos ramas y en `CastFailed`.

### El `ANS_HitBox`, por dentro

```
Received_NotifyBegin → GetComponentByClass(BP_CollisionHandlerComponent) del owner
                       → ActivateCollision(CollisionPartTag)
Received_NotifyEnd   → DeactivateCollision
```

Es un **NotifyState** (tiene duración): la ventana de golpe es exactamente su longitud en la
pista. `GetComponentByClass` devuelve el primero de esa clase; el Giant solo tiene
`MeleeCollisionHandler`, así que no hay ambigüedad.

`CollisionPartTag` vale `CollisionPart.PrimaryItem` por defecto. En el Giant **da igual**:
`ActivateCollision` solo guarda el tag y lanza el evento; el trace real usa lo que configuró
`SetCollisionMeshes` (un componente con los 4 sockets `hand_r/l`, `foot_r/l`).

### ⚠️ Segunda modificación a un asset de terceros — encontrada

Las notas registraban **una** sola (`CanCycleDirectionalTargets` en DCS). Hay una segunda:
el `ANS_HitBox` se añadió **directamente sobre**
`GiantBossProject/Anims/Attacks/SmashAttack1_Montage`, sin copia en DarkAngels. Verificado
por `grep` binario: de los 19 montages del pack, ese es el único que menciona `ANS_HitBox`.

### Copias en DarkAngels ✅

Corregido: 12 montages de cuerpo a cuerpo duplicados a
**`/Game/DarkAngels/Animations/Boss/`** con prefijo `AM_DA_` (la lección de siempre: nunca
duplicar conservando el nombre).

```
AM_DA_SmashAttack1          ← conserva el ANS_HitBox de su original
AM_DA_SmashAttack2          AM_DA_SmashAttackLong
AM_DA_SingleMediumAttack    AM_DA_DoubleMediumAttack
AM_DA_HitTheGroundAttack    AM_DA_TurningAttack
AM_DA_HeavyGoundHitL        AM_DA_HeavyGoundHitR
AM_DA_HeavyGoundHitTriple   AM_DA_LowAttack
AM_DA_GroundFallAttack
```

**Duplicar un montage conserva sus notifies**, así que `AM_DA_SmashAttack1` funciona desde
el primer momento sin tocar nada.

Excluidos a propósito: `CatchAndThrow` y `LowGrabAttack` (agarres), `Throw_Dirt` y
`Throw_Heavy_Rock` (proyectiles), `RoaringAttack` (no golpea), `JumpingAttack` (disponible si
se quiere, root motion fuerte), `Death1` (muerte).

`montage to Play_Short` reapuntado a las 14 ranuras con `AM_DA_SmashAttack1`. **El
comportamiento no cambia**, pero el árbol ya no referencia el montage de terceros.

### Trampa de `set_properties` con arrays

No se puede **cambiar el tamaño y el contenido a la vez**:

```
ArrayRemove: elements changed alongside the size change; removed elements are ambiguous.
```

Hay que escribir el array **con el mismo número de elementos** que tenía. De ahí que se
dejaran las 14 ranuras en vez de reducirlas a una. Ventaja no buscada: las 14 ranuras son
una **bolsa ponderada** para el `RandomArrayItem` — repetir un montage lo hace más frecuente.

### Cómo añadir el notify a los demás (paso manual)

El MCP **no puede**: no existe toolset de montages ni de AnimNotifies, y la propiedad
`Notifies` del montage tampoco es legible por `ObjectTools`.

Para cada `AM_DA_*` que se quiera activar:

1. Abrir `AM_DA_SmashAttack1`, seleccionar su `ANS_HitBox` en la pista de notifies y
   **copiarlo** (`Ctrl+C`). Copiarlo en vez de crear uno nuevo evita tener que configurar el
   `CollisionPartTag` a mano.
2. Abrir el montage destino, `Ctrl+V` en una pista de notifies, y **ajustar inicio y
   duración** a la ventana del golpe.
3. Referencia para encontrar la ventana: el **notify de camera shake** que ya trae el pack
   marca el instante del impacto. La ventana del `ANS_HitBox` debe abrirse un poco antes y
   cerrarse justo después.

**Orden importante:** añadir un montage a `montage to Play_Short` **antes** de ponerle el
notify hace que el boss ejecute ataques que no hacen daño. Primero el notify, después la
lista.

### Estado: 5 montages activos

Con `ANS_HitBox` puesto y verificado por `grep` binario sobre el `.uasset`:

```
AM_DA_SmashAttack1  ·  AM_DA_SmashAttack2  ·  AM_DA_SingleMediumAttack
AM_DA_DoubleMediumAttack  ·  AM_DA_HitTheGroundAttack
```

Repartidos en las 14 ranuras de `montage to Play_Short` en proporción 3/3/3/3/2.

**Verificación parcial en PIE:** con el jugador teletransportado a 169 uu del boss, un ataque
impactó por **exactamente 25** de daño (100 → 75, `ReceivedHitCount` 0 → 1). Confirma que la
cadena entera funciona con los montages copiados.

**Pero solo se pudo medir UN impacto**, porque el empujón (`KnockbackForce = 850`) lanza al
jugador fuera de alcance y el boss no puede volver a acercarse — no persigue. **Los 4 montages
nuevos no están verificados individualmente.** Para hacerlo hace falta arreglar antes el Chase,
o bajar temporalmente `KnockbackForce` a 0 y repetir la prueba a bocajarro.

### Variedad de ataques COMPLETA ✅ — 9 montages en rotación

**9 montages con `ANS_HitBox`**, verificado por `grep` binario sobre el `.uasset`, y repartidos
en las 14 ranuras de `montage to Play_Short` (`BT_DA_Boss:BP_DA_BossAttack_C_0`):

| Montage | Ranuras |
|---|---|
| `SmashAttack1` · `SmashAttack2` · `SmashAttackLong` | 2 cada uno |
| `SingleMediumAttack` · `DoubleMediumAttack` | 2 cada uno |
| `HitTheGroundAttack` · `LowAttack` · `TurningAttack` · `HeavyGoundHitTriple` | 1 cada uno |

Los cinco de peso 2 son el núcleo; los de peso 1 son los situacionales o los que conviene
dosificar. Verificado en PIE: el combate corre con 15 impactos encadenados y **cero errores**.

Recordatorio: el array hay que escribirlo **con los mismos 14 elementos**, no se puede cambiar
tamaño y contenido a la vez.

### El `HeavyGoundHitTriple` lleva UNA ventana, no tres

Comprobado a ojo en el editor del montage: la pista 2 tiene **un solo `ANS_HitBox`** que abarca
del frame ~17 al ~65 (de 80). Los tres notifies de la pista 1 son los `BP_Roar_Shake` de cada
impacto, no hitboxes.

**Consecuencia: 25 de daño y un derribo, no 75.** `AddHitActor` descarta a quien ya fue golpeado
dentro de la misma activación, así que una ventana = un impacto por muy larga que sea.

**Matiz:** al ser ~1,6 s de trace activo, el golpe entra **en cuanto el trace roza al jugador**,
que puede no coincidir con ninguno de los tres impactos visibles. Hace el ataque muy difícil de
esquivar y el daño puede sentirse adelantado. Si molesta, estrechar la ventana hasta el primer
`BP_Roar_Shake`.

### La duración del montage decide si hay stunlock

Con el derribo de **2,73 s**, el ciclo `montage + Wait 1,0 s` tiene que ser mayor o el jefe te
pega otra vez en el suelo:

| Montage | Duración | Ciclo | ¿Sirve? |
|---|---|---|---|
| `HeavyGoundHitL` | 1,40 s | ~2,40 s | ❌ pega en el suelo |
| `HeavyGoundHitR` | 1,60 s | ~2,60 s | ❌ pega en el suelo |
| `TurningAttack` | 1,93 s | ~2,93 s | ⚠️ 0,2 s de margen → peso 1 |
| `LowAttack` | 2,20 s | ~3,20 s | ✅ |
| `SmashAttackLong` | 2,27 s | ~3,27 s | ✅ |
| `HeavyGoundHitTriple` | 2,67 s | ~3,67 s | ✅ |
| `GroundFallAttack` | 2,70 s | ~3,70 s | ✅ |

**`HeavyGoundHitL` y `HeavyGoundHitR` quedan fuera a propósito**: reintroducen el stunlock. Si
se quieren, hay que subir antes el `Wait` del Behaviour Tree de 1,0 a 1,5 s.

`GroundFallAttack` sin notify a propósito: root motion de salto, riesgo de desplazar al boss.

**⚠️ Comprobar el Triple:** si lleva **tres** ventanas de `ANS_HitBox` (una por impacto), hace
**75 de daño** y aplica el derribo tres veces, porque `RefreshHitActors` limpia la lista de
golpeados en cada `ActivateCollision`. Con una sola ventana se comporta como un golpe normal.

Para repoblar la lista por MCP, escribir las 14 ranuras de golpe sobre
`BT_DA_Boss:BP_DA_BossAttack_C_0`, propiedad `montage to Play_Short` (ojo: el nombre real
lleva **espacios y minúscula inicial**, no `MontagetoPlay_Short`).

### ⚠️ CORRECCIÓN: quién mataba al jugador en la prueba de la derrota

En la prueba de la derrota se dio por hecho que el Giant bajaba la vida del jugador.
**Era falso: lo mataba el `BP_WarriorAI`** del `BP_AIOSpawner2` que se conservó en el paso 7.

La prueba lo destapó: con el jugador en el PlayerStart, el `BP_WarriorAI_C_0` estaba a
`(88, -522)` — **92 uu del jugador** — mientras el Giant seguía a 1208 uu sin moverse.

Eso explica el "20 de daño por golpe" que no cuadraba con los 25 documentados del Giant:

| Atacante | Daño | De dónde sale |
|---|---|---|
| `BP_WarriorAI` | **20** | hereda de `BP_CombatCharacter`: `Stat.Damage` 10 base + 10 modifier |
| `BP_DA_GiantBoss` | **25** | su `StatsManager.Stat.Damage` |

**La derrota en sí sigue verificada** — el jugador murió y reapareció con vida completa y sin
errores. Solo la atribución del daño estaba mal.

**Lección:** en este nivel hay **dos** IAs hostiles. Cualquier medida de daño al jugador tiene
que comprobar la posición de las dos antes de atribuir nada.

### El Giant sigue sin perseguir ❌ — el problema NO estaba resuelto

Reproducido el 2026-08-02 en dos sesiones de PIE seguidas. El Giant se asienta en
`(0, 658.38, 89.65)` yaw `-90.000000000000014` y se queda ahí. Tres muestras **bit a bit
idénticas**, y el mismo valor exacto en dos sesiones distintas de PIE.

**Prueba de que la máquina de estados sí funciona:** al teletransportar el pawn del jugador a
329 uu, el yaw pasó de `-90.000000000000014` a `-89.9848` y la X se movió. El boss despierta
y ataca cuando el jugador entra solo en su rango. **Lo que está roto es únicamente el Chase.**

Descartado, comprobado uno por uno:

| Hipótesis | Resultado |
|---|---|
| NavMesh ausente o vacío | ❌ `RuntimeGeneration = Dynamic`, bounds X -2964..4940 · Y -988..2964 · Z -170..-140 |
| Umbrales mal | ❌ `ChooseState`: ≥1500 Idle · ≤400 Attack · resto Chase. A 1219 uu toca Chase |
| `AcceptanceRadius` grande | ❌ `BP_DA_BossChase` tiene `AIMoveTo(..., 145)` con sus dos `FinishExecute` |
| El árbol usa los nodos originales | ❌ Selector → servicio `BP_DA_BossChooseState_C_0`, rama Chase → `BP_DA_BossChase_C_0`, decorador `State == 1` |
| El servicio no tickea | ❌ `KeyName = "State"`, `Interval 0.5` |
| El BT no arranca | ❌ existen `BehaviorTreeComponent_0`, `BlackboardComponent`, `PathFollowingComponent` |
| `set_properties` rompió el nodo | ❌ `Mid` y `Long` intactos tras escribir `Short` |
| Falta de foco del editor | ❌ el boss sí se asienta en los primeros frames; el mundo tickea |

**Sospecha principal, sin confirmar: desajuste del agente de navegación.**

| Actor | `agentRadius` | `agentHeight` | ¿Navega? |
|---|---|---|---|
| `RecastNavMesh-Default` | 35 | 144 | — |
| `BP_WarriorAI` | 50 | 192 | ✅ |
| `BP_DA_GiantBoss` | **102** | **528** | ❌ |

El agente del Giant sale de su cápsula (radio 102, media altura 264) y pide **3× el radio y
3,7× la altura** de la malla construida.

**Probado y NO lo arregla:** bajar su `NavAgentProps` a 50/192 (los del Warrior) deja al boss
igual de quieto. El cambio está **revertido** a 102/528.

### Supported Agents — aplicado, pendiente de reinicio

**Por qué la prueba de 50/192 no probaba nada:** con `SupportedAgents` **vacío** (que era el
caso — `Config/DefaultEngine.ini` no tenía sección `[/Script/NavigationSystem.NavigationSystemV1]`),
Unreal enruta *todos* los agentes a una única nav data sin comparar propiedades. Cambiar el
radio del Giant no podía cambiar nada. El Supported Agent modifica el **enrutado**, que es lo
que de verdad está en cuestión.

Añadido a `Config/DefaultEngine.ini`:

```ini
[/Script/NavigationSystem.NavigationSystemV1]
+SupportedAgents=(Name="Default", AgentRadius=35,  AgentHeight=144, DefaultQueryExtent=(50,50,250)  ...)
+SupportedAgents=(Name="Giant",   AgentRadius=102, AgentHeight=528, DefaultQueryExtent=(150,150,500) ...)
```

**Van los dos a propósito.** Con la lista vacía todo funcionaba por el camino de respaldo; en
cuanto se declara **una** entrada, el emparejamiento pasa a ser explícito y cualquier agente no
cubierto se queda sin malla. `Default` mantiene al jugador y al `BP_WarriorAI` (50/192, que
emparejan con 35/144 antes que con 102/528).

`Config/` está bajo git: para deshacerlo, `git checkout Config/DefaultEngine.ini`.

**Requiere reiniciar el editor.** `SupportedAgents` se lee al inicializar el sistema de
navegación; en caliente no hace nada.

Qué comprobar tras el reinicio:

1. Que aparecen **dos** actores `RecastNavMesh` en el Outliner (uno por agente) en vez de uno.
2. `Build > Build Paths` — aunque con `RuntimeGeneration = Dynamic` se regenera sola.
3. En PIE, que el Giant se mueve desde `(0, 658)` hacia el jugador.

### RESUELTO ✅ — el Chase funciona

Tras reiniciar aparecieron **dos** actores en el Outliner: `RecastNavMesh-Default` y
`RecastNavMesh-Giant` (`AgentRadius 102`, `AgentHeight 528`). Confirmado que la hipótesis del
agente era correcta: **el problema era el enrutado, no las propiedades**.

**Segundo escalón, el mismo que ya mordió antes:** la malla nueva nace con
`RuntimeGeneration = Static` y bounds planos (`Z -170..-170`, sin superficie). Hubo que
ponerle **`Dynamic`**, igual que a la `-Default` en su día, y guardar.

> **Regla:** cada `RecastNavMesh` nuevo que cree el sistema de navegación viene en `Static`
> por defecto. Hay que pasarlo a `Dynamic` uno por uno.

Verificado en PIE: el Giant sale de `(0, 600)`, recorre más de 1200 uu y llega a
`(-513, -513)` — a 514 uu del jugador — con el yaw cambiando todo el rato (`-125.6`, `-152.1`,
`26.8`). **Navega de verdad.** El jugador acabó muerto con `ReceivedHitCount = 31`.

### PROBLEMA NUEVO: el BT se cuelga al morir el jugador

Tras la muerte y el respawn del jugador, el Giant se queda clavado en
`(-513.00000311970757, -513.0000015764906)` yaw `26.808959960937518` — tres muestras **bit a
bit idénticas**, con el pawn nuevo (`BP_CombatCharacter_C_1`) ya existiendo a 514 uu, distancia
que exige Chase.

Son **dos fallos distintos**, no uno:

| # | Fallo | Estado |
|---|---|---|
| 1 | Sin nav data para el agente del Giant → nunca perseguía | ✅ arreglado (Supported Agents + Dynamic) |
| 2 | El BT se cuelga cuando se destruye el pawn objetivo | ❌ abierto |

**Sospecha del #2:** `BP_DA_BossChase` llama a
`AIMoveTo(pawn, location, GoalActor = GetPlayerPawn(0), 145)`. `Respawn()` hace `DestroyActor`
sobre el pawn, así que el **goal actor se invalida a mitad de movimiento**. Si en ese aborto no
se dispara ni `OnSuccess` ni `OnFail`, `FinishExecute` no se llama nunca y el árbol queda
colgado para siempre. Es exactamente la misma clase de bug que ya tenía `BP_BossAttack` en la
rama larga.

### La causa real del #2: los cubos del borde bloquean al Giant

**La hipótesis del `GoalActor` destruido era falsa.** Se instrumentó `BP_DA_BossChase` con
`PrintString` en la entrada de la tarea, en `OnSuccess` y en `OnFail`, y el log fue tajante:

```
[BP_DA_BossChase_C_0] CHASE: Execute
[BP_DA_BossChase_C_0] CHASE: OnSuccess      ← en el MISMO milisegundo
```

en bucle, **con el Giant a 521 uu del jugador y un `AcceptanceRadius` de 145**.

`AIMoveTo` no se cuelga: devuelve **éxito** porque Unreal calcula un **camino parcial** hasta
el punto alcanzable más cercano, el Giant llega ahí, y reporta éxito. El árbol funciona
perfectamente; lo que no existe es una ruta hasta el jugador.

**Dónde se queda clavado:** `(-519.9, -516.3)` = **radio 732** desde el centro. Justo el anillo
de los 8 `SM_DA_ArenaEdge`.

**Prueba concluyente:** teletransportando al Giant a `(0, 0)` —dentro del anillo— salió
disparado hacia el jugador y se paró en `(34.25, -409.64)`, a **144 uu**: exactamente su radio
de aceptación. Y empezó a pegar: vida del jugador 100 → 50, `ReceivedHitCount` 3.

**Las cuentas del anillo:**

| Medida | Valor |
|---|---|
| Cubos en radio 730, cada 45°, escala `3,3,6` → **300×300** de planta | |
| Cuerda entre centros | `2 × 730 × sin(22.5°)` = **558,7** |
| Hueco libre entre cubos | 558,7 − 300 = **258,7** |
| Lo que necesita el Giant (`agentRadius` 102) | **204** + margen |

258 contra 204 es demasiado justo: con la erosión de Recast y la voxelización, el hueco **se
cierra** en la navmesh del agente grande. El jugador (radio 35) pasa sin problema; el Giant no.

**Por eso parecía "se cuelga al morir el jugador":** el Giant deambula con `BP_DA_BossRandomPatrol`
(radio 500), acaba fuera del anillo — se le vio en radio 964 y 999, fuera incluso del disco de
900 — y ya no puede volver a entrar. No es un cuelgue, es un encierro.

### Arreglo APLICADO ✅ — cubos adelgazados

Los 8 `SM_DA_ArenaEdge` pasan de escala `3,3,6` a **`2,2,6`**. Posición (radio 730, cada 45°
desde 22.5°, Z=123.5) y rotación (yaw = ángulo polar) **sin tocar**.

```
hueco = 558,7 − 200 = 358,7   →  204 necesarios, 154 de margen
```

Mantiene los 8 pilares y la lectura de la arena, solo los adelgaza. Como los cubos siguen a
Z=123.5 con escala Z=6, la altura no cambia y la base sigue a ras de suelo (-176.5).

Alternativas descartadas: moverlos hacia fuera no cabe (la esquina se saldría del disco de 900
y tocaría la pared en 944), y bajar el `agentRadius` del Giant lo haría atravesar los pilares.

**Verificado en PIE, sin tocar el teclado:**

- El Giant **entra en la arena**: se le midió en `(32.2, -307.5)` = radio 309, a 244 uu del
  jugador. Antes se quedaba clavado en radio 732.
- **Sigue operativo tras la muerte y el respawn del jugador** — se movía mientras existía ya el
  pawn `BP_CombatCharacter_C_1`. El falso "cuelgue al morir" era solo el encierro.
- El log de `CHASE` alterna `Execute` → `OnSuccess` / `OnFail` sin quedarse mudo: el árbol cicla.

### Residuo conocido, no bloqueante

El Giant todavía **deambula hasta el borde** (se le vio en radio 801-822 y, antes del arreglo,
hasta 999, fuera del disco). Es `BP_DA_BossRandomPatrol`, que vaga en radio 500 desde donde
esté, sin ninguna atadura a la arena. Ahora puede volver a entrar, así que no bloquea la POC,
pero un jefe de arena no debería salirse.

Arreglo natural cuando toque: acotar el patrullaje al disco (usar el centro de la arena como
origen en vez de la posición del boss), o subir el umbral de Idle por encima del diámetro de la
arena para que nunca entre en patrulla estando el jugador dentro.

### ⚠️ Pendiente de limpieza

`BP_DA_BossChase` **conserva los `PrintString` de diagnóstico**. Quitarlos cuando se cierre esto.

### ⚠️ `write_graph_dsl` deja nodos huérfanos

Al reescribir el `EventGraph` de `BP_DA_BossChase` se descubrió que el grafo tenía **6 nodos
`AIMoveTo`** y más de 30 `CallFunction`, cuando `read_graph_dsl` solo muestra uno. Las
reescrituras anteriores (700-1000 → 200 → 145) **no borraron los nodos viejos**: quedaron
desconectados. Sigue ahí el `RandomFloatInRange` original.

No compilan —están sueltos— pero engordan el asset y confunden. `read_graph_dsl` solo enseña lo
conectado al evento; para ver la basura hay que usar `find_nodes`.

**Segunda trampa del DSL:** al escribir `(AI|BehaviorTree|FinishExecute true)` el literal
booleano **se guardó como `false`**. Hubo que corregirlo con `set_pin_value` sobre el pin
`bSuccess`. **Releer siempre con `read_graph_dsl` después de escribir.**

**No confundir con el aviso `LogCrowdFollowing: Unable to find RecastNavMesh instance`**: sale
**una sola vez por sesión** al crear el `UCrowdManager` durante el init del mundo, antes de que
la malla Dynamic se genere. Es de temporización y es inofensivo — se le atribuyó importancia
que no tiene.

### Ruta del nodo dentro del Behaviour Tree

Descubierta navegando por propiedades, porque el MCP no tiene toolset de Behaviour Trees:

```
BT_DA_Boss.BT_DA_Boss                        → rootNode
  :BTComposite_Selector_0                    → children[]
    [0] BTComposite_Sequence_1   (Idle)
    [1] BTComposite_Sequence_0   (Chase)
    [2] BTComposite_Sequence_3   (Attack) → children[]
          [0] BP_DA_BossAttack_C_0   ← el nodo con los arrays
          [1] BTTask_Wait_0
```

`ObjectTools.get_properties` / `set_properties` **sí funcionan** sobre estos subobjetos. Lo
que no se puede sigue siendo cambiar la *clase* de un nodo.

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

## Reacción al golpe del Giant

Dos capas, ambas en el `OnHit` de `BP_DA_GiantBoss`:

1. **Stun nativo de DCS.** Se añadió el tag **`HitData.CanStun`** al `FHitData` (antes solo
   llevaba `CanBeBlocked`). `BP_CombatCharacter.TakeDamage` tiene la rama que lo consume y
   llama a `ApplyStatus` sobre el `StatusEffects`. Es lo mismo que hace `MakeMeleeHitData`.
2. **Empujón.** `LaunchCharacter` con
   `Normalize2D(dirección) × KnockbackForce + (0,0,320)`. `KnockbackForce` es variable
   editable, **850** por defecto.

**El `Normalize2D` es imprescindible, no un adorno.** Sin él, usando la dirección 3D entre
orígenes, el vector salía **apuntando hacia abajo**: el origen del Giant está a Z=93.7 (centro
de su cápsula) y el del jugador a Z=-78, así que a corta distancia esa diferencia vertical
domina el vector normalizado. Medido con un print: `X=113 Y=-1166 Z=-766`. El impulso existía
y era grande, pero **clavaba al jugador contra el suelo**, por eso no se veía nada.

También hace falta **`StopAnimMontage` sobre la víctima antes de lanzar**: con root motion
activo, `CharacterMovementComponent` descarta la velocidad y manda la animación. El coste es
perder la animación de reacción de DCS; para un golpe de un gigante, el empujón cuenta mejor
la historia.

### Derribo (falldown) en vez de empujón ✅

El empujón leía como "el jugador saltó hacia atrás", no como "lo machacaron". La culpa era del
`+ (0,0,320)` en Z del `LaunchCharacter`, más el `StopAnimMontage` que deja al personaje en
pose neutra mientras vuela.

**DCS ya tenía la animación.** `M_Backstabbed` no es una animación suelta, son dos encadenadas
en el slot **`FullBody`** (5,46 s en total, con root motion):

| Segmento | Animación | Tramo |
|---|---|---|
| 1 | `Anim_GetHitBackFall` — cae de espaldas | 0 → 2,81 s |
| 2 | `Anim_GetHitBackStandUp` — se levanta | 2,81 → 5,46 s (play rate 1,75) |

**El StatusEffect de Backstab entero NO sirve.** Leído `BP_StatusEffectLogic_Backstab`: es un
derribo **sincronizado** — añade `Activity.IsDisabled.Backstab` a víctima *y* atacante, y un
Timeline (`UpdateApplierPosition`) **teletransporta al atacante** a una posición concreta
respecto a la víctima para que las animaciones casen. Aplicado a un gigante de 5,3 m sería un
desastre. Solo se reutiliza el montage.

Copia propia en `/Game/DarkAngels/Animations/Player/AM_DA_Knockdown` (duplicado de
`M_Backstabbed`). Duplicar conserva los segmentos y el slot.

`OnHit` de `BP_DA_GiantBoss` queda:

```
TakeDamage(...)  ·  CastToCharacter  ·  StopAnimMontage
Animation|PlayAnimMontage(victima, AM_DA_Knockdown)     ← sustituye a LaunchCharacter
```

`LaunchCharacter` **se eliminó**: su velocidad y el root motion del montage se pelean (la misma
razón por la que hizo falta el `StopAnimMontage` en su día), y el root motion del
`GetHitBackFall` ya arrastra al personaje hacia atrás y al suelo. `KnockbackForce` queda sin
uso; se puede borrar la variable.

**Editado por nodos, NO con `write_graph_dsl`.** Ese `EventGraph` contiene
`EventTick → Parent: Tick` y el DSL no sabe crear nodos `Parent:`; reescribirlo lo habría roto.
La secuencia fue: `delete_node` sobre el `LaunchCharacter`, `create_node`
(`Animation|PlayAnimMontage`), dos `connect_pins` y un `set_pin_value` con la ruta del montage.
Verificado que el `Parent: Tick` sigue ahí.

`Animation|PlayAnimMontage` acepta el **Character directamente**, así que no hacen falta los
`GetMesh` → `GetAnimInstance` que usa `Montage_Play`.

### `InPlayRate = 2.0` — por qué ese número

A rate 1.0 el derribo dura 5,46 s y **el boss encadenaba golpes con el jugador en el suelo**
(confirmado jugando). El derribo tiene que ser más corto que el ciclo de ataque del jefe.

Ciclo del jefe, medido sobre el árbol y los montages:

```
[State == Attack] Sequence → BP_DA_BossAttack → Wait 1.00s
SmashAttack1_Montage = 67 frames @ 30 fps = 2,23 s
→ ciclo completo ~3,2 s de un impacto al siguiente
```

| `InPlayRate` | Duración | Margen antes del siguiente golpe |
|---|---|---|
| 1.0 | 5,46 s | **negativo** — encadena |
| 1.5 | 3,64 s | ~0 s, sigue sin dar respiro |
| **2.0** | **2,73 s** | **~0,5 s de pie antes del siguiente impacto** |

Se eligió **2.0**: es el primer valor que abre ventana real. Reparte 1,4 s de caída y 1,3 s de
levantarse, que todavía lee como derribo y no como animación acelerada.

**La otra palanca, si 0,5 s sigue siendo poco margen:** subir el `Wait` del nodo del Behaviour
Tree (rama Attack) de 1,0 s a 1,5-2,0 s. Es el arreglo más de diseño — ralentiza al jefe en vez
de acelerar al jugador — y no toca la animación.

**Descartado:** `ApplyImpulseToSelf` de DCS **no sirve** para esto. Está guardado por
`if IsAnySimulatingPhysics(mesh)`, así que solo actúa sobre un ragdoll — es el impulso de
muerte, no un empujón para un personaje vivo.

**El tag `HitData.CanStun` se quitó**: se probó como sospechoso del empujón fallido y no era
la causa, pero se dejó fuera porque el empujón ya da la reacción. Reañadirlo es trivial si se
quiere también el aturdimiento.

**Lección de método:** el fallo se encontró **imprimiendo el vector**. Las dos hipótesis
previas (root motion, stun) eran plausibles y ambas erróneas. Cuando un nodo se ejecuta pero
no tiene efecto, imprimir sus entradas antes de teorizar sobre el sistema que lo consume.

### Un golpe = un impacto (ya lo garantiza DCS)

No hace falta contador propio. `GetHitActors` / `AddHitActor` del `BP_CollisionHandlerComponent`
mantienen la lista de actores golpeados **indexada por componente de colisión, no por socket**.
El Giant tiene un único componente con 4 sockets, así que los cuatro comparten lista: el primero
que impacta registra al objetivo y los demás quedan descartados. `RefreshHitActors` limpia en
cada `ActivateCollision`.

Por eso `OnHit` —y con él el daño y el empujón— se dispara **una sola vez por ataque**.

## Lock-on — ya venía en DCS, no hubo que añadir nada

`BP_DynamicTargetingComponent` (en `BP_CombatCharacter`) hace todo el trabajo:

```
SphereOverlapActors(jugador, 2500, [Pawn])
  → IsTargetable()  (interfaz I_IsTargetable)
  → ¿en pantalla? → ¿línea de visión libre?
  → elige el más centrado (dot product)
```

Config: alcance **2500**, altura máx **640**, tipos **Pawn**, bloqueo por **WorldStatic**.

### Teclas reales (de `IMC_Player`)

| Acción | Teclado | Mando |
|---|---|---|
| `IA_ToggleTargeting` | **`Tab`** | clic stick derecho |
| `IA_SwitchTargetToLeft` | `Q` | stick derecho izq. |
| `IA_SwitchTargetToRight` | `E` | stick derecho der. |

**No es la rueda del ratón** (esa cambia de arma). `Q` y `E` solo funcionan con un objetivo ya
fijado. Ojo: `Q` también es `IA_UIBack` y `E` también es `IA_Interact` / `IA_UITakeAll`.

En el juego, la tecla `K` abre la lista de controles de DCS.

### El Giant es fijable

Implementa `I_IsTargetable` (`IsTargetable` devuelve `not IsDead`) y tiene un `TargetWidget`
con el `WB_LockIcon` de DCS a 50x50, Z=170, oculto por defecto. `OnSelected` lo muestra y
`OnDeselected` lo oculta.

### ⚠️ ÚNICA modificación hecha a un asset de terceros

```
BP_CombatCharacter → DynamicTargeting → CanCycleDirectionalTargets : false → true
```

Es un booleano sin lógica, para poder alternar objetivos con `Q` / `E`. **Se hizo sobre el
asset de DCS porque el GameMode sigue usando `BP_CombatCharacter`, no
`BP_DA_PlayerCharacter`** (verificado: `DefaultPawnClass = BP_CombatCharacter_C`).

**Una actualización de DCS lo revertirá.** Cuando el GameMode pase a usar
`BP_DA_PlayerCharacter`, conviene mover este ajuste al hijo y devolver el original a `false`.

## Knockdown como StatusEffect propio ✅ + GameMode al hijo

### El problema: `CustomJump` cancela cualquier montage

```
fn CustomJump()
  si IsInState(StateManager, "NewEnumerator1") Y CanJump():
     si hay montage sonando → Montage_Stop(0.25)      ← cancelaba el derribo
     Jump()
```

Está **diseñado** para eso. No mira actividades ni tags, solo esas dos condiciones, así que la
única forma de bloquearlo sin tocar DCS es hacer fallar una: **`CanJump()`**, que se cae si el
movimiento está desactivado.

### Enums descifrados

| Enum | Valores |
|---|---|
| `E_CharacterState` | `NewEnumerator1` = **Idle** · `NewEnumerator6` = **Dead** (lo confirma `Kill`) |
| `E_StatusEffectType` | 0=Undefined · **1=Stun** · **2=Knockdown** · **5=Backstab** |

Cuadra con `Impact` (usa 1 = Stun) y `TryBackstab` (usa 5 = Backstab).

### DCS dejó el hueco `Knockdown` sin implementar

`E_StatusEffectType` declara `Knockdown` pero **no existe ninguna lógica ni data asset** — solo
están las carpetas `Stun/` y `Backstab/`. Es un punto de extensión que el pack dejó abierto.

Rellenado con assets propios en `/Game/DarkAngels/Blueprints/Combat/`:

| Asset | Qué es |
|---|---|
| `BP_DA_StatusEffectLogic_Knockdown` | Copia del Stun **sin VFX**. `OnApplied` → `AddActivity(IsDisabled.Movement)` **y** `AddActivity(IsImmortal)` (i-frames en el piso); `OnRemoved` quita ambas |
| `DA_DA_StatusEffect_Knockdown` | data asset de referencia; en combate se usa `ApplyStatusByParams` con duración **2.39** (montage a rate 2.5) |

### La clave: `ApplyStatusByParams` evita tocar DCS

`BP_StatusEffectsComponent.DefaultStatusEffects` es un mapa `tipo → data asset` que solo tiene
Stun y Backstab. Registrar Knockdown ahí habría exigido modificar `BP_CombatCharacter`.

**No hace falta.** El componente expone `ApplyStatusByParams(Applier, StatusParams)`, que
**recibe el struct directamente y no consulta el mapa**. Desde el `OnHit` del Giant:

```
ApplyStatusByParams(
   GetComponentByClass(victima, BP_StatusEffectsComponent_C),
   self,
   MakeFStatusEffectParams(2.73, BP_DA_StatusEffectLogic_Knockdown_C, NewEnumerator2))
```

**Verificado en PIE** leyendo `ActiveStatusEffects` del jugador en vivo: `type: "Knockdown"`,
`duration 2.73`, `applier` = el Giant, y `logicSpawnedObject` instanciado — o sea que
`EventOnApplied` corrió.

### GameMode al hijo ✅

Aunque `ApplyStatusByParams` ya evitaba tocar DCS, se hizo igual el cambio de GameMode porque
es lo que permite saldar la deuda del lock-on.

**Sin tocar `BP_DCSGameMode`:** se creó `/Game/DarkAngels/Blueprints/World/BP_DA_GameMode` como
**hijo** suyo, con `DefaultPawnClass = BP_DA_PlayerCharacter_C`, y se puso en
`World Settings > GameMode Override` del nivel — que es propiedad del mapa, no de DCS.

Verificado en el log: `LogLoad: Game class is 'BP_DA_GameMode_C'`, y el pawn en PIE es
`BP_DA_PlayerCharacter_C_1`.

### ⚠️ Paso manual pendiente: la deuda del lock-on

`CanCycleDirectionalTargets` sigue en `true` sobre el `DynamicTargeting` de
**`BP_CombatCharacter`** (asset de DCS). Ahora que el GameMode usa el hijo, toca moverlo:

1. Abrir `BP_DA_PlayerCharacter`, seleccionar el componente heredado `DynamicTargeting`,
   marcar `CanCycleDirectionalTargets = true`.
2. Abrir `BP_CombatCharacter` (DCS) y devolverlo a **`false`**.

**El MCP no puede hacerlo:** `StatusEffects` y `DynamicTargeting` son componentes *heredados*,
y no existen como subobjetos del CDO del hijo hasta que se sobrescriben desde el editor.
`ObjectTools` devuelve `is not valid Object` en todas las variantes de ruta.

## Enemigo pequeño desactivado temporalmente ⏸️

El `BP_WarriorAI` estaba ensuciando las pruebas del jefe: es quien mataba al jugador en la
prueba de la derrota, y su daño (20) se confundía con el del Giant (25).

**Apagado sin borrar nada.** `BP_AIOSpawner_C_2` (label `BP_AIOSpawner2`) tiene una propiedad
pensada justo para esto:

```
startSpawningMethod :  SpawnOnGameStart  →  None
```

El enum `E_SpawnerStartSpawningMethod` admite `None | SpawnOnGameStart | SpawnOnRadius |
SpawnOnRegion`. Con `None` el spawner nunca arranca. Verificado en PIE: **cero `BP_WarriorAI`**
en el mundo, y el actor spawner sigue en el nivel.

**Es propiedad de instancia**, así que no toca `BP_AIOSpawner`, que es asset de DCS.

### Para volver a encenderlo

Poner `startSpawningMethod` de nuevo en **`SpawnOnGameStart`**. El resto de su configuración
está intacta y es esta:

| Propiedad | Valor |
|---|---|
| `spawnedActorClass` | `BP_WarriorAI_C` |
| `spawnAmount` | 1 |
| `respawnMethod` | `EachIndividually` |
| `respawnDelay` | 5 |

**Por qué no otras vías:** `isSpawningStopped` es estado de runtime, no configuración, así que
no persiste bien como ajuste de nivel. Borrar el spawner habría roto la referencia por GUID que
`BP_PatrolPath3` tiene con él (ver paso 7). Y ocultar el actor no impide que la IA corra.

## Polish de combate — sesión 2026-08-02 ✅

Trabajo posterior al cierre de la POC v2. Todo en `Content/DarkAngels` salvo el flag
`Debug` del CollisionHandler (se restauró al valor documentado en estas notas).

### Roll = i-frames ✅

`CanBeAttacked` de DCS solo mira `Activity.IsImmortal`. El roll pone estado `Rolling`
(`NewEnumerator5`) pero **no** inmortalidad, y el Giant aplicaba knockdown aunque
`TakeDamage` fallara.

**Fix:**
- Override en `BP_DA_PlayerCharacter` → `CanBeAttacked`: `false` si Dead (`NewEnumerator6`),
  Immortal, o **Rolling** (`NewEnumerator5`).
- En `BP_DA_GiantBoss` OnHit: knockdown solo si `TakeDamage` retorna éxito.

### Giant temblando / ataques cortados ✅

Causa: decorators del BT abortaban Attack al parpadear el State cerca del umbral (~400 uu)
sin histéresis.

**Fix en `BT_DA_Boss`:**
- Attack decorator: `flowAbortMode = None`
- Chase e Idle: `flowAbortMode = Self`

**Fix en `BP_DA_BossChooseState` (histéresis):**
- Entra Attack ≤ 350
- Sale a Chase ≥ 700
- Idle ≥ 1500
- Solo escribe blackboard si el estado relevante cambia

### Knockdown atrasado (~1 s) ✅

Dos causas:
1. `AM_DA_Knockdown` tenía `blendIn = 0.25` y el primer segmento `animStartTime = 0.5`.
2. `TakeDamage` de DCS llama `PlayGetHitAnim` **antes** de que el Giant reproduzca el
   knockdown → reacción competidora.

**Fix montage** (`/Game/DarkAngels/Animations/Player/AM_DA_Knockdown`):
- `blendIn = 0.05`, `blendOut = 0.15`
- Fall `animStartTime = 0`, standup `startPos = 3.307`
- Play rate desde OnHit: **2.5**

**Fix OnHit del Giant** (antes de `TakeDamage`):
```
GetComponentByClass(victima, BP_StateManagerComponent)
→ Cast → AddActivityForDuration(Activity.HasPlayedGetHitEffects, 0.5)
→ TakeDamage(Message)   ; si WasAdded ya es false, DCS no reproduce get-hit
→ si Result: StopAnimMontage → PlayAnimMontage(AM_DA_Knockdown, 2.5)
→ ApplyStatusByParams(..., Duration 2.39, Knockdown logic)
```

Usar **`CanBeAttacked|TakeDamage(Message)`**, no `CanBeAttacked|TakeDamage` (ese resuelve a
la función del Giant y el pin `self` es `BP_BaseAI`, no la víctima).

`BreakHitResult` con bind simple agarra `bBlockingHit`; hay que multi-bind hasta `HitActor`
o conectar el pin 9 a mano.

### Invulnerable mientras está tirado ✅

`BP_DA_StatusEffectLogic_Knockdown`:
- `OnApplied` → también `AddActivity(Activity.IsImmortal)`
- `OnRemoved` → `RemoveActivity(IsImmortal)`

`CanBeAttacked` del player ya rechaza golpes con Immortal (misma vía que el roll).

Duración del status alineada al montage: **2.39 s** (antes 2.73 / 2.98).

### Giant se gira hacia el jugador antes de atacar ✅

`BP_DA_BossAttack` a veces lanzaba el montage mirando a un lado vacío (el player ya estaba
a la espalda). Chase sí actualizaba posición, pero Attack no reorientaba.

**Fix en `BP_DA_BossAttack` EventReceiveExecuteAI** (antes de elegir montage):
```
FindLookAtRotation(GiantLoc, PlayerLoc)
→ SetActorRotation(yaw only; pitch/roll = 0)
→ luego distancia y PlayMontage Short/Long
```

### Traces de debug (esferas rojas) apagados ✅

Documentado arriba: `BP_CollisionHandlerComponent.Debug`. En `DoTraceTest`, si `Debug`:
`DrawDebugType = ForDuration` con color rojo.

**Trampa:** el BP del Giant puede tener `Debug = false` y la **instancia del mapa**
(`L_DA_SeraphArena_POC` → `BP_DA_GiantBoss_C_6.MeleeCollisionHandler`) seguir en `true`.
El CDO del componente también se había quedado en `true`.

**Fix aplicado:**
1. CDO de `BP_CollisionHandlerComponent`: `Debug = false` (valor de estas notas).
2. Template del Giant: `Debug = false`.
3. BeginPlay del Giant: `SetDebug(false)` en `MeleeCollisionHandler` (fuerza la instancia).
4. `BP_CombatCharacter.MeleeCollisionHandler`: `Debug = false` (traces del arma del player).

Para volver a verlos al diagnosticar hits: poner `Debug = true` en el `MeleeCollisionHandler`
del actor que interese (o comentar/quitar el `SetDebug(false)` del BeginPlay).

### Pendientes que siguen abiertos

- Deuda lock-on: `CanCycleDirectionalTargets` mover a `BP_DA_PlayerCharacter`, revertir en DCS
- Quitar PrintString de diagnóstico en `BP_DA_BossChase` (si aún quedan)
- Variedad de ataques: más `ANS_HitBox` en montages `AM_DA_*` (hoy casi todo SmashAttack1)

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
