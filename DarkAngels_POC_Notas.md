# Dark Angels POC — notas de trabajo

Documento de traspaso entre sesiones. Última actualización: 2026-08-03 (POC v3: blockout del
nivel **Malkuth** en `L_DA_Malkuth_POC`).

> **Control de versiones: SÍ lo hay.** Repositorio git en la raíz, remoto
> `github.com/angelsolares/unreal_da`. Es la red principal; los `_Backups/` son secundarios.
>
> **Los tres packs de pago están excluidos** del repo vía `.gitignore`:
> `DynamicCombatSystem/`, `GiantBossProject/`, `Angel_wings_pack/` y
> `DarkAngels/Animations/` (montages derivados). Verificado: `git ls-files` no devuelve ni un
> archivo de ninguno. **Comprobarlo antes de cada push.**

## Estado actual de la POC

| Bloque | Estado |
|---|---|
| Arena, iluminación, NavMesh | ✅ |
| El jefe persigue y ataca (9 montages en rotación) | ✅ |
| Daño en ambas direcciones, muerte y respawn del jugador | ✅ |
| Derribo (Knockdown propio) + tech roll con ventana | ✅ |
| Alas del pack en jefe y enemigos pequeños | ✅ |
| Oleada secuencial: 2 enemigos, uno tras otro, luego el jefe | ✅ |
| SFX: impacto en ambas direcciones + swing del jefe | ✅ |
| **Cero modificaciones a assets de pago** | ✅ |
| Nivel Malkuth: blockout completo en `L_DA_Malkuth_POC` | ✅ (sin iluminación construida) |
| Assets Megascans reales | ❌ los dos packs aún no están descargados |

**Cabos sueltos conocidos** (detallados en sus secciones):

- `AM_DA_DoubleMediumAttack` sin notify de swing; los otros 8 sí lo tienen.
- El jefe se sale de la arena con `RandomPatrol`; puede volver, pero no debería salir.
- `EnemiesSpawned` no se reinicia si el jugador muere a mitad de oleada.
- El sonido al golpear al jefe es siempre de espada, sin leer el tag de tipo de daño.
- `HeavyGoundHitTriple`: tres impactos pero un solo swing y una sola ventana de hitbox.
- `BP_DA_BossChase` conserva `PrintString` de diagnóstico y nodos huérfanos.

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

> ### ⚠️ REGLA: `write_graph_dsl` corrompe los literales `true`
>
> No es un caso aislado. Ha pasado **cuatro veces** hasta ahora, siempre igual: se escribe
> `true` y se guarda `false`. Los `false` sí se respetan.
>
> | Dónde | Pin |
> |---|---|
> | `BP_DA_BossChase` (×2, al instrumentar y al limpiar) | `FinishExecute.bSuccess` |
> | `BP_DA_GiantBoss:HideUntilWaveCleared` | `SetActorHiddenInGame.bNewHidden` |
> | `BP_DA_GiantBoss:CheckWaveCleared` | `SetActorEnableCollision.bNewActorEnableCollision` |
>
> **Procedimiento obligatorio:** tras cada `write_graph_dsl`, releer con `read_graph_dsl` y
> corregir cada `true` perdido con `set_pin_value`. Es silencioso: compila sin errores y el
> comportamiento sale al revés.

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

## SFX del combate contra el Giant

### El pack del Giant NO trae sonido

Cero assets de audio en `GiantBossProject`. Todo el SFX del jefe tiene que salir de la
librería de DCS, que es esta:

```
CUE_HitHands · CUE_HitSword · CUE_HitArrow
CUE_SwingLarge · CUE_SwingSmall
CUE_ShieldBlock · CUE_SwordBlock
CUE_Roll · CUE_PotionHeal · CUE_Explosion · CUE_GroundExplosion
```
(en `DCS/SFX/`)

### Causa 1: faltaba el tag de tipo de daño

`BP_CombatCharacter:PlayGetHitEffects` elige el sonido **por GameplayTag del `FHitData`**:

```
si tiene HitData.DamageType.MeleeWeapon → CUE_HitSword
si tiene HitData.DamageType.Hands       → CUE_HitHands
si no                                    → la variable queda vacía
```

Y luego llama a `PlaySoundAtLocation` con esa variable. **Sin tag no hay sonido, sin más.**

El `FHitData` del Giant solo llevaba `HitData.CanBeBlocked`. Añadido
**`HitData.DamageType.Hands`** (pega con los puños) en **las dos ramas** del `OnHit` — `then` y
`CastFailed`, porque la lógica está duplicada.

### Causa 2: un `AddActivityForDuration` que silenciaba todo

Había un nodo añadiendo `Activity.HasPlayedGetHitEffects` a la víctima **antes** de llamar a
`TakeDamage`, con duración 0,5 s. **Eliminado.**

Final de `BP_CombatCharacter:TakeDamage`:

```
wasAdded = AddActivityForDuration(StateManager, "Activity.HasPlayedGetHitEffects", 0.3)
si wasAdded:
    PlayGetHitEffects(HitData)      ← el sonido
    PlayGetHitAnim(HitDirection)    ← la animación de reacción
```

`AddActivityForDuration` devuelve **`false` si el tag ya estaba**. Es el antirrebote de DCS: en
0,3 s solo el primer golpe reproduce efectos. Al ponerlo por adelantado, `wasAdded` salía
siempre `false` y **se cancelaban sonido y animación a la vez**.

**Por qué quitarlo no rompe la animación:** aunque ahora DCS reproduzca su `PlayGetHitAnim`, el
`OnHit` del Giant hace `StopAnimMontage` + `PlayAnimMontage(AM_DA_Knockdown)` justo después, así
que el derribo se impone igual.

### Causa 3: al golpear TÚ al Giant tampoco sonaba (problema distinto)

**No es el mismo fallo.** Las causas 1 y 2 eran del Giant pegándote a ti. Al revés el motivo es
otro: el sonido de impacto lo reproduce `PlayGetHitEffects`, que vive en `BP_CombatCharacter`.
**El Giant no hereda de esa clase** — implementa su propio `TakeDamage`, que resta vida y poco
más. Nunca hubo sonido en esa dirección.

Añadido en `BP_DA_GiantBoss:TakeDamage`, en la rama de daño aplicado y **antes** de la
comprobación de muerte, para que suene en todos los golpes incluido el último:

```
Interface|TakeDamage(StatsManager, damage)
SetCurrentHealth(...)
PlaySoundAtLocation(CUE_HitSword, GetActorLocation)     ← añadido
si CurrentHealth <= 0: [secuencia de muerte]
```

**Simplificación asumida:** suena siempre `CUE_HitSword`, el arma por defecto del jugador. DCS
elegiría el sonido leyendo el tag `HitData.DamageType.*` del `FHitData` entrante; replicar eso
aquí exigiría una rama y varias referencias de sonido. Si algún día el jugador pelea desarmado
o con arco, el sonido no encajará.

Se reproduce en la **localización del actor**, no en el punto de impacto. Para un bicho de
5,7 m es aceptable; si molesta, sacar el `HitResult` del `BreakFHitData` que ya existe en el
grafo.

### Sonido de swing ✅ — notify por montage

`CUE_SwingLarge` como **AnimNotify `Play Sound`** en cada montage de ataque. Paso manual: el MCP
no toca notifies.

**Es un notify instantáneo, no un NotifyState** — se ve como una marca, no como una barra.

**Colocación:** un poco **antes** de que empiece la ventana del `ANS_HitBox`. El silbido suena
cuando el brazo arranca, no cuando conecta. Con el `HitBox` empezando sobre el frame 29, el
sonido va por el 20-24.

**Cómo replicarlo:** seleccionar la marca, `Ctrl+C`, abrir el siguiente montage (pestaña
`Asset Browser`, sin salir de la ventana), clic derecho en la pista → `Paste`, ajustar y
`Ctrl+S`. Al pegarlo ya viene con el sonido asignado.

**Cómo verificar que llegaron a disco** (sin fiarse de la vista):

```bash
for f in *.uasset; do
  printf "%-32s hitbox:%s swing:%s\n" "${f%.uasset}" \
    "$(grep -aoc ANS_HitBox "$f")" "$(grep -aoc CUE_SwingLarge "$f")"
done
```

Ese chequeo destapó que `AM_DA_DoubleMediumAttack` se había quedado sin el swing aunque sí
tenía el hitbox.

`GroundFallAttack`, `HeavyGoundHitL` y `HeavyGoundHitR` van sin notify de ningún tipo **a
propósito**: están fuera de la rotación.

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

### Deuda del lock-on SALDADA ✅ — cero modificaciones a assets de pago

Era la última atadura con DCS. Resuelta en dos mitades:

**1. Revertir DCS** (hecho a mano). Se quitó el override de `CanCycleDirectionalTargets` en
`BP_CombatCharacter`. Verificado: el CDO del componente
(`BP_DynamicTargetingComponent`) está en `false` y **ningún** Blueprint tiene override — el
nombre de la propiedad no aparece en ningún `.uasset`, comprobado por `grep` binario.

**Con esto, el proyecto ya no modifica ningún asset de terceros.**

**2. Activarlo en el hijo** — y aquí el override desde el editor **no funcionó**. Tres intentos
marcando el checkbox en `BP_DA_PlayerCharacter > DynamicTargeting` no llegaron nunca a disco.

> **Cómo se detectó:** el log solo tenía **un** `LogFileHelpers: Saving Package:
> BP_DA_PlayerCharacter`, con el mismo timestamp que el `.uasset`. Todo lo posterior generaba
> entradas de *compilar*, nunca de *guardar*. **Compilar y guardar son cosas distintas**, y el
> asterisco de la pestaña es la única señal fiable.

**Solución aplicada, sin depender del override:** se asigna en el `BeginPlay` de
`BP_DA_PlayerCharacter` por cirugía de nodos:

```
EventBeginPlay
  Parent: BeginPlay
  SetCanCycleDirectionalTargets(true, GetDynamicTargeting)
```

Editado **por nodos, no con `write_graph_dsl`** — ese grafo tiene `Parent: BeginPlay` y
`Parent: Tick`, y el DSL no sabe crear nodos `Parent:`.

**Verificado en PIE leyendo el pawn en vivo:** `CanCycleDirectionalTargets: true`.

## Tech roll: recuperación rápida con timing

Ventana corta durante la caída del derribo en la que el roll sí funciona, como el "tech" de los
Souls. **Solo fue posible gracias al cambio de GameMode**: toda la lógica vive en
`BP_DA_PlayerCharacter`, sin tocar el input de `BP_CombatCharacter`.

### Punto de partida: el roll ya estaba bloqueado

Comprobado jugando. Importante porque la condición de DCS **no** lo explica sola:

```
fn CanRoll()          →  IsIdleNotFalling()  Y  stamina >= 1
fn IsIdleNotFalling() →  IsInState(Idle)  Y  not IsFalling()
```

El Knockdown solo añade `Activity.IsDisabled.Movement` y **no cambia el estado**, así que sobre
el papel `CanRoll` debería pasar. En la práctica no rueda, así que algo más lo bloquea — no se
investigó porque el comportamiento deseado ya era el correcto. **Se verificó preguntando, no
asumiendo:** la hipótesis inicial (que el roll escapaba libremente) era falsa.

### Piezas

| Pieza | Qué hace |
|---|---|
| `CanTechRoll` (bool en `BP_DA_PlayerCharacter`) | marca si estás dentro de la ventana |
| `ANS_DA_TechWindow` | notify state: `NotifyBegin` → `SetCanTechRoll(true)`, `NotifyEnd` → `false` |
| `TryTechRoll()` | la secuencia del tech |
| Evento `IA_Roll` → `TryTechRoll` | engancha la tecla de esquiva |

`fn TryTechRoll()`:

```
si CanTechRoll:
   SetCanTechRoll(false)                          ← evita encadenar dos techs
   InterruptStatus(StatusEffects, NewEnumerator2) ← quita el Knockdown y devuelve el movimiento
   StopAnimMontage
   Roll()
```

**El orden importa:** `InterruptStatus` va primero porque retira
`Activity.IsDisabled.Movement`; sin eso `Roll()` no pasaría sus propias condiciones.

### Colocación de la ventana

`ANS_DA_TechWindow` sobre el arranque de `AM_DA_Knockdown`, cubriendo **el primer ~30 % del
tramo de caída** ≈ **0,4 s** con el montage a rate 2.0. Si resulta muy difícil, alargarlo; si
sale siempre, acortarlo. Es arrastrar el borde.

### Trampas encontradas

**El `AnimNotifyState` nuevo nace sin grafos.** Sus handlers son *overrides* de función, no
eventos, y `BlueprintTools.create` deja el Blueprint vacío. Solución: **duplicar `ANS_HitBox`**,
que ya trae `Received_NotifyBegin` / `Received_NotifyEnd` / `GetNotifyName`, y reescribirlos.

**Ojo con `GetNotifyName` al duplicar:** la copia seguía reportando `"HitBox"` y en la pista del
montage se veía idéntica a un hitbox real — imposible distinguirlas. Hay que reescribirla.
Quedó devolviendo `"TechWindow"`.

**Orden de argumentos en los setters del DSL:** `(Set<Var> valor target)`, primero el valor y
luego el objetivo. Al revés da `Could not connect pin ... The pins may be incompatible types`.

**El DSL no renderiza el cuerpo de los eventos de Enhanced Input.** `read_graph_dsl` muestra
`(event EnhancedInputActionIA_Roll (...))` sin nada dentro aunque la conexión exista. Para
verificarlo hay que usar `get_node_infos` sobre el nodo llamado y mirar sus `connected_pins`.

### Trampa: los componentes heredados no se leen ni escriben por MCP

`StatusEffects` y `DynamicTargeting` vienen de `BP_CombatCharacter` y **no existen como
subobjetos del CDO del hijo** hasta que se sobrescriben desde el editor. `ObjectTools` devuelve
`is not valid Object` en todas las variantes de ruta probadas:

```
BP_DA_PlayerCharacter.BP_DA_PlayerCharacter_C.DynamicTargeting      ✗
BP_DA_PlayerCharacter.Default__BP_DA_PlayerCharacter_C.DynamicTargeting  ✗
BP_DA_PlayerCharacter.BP_DA_PlayerCharacter_C:DynamicTargeting      ✗
```

**Lo que sí funciona:** leerlos sobre la **instancia en PIE**
(`UEDPIE_0_...:PersistentLevel.BP_DA_PlayerCharacter_C_0.DynamicTargeting`), o sobre el CDO del
**componente** (`BP_DynamicTargetingComponent.Default__BP_DynamicTargetingComponent_C`).

Y para *escribir* en un componente heredado, la vía fiable es **asignarlo en `BeginPlay`** en
vez de pelearse con el override del editor.

## Alas en TODOS los enemigos ✅

### Valores finales, verificados a ojo

| Propiedad del componente `Wings` | Valor |
|---|---|
| `RelativeLocation` | `(0, 0, 0)` |
| `RelativeRotation` | **Pitch `-90`** |
| `RelativeScale3D` | **`1.0`** |
| `Parent Socket` | **`spine_05`** (manual) |

**Escala 1.0 es lo correcto en los dos, y hay una razón:** las alas están hechas para un ángel
humano a escala 1:1 con el esqueleto de Epic. Como el componente cuelga de la malla y **hereda
su escala**, en el Giant (malla ×3) las alas salen ×3 automáticamente, y en el Warrior (malla
×1) salen a tamaño natural. Poner 0.35 o 0.6 fue el error: estaba compensando algo que ya se
compensaba solo.

> **La malla del Giant está a escala 3** (`CharacterMesh0.RelativeScale3D = 3`). Cualquier
> componente que se le cuelgue hereda ese ×3.

**La rotación `Pitch -90` es imprescindible.** Los huesos de la columna de Manny apuntan **a lo
largo del hueso**, o sea hacia arriba, no hacia adelante. Con rotación `0,0,0` las alas salen
disparadas por encima de la cabeza. Es un clásico al colgar cosas de sockets de columna.

### `BP_DA_WarriorAI` — hijo propio, sin tocar DCS

`BP_WarriorAI` es asset de DCS, así que **no se le añadió nada**. Se creó
`/Game/DarkAngels/Blueprints/Characters/BP_DA_WarriorAI` como hijo, con el componente `Wings`,
y el spawner apunta a él (`spawnedActorClass`).

Hereda IA, combate y equipo; solo añade las alas.

### Las alas se DISUELVEN 1 s después del cuerpo

Efecto buscado: que las alas "vivan" un poco más que el cuerpo.

**`StartDissolve` funciona sobre cualquier malla.** Leído `BP_DissolveComponent:StartDissolve`:
no toca parámetros del material existente, **lo sustituye** por instancias dinámicas de
`MI_DissolveEffect` guardando los originales. Por eso da igual que las alas usen `MI_Wings`. Y
`DissolvedComponents` es un **array**, así que admite varias mallas a la vez.

```
TakeDamage (muerte):
   ...
   SetTimerByFunctionName("DissolveWings", 1.0)     ← retardo
   ...
   StartDissolve(Mesh)                              ← cuerpo, inmediato

fn DissolveWings():
   StartDissolve(Wings)
   SetTimerByFunctionName("DestroySelfAfterWings", 2.7)

fn DestroySelfAfterWings():
   DestroyActor
```

**Duración del disolve: 2,5 s exactos.** `DissolveInterpSpeed = 0.4` con
`FInterpTo_Constant` → `1 / 0.4`. De ahí el 2,7 de margen.

### ⚠️ Por qué hubo que mover el `DestroyActor`

`OnDissolveFinished` **se dispara por CADA componente**, no cuando terminan todos — se ve en
`UpdateDissolvedComponents`, que llama al dispatcher dentro del bucle por elemento.

Con el `DestroyActor` colgando de ahí, el cuerpo terminaba a los 2,5 s, destruía el actor y
**cortaba las alas a media disolución**. Se desconectó ese enlace y ahora la destrucción la
programa `DissolveWings` con su propio temporizador.

**Consecuencia:** `OnDissolveFinished` queda vacío. Si algún día se quita `DissolveWings` de la
cadena de muerte, el jefe **no se destruirá nunca**.

Se descartó comparar qué componente terminó porque no hay nodo de igualdad de objetos accesible
por MCP (`Math|Object|...` no devuelve nada, y `Equal(Object)` solo encuentra el de Asserts).

### Alternativa anterior, descartada

Los Warriors desaparecen enteros al morir, pero el Giant **se disuelve**: el cuerpo hace
ragdoll + dissolve y el actor no se destruye hasta `OnDissolveFinished`. Las alas, al ser un
componente aparte, ni ragdollizaban ni se disolvían — se quedaban animando en el aire durante
todo el efecto.

Arreglado en `TakeDamage`, en la rama de muerte, justo después de ocultar la barra de vida:

```
SetVisibility(StatBarsWidget, false, true)
SetVisibility(Wings, false, true)          ← añadido
StopAnimMontage
...
```

Editado **por cirugía de nodos**: ese grafo arrastra cientos de nodos huérfanos de reescrituras
anteriores y un `write_graph_dsl` habría sido una ruleta.

## Oleada: primero los Warriors, luego el Giant ✅

El Giant ya no está en pantalla desde el inicio. Aparece **cuando la oleada de `BP_WarriorAI`
está limpia**.

Implementado **dentro de `BP_DA_GiantBoss`**, sin actores nuevos, para que el `WaveManager`
completo se pueda construir encima sin tirar esto.

| Función | Qué hace |
|---|---|
| `HideUntilWaveCleared()` | En `BeginPlay`: `SetActorHiddenInGame(true)`, quita colisión, **`StopLogic`** del BrainComponent y arranca `SetTimerByFunctionName("CheckWaveCleared", 0.5, looping)` |
| `CheckWaveCleared()` | `GetAllActorsOfClass(BP_WarriorAI_C)`. Si hay > 0 → `WaveStarted = true`. Si hay 0 **y** `WaveStarted` → aparece, recupera colisión, `RestartLogic` y `ClearTimerByFunctionName` |

**La guarda `WaveStarted` es imprescindible.** Sin ella, en el primer frame hay 0 Warriors
—todavía no han spawneado— y el Giant saldría de inmediato. Solo aparece si la oleada
**existió y luego murió**.

**Hay que parar el `BrainComponent`, no solo ocultar.** Si solo se oculta, el boss te persigue
invisible y te pega.

### Ahora es SECUENCIAL: uno, luego otro, luego el jefe

El spawner de DCS **no sabe generar enemigos de uno en uno bajo demanda** — su lógica de spawn
vive en eventos internos y no expone función pública (`list_functions` solo devuelve helpers de
posición y comprobación). Así que se **apagó** (`startSpawningMethod = None`) y la secuencia la
lleva el propio jefe.

`CheckWaveCleared()`, cada 0,5 s:

```
si no queda ningún BP_WarriorAI vivo:
   si EnemiesSpawned < EnemiesToSpawn:
       SpawnActor(BP_DA_WarriorAI) en la posición del spawner
       EnemiesSpawned++
   si no:
       aparece el jefe · RestartLogic · ClearTimer
```

Ya no hace falta la guarda `WaveStarted`: `EnemiesSpawned < EnemiesToSpawn` cubre el arranque
(al principio hay 0 vivos y 0 spawneados, así que genera el primero).

**Sigue usando la posición del `BP_AIOSpawner2`** como punto de aparición, así que mover ese
actor cambia dónde salen.

### Configuración

**`EnemiesToSpawn`** en el **Giant** (Instance Editable) = **2**. Ahí se cambia la cantidad.

> ### ⚠️ Hay que ponerlo en la INSTANCIA, no en la clase
>
> Al añadir la variable, el Giant ya colocado en el nivel se quedó con `0` y en la primera
> prueba el jefe salió de inmediato sin generar enemigos. Es la misma trampa de siempre:
> **los actores colocados no recogen valores nuevos del Blueprint.**
>
> Comprobar siempre leyendo la propiedad **en la instancia del nivel**.

**Verificado en PIE:** un solo `BP_DA_WarriorAI_C_0` en el mundo, `EnemiesSpawned: 1` de `2`, y
`bHidden: true` en el jefe.

**Detalle que se verificó a propósito:** `CheckWaveCleared` busca `BP_WarriorAI_C`, pero el
spawn es de `BP_DA_WarriorAI` (subclase). `GetAllActorsOfClass` **incluye subclases**, así que
los sigue contando. Podría haber roto la secuencia y no lo hace.

### Cabo suelto conocido

Si el jugador muere durante la oleada, **`EnemiesSpawned` no se reinicia**: la secuencia
continúa desde donde estaba en vez de empezar de cero. Para la POC no molesta; si se quiere,
hay que resetearlo al reaparecer.

### Pendiente: el WaveManager de verdad

Lo de arriba resuelve "una oleada y luego el jefe". Para varias oleadas configurables haría
falta un `BP_DA_WaveManager` propio con un array de oleadas (clase + cantidad por entrada). El
diseño acordado: ocultar/despertar el Giant en vez de spawnearlo, porque la instancia colocada
tiene configuración ya verificada (controller de IA, componentes de DCS, barra de vida).

## Alas para los enemigos — placeholder montado

Objetivo: dar sensación de Dark Angels poniendo alas a los enemigos.

### Sobre comprar el pack de alas

Se revisó **"Animated angel wings fifth"** (Nikita00, **$704–$1.005**). Veredicto: **técnicamente
sirve, pero es la compra equivocada**.

- Usarías **~4 de sus 25 animaciones** (idle, aleteo, plegar, desplegar). Todo lo que lo encarece
  —vuelo, 11 dashes, caída, escudo, grito— no se toca.
- El Giant mide 5,3 m: unas alas de ángulo humano hay que escalarlas ×2,8.
- Distribución "Complete project": migración y demo de relleno. Sería el cuarto asset de terceros.
- Y el Giant es el **placeholder** que sustituirá el Serafín.

Para este uso, un asset dedicado de alas ($20–80 en Fab) da lo mismo.

### Lo que ya está montado

`WingPlaceholder_L` y `_R` (`StaticMeshComponent`, cubo de Engine) en `BP_DA_GiantBoss`, con
`set_parent_component` colgando de `CharacterMesh0`:

```
RelativeLocation  (-35, ±55, 410)      ← altura de la espalda del Giant
RelativeRotation  (pitch 20, yaw ±25)
RelativeScale3D   (3.0, 0.15, 1.8)
```

**Sirve para validar el pipeline antes de gastar:** cuando lleguen alas de verdad, se cambia el
componente a `SkeletalMeshComponent` y se le asigna el mesh.

### Pack comprado y migrado ✅

Se compró **"Animated angel wings fifth"**. Migrado a `Content/Angel_wings_pack/` con solo
**12 assets** — sin `ThirdPerson`, sin `Map`, sin las animaciones del `Base_avatar`:

```
Meshes/      SKM_Wings5 · SK_Wings5_Skeleton · PA_Wings5_PhysicsAsset
Animations/  AS__AS_W5_idle_ground · AS__AS_W5_flapping
Materials/   M_Wings · M_Wings_bones · MI_Wings
Textures/    4 (base color, opacity, normal, AO)
```

**Excluido del repo** en `.gitignore` (`Content/Angel_wings_pack/`): es asset de pago.

> **Migrar arrastra las dependencias completas.** Bastó seleccionar las dos animaciones: el
> diálogo *Asset Report* incluyó solo el mesh, el esqueleto, el physics asset, materiales y
> texturas. No hicieron falta dos pasadas.
>
> **`Migrate` está en el submenú `Asset Actions`**, no en el nivel principal del menú
> contextual. En UE5 lo movieron ahí.

### El esqueleto de las alas es independiente ✅

```
Bone (raíz)
├── R_Wing3 → R_Wing3_001 ... _012
└── L_Wing3 → L_Wing3_001 ... _012
```

**Ningún hueso de Manny.** Son un `SkeletalMesh` autónomo que se engancha por socket a
cualquier personaje y **anima por su cuenta**. Era la única duda técnica que quedaba.

**Las dos alas van en un solo mesh**, así que basta **un** `SkeletalMeshComponent`, no dos.

### Componente `Wings` en `BP_DA_GiantBoss`

Sustituye a los dos `WingPlaceholder` (eliminados).

| Propiedad | Valor |
|---|---|
| `SkeletalMeshAsset` | `SKM_Wings5` |
| `AnimationMode` | `AnimationSingleNode` |
| `AnimationData.AnimToPlay` | `AS__AS_W5_idle_ground` |
| `bSavedLooping` / `bSavedPlaying` | `true` / `true` |
| `RelativeLocation` | `(-25, 0, 600)` |
| `RelativeScale3D` | `2.5` |

### ⚠️ Escala y posición SIN AJUSTAR

Los valores de arriba son un punto de partida calculado, **no verificados a ojo**. Con
`Z = 400` y escala 3 los bounds del actor llegaban a `Z = -359`, es decir **las alas colgaban
183 uu por debajo del suelo** (-176,5). Se subió a `Z = 600` y escala 2,5, pero sigue sin
comprobarse en pantalla.

**Ajustar mirando el viewport**, no por bounds: las lecturas de `get_actor_bounds` sobre un
skeletal mesh animado no son fiables para esto (tras el ajuste los bounds en X se *encogieron*,
lo que no cuadra con la geometría). Los dos números a tocar son `RelativeLocation.Z` y
`RelativeScale3D` del componente `Wings`.

**Captura del viewport por MCP: poco útil aquí.** El billboard del `SPAWNER` tapa al Giant y el
viewport tiene una relación de aspecto muy alargada. Y cada `CaptureViewport` devuelve ~1,5 MB
de base64 que hay que volcar a PNG a mano para poder verlo.

### ⚠️ Paso manual: el socket

Están colgando del **componente** de malla, no del **hueso**. `AttachSocketName` **no se puede
escribir por MCP** — vive en el nodo del SCS, no en la plantilla del componente
(`the following properties could not be set`).

En `BP_DA_GiantBoss`, seleccionar cada `WingPlaceholder` y poner **`Parent Socket` = `spine_05`**
(el hueso más alto de la espalda en `SKM_Manny`; la jerarquía llega hasta `spine_05`).

### Trampa: `set_parent_component` y la ruta del padre

El componente hijo se referencia con `..._C:Nombre_GEN_VARIABLE`, pero **el padre hay que
pasarlo por el CDO**:

```
componente: BP_DA_GiantBoss_C:WingPlaceholder_L_GEN_VARIABLE     ✓
padre:      BP_DA_GiantBoss.Default__BP_DA_GiantBoss_C.CharacterMesh0   ✓
padre:      BP_DA_GiantBoss_C:CharacterMesh0                     ✗ "is not valid SceneComponent"
```

## Enemigo pequeño desactivado temporalmente ⏸️ (revertido, ver oleada arriba)

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

## POC v3 — Malkuth, el primer nivel

Nivel nuevo: **`/Game/DarkAngels/Maps/L_DA_Malkuth_POC`**. `L_DA_SeraphArena_POC` se conserva
intacto como banco de pruebas de combate (verificado `is_dirty = false` tras duplicar).

### Por qué Malkuth y qué significa

Malkuth es la **décima y última sefirá** del Árbol de la Vida cabalístico: el *Reino*, el mundo
material, donde el cielo toca la tierra. Es el suelo sobre el que se apoya todo el Árbol. Es la
sefirá **cuatripartita**: la única con cuatro colores en la escala del Golden Dawn — **citrino,
oliva, rojizo (russet) y negro** — uno por cada uno de los Cuatro Mundos, y por extensión los
cuatro elementos (aire, agua, fuego, tierra). Sus títulos son todos de umbral: *la Puerta*, *la
Puerta de la Muerte*, *la Puerta de las Lágrimas*, *la Puerta de la Justicia*. Su arcángel es
**Sandalfón**; su símbolo ritual, el **altar del doble cubo**. Su qliphá (cara oscura) es
**Nehemot / Lilit**, «la Reina de la Noche», reino de susurros, pesadillas e ilusiones.

Por eso es el nivel 1: **es el único sitio por donde se puede empezar a subir.** De Malkuth solo
sale un camino, la **senda 32 (Tau)**, que lleva a Yesod. El juego entero puede mapearse al Árbol:
10 niveles, uno por sefirá.

### Traducción a diseño de nivel

| Idea cabalística | Cómo se lee en el nivel |
|---|---|
| Malkuth = el mundo material, lo mundano | Una **aldea medieval** corriente, no un templo celestial |
| Sefirá cuatripartita, 4 colores / 4 elementos | La aldea se parte en **cuatro barrios**, uno por color-elemento |
| Cruz de brazos iguales, símbolo de Malkuth | Las calles de los barrios convergen en la plaza |
| Altar del doble cubo | **Monolito 3×3×6 m en el centro exacto de la plaza** |
| Las 10 sefirot | **Círculo de 10 pilares** rodeando el altar, abierto al norte |
| «La Puerta» (título de Malkuth) | El **templo sellado** al norte: la salida hacia Yesod |
| Senda 32 (Tau), única salida | La **escalinata procesional** del eje +Y, plaza → templo |
| Nehemot, la Reina de la Noche | Justificación de fondo para los enemigos alados y la paleta oscura |

**El eje sur→norte lo cuenta todo de un vistazo:** el jugador entra por la puerta sur, camina por
la avenida, cruza el círculo de las diez sefirot con el altar en medio, sube la escalinata Tau y
se encuentra la Puerta cerrada. Todo alineado en X = 0.

### Los cuatro barrios

Cada uno en una diagonal, arranque a radio 2100 del centro, calle propia hacia la plaza.

| Barrio | Color de Malkuth | Ángulo | Hito que cierra la calle |
|---|---|---|---|
| **Aire** | Citrino | 45° | Campanario (4×4×16 m) + plaza de mercado |
| **Fuego** | Rojizo | −45° | Fragua con chimenea (cilindro 11 m) + casa quemada |
| **Agua** | Oliva | −135° | Pozo + molino (4×4×12 m) |
| **Tierra** | Negro | 135° | Cripta + osario + 8 lápidas — *la Puerta de la Muerte* |

Cada barrio tiene un **pedestal** (cilindro, u=550 sobre su calle): ahí va el fragmento/llave que
abre la Puerta. Encaja con el sistema de oleadas que ya existe: limpiar barrio → coger fragmento
→ cuatro fragmentos → se abre la Puerta → el jefe.

### Cotas y medidas reales

Todo se calibró para **reutilizar la cota de suelo de la arena, `Z = -176.5`**, y así no invalidar
ni el `PlayerStart`, ni la Z del jefe, ni nada ya verificado.

| Pieza | Valor |
|---|---|
| Suelo (`SM_MK_Ground`) | Cubo `scale 140,140,4`, centro Z `-376.5` → cara superior **-176.5** |
| Plaza (`SM_MK_PlazaFloor`) | Cilindro `scale 28,28,0.4` → **radio 1400**, a ras (centro Z -196.5) |
| Altar doble cubo | 2 cubos `scale 3,3,3` a Z `-26.5` y `273.5` → 300×300×600 |
| Círculo de las 10 sefirot | Cilindros `scale 2,2,8` a **radio 1300**, cada 36° desde 0° |
| Escalinata Tau | 8 peldaños, huella 150, contrahuella **37.5**, ancho 2000, Y de 1600 a 2800 |
| Plataforma del templo | `scale 44,18,3`, centro `(0, 3700)` → cara superior **+123.5** |
| Muralla | **radio 5200**, 16 tramos de 22.5°, `scale 21,3,8`; falta el tramo 12 = puerta sur |
| `PlayerStart` | `(0, -3400, -71.5)`, yaw 90 (mira al eje Tau) |
| `NavMeshBoundsVolume` | `(0, 0, -100)`, `scale 56,56,4` → XY ±5600, Z -500..300 |
| `BP_AIOSpawner2` | `(0, 900, -50)` — punto de aparición de la oleada, dentro de la plaza |
| `BP_DA_GiantBoss` | sin tocar: `(0, 600, 93.74)`, dentro del disco de la plaza |

**97 actores `SM_MK_*`**, organizados en el Outliner: `Malkuth/00_Terreno`, `01_Plaza`,
`01_Plaza/Sefirot`, `02_SendaTau`, `03_TemploPuerta`, `03_TemploPuerta/LaPuerta`,
`04_Barrios/<Elemento>_<Color>`, `05_Muralla`.

Borrados de la copia: `BP_DemoRoom` (la sala cerrada del demo, que era suelo *y* paredes) y los
10 `StaticMeshActor` de la arena (disco + 8 pilares + `SM_BoxPlaceholder`).

### ⚠️ Restricción de diseño heredada: el jefe no cabe por todas partes

El agente de navegación del Giant es `AgentRadius 102` / `AgentHeight 528`. Ya se aprendió por
las malas (ver *«los cubos del borde bloquean al Giant»*): necesita **≥ 204 uu de hueco libre**
más margen de voxelización, y en la práctica 258 no bastaban.

Comprobado en este blockout:

- Círculo de las sefirot: hueco entre pilares = `2·1300·sin(18°) − 200` = **603 uu** ✅
- Calles de los barrios: **700 uu** entre hileras de casas ✅
- Pórtico del templo: columnas interiores a ±700 → hueco **1100 uu** ✅

**Regla para todo lo que se coloque a partir de ahora:** ningún paso por el que deba circular el
jefe puede quedar por debajo de ~400 uu libres. Los interiores de casa y los callejones son
territorio del `BP_DA_WarriorAI` (`AgentRadius 50`), no del jefe.

### Verificado

| Comprobación | Resultado |
|---|---|
| Trazas verticales en plaza, calle sur, barrio Aire y anillo exterior | **-176.5** en todas |
| Traza sobre la plataforma del templo | **+123.5** |
| `RecastNavMesh-Default` / `-Giant` | ambas siguen en **`Dynamic`** |
| `WorldSettings.defaultGameMode` | `BP_DA_GameMode_C` (el override sobrevivió al duplicado) |
| Ningún actor por encima de Z = 1600 | ✅ nada atraviesa el cielo |
| `L_DA_SeraphArena_POC` tras duplicar | `is_dirty = false`, intacto |

### Pendiente en Malkuth

- **Construir la iluminación** (`Build > Build Lighting Only`) y **guardar**: mismo caso que la
  arena, el `_BuiltData` no se duplica. Hasta entonces se ve blanco plano. **El MCP no puede
  lanzar el build.**
- Ver el NavMesh en verde con `P`. El volumen es ahora 11200×11200: puede tardar en generarse.
- Añadir un `LightmassImportanceVolume` — con un nivel de este tamaño ya no es opcional.
- La iluminación heredada (2 SpotLight de la sala del demo) no tiene sentido a cielo abierto:
  hay que rehacerla.

### Límites del MCP encontrados aquí

- **No hay tool para crear un nivel nuevo.** `SceneTools` solo tiene `load_level`. La vía es
  `AssetTools.duplicate` sobre el `.umap`.
- `AssetTools.duplicate` deja el asset **sucio**, y `load_level` se niega a cargar un nivel con
  cambios sin guardar. Hay que `save_assets` en medio.
- `ObjectTools.get_properties` usa los parámetros **`instance`** y **`properties`**, no
  `object` / `property_names`.
- `EditorAppToolset.CaptureViewport` sigue devolviendo ~1,5 MB de base64: inviable en
  conversación. Para ver el nivel, mejor mover la cámara del viewport con `SetCameraTransform` y
  mirar el editor.

## Assets reales — Megascans (PENDIENTE de descarga manual)

Los dos packs elegidos **no están instalados**: `Content/` solo tiene `DynamicCombatSystem`,
`GiantBossProject`, `Angel_wings_pack` y `DarkAngels`.

| Pack | Uso previsto en Malkuth |
|---|---|
| **Medieval Village Megascans Sample** (gratis) | Los 4 barrios, la muralla y las calles |
| **Goddess Temple Megascans Sample** (gratis) | El templo del norte y la Puerta |

**Hay que descargarlos desde Fab / Epic Games Launcher** — no se puede por MCP ni por línea de
comandos. Ambos son *proyectos completos*, no packs de assets: lo correcto es abrirlos aparte y
**migrar** solo lo necesario a `Content/`, igual que se hizo con las alas.

**Ojo con la versión:** el *Goddess Temple* es de la época de UE 4.25 (usa Runtime Virtual
Textures y ray tracing). Puede pedir conversión al abrirlo, y sus materiales RVT quizá haya que
retocarlos en 5.8. El *Medieval Village* es de UE5 y no debería dar problema.

**Son gratuitos, pero siguen siendo assets de terceros:** aplica la regla del proyecto —
carpeta propia, no tocar los originales, y el trabajo nuevo en `Content/DarkAngels`. Decidir
antes de migrar si van al repo o al `.gitignore`; al ser gratis se pueden subir, pero engordan
mucho el repositorio.

### Cómo sustituir el blockout por los assets reales

El blockout está hecho **solo con `/Engine/BasicShapes/Cube` y `Cylinder`**. Cada caja marca un
volumen y una orientación ya validados contra el NavMesh, así que el reemplazo es mecánico:
localizar el actor por su label `SM_MK_*`, colocar la malla real en su transform y borrar la caja.
El orden sensato es plaza → senda Tau → templo → barrios → muralla.

## Migración de los Megascans — hecha ✅

`Migrate` desde `D:\Game Projects\Mega Scans\MedievalVillageMegascansS` (abierto con 5.8) hacia
`Content/`. Se conserva la estructura de origen **a propósito**: es lo que permite copiar
actores desde el nivel del sample y pegarlos en Malkuth.

| Carpeta | Tamaño | Assets |
|---|---|---|
| `Content/Meshes` (incl. `Houses` 2,7 GB / 387 assets) | 4,1 GB | 532 |
| `Content/Megascans` (`3D_Assets` 2,6 GB · `Surfaces` 669 MB) | 3,3 GB | 302 |
| `Content/Materials` | 356 MB | 37 |
| `Content/PhysMat` · `Content/Effects` | 440 KB | 4 |

Verificado: **39 dependencias comprobadas sobre 18 mallas de muestra, cero rotas**.
`MapCheck: 0 Error(s), 0 Warning(s)`. Nivel intacto: 119 actores, 97 `SM_MK_*`.

Todo excluido del repo en `.gitignore`. **No renombrar ni mover esas carpetas** o se rompe el
copiar/pegar desde el sample.

### ⚠️ Al sample le faltaba el `.uproject`

`MedievalVillageMegascansS/` solo tenía `Content`, `DerivedDataCache`, `Intermediate` y `Saved`.
Se le escribió a mano un `MedievalGame.uproject` con `EngineAssociation: 5.8`.

### ⚠️ No hay casas prefabricadas — es un kit modular

No existe ningún `SM_House_XX` completo. Las casas del sample se montan pieza a pieza
(`SM_BoardWall`, `SM_GableFront_*`, `SM_HBeam_*`, `SM_Roof_*`, cartas de paja). Por eso su nivel
tiene **6208 actores**.

**La vía es copiar/pegar actores entre proyectos**: seleccionar los actores de una casa en
`MedievalVillage_P_WP`, `Ctrl+C`, y `Ctrl+V` en `L_DA_Malkuth_POC`. Funciona porque Unreal
serializa los actores como texto y las rutas de las mallas coinciden.

### ⚠️ `MI_Cobblestone` depende de una RVT de landscape

```
MI_Cobblestone → M_BlendMaster → Materials/Landscape/RVT/RVT_Landscape_01 (+ _Height_01)
```

Los assets están, pero Malkuth no tiene landscape ni `RuntimeVirtualTextureVolume`, así que se
verá mal. Hará falta una instancia propia en `DarkAngels/Materials` sin la parte de blend.
**Las mallas de casas están limpias** — `SM_GableFront_01` solo depende de sus tres `MI_`.

## Salto a SM6 + Lumen + Nanite

### El proyecto corría en Shader Model 5

Heredado de ser una plantilla de época UE4: `Config/DefaultEngine.ini` **no tenía sección
`[/Script/WindowsTargetPlatform.WindowsTargetSettings]`**, así que caía en SM5 por defecto.

```
LogRHI: Using Default RHI: D3D12
LogCsvProfiler: Metadata set : rhifeaturelevel="SM5"
LogD3D12RHI: Skipped NVAPI RT queries since the feature level is below SM6
LogShaderCompilers: Compiling shader autogen file: .../ShaderAutogen/PCD3D_SM5/...
```

Consecuencia leída en vivo con `SearchCVars`:

| CVar | Valor antes |
|---|---|
| `r.DynamicGlobalIlluminationMethod` | 0 = None |
| `r.Shadow.Virtual.Enable` | 0 |
| `r.ReflectionMethod` | 2 = SSR |
| `r.AllowStaticLighting` | 1 |

**No era la escalabilidad** (estaba en Epic, `@3`, con `r.Lumen.DiffuseIndirect.Allow:1`) ni el
hardware targeting (`Desktop` / `Maximum`).

### Lo que lo decidió: Nanite estaba apagado

`naniteSettings.bEnabled = true` en `SM_GableFront_01`, `SM_CastleWall` y `SM_GraveA_00`.
**Nanite requiere SM6**, así que los 8 GB de Megascans se dibujaban con su malla *fallback*.

### Por qué Lumen y no seguir horneando

Contradice la decisión de la arena (*«Por qué NO se puede pasar las luces a Movable»*), y con
razón: ahí era una sala de 41 mappings que horneaba en 3 s. Malkuth con casas reales son miles
de mappings, y las mallas de Megascans traen UVs de lightmap pobres o inexistentes.

Además el sample del Medieval Village es un proyecto 5.3 **construido sobre Lumen + Nanite +
VSM**: sin eso sus materiales se ven planos hagas lo que hagas.

Equipo: **RTX 4070 (12 GB) + i7-14700F**. De sobra.

### Escrito en `Config/DefaultEngine.ini`

```ini
[/Script/WindowsTargetPlatform.WindowsTargetSettings]
DefaultGraphicsRHI=DefaultGraphicsRHI_DX12
-D3D12TargetedShaderFormats=PCD3D_SM5
+D3D12TargetedShaderFormats=PCD3D_SM6
-D3D11TargetedShaderFormats=PCD3D_SM5

[/Script/Engine.RendererSettings]
r.DynamicGlobalIlluminationMethod=1
r.ReflectionMethod=1
r.Shadow.Virtual.Enable=1
r.GenerateMeshDistanceFields=True
```

**`r.AllowStaticLighting` se deja en 1 a propósito:** así `L_DA_SeraphArena_POC` conserva sus
lightmaps horneados y no se rompe. Lumen añade GI dinámica encima, no la sustituye.

`r.GenerateMeshDistanceFields=True` es requisito de Lumen por software.

**Revertir:** `git checkout Config/DefaultEngine.ini` — pero obliga a otra recompilación completa.

### Coste asumido

Cambiar de SM5 a SM6 **invalida el caché de shaders entero**: DCS, GiantBossProject y los 8 GB
nuevos. Media hora a una hora con 14 workers. Es de una sola vez.

### Si tras reiniciar sigue en SM5

`Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini` guarda `PreviewFeatureLevel=3`
(3 = SM5, 4 = SM6). Tiene `bPreviewFeatureLevelWasDefault=True`, así que debería recalcularse
solo. Si no: botón **Platforms** de la barra de herramientas → **Preview Rendering Level** →
*Shader Model 6*.

### SM6 verificado en vivo ✅

Tras reiniciar, leído con `SearchCVars` y del log:

| Comprobación | Antes | Ahora |
|---|---|---|
| `rhifeaturelevel` | `SM5` | **`SM6`** |
| `ShaderAutogen` | `PCD3D_SM5` | **`PCD3D_SM6`** |
| `r.DynamicGlobalIlluminationMethod` | 0 | **1 = Lumen** |
| `r.ReflectionMethod` | 2 = SSR | **1 = Lumen** |
| `r.Shadow.Virtual.Enable` | 0 | **1** |
| `r.GenerateMeshDistanceFields` | — | **1** |
| `r.Nanite` | inactivo | **1** |
| `r.AllowStaticLighting` | 1 | **1** (la arena conserva su horneado) |

El aviso *«Missing Project Settings / SM6 is required to use Nanite»* ya no aparece. Es el
indicador definitivo.

> ### La estimación de «media hora a una hora» de recompilado fue errónea
>
> No recompiló nada visible. Tres motivos: UE5 compila **bajo demanda**; el
> `DerivedDataCache` del proyecto son 1,6 MB (el grueso vive en la caché global compartida, que
> ya tenía permutaciones SM6); y Malkuth solo tiene primitivas de Engine. **La compilación
> pesada llegará al colocar la primera malla de Megascans.**

## Iluminación de Malkuth reconstruida para Lumen

El nivel heredó de la sala del demo un montaje de UE4 que con Lumen no funciona.

### Lo que había y por qué no servía

| Actor | Problema |
|---|---|
| `AtmosphericFog` | **Actor deprecado de UE4: en UE5 no renderiza nada.** Borrado |
| `BP_Sky_Sphere` | Skybox estático; no alimenta a Lumen y tapa a la `SkyAtmosphere` |
| **Ninguna `SkyLight`** | Sin ella Lumen no tiene ambiente de cielo: todo lo que no toca el sol queda casi negro |
| `LightSource` | `Stationary` — no lo gestiona Lumen |
| 2 × `SpotLight` | 100.000 de intensidad apuntando a una sala que ya no existe |
| `PostProcessVolume` | **Exposición clavada**: ver abajo |

### ⚠️ El hallazgo importante: la exposición estaba bloqueada

`PostProcessVolume_1` (`bUnbound = true`, afecta a todo el mundo) traía:

```
autoExposureMinBrightness = 0.5
autoExposureMaxBrightness = 0.5     ← min == max: exposición FIJA
```

Calibrada para la sala oscura del demo. A cielo abierto eso revienta la imagen a blanco. Es
parte de por qué el blockout se veía plano incluso antes de Lumen.

**Unidades:** `r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange = 0`, o sea **legacy de
UE4** (brillo lineal), **no EV100**. No confundir las escalas al tocar estos valores.

Puesto en **`0.03` – `4.0`** (auto-exposición desbloqueada). Cuando el arte esté fijado conviene
volver a bloquearla para poder juzgar la iluminación.

### Montaje actual — carpeta `Malkuth/06_Iluminacion`

| Actor | Config |
|---|---|
| `Light Source` | **Movable**, `bAtmosphereSunLight = true`, pitch **-25** yaw **140** (sol bajo, sombras largas cruzando la plaza) |
| `MK_SkyAtmosphere` | por defecto |
| `MK_SkyLight` | **Movable**, `sourceType = SLS_CapturedScene`, **`bRealTimeCapture = true`**, intensidad 1.0 |
| `MK_HeightFog` | `bEnableVolumetricFog = true`, densidad 0.025, falloff 0.15, a cota de suelo |

En `Malkuth/99_HeredadoDelDemo`, apagados pero **no borrados** (reversible con un clic):

- `SpotLight` y `SpotLight2` → `bAffectsWorld = false`
- `SkySphere` → `SkySphereMesh.bVisible = false`

**Total: 121 actores.**

### Trampas del MCP encontradas aquí

- `ObjectTools.set_properties` usa **`instance`** y **`values`** (un *string* JSON), no
  `properties`. `get_properties` sí usa `properties`.
- **`bUsedAsAtmosphereSunLight` no existe** en 5.8. La propiedad es **`bAtmosphereSunLight`**.
- **`bHiddenEd` no se puede escribir** (es transitoria del editor). Para ocultar algo en el
  viewport hay que apagar la **visibilidad del componente** (`bVisible = false` sobre
  `SkySphereMesh`), no el actor.
- **`add_to_scene_from_class` falla si PIE está corriendo** (`Cannot create actors while PIE is
  active`). Los `set_properties` sí pasan.
- Para editar el `PostProcessVolume` hay que **leer el struct `settings` entero, modificarlo y
  reescribirlo completo**, activando además el `bOverride_<Campo>` correspondiente.

### Pendiente de vista humana

- La intensidad del sol sigue en **3,14** (valor heredado de UE4, sin unidades). Con la
  auto-exposición desbloqueada importa poco, pero si al mirar sale lavado o gris, es la primera
  palanca.
- El ángulo del sol (-25 / 140) es un punto de partida, no una decisión de arte.

## Material de blockout world-aligned ✅

### Por qué no se pueden "pintar" los Megascans sobre los cubos

Duda que salió y conviene dejar zanjada: lo migrado son **mallas escaneadas**, no un pack de
texturas. Un `MI_Cobblestone` sobre un cubo de Engine de 140 m se estira: las UVs de un cubo van
de 0 a 1 por cara. **Los cubos se sustituyen, no se pintan.**

Pero ver todo blanco impide juzgar volúmenes, así que se montó la solución estándar para
graybox: un material de **proyección triplanar** que ignora las UVs y proyecta según la posición
en el mundo. Densidad de téxel correcta sea cual sea la escala de la caja, y desechable.

### `/Game/DarkAngels/Materials/M_DA_Blockout`

Construido entero por MCP con `MaterialTools`:

```
BaseColorTex (TextureObjectParameter) ┐
TextureSize  (Scalar, 256 por defecto)┼→ WorldAlignedTexture ─[XYZ Texture]→ Multiply → BaseColor
                                      │                                        ↑
Tint (VectorParameter) ───────────────┼────────────────────────────────────────┘
NormalTex (TextureObjectParameter)    ┼→ WorldAlignedNormal  ─[XYZ Texture]→ Normal
Roughness (Scalar, 0.85) ─────────────┴──────────────────────────────────────→ Roughness
```

Funciones de Engine usadas:
`/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture` y
`.../WorldAlignedNormal`.

**Pines de `WorldAlignedTexture`:** entradas `TextureObject`, `TextureSize`, `WorldPosition`,
`Export Float 4`, `World Space Normal`, `ProjectionTransitionContrast`; salidas `XY Texture`,
`Z Texture`, **`XYZ Texture`** (la buena).

### 8 instancias — y los cuatro colores de Malkuth

| Instancia | Textura | Tamaño | Tinte | Actores |
|---|---|---|---|---|
| `MI_DA_BO_Suelo` | `MossyGround` | 800 | — | 1 |
| `MI_DA_BO_Plaza` | `Cobblestone` | 300 | — | 1 |
| `MI_DA_BO_Muralla` | `CastleWall` | 450 | — | 18 |
| `MI_DA_BO_Templo` | `JapaneseShrineStoneFloorA` | 300 | cálido | 33 |
| `MI_DA_BO_Aire` | `StoneWall` | 260 | **citrino** `1.00, 0.94, 0.70` | 9 |
| `MI_DA_BO_Fuego` | `StoneWall` | 260 | **rojizo** `0.88, 0.55, 0.40` | 9 |
| `MI_DA_BO_Agua` | `StoneWall` | 260 | **oliva** `0.70, 0.78, 0.55` | 9 |
| `MI_DA_BO_Tierra` | `StoneWall` | 260 | **negro** `0.40, 0.40, 0.45` | 17 |

Los cuatro barrios llevan literalmente la escala de color de la décima sefirá. **97 de 97
actores con material**, ninguno sin asignar.

Se evitó `MI_Cobblestone` del pack a propósito: arrastra la RVT de landscape. Aquí solo se usan
sus **texturas**, no su material.

## Goddess Temple — inventario (SIN migrar todavía)

`D:\Game Projects\Mega Scans\GoddessTempleMegascansSam` · `GoddessTempleMegascansSam.uproject`
· **`EngineAssociation: 4.25`** → hay que abrirlo con 5.8 y convertir copia. **8,0 GB.**

| Carpeta | Tamaño |
|---|---|
| `Megascans/3D_Assets` (38 assets) | 4,7 GB |
| `CustomAssets` | 1,5 GB |
| `Megascans/3D_Plants` | 1017 MB |
| `Megascans/Surfaces` (5) · `Atlases` | 449 + 357 MB |
| `Maps` · `Masters` · `FX` · `HDRI` · `Blueprints` | ~80 MB |

### Lo que encaja con Malkuth

| Asset | Sustituye a |
|---|---|
| **`RomanColumn`** + **`RomanMarbleCapital`** | Las 4 columnas del pórtico **y los 10 pilares de las sefirot** |
| **`RomanStoneFloor`** | Plataforma del templo y losas de la plaza |
| **`OldChapelArch`** | El arco de **la Puerta** |
| **`ChapelStructure`** · `BrokenChapelStoneWall` | Muros del templo |
| **`CastleStairs`** | La escalinata de la senda Tau |
| **`AngkorWatTempleStones`** | Sillería y **el altar del doble cubo** |
| **`SM_RomanHead`** (`CustomAssets/HeadTextures`) | Cabeza colosal. Candidata a pieza central de la plaza |
| `JapaneseBell` | El campanario del barrio del Aire |
| `Candle` · `IncenseBurner` · `OldCandleHolder` · `VintageOilLamp` · `OldAlembic` · `OldJar` | Props rituales del altar — encajan con el tono |
| `Cobblestone` · `Chain` · `ChiseledRock` · `CrackedRock` · `RockGranite` · `RockSandstone` | Relleno |
| `Surfaces`: `IcelandicStonyGround` · `QuarryGroundGravel` · `RockCliffLayered` · `Sand` | Suelos |

### No migrar

`Maps/` · `FX/` · `Cinematics/` · `Blueprints/` · `3D_Plants` (1 GB) · `Atlases` (357 MB) ·
`CustomAssets/Quarry` (820 MB, es la cantera del demo) · `CustomAssets/CommentaryBox` ·
`CustomAssets/ScaleMan`.

**`Masters/` sí hace falta** (23 MB): son los master materials de los que cuelgan los `MI_`.

### ⚠️ Riesgo específico de este pack

Es de **4.25** y fue el sample con el que Quixel estrenó las Runtime Virtual Textures. Espera
más materiales con dependencia de RVT que en el Medieval Village. Si una malla sale negra,
mirar ahí primero. Y **verificar que el `.uproject` sigue en su sitio** tras crearlo: al
Medieval Village le faltaba.

## Primeras mallas reales en Malkuth ✅

**162 actores.** Cuatro bloques del blockout sustituidos por Megascans.

| Bloque | Cajas fuera | Mallas dentro |
|---|---|---|
| 10 pilares de las sefirot | 10 cilindros | **40** (`SM_MK_Sefirah_NN_{Base,Fuste,Alto,Capitel}`) |
| Altar del doble cubo | 2 cubos | **12** (`SM_MK_Altar_HN_M`) |
| Escalinata Tau | 8 peldaños | **9** (`SM_MK_TauStair_K_J`) |
| Lápidas del barrio de Tierra | 8 cubos | **8** (`SM_MK_Tierra_Tumba_N`) |

### ⚠️ Las dos mallas que colgaron el editor

```
SM_RomanColumnHigh_01 →   559.991 triangulos, build 2942 MB
SM_RomanColumnHigh_02 → 1.099.989 triangulos, build 2942 MB
```

Todo lo demás del pack está entre **4 y 39 MB** de build. Instanciar esas dos dejó el editor
bloqueado ~40 min con un núcleo al 100 %, hasta que hubo que matar el proceso. **No usarlas
nunca**: no aportan nada frente a `SM_RomanColumn_01..06` y **no traen Nanite**.

> ### REGLA: medir con `get_asset_tags`, nunca instanciando
>
> `AssetTools.get_asset_tags` lee el **registro de assets sin cargar la malla**, así que no
> dispara ningún build. Devuelve `ApproxSize`, `Triangles`, `NaniteEnabled`,
> `BuildRequiredMemoryEstimate`, `Materials`, `UVChannels`, `LODs`…
>
> **Antes de instanciar cualquier Megascan, mirar ahí.** Cualquier cosa por encima de ~100 MB de
> `BuildRequiredMemoryEstimate` se instancia sola y cronometrada, o no se instancia.
>
> Trampa del DSL: el valor devuelto es un `_StrictDict`. **`d.get(k, defecto)` falla en
> silencio**; hay que comprobar `k in list(d)` y usar `d[k]`.

> ### REGLA: un solo editor de Unreal abierto
>
> Con el sample del Medieval Village abierto a la vez quedaban **4,6 GB libres de 31,8**. Un
> build de Nanite pide ~3 GB y una textura 4K otros 1,2. Cerrando el sample subió a 14,9 GB.

### Los Megascans del Goddess Temple son fragmentos, no un kit

Medido, no supuesto. Ninguna pieza es una columna de templo:

| Malla | Tamaño real (cm) |
|---|---|
| `SM_RomanColumn_05` | 55×55×**213** |
| `SM_RomanColumn_02` | 31×31×**187** |
| `SM_RomanColumn_06` | 40×40×**161** |
| `SM_RomanMarbleCapital` | 37×37×14 |
| `SM_CastleWall` | 363×90×**41** ← es una losa tumbada, no un muro |
| `SM_CastleStairs` | 727×145×94 |
| `SM_OldChapelArch` | 250×84×256 |

**Ninguna malla del Goddess Temple trae Nanite** — el pack es de 4.25, anterior a Nanite. Solo lo
tienen las del Medieval Village.

Consecuencia de diseño: para el **pórtico y los muros del templo** hay que copiar/pegar desde el
nivel del sample, igual que con las casas. Solo lo apilable en vertical se puede componer por MCP.

### Cómo se compuso cada pilar de las sefirot

Cuatro piezas, escala **1,5**, estrechándose al subir, con **15 cm de solape** entre tambores
(son fragmentos rotos: a tope se ven las juntas). Yaw distinto por pieza para que los diez no
parezcan clonados. Rematan a **Z = 647** (los cilindros llegaban a 623).

**Todos los pivotes de estas mallas están en la base y centrados en XY** — verificado uno a uno
con `get_actor_bounds` sobre una instancia temporal. Excepción: `SM_GraveA_01` tiene el pivote
desplazado **74 cm en X**; por eso se descartó y se usaron `SM_GraveA_00` y `SM_GraveB`.

### La escalinata: dos fallos y cómo se detectaron

**1. La malla estaba del revés.** El perfil por trazas *descendía* al avanzar
(−90,6 → −163,5). La cara alta de `SM_CastleStairs` mira a **−Y**. Arreglado con **yaw 180**.
Ojo: al girar 180° el offset del pivote (`off_XY.y = 10`) cambia de signo.

**2. Agujero en la junta.** Con el paso igual a la profundidad de la malla (154) quedaba un hueco
en Y=2640: la traza caía al suelo. **Paso reducido a 138** → ~16 cm de solape.

Verificación final, trazas cada 10 uu en **tres carriles** (X = −700, 0, +700):
**cero huecos y cero descensos**, de −176,5 (suelo) a +123,5 (plataforma) de forma continua.

> **Lección:** una escalera de Megascans es un **escaneo dañado**, no un bloque limpio. Nunca dar
> por hecha su orientación ni que el paso sea igual a su profundidad. Trazar siempre el perfil
> completo, y en varios carriles.

### El altar

6 hiladas × 2 losas de `SM_AngkorWatTempleStones` (191×100×69), escala 1,55, **aparejo alterno**
(yaw 0 / 90 en hiladas pares/impares). Las dos losas de cada hilada estaban a ±77,5 y dejaban una
**junta de cuchillo** en el eje: la traza en (0,0) se colaba al suelo. **Acercadas a ±70.**

La cima es irregular (347 a 425 según el punto) porque es un montón de piedras escaneadas. Es lo
buscado, no un defecto.

## Segunda tanda de mallas reales — 184 actores

| Bloque | Fuera | Dentro |
|---|---|---|
| Pozo del barrio de Agua | 1 cilindro | **4** piezas (`SM_MK_Agua_Pozo_*`) |
| Fragua del barrio de Fuego | 1 cilindro | **2** (`SM_MK_Fuego_Horno` + `_Chimenea`) |
| Pedestales de los 4 barrios | 4 cilindros | **4** tambores `SM_RomanColumn_04` |
| Ofrendas del altar | — | **10** (`SM_MK_Ofrenda_*`) |
| Taller de la fragua | — | **8** (`SM_MK_Fuego_Taller_*`) |

Verificado por bounds: base a −176,5 (±2) en todo, nada flotando ni enterrado.

### ⚠️ Cinco bombas más, cazadas antes de instanciarlas

`get_asset_tags` sobre todos los candidatos, antes de tocar nada:

```
SM_WoodenBarrelA    3050 MB   ← un barril de 38 cm
SM_WindmillWings_B  1742 MB
SM_WindmillWings    1638 MB
SM_Fence_Rough_01    589 MB
SM_Fence_Rough_02    168 MB
```

**El recuento de triángulos no predice el coste**: `SM_WoodenBarrelA` tiene 5.058 triángulos y
pide 3 GB — lo caro son sus texturas. Mirar siempre `BuildRequiredMemoryEstimate`, no `Triangles`.

Las 10 mallas ligeras que sí se usaron tardaron **15,2 s en total** en su primera carga.

### Piezas que comparten origen

Hallazgo útil: varios conjuntos de Megascans están modelados **con un origen común**, así que se
colocan las piezas todas en el mismo punto y encajan solas. Se detecta porque el pivote queda
*por debajo* de la base de la malla:

| Malla | Pivote sobre su base |
|---|---|
| `SM_WellBase` | +2 |
| `SM_MainWell` | 0 |
| `SM_WellDetailPieces` | **−24** |
| `SM_WellShingles` | **−171** |
| `SM_Furnace_Low` | +81 |
| `SM_Furnace_ChimneyAddon` | **−147** |

Los cuatro del pozo van en `(x, y, suelo)` sin más. El horno se sube 81·escala para apoyarlo, y la
chimenea va **en ese mismo punto**, no encima.

### Rutas: no asumirlas

`/Game/Meshes/Well/SM_WellBase` **no existe** — es `/Game/Meshes/Well/WellBase/SM_WellBase`,
mientras que sus tres hermanas sí cuelgan directamente de `Well/`. Resolver siempre con
`find_assets` antes de construir la ruta a mano.

### Descartado: `SM_Townsign`

118×205×**19**: está modelado **tumbado**, y con el pivote en un extremo (`offXY.y = −102`).
Levantarlo exige pitch/roll a ojo. No compensa por MCP.

## Escombro contra la silueta de caja ✅

**131 piezas** repartidas con un kit de 14 mallas ligeras (4-40 MB), todas medidas antes con
`get_asset_tags`:

| Zona | Piezas | Carpeta |
|---|---|---|
| Templo: borde de plataforma, muros interiores, pie de columnas, faldón exterior | **60** (`SM_MK_Escombro_T*`) | `03_TemploPuerta/Escombro` |
| Muralla: cara interior de los 15 tramos + torres de la puerta sur | **51** (`SM_MK_Escombro_M*`) | `05_Muralla/Escombro` |
| Pie de las 10 columnas de las sefirot | **20** | `01_Plaza/Sefirot/Escombro` |

Kit: `VolcanicDolerite_01..06` (rocas), `ChapelStructure_01..04` (cascotes tallados),
`RomanStoneFloor` y `AngkorWatTempleStones` (losas), `StoneWall` y `BrokenChapelStoneWall`
(bloques grandes). Cada pieza con yaw aleatorio, pitch/roll de ±6°, escala variable y
**hundida 8-28 cm** en el suelo para que nada flote.

**No se migraron carpetas de rocas** (`ChiseledRock`, `CrackedRock`, `RockGranite`…). El escombro
sale de piedra tallada, que para una ciudad en ruinas funciona mejor que cantos rodados.

> ### ⚠️ TRAMPA: si el MCP no devuelve respuesta, la operación PUEDE haberse ejecutado igual
>
> Un apagón cortó la respuesta de un script que colocaba 71 escombros. Al volver, se relanzó — y
> había **142**: el original **sí se había ejecutado y guardado**, solo se perdió la respuesta.
> Como se usa una semilla fija para el azar, las copias quedaron **exactamente superpuestas** e
> invisibles a ojo.
>
> **Procedimiento obligatorio tras cualquier corte (apagón, timeout, reconexión del MCP):**
> contar actores por prefijo **antes** de relanzar nada. Se detecta comparando el total esperado,
> y se limpia recorriendo los actores y borrando los que repitan etiqueta.
>
> Ventaja lateral de nombrar todo con prefijo (`SM_MK_Escombro_M%03d`): sin nombres
> deterministas, los duplicados habrían sido imposibles de distinguir.

## Primera casa real en Malkuth ✅

`House_01` del Medieval Village traída por **copiar/pegar entre editores**. **600 actores**,
**12,7 × 12,2 × 8 m**. Colocada en el barrio del Aire, hueco `Casa_1` en `(2404, 849)`.

### El copiar/pegar, paso a paso

1. En el sample: clic en la carpeta `House_01` → clic derecho → **`Select` → `Select Subtree`**.
   **Marcar la carpeta NO selecciona sus actores** — este era el fallo por el que "no copiaba".
2. Ratón **sobre el viewport** → `Ctrl+C`.
3. Comprobación barata: pegar en el Bloc de notas. Si sale `Begin Map / Begin Actor Class=…`,
   la copia es buena.
4. En Malkuth: ratón sobre el viewport → `Ctrl+V`.

### ⚠️ Comprobar las dependencias ANTES de pegar

Del volcado de texto salieron **42 mallas distintas**, y **18 no estaban migradas** — entre ellas
los `SM_MedievalModularWall*`, `Door*`, `Gable*` y `CornerWall*`, o sea **los muros, puertas y
esquinas**. Pegar así habría dado una casa sin paredes, y **las referencias vacías no se
rellenan solas** al migrar después: hay que borrar y repetir.

Se resolvió migrando en bloque `Megascans/3D_Assets` y `Meshes` enteras (~4,5 GB de más), que
cubre también las seis casas restantes.

> **`AssetTools.exists` NO sirve para assets.** Devolvió `false` para las 42, incluidas mallas
> que estaban en el proyecto. Comprobar siempre con **`find_assets`** y comparar el último
> segmento del path.

### ⚠️ El `Ctrl+G` no ayuda al MCP

Se agrupó la casa con `Ctrl+G` pensando en mover el `GroupActor` de una llamada.
**No funciona: mover el GroupActor por MCP cambia su transform pero no arrastra a los hijos** —
el agrupado es lógica del editor y la API se la salta. Además sus `get_actor_bounds` devuelven
basura (±1.638.400).

El grupo **sí sirve para el humano**: con él seleccionado, el **gizmo del viewport** (tecla `W`)
mueve los 600 de golpe. El Details panel no, porque muestra "Multiple Values" y no deja teclear.

### Rendimiento: el cuello de botella era `get_label`

Mover 600 actores uno a uno costó tres tandas. La primera versión recorría **los 900 actores del
nivel llamando a `get_label`** en cada pasada: **245 s solo de preparación**.

> **Truco:** `find_actors(name='SM_MK_')` devuelve todos los nuestros en **una** llamada. Restando
> ese conjunto (más los actores de sistema, buscados por nombre) se obtiene la casa sin recorrer
> etiquetas. La preparación bajó de **245 s a 7 s**.

> **Reanudar tras un corte:** `ActorTools.add_tag` + `find_actors(tag=…)`. Se etiqueta cada actor
> al moverlo y el siguiente script recupera los pendientes con una sola llamada. Los 600 quedaron
> con el tag **`MK_Casa01_movida`**, así que futuros movimientos de esa casa son inmediatos.

### Reparto de casas rehecho: 4 por barrio

Las cajas originales eran de 7×5 m; la casa real mide 12,7×12,2. Se rehízo el reparto:

| | |
|---|---|
| Huecos | **4 por barrio** (16 en total), `SM_MK_<Barrio>_Casa_1..4` |
| Tamaño de caja | 1300 × 1250 × 800, la planta real medida |
| Separación a lo largo de la calle | 1450 (`u = 200` y `1650`) |
| Hileras | `v = ±1100` → **calle de 900 uu** |
| Radio ocupado | 1609 a 4849: fuera de la plaza, dentro de la muralla |

**Ojo con la posición inicial:** al colocar la casa en el reparto viejo, su esquina llegaba a
radio 918 (la plaza tiene 1400) y **se comía la columna `SM_MK_Sefirah_02`**. Verificar siempre
por traza que la plaza y las columnas quedan libres.

## Traces de debug del arma — apagados de verdad ✅

En la primera partida con assets reales salía una **línea roja** del jugador al enemigo. Leído en
PIE sobre las instancias vivas:

```
BP_DA_WarriorAI_C_0.MeleeCollisionHandler      debug = true
BP_DA_PlayerCharacter_C_0.MeleeCollisionHandler debug = true
BP_DA_GiantBoss_C_6.MeleeCollisionHandler       debug = false
```

El CDO del componente está en `false`, así que el `true` venía de la plantilla en
`BP_CombatCharacter` — **inaccesible por MCP**, porque los componentes heredados no existen como
subobjetos del CDO del hijo.

**Arreglado por cirugía de nodos** en el `BeginPlay` de nuestras dos clases hijas, sin tocar DCS:

```
EventBeginPlay
  Parent: BeginPlay                                    ← conservado
  [SetCanCycleDirectionalTargets true …]               ← solo en el jugador
  SetDebug(false, target = GetMeleeCollisionHandler)   ← nuevo
```

Verificado en PIE: las tres instancias a `false`.

### Trampas del API de Blueprints

- **El DSL muestra el nodo como `Class|PCGSettingsInterface|SetDebug`.** Es un despiste del
  visor: varias clases del motor tienen una función `SetDebug`. El nodo es el correcto — se
  confirma por el tipo del pin `self`: `BP Collision Handler Component Object Reference`.
- **`pin_id.index_id` va por dirección**, no en un espacio común: entradas 0,1,2 y salidas 0,1
  conviven. Leerlos con `get_node_infos`, nunca contarlos a ojo.
- **`arrange_nodes` no acepta `graph`**, pide una lista de `nodes`. Llamarlo mal aborta el script.
- Los dicts que devuelve el `ProgrammaticToolset` son **`_StrictDict`**: `d.get(k, defecto)`
  **lanza** si la clave no existe. Comprobar con `k in list(d)` y usar `d[k]`.
- **`describe_toolset` de `BlueprintTools` no cabe en contexto** (72 000 caracteres). Volcarlo a
  fichero y extraer solo los esquemas que hagan falta.

## Las 7 casas colocadas ✅ — 1655 actores

| Casa | Barrio | Centro | Actores | Caballete |
|---|---|---|---|---|
| 01 | Aire | (2404, 849) | 600 | de costado |
| 02 | Aire | (3429, 1874) | 85 | a hastial |
| 03 | Aire | (879, 2393) | 185 | de costado |
| 04 | Fuego | (1874, −3429) | 82 | a hastial |
| 05 | Fuego | (849, −2404) | 80 | a hastial |
| 06 | Agua | (−2405, −850) | 58 | de costado |
| 07 | Tierra | (−849, 2374) | 102 | a hastial |

**1192 actores de casa.** Los cuatro barrios tienen al menos una.

### ⚠️ El templo se come dos huecos: son 14, no 16

La plataforma del templo ocupa **X ±2200, Y 2800–4600**, y ahí caían `Aire_Casa_4` (1874, 3429) y
su espejo `Tierra_Casa_2` (−1874, 3430). House_04 se colocó ahí y quedó **atravesando el muro
derecho del templo y su columna 4**; hubo que rescatarla al barrio del Fuego.

**La calle del barrio de Tierra sigue chocando** con la plataforma a partir de u≈1500 (la traza da
123,5 en vez de −176,5). No bloquea nada hoy, pero al montar el templo real habrá que estrechar
la plataforma o desviar esa calle.

Las 7 cajas de hueco libre se borraron: al lado de casas reales cantaban demasiado. Coordenadas
por si se reponen (tamaño 1300×1250×800, yaw = ángulo del barrio):

```
Fuego_Casa_3   ( 2404,  -849)      Agua_Casa_2   (-3429, -1874)
Fuego_Casa_4   ( 3429, -1874)      Agua_Casa_3   ( -849, -2404)
Tierra_Casa_3  (-2404,   849)      Agua_Casa_4   (-1874, -3429)
Tierra_Casa_4  (-3429,  1874)
```

### El flujo bueno: pegar y NO agrupar

```
House_01   600 actores   ~7 min
House_02    85 actores    123 s
House_03   185 actores      5 s   <- sin Ctrl+G
House_04    82 actores      6 s
```

**La clave es la carpeta `House_NN` que el pegado conserva.** Con `get_actors_in_folder` se tienen
los actores en **una** llamada y desaparece toda la fase de búsqueda, que era el 95 % del coste.
El `Ctrl+G` destruye esa carpeta y encima **no sirve por MCP** (mover el GroupActor no arrastra a
los hijos).

Receta por casa:
1. Sample: carpeta → `Select` → `Select Subtree` → `Ctrl+C` sobre el viewport.
2. Malkuth: `Ctrl+V`. **No agrupar.**
3. Medir con `get_actors_in_folder`: centro de bounds, **Z de los muros modulares** (es el plano
   de suelo de la casa) y el eje del caballete (el par de `Gable` más separado).
4. Rotar al múltiplo de 90° más cercano respecto a la calle del barrio, trasladar al hueco y
   bajar `DZ = -176.5 - Z_muros`.
5. Etiquetar `MK_CasaNN`, mover a `Malkuth/04_Barrios/<Barrio>/Casa_NN`, borrar la caja.

> ### Los tags salvaron Casa_03
>
> Apareció desplazada **(+810, −730)** en bloque —traslación pura, cosa de un arrastre de gizmo
> con selección residual—. Como sus 185 actores llevaban `MK_Casa03`, se localizaron en una
> llamada, se comprobó que el desplazamiento era uniforme y se devolvieron.
>
> **Sin el tag habría sido imposible distinguirlos de las casas vecinas.** Etiquetar siempre.

## Suelo y vegetación

**El suelo era `MossyGround` a 800 cm de tiling:** verde saturado y sin variación, al lado de
fotogrametría se leía como una moqueta. Cambiado a **`HeavyMud` a 380 cm** con tinte
`0.92, 0.90, 0.85`.

**168 props** repartidos (`Malkuth/07_Vegetacion`): musgo `IcelandicMossClusters`, doleritas,
ramas, raíces, tocones. 120 en las cuatro calles, 26 en la avenida sur, 22 en el anillo de la plaza.

> ### ⚠️ Todos los Megascans son `BlockAll`
>
> Soltar 168 props con colisión en las calles habría destrozado el NavMesh del jefe. Van todos
> con colisión desactivada. Verificado por trazas: las calles siguen dando −176,5 limpio.

### Trampas nuevas

- **La colisión no se escribe en el componente**: `collisionEnabled` y `collisionProfileName` **no
  existen** ahí. Viven dentro del struct **`bodyInstance`**:
  ```json
  {"bodyInstance": {"collisionEnabled": "NoCollision", "collisionProfileName": "NoCollision"}}
  ```
- **Un `set_properties` fallido aborta el script entero** del `ProgrammaticToolset`, aunque lo
  envuelvas en `try/except`. Probar cada propiedad con una llamada suelta antes de meterla en un
  bucle de 200.
- **`delete_folder` sobre una carpeta que ya no existe también aborta.** Las carpetas se borran
  solas al quedarse vacías, así que comprobar contra `get_folders` antes.
- **No borrar `GroupActor` por MCP**: podría llevarse a sus hijos y no hay deshacer. Para
  deshacer un grupo, en el editor: clic derecho → `Group` → `Ungroup`.

## El templo con assets reales ✅ — 1848 actores

Traído del Goddess Temple por copiar/pegar. El sample es una **cantera/gruta con ruinas romanas
dispersas**, no un templo en pie: no hay pórtico que copiar, hay piezas sueltas.

| Elemento | Qué se usó |
|---|---|
| **Pórtico** | 4 columnas de `Columns_Large` a ×7,4–7,6 en (±700, 3000) y (±1700, 3000) |
| **Ruinas al pie de la escalinata** | Las 2 columnas derribadas del mismo lote, de 9,9 y 8,6 m |
| **Enlosado** | Las 52 `SM_RomanStoneFloor` de `GroundTiles`, a ×3,7 (392×597 cada una) |
| **La Puerta** | `SM_OldChapelArch` a ×5 (1245×414×1281) empotrado en el muro del fondo |
| **Muros de la cella** | 15 tramos de altura irregular + 70 piezas de sillería rota |
| **Decorado ritual** | 60 piezas curadas (braseros, vasijas, alambiques, velas) |

Cotas: la plataforma remata a **+123,5**; las columnas apoyan ahí y coronan a 1307–1354, tocando
el dintel que arranca en 1323.

### ⚠️ El decorado del sample eran 1676 actores

`Candles` (734), `HangingLanterns` (279), `IncenseBurners` (114), `Z_Dressing` (547) y `Heads` (2).
Es el decorado completo de una gruta de 2578 actores, **con decenas de luces puntuales dentro**
(`CandleLightSmall*`, `PointLight1..49`). Con Lumen eso hunde el frame.

**Borrado entero y repuesto a mano** con 60 piezas colocadas por traza. El nivel pasó de 3388 a
1768 actores.

Las **cabezas colosales** venían con bounds de 22869 × 23147 × **26501** — 265 metros — y su malla
llegó sin material (`CustomAssets/HeadTextures` solo trae el `.uasset`). Borradas. Si se quieren,
hay que migrar sus `T_Head*` y escalarlas a 4–6 m.

Los **faroles colgantes** no se repusieron: su montaje cuelga de `SM_LongChain` desde una bóveda
de gruta y en un templo a cielo abierto no tienen de dónde colgar. Para luz de calle está
`SM_LanternPost` del pueblo, ya migrado.

### Los muros: partir en vez de bajar

Los tres muros originales eran losas de 44×16 m y 14 m de alto. No hay ninguna pieza migrada que
dé esa medida (`ChapelStructure` es de 1×2×3 m), así que componerlos habría costado **más de 200
actores por muro**.

Solución: **partirlos en tramos de altura irregular**, que cuesta 15 actores y rompe la silueta.

```
Fondo (7 tramos):  640 · 900 · 1450 · 1520 · 1450 · 980 · 700
Laterales (4 c/u): 560 · 840 · 700 · 1080
```

Los tres centrales del fondo se quedan altos **a propósito**: el arco necesita 1280 de despeje.

Y **28 de las 70 piezas de sillería van coronando** los tramos, para que el corte superior no se
lea recto. Ese es el detalle que lo convierte en ruina.

### ⚠️ Ojo con `SM_RomanColumnHigh_02`

`Columns_Large` la arrastra. Es la de **1.099.989 triángulos y 2.942 MB de build** que ya nos
colgó el editor una vez. Al pegar la carpeta el editor se queda al 0 % un buen rato construyendo
su Nanite: **no es un cuelgue, hay que dejarlo terminar.**

### Pendiente en el templo

- El **dintel del pórtico** (`SM_MK_TempleLintel`) sigue siendo una caja de 4000×300×200. No hay
  viga de 40 m en lo migrado; se podría partir en tramos como los muros.
- La **plataforma** sigue siendo caja, aunque enlosada por encima.
- La **calle del barrio de Tierra choca con la plataforma** a partir de u≈1500. Al decidir la
  forma final del templo habrá que estrecharla o desviar la calle.

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

## Vórtice Celestial v2 — hueste de ángeles sobre Malkuth

Reemplaza los 7 anillos poligonales originales (`MK_Coro_Anillo_0..6`, ~200 componentes
StaticMesh individuales) por una hueste densa estilo "hostia angelical": **~280 ángeles en
8 draw calls** + 10 serafines skeletal. Todo vive en `Malkuth/08_Cielo/Vortice`.

Centro: **(0, 45000)**. Núcleo (`MK_Coro_Nucleo`, esfera de 24 m de diámetro) y luz central
en **Z=38000**; quedan completamente por encima de la hueste (máximo medido ≈Z=33772).
Los anillos bajan en embudo desde Z=30500 (interior) hasta Z=23400 (exterior).

| Actor | Mesh | Radio | Cant. | Escala | Giro (°/s) |
|---|---|---|---|---|---|
| `MK_Vortice_Anillo_1` | `SM_DA_AngelV2` | 60 m | 14 | 6–9 | 14,0 |
| `MK_Vortice_Anillo_2` | `SM_DA_AngelV2` | 95 m | 20 | 7–11 | 11,0 |
| `MK_Vortice_Anillo_3` | `SM_DA_AngelV2` | 135 m | 26 | 8–12 | 8,5 |
| `MK_Vortice_Anillo_4` | `SM_DA_AngelV2` | 180 m | 32 | 9–14 | 6,5 |
| `MK_Vortice_Anillo_5` | `SM_DA_AngelSilueta` | 235 m | 40 | 8–13 | 5,0 |
| `MK_Vortice_Anillo_6` | `SM_DA_AngelSilueta` | 295 m | 48 | 9–14 | 3,8 |
| `MK_Vortice_Anillo_7` | `SM_DA_AngelSilueta` | 360 m | 56 | 10–16 | 2,8 |
| `MK_Vortice_Dispersos` | `SM_DA_AngelV2` | 70–340 m | 34 | 6–12 | 4,5 |
| `MK_Vortice_Serafines` | `BP_DA_AngelCentinela` ×10 | 45 m | 10 | 6 | 9,0 |

### Cómo está montado

- Cada anillo es **un solo actor** con un `InstancedStaticMeshComponent` ("Angeles",
  Movable, sin sombras) y un `RotatingMovementComponent` ("Giro"). Interior más rápido →
  paralaje de vórtice.
- Las instancias se escribieron vía MCP (`PerInstanceSMData` con matrices 4×4). Jitter por
  instancia: radio ±15 %, Z ±14 m, guiñada ±15°, alabeo ±30°, **cabeceo −85°…−50°** (vuelo
  prono, cabeza hacia la tangente; los meshes son figuras verticales con alas en su eje Y).
- `MK_Vortice_Serafines`: pivote con `SceneComponent` + `RotatingMovementComponent`; los 10
  `BP_DA_AngelCentinela` (cuerpo + alas skeletal animadas) van attacheados y orbitan a 45 m
  del núcleo, de pie, mirando a la tangente.
- `MK_Vortice_LuzCentral`: PointLight en el núcleo — 100k cd, atenuación 600 m,
  blanco cálido (255, 240, 205), radio de fuente 15 m, **sin sombras** (coste).

### Coste

Los 8 ISM son 8 draw calls (~86k tris estáticos en total). Los 10 serafines son los únicos
skeletal (20 SkeletalMeshComponents). El giro es `RotatingMovementComponent` puro: solo se
ve en PIE/juego, en el viewport del editor queda congelado.

### Verificado

- Rotación confirmada en PIE (dos capturas separadas muestran los anillos girados).
- Vista cenital: espiral densa y orgánica, sin patrón concéntrico evidente.
- Desde el PlayerStart el vórtice queda a ~850 m tras el bosque de aproximación; se percibe
  el resplandor al final del camino.

### Rebalance anti-ceguera (misma sesión)

La primera versión lavaba el cielo en blanco y los ángeles (emisivos blancos) desaparecían
contra el resplandor. Ajustes:

| Qué | Antes | Después |
|---|---|---|
| Emisivo `M_DA_NucleoLuz` | (90, 78, 57) | (22, 18.5, 13) |
| `MK_Vortice_LuzCentral` | 400k cd, fuente 25 m | 100k cd, fuente 15 m |
| Esfera núcleo | escala 66 | escala 24, Z=38000 |
| Ángeles del vórtice (8 ISM) | `M_DA_AngelLuz` (emisivo 13/11/7.4) | **`M_DA_AngelContraluz`** |

`M_DA_AngelContraluz` (nuevo): material lit sin emisivo — BaseColor bronce (0.28, 0.18,
0.10), roughness 0.65. La hueste se lee como **cuerpos oscuros a contraluz** contra la luz
central, igual que la referencia. Los 10 serafines skeletal y los centinelas del camino
conservan sus materiales luminosos (contraste: pocos brillantes cerca del núcleo, masa
oscura alrededor). Verificado en PIE: el cielo al final del camino ya muestra azul y nubes,
y los ángeles se distinguen como siluetas.

Corrección posterior: la luz estaba en el vórtice, pero la esfera había quedado por error en
el origen del mundo `(0,0,0)`, ocupando la plaza de Malkuth. Se trasladó a
`(0,45000,38000)` y se redujo de escala 45 a 24.

## Barrios elementales v2 — lectura visual y densidad

Se reforzó la lectura de los cuatro barrios sin convertir todo Malkuth en VFX ni teñir el
suelo completo. La identificación usa tres capas repetibles: **estandarte en la entrada**,
**silueta/hito propio** y **actividad ambiental local**.

### Corrección de densidad

La casa grande de Aire tenía copias superpuestas en la misma transformación. Se retiraron
**524 actores redundantes** que no aportaban volumen visible. El barrio pasó de 877 a 353
actores antes de añadir su nueva señalización; tras el pase completo quedó en 360.

Para poblar Agua y Tierra sin repetir el problema se combinaron sus casas existentes en
meshes reutilizables:

| Asset | Triángulos | Optimización | Copias nuevas |
|---|---:|---|---:|
| `SM_SM_MK_House_Water_01` | 110.509 | Nanite + 10 hulls convexos | 2 |
| `SM_SM_MK_House_Earth_01` | 196.255 | Nanite + 10 hulls convexos | 2 |

Los assets viven en `Content/DarkAngels/Environment/Malkuth/Districts`. Las cuatro casas
nuevas son un actor cada una y conservan colisión para gameplay.

### Lenguaje de cada barrio

| Barrio | Estandarte | Hito / silueta | Atmósfera y utilería |
|---|---|---|---|
| Aire / Citrino | oro-citrino | campanario + campana | viento, hojas en vórtice y tres estandartes altos |
| Fuego / Rojizo | rojo oscuro | fragua + casa quemada | llama, brasas y columna de humo |
| Agua / Oliva | oliva húmedo | pozo + molino | charcos, lluvia vertical, gotas ascendentes y cisterna |
| Tierra / Negro | negro-bronce | cripta + osario | raíces, piedras, polvo y niebla baja |

Cada entrada tiene dos postes altos y dos planos de tela con una instancia de
`MI_Flag` propia. Materiales:

- `MI_MK_Flag_Air_Citrine`
- `MI_MK_Flag_Fire_Reddish`
- `MI_MK_Flag_Water_Olive`
- `MI_MK_Flag_Earth_Black`

Todo el pase nuevo usa el tag `MK_DistrictIdentity` y carpetas `Identity` dentro de cada
barrio. Conteo final del pase: Aire 22, Fuego 8, Agua 24 y Tierra 22 actores de identidad.

### Refuerzo de lectura elemental

El fuego seguía siendo el único elemento legible en una vista estática porque llama y
emisivo producen una silueta inmediata; viento, goteo y polvo dependen demasiado del
movimiento. Se añadió un sello físico de 8–9,2 m en el pedestal de Aire, Agua y Tierra,
usando sus materiales cabalísticos existentes:

- Aire: halo citrino elevado de 8,2 m, anillo de ocho luces, tres postes altos, viento
  contenido y hojas en movimiento.
- Agua: cuenca oliva de 9,2 m, superficie mojada, columna de lluvia, tres gotas ascendentes
  y seis luces turquesa.
- Tierra: sello carbón/bronce de 8,8 m, seis piedras verticales, raíces, polvo más denso y
  dos nieblas bajas.

Así los tres barrios conservan su VFX, pero también se pueden localizar desde arriba o
cuando el efecto está entre ciclos.

La composición final forma cuatro cuadrantes claros:

| Cuadrante | Elemento | Centro focal |
|---|---|---|
| 1 | Tierra | `(−2000, +2000)` |
| 2 | Agua | `(−2758, −2758)` |
| 3 | Aire | `(+2000, +2000)`, halo en `Z=1050` |
| 4 | Fuego | `(+2758, −2758)` |

Materiales emisivos nuevos: `M_DA_Element_Air_Citrine`, `M_DA_Element_Water_Olive` y
`M_DA_Element_Earth_Bronze`. El `NS_Wind` no se escaló como marcador principal: a gran
tamaño sus sprites parecían tablones beige y tapaban Aire, por lo que se redujo y el halo
pasó a ser la lectura dominante.

### Assets que todavía mejorarían el resultado

No hace falta descargar nada para reconocer los barrios en esta POC. Para un segundo pase
de calidad, la prioridad de Fab sería:

1. **Canal medieval modular + agua animada** para que Agua tenga una línea de circulación,
   no solo superficies mojadas.
2. **Banderas de tela animadas, veletas y campanas de viento** para que Aire tenga movimiento
   físico legible además de partículas.
3. **Set modular de cementerio/cripta y niebla localizada** para dar más profundidad a Tierra.

Fuego ya está razonablemente cubierto por la fragua, carbón, yunque y VFX existentes; no es
prioridad comprar otro pack.

---

## L_DA_Malkuth_POC_V2 — POC jugable con mecánicas (2026-08-07)

Segunda versión del nivel Malkuth, esta vez como **POC jugable completo** (loop de ~5 min)
con enemigos funcionales, sistema Farsa/Corruptio, boss Gabriel de 3 fases, trampas y UI base.
Construido íntegramente vía MCP (BlueprintTools DSL + SceneTools + ProgrammaticToolset).

### Cómo probar

1. Abrir `/Game/DarkAngels/Maps/L_DA_Malkuth_POC_V2` y pulsar Play.
2. El jugador spawnea en el Jardín (0, 6500) como `BP_DA_PlayerCharacter_V2`.
3. Recorrido: Jardín → Sendero → Claro → Gazebo (Archangel) → Puente (trampas) →
   Santuario (altar con `IA_Interact`) → Anfiteatro → Trono (Gabriel) → Escalera → Portal.
4. Para probar el sistema Farsa: seleccionar al jugador en PIE y poner `Farsa = 30`
   en Details → los Messengers pasan de Patrol/Observation a Attack.
5. Dark Strike: botón de thrust attack (`IA_MeleeThrustAttack`) con Corruptio >= 30.
   Cuesta 30 Corruptio + 5 Farsa, daño 60 en 5 m, rompe el Light Shield (3 hits).
6. Alas: se desbloquean al derrotar a Gabriel (Jump en el aire = glide 0.3x gravedad).

### Assets nuevos

- **Player**: `BP_DA_PlayerCharacter_V2` (hijo de `BP_DA_PlayerCharacter`). Vars Farsa /
  Corruptio / MaxFarsa / TearsOfRepentance / checkpoint. Funciones `AddFarsa`,
  `AddCorruptio`, `GetFarsaValue`, `GetCorruptioValue`, `RestAtAltar`, `RestoreHealth`.
  EventGraph: cooldown Dark Strike + glide por polling de `Input|EnhancedActionValues`
  (los eventos `EnhancedInputActionIA_*` no se pueden crear vía MCP DSL), daño con
  `Game|Damage|EventAnyDamage` (HP vía `Interface|SetStat`/`GetStatValue` del
  StatsManager DCS), muerte → Mancha de Sombra (log), MaxFarsa -10 (mín 50), respawn
  en checkpoint. BeginPlay crea `WBP_DA_HUD`.
- **Enemigos**: `BP_Angel_Messenger` (HP 60, patrol/observation/attack, trompeta 8 s,
  refuerzo <50 % HP, autodestrucción si hay Archangel vivo, +15 Corruptio al morir),
  `BP_Archangel` (HP 400, 3 fases, escudo al 70 % que rompe con 3 Dark Strikes o 5 s,
  Judgment Beam cada 12 s en fase 2+, invoca Messengers en fase 3),
  `BP_Gabriel` (HP 800, hijo de Archangel; fase 1 diálogo por log cada 10 s con check
  Farsa >= 50, fase 2 destruye 4 espejos + mirada drena Farsa 5 %/s, fase 3 destruye
  todos los espejos + escudo regenera cada 15 s + cristalización en sal al 10 % HP;
  al morir desbloquea las alas). Tags: `Angel`, `Archangel`, `Gabriel`, `Mirror`.
- **Mundo**: `BP_CelestialRay` (aviso 1.5 s + rayo 25 daño, patrón 3 s/1.2 s),
  `BP_AltarOfContemplation` (proximidad + `IA_Interact` → `RestAtAltar`),
  `BP_Portal` (rotación + "TO BE CONTINUED"), `BP_RespawnVolume` (KillZ bajo el puente,
  respawn en inicio del puente), `BP_DA_BeamVisual` (cilindro 20 m, muere en 1 s),
  `BP_LightShield` (esfera visual, muere en 5 s).
- **UI**: `WBP_DA_HUD` (vars HP/Stamina/Corruptio/Farsa Percent, Tick actualiza Farsa y
  Corruptio), `WBP_DA_BossBar`, `WBP_DA_DialogueWheel`, `WBP_DA_DeathScreen`,
  `WBP_DA_PauseMenu` (shells funcionales: sin árbol visual, diseñar en UMG a mano).
- **Data**: `DT_FarsaEvents` (8 filas, schema `GameplayTagTableRow` como workaround:
  evento en `Tag`, delta y descripción en `DevComment`).

### Simplificaciones del POC (documentadas)

- Diálogo de Gabriel y telegrafía de ataques van por `PrintString` (la Dialogue Wheel
  visual requiere diseño UMG manual).
- Desperation del Messenger: AoE si existe CUALQUIER Archangel vivo (sin check de HP
  del Archangel; los getters cross-BP no se indexaban en el registro de nodos).
- Sin Niagara (no soportado por MCP): fuentes/portal usan materiales con Panner;
  feather-dissolve y dust burst son logs + destrucción.
- Sin audio (no hay toolset de SoundCues): cues descritos vía logs.
- "Romper objeto sagrado" y "evadir sin matar (+1 %)" no implementados (requieren
  BPs de setos/fuentes dañables y tracking de evasión).
- Stamina la gestiona el DCS base; HP del jugador se reduce en `EventAnyDamage`
  propio (el DCS no escucha ese evento, no hay doble descuento).
- Escudo: Dark Strike se detecta como daño >= 60 (mismo canal ApplyDamage).

### Verificación (2026-08-07)

- PIE OK: jugador spawnea en PlayerStart, sin errores LogBlueprint/LogScript.
- Messenger patrulla en loop (muestreo de posiciones en PIE).
- Los 12 espejos del Trono tienen tag `Mirror`; GameMode apunta a `BP_DA_PlayerCharacter_V2`.

## Reemplazo con GardenKit de Blender (2026-08-07)

Se reemplazaron 48 actores placeholder (primitivas SM_MK_*) por meshes del kit Blender importado en `/Game/Blender/`:

- **Setos** (`SM_MGK_Hedge_Straight_400`): 12 setos del Jardin Geometrico (escala 1.19/1.0/1.9) y 12 muros del Sendero de Setos (escala 1.19/2.5/1.9, offset +500 Y por pivot al extremo).
- **Fuentes del jardin** (`SM_MGK_Fountain_Octagonal_Centerpiece` + `_WaterUpper`): 3 bases y 3 jets reemplazados (z=0, pivot inferior).
- **Bancas** (`SM_MGK_Bench_Stone_B`, `SM_MGK_Bench_Straight_A`): 2 bancas del Sendero.
- **Fuentes del puente** (`SM_MGK_Fountain_Round_Small` + `_Water`): 8 fuentes + 8 jets en el Puente (z=210, nivel del deck).

Los meshes conservan sus materiales importados de Blender (`M_MGK_Foliage_Emerald`, `M_MGK_Stone_Ivory`, `M_MGK_Water_Preview`).
Piezas del kit aun sin usar (disponibles para decoracion extra): Topiary_Sphere/Spiral, GardenLamp, Trellis_Arch, Hedge_GateArch, Hedge_Corner/T/Cross/End, Hedge_Low_200, Path_*, PathBorder_*, Planter_*, Flowerbed_Round, Birdbath(+Water), Fountain_Wall(+Water), SteppingStones_Cluster, StoneBollard, Bench_Curved_45, SM_Malkuth_GardenKit_ALL.

## Pasada de decoracion GardenKit (2026-08-07)

63 piezas decorativas del kit Blender colocadas en carpeta `Deco_GardenKit/` del outliner (snap_to_ground):

- **A_Jardin** (24): Hedge_GateArch en entrada (0,6100), 4 Topiary_Sphere en esquinas, 2 Topiary_Spiral flanqueando estatua, 6 GardenLamp en eje central, 2 Birdbath+Water, 4 Flowerbed_Round, SteppingStones, 2 Bench_Curved_45 (escala 1.3) alrededor de fuente central.
- **B_Sendero** (16): 5 GardenLamp alternados, 4 StoneBollard en entrada/salida, Trellis_Arch (0,24500), 2 Planter_Rectangular junto a bancas, 4 Hedge_End como capas de los muros.
- **C_Claro** (3): 2 Flowerbed_Round, SteppingStones.
- **D_Gazebo** (4): 2 Planter_Rectangular y Fountain_Wall+Water sobre el piso pulido (z=1050, corregido tras detectar que snap_to_ground traza desde el Z de spawn).
- **E_Puente** (6): 4 StoneBollard, 2 GardenLamp. **Fix**: las 8 fuentes + 8 aguas del puente estaban flotando sobre el agua (x=+/-600, z=210); se movieron al deck (x=+/-360, z=0).
- **F_Santuario** (6): 2 GardenLamp flanqueando dais, 2 Topiary_Sphere en entrada, 2 Flowerbed_Round.
- **G_Anfiteatro** (4): 2 StoneBollard, 2 GardenLamp.

Zonas H (Trono) e I (Escalera) se dejaron limpias intencionalmente: claridad para el boss y la ascension.

## Pavimento y setos bajos GardenKit (2026-08-07)

62 piezas adicionales (carpeta `Deco_GardenKit/`):

- **Eje central del jardin pavimentado**: Path_Straight_600 de (0,6400) a (0,12400), Path_Straight_300 de transicion, Path_Plaza_600 bajo la fuente central (0,13000) con PathBorder_Straight_300 en lados E/W, y continuacion norte hasta el pedestal de la estatua (0,18700).
- **Sendero pavimentado**: 10x Path_Straight_600 de y=20500 a y=26500 (pasan bajo el Trellis_Arch).
- **Enlace al Claro**: 2x Path_Straight_600 (y 26500-27700) que conectan con los SteppingStones.
- **Setos bajos** (Hedge_Low_200): 12 flanqueando la entrada (6200-7400, x=+/-250) y 10 flanqueando la aproximacion a la estatua (17700-18700).
- **Hedge_Cross**: 2 parterres en (+/-2800, 10000).

Nota: los tiles de Path tienen pivot al extremo (-Y), igual que los setos: colocar en y = fin_del_tramo.

## Fix de caminabilidad puente->portal (2026-08-07)

Reporte del usuario: "cuando llego al puente no puedo pasar desde ahi, no me deja llegar hasta el templo".

Diagnostico (trazas + capturas): el "link" entre el puente (termina y=50000) y el santuario (empieza y=52500) era un cilindro escalado (10,25,1) en (0,51250,-50). Su colision convexa facetada dejaba huecos reales de ~60cm+ en el centro y mas en los lados; el jugador caia al agua (z=-650) y el RespawnVolume (kill z<-400) lo devolvia al inicio del puente. La traza por canal Visibility daba falso positivo de suelo continuo.

Fixes aplicados (carpeta `Fixes_Walkability/` + `Deco_GardenKit/E_Puente`):

1. **Pasarela puente->santuario**: 5x Path_Straight_600 (y=50200..52600) + 1x Path_Straight_300 (y=52900) en z=-14 (tope al ras del deck, z=0), sin snap_to_ground. Cubre y 49600..52900.
2. **Pasillo anfiteatro**: los 5 tiers centrales (StaticMeshActor_565/568/571/574/577, topes 100-500) bloqueaban la entrada sur. Eliminados; pasillo pavimentado con tiles (y 57400..58900). Los tiers laterales quedan.
3. **Rampa del trono**: el ascenso era 0->800->1500->1600 en escalones gigantes (la "rampa" original era una losa con pitch=31 que no inclinaba nada util y colisionaba como bbox plano). Nueva rampa: cubo (10,26.2,0.5) en (0,63475,750) roll=-34.9 (sube de 0 a 1500 entre y 62400..64550) + cubo (10,6.1,0.5) en (0,64850,1550) roll=-9.46 (1500->1600). Material Cream_Stone.
4. **Escalera de cristal**: SM_MK_GlassStair original era una losa PLANA inclinada de lado (pitch=31 sobre eje equivocado) con colision bbox plana a z=3150: imposible subir. Eliminada y reemplazada por cubo (6,58.3,0.5) en (0,73100,3100) roll=-30.96, material M_DA_MK_Glass: sube de 1600 (y=70600) a 4600 (y=75600), pendiente 31 caminable.
5. **Borde arena->base escalera**: depresion de 100cm (montana top 1500 entre arena y base, ambos 1600). Rampa cubo (8,4.12,0.3) en (0,69200,1550) roll=-14.04.
6. **Entrada de la arena**: espejo sur (596) y pilar sur (585) estaban en (0,65500) bloqueando el eje. Movidos a (+1300,65400) y (-1300,65400).
7. **Escenario del anfiteatro**: hundido de z=25 a z=0 (tope 25cm, subible sin salto).
8. **Arbol sur del santuario** (0,53200): movido a (1000,53400) para despejar el eje de entrada.

**Leccion clave**: en este MCP, `roll` POSITIVO levanta el extremo -Y (sur). Para rampas que ascienden hacia +Y (norte) usar roll NEGATIVO. Verificado empiricamente con tile de prueba y trazas finas.

Verificacion: traza completa y 42000->76600 sin huecos ni escalones >45cm (las pendientes continuas 31-35 grados son caminables). Portal accesible a z=4600.

PENDIENTE: el guardado por MCP (SceneTools.save) hizo timeout repetidamente y luego el MCP dejo de responder ("fetch failed") con el editor vivo. Los cambios quedaron en memoria del editor: guardar manual con Ctrl+S al volver al editor.

RESUELTO: al reconectar el MCP se guardo con `AssetTools.save_assets` (lista vacia = todos los dirty). NOTA: `SceneTools.save` ya no existe en el toolset actual; usar `AssetTools.save_assets`.

## Reemplazo con PropsKit de Blender (2026-08-07 noche)

Kits nuevos importados por el usuario en `/Game/Blender/`: **PropsKit** (32 meshes + 7 mats), **RuinsKit** (29 + 6), **MirrorLabyrinthKit** (27 + superficies espejo separadas + 6). Importacion limpia: materiales asignados en slots, tamanos coherentes, low-poly (36-232 tris).

Pasada PropsKit aplicada (carpeta `PropsKit_POC/`):

1. **Puente (E)**: deck cubo eliminado. 6x `SM_MP_Bridge_Wide_600x1200` (pivots y 43200-49200, z=-45 para tope a z=0; pivot al extremo +Y como los tiles GardenKit). 48x `SM_MP_BridgeRailing_300` continuas en x=+/-290 (seguridad anti-caidas al agua). 8 fuentes + 8 aguas movidas de x=+/-360 a +/-200. Tile walkway EF_0 movido a y=49800 para empatar sin gap ni overlap.
2. **Escalera del trono (G)**: rampa cubo reemplazada por 5x `SM_MP_Stair_Wide_600x600` yaw=180, pivots y=61500+600i, z=300i. Sube 0->1500 y aterriza exacto en la cara de la montana (y=64500). La mini-rampa cubo ArenaLip (1500->1600) se conserva.
3. **Escalera de ascension (H)**: cubo de cristal reemplazado por 10x `SM_MP_Stair_Wide_600x600` yaw=180, pivots y=69600+600i, z=1600+300i. Ultimo peldaño aterriza al ras de la plataforma del portal (4600) en y=75600.
4. **Portal (I)**: anillos cubo eliminados. Set completo en (0,76200) sobre la plataforma: `Portal_Arch_500` + `Portal_RuneRing` + `PortalSurface_Preview` (superficie violeta emisiva) + `Threshold` + `Keystone`. `BP_Portal_C_0` intacto.
5. **Trono (H)**: no existia blockout de trono (solo pilar + espejo). Agregado: `Throne_Dais_400` (z=1600) + `Throne_Malkuth_Main` (z=1675) + `ThroneCanopy`. Pilar norte movido a (600,68500).

**Lecciones PropsKit**: pivot al extremo +Y en puentes/escaleras/barandales (colocar en y = fin del tramo). Escaleras: borde BAJO en el pivot; con yaw=180 el cuerpo cubre y..y+600 ascendiendo al norte; apilar con delta z=300 (peldaños de ~33cm, caminables). Verificado con trazas finas.

Verificacion: trazas puente/escaleras sin huecos ni escalones >45cm; capturas de las 4 zonas OK. Guardado en disco.

## Sistema de guia del jugador: HUD de objetivos + texto flotante (2026-08-07 noche)

Pedido del usuario: "Necesito que me marques con texto flotante en que parte del escenario estoy y un HUD que me diga cual es la meta a seguir, y al pasarla cual seguiria".

### Arquitectura implementada

- **`/Game/DarkAngels/Blueprints/UI/BP_DA_HUD`** (BP de **AHUD**, no UMG): dibuja en `EventReceiveDrawHUD` el objetivo actual (arriba-centro, dorado, escala 2) y un banner de zona (30% alto, escala 3.5, con fade por alpha). Variables: `ObjectiveText` (default "OBJETIVO: Explora el Jardin de las Hostias"), `ZoneText`, `ZoneBannerEnd`, `ObjectiveIndex`. Funciones `SetObjective(InText, InIndex)` (solo avanza si InIndex > actual: progresion monotonica, no regresa si el jugador vuelve atras) y `ShowZoneBanner(InText)` (visible 5s con fade).
- **`/Game/DarkAngels/Blueprints/Level/BP_DA_HUDSpawner`** (actor en el nivel, carpeta Guidance): en BeginPlay hace `CreateWidget(WBP_DA_HUD)` + `AddToViewport` (el widget UMG queda para futuras barras de stats) y **`ClientSetHUD(BP_DA_HUD)`** sobre el PlayerController 0.
- **`/Game/DarkAngels/Blueprints/Level/BP_DA_ZoneTrigger`**: actor con `TriggerBox` + `TextRenderComponent` ("ZoneLabel", texto flotante 3D). Vars instance-editables: `ZoneName`, `ObjectiveText`, `ObjectiveIndex`. En BeginPlay: setea collision OverlapAllDynamic + overlap events + texto del label + **timer loop 0.5s a `CheckPlayerInside`**. Esta funcion hace chequeo MATEMATICO (`IsPointinBox` con loc del jugador vs loc del actor + `GetScaledBoxExtent`) con guard `HasFired`: al detectar al jugador dentro, dispara `FireZoneEntry` una sola vez, que castea `GetHUD(PC0)` a `BP_DA_HUD` y llama `SetObjective` + `ShowZoneBanner`. (Existe ademas el evento `OnComponentBeginOverlap` como via redundante.)
- **9 instancias en el nivel** (carpeta Guidance): Jardin (0,9000) idx1 -> Sendero (0,20500) idx2 -> Claro (0,30000) idx3 -> Ruinas/Gazebo (0,36500) idx4 -> Puente (0,47000) idx5 -> Santuario (0,53000) idx6 -> Anfiteatro (0,59000) idx7 -> Trono/Arena (0,65500,z1800) idx8 "Derrota a Gabriel" -> Escalera Ascension (0,71000,z2600) idx9 "Entra al Portal".

### Errores encontrados y fixes (lecciones clave)

1. **UMG OnPaint no dibuja nada**: `WBP_DA_HUD` creado por MCP es un shell sin root widget de designer; su `OnPaint` nunca renderiza. Solucion: pivot a **AHUD con DrawText/DrawRect de canvas** (deterministico, no depende del designer UMG).
2. **El GameMode NO spawnea el HUD aunque `HUDClass` este bien seteado** en el CDO de `BP_DA_GameMode` (verificado con get_properties). Fix: **`HUD|ClientSetHUD`** desde el HUDSpawner.
3. **Las capturas MCP NO muestran UI screen-space**: ni `CaptureViewport` (re-render desde pose, sin canvas) ni `CaptureEditorImage` (downscaleado a 512px) muestran PrintString en pantalla, DrawText ni DrawRect. Horas de debugging falso-negativo. **Verificacion real = captura de pantalla de Windows con PowerShell** (`CopyFromScreen`), que si muestra lo que ve el usuario.
4. **Fuente distance-field invisible en canvas**: `RobotoDistanceField` no renderiza con `AHUD::DrawText`. Con font null ("" en DSL) cae al font default del engine y si dibuja.
5. **Typo de clase en llamadas cruzadas**: `Class|WBPDAHUD|SetObjective` (widget UMG) vs `Class|BPDAHUD|SetObjective` (AHUD) — find_node_types muestra ambos; el resolver del DSL eligio el equivocado silenciosamente. Verificar siempre el id exacto con find_node_types.
6. **Los BoxExtent de las instancias quedaron con Y/Z por defecto (1500/400)**: `ObjectTools.set_properties` con JSON `{"x":..,"y":..,"z":..}` **solo aplica X** (bug del tool). El formato que funciona es texto Unreal: `"(X=5000,Y=9000,Z=500)"`. Con Y=1500 el jugador (y=3070) estaba fuera de la caja del jardin (y 7500-10500): por eso nunca disparaba.
7. **Overlaps de colision no confiables aqui**: `IsOverlappingActor` (version actor) reportaba false pese al jugador dentro (respuestas de colision del capsule DCS vs WorldDynamic). Solucion robusta: chequeo matematico `IsPointinBox` en timer 0.5s + guard `HasFired` (bool agregada con `add_variable` name/type_name).
8. **DSL docs**: `BlueprintTools.get_graph_dsl_docs()` tiene la gramatica completa (if/else multi-statement, `not`, multi-exec con `(:Pin ...)`, binds). `add_function_graph(blueprint, graph_name)` crea funciones; `add_variable(blueprint, name, type_name)`; `find_nodes(graph, title, entry_points_only)` + `delete_node` para borrar eventos huerfanos (write_graph_dsl hace upsert por evento, NO borra los no mencionados).

Verificacion final (captura real de pantalla): objetivo "OBJETIVO: Sigue el sendero hacia el norte" arriba-centro, banner "JARDIN DE LAS HOSTIAS" con fade al 30%, y texto flotante 3D "JARDIN DE LAS HOSTIAS" visible en el mundo. Sin prints de debug. Todo guardado con `AssetTools.save_assets([])`.

### Mejora de contraste/legibilidad (2026-08-07 noche, feedback del usuario)

El texto dorado sobre cielo brillante no se leia. Fix en `BP_DA_HUD.EventReceiveDrawHUD`:

- **Paneles de fondo**: `HUD|DrawRect` semitransparente oscuro (0.01,0.01,0.05, a=0.62) detras del objetivo y del banner (alpha del panel = 0.65 * fade para el banner). El texto se dibuja DESPUES del rect para quedar encima.
- **Centrado exacto**: `HUD|GetTextSize(self, text, font, scale)` -> (OutWidth, OutHeight) permite centrar texto y panel al pixel: `x = SizeX*0.5 - tw*0.5`, panel con padding (+56 ancho, +24 alto objetivo; +96/+40 banner).
- **Texto flotante 3D**: `WorldSize` de los 9 ZoneLabel de 110 a 220 (el doble). El `TextRenderColor` NO se pudo cambiar por instancia (set_properties no aplica FColor ni en formato texto ni JSON; queda blanco por defecto, que es legible).

Nota DSL: `bind` con tupla `(bind (_tw _th) (HUD|GetTextSize ...))` funciona para nodos multi-output. Verificado con captura real: objetivo y banner perfectamente legibles sobre sus paneles.

### Fix de solapamiento banner/texto 3D (2026-08-07 noche, feedback del usuario)

Problema: el banner del HUD (30% altura) se sobreponia al texto 3D flotante (que se proyecta al centro de pantalla al mirarlo) y ninguno se leia.

Fixes:

- **Banner movido al 72% de altura** (tercio inferior) en `BP_DA_HUD`: ya no solapa con el texto 3D central ni con el objetivo superior.
- **Color del texto 3D por runtime**: `TextRenderColor` no es seteable ni por instancia ni por CDO template via `ObjectTools.set_properties` (no aplica FColor y el getter regresa basura). Solucion: `Rendering|Components|TextRender|SetTextRenderColor` + `Utilities|Struct|MakeColor` en el `EventBeginPlay` del trigger (dorado 255,215,100). NOTA: el post-proceso del nivel (bloom/exposure) lava los tonos; un rojo puro de prueba renderizo como amarillo-dorado, o sea que el pipeline de color funciona pero los tonos finales se aclaran.

Estado final verificado con captura real: objetivo con panel arriba, banner con panel abajo, texto 3D dorado al centro — los tres separados y legibles. Guardado en disco.

## Integracion runtime Malakh / BP_Malakh_DCS (2026-08-09)

### Causa principal
`MalakMesh` NO era invisible por HiddenInGame ni por mesh roto. El body desaparecia al activar `ABP_Malakh_Retarget`: el IK Retargeter manda la pose de Malakh varios miles de UU en +Z (bounds Z max ~4800-9300 vs ~680 en pose estatica). La camara tercera persona mira la capsula; solo se veia equipo (escudo/espada) sobre sockets de Manny.

Ademas, `RelativeScale3D=100` era correcto para el FBX tipico de Tripo en metros, pero **`SKM_Malakh_Own` en `Malakh_Scale1v2` ya mide ~1 m** (bounds height ~100 UU). Scale 100 lo convierte en gigante.

### Assets reales
- `BP_Malakh_DCS` → parent `BP_DA_PlayerCharacter`; DefaultPawn de `BP_DA_GameMode`
- Componente: **`MalakMesh`** (hijo de `CharacterMesh0`)
- `SKM_Malakh_Own` + `SK_Malakh_Own` + `PHYS_Malakh_Own` + `IK_Malakh` + `ABP_Malakh_Retarget` en `/Game/Tripo/Malakh_Scale1v2/`
- `RTG_DCS_to_Malakh` en `/Game/DynamicCombatSystem/Demo/Meshes/Mannequins/Meshes/` (Source `IK_DCS` / Target `IK_Malakh`)
- `SKM_Manny` + `ABP_CombatCharacter` en CharacterMesh0
- No existen assets `_100`
- AccuRig (`SKM_Malakh_AccuRig_UE5`) NO comparte huesos UE5 de DCS Manny (nombres Tripo: Root/Hip/Pelvis) → no sirve Copy Pose directo

### Cambios aplicados (compilado + guardado)
**CharacterMesh0 (Manny fuente):**
- Visible=true, HiddenInGame=false
- RenderInMainPass/Depth/CustomDepth=false, CastShadow=false
- AlwaysTickPoseAndRefreshBones, Scale 1,1,1
- Mesh/AnimBP DCS intactos

**MalakMesh:**
- Mesh = SKM_Malakh_Own
- Scale final **1.7** (antes 100)
- Visible, RenderInMainPass=true
- Durante el diagnostico se uso **AnimationCustomMode** temporalmente para confirmar el body en A-pose.
- Estado final: **AnimationMode = AnimationBlueprint**, AnimClass = `ABP_Malakh_Retarget`.
- Parent = CharacterMesh0 confirmado

**RTG_DCS_to_Malakh:**
- TargetMeshScale: 100 → **1** (coherente con Scale1v2)
- TargetMeshOffset → 0
- En ABP node: customRetargetProfile con translationAlpha=0, bEnableFK=true (no bastó solo: OpStack del asset sigue lanzando Z)

### Resultado PIE
- Estatico (sin ABP): Malakh **visible**, actor/capsule scale 1, Manny no se dibuja, espada/escudo DCS siguen
- El primer intento con ABP enviaba Malakh al cielo. Este estado historico queda **superado por el workaround documentado abajo**.

## 2026-08-09 (tarde) — Malakh visible Y animado en PIE (RESUELTO via MCP)

### Diagnostico definitivo (con datos runtime)
Se instrumento un probe temporal por Blueprint que imprimia `GetSocketLocation` de los huesos
de MalakMesh cada segundo durante PIE:

- Actor: Z = -429.7 (correcto, en el suelo, scale 1,1,1)
- MalakMesh (componente): Z = -526.7 (correcto)
- **Hueso Pelvis: Z = +8206.762 (constante exacta entre frames y sesiones)**
- Hueso Head: Z = +8260 y variaba frame a frame → la animacion FK **si funcionaba**

Conclusion: TODA la pose venia desplazada una constante de **+5137 unidades en espacio del mesh**
(~51.37 × 100 = la altura de la pelvis multiplicada por 100). Es el clasico dato x100 guardado
dentro de la **Retarget Pose del target** en `RTG_DCS_to_Malakh` (RootTranslationOffset corrupto,
producto de los experimentos con TargetMeshScale=100). No era la logica del personaje ni la op
de Pelvis Motion.

### Intentos que NO funcionaron (documentado para no repetir)
1. Legacy `rootSettings/globalSettings` en customRetargetProfile del nodo (UE 5.8 los ignora, usa Op Stack).
2. Forzar `targetRetargetPoseName = "Default Pose"` via perfil → sin efecto (la pose corrupta ES la Default).
3. `retargetOpProfiles` tipado con `/Script/IKRig.IKRetargetPelvisMotionOpSettings`
   (translationAlpha=0, bEnabled=false, translationOffsetGlobal=-5090) → **ninguno tuvo efecto en runtime**;
   en este build el customRetargetProfile del nodo no llega al procesador.
4. El Op Stack y las Retarget Poses del asset RTG son propiedades privadas: MCP no puede editarlas.

### Fix inicial aplicado (workaround determinista, escala 1.7)
Como el desplazamiento es una constante perfecta, se cancelo a nivel de componente:

- `BP_Malakh_DCS` → `MalakMesh.RelativeLocation = (0, 0, -8646.2)`
- `MalakMesh.AnimationMode = AnimationBlueprint` (ABP_Malakh_Retarget reactivado)
- Verificado en PIE: Pelvis queda en Z = -439.4 (altura correcta), Head anima frame a frame

### Resultado PIE final (verificado visualmente por captura)
- Malakh **visible**, de pie sobre el suelo y animado
- Animado via retarget FK (idle sway confirmado por posiciones de Head variables)
- Espada y escudo DCS visibles y unidos
- Manny sigue generando la animacion sin renderizarse
- Bounds del actor normalizados (Z max: 8534 → 680)
- Assets compilados y guardados; probe de debug eliminado (HUDSpawner restaurado)

### ADVERTENCIA importante
El `RelativeLocation.Z = -8646.2` actual de MalakMesh **compensa la pose corrupta del Retargeter**
con su escala final 1.7.
Si algun dia se corrige la Retarget Pose del target en `RTG_DCS_to_Malakh` (opcion correcta:
en el editor del Retargeter, Target → Retarget Pose → Reset o poner el offset de traslacion
del root/pelvis en 0), hay que **volver a poner MalakMesh RelativeLocation en (0,0,0)**.
Tambien depende de la escala del componente: si cambia la escala, recalcular el offset
(offset local base observado = -5086 UU; `offset final ≈ -5086 × escala del componente`;
con escala 1.7 → aproximadamente -8646.2). No reutilizar este numero a ciegas en otro personaje:
medir primero su error runtime.

### Limitacion conocida del workaround
La traslacion de la pelvis queda congelada (no hay bob vertical en locomocion ni crouch
con desplazamiento de cadera); rotaciones y extremidades animan normal. Se corrige de raiz
arreglando la Retarget Pose y quitando el offset.

### Prueba de altura 1.8 y reversion (2026-08-09)

Se probo temporalmente aumentar solamente el componente visual:

- `MalakMesh.RelativeScale3D`: `(1.7,1.7,1.7)` → `(1.8,1.8,1.8)`.
- `MalakMesh.RelativeLocation.Z`: `-8646.2` → `-9154.8`.

La prueba funciono, pero visualmente la escala original era preferible. Por solicitud del usuario
se revirtio y el **estado final guardado** es:

- `MalakMesh.RelativeScale3D = (1.7,1.7,1.7)`.
- `MalakMesh.RelativeLocation = (0,0,-8646.2)`.
- Actor, Capsule y CharacterMesh0 permanecen en escala `(1,1,1)`.
- `AnimationMode=AnimationBlueprint` y `ABP_Malakh_Retarget` permanecen activos.
- Blueprint compilado y guardado por MCP.

## Procedimiento reutilizable — Personaje Tripo como visual de DCS

Esta es la receta recomendada para los proximos personajes creados en Tripo que deban usar
locomocion, ataques, bloqueos, montages y equipo del Dynamic Combat System.

### Principio de arquitectura

```text
BP_<Personaje>_DCS
└── CapsuleComponent                  escala 1,1,1; colision y movimiento
    └── Mesh / CharacterMesh0         Manny; AnimBP original de DCS
        └── <Personaje>Mesh           personaje Tripo visible
```

- **Nunca reemplazar Manny en CharacterMesh0.** DCS necesita su skeleton, AnimBP, montages,
  sockets y logica de equipamiento originales.
- Manny debe permanecer activo y animando, pero sin render:
  `Visible=true`, `HiddenInGame=false`, `RenderInMainPass=false`,
  `RenderInDepthPass=false`, `RenderCustomDepth=false`, `CastShadow=false`,
  `AlwaysTickPoseAndRefreshBones`, escala `1,1,1`.
- El mesh Tripo es solo la representacion visual:
  `NoCollision`, visible, render main/depth, `UseAttachParentBound=false`,
  `AlwaysTickPoseAndRefreshBones`; es hijo directo de CharacterMesh0.
- Actor, Capsule y Manny siempre quedan en escala `1,1,1`. Ajustar provisionalmente solo
  el componente visual Tripo. No usar World Settings para corregir escala.

### 1. Importacion segura y nomenclatura

No sobrescribir assets originales de DCS ni reemplazar una importacion Tripo que ya se use.
Crear assets nuevos por personaje:

```text
/Game/Tripo/<Personaje>/
SKM_<Personaje>
SK_<Personaje>
PHYS_<Personaje>
IK_<Personaje>
RTG_DCS_to_<Personaje>
ABP_<Personaje>_Retarget
BP_<Personaje>_DCS
```

Importar el FBX con Skeleton=None, auto-select skeleton desactivado, animations off y
physics asset on. Primero medir el mesh en Unreal:

- Un humano normal debe medir aproximadamente 170-200 UU de alto.
- Si mide ~1-2 UU, la conversion metros→centimetros sigue incorrecta: preferir reimportar
  una **copia nueva** con escala uniforme 100.
- Si mide ~100 UU como `SKM_Malakh_Own`, no aplicar escala 100 al componente. Usar una
  escala visual razonable (Malakh usa 1.7).
- `Target Mesh Scale` del Retargeter es solo preview; no corrige runtime.

### 2. Validacion estatica obligatoria

Antes de tocar IK o retargeting:

1. Asignar el SKM Tripo al componente visual.
2. Poner `AnimationMode=AnimationCustomMode`, sin animacion.
3. Confirmar geometria, materiales, reference pose, escala y bounds.
4. Probar en Viewport y PIE.

Interpretacion:

- Invisible estatico → problema de importacion, materiales, transform, bounds o visibilidad.
- Visible estatico pero falla con ABP → problema de IK Rig, Retargeter o Retarget Pose.
- Visible en Blueprint pero no en PIE → buscar overrides runtime de mesh, escala o visibilidad.

No diagnosticar cadenas hasta que esta prueba estatica pase.

### 3. IK Rig y Retargeter

- Source IK Rig: el IK Rig de Manny/DCS (`IK_DCS` en esta integracion).
- Target IK Rig: `IK_<Personaje>` con preview mesh del personaje.
- Elegir el hueso de cadera real (`Pelvis`, `Hips`, `Hip`, etc.) como Retarget Root/Pelvis.
- Crear y revisar cadenas principales: pelvis, spine, neck, head, brazos, manos, piernas y pies.
- Operation Stack minimo comprobado:

```text
Pelvis Motion
FK Chains
```

- No borrar `FK Chains`: sin esta operacion solo se desplaza el cuerpo y las extremidades
  quedan rigidas.
- Base FK: enabled, Interpolated, rotation alpha 1, translation mode None.
- Base Pelvis Motion: translation alpha 0, rotation alpha 1.
- Evitar editar escala de huesos en Current Retarget Pose.
- Mantener `TargetMeshScale=1` salvo que se necesite exclusivamente para inspeccion visual.

### 4. Animation Blueprint destino

Crear `ABP_<Personaje>_Retarget` sobre el skeleton propio del personaje:

```text
Retarget Pose From Mesh → Output Pose
```

Configurar:

- IK Retargeter = `RTG_DCS_to_<Personaje>`.
- Retarget From = Parent Skeletal Mesh Component.
- No usar Copy Pose From Mesh entre skeletons diferentes.
- Componente visual: `AnimationMode=AnimationBlueprint`,
  `AnimClass=ABP_<Personaje>_Retarget`.

### 5. Diagnostico runtime si el cuerpo desaparece o vuela

No asumir que es culling. Medir en PIE:

1. Actor location/scale.
2. Componente visual world location y relative transform.
3. `GetSocketLocation` de root, pelvis y head.
4. Bounds del actor.

Patrones:

- Actor/componente correctos, pero root/pelvis/head miles de UU lejos: pose/retarget corrupto.
- Pelvis constante lejos y Head cambia entre frames: FK funciona; toda la pose tiene un
  offset constante.
- Bounds enormes con el Actor en el suelo: los huesos animados estan fuera, no es la capsula.
- Huesos inmoviles: revisar FK Chains, chain mappings y tick order.

Para instrumentar temporalmente se puede usar un actor de diagnostico con timer y
`GetSocketLocation`. Eliminar el actor, funcion y prints al terminar.

### 6. Workaround de offset constante

Usarlo solamente cuando MCP no pueda editar la Retarget Pose privada y se confirme que el
error es constante:

1. Medir `PelvisWorldZ` durante varios frames.
2. Definir la altura deseada de pelvis sobre el Actor.
3. Calcular la compensacion local considerando `RelativeScale3D`.
4. Aplicarla solo a `<Personaje>Mesh.RelativeLocation.Z`.
5. Verificar pelvis/head, bounds, locomocion, ataques, bloqueo y equipo en PIE.
6. Registrar el valor, escala, mediciones y captura por personaje.

No copiar `-8646.2` a otro personaje. Ese valor pertenece a Malakh, su pose corrupta y
su escala 1.7.

Arreglo definitivo cuando se tenga acceso manual al asset:

1. Abrir `RTG_DCS_to_<Personaje>`.
2. Target → Retarget Pose.
3. Resetear la pose o dejar la traslacion del root/pelvis en cero.
4. Guardar y verificar PIE.
5. Volver `<Personaje>Mesh.RelativeLocation` a `(0,0,0)`.

### 7. Checklist de aceptacion por personaje

- Mesh visible estatico y con ABP.
- Actor, Capsule y Manny en escala `1,1,1`.
- Manny invisible pero animando con el AnimBP original de DCS.
- Personaje Tripo en el suelo, escala humana y bounds razonables.
- Brazos, manos, columna, piernas y pies se animan.
- Locomocion, equipar, atacar y bloquear funcionan.
- Espada/escudo siguen unidos correctamente mediante DCS.
- No desaparece por distancia ni culling.
- Blueprint/ABP/IK/RTG compilados y guardados.
- No se modificaron destructivamente assets originales de DCS.
- Cualquier workaround queda documentado con valores medidos y condicion para retirarlo.

## Nivel: El Claro (L_DA_Malkuth_Claro_POC) - 2026-08-12

Beat 04/13 del PDF (El Claro - Hueste Mixta). Creado desde cero duplicando la base
visual del Jardin (misma luz/cielo/niebla/landscape/montanas lejanas) y limpiando
todo el contenido del jardin (setos, topiarios, rio, coloso, abetos del valle).

Composicion (centro de arena en X=8000, Y=0, suelo Z=-40):

- Anillo doble de acantilados QuarryCliff (25 piezas) cerrando el claro; hueco de
  entrada al sur y puerta al norte. Carpeta Claro/Acantilados.
- Puerta norte: piramide escalonada de bloques AngkorWatTempleStones + plataforma,
  2 hojas SM_MedievalModularDoor3x2M con M_DA_MK_Pale_Gold, columnas MRK flanqueando,
  2 PointLights calidos, roca QuarryCliff de fondo. Carpeta Claro/Puerta.
- 12 bloques de ruina Angkor + columna caida + escombros MRK. Carpeta Claro/Bloques.
- Vegetacion: 44 abetos PN full sobre las cimas (trace_world para asentarlos),
  46 helechos en bases y bloques, 30 flores (Crownbeard/WhiteEverlasting/Lily),
  12 GroundCover. Carpeta Claro/Vegetacion.
- Hueste: 4 siluetas emisivas SM_DA_AngelV2 (2 Vigilantes, Lancero, Arquero sobre
  bloques apilados en Z=344) + PointLight dorado a los pies de cada uno + 2 estatuas
  flanqueando la escalinata. Carpeta Claro/Hueste. SIN gameplay todavia (los
  BP_Angel_Messenger son graybox cilindro+esfera; se retiraron por fidelidad visual).
- PlayerStart en (8000, -1650) mirando yaw 90 hacia la puerta.
- Sol TEMP_Sun: pitch -40, yaw 70 (desde detras del jugador, bana la cara de la
  puerta), intensidad 9, temperatura 4300K.

Aprendizajes:

- SM_CastleStairs de Megascans es UN solo escalon, no una escalera.
- SM_MP_Stair_Wide_600x600 del PropsKit se deforma gigante al colocarlo (revisar export).
- SM_DA_AngelV2 funciona a media/larga distancia; de cerca se ve voxel.
- SK_MAP_Archangel lee como tablones blancos (alas de tarjetas), no usar para hueste.

Pendiente proximo pase: mas brillo/presencia del oro de la puerta, niebla suave de
distancia, NavMesh + enemigos reales cuando exista arte de angeles, conexion con
el Jardin (corredor sur).

### Correccion de puerta y escalinata (feedback usuario, 2026-08-12)

- La piramide de bloques Angkor NO era subible (160cm por fila > max step height).
  Reemplazada por SM_CastleStairs_02 (escalera completa de Megascans con muretes,
  332x455x166) escala (2.0, 2.0, 1.8) = ~30cm por escalon, subible caminando.
- La puerta ahora es SM_MedievalModularDoor3x2M CON SU MATERIAL ORIGINAL (porton
  doble de madera con herrajes, se distingue como puerta). OJO: a yaw 0 se ve su
  TRASERA (refuerzos en X, tablas con backface culling = invisible); debe ir a
  yaw 180 para mostrar la cara frontal hacia el sur.
- BP_DoorToMirrorChapel descartada para esto: es solo un marco abierto con tablas,
  no un porton monumental cerrado.
- Eje real de la abertura norte del anillo: x=8250 (no 8000); cara de roca de fondo
  en y~3255 (medida con trace_world). Puerta adosada a esa cara sobre plinto de 2
  bloques Angkor apilados (top z=264).
- Cliff_In_2 movido a (10250, 3000) y GateRock_L/R a (6950/9550, 3950) porque
  tapaban el nicho.

REGLA DE FLUJO: antes de elegir un asset para una construccion, revisar el Content
completo desde el Parent (find_assets en /Game + CaptureAssetImage + get_bounds de
los candidatos). No asumir por el nombre: SM_CastleStairs es UN escalon,
SM_CastleStairs_01/_02 son escaleras completas.

### Alineacion fina de la puerta (2026-08-12)

- SM_MedievalModularDoor3x2M tiene el PIVOTE EN LA ESQUINA (bounds locales x[0,300]),
  no en el centro: al colocarla por location queda corrida media anchura (~390cm a
  escala 2.6). Compensar: loc_x = centro_deseado + escala_x * 150.
- Metodo correcto de ensamblaje: leer bounds locales (StaticMeshTools.get_bounds) y
  calcular el AABB mundial con yaw/escala para poner caras al ras, en lugar de
  posicionar a ojo. Valores finales: escalera top y=3008 z=232; plinto frente
  al ras en y=3008, top z=232; puerta base z=232.5, cara frontal y=3068,
  centrada en x=8245.

### Playtest PIE y correcciones (2026-08-12, tarde)

- Escalera pegada a la puerta: Claro_Escalera movida a y=2600 para que el ultimo
  escalon toque la cara frontal del porton (y=3068). Sin hueco.
- BUG ENCONTRADO EN PIE: los 4 angeles de la hueste (SM_DA_AngelV2) estaban
  ENTERRADOS 2.4m. El pivote del mesh esta 200cm ARRIBA de los pies (bounds
  locales z[-200, 90]); al colocarlos con z=suelo solo asomaban cabeza/alas y se
  veian como manchas blancas acostadas. Regla: z_actor = superficie + 200 * escala.
  Corregidos: Vigilante1/Lancero z=200, Vigilante2 z=210, Arquero z=642 (sobre
  bloques, tope real en z=422 medido con trace_world).
- OJO trace_world: devuelve la DISTANCIA (float) desde start, no un hit struct.
  z_impacto = start_z - distancia. Ademas puede chocar con el propio mesh que se
  quiere asentar (a los angeles enterrados les pegaba en la cabeza): validar el
  resultado contra el suelo esperado.
- Estatuas flanqueantes: mismas SM_DA_AngelV2 pero ahora con override
  M_MRK_Stone_Ivory (sin brillo, leen como estatuas de piedra) paradas SOBRE sus
  pedestales SM_MRK_StatueBase_200 (150cm alto, pivote en base), simetricas al eje
  de la escalera en x=8250+-650, y=2300. Solo la hueste del campo queda emisiva.
- Luz Claro_Vigilante_1_Glow bajada a intensidad 3 / radio 600: sobreexponia la
  columna caida de marfil y se veia como bloque blanco desde lejos.
- FALSA ALARMA: patron de tablero de ajedrez en el cielo tras los abetos en las
  capturas = ghosting del antialiasing temporal al teletransportar la camara de
  captura (desaparece al capturar dos veces seguidas). NO es material roto; no
  forzar LODs por esto.

## Master: conexion Jardin + Claro + Santuario (2026-08-12)

`L_DA_Malkuth_Master` ya tenia hitos del plano PDF y Level Instances de
Jardin (-60000,-60000), Santuario (44000,48000), Anfiteatro y Gabriel.
Faltaba El Claro.

- LI_04_ElClaro en el hito 04 (36000, -12000, 0), DesiredRuntimeBehavior
  Partitioned, carpeta Secciones. Arena mundial ~ (44000, -12000).
- Paso norte del Claro: GateRock_Back corrido a y=-5000 y cliffs Out_2/Out_3
  abiertos para dejar un hueco caminable detras del porton (la ruta que se abre).
- Corredor Jardin->Claro (Conexiones/JardinClaro): senda SM_MGK_Path_Straight_600
  + setos a ambos lados desde el fin del Sendero (-25500,-59800) hasta la boca
  sur del Claro (44000,-15000). El landscape del Master y el del Claro se
  solapan en x[5600,10400], y[-62400,-9600]: se puede CAMINAR sin teletransporte.
- Corredor Claro->Santuario (Conexiones/ClaroSantuario): misma senda+setos desde
  detras de la puerta (44000,-6800) hasta el spawn del Santuario (42850,47200).
  Suelo extra Conn_CS_Ground (hierba del valle) cubre el hueco donde termina el
  landscape del Claro (y=38400) y empieza el templo (y=48000).
- PlayerStart persistente del Master movido al spawn del Jardin
  (-59649,-60004,112). OJO: los subniveles siguen teniendo sus propios
  PlayerStart; PIE puede elegir otro al azar. Si spawneas en Anfiteatro/Gabriel,
  usa el PS del Jardin.
- Zone triggers (BP_DA_ZoneTrigger) en las tres entradas.
- Luces: cada LI trae su DirectionalLight (aviso de Forward Shading). El sol
  persistente del Master tiene ForwardShadingPriority=10.

## Nivel: Puente Ascendente (L_DA_Malkuth_Puente_POC) - 2026-08-12

Beat 07/13 del PDF (Puente de Agua Ascendente - Trampa Celestial: agua invertida,
patron de picos, Angel gigante como orientacion. Objetivo: "Cruza entre los pulsos
de picos"). Duplicado de la base visual del Jardin, limpiado igual que El Claro
(602 actores: Jardin/*, Valle/*, Fondo/Coloso).

OJO WORLD PARTITION: al cargar un mapa duplicado, los actores espaciales quedan
DESCARGADOS en el editor (find_actors solo ve ~111 de 700+; get_actors_in_folder
falla con "Folder does not exist" aunque get_folders si lista las carpetas). No
hay tool para cargar celdas. WORKAROUND: crear un LevelInstance del mapa dentro
del Master, edit_level_instance (carga TODO), borrar ahi, commit, borrar el LI y
recien entonces cargar el mapa directo (lo que queda si esta cargado).

Composicion (eje del puente x=0, sur->norte ascendiendo; suelo del valle z=-40):

- Puente: 10 x SM_MP_Bridge_Wide_600x1200 inclinados ROLL=-14 (en UE roll
  negativo = extremo -Y del mesh baja; el pivote esta en el extremo +Y ALTO).
  Pivote i: y = -4624.76 + i*1164.35, z = 216.64 + i*290.31. Deck: z(y) = -30 +
  (y+5800)*tan(14). Arranca al ras del suelo (-30 vs suelo -32) en y=-5800 y
  termina en y=5844 z=2872. 80 barandales SM_MP_BridgeRailing_300 siguiendo la
  pendiente (misma rotacion, offset local (+-290, -d, 45) rotado a mano) y 5
  pilares SM_MP_Bridge_Pillar escalados hasta el agua.
- Picos del deck: SM_MRK_Obelisk_400 escala (0.5,0.5,1.1) con M_DA_MK_Salt_Crystal,
  4 filas (y=-3000,-800,1400,3600) de 2 picos c/u con HUECO alternado (x=180,
  -180, 0, 180) para poder zigzaguear. Estaticos por ahora: el "pulso" (subir/
  bajar temporizado) queda pendiente como gameplay.
- Abismo: plano de agua M_DA_MK_Agua_Quieta (95x150m) bajo el puente + 8 picos
  gigantes Obelisk_700 de cristal saliendo del agua.
- Agua invertida: 24 planos verticales (SM_DA_GroundPlane pitch 90) con
  M_DA_MK_Water_Upward: 5 pares de cortinas flanqueando el puente (x=+-750,
  altura deck+600) + 2 cascadas grandes (8m ancho, 37m alto) junto a la mesa
  norte. Cada cortina son 2 planos espalda con espalda (yaw 0+180) por el
  backface culling.
- Canon: 10 QuarryCliff_01 escala 3 x lado (x=+-3300) con altura creciente
  (sz 2.6->5.6) + 2 flancos sur + mesa norte (3 cliffs sz 6.6-7.0 de fondo y
  2 sub-soportes bajo la plataforma).
- Plataforma norte: SM_DA_GroundPlane (16x20m) con M_MGK_Stone_Ivory en z=2872,
  al ras del final del puente (verificado con trazas: 2872 continuo en la union
  y=5870). Portal de 2 Obelisk_700 dorados (M_DA_MK_Pale_Gold) + 2 PointLights
  calidas. BUG CORREGIDO: Puente_Mesa_2 atravesaba la plataforma (roca a z=3077);
  movida a y=9600 como telon de fondo.
- Angel gigante: SM_SM_DA_AngelSilueta escala 45 (154m de envergadura) en
  (0, 16000, 6000) yaw 270, flotando tras la plataforma + 3 BP_CelestialRay.
- Sol TEMP_Sun: pitch -22, yaw 270 (desde el NORTE, detras del angel = contraluz
  al ascender), intensidad 8, temperatura 4800K. Propiedad del componente:
  bUseTemperature (con b, no useTemperature).
- PS_Puente en (0,-6600,72) yaw 90 + BP_DA_ZoneTrigger "Puente Ascendente" /
  "Cruza entre los pulsos de picos" en la entrada.

QA por trazas (el viewport del usuario quedo en modo Top ortografico y
CaptureViewport/PIE solo devuelven esa proyeccion; sin captura en perspectiva):

- Deck continuo y monotono cada 300cm de y=-5800 a 5844, sin huecos.
- Picos: fila y=-3000 golpea a z=1072 en x=-180/0 y deja libre x=180.
- Union puente->plataforma al ras (2872/2872). Escalon de entrada sur: 2cm.

LECCION set_actor_transform: un xform PARCIAL (solo rotation) RESETEA location a
(0,0,0) en la practica. Pasar SIEMPRE location+rotation+scale completos al mover
actores existentes.

Pendiente Puente: pulso temporizado de los picos (gameplay), verificacion visual
en perspectiva, conexion en el Master (LI + corredor), oro/bloom del portal.

### Fix "el puente no tiene colision" (feedback usuario, 2026-08-12 noche)

El puente SI tenia colision (1 convex hull por modulo); el bug real era el SPAWN:

- PS_Puente estaba a z=72 pero el pawn DCS necesita ~z=suelo+156 para spawnear
  sin encroachment (suelo -32 => minimo ~124). Al spawnear enterrado 52cm, la
  resolucion de colision lo empujaba HACIA ABAJO y caia al LECHO DEL RIO del
  landscape heredado del Jardin (z~-90), POR DEBAJO del plano de agua: desde ahi
  el puente es una pared y "no se puede subir". Reproducido con spawn de prueba
  en PIE (pawn terminaba en z=-90). Fix: PS_Puente a z=145.
  REGLA: PlayerStart a suelo + ~150, igual que el del Jardin (112 sobre -40).
- Bonus arreglado: el convex hull del SM_MP_Bridge_Wide_600x1200 queda hasta
  66cm POR ENCIMA del deck visible a mitad de modulo (el hull une los picos de
  los extremos): el pawn "flotaba" al caminar. Puesto
  bodySetup.collisionTraceFlag = CTF_UseComplexAsSimple en el mesh (guardado en
  el asset, tambien beneficia al V2). Verificado en PIE: pies exactamente sobre
  el deck (z pawn 2014 = deck 1915 + capsula ~99) y estable en la rampa de 14.
- Diagnostico util: spawnear el pawn con StartPIE startTransform y leer su Z con
  find_actors(actor_type=/Script/Engine.Character) a los 3s: si z-capsula no da
  la superficie esperada, esta parado en otra cosa (hull, agua, lecho).
- OJO CaptureViewport: captura el viewport de NIVEL activo; si el usuario lo
  dejo en Top ortografico, todas las capturas (incluso con PIE corriendo en otro
  panel) salen top-down. Sin tool para cambiar la proyeccion.

### Pase visual del Puente + workaround de captura en perspectiva (2026-08-12)

WORKAROUND CAPTURA EN PERSPECTIVA (clave para todo QA visual futuro):
StartPIE con playMode=PlayMode_InEditorFloating + startTransform donde se quiera
inspeccionar, y luego CaptureEditorImage: la ventana flotante de PIE SI sale en
la captura del escritorio del editor, en perspectiva 3a persona real con HUD.
Recortar la region de la ventana (aprox rect 893,0,387,240 en captura 1280x494)
con System.Drawing y ampliar. Verificado: trigger "Puente Ascendente" aparece,
pawn sobre el deck, colision OK.

Cortinas de agua rehechas: los 20 planos anchos flotantes (5 pares por lado) se
veian como rectangulos blancos; reemplazados por 12 columnas en CRUZ (2 planos
de 1.7-2.6m de ancho con yaw 0/90) que nacen EN el agua del abismo (z=-32) y
suben hasta deck+500, alternando lado y radio (x=+-680..1100). Leccion:
M_DA_MK_Water_Upward es translucent + twoSided => NO hacen falta pares
espalda-con-espalda; la cruz da volumen desde cualquier angulo. Las 2 cascadas
de la mesa tambien convertidas a cruz (plano B yaw 90 en vez de 180).

Estado visual verificado en PIE (sur, y mitad del puente): puente ascendente
hacia angel luminoso central (M_DA_AngelLuz emisivo), columnas de agua
flanqueando, canon enmarcando, agua reflejante abajo. Muy blanco/bloom al centro
pero coincide con "trampa celestial" + majestuosidad divina del PDF (beat 7).

### Integracion Master: 12 zonas conectadas + niveles _Sub (2026-08-12)

Master (L_DA_Malkuth_Master) ahora contiene los 13 beats del PDF como Level
Instances conectados por senderos (SM_MGK_Path_Straight_600, escala 1.3x3,
z=-38, piezas cada ~2000; el suelo global es SM_Plano_Referencia a z=-50).

Posiciones de LIs nuevos (z=0 salvo indicado):
- LI_03_MiradorSariel (-16000,-24000) ramal desde el sendero Jardin-Claro
- LI_05_RuinasGazebo (64000,16000) ramal al este del Claro
- LI_07_PuenteAscendente (16000,60000, yaw 90, z=-4) tras el Santuario
- LI_09_ElevadorTrono (-74000,8000) al sur del Anfiteatro
- LI_10_GabrielC1 (-40000,-15000); LI_11_GabrielC2 (renombrado, ex LI_10_12)
- LI_12_GabrielC3 (-92000,-15000); LI_13_PortalYesod (-92000,16000)
Corredores: JardinMirador, ClaroGazebo, SantuarioPuente, PuenteAnfiteatro,
AnfiteatroElevador, ElevadorGabrielC1, GabrielC1C2, C2C3, C3Yesod (139 piezas
en carpetas Conexiones/*).

LECCION CLAVE - niveles _Sub sin entorno: cada POC arrastra su propio entorno
(TEMP_Sun/Atm/Sky/Fog/PP/Cloud + PlayerStart + Landscape + ~93 montanas
Monte_Lejos/Aguja/Monte_Medio/Ladera + WaterZone heredadas de la BaseVisual).
Meterlos directo como LI al Master duplica soles/cielos y planta anillos de
montanas sobre las zonas. Solucion: duplicar cada POC a L_DA_Malkuth_*_Sub y
ahi borrar los 7 actores de entorno (en los 10: Mirador, Gazebo, Puente,
Elevador, GabrielC1, GabrielC3, Yesod, Jardin, Claro, Gabriel) y ademas las 96
piezas de escenografia+landscape en los 6 nuevos de interior (el Puente_Sub
conserva su canon/mesa/agua porque es parte del beat). Los LIs del Master
apuntan a los _Sub; los *_POC originales quedan intactos para trabajo
individual. Resultado verificado: 1 DirectionalLight, 1 SkyAtmosphere, 1 PPV
en el Master.

Ademas se borraron 12 montanas puntuales que invadian zonas jugables: 11 en
Jardin_Sub (Monte_Lejos 15/18/20/24/26/27, Ladera 69/70/86/90/92) y Ladera_89
en Puente_Sub (bloqueaba el corredor Claro-Gazebo). Deteccion: bounds de cada
montana vs circulo de zona / distancia a segmento de corredor.

Playtest en PIE (ventana flotante + captura de escritorio, recorte
893,0,387,240): spawn por defecto cae en el Jardin (PS_Master_Jardin); Mirador
con estatua y luz de llave visibles desde el sendero; trigger "Ruinas del
Gazebo" dispara; acceso al Puente con canon y columnas de agua; Elevador con
rayo celestial entre acantilados (muy PDF); Gabriel C1/C3 con portales
iluminados; ascenso a Yesod legible con obeliscos. Trazas de suelo continuas
en las 12 zonas y 9 corredores (sendero z=-26, suelo -50, escalon 24cm
caminable).

## Revision visual del Master zona por zona (2026-08-12, sesion Claude Code)

Recorrido de las 12 Level Instances con el workaround de PIE flotante
(`StartPIE` playMode=PlayMode_InEditorFloating + startTransform, luego
`CaptureEditorImage` y recortar la esquina superior derecha ~70% del ancho x 47%
del alto). Confirmado: `CaptureViewport` es inutil mientras el viewport de nivel
este en ortografico (sale la regla de "10cm" y capturas dentro de las mallas).

### CAUSA RAIZ del blanqueo general: la NIEBLA, no las luces

Auditado el mundo del Master: **1 DirectionalLight, 1 SkyAtmosphere, 1
ExponentialHeightFog, 1 PostProcessVolume, 1 SkyLight**. No habia soles
duplicados. El lavado venia de tres valores del `Fog_Malkuth`:

| Valor | Antes | Ahora | Por que |
|---|---|---|---|
| `fogDensity` | 0.055 | **0.006** | 0.055 disuelve todo mas alla de ~300 m en un mundo de 1,8 km |
| `fogMaxOpacity` | 0.85 | **0.45** | techo de opacidad demasiado alto |
| `directionalInscatteringLuminance` | (1.3, 0.85, 0.42) | **(0.10, 0.08, 0.06)** | era el halo ambar que tenia todo del color del sol |
| `volumetricFogExtinctionScale` | 1.1 | 0.35 | |
| `fogInscatteringLuminance` | — | (0.22,0.26,0.34) | azul frio de aire, en vez de crema |

Ademas sol subido de pitch -24 a **-38** (intensidad 5.2, 5600K,
volumetricScattering 2.2 -> 0.8) y PP con auto-exposicion 0.06-6.0, bias 0.35,
bloom 0.45 con umbral 1.25, film slope 0.95 / toe 0.62 / shoulder 0.22.

Resultado: el valle del Jardin pasa de crema uniforme a verde legible con
coniferas y setos visibles a ambos lados.

### Estado por zona (contra el PDF)

- **01 Jardin** — lo mejor tras el arreglo de niebla. FALTA: el coloso no se ve
  desde el spawn (deberia dominar el fondo segun el beat 01); el sendero es una
  cinta de losas con borde duro, no una vereda de tierra; sabana especular en la
  hierba a contraluz.
- **04 El Claro** — no evaluado en condiciones: el spawn de prueba (44000,-15500)
  cae contra una cara de acantilado. Usar el PS real del Claro.
- **06 Santuario** — el que mas se acerca al PDF: contraluz por la abertura,
  hiedra, helechos, musgo, rayos volumetricos. FALTA: el centro se sobreexpone y
  se come el altar y a Cassiel.
- **07 Puente Ascendente** — composicion correcta (rampa, columnas de agua,
  canon, angel al fondo, agua reflejante). FALTA: todo es blanco puro sin
  definicion de material; el angel gigante lee como una cruz blanca, no como
  angel.
- **08 Anfiteatro** — se distinguen columnas y obeliscos en el horizonte pero el
  graderio se pierde en la bruma. FALTA: revisar tras el cambio de niebla; la
  hierba tapa el empedrado de la arena.
- **11 Gabriel C2** — la mejor de las tres camaras: sala circular, hornacinas de
  espejo reflejando, agua reflejante, boveda. FALTA: sobreexpuesto al centro;
  Gabriel sigue siendo `SM_DA_AngelV2` (placeholder plano).
- **13 Portal a Yesod** — legible (senda, escalinata, portal luminoso, obeliscos
  morados). FALTA: los dos focos del portal revientan a blanco; falta el viraje
  oro->purpura que pide el beat 13.

### Patron transversal

Casi todas las zonas comparten dos defectos: **sobreexposicion en el foco de
interes** (focos locales demasiado intensos con la exposicion automatica del
Master) y **placeholders de angel** (`SM_DA_AngelV2` / `SM_SM_DA_AngelSilueta`)
que a corta distancia no leen como personaje. El segundo no se arregla con
ajustes: necesita arte de angel propio.

## REGLA DE MAPAS: el _Sub manda (2026-08-12)

Establecida tras romper el Puente por editar los dos gemelos como si fueran iguales.

**La regla, en una linea: todo cambio va al `_Sub`. El Master apunta al `_Sub`. Los
`_POC` son archivo de solo lectura.**

Por que: mantener dos copias del mismo nivel sin mecanismo de sincronizacion ya
costo un fallo real. Se ensancho la calzada del Puente a 18 m **solo en el Sub**;
al aplicar despues un arreglo de barandales a los dos mapas por igual con el
borde del Sub (|x|=878), en el POC —cuya calzada llega a ±300— quedaron 60
barandales flotando a 6 m sobre el vacio. Duplicar el arreglo no arregla la
duplicacion.

### Estado tras la limpieza

Ahora **las 12 zonas tienen `_Sub`** y el Master apunta a todos. Se crearon los dos
que faltaban duplicando su POC (ya venian sin entorno global, verificado):

- `L_DA_Malkuth_Santuario_Sub`  (663 actores) ← LI_06, en (44000, 48000)
- `L_DA_Malkuth_Anfiteatro_Sub` (1205 actores) ← LI_08, en (-74000, 42000)

Las Level Instances se repuntaron borrando la vieja y recreandola con
`create_level_instance` sobre el mismo transform: es fiable, y `worldAsset` no se
puede escribir por MCP.

### PENDIENTE MANUAL: archivar los 12 POC

`AssetTools.move` **no puede mover `.umap`**: devuelve `false` sin mensaje, incluso
con el mapa descargado y la carpeta destino ya creada. No es World Partition (estos
mapas no tienen `__ExternalActors__` propios). Es limitacion de la tool.

La carpeta `/Game/DarkAngels/Maps/_Archivo/` **ya esta creada**. Hay que arrastrar
estos 12 ahi desde el Content Browser, que si gestiona los redirectors:

```
L_DA_Malkuth_Jardin_POC      L_DA_Malkuth_Claro_POC
L_DA_Malkuth_Mirador_POC     L_DA_Malkuth_Gazebo_POC
L_DA_Malkuth_Puente_POC      L_DA_Malkuth_Elevador_POC
L_DA_Malkuth_GabrielC1_POC   L_DA_Malkuth_Gabriel_POC
L_DA_Malkuth_GabrielC3_POC   L_DA_Malkuth_Yesod_POC
L_DA_Santuario_POC           L_DA_Malkuth_Anfiteatro_POC
```

Verificado con `get_referencers`: **ninguno tiene referencias externas**. Mover es
seguro. Mover, no borrar: son la red si un Sub sale mal.

### Como trabajar una seccion suelta

Los `_Sub` no tienen sol ni cielo (por eso el Master no tiene 13 soles), asi que
abrirlos solos se ven sin luz. Dos caminos:

1. **Edit Level Instance desde el Master** — camino bueno, da la iluminacion real.
2. Rig temporal de luz en el Sub, y **quitarlo antes de guardar**.

## Electric Dreams migrado: SUBSTRATE es la trampa (2026-08-12)

Migrado de `ElectricDreamsEnv` (UE 5.5) el follaje templado y el material de
landscape: KikuyuGrass, CloverVarieties, WhiteWindflower, Periwinkle, Fern,
GroundCover, LilyOfTheValley + `Content/Landscape/M_BGLandscape_Auto`.

**Sus materiales salen NEGROS.** Causa: el maestro de follaje
`/Game/Custom/CustomMaterials/.../M_MS_CustomFoliage` esta autorado para
**Substrate**. Electric Dreams tiene en su `DefaultEngine.ini`:

```
r.Substrate=True
r.Substrate.AccurateSRGB=1
r.Substrate.BytesPerPixel=170
```

y DarkAngelsPOC **no tiene ninguna linea de Substrate**. Sin el, esos materiales
no compilan bien y renderizan en negro.

**NO se activo Substrate a proposito**: es un cambio de render que afecta a TODOS
los materiales del proyecto (DCS incluido), obliga a recompilar shaders enteros y
puede cambiar el aspecto de lo ya construido. Decision: dejarlo apagado.

**Solucion aplicada:** material propio `M_DA_MK_Hierba_Kikuyu` en
`DarkAngels/Materials/Malkuth`, hecho con las texturas de Megascans que si
migraron bien (`T_KikuyuGrass_01_BC/_N/_AoRT/_T`), sin depender del maestro de ED:

- BlendMode Masked, TwoSided, ShadingModel **TwoSidedFoliage**
- BaseColor <- BC.RGB ; OpacityMask <- BC.A (clip 0.5)
- Normal <- N ; Roughness <- AoRT.G ; AO <- AoRT.R ; SubsurfaceColor <- T
- Asignado a las 7 mallas SM_KikuyuGrass_0X

**Regla general:** cualquier asset que venga de Electric Dreams (o de otro proyecto
con Substrate) necesita re-materializarse contra un maestro propio. Comprobar el
`DefaultEngine.ini` del proyecto origen ANTES de migrar materiales.

### Otra cosa que NO funciona: M_BGLandscape_Auto

Se aplico al landscape del Jardin y salio en blanco y negro. Es un material de
mezcla por capas y necesita **pesos de capa pintados** en el landscape, que el
nuestro no tiene y que no se pueden pintar por MCP. Revertido a
`M_DA_MK_Valle_Hierba`.

### Densidad de vegetacion: usar InstancedStaticMesh, no actores

Colocar matas como actores sueltos no da densidad de pradera: 900 actores sobre el
valle = una cada 4,6 m², sigue leyendo a cesped. La via buena es
`ActorTools.add_component` con `/Script/Engine.InstancedStaticMeshComponent` y
escribir `perInstanceSMData`.

Hecho en el Jardin: 4 actores ISM con 1.401 instancias cada uno = **5.604 matas de
KikuyuGrass**. La matriz de cada instancia es un `FMatrix` (xPlane/yPlane/zPlane/
wPlane); wPlane lleva la traslacion.

**OJO con el tamano del lote:** 1.401 instancias en una sola llamada hacen que la
peticion HTTP expire por timeout (`UND_ERR_HEADERS_TIMEOUT`) aunque **la escritura
SI se completa** en el editor. Verificar leyendo `perInstanceSMData` antes de
reintentar, o el trabajo se duplica. Trocear en lotes de ~300 para evitarlo.

## ESTADO POR ZONA — revision visual completa (2026-08-12, fin de sesion)

Capturado con `CaptureViewport` (funciona si el viewport de nivel esta en
**Perspectiva**; en Top ortografico devuelve basura — dejarlo SIEMPRE en
Perspectiva). Camaras usadas: posicion del LI en el Master +/- offset, mirando yaw 0.

| Beat | Zona | Estado | Que le falta |
|---|---|---|---|
| 01 | Jardin | Bueno | Terreno plano (esculpir a mano); coloso es ESFINGE |
| 03 | **Mirador Sariel** | **GRAYBOX** | Todo: caja blanca + 2 columnas + cesped |
| 04 | El Claro | Bueno | Angeles placeholder (SM_DA_AngelV2 = cruces) |
| 05 | **Ruinas Gazebo** | **CASI GRAYBOX** | Plataforma blanca + columnas; sin vegetacion ni ruina |
| 06 | Santuario | **El mejor** | Solo sobreexposicion al centro |
| 07 | Puente | Bueno | Angel gigante lee como cruz blanca |
| 08 | Anfiteatro | **REGRESION** | Manto de geometria verde/amarilla deforme en primer plano |
| 09 | **Elevador Trono** | **ROTO** | **NO TIENE SUELO** — se ve la rejilla del editor |
| 10-12 | Gabriel C1/C2/C3 | C2 bueno | Gabriel placeholder; cortinas de agua |
| 13 | Yesod | Bueno | — |

### Orden de trabajo acordado
1. **Elevador** (bug: falta suelo, no es jugable)
2. **Anfiteatro** (regresion: averiguar el manto verde del primer plano)
3. **Mirador** y **Gazebo** (construir de cero)

### Receta que YA funciona, aplicar en las tres
- Suelo: `SM_DA_GroundPlane` + `M_DA_MK_Valle_Hierba` (o `M_DA_MK_Tierra_Arena`
  para patios de combate, ver El Claro).
- Acantilados: `QuarryCliff_01/02/05` para altura, `IcelandicCliff` SOLO a ras de
  suelo (escalados leen como laminas flotantes). Nunca `GraniteRockAssembly` ni
  `IcelandicRockAssembly` en primer plano: traen madera muerta que lee a bosque
  quemado.
- Cascadas: `SM_Waterfall_Arc` + `SM_Waterfall_Base` de `/Game/WaterMaterials`
  (pack tharlevfx, CC BY - **acreditar en creditos**). Medir la pared con
  `trace_world` antes de colocar; validar que |x| no caiga sobre geometria jugable.
- Hierba densa: ISM con `SM_KikuyuGrass_0X` + `M_DA_MK_Hierba_Kikuyu` (material
  propio, NO el de Electric Dreams: Substrate).
- Piedra: `M_DA_MK_Piedra_Marfil` / `_Oscura` / `_Pulida` / `_Calzada` / `_Borde`.
- Zonas encerradas por acantilados quedan en sombra (el sol del Master viene de
  +X): meter PointLights de relleno calidas ~1500-2600, castShadows=false.

### Deuda transversal (no se arregla colocando actores)
- **El angel colosal**: bloquea el parecido en beats 01, 04, 07 y 10-12. No existe
  gratis; hay que encargarlo o esculpirlo.
- **Terreno plano**: esculpir es manual (Landscape Mode). El MCP no lo expone.
- **Rotulos del plan**: siguen colandose en encuadres. Carpeta `Plan/` en el Master,
  se pueden borrar cuando ya no hagan falta para orientarse.

## Elevador del Trono — trabajo a medias (2026-08-12, fin de contexto)

Referencia (beat 09 del PDF): plataforma circular con roseta labrada donde esta
Malakh, encajada en un POZO vertical entre paredes de roca oscuras que enmarcan
izquierda y derecha; al fondo y abajo, vacio abierto con plazas circulares
aterrazadas, cascadas por los acantilados, coniferas y una puerta gotica lejana
con luz calida. Contraste fuerte: primer plano oscuro, fondo luminoso.

### Lo que se hizo

- **BUG PRINCIPAL ERA: no habia suelo.** El nivel tenia 29 actores y ningun plano
  de suelo; se veia la rejilla del editor. Anadido `Elevador_Suelo`
  (SM_DA_GroundPlane, esc 260 = X -13000..13000, Y -10400..15600, z=-400).
- El "disco" del elevador era `SM_MRK_Pedestal_Round_120` — **1,2 m**, cuando en la
  lamina mide ~12 m. Sustituido por `Elevador_Plataforma` (Cylinder esc 12 = 1200 cm)
  + `Elevador_Roseta` (Cylinder esc 7.5 en Piedra_Pulida) encima.
- 12 paredes de pozo (QuarryCliff_02/05), 6 cascadas del pack tharlevfx,
  3 terrazas circulares al fondo (esc 26/34/20), 34 coniferas, spot de fondo
  calido y 2-3 PointLights de relleno.

### ESTADO: mal, hay que retocar

Ultimo cambio **empeoro**: baje las paredes de escala 5-9 a 2.6-4.2 y las acerque
a |x|=2400, y ahora **hay rocas atravesando el encuadre** de lado a lado, tapando
la vista. Antes el problema era el opuesto: a escala 5-9 y |x|=1750 eran muros de
128 m que dejaban TODO el pozo en sombra total (el suelo existia pero salia negro).

**Lo que hay que hacer:** las paredes del pozo deben quedar ALTAS pero **abiertas
por arriba y por el fondo** — enmarcar sin cerrar. Probar |x| ~3000-3500, escala
5-7, y **verificar con captura que no cruzan el eje central** (y que dejan ver las
terrazas del fondo). El error de las dos veces fue no medir el AABB resultante
contra el corredor de vision antes de dar por bueno.

Camara de referencia usada: world `(-74000, 6200, 250)` yaw 90, pitch -2.
(LI_09 esta en -74000, 8000 => local (0, -1800)).

### Siguientes en la cola, sin empezar

- **08 Anfiteatro**: REGRESION. Manto de geometria verde/amarilla deforme cubriendo
  el primer plano. No estaba al construirlo. Hay que identificar que actor es
  (probar `find_actors` con bounds sobre la zona baja del encuadre).
- **03 Mirador de Sariel**: graybox (caja blanca + 2 columnas). Beat: el ramal
  opcional que entrega la Llave. Construir de cero.
- **05 Ruinas del Gazebo**: casi graybox (plataforma blanca + columnas). Beat:
  "Cenizas y Verdad", lore + Corruptio en ramal elevado. Construir de cero.

### Anfiteatro: el "manto verde" RESUELTO (2026-08-12)

Era **`SM_Suelo_Base`**, el propio plano de suelo del Anfiteatro: 200 m de lado con
`M_DA_MK_Valle_Hierba`, cuyo material tiene **TextureCoordinate tiling 420** (se
hizo para un Landscape de 1 km). A ras de horizonte ese tileado produce un muare
verde/amarillo estirado que parece geometria rota.

**Arreglo:** material `M_DA_MK_Tierra_Arena` (tiling 26, y ademas es lo que pide el
beat 08: patio de piedra y tierra, no pradera) y plano reducido de escala 200 a 85.

**Leccion:** un tiling alto pensado para landscape genera muare en planos grandes
vistos en rasante. Al reutilizar `M_DA_MK_Valle_Hierba` fuera de un Landscape,
bajar el tiling o usar otro material.

**Y una leccion de metodo:** el actor culpable YA aparecia en mi consulta de bounds
(`SM_Suelo_Base | dim 20000 | Z -6..-6`) y lo pase por alto cuatro veces porque
buscaba "algo roto" en vez de sospechar del suelo. Antes de descartar, revisar
tambien lo que parece normal. Lo identifico Angel pinchandolo en el viewport en
30 segundos, igual que con los barandales del Puente.

### Mirador de Sariel — construido (2026-08-12)

De graybox (caja blanca + 2 columnas) a zona vestida. Referencia beat 03:
promontorio rocoso con senda, Sariel al borde ofreciendo la llave, cofre al lado,
lago turquesa abajo y montanas con MUCHAS cascadas al fondo.

Puesto: suelo, lago (plano 420x300 con `M_DA_MK_Agua_Quieta`), 50 rocas de
montana/ribera, 14 cascadas del pack, 48 coniferas, 260 matas (KikuyuGrass +
trebol + anemonas + helechos), cofre junto a Sariel, y **material de piedra a la
terraza**, que era una caja blanca (`SM_DA_GroundPlane` sin override).

**PENDIENTE:** el lago NO se ve todavia desde la terraza; hay roca de por medio
mas alla del corredor que despeje (aparte 27 rocas de la caja x[-4500,4500],
y[1600,15000], pero el lago esta en y=16000 y sigue tapado). Sariel es el
placeholder plano de siempre.

### ERROR REPETIDO 3 VECES EN LA MISMA SESION

Escalar roca sin medir su alcance: paso en el **Elevador** (paredes de 128 m que
cegaron la zona), en **Yesod** (montanas de 413 m invadiendo el Anfiteatro) y en el
**Mirador** (rocas de promontorio a escala 4 = 55 m que se tragaron la terraza y
dejaron la camara dentro de la piedra).

**REGLA:** despues de colocar cualquier roca escalada, LEER su AABB
(`get_actor_bounds`) y comprobarlo contra una caja jugable definida; empujar en
bucle hasta que no invada. Funciona — asi se arreglaron las paredes del Elevador
(12/12 fuera) y las rocas del Mirador (14/14 fuera). Hacerlo SIEMPRE en el mismo
paso que la colocacion, no como correccion posterior.

### Mirador: vista al lago RESUELTA (2026-08-12)

Dos causas encadenadas, ambas mias:

1. **39 rocas y arboles cortaban la linea de vision.** Resuelto calculando la recta
   ojo(0,1150,500) -> lago y comprobando el AABB de cada actor contra ella
   (`b.max.z > alturaVista(y)` dentro de un cono de +-5000 en X). 36 de 39
   despejados empujando en bucle; 3 quedan y no molestan.
2. **El lago estaba a z=-900, ENTERRADO bajo el landscape del Jardin**, que se
   extiende hasta el Mirador (X -90400..10400, Y -110400..-9600). Invisible.
   Subido a z=-30.
3. Al subirlo **inundo la pradera** (empezaba en y=1500). Retirado a y 8000..22000,
   pasado el promontorio. Las 28 cascadas subidas +875 para morir en el agua.

**OJO GENERAL:** varias zonas caen dentro del landscape de otra (el del Jardin y el
del Claro son de 1009 m cada uno y se solapan con las vecinas). Antes de poner agua
o suelo en una zona, comprobar a que cota esta el landscape que la cubre.

### Ruinas del Gazebo — construido (2026-08-12)

La rotonda ya existia (`SM_MRK_Rotunda_Ruin_800`, tableta `InscribedSlab`,
pedestal, columnas caidas, escombro, domo caido). Faltaba todo lo demas.

Anadido: material de piedra a plataforma y muros (eran planos blancos, mismo caso
que el Mirador), suelo del promontorio, **110 piezas de hiedra sobre la rotonda**
(es lo que la define en la lamina), 240 matas de KikuyuGrass/trebol/anemona/helecho,
52 rocas de valle, **16 cascadas**, 44 coniferas, y el fragmento de Corruptio con
`M_DA_MK_Shadow_Purple` + luz violeta.

**La colocacion medida FUNCIONO a la primera:** cada roca se coloco y se comprobo
su AABB contra la caja jugable en el mismo paso, empujandola en bucle si invadia.
7 reubicadas automaticamente, verificacion final **0 invadiendo**. Es la primera
zona de la sesion donde no hubo que corregir a posteriori. Hacerlo asi SIEMPRE.

**Pendiente:** la zona queda oscura (la roca tapa el sol del Master, patron que se
repite en Claro, Yesod, Elevador y Gazebo). Se metieron 5 rellenos y aun asi el
cielo sale negro en las capturas. Merece un criterio comun de iluminacion de zona
en vez de parchear una a una.

## Elevador del Trono — el pozo, de verdad (2026-08-13)

### Lo que decian las notas NO era el problema

La sesion anterior cerro culpando a `Elevador_Pared_*` ("rocas atravesando el
encuadre"). **Falso.** Medido con un abanico de rayos (`trace_world` desde la camara
de referencia, 7 yaws x 4 pitches): ninguna pared aparecia en ningun rayo. Sus bordes
interiores estan a 16-24 m del eje.

Los que sellaban el encuadre eran **`Elevador_Roca_0/1/2`**, tres QuarryCliff de 41 m
de ancho atravesados en el paso entre la plataforma y las terrazas. `Roca_1` era un
dique completo de lado a lado. Nada mas alla de 57 m era visible desde ningun punto
del cuadro.

**Metodo que lo encontro** (reutilizable): definir un corredor de vision como caja
(x +-1100 del eje, y 9500..21000, z -300..2600), recorrer todos los actores, y
empujar en bucle en X los que la invaden hasta que salgan. 11 movidos, 0 invadiendo
al verificar. **Excluir las luces**: tienen bounds pero no ocluyen, y estaban en el
eje a proposito.

### El anillo de columnas tapaba el eje

Habia una columna en el eje norte (`Columna_2`) y otra en el sur (`Columna_6`).
Girado el anillo 22.5° (8 columnas, r=550, angulos 22.5+45k) — el mismo truco que los
8 cubos de la arena del paso 7. Eje norte y sur libres.

### CAUSA RAIZ REAL: el suelo de la zona estaba enterrado

| Que | Cota |
|---|---|
| `Elevador_Suelo` | -260 |
| Las 3 `Elevador_Terraza_*` | -380 a -280 |
| `SM_Plano_Referencia` (plano global del Master, 2400 x 1800 m) | **-50** |
| `Yesod_Suelo` (de LI_13, 420 m, llegaba a x=-71000) | **-60** |

Todo el diseno de suelo del beat 09 estaba **por debajo de dos planos ajenos**. Desde
la plataforma los rayos al norte salian a CIELO: las "plazas circulares aterrazadas"
no existian en pantalla. Lo que se veia era la cinta del sendero
`Conn_AnfiteatroElevador` y negro a los lados.

Es la misma trampa del lago del Mirador, pero con el plano global del Master.

### Solucion aplicada (opcion B: agujerear el plano global)

1. **`SM_Plano_Referencia` recortado en 4 tiras** dejando el hueco del pozo en
   x [-78500, -69500], y [9600, 18000]. Se reutilizo el actor original como tira
   Sur y se crearon `SM_Plano_Ref_Norte/Oeste/Este` (mismo mesh
   `/Game/DarkAngels/Environment/SM_DA_GroundPlane`, sin material override, carpeta
   `_Plano`). El hueco empieza en y=9600, o sea **al norte de la plataforma**: la
   aproximacion sur sigue siendo suelo solido.
2. **`Yesod_Suelo` encogido** de escala X 420 a 340 (borde este de -71000 a -79000).
   Ademas `Yesod_Monte_24/25/26` y `Yesod_Fondo_34` estaban metidos DENTRO del pozo;
   empujados al oeste (24 se movio 56 m). Comprobado antes que el contenido real de
   Yesod no llega al este de -78700, asi que no se queda sin piso.
3. **Pozo excavado**: `Elevador_Suelo` a **z=-3000** (30 m de profundidad).
4. **Terrazas reescalonadas dentro del hueco**, descendiendo hacia el norte:
   `Terraza_0` y=11800 cota -1300 · `Terraza_1` y=14400 cota -2100 ·
   `Terraza_2` y=16900 cota -2700. (Estaba a y=19500, fuera del hueco.)
5. **Las 12 paredes bajadas** para que su base llegue a z=-3200 y forren el pozo en
   vez de flotar 20 m sobre el fondo. Bajadas entre 2018 y 2264. Sus cimas quedan
   ahora en 4057..6617.
6. Todo lo apoyado en el viejo suelo y dentro del hueco (34 abetos, rocas, cascadas
   interiores) bajado con el, delta -2740.
7. **Cascadas asentadas**: las de dentro del pozo (2, 4, 5) caen al fondo (arco base
   -3100, base de espuma -3000); las del borde de aproximacion (0, 1, 3) apoyan en
   el plano global (arco -100, base -50). Antes las bases estaban atravesadas en el
   aire, de -3302 a -1702.
8. **Rellenos reubicados dentro del pozo**, uno sobre cada terraza:
   `Elev_Fill_2` (-74000, 11800, -700) · `Elev_Fill_3` (14400, -1500) ·
   `Elev_Fill_4` (16900, -2100) · `Elevador_Relleno_2` (13000, -2500, fondo).

### Verificacion por trazas

Perfil sur-norte en x=-75000: borde -50 → suelo -3000 → Terraza_0 -1300 → suelo
-3000 → Terraza_1 -2100 → suelo -3000 → borde -50. Corte este-oeste en y=14000:
`Pared_8` a 5761, fondo -3000, `Terraza_1` -2100, fondo -3000, `Pared_7/11` a
3403/5113. **El pozo es un pozo.**

La pasarela `Conn_AnfiteatroElevador` (17 tramos, z=-24, x -74196..-73804, de y=4800
a 40500) cruza el pozo entera y ahora funciona como **puente sobre el vacio**. Es del
Master, no del LI.

### ERROR COMETIDO: filtrar actores por nombre parcial

El filtro `find_actors(name='Elev')` capturo tambien `Conn_AnfiteatroElevador_11..14`
—que son del Master, no del Elevador— y les aplico el delta de -2740, rompiendo la
pasarela. Restaurados con +2740. **Regla: al filtrar por nombre para una operacion
masiva, comprobar la lista de afectados antes de escribir, no despues.**

### ERROR COMETIDO: unidades de intensidad de luz

Puse `intensity` 7-9 en los PointLight creyendo que era la escala 1-10 de las notas
del Claro. **Estaban en candelas: los valores originales eran 3000-9000.** Las deje
practicamente apagadas y hubo que restaurarlas (3000-4500). Leer siempre el valor
actual antes de escribir uno nuevo.

### PENDIENTE MANUAL DE ANGEL — bloqueante

**`Ctrl+Shift+S` (Save All).** Las 4 tiras del plano global viven en el nivel
persistente del Master, y **no hay tool MCP para guardar un nivel**:
`SceneTools.save_actor` responde *"is not an external actor asset and cannot be saved
individually. Save the level instead"* (el Master no es World Partition), y en
`AssetTools` no existe ningun `save*`. Los cambios del `_Sub` si estan guardados
(`commit_level_instance` los persiste); **los del Master no**. Sin ese guardado, al
reabrir vuelve el plano entero y el pozo desaparece.

### Lo que queda en el Elevador

- **Sobreexposicion.** Todo lee blanco lavado. Con el pozo oscuro en cuadro la
  auto-exposicion del Master (0.06-6.0) se abre y revienta columnas, cascadas y
  `Elevador_Gabriel`, que sale como una cruz blanca. Es el defecto transversal que
  ya estaba fichado en las otras zonas, no algo propio del Elevador.
- **Las cascadas leen como cartas blancas planas** (`SM_Waterfall_Arc` / `_Base` del
  pack tharlevfx, sin material override). Mismo sintoma que los planos de agua del
  Puente.
- **Las paredes siguen altas**: cimas en 4057..6617 sobre un pozo de 90 m de ancho.
  Con el sol del Master a pitch -38 desde +X, para que el sol entre al fondo la cima
  del muro este tendria que estar por debajo de z≈1900. Hoy no entra.
- `Elevador_Roca_1` acabo solapada dentro de `Elevador_Roca_0` al sacarla del
  corredor: es geometria redundante, se puede borrar o reutilizar.
- Las columnas leen enormes para ser un anillo de pedestal (escala 1.2/1.2/3).

### Cimas de los muros — pase de luz (2026-08-14)

Sol del Master leido del actor, no de las notas: **pitch -38, yaw 150**. Direccion HACIA
el sol = `(0.6824, -0.3940, 0.6157)`, o sea viene de +X con algo de -Y. Los que hacen
sombra al pozo son por tanto los **muros impares (lado +X)**; los pares reciben la luz
de cara y son el telon iluminado.

Metodo: `trace_world` desde cada punto de interes en direccion al sol; si no impacta
nada, hay sol directo. Primero se bajaron los ocluyentes en bucle hasta que entrara luz
(paso proporcional, **se paso de largo**), y luego se **subieron de nuevo en pasos de
400 aceptando solo las subidas que no rompieran la luz ya ganada**. Ese segundo pase es
el que hay que conservar: maximiza altura sujeto a la restriccion de luz.

Cimas finales (z del techo del AABB):

| Actor | Cima final | Original |
|---|---|---|
| `Elevador_Pared_1` | 5837 | 5593 |
| `Elevador_Pared_3` | 4397 | 4327 |
| `Elevador_Pared_5` | 3632 | 4353 |
| `Elevador_Pared_7` | 3700 | 4698 |
| `Elevador_Pared_9` | **2325** | 6489 |
| `Elevador_Pared_11` | **1538** | 5532 |
| `Elevador_Roca_4` | 2900 | 2867 |
| `Elevador_Roca_1` | **-3150** (hundida) | 777 |

Resultado: **Terraza_2 con sol directo**; Terraza_1, Terraza_0, plataforma y fondo en
sombra. Es primer plano oscuro / fondo luminoso, que es lo que pide el beat.

**LIMITE GEOMETRICO, no es un fallo:** con el sol a 38 de elevacion, iluminar el FONDO
de un pozo de 30 m exige un corredor despejado de 30/tan(38) = 38 m por el lado del sol.
No se puede tener a la vez muro este alto y fondo de pozo soleado. Hay que elegir.

### INCIDENTE: el `_Sub` del Elevador no se deja guardar

Sintoma: `commit_level_instance` **devuelve exito mientras el guardado del paquete falla
por debajo**. No fiarse de su valor de retorno; verificar contra el `LastWriteTime` del
`.umap` en disco y contra `Saved/Logs/DynamicCombatSystem.log`.

En el log:

```
LogFileManager: Warning: MoveFile was unable to move '...L_DA_Malkuth_Elevador_Sub.umap'
   to 'Saved/L_DA_Malkuth_Elevador_Sub<hash>.tmp' (Error Code 32), retrying in .5s...   x10
LogSavePackage: Error: Error saving '...L_DA_Malkuth_Elevador_Sub.umap'
Message dialog closed, result: Ok, title: Message, text: The asset ... failed to save.
```

**Error 32 = fichero en uso por otro proceso.** Cada fallo abre un **dialogo modal** que
bloquea el hilo de juego y con el **todo el servidor MCP** (las llamadas dan timeout
durante minutos). El editor sigue vivo y `Responding=True`: no esta colgado, esta
esperando un clic.

Diagnostico hecho:

- Los **12 `_Sub` estan bloqueados** para apertura exclusiva desde fuera — es normal,
  Unreal mantiene abierto el linker de cada sub-mapa cargado como Level Instance. Ese
  test **no** sirve para predecir si un guardado va a fallar.
- Solo `Elevador_Sub` falla (4 `Error saving` en todo el log; ni Yesod ni el Master
  fallaron nunca). O sea que hay un **handle extra** sobre ese paquete concreto,
  probablemente filtrado por los cinco ciclos `edit_level_instance` /
  `commit_level_instance` seguidos sobre LI_09.
- Un ciclo **StartPIE + StopPIE** (para forzar recoleccion de basura) **no lo suelta**.
- Al pulsar `Cancel` en el dialogo, la sesion de edicion **se descarta**: se perdio el
  pase de cimas y hubo que rehacerlo. Los pases anteriores (pozo, luces, cascadas)
  seguian en memoria.
- `commit_level_instance` sobre un LI en el que no se ha tocado nada **no intenta
  guardar** (lo da por limpio). Para forzar un intento hay que ensuciar el paquete.

**Leccion operativa:** no encadenar muchos ciclos de edicion de un mismo Level Instance
en una sesion. Y despues de cada `commit_level_instance` que importe, comprobar el
`LastWriteTime` del `.umap`.

**Salida:** reiniciar el editor. Al arrancar de cero no hay handle filtrado. Lo que hay
en disco del Elevador es el estado hasta el pase de luces; hay que **rehacer dos pases**,
y los dos estan documentados con valores exactos:

1. **Cascadas** — grupo del pozo `{2_a,2_b,4_a,4_b,5_a,5_b}`: arco con base a **-3100**,
   base de espuma a **-3000**. Grupo del borde `{0_a,0_b,1_a,1_b,3_a,3_b}`: arco a
   **-100**, base a **-50**.
2. **Cimas de los muros** — la tabla de arriba.

### RESUELTO tras reiniciar el editor (2026-08-14 04:32)

Con el editor recien arrancado el handle filtrado desaparece y **el guardado funciona a la
primera**: `L_DA_Malkuth_Elevador_Sub.umap` escrito a las 04:32:20, y **cero
`LogSavePackage: Error`** en el log de la sesion nueva.

Al recargar de disco resulto que **las cascadas SI se habian guardado** en el save bueno de
las 20:36; lo unico que faltaba era el pase de cimas, que se reaplico con la tabla de
arriba y se verifico igual (Terraza_2 con sol, Terraza_1 en sombra).

Estado final verificado por trazas: perfil sur->norte por x=-75000 da
`-50 / -3000 / -1300 / -3000 / -2100 / -3000 / -3000 / -50`, y el eje norte desde la
plataforma sale **libre**.

**Efecto secundario grande y bueno:** bajar los muros del lado del sol **arreglo la
sobreexposicion**. Antes todo salia blanco lavado porque la auto-exposicion se abria ante
un pozo completamente oscuro; con luz entrando, la exposicion se asienta y ahora se ve
**cielo azul con nubes, roca con color y las columnas en marmol crema**. La zona pasa de
ilegible a legible sin tocar el PostProcess. Vale la pena probar el mismo truco en las
otras zonas oscuras (Claro, Yesod, Gazebo) antes de andar retocando la exposicion global.

Lo que sigue pendiente en el Elevador, por orden de fealdad:

1. Los flancos del pozo siguen muy oscuros.
2. Las columnas leen enormes para ser un anillo de pedestal.

### Gabriel reubicado al fondo (2026-08-14)

`Elevador_Gabriel` estaba en **y=9400: a cinco metros del borde norte de la plataforma**.
Una silueta de 41 m de ancho por 22 m de alto a esa distancia solo podia leer como una
pared blanca recortada por el encuadre — que era justo la queja.

Movido a **y=19400, de pie sobre el borde norte** (base z=-50, cima z=2134), a **105 m de
la plataforma**, que es donde ya apuntaba el `Elevador_Luz_Fondo`. Ahora **lee como una
figura alada** al final del pasillo, enmarcada por la columnata y con la pasarela llevando
hasta ella. Linea de vision comprobada: despejada hasta el.

Guardado verificado en disco: 06:38:08, cero `LogSavePackage: Error`.

**Nota sobre la malla:** `SM_SM_DA_AngelSilueta` (ojo al `SM_` duplicado del nombre) la
comparten **seis actores**: `C1_Silueta`, `Mirador_Estatua_Sariel`, `Puente_Angel_Gigante`
(escala 45), `GC3_Gabriel`, `Yesod_Gabriel` y este. Su material `M_DA_AngelLuz` es
**Unlit + Opaque**: emite plano, sin sombreado ni volumen, y por eso todas las siluetas del
juego leen como cruces blancas. Cambiar ese material arregla las seis de golpe — pero ojo,
en el Puente el angel SI quiere ser luminoso, asi que conviene override por actor y no
tocar el material compartido. En el Claro ya funciono `M_MRK_Stone_Ivory` para las estatuas.

### La sobreexposicion que queda es de la PLATAFORMA, no del pozo

Descubierto al capturar a la altura de los ojos desde la plataforma: el encuadre sale
lavado a blanco. **Se repitio identico en dos capturas seguidas, asi que no es un
artefacto de streaming.**

Causa: a esa altura el cuadro lo llenan las **columnas de marmol blanco y la losa de la
plataforma**. La auto-exposicion del Master se calibra con eso y lo sube todo al tope.
Desde una camara alta se ve bien porque entran cielo y roca oscura que compensan.

O sea que quedan **dos focos de sobreexposicion distintos** y no hay que confundirlos:
el del pozo oscuro (resuelto bajando las cimas) y este, que es de la plataforma.

### RESUELTO — y NO era el albedo (2026-08-14 07:53)

Se midio antes de tocar, y menos mal. El albedo de `M_DA_MK_Piedra_Marfil` **ya era
correcto**: su `Constant3Vector_0` (que multiplica la textura de BaseColor) vale
**(0.58, 0.555, 0.50)**, un valor de piedra fisicamente sensato. Bajarlo habria sido
apagar la zona sin arreglar nada.

**La causa real: cuatro focos a quemarropa dentro del anillo de columnas** (radio 5,5 m),
sumando ~16.900 candelas:

| Luz | Antes | Ahora | Posicion |
|---|---|---|---|
| `Elev_Fill_1` | 4200 | **900** | en el centro exacto del anillo, a 10 m de alto |
| `Elevador_Cenital` | 9000 | **3000** | spot cenital a 600 del eje (se conserva, es el haz) |
| `Elevador_Relleno` | 3200 | **700** | a 200 del eje |
| `Elev_Fill_6` / `_7` | 2000 c/u | **1200** | flancos, a 1746 |
| `Elevador_Luz_Disco` | 500 | 500 (sin tocar) | pozo de luz del disco |

Resultado: las columnas pasan de blanco plano a **marmol crema con volumen y sombreado**,
y la losa lee con su despiece. Guardado verificado: 07:53:31, cero errores.

**LECCION:** cuando algo sale blanco lavado, medir **`intensity` y distancia de los focos
locales** antes de tocar albedo o exposicion. Paso igual con la columna caida del Claro y
con `Claro_Vigilante_1_Glow`.

**PERO OJO, no generalizar de mas** (comprobado el 2026-08-14 barriendo el mundo entero):
en todo Malkuth solo hay **tres luces por encima de 5000 cd** — `Elevador_Luz_Fondo`
(26000), `Elev_Fill_5` (9000) y `Claro_Haz_Puerta` (5200). Es decir que **Santuario,
Gabriel C2 y Yesod NO tienen focos fuertes**, asi que su sobreexposicion **no** es esta
causa. Son los tres espacios cerrados y oscuros: ahi el mecanismo es el otro, el de la
auto-exposicion abriendose ante un entorno oscuro y reventando lo poco que brilla. En el
Elevador se arreglo dejando entrar el sol; en un interior eso no se puede, hay que
**subir el suelo de luz ambiente** o acotar la exposicion minima del PostProcess.

Son **dos causas distintas con el mismo sintoma**. Diagnosticar cual antes de actuar.

### Gabriel estaba en una trampa de luz (2026-08-14 08:09)

Al moverlo a y=19400 quedo entre las **dos luces mas potentes del juego**: `Elev_Fill_5`
(9000 cd) a y=19500, practicamente encima, y `Elevador_Luz_Fondo` (26000 cd) apuntandole
desde y=17000. Bajadas a **1500** y **7000**. Guardado 08:09:43, cero errores.

Leccion: al reubicar un actor, comprobar que luces caen cerca de su nueva posicion.

## 01 Jardin: el coloso SI se ve — el punto estaba obsoleto (2026-08-14)

La lista de pendientes decia "el coloso no se ve desde el spawn". **Ya no es cierto**,
probablemente desde el arreglo de la niebla.

`SM_Coloso_Landmark` mide 186 x 150 m y **187 m de alto**; desde `PS_Master_Jardin` esta a
**267 m**, a yaw 3 (o sea casi justo al frente) y 17.8 de elevacion. Capturado desde el
spawn: **domina el encuadre por completo**, con cielo azul, pradera verde con flores y la
senda de tierra curvandose hacia el.

**OJO con el metodo:** una primera traza al *centro del AABB* del coloso devolvio
"bloqueada a 213m" y casi lo doy por tapado. Era **el propio coloso**: su AABB empieza a
182 m, asi que el impacto estaba dentro de el. Es la misma trampa que ya paso al asentar
los angeles del Claro. **Al comprobar visibilidad hay que identificar QUE actor devuelve la
traza, no solo si hay impacto.**

Lo que le queda de verdad al Jardin, visto en la captura:

1. **Los rotulos de `Plan/Rotulos` se cuelan en pleno cielo** ("02 SENDERO DE SET / Primeras
   Reglas" justo sobre el coloso). Es lo que mas rompe el plano ahora mismo. Estan en la
   carpeta `Plan/` del Master y se pueden ocultar o borrar.
2. El coloso es una **esfinge**, no un angel: no corresponde al beat 01 del PDF. Deuda de arte.
3. Algunos artefactos cian sueltos a la derecha del encuadre, sin identificar.
4. La senda ya lee como vereda de tierra clara, no como cinta de losas. Ese punto tambien
   estaba obsoleto; solo le queda el borde algo duro.

### Rotulos del plan ocultados (2026-08-14)

Los **11 `Rotulo_*`** de la carpeta `Plan/Rotulos` del Master estan ocultos. **No se han
borrado**: siguen ahi para orientarse, basta con revertir las dos propiedades.

Como se hizo, porque tiene truco:

- `bHiddenEd` **no se puede escribir** por MCP (`the following properties could not be set`).
- `visible` **no existe** como nombre de propiedad; la buena es **`bVisible`**, y va en el
  **componente**, no en el actor.
- Receta que funciona: `bHidden = true` en el actor (lo oculta en juego/PIE) **y**
  `bVisible = false` en cada componente (lo oculta tambien en el viewport del editor).

Verificado leyendo las propiedades de los 11: `bHidden=true`, `bVisible=false`.
**Viven en el nivel persistente del Master, asi que hace falta `Ctrl+Shift+S` a mano.**

La carpeta `Plan/Hitos` (los obeliscos por estacion) **no se ha tocado**.

### El aviso de `L_DA_Malkuth_Master_BuiltData` es INOFENSIVO

Al guardar el Master sale:

```
The Asset L_DA_Malkuth_Master_BuiltData being saved does not have any of the provided
object flags (0x10000002); saving the package would cause data loss.
Run with -dpcvars=save.FixupStandaloneFlags=1 to add the RF_Standalone flag.
```

**El `.umap` SI se guarda**; lo unico que no se escribe es el `_BuiltData`, que es el
horneado de iluminacion. Comprobado por fechas en disco, y el aviso ya salia en guardados
anteriores del dia, asi que no lo provoca ningun cambio concreto.

**Y no importa, porque el Master no usa horneado:** su `DirectionalLight` y su `SkyLight`
son las dos **Movable**, o sea iluminacion completamente dinamica. El `_BuiltData` es un
asset vestigial sin contenido util aqui.

**OJO, esto corrige una nota vieja:** lo de *"este proyecto depende del horneado, no se
pueden pasar las luces a Movable"* es de la arena `L_DA_SeraphArena_POC`, con luces
Stationary. **No aplica al Master de Malkuth.**

Opciones, de menos a mas invasiva: ignorar el aviso (recomendado); arrancar una vez con
`-dpcvars=save.FixupStandaloneFlags=1` para que repare el flag; o borrar el `_BuiltData`,
que no aporta nada. Decision: **ignorarlo**.

## Revision 07 Puente y 08 Anfiteatro (2026-08-14)

Camaras: Puente en (16000, 53000, 500) yaw 90 — el eje del puente es **x=16000** y el
angel del fondo esta en (16000, 76000, 6716). Anfiteatro desde su PlayerStart real,
(-73649, 41996) yaw 180.

### 07 Puente — dos de tres puntos, resueltos

- **"Todo blanco puro sin definicion de material" → RESUELTO.** La calzada lee como arenisca
  calida con despiece, el canon como roca marron con detalle y el cielo es azul con nubes.
- **"Agua sin definicion" → RESUELTO.** Las cascadas de la izquierda leen como agua cayendo.
  Probablemente merito del `BP_SolAgua_Global` de hoy.
- **"El angel gigante lee como una cruz blanca" → SIGUE.** Es el mismo `M_DA_AngelLuz` Unlit.
- **NUEVO:** hay un rotulo rojo **"Text"** sin configurar flotando sobre la calzada, a media
  altura del puente. Es un TextRender suelto, no de `Plan/Rotulos` (esos ya estan ocultos).

### 08 Anfiteatro — la bruma resuelta, pero aparece una costura

- **"El graderio se perdia en la bruma" → RESUELTO.** Cielo azul limpio, sin halo. El
  empedrado del primer plano lee muy bien, con musgo y hierbajos entre las losas.
- **NUEVO Y FEO:** en el horizonte hay una **banda negra horizontal** y, mas alla, un
  **plano crema plano hasta el infinito**. Es una costura de suelos: el suelo de la zona
  acaba y deja un hueco negro contra otro plano (probablemente `SM_Plano_Referencia` a
  z=-50 visto a ras). Ocupa todo el ancho del encuadre.
- La camara a yaw 180 desde el PlayerStart **no mira al graderio**: solo asoma un escalonado
  por el borde izquierdo. Para evaluarlo de verdad hay que girar; queda pendiente.

### 04 El Claro — visto por fin (2026-08-14)

Camara **(44000, -13650, 320) yaw 90** (LI_04 en 36000,-12000 + el PS local 8000,-1650).
Anotarla: es la unica forma de evaluarlo, la zona **no tiene PlayerStart propio**.

Lo bueno: **el anillo de acantilados es lo mejor de roca que hay en el proyecto** — quarry
cliff calido, alto, con detalle, encerrando de verdad. Y la puerta del fondo se lee: porton
de madera, escalinata y las dos columnas de marfil flanqueando.

Lo malo, por gravedad:

1. **El cielo sale NEGRO.** Toda la franja superior en negro puro con unos abetos
   recortados. Es el caso extremo del patron "zona encerrada por acantilados".
2. **Una masa marron gigante invade el encuadre desde arriba a la derecha**, colgando boca
   abajo sobre la arena. Algun actor (roca o montana de otra zona) metido en el espacio
   aereo. Es lo que mas rompe el plano; hay que identificarlo por bounds sobre la caja de
   la arena.
3. **Los 4 angeles leen como farolas blancas en forma de T**, no como figuras. Son los
   `SM_DA_AngelV2` emisivos.
4. **El suelo es un plano palido casi liso**, con el tileado a la vista y muy brillante en
   comparacion con todo lo demas. No lee como patio de tierra.

Nota de iluminacion: suelo brillante + cielo negro es la relacion **invertida**. Aqui la
luz la estan poniendo los rellenos locales y no entra nada de cielo.

#### La masa intrusa: NO identificada todavia (intento fallido)

Se sospecho de **`Gazebo_Monte_25`** (138 m de ancho, 222 m de alto, borde sur a y=-4676,
o sea a 90 m de la camara). Encajaba bien. **Se movio +8676 en Y** (a y 4000..28254) y
**la masa del encuadre no cambio nada**. No era.

`Gazebo_Monte_25` se quedo movido; el cambio esta guardado en `L_DA_Malkuth_Gazebo_Sub`
(09:56:07). Es benigno —alejaba una montana del borde norte del Claro— pero **conviene
revisar que no estorbe ahora en el Gazebo**. Para revertirlo: **dy = -8676**.

**Por que fallo la deteccion por trazas:** se lanzo un abanico de rayos hacia arriba desde
la camara (centro, 20/30/45 a la derecha, cenit) y **casi todos salen a cielo**; solo el de
45 golpea `Claro_Cliff_Out_5`. O sea que **la masa no tiene colision**, y por eso
`trace_world` no la ve. Toda la deteccion por trazas es inutil para este actor.

**La masa es `Gazebo_Monte_24`** (identificada por Angel pinchandola en el viewport).
Bounds originales: x 67059..87956, y 14724..35061, **z hasta 15971 (160 m de alto)**.

**Estado actual: NO resuelto, y con dos correcciones de por medio.**

- `Gazebo_Monte_25` **restaurada a su sitio original** (y -4676..19578). No era la culpable.
- `Gazebo_Monte_24`: se probo **+9000 en X** y **no basto** (la captura de verificacion
  salia practicamente igual), asi que **se revirtio**. Guardado 10:18:40, cero errores.

**Las dos montanas estan EXACTAMENTE en su posicion original**, verificado comparando
bounds contra los valores previos: `Monte_24` en x 67059..87956 / y 14724..35061, y
`Monte_25` en x 36061..49881 / y -4676..19578. **De todo este intento no queda ningun
cambio en disco.**

**Por que no basta y que haria falta:** con la camara en x=44000, el borde oeste de la
montana queda a ~320 m y su cima a z=15971, o sea **26 de elevacion**; moverla 90 m mas
solo la baja a 21. Sigue dentro del encuadre. Para que desaparezca detras del borde norte
del Claro (los acantilados rematan a z~3900) habria que **bajarla mucho o alejarla
cientos de metros**, y eso ya no es un empujon: es decidir el telon de fondo del Gazebo.

## ~~PROXIMA SESION~~ — LAS TRES HECHAS (cerrado 2026-08-14 12:35)

> **Las tres tareas de abajo estan resueltas**, pero **con el culpable cambiado en dos de
> ellas**. Ver las secciones nuevas al final del documento. Resumen de en que se equivocaba
> este bloque:
>
> - **(1)** La masa que invadia El Claro **no era `Gazebo_Monte_24`**, era `Monte_Medio_64`
>   del **Jardin**. Por eso empujar el Monte_24 nunca cambiaba nada.
> - **(2)** La costura del Anfiteatro si era lo que se sospechaba (hueco contra el plano de
>   referencia), y ademas se midio exacta: `SM_Suelo_Base` a z=-6 contra
>   `SM_Plano_Ref_Norte` a z=-50.
> - **(3)** El cielo negro de El Claro **no era falta de luz**: eran `Gazebo_Monte_21` y
>   `Gazebo_Monte_25` asomando a 41-46 de elevacion. El 57% del suelo ya recibia sol directo.
> - **La regla de lateralidad de mas abajo esta AL REVES.** A yaw 90 el lado derecho de la
>   pantalla es **-X**, no +X.

Orden acordado con Angel. Los tres estan acotados y con datos medidos:

**1. Telon de fondo del Gazebo (`Gazebo_Monte_24`).** Es la masa que invade El Claro.
Bounds x 67059..87956, y 14724..35061, cima **z=15971**. Desde la camara del Claro
(44000, -13650, 320) yaw 90 queda a ~320 m y **26 de elevacion**, y el borde norte del
Claro solo remata a z~3900. Empujarla no sirve (probado, +9000 en X no cambia nada).
Las vias reales son **bajarla** (que su cima quede bajo ~3900 vista desde alli) o
**reducir su escala**. Verificar siempre con captura desde esa camara exacta, y comprobar
que no se rompe el fondo del propio Gazebo, que es para lo que existe.

**2. Anfiteatro: la costura del horizonte.** Banda negra horizontal cruzando todo el
encuadre con un plano crema liso detras. Camara: su PlayerStart (-73649, 41996) — **ojo,
a yaw 180 NO mira al graderio**, hay que girar. Sospechoso: el suelo de la zona acaba y
deja hueco contra `SM_Plano_Referencia` (z=-50). Metodo: trazas verticales a ambos lados
de la costura para ver que actor devuelve cada una.

**3. Cielo negro de El Claro.** Camara (44000, -13650, 320) yaw 90. Suelo brillante +
cielo negro = relacion invertida; la luz la ponen los rellenos locales y no entra cielo.
**Probar el mismo truco que funciono en el Elevador**: bajar las cimas de los acantilados
del lado del sol (pitch -38, yaw 150; el sol viene de +X con algo de -Y) midiendo con
`trace_world` hacia el sol, y despues subirlas de nuevo en pasos aceptando solo lo que no
rompa la luz ganada. Ahi tambien se arreglo la sobreexposicion de rebote.

**TRAMPA QUE ME COSTO DOS ERRORES: la lateralidad de pantalla.** Con la camara a **yaw 90**
(mirando +Y), el lado **DERECHO** del encuadre es **+X**, no -X. En UE, para yaw t:
`forward = (cos t, sin t, 0)` y `right = (sin t, -cos t, 0)`. Lo tuve invertido y por eso
una regla de "apartar" empujo la montana 107 m **hacia** el Claro en vez de alejarla.
Comprobar siempre el signo con un actor de posicion conocida antes de mover nada por
criterio de izquierda/derecha.

**Ojo con las unidades:** estas luces estan en **Candelas** (`intensityUnits: Candelas`),
con valores de miles. La escala 1-10 que aparece en notas viejas del Claro es de otra cosa.

**Pendiente relacionado:** la rugosidad de `M_DA_MK_Piedra_Marfil` es **0.22**, bastante
pulida para piedra; sube el especular en superficies grandes. Si vuelve a haber brillos
molestos, ese es el siguiente dial, pero es un cambio global (lo usan varias zonas).

## El agua del pack tharlevfx necesita su BP_Sunlight (2026-08-14)

**Sintoma:** las cascadas (`SM_Waterfall_Arc` / `SM_Waterfall_Base`) leian como laminas
blancas planas, sin estructura de agua. Mismo sintoma que los planos de agua del Puente.

**No era falta de material.** Las mallas ya traen el suyo asignado en sus slots:

| Malla | Material |
|---|---|
| `SM_Waterfall_Arc` | `MIC_Waterfall_Arc` (padre `M_Waterfall`) |
| `SM_Waterfall_Base` | `M_Waterfall` |

**CAUSA:** los materiales de agua del pack leen un Material Parameter Collection,
`/Game/WaterMaterials/Materials/MPC_Globals`, que tiene **un unico parametro vectorial
`LightVector`** con valor por defecto **`(1, 0, 0, 0)`** — un sol horizontal apuntando a
+X, que no tiene nada que ver con el nuestro (pitch -38, yaw 150). Quien debe escribir ese
parametro es `/Game/WaterMaterials/Blueprints/BP_Sunlight`, y **no habia ninguno colocado
en el mundo**. El agua se estaba iluminando contra un sol inventado.

**Arreglo:** colocado `BP_SolAgua_Global` (una instancia de `BP_Sunlight`) en el
**Master**, carpeta `_Plano`, en (-74000, 12000, 4000) con rotacion **pitch -38 / yaw 150**
igual que el sol, y con su propiedad **`LightSourceActor` apuntando al `DirectionalLight`
del Master**. Sin esa propiedad el blueprint escupe `Accessed None trying to read property
LightSourceActor` al colocarlo (aunque el actor SI se coloca pese al error).

Resultado: las cascadas pasan de lamina lisa a **agua con vetas y estructura de caida**.

**Va en el Master a proposito**: el MPC es global, asi que arregla de una vez el agua de
**todas** las zonas — Puente, Mirador, Jardin. Merece la pena volver a mirar esas tres.

**No se toco ningun asset de terceros.** Se considero poner el `LightVector` a mano en el
`MPC_Globals`, y se descarto por dos razones: es un asset del pack, y su
`vectorParameters` es un array de structs de un solo elemento — escribirlo por MCP puede
perderlo entero.

**Lo que le sigue faltando al agua:** los arcos estan escalados 1.8-3.1 para cubrir 40-50 m
cuando la malla esta pensada para una caida mucho menor, asi que la densidad de textura se
estira y se ven vetas muy alargadas. Si se quiere mejor, la via es varias cascadas mas
pequenas en vez de una gigante escalada.

## La masa que invadia El Claro NO era el Gazebo (2026-08-14, tarea 1)

**Era `Monte_Medio_64`, del anillo de horizonte del JARDIN.** No tiene nada que ver con el
Gazebo. Por eso las sesiones anteriores empujaban `Gazebo_Monte_24` y no cambiaba nada:
ese monte nunca estuvo en el encuadre.

Datos: el actor vive en `L_DA_Malkuth_Jardin_Sub` (`StaticMeshActor_518`), escala 12.09,
bounds x 38097..56084, y -22026..-9282, cima **z=1833**. La camara de El Claro
(44000, -13650, 320) esta **dentro de su AABB en X y en Y**, con la cima a 15 m sobre el
ojo: era un techo colgando sobre la plaza, sin iluminar, o sea la mancha marron oscura de
la esquina superior derecha.

**Arreglo:** bajado 3500 en Z (loc z -6027.96 → -9527.96), cima a **z=-1667**, por debajo
de la cota -50 del plano de referencia, o sea enterrado. Commit del Level Instance
verificado contra disco (`L_DA_Malkuth_Jardin_Sub.umap` reescrito).

**Que le cuesta al Jardin: nada.** Desde `PS_Master_Jardin` estaba a **1156 m** y a solo
**0.9 de elevacion**, y ademas tapado por la cresta marron cercana. Comprobado A/B con dos
capturas desde el spawn del Jardin, oculto y visible: **son identicas**. El anillo del
Jardin tiene 50 montes (`Monte_Medio_*` cerca, `Monte_Lejos_*` lejos) y hay ~14 hermanos a
la misma altura de horizonte.

### LA LATERALIDAD DE LA NOTA ANTERIOR ESTABA AL REVES

La nota de la sesion previa decia `right = (sin t, -cos t, 0)` y que "a yaw 90 el lado
DERECHO del encuadre es +X". **Las dos cosas son falsas.** En UE:

    forward(t) = ( cos t, sin t, 0)
    right(t)   = (-sin t, cos t, 0)

A **yaw 90 el lado derecho de la pantalla es -X**, y +X cae a la IZQUIERDA. Verificado
contra la proyeccion del propio motor y no a ojo: `WorldPosToScreenCoords` devuelve
`x < 0.5` para los montes que estan en +X respecto de la camara.

De paso, los convenios de esas dos herramientas: `WorldPosToScreenCoords` devuelve
**normalizado 0..1 con origen arriba-izquierda** (y crece hacia abajo), y saca valores
fuera de [0,1] para lo que queda fuera de encuadre — util para saber cuanto se sale.

### Metodo que funciono para identificar al culpable

Dejar de razonar por bounds y preguntarle al motor:

1. `SetCameraTransform` a la camara del problema.
2. `ScreenCoordsToWorld` sobre varios puntos de la zona sospechosa del encuadre.
3. `find_actors` con un `bounds` pequeño alrededor de cada impacto → lista de candidatos.
4. Confirmar con A/B: ocultar el candidato y recapturar.

El paso 4 no es opcional. Para ocultar sirve la receta ya conocida (`bHidden` en el actor
+ `bVisible=false` en el componente), pero **exige `edit_level_instance` antes**: sin modo
edicion, tanto `set_properties` como `set_actor_transform` fallan con
"is inside level instance ... which is not in edit mode".

**Ojo al leer las capturas en modo edicion:** Unreal desatura todo lo que no pertenece al
level instance que se esta editando. La imagen sale en gris y **no es un cambio de luz**.

### Herramienta nueva: `scratchpad/ue.mjs`

`CaptureViewport` devuelve el PNG en base64 y una captura de 1208x928 son ~2.6 M de
caracteres: revienta el limite de una respuesta de herramienta. La solucion es hablarle al
MCP por HTTP con Node (ver la nota de MCP por HTTP) y **escribir el PNG a disco**, que
luego se lee como imagen. Tres comandos: `shot`, `call` y `script`.

Usa `node:http`, **no `fetch`**: undici corta a los 5 minutos con
`UND_ERR_HEADERS_TIMEOUT` y hay consultas al editor (barridos de cientos de actores) que
tardan mas.

## La costura del horizonte del Anfiteatro (2026-08-14, tarea 2)

**Que era, con nombres y cotas exactas.** No era un hueco: eran dos suelos a distinta
altura y con distinto material, vistos casi de canto.

| Que se ve en el encuadre | Actor | Cota | Se ve desde |
|---|---|---|---|
| Crema liso | `SM_Suelo_Base` (Anfiteatro) | **z = -6** | hasta 44 m |
| **Banda negra** | `SM_Plano_Ref_Norte` (Master) | **z = -50** | 44 m a 463 m |
| Cielo | — | — | por encima de -0.4 |

`SM_Suelo_Base` es un plano de 85 x 85 m centrado en (-74000, 42000): se acaba a 44 m del
spawn. A partir de ahi asoma el plano de referencia global, que es oscuro, hasta su propio
borde en x=-120000 (463 m). La "banda" es ese plano, y su grosor aparente es solo el angulo
entre -0.4 y -3.3 de elevacion.

**El Anfiteatro es un cuenco con la boca abierta en yaw 150..210.** Barrido de 360 con
`trace_world` desde el PlayerStart (-73649, 41996, z ojo 262): en todas las demas
direcciones el graderio corta a 13-24 m; en ese arco no habia impacto ninguno. Fuera de la
boca, a partir de yaw 219, ya estaba la sierra de Yesod (cimas 8000-13500 a 220-390 m).

**Arreglo: dos anillos, como El Claro** (`Claro_Cliff_In_*` / `Claro_Cliff_Out_*`), todo
dentro de `L_DA_Malkuth_Anfiteatro_Sub`, carpeta `Telon`, con `SM_QuarryCliff_01/02/05`:

- **`Anfi_Telon_0..5`** — telon lejano a 270-300 m, cimas 4800-9500, para la linea de
  cielo. La ultima sube a 8650 para empalmar con Yesod.
- **`Anfi_Reborde_0..8`** — reborde cercano a 58-68 m, cimas 1250-2200.

**Por que hicieron falta los dos.** Con solo el telon lejano la banda negra SEGUIA ahi:
tapaba el cielo pero dejaba ver el plano entre 44 m y 270 m. La clave es que **el plano
esta por debajo del ojo**, asi que basta con que la cima del reborde quede por encima de
z=262 para taparlo entero desde cualquier punto de la arena. Se le dio 1250-2200 (no 400)
para que aguante tambien mirando desde el graderio.

**Lo que NO se hizo y por que:** agrandar `SM_Suelo_Base` habria sido un cambio de una sola
propiedad, pero para llegar al telon necesitaba ~350 m de radio y **se habria comido
Yesod**, que esta a 316 m y cuyo suelo (`Yesod_Suelo`, cima -60) quedaria por debajo del
plano a z=-6. Tampoco se toco `SM_Plano_Ref_Norte`: es global y lo comparten todas las
zonas.

**Verificacion — y una leccion sobre el paso del barrido.** Primero se barrio **cada 2.5 de
yaw** y dio "sin rendijas". **Era falso**: al mirar la captura habia una cuña de cielo a la
izquierda. Un barrido grado a grado encontro un **hueco real en yaw 144-146**, entre el
final del graderio (que corta a 24 m) y `Anfi_Reborde_0`. El paso de 2.5 grados salto por
encima: 143 daba 24 m y 146 daba 70 m, y el agujero estaba justo en medio.

**Regla: para dar por cerrado un arco, barrer de 1 en 1 grado y a dos elevaciones.** Un
hueco de 2 grados es perfectamente visible en pantalla (a 90 de FOV son ~27 px de 1208) y
se cuela en cualquier paso mayor.

Tapado con `Anfi_Reborde_9` (yaw 145, 50 m, cima 1700). Barrido definitivo de 130 a 230
grado a grado y a 0.4 y 2.0 de elevacion: **sin rendijas**, todo muere a 51 m o menos.
Commit verificado contra disco.

**Critica del resultado, ya recapturado en Lit.** En Detail Lighting el reborde parecia
"bloques de cantera apilados"; **en Lit esa lectura casi desaparece** — el color calido y
el corte de sol y sombra rompen las juntas y lee como pared de canon. Esa critica era un
artefacto del modo de vista, no del montaje.

Lo que si queda:

1. **El reborde se come el telon lejano.** Al ser alto (1250-2200) y estar cerca (50-68 m),
   los montes de 270-300 m no asoman nada. Se pusieron dos anillos y solo se ve uno. Bajar
   el reborde a ~800-1200 lo arreglaria, pero entonces deja de tapar el plano de referencia
   visto desde lo alto del graderio. **Compromiso sin resolver.**
2. **Franja clara al pie de las rocas.** Entre la piedra de la arena y los pies del reborde
   asoma el suelo base de la zona, muy palido y a pleno sol: lee como un hueco quemado. Es
   el mismo problema de material que la plaza de El Claro.

**Comprobar que no se rompe nada ajeno, ANTES de colocar:** se midio la distancia de cada
pieza propuesta al centro de las 12 zonas. La mas cercana era `LI_13_PortalYesod` a 146 m,
y los portales y triggers de la zona estan todos en yaw 233-269, o sea fuera del arco: el
telon no tapa ninguna salida.

## El cielo negro de El Claro era el anillo del Gazebo (2026-08-14, tarea 3)

**No era un problema de luz.** Trazando hacia arriba desde la camara del Claro
(44000, -13650, 320) a yaw 90:

| Elevacion | Que hay |
|---|---|
| 20-25 | acantilados del propio Claro, a 58-61 m |
| **30-45** | **`Gazebo_Monte_21` y `Gazebo_Monte_25`, a 161-205 m** |
| 55+ | cielo de verdad |

O sea: el "cielo negro" del encuadre era la cara en sombra de los montes del anillo del
Gazebo, que asomaban a 41 y 46 de elevacion. El cielo real empezaba fuera de encuadre (el
FOV vertical solo llega a 37.5).

**Perfil de silueta desde El Claro, arco yaw 60-120, antes → despues:**
42/58/50/42/34 → **26/38/30/38/34**.

**Arreglo: bajados 7 montes del Gazebo** (`Monte_2, 15, 21, 25, 26, 28, 29`), con la cota
calculada por dos restricciones a la vez, no a ojo:

- desde El Claro la cima no debe pasar de **28** de elevacion (sus propios acantilados
  rematan a ~25, asi que por encima toca cielo);
- desde el Gazebo no debe bajar de **22**, para que siga siendo un telon.

Los 7 tenian solucion sin conflicto. Quedan en 18-26 vistos desde El Claro y en 24-44
vistos desde el Gazebo. Barrido de 360 desde el Gazebo despues del cambio: **sin agujeros**,
techo de 30-60 en todas las direcciones. Commit verificado contra disco.

**Lo que remata ahora el encuadre del Claro es el propio Claro:** sus acantilados y sus
`Claro_Abeto_*` a 34-39 de elevacion, con los montes del Gazebo detras a 30. Esa es la
relacion que se buscaba.

### Dos cosas que la nota anterior daba por hechas y son falsas

1. **"La luz la ponen los rellenos locales."** En El Claro solo hay **dos** luces locales,
   `Claro_GateLight_L` y `_R`, de **8 candelas** y 10 m de radio, en la puerta. No iluminan
   la plaza. Los millares de candelas de la nota vieja son de otra zona.
2. **"No entra cielo / no llega el sol."** Rejilla de 35 puntos sobre el suelo real de la
   plaza, trazando hacia el sol (yaw -30, elevacion 38): **el 57% recibe sol directo**. Lo
   que estaba mal medido antes era el muestreo: los 5 puntos de la primera prueba estaban
   pegados a una roca y daban "bloqueado" por ella, no por el reborde.

Por eso **no se toco ningun acantilado del Claro**. Si hiciera falta mas sol, los que tapan
de verdad en el azimut del sol son solo cuatro y estan medidos: `Claro_Abeto_32` (18 m,
cima 3774, tendria que bajar a 1742), `Claro_Abeto_35` (34 m, 4881 → 2987),
`Claro_Cliff_In_9` (16 m, 2415 → 1582) y `Claro_Cliff_Out_11` (34 m, 3432 → 2983).

**Si la plaza sigue leyendo demasiado caliente**, el dial ya no es la geometria: es
`M_DA_MK_Piedra_Marfil` (rugosidad 0.22, muy pulida para piedra). Ojo que es global.

### Comprobado por fin en Lit: el arreglo es PARCIAL

Toda la verificacion de arriba se hizo con el visor en **Detail Lighting** sin saberlo, que
pinta el color base de todo en gris neutro. Recapturado en Lit, el veredicto honesto:

- **Entra cielo, si.** Donde antes habia negro puro ahora hay **azul con nubes**, arriba a
  la izquierda y en el centro. Bajar los 7 montes del Gazebo funciono.
- **Pero la franja de cielo es minima**, una tira estrecha en el borde superior y en buena
  parte tapada por los `Claro_Abeto_*`. **La relacion invertida sigue ahi**: el suelo de la
  plaza es lo mas brillante del encuadre, mas que el propio cielo.

**O sea que el problema de fondo nunca fue la geometria: es el suelo.** La plaza lee blanca
y plana, y ninguna cantidad de cielo la va a equilibrar mientras siga asi. El siguiente
dial es `M_DA_MK_Piedra_Marfil` (rugosidad 0.22), no mover mas rocas. Es un cambio global
que afecta a varias zonas, asi que conviene hacerlo mirando dos o tres a la vez.

**Artefacto sin identificar:** en el borde superior del encuadre, sobre el acantilado del
fondo, hay una mancha con aspecto de **damero** (textura sin cargar o material por defecto).
**Es anterior a los cambios de esta sesion** — ya sale en la captura del estado inicial.
`ScreenCoordsToWorld` **no la alcanza**, o sea que no tiene colision: apunta a agua,
follaje o algo translucido, no a geometria solida.

### Metodo: el "perfil de techo"

Para saber si una zona esta tapada, barrer yaws y para cada uno buscar la elevacion mas
alta con impacto. Da la silueta en numeros y permite comparar antes/despues sin depender de
mirar capturas. Es lo que hizo evidente que el Gazebo esta **debajo de una tapa de 50-60
grados en los 360**, que es un pendiente de verdad y no se ha tocado.

### El modo de vista del viewport se torcio a mitad de sesion

De golpe todas las capturas salieron lavadas y sin color, en todo el mapa. **No era el modo
edicion de Level Instance** (hay capturas en color estando en modo edicion). Se descarto que
fuera el render o los materiales renderizando la miniatura de un asset con
`CaptureAssetImage`: **salio a todo color**. O sea es estado del viewport del nivel (View
Mode / Show Flags), y **no se puede cambiar por MCP**: hay que tocarlo a mano en el editor.

Consecuencia practica: **las trazas no se ven afectadas**, las capturas si. Por eso toda la
verificacion de esta sesion se apoya en numeros y no en mirar la imagen.

## PROXIMA SESION — empezar por aqui (escrito 2026-08-14 12:35)

**Antes de nada: devolver el viewport a `View Mode > Lit` y comprobar `Show > Post
Processing`.** Sin eso no se puede juzgar nada de luz o color.

**0. Repaso visual de lo de esta sesion.** Los tres arreglos estan verificados por
geometria pero **ninguno se ha visto con el visor en condiciones**. Camaras exactas:
El Claro (44000, -13650, 320) yaw 90; Anfiteatro (-73649, 41996, 262) yaw 180 y yaw 150.
Mirar sobre todo si la plaza del Claro sigue leyendo demasiado caliente ahora que detras
hay cielo de verdad en vez de monte en sombra.

**1. El Gazebo esta debajo de una tapa.** Es el pendiente gordo que ha salido midiendo.
Perfil de techo desde (64000, 16000, 262): **50-60 de elevacion en las 24 direcciones**.
Su anillo de 34 montes esta demasiado cerca y demasiado escalado; no es un telon de fondo,
es un pozo. Es el mismo trabajo que se acaba de hacer para el Claro pero mirando desde
dentro del Gazebo: bajar cimas con un objetivo numerico (algo como 25-30 de techo) y
comprobar con `probe_gaz360` que no se abren agujeros.

**2. Los abetos del borde del Claro.** `Claro_Abeto_32/35` rematan a 53-62 de elevacion a
18-34 m. Son los que mas cierran el encuadre por arriba ahora que los montes bajaron. Si se
quiere mas cielo, mover o quitar esos dos es mas barato que tocar roca.

**3. Volver a mirar el agua de Puente, Mirador y Jardin.** Sigue pendiente de la sesion
anterior: al colocar `BP_SolAgua_Global` se arreglo el MPC global y esas tres zonas no se
han revisado desde entonces.

### Herramientas que deja esta sesion

En el scratchpad, `ue.mjs`: habla con el MCP del editor por HTTP y **guarda las capturas
como PNG en disco** (`shot`, `thumb`, `call`, `script`). Sin eso `CaptureViewport` no cabe
en una respuesta de herramienta. Usa `node:http`, no `fetch`.

Los `probe_*.py` que se han quedado utiles: `probe_arco` (barrido de 360 buscando el
horizonte abierto), `probe_rendijas` (barrido fino para rendijas), `probe_gaz_claro` y
`probe_gaz360` (perfil de techo), `probe_rejilla` (rejilla de sol sobre el suelo),
`probe_bloqueo` (que actor tapa el sol y a que cota tendria que bajar).

## Comparacion contra el PDF, zona por zona (2026-08-14)

**Como leer el PDF, que no era obvio.** `Dark_Angels_MALKUTH_Demo_Visual_Optimizado.pdf`
lo genero ReportLab y **no hay pdftoppm ni poppler completo en esta maquina** (solo
`pdftotext`, en `C:\Program Files\Git\mingw64\bin`). Las 14 laminas se sacan asi:

- Son XObject de imagen con `/Filter [/ASCII85Decode /DCTDecode]`. **Hay que deshacer el
  ASCII85 antes**, o el fichero empieza por `s4IA0` y no es un JPEG valido.
- Buscar los marcadores `FFD8...FFD9` a pelo **no funciona**; hay que ir por el
  diccionario: `/Subtype /Image` → `/Length` → volcar el stream.
- Script en `scratchpad/extraer2.mjs`.

**Indice de laminas:** `lam_01` = portada, que es la vista de la estacion 01. `lam_02` =
mapa de ruta. `lam_03` a `lam_14` = estaciones 02 a 13. O sea **El Claro = `lam_05`,
Gazebo = `lam_06`, Santuario = `lam_07`, Puente = `lam_08`, Anfiteatro = `lam_09`**.

### La frase que lo juzga todo

Del cierre del PDF: *"Paraiso material: tierra, agua, roca, bosque y marmol marron. La
inquietud nace de la escala; evitar jardin artificial, ruinas dominantes y cielo de nubes."*

Son tres prohibiciones explicitas, y ahora mismo **incumplimos las tres**:

| Prohibicion | Estado |
|---|---|
| jardin artificial | El Jardin es cesped plano uniforme + setos en caja alineados |
| ruinas dominantes | Acantilados de cantera y plazas de losa dominan casi todas las zonas |
| cielo de nubes | Cielo azul con cirros en todas partes; las laminas son calidas y con bruma |

Y **"marmol marron"**: se construyo con `M_DA_MK_Piedra_Marfil`, marfil. El color base
esta equivocado, no solo la rugosidad.

### Los cuatro huecos sistemicos

1. **El suelo.** En las laminas el suelo es **tierra batida con hierba y flores creciendo
   entre las piedras**. Aqui es losa marfil pulida, continua y brillante. Es el mismo
   problema que ya aparecio como "plaza sobreexpuesta" en El Claro y como "franja quemada"
   en el Anfiteatro: **no era exposicion, era el material**.
2. **Densidad de vegetacion.** Las laminas estan llenas: matorral, helechos, hiedra
   colgando, musgo entre las juntas, flores. Aqui la vegetacion es puntual y decorativa.
3. **Faltan los personajes y las estatuas**, que es lo que sostiene cada encuadre del PDF.
4. **La luz.** Las laminas son de sol bajo y calido con bruma volumetrica; aqui el sol es
   alto y duro, y el contraste se va a negros aplastados (Santuario) o a blancos
   reventados (Claro).

### Zona por zona

**01 Jardin Geometrico (`lam_01`) — la diferencia mas grande de todas.**
El PDF es un **valle alpino verde** con bancales de seto bajo y desbordado siguiendo el
terreno, prado con flores, coniferas sueltas, **un arroyo junto al camino**, picos grises
con nieve y cascadas, y de landmark **un coloso de ANGEL sentado, de piedra clara, con alas
e inclinado hacia el jugador**. Lo construido: cesped verde acido plano, setos en caja
alineados, camino de losas, mesetas rojas de fondo, sin agua, y de landmark **una esfinge
egipcia oscura**. Coinciden la silueta del landmark y poco mas.

**04 El Claro (`lam_05`).** El PDF es un **claro de bosque intimo**, de unos 25-30 m,
suelo de tierra con hierba, bloques de ruina cubiertos de musgo, arboles alrededor, y al
fondo una **puerta de bronce labrada** con arco y una estatuilla de angel en hornacina.
Lo construido: **plaza pavimentada enorme** de marfil, anillo de acantilados rojos, puerta
de tablones lisa, y cuatro postes blancos luminosos que **no existen en el PDF**.

**06 Santuario (`lam_07`) — el mas cercano en composicion.** Gruta cerrada, arboles
enmarcando, altar con pila de agua, senda al fondo: eso esta. Falta lo que lo hace la
lamina: **Cassiel** (angel de pie, tunica clara, alas grandes, rostro velado), **decenas de
velas** entre el musgo, un cofre de madera, vasijas. Y la luz esta mucho mas dura: los
rayos leen como sprites blancos picudos, no como haces suaves.

**08 Anfiteatro (`lam_09`).** Falta el elemento grafico que define el espacio: **el suelo
de la arena lleva anillos concentricos y una estrella inscrita**. Tampoco esta el **porton
monumental con pilastras y estatuas en hornacinas** del fondo. Y el cielo de la lamina es
**tormentoso**, no azul: es el beat donde el tono se ensombrece.

### La linea del horizonte NO es geometria: es un dibujo del editor

Primero se atribuyo al canto de `SM_Plano_Referencia`. **Falso, y ademas ese actor no
existe con ese nombre**: los planos de referencia son cuatro (`SM_Plano_Ref_Norte`, `_Sur`,
`_Este`, `_Oeste`), todos a z=-50, cubriendo x -120000..120000 e y -90000..90000.

Lo que se ve son **dos lineas rosadas finas** (mas una diagonal) que **se dibujan por
delante de la roca y de los arboles, sin respetar la profundidad**. Ampliando el recorte se
ve clarisimo. Nada que este en el mundo se pinta encima de lo que tiene delante.

**Verificado lanzando PIE desde la misma pose: las lineas desaparecen por completo.**
O sea que **no salen en el juego y no hay nada que quitar del nivel**. Es un overlay del
viewport; el sospechoso son las visualizaciones de agua (el Jardin tiene `Rio_Malkuth2` y
un `WaterZone` de 81200 x 81200 m, cuyos limites proyectan justo como rectas larguisimas).
Para no verlas mientras se compone: **tecla G (Game View)** en el viewport.

**No se toco ningun actor de agua a proposito** — segun la nota de arrays de structs, esos
splines pueden tumbar el editor, y no hacia falta para responder la pregunta.

Dos trampas del metodo que costaron tiempo aqui:
- `ScreenCoordsToWorld` **no alcanza estas lineas** (ni el "damero" del Claro). Cuando una
  sonda no impacta, la conclusion util no es "no hay nada": es **"no es geometria solida"**.
- Cuando una llamada del script falla, el `try/except` de Python **no lo contiene**: el
  error sale del sandbox y aborta todo el script. Hay que sondear de una en una.

**Recortar y ampliar la captura resuelve en un minuto lo que media hora de trazas no
resolvio.** Herramienta: `scratchpad/recortar.mjs` (decodifica el PNG, recorta y amplia).

### Lista de assets, por orden de impacto

1. **Angel colosal sentado** para el Jardin — sustituye a `SM_Coloso_Landmark` (la esfinge).
   Es el plano que abre el juego.
2. **Angel de pie con alas** para Cassiel en el Santuario.
3. **Huestes**: tunica clara con capucha, alas emplumadas, **rostro velado sin rasgos**,
   ribetes dorados. Tres armas: espada, lanza y arco. Salen en `lam_05` y `lam_09`.
4. **Estatuas de angel medianas**: en hornacina junto a la puerta del Claro, en el porton
   del Anfiteatro, sobre el risco del `lam_03`.
5. **Puerta de bronce labrada** para El Claro.
6. Vasijas, cofre, velas sueltas para el Santuario.

### Lo que NO es el problema

El layout, las distancias, la ruta y los cierres de horizonte estan bien. Las tres tareas
de esta sesion iban de encuadre y no habia mas jugo ahi: **lo que separa esto de las
laminas es material, vegetacion y assets heroe**, no mover mas rocas.

## El suelo, a marron: que era de verdad y como se cambio (2026-08-14)

**Primer error, corregido: el suelo brillante de El Claro NO era `M_DA_MK_Piedra_Marfil`.**
Eso venia de las notas viejas y me lo crei sin comprobarlo. Lo que se pisa en la plaza es
**`SM_Claro_Tierra`** (un cilindro de Engine aplastado) con material
**`M_DA_MK_Tierra_Arena`**. El Landscape del Claro lleva `M_DA_MK_Valle_Hierba`, que es otra
cosa. Metodo para no volver a equivocarse: `trace_world` recto hacia abajo desde la camara,
`find_actors` con `actor_type` StaticMeshActor en una caja pequeña alrededor del impacto, y
leer `StaticMesh` + `OverrideMaterials` del componente.

**La causa exacta.** `M_DA_MK_Tierra_Arena` no expone parametros (es Material, no instancia).
Su grafo: BaseColor = textura `T_DA_Dirt_C` **multiplicada por un Constant3Vector de
(0.86, 0.78, 0.66)** — un tinte casi blanco. Ese multiplicador era el que lavaba la plaza.
Rugosidad y normal ya salian de sus texturas y estaban bien; Specular ya estaba a 0.08.

**Cambio aplicado:** el tinte a **(0.20, 0.14, 0.095)**, marron calido. Nada mas del grafo.
Nodo: `MaterialExpressionConstant3Vector_0`. Recompilado y guardado con
`AssetTools.save_assets`. **Copia previa en `_Backups/Materiales_2026-08-14/`** porque el
asset **no esta en git** (las materiales de Malkuth son untracked).

**Radio de impacto medido, no supuesto:** `AssetTools.get_referencers` da exactamente dos
mapas, **Claro y Anfiteatro**. Justo las dos zonas donde estaban los sintomas.

### Medir la imagen, porque el ojo miente con exposicion automatica

Tras el cambio la plaza **parecia igual de clara** y casi lo doy por fallido. Falso. Midiendo
la media de pixeles por region (`scratchpad/medir.mjs`):

| Region | Antes | Despues |
|---|---|---|
| Suelo del Claro, luma | 211 | **157** |
| Suelo del Claro, saturacion | 13% | **38.5%** |
| Acantilado del Claro, luma | 41 | **83** |
| **Ratio suelo/acantilado** | **5.2 : 1** | **1.9 : 1** |
| Franja al pie del Anfiteatro, luma | 187 | **86** |
| Franja al pie del Anfiteatro, saturacion | 29% | **70%** |

La relacion invertida esta practicamente corregida. **Con exposicion automatica, comparar dos
capturas a ojo no vale**: al oscurecer la superficie dominante sube la exposicion y todo lo
demas se aclara, asi que el cambio "no se nota" aunque sea grande. Hay que medir.

### El dial que queda: la exposicion, y por que no la toque

`PostProcessVolume_0` del Master (`bUnbound: true`, prioridad 1):

- `autoExposureMethod: AEM_Histogram`
- `autoExposureMinBrightness: 0.06`, `autoExposureMaxBrightness: 6` → **rango de 100:1**
- `autoExposureBias: 0.35`

Con ese rango, la superficie que llena el encuadre **siempre** se renormaliza a tono medio.
Por eso bajar el albedo a la mitad otra vez ya casi no cambio el suelo: lo que cambia es el
reparto tonal, no el brillo del suelo. **Si se quiere que la plaza lea oscura de verdad, el
dial es estrechar ese rango o pasar a exposicion manual, no seguir bajando el albedo.**

**No se toco.** Escribir `Settings` en un PostProcessVolume por MCP **reemplaza el struct
entero**, y ahi vive tambien el color grading: habria que reenviarlo todo en la misma
llamada. Es un cambio que conviene hacer a proposito y verificando, no de pasada.

## Exposicion: ajustada y medida, PERO EL MAESTRO NO GUARDA (2026-08-14)

### El Maestro SI guarda. Lo que falla es solo su `_BuiltData`

**Primero di una falsa alarma diciendo que el mapa no guardaba. Es falso.** El dialogo
"L_DA_Malkuth_Master.umap failed to save" es un **resumen agregado** del editor: se dispara
porque uno de los paquetes del lote fallo, aunque el mapa ya estuviera escrito. Unas lineas
mas arriba, el log dice lo contrario:

    LogSavePackage: Moving 'Saved/L_DA_Malkuth_Master5F2DAA5B....tmp'
                 to 'Content/DarkAngels/Maps/L_DA_Malkuth_Master.umap'

**Verificado en el binario, que es lo unico que no opina.** Buscando el float del bias en el
.umap actual y en la copia previa: en el **offset 583524** la copia tiene `0.35` y el
fichero actual tiene `-0.65`. Un solo valor cambiado, en un solo sitio. Los clamps (`0.06`
en 583553 y `6.0` en 583582) intactos en ambos. Herramienta: `scratchpad/buscar_float.mjs`.

**Moraleja de metodo:** `save_assets` devolvio `false`, `is_dirty` devolvio `false`, la fecha
del fichero cambio y el tamaño no. Cuatro señales, todas ambiguas. Para saber si un valor
llego al disco, **buscarlo en el binario**.

### Que le pasa al `_BuiltData` y por que no es grave

**Cuando empezo:** el aviso `does not have any of the provided object flags (0x10000002)`
aparece **solo en el log de la sesion actual**, primera vez a las 10:59:51. No sale en
ninguno de los logs del 12, 13 ni en el backup del 14. Es de esta sesion.

**Que lo arreglo la ultima vez:** en la sesion anterior corrio una construccion de
iluminacion —`LogStaticLightingSystem: storing lightmap data for 453 meshes in 11
LightmapResourceClusters`— y **justo despues el BuiltData guardo bien**, con su
tmp→final. Ese guardado es el fichero que hay en disco (304398 bytes, 13/08 23:30).

**Por que no es grave, con numeros:**

| | |
|---|---|
| Sol (`DirectionalLight`) | **Movable** — no usa nada horneado |
| `SkyLight` | **Movable** — idem |
| PointLight | 60, todas **Stationary** |
| SpotLight | 14, todas **Stationary** |
| GI / reflexiones | **Lumen** (`r.DynamicGlobalIlluminationMethod=1`, `r.ReflectionMethod=1`) |

La luz principal y el cielo son dinamicos y la GI la pone Lumen, asi que el lightmap solo
afecta a las 74 luces locales estacionarias. Y en el log de esta sesion **no hay ni un aviso
de "needs to be rebuilt"**: el motor no considera la iluminacion invalida.

**Estado real:** el `.uasset` en disco esta intacto (no se ha reescrito ni una vez hoy) y se
cargara bien al reabrir. Lo unico que no se puede es **persistir un horneado nuevo**. Con
esta configuracion de luces, eso hoy es ruido: un dialogo molesto en cada guardado.

**Como quitarlo:** `Build > Build Lighting Only` una vez desde el editor. Es exactamente lo
que precedio al ultimo guardado bueno, y regenera el registro con sus flags. **No hace falta
borrar nada.** Por MCP no se puede lanzar: no hay herramienta de build ni forma de ejecutar
comandos de consola o cvars, y `save_actor` sobre el volumen tampoco vale ("is not an
external actor asset").

### ✅ RESUELTO — el build de iluminacion lo arreglo (2026-08-14, 16:40)

Angel lanzo `Build Lighting Only` y el guardado siguiente fue limpio. Secuencia en el log:

    22:39:28  LogStaticLightingSystem: Running Lightmass
    22:39:46  L_DA_Malkuth_Master_BuiltData storing lightmap data for 453 meshes
              en 11 LightmapResourceClusters
    22:40:41  Saving Map: L_DA_Malkuth_Master
    22:40:41  Moving output files for package: L_DA_Malkuth_Master           <-- ok
    22:40:41  Saving Package: L_DA_Malkuth_Master_BuiltData
    22:40:41  Moving output files for package: L_DA_Malkuth_Master_BuiltData <-- ok

**Ni un `failed to save` ni el aviso de flags despues de esa hora**, y `save_assets` devuelve
`true` por primera vez en toda la sesion. El `_BuiltData` se ha reescrito por fin: llevaba
clavado en 13/08 23:30 y ahora es del 14/08 16:40. (El horneado ocupa lo mismo, 304398
bytes, porque son los mismos 453 meshes y los mismos 11 clusters.)

**Los dos cambios del dia, verificados en binario y no por lo que diga el editor:**

| Fichero | Que se busco | Resultado |
|---|---|---|
| `L_DA_Malkuth_Master.umap` | bias `-0.65` | 1 coincidencia en 583524 |
| idem | clamps `0.06` y `6.0` | en 583553 y 583582 |
| `M_DA_MK_Tierra_Arena.uasset` | tinte `0.20 / 0.14 / 0.095` | seguidos en 11561, 11565, 11569 |
| idem | tinte viejo `0.86 / 0.78 / 0.66` | **0 coincidencias** |

**Aparte, sin relacion:** los 6 "failed to save" de la sesion anterior eran todos de
`L_DA_Malkuth_Elevador_Sub`, otro asunto.

**Los sublevel guardan sin problema.** Jardin_Sub y Anfiteatro_Sub se escribieron y
verificaron hoy.

### El ajuste, y el error que cometi primero

**Intento 1, equivocado:** estrechar el rango a Min 0.35 / Max 3.0. Resultado medido: el
Claro **no se movio** (156 → 156) y **el Santuario se hundio** (86 → 37).

Los clamps no sirven para esto, y conviene tener clara la direccion:
`EyeAdaptation = clamp(luminanciaMedia, Min, Max)` y la exposicion va como `1/EyeAdaptation`.

- **`Min` controla cuanto ACLARAN las escenas oscuras.** Subirlo oscurece la gruta. Fue lo
  que rompio el Santuario.
- **`Max` controla las claras, y en el sentido contrario** al que hacia falta: bajarlo las
  aclara. Por eso Anfiteatro y Jardin salieron algo mas claros, no mas oscuros.
- Una escena clara cuya media ya cae dentro del rango **no se ve afectada por ningun clamp**.
  Por eso el Claro no se movio.

**Intento 2, el bueno:** clamps devueltos a su valor original (0.06 / 6.0) y bajar
**`autoExposureBias` de +0.35 a −0.65 EV**. Eso baja el conjunto sin tocar la adaptacion.

| Region | Antes del EV | Despues |
|---|---|---|
| Claro, suelo | 157 | **91** |
| Claro, acantilado | 83 | **36** |
| Anfiteatro, franja | 86 | **41** |
| Santuario, gruta entera | 86 (lavado) | **62** |
| Jardin, cesped | 143 | **81** |

El Santuario **mejora**: se lee la estructura de la gruta y el cielo deja de reventar a
blanco. Ninguna de las cuatro zonas se rompe.

### Escribir `Settings` en un PostProcessVolume sin perder nada

Reemplaza el struct entero, asi que hay que leer, modificar y reescribir **dentro del mismo
script**, sin que el struct salga del editor. Y hay que verificarlo: se comparan el numero
de claves y una lista de testigos de color grading antes y despues.
Resultado aqui: **463 claves antes y 463 despues, ninguna perdida, ningun testigo alterado.**
Ojo tambien con los `bOverride_*`: sin ponerlos a true el volumen ignora el valor nuevo.
Script en `scratchpad/exposicion.py`.

## NPCs de Tripo: Sariel y Cassiel importados y colocados (2026-08-14)

**Solo van dos, y lo dice el compendio.** `Dark_Angels_Compendio_Visual_NPCs_y_Modelado_3D_v1.pdf`
da la localizacion de cada uno: Sariel "multiples esferas, siempre a distancia", Cassiel
"Altares de Contemplacion" y **Orphan "Cueva oculta en Binah"**. Binah es otra Sefira, no
Malkuth: Orphan no entra en este mapa.

### Que se importo

Con `SkeletalMeshTools.import_file` (`import_materials` + `import_textures` +
`create_physics_asset`), a `/Game/DarkAngels/Characters/NPCs`:

| | Sariel | Cassiel |
|---|---|---|
| Fichero | `NPCs\Sariel\sariel rigged.fbx` | `NPCs\Cassiel\Cassiel.fbx` |
| Altura de malla | 98.4 cm | 98.3 cm |
| **Escala aplicada** | **1.829** | **1.8309** |
| Huesos | 118, raiz `root` | 118, raiz `root` |
| Vertices | 45.782 | 46.495 |

Los dos traen el mismo rig de Tripo, asi que deberian poder compartir animaciones.
`import_file` **devuelve solo la malla** aunque cree tambien esqueleto, physics asset,
material y texturas: hay que listar la carpeta para ver lo que hizo de verdad.

### Donde quedaron

- **Sariel**: sobre `Mirador_EstatuaBase`, en (-16000, -22850, 468), yaw -90 mirando a la
  escalera. **Sustituye al marcador `Mirador_Estatua_Sariel`**, que **no se borro**: se
  oculto con `bHidden` + `bVisible=false`, que es reversible. Su cima era 639.2 y la de
  Sariel es 647.8, o sea misma silueta.
- **Cassiel**: junto al altar del Santuario, en (44120, 48280, 169.1), yaw 195, al lado +Y
  (la derecha del jugador que entra desde -X), como en la lamina `lam_07`.

Ambos en la carpeta `NPCs` de su zona. Commits de los dos sublevel verificados contra disco.

### El material esta bien; lo que falla es el suelo de la zona

Los NPC leen **blancos y sin detalle**, y casi lo doy por un fallo de importacion. No lo es:

- El grafo del material esta **bien cableado**: `MP_BaseColor` ← TextureSample del Diffuse,
  `MP_Normal` ← TextureSample del Normal. Comprobado nodo a nodo.
- La textura Diffuse esta bien importada: es un atlas de armadura gris-plata, que ademas es
  justo lo que pide el compendio.
- Medido en la captura: Sariel esta a **luma 168 y 23% de saturacion** — no esta reventado.
  **El suelo de la plataforma del Mirador esta a luma 250**, o sea blanco puro. Es el que
  se lleva la exposicion por delante.

**El thumbnail del asset engana:** salio gris con **0.1% de saturacion**, porque
`CaptureAssetImage` lo renderizo con material por defecto. No sirve para juzgar materiales.

### Metallic y roughness conectados — y el mapa de Tripo no es de fiar

En las carpetas `.fbm` hay `*_metallic.JPEG` y `*_roughness.JPEG` que el FBX no referencia,
asi que la importacion los dejo fuera. Se han importado a mano y cableado:

- `T_DA_Sariel_Metallic` / `_Roughness` (4096x4096) y `T_DA_Cassiel_*` (2048x2048).
- Los cuatro con **`SRGB=false` y `CompressionSettings=TC_Masks`**, que es obligatorio: son
  datos, no color. El Diffuse se queda en sRGB y TC_Default, como debe.
- Cableados al canal **R** (son mapas en escala de grises, no RGB) de `MP_Metallic` y
  `MP_Roughness`. Verificadas las cuatro salidas de cada material.

**El efecto visual es pequeño, y conviene decirlo:** medido sobre el cuerpo de Sariel en la
misma pose, luma **195.8 → 187.0** y saturacion **11.4% → 12.7%**. Una mejora modesta, no
una transformacion.

**La razon, y es un problema de origen:** el mapa metallic de Tripo esta **casi blanco en
todo el atlas** (~0.68 de media). Esta declarando el personaje como metal de arriba abajo,
piel y tela incluidas. Con metallic alto el difuso se apaga y todo pasa a ser especular, que
es justo lo que aplana la lectura. **No es un mapa de fiar tal cual.** Vias: multiplicarlo
por ~0.3, o dejar solo el roughness y poner metallic a un valor bajo a mano. Aplica
igual a cualquier otro personaje que salga de Tripo.

Pendiente aparte: el suelo del Mirador necesita el mismo tratamiento que
`M_DA_MK_Tierra_Arena`, y los materiales quedaron con nombres de Tripo
(`tripo_mat_b0fc3593`), que conviene renombrar.

### Trampa: guardar sublevel fallaba con Error Code 32

Durante un rato **ningun sublevel guardaba**: `MoveFile ... (Error Code 32)`, o sea fichero
en uso por otro proceso, y el commit fallido **descarta la sesion de edicion** y pierde lo
colocado. Ademas deja un **dialogo modal** que cuelga cualquier llamada MCP posterior.

**Se arreglo reiniciando el editor.** Ojo con el diagnostico: probar a abrir el `.umap` en
exclusiva **no sirve** para identificar al culpable — con el editor abierto salen bloqueados
todos los paquetes cargados, incluido el Master y hasta `M_DA_MK_Tierra_Arena.uasset`, que
se habia guardado perfectamente una hora antes.

## El suelo del Mirador: el albedo no era la causa (2026-08-14)

Se pidio "lo mismo que a `Tierra_Arena`". Se hizo, pero **el diagnostico era otro** y
conviene dejarlo escrito para no repetirlo.

**Que material es cada cosa en el Mirador:**

| Pieza | Material | Referenciadores |
|---|---|---|
| `Mirador_Plataforma` (el suelo) | `M_DA_MK_Piedra_Calzada` | **3** |
| Muros, barandas, base de la estatua, pedestal | `M_DA_MK_Piedra_Marfil` | **~75** |

`Piedra_Marfil` lo usan el RuinsKit entero, el MirrorLabyrinthKit, todos los escaneos de
estatuas y 8 mapas. **No se toco**: es una decision de otro calibre.

**Paso 1, el albedo (hecho).** `Piedra_Calzada` tiene la misma estructura que
`Tierra_Arena`: textura `T_DA_Travertine_C` por un Constant3Vector. Tinte de
**(0.62, 0.50, 0.36) → (0.26, 0.20, 0.14)**. Resultado medido: el suelo solo bajo de
**luma 239 a 229**. Casi nada.

**Paso 2, la causa real.** En la plataforma hay dos luces locales:

| Luz | Antes | Ahora |
|---|---|---|
| `Mirador_Luz_Llave` | **800 candelas** | 150 |
| `Mirador_Luz_Estatua` | **300 candelas** | 80 |

800 candelas a dos metros del suelo en una plataforma pequeña. **Para comparar, las luces de
la puerta de El Claro son de 8.** Eso era lo que reventaba el suelo, no el color base.

**Resultado total, medido en la misma pose:**

| | Antes | Despues |
|---|---|---|
| Suelo, luma | 239.2 | **211.3** |
| Suelo, saturacion | 12.5% | **32.9%** |
| Sariel, luma | 187.0 | **180.5** |
| Sariel, saturacion | 12.7% | **18.7%** |

**Leccion:** antes de tocar el albedo de un suelo que lee reventado, **mirar las luces
locales**. En El Claro la causa si era el material porque el suelo llenaba el encuadre; aqui
el encuadre es mayormente oscuro y lo que clipa es un foco de 800 candelas.

**Queda un desajuste a proposito:** el suelo ya es marron calido pero la base de la estatua,
los muros y las barandas siguen blancos, porque son `Piedra_Marfil` y no se toco. Si se
quiere igualar, ese cambio afecta a ~75 assets y a 8 mapas: merece hacerse mirando varias
zonas a la vez, no de pasada.

## Piedra_Marfil a marmol marron, verificado por zonas (2026-08-14)

Es el material mas extendido del proyecto: **~75 referenciadores** — el RuinsKit entero, el
MirrorLabyrinthKit, todos los escaneos de estatuas y 8 mapas. Por eso se verifico zona por
zona en vez de mirar solo una.

**Cambio:** el tinte del BaseColor de **(0.58, 0.555, 0.50) → (0.32, 0.27, 0.21)**. Nodo
`MaterialExpressionConstant3Vector_0`, igual que en los otros dos materiales de piedra.
Verificado en el binario: el tinte nuevo esta en el offset 13986 y el viejo ya no aparece.

**Efecto por zona, medido en la misma franja del encuadre:**

| Zona | luma antes → despues | saturacion antes → despues |
|---|---|---|
| Mirador | 178.5 → 174.3 | 33.0% → **43.2%** |
| Gazebo | 206.7 → 194.8 | 40.0% → **46.5%** |
| GabrielC3 | 34.8 → 33.6 | 42.0% → 43.8% |
| Puente | 66.9 → 68.1 | 80.2% → 81.8% |
| Yesod | 167.8 → 167.5 | 7.4% → 7.6% |
| Elevador | 58.3 → 58.3 | 3.0% → 3.0% |

**Solo se nota de verdad en Mirador y Gazebo.** En Elevador el cambio es literalmente cero y
en Yesod y Puente es despreciable: desde esas camaras no hay superficie de `Piedra_Marfil` a
la vista. Los 75 referenciadores son sobre todo **assets de malla** cuyo material por defecto
es este, no piezas colocadas en todas las zonas. **Util saberlo: el numero de referenciadores
mide el riesgo, no el impacto visual.**

Tambien queda descartado que la pasarela blanca de Yesod sea `Piedra_Marfil`: no se movio.

**Lo que arregla:** el desajuste que dejo el cambio anterior en el Mirador. Suelo, muros,
barandas y base de la estatua vuelven a ser la misma familia de piedra calida.

**Lo que no arregla:** la plataforma del Mirador **sigue siendo lo mas claro del encuadre**
(base a luma 240, muro a 206). Ya no por el material ni por los focos, sino porque es una
superficie grande a pleno sol rodeada de oscuridad, y la exposicion automatica la empuja
arriba. Si molesta, el siguiente dial es un PostProcessVolume local para el Mirador, no
seguir bajando albedos.

## Pulido de los NPCs y volumen local del Mirador (2026-08-14)

**1. Metallic de Tripo atenuado.** Se intercala un `MaterialExpressionMultiply` entre el
TextureSample del mapa y `MP_Metallic`, con **`ConstB = 0.25`**. Asi se conserva la
variacion del mapa pero se le quita el "todo es metal". Hecho en los dos materiales.
**Receta a repetir con cualquier personaje que salga de Tripo.**

**2. Nombres legibles.** Con `AssetTools.move`, que arregla las referencias solo:

| Antes | Ahora |
|---|---|
| `tripo_mat_b0fc3593` | `M_DA_NPC_Sariel` |
| `tripo_mat_b0fc3593_Diffuse` | `T_DA_Sariel_BaseColor` |
| `tripo_mat_b0fc3593_Normal` | `T_DA_Sariel_Normal` |
| `tripo_mat_78e80924` | `M_DA_NPC_Cassiel` |
| `tripo_mat_78e80924_Diffuse` | `T_DA_Cassiel_BaseColor` |
| `tripo_mat_78e80924_Normal` | `T_DA_Cassiel_Normal` |

Verificado despues del renombrado: las mallas siguen apuntando a su material y las cuatro
salidas de cada uno siguen conectadas.

**3. `PP_Mirador`, volumen de post proceso local.** En `L_DA_Malkuth_Mirador_Sub`, carpeta
`Luz`. Caja x -18200..-13800, y -25800..-21400, z -500..1700, o sea toda la zona con la
escalera. `bUnbound=false`, **prioridad 5** (el global del Master es unbound con prioridad 1)
y `BlendRadius=400` para que la transicion no de un salto. Unico override:
**`autoExposureBias = -1.9`** frente al -0.65 global. El struct se leyo, modifico y
reescribio entero: 463 claves antes y 463 despues.

**Resultado medido en la misma pose:**

| Region | luma | saturacion |
|---|---|---|
| Base de la estatua | 240.2 → **219.1** | 11.8% → **23.1%** |
| Muro del fondo | 206.2 → **156.8** | 24.5% → **41.6%** |
| Sariel | 178.7 → **147.9** | 21.3% → 15.8% |

El muro baja 50 puntos de luma y gana 17 de saturacion. **Este era el dial correcto**: tres
materiales de piedra tocados dieron menos que un volumen local bien puesto.

**Ojo:** el volumen dibuja su contorno en el viewport (una linea amarilla arriba del
encuadre). Como las lineas del agua, es solo del editor.

### Correccion: el Santuario tambien tenia marcador de Cassiel

Al fotografiar los NPC en juego aparecio una estatua blanca con aletas junto a Cassiel.
**Era `SM_Cassiel`**, un marcador que ya existia —malla de `/Game/Fab/statue-retopology`,
escala 0.72, con su propia `Luz_Cassiel` de 110 candelas— y le habia plantado el modelo a
**50 cm**, interpenetrandose con el. En el Mirador si busque marcador previo; aqui no, y es
el mismo patron. **Antes de colocar un NPC, buscar por su nombre en la zona.**

Corregido igual que en el Mirador: `SM_Cassiel` **oculto, no borrado**, y el NPC llevado a
su sitio y su giro (yaw -125). La `Luz_Cassiel` se mantiene, que para eso esta.

**Trampa dentro de la trampa:** al reubicarlo, la traza de suelo dio z=285 y lo dejo
flotando. **`bHidden` quita el dibujo pero NO la colision**, asi que el rayo choco con el
marcador oculto. Se resolvio trazando desde **por debajo** de su base (z=55): suelo real a
**8.5**. Pies a 5.7 y cabeza a 196.1.

### Aviso serio visto en PIE: memoria de video agotada

En la captura del Santuario en juego salio en rojo:

    Video memory has been exhausted (1787.690 MB over budget).
    Expect extremely poor performance.

**1.8 GB por encima del presupuesto.** Las texturas de los NPC contribuyen: Sariel trae
BaseColor, Metallic y Roughness a **4096x4096** cada una. Conviene bajar el `MaxTextureSize`
de las de personaje y revisar el resto del presupuesto antes de meter mas modelos.

### MaxTextureSize de las texturas de personaje

Puesto en las ocho texturas de los NPC. Los originales eran mas grandes de lo que parecia:
**Sariel BaseColor, Metallic y Roughness a 4096**, y Cassiel BaseColor tambien a 4096.

| Mapa | MaxTextureSize |
|---|---|
| BaseColor | 1024 |
| Normal | 1024 |
| Metallic | 512 |
| Roughness | 512 |

Metallic y roughness bajan mas porque son mapas casi planos: no llevan detalle que perder.
Comprobado a la distancia de juego: Sariel mantiene placas, hombreras y los tintes lilas.
Medido, luma 147.9 → 142.4 y saturacion 15.8% → 13.8%, o sea el salto de mip y poco mas.

**Cuanto ahorra de verdad, sin inflarlo:** en VRAM, unos **95 MB** de los **1787 MB** de
exceso, poco mas del 5%. Ayuda y evita que el problema crezca con cada personaje nuevo, pero
**no arregla el aviso**. El grueso esta en otra parte: Megascans, los escaneos de estatuas y
las texturas de superficie a 4K. Si se quiere resolver de verdad hay que auditar el
presupuesto entero, no las de personaje.

**El .uasset en disco no encoge:** sigue guardando la imagen original. `MaxTextureSize`
limita lo que se construye y se sube a memoria, no la fuente.

## El coloso de angel sustituye a la esfinge (2026-08-14)

Importado de `World Assets/Malkuth/angel+colosal/tripo_convert_44d7524f-....fbx` como
**StaticMesh** (es una estatua: no necesita rig) a `/Game/DarkAngels/Characters/Colosos`.

**Colocado exactamente donde estaba la esfinge**, calculando la escala a partir de las dos
alturas en vez de a ojo: malla de **0.998 cm**, esfinge de **18750 cm**, factor **18786.7**.
Misma posicion (-33000, -58400), misma cota de pies (-500) y mismo yaw (-150). Resultado
verificado: **18750 cm de alto**, huella 173 x 176 m.

`SM_Coloso_Landmark` **oculto, no borrado**, igual que los otros marcadores.

### Dos cosas que trae de fabrica y conviene saber

**1. El FBX no traia material ni texturas.** Su unico slot venia con `WorldGridMaterial`, o
sea el damero por defecto: en la carpeta no habia ni `.fbm` ni imagenes, al contrario que
los FBX de los NPC (43-48 MB con sus mapas embebidos; este pesa 0.2 MB). Se le asigno
`M_DA_MK_Piedra_Marfil`, la piedra del proyecto.

**2. Solo 7.795 triangulos y 4.720 vertices.** Para un landmark de 187 m eso deja triangulos
de unos 2 m. La silueta aguanta bien, pero **la superficie lee lisa**, sin grano: no tiene
detalle propio y la textura de travertino, estirada sobre 187 m, no se aprecia.

### Como lee

- **Desde el spawn del Jardin** esta a contraluz (el sol viene de yaw ~330 y se mira a yaw 3):
  luma **27.5**. Sale como silueta oscura contra el cielo, y **funciona muy bien** para la
  direccion de "divinidad que abruma".
- **Desde el lado del sol**: luma **92.1** y saturacion 68%. Ahi si se ve que la superficie
  es lisa y el tono tira a arena.

**Es una mejora clara sobre la esfinge**: ahora es un angel sentado y monumental, que es lo
que pide `lam_01` del PDF.

**Si se quiere superficie de verdad**, la via es reexportar desde Tripo **con el paquete de
texturas**, como vinieron Sariel y Cassiel. Un material dedicado con mas tiling tambien
ayudaria, pero `Piedra_Marfil` lo comparten ~75 assets y no tiene parametros, asi que habria
que crear uno aparte.

## Coloso V2: con texturas, 990k vertices y mirando al jugador (2026-08-14)

Segundo export de Tripo, este si con el paquete completo:
`World Assets/Malkuth/angel+statue+3d+model/`, FBX de **50.5 MB** con su `.fbm`
(basecolor, normal, roughness, metallic y rm).

**Falla como StaticMesh.** `StaticMeshTools.import_file` devuelve "produced no assets".
El motivo: **trae un hueso**, asi que Unreal lo trata como skeletal. Importado con
`SkeletalMeshTools.import_file` entra sin problema. Es una estatua con **1 solo hueso**, o
sea que en la practica es estatica; no pasa nada por dejarla como SkeletalMesh.

| | V1 | V2 |
|---|---|---|
| FBX | 0.2 MB | 50.5 MB |
| Vertices | 4.720 | **990.200** |
| Texturas | ninguna | basecolor + normal + roughness |
| Material | hubo que asignar piedra | el suyo propio |

### La orientacion, medida y no a ojo

**El modelo mira a +Y cuando su yaw es 0.** Se determino colocandolo a yaw 0 y capturando
desde el sur (se ve la espalda y las alas) y desde el oeste (se ve de perfil mirando a +Y).

Para que mire al jugador que llega por el sendero: el spawn del Jardin esta a **yaw -176.57**
desde la estatua, y hay que restarle el desfase de 90 grados del modelo →
**yaw aplicado 93.43**. Ahora encara el sendero de frente, con las dos alas simetricas
detras, que es la lectura de `lam_01`.

Escala 19143.2 desde una malla de 0.98 cm, para los mismos **18750 cm** de la esfinge.

### Limpieza y ajustes

- **`Coloso_Angel` (el V1 de 7.795 triangulos) borrado**, ya no hacia falta.
- `SM_Coloso_Landmark`, la esfinge original, sigue **oculta y no borrada**.
- `MaxTextureSize`: 2048 en basecolor y normal, 1024 en roughness. Es un landmark de 187 m y
  admite mas que un NPC, pero 4K por mapa con la VRAM ya 1.8 GB pasada no se justifica.
- El roughness entro con **`SRGB=true`**, que esta mal para un mapa de datos: corregido a
  `SRGB=false` y `TC_Masks`. **Conviene revisarlo en cada importacion**: el importador no
  acierta solo.
- Metallic no se importo, y para una estatua de piedra eso es lo correcto: queda en 0.

## La hueste de El Claro: los cinco enemigos importados (2026-08-14)

### AccuRig o `tripo_convert`: NO son lo mismo

Primero se importaron los FBX que venian dentro de los `.zip` de cada carpeta
(`tripo_convert_*.fbx`, ~1.8 MB). Entraron sin error y con sus texturas, **pero traen 1 solo
hueso**: son mallas, no personajes. No se pueden animar.

Los buenos estan en **`<enemigo>/AccuRig/<enemigo>.fbx`** (42-47 MB) y traen los **118
huesos** del rig, el mismo que Sariel y Cassiel. Se borro la carpeta de assets entera y se
reimporto desde ahi.

**Como distinguirlos sin abrir nada:** por el peso. El export riggeado ronda los 45 MB; el
`tripo_convert` no llega a 2 MB. Y una vez dentro, `get_bone_names` lo confirma: 118 contra 1.

| | Vertices | Huesos | Altura | Escala a 1.80 |
|---|---|---|---|---|
| Vigilante | 46.461 | 118 | 98.5 cm | 1.8273 |
| Lancero | 55.493 | 118 | 98.4 cm | 1.8289 |
| Arquero | 45.774 | 118 | 98.4 cm | 1.8287 |
| Heraldo | 47.195 | 118 | 98.2 cm | 1.8337 |
| Inspector | 47.748 | 118 | 98.3 cm | 1.8318 |

En `/Game/DarkAngels/Characters/Enemigos`, cada uno con esqueleto, physics asset, material y
sus texturas Diffuse y Normal. `MaxTextureSize` a 1024 en las dos.

### Reparto: el PDF lo dice y los marcadores ya estaban

La estacion 04 dice literalmente *"Dos Vigilantes, un Lancero y un Arquero"*, y en el Claro
habia **exactamente esos cuatro marcadores**, cada uno con su luz `*_Glow`:

| Marcador | Modelo | Posicion | Cota |
|---|---|---|---|
| `Claro_Angel_Vigilante1` | Vigilante | 43300, -11400 | -42 |
| `Claro_Angel_Vigilante2` | Vigilante | 44200, -11100 | -42 |
| `Claro_Angel_Lancero` | Lancero | 44900, -11700 | -42 |
| `Claro_Angel_Arquero` | Arquero | 45350, -12450 | **420** |

El arquero estaba ya **elevado sobre un bloque**, igual que en la lamina `lam_05`. Los cuatro
orientados hacia la camara del jugador y en la carpeta `Hueste`. Marcadores **ocultos, no
borrados**; las luces se mantienen.

### Heraldo e Inspector: no se colocan, y hay motivo

- **Inspector**: el LDD lo describe como spawn **condicional**, no fijo — *"If Farsa < 20%,
  a 5th angel spawns as 'Inspector'"*, y en la tabla de Farsa *"20-39%: Angels attack on
  sight. Inspectors spawn."* Plantarlo en el mundo contradiria su diseño. Queda importado y
  listo para el sistema de spawn.
- **Heraldo**: el Art Bible lo reconoce como variante (*"Variantes: Vigilante, Heraldo,
  Lancero, Arquero e Inspector"*) pero **ningun documento le asigna sitio**. No se inventa
  una posicion: queda importado, esperando decision.
  **Angel lo confirmo el 14/08: de momento NO se coloca, se hara mas adelante.** O sea que
  si aparece sin colocar no es un olvido, es una decision.

El boss queda fuera a proposito, que ese modelo aun no existe.

## Los enemigos, dentro del sistema DCS (2026-08-14)

**Si se puede, y por la via facil.** La documentacion de ue4dcs.com carga por JavaScript y
solo devuelve el indice, asi que lo util salio del propio proyecto.

### Como esta montado DCS aqui

    BP_WarriorAI  ->  BP_BaseAI  ->  Character      (enemigos, con su BT_WarriorAI)
    BP_CombatCharacter  ->  Character               (el jugador)

Componentes en `DCS/Blueprints/Components`: Ability, CollisionHandler, Combat, Dissolve,
InputBuffer, Inventory, MontageManager, MovementSpeed, Rotating, StateManager, StatsManager,
StatusEffects, TeamRelations, mas targeting y patrol. Todo eso lo hereda el Warrior.

### El hallazgo: AccuRig usa la nomenclatura de UE

Los huesos de AccuRig son `root`, `pelvis`, `spine_01..05`, `clavicle_l`, `upperarm_l`,
`hand_r`... **los mismos nombres que el `SK_Mannequin` de DCS**, mas 47 huesos auxiliares
`cc_base_*`.

Por eso `SkeletalMeshTools.import_file` acepta el parametro **`skeleton`** apuntando al de
DCS y la malla queda atada a el. Verificado comparando la ruta del esqueleto, no a ojo:
los cinco devuelven `SK_Mannequin.SK_Mannequin`.

**Consecuencia: las animaciones y montages de DCS funcionan directamente, sin IK Retargeter.**

### ⚠️ Esto modifica un asset de pago que NO esta en git

Atar las mallas a `SK_Mannequin` **le añade los 47 huesos `cc_base_*`**: el fichero paso de
148.518 a 191.521 bytes. Es un cambio **aditivo** —las animaciones y mallas existentes de DCS
no usan esos huesos y siguen igual— pero:

- `Content/DynamicCombatSystem/` esta en `.gitignore` por licencia, asi que **este cambio no
  viaja en el repo**.
- Si se reinstala o actualiza DCS, el esqueleto vuelve a su estado original y **las cinco
  mallas se quedan sin esqueleto valido**. La reparacion es reimportar los cinco FBX de
  AccuRig pasando de nuevo `skeleton = SK_Mannequin`: dos minutos con `importar_dcs.ps1`.

Decidido con Angel el 14/08 sabiendo esto. La alternativa era un IK Rig + IK Retargeter por
enemigo, que el MCP no puede crear y habria que montar a mano.

### Lo que quedo hecho

`/Game/DarkAngels/Blueprints/Enemies/`: **BP_DA_Vigilante, BP_DA_Lancero, BP_DA_Arquero,
BP_DA_Heraldo y BP_DA_Inspector**, duplicados de `BP_WarriorAI`, o sea que heredan su
Behaviour Tree, su AI Controller y todos los componentes de combate.

**La escala va en la malla, no en el actor.** El Warrior original tiene capsula de 96 de
semialtura y la malla a Z −97 con escala 1. Nuestras mallas miden 98.4 cm, asi que se les
puso **RelativeScale3D ~1.83 al componente CharacterMesh0** y se dejo la capsula intacta:
asi el personaje mide 1.80 m dentro de la capsula estandar y ni el movimiento ni la
colision se deforman. Escalar el actor entero habria escalado tambien la capsula.

Colocados en El Claro sustituyendo a los `SkeletalMeshActor` estaticos, sobre las mismas
poses. **Ojo con la cota**: el origen de un Character es el **centro de la capsula**, no los
pies, asi que la Z del actor es la de los pies **+96**.

## La puerta de El Claro (2026-08-15)

Sustituye a `Claro_Puerta_Ruta` (una `SM_MedievalModularDoor3x2M` escalada 2.6). La vieja
queda **oculta, no borrada**. Nueva: `Claro_Puerta_Bronce`, en la carpeta `Puerta`.

Escala 531.9 desde una malla de 0.98 cm, para los mismos **521 cm de alto** que tenia el
hueco. Sale **388 cm de ancho** frente a los 781 de la anterior, porque es una puerta con
jambas en vez de un panel modular ancho.

### Otra vez: 52 MB de FBX no entran como StaticMesh

`StaticMeshTools.import_file` **si** devolvio un asset, pero con **84 triangulos**. La
version skeletal del mismo fichero da **1.009.712 vertices**. O sea que aqui el importador
estatico no falla ruidosamente como con el coloso: **devuelve algo, y es basura**.

**Regla: tras importar un FBX pesado como StaticMesh, comprobar el numero de triangulos.**
Si son decenas en vez de cientos de miles, reimportar como SkeletalMesh.

### El fallo que me costo cuatro intentos: el material no compilaba

La puerta salia **negra** (luma 3.5). Diagnostico correcto —metal liso sin nada que
reflejar en un hueco a oscuras— pero **los arreglos no surtian efecto**, y tarde en ver por
que. El error real solo aparecio al leer la salida completa en vez del traceback recortado:

    Material failed to compile:
    (Node TextureSample) Sampler type is Color, should be Masks for clarodoor_roughness

Al pasar la textura a `TC_Masks` hay que cambiar **tambien el `SamplerType` del nodo**. Y no
bastaba con el nodo que yo añadi: habia **un segundo TextureSample original**
(`MaterialExpressionTextureSample_1`) usando la misma textura en modo Color, y era el que
alimentaba `MP_Metallic`. Mientras uno solo estuviera mal, **el material no compilaba y
ningun cambio se veia**.

**Leccion doble:**
1. `recompile` fallando deja el material con el shader viejo: los cambios parecen no hacer
   nada. Si un cambio de material "no se nota", **mirar si compilo**.
2. Al cambiar una textura a `TC_Masks`, revisar **todos** los nodos que la usan, no solo el
   que acabas de tocar.

### Estado final, medido en la misma region

| | luma | saturacion |
|---|---|---|
| Al colocarla (negra) | 3.5 | 53% (ruido) |
| Con las luces subidas | 52.6 | 0.3% |
| Con el material ya compilado | **64.9** | **48.5%** |

Cambios aplicados: `MP_Roughness` conectado (venia suelto), metallic atenuado a **0.15**
—el basecolor es marron terroso, no bronce brillante, y con metallic alto se iba a gris—,
texturas a 2048 el color y la normal y 1024 la rugosidad.

**Y las luces de la puerta:** `Claro_GateLight_L` y `_R` estaban a **8 candelas**, que no
iluminan nada. Subidas a **220** con radio 1200. Ese cambio por si solo saco la puerta del
negro.

**Pendiente:** las dos luces salen con una X roja en el editor. Son Stationary y se les
cambio la intensidad, asi que **piden rebuild de iluminacion**.

### La puerta, agrandada (2026-08-15)

Se escalo **por ancho** en vez de por alto, para que llene el hueco: factor **1070.2** desde
el ancho de malla, o sea **780 x 1048 cm** (antes 388 x 521). Base sin mover en z=230, cima
en 1278. Sobresale del hueco original y Angel lo dio por bueno.

Ahora se lee lo que es: portal con jambas talladas, dintel decorado, batientes con discos y
**dos figuras de angel flanqueandolo** — justo la hornacina con estatuilla que pide `lam_05`.
Desde la entrada del jugador remata el fondo de la plaza y ordena el encuadre:
sendero → hueste → puerta.

**Se repitio el Error Code 32 al guardar `L_DA_Malkuth_Claro_Sub.umap`**, con su dialogo
modal colgando el editor, igual que con el Santuario el 14/08. Reiniciar el editor volvio a
arreglarlo. El primer intento de escalado **se perdio** con la sesion de edicion descartada;
confirmado al reaplicarlo, que partia de 388 x 521.

**Patron a vigilar:** las dos veces que ha pasado ha sido poco despues de commitear esos
`.umap` a git. No esta demostrado —el 14/08 se descarto que fuera Unreal reteniendo los
paquetes— pero si vuelve a ocurrir, conviene probar a no commitear hasta cerrar la tanda de
ediciones y ver si desaparece.

### Vegetacion y ruinas con musgo en El Claro (2026-08-15)

La plaza mide **46 x 46 m** (x 41700..46300, y -14300..-9700), centro en (44000, -12000).
Colocados **11 bloques de ruina y 35 plantas** en anillo perimetral; 18 posiciones se
descartaron solas por caer en zona prohibida o no encontrar suelo.

**Es una arena de combate, asi que el reparto respeta tres exclusiones**, no se siembra a
voleo:

- **Circulo central de 15 m libre**, que es donde se pelea.
- **Corredor a la puerta**: nada con `y > -10400` a menos de 9 m del eje x=44245.
- **Entrada del jugador**: nada con `y < -13300` a menos de 8 m del eje x=44000.

Assets usados: `SM_MossyStoneWallA` y `_B`, `SM_IcelandicMossyRock`, `SM_MossyRocksA`,
`SM_MRK_RubbleCluster_A` y `_B` para la ruina; `SM_DA_Fern_02`, `SM_DA_Grass_Medium` y
`SM_DA_Flower_White` para el verde. Carpetas `Vestido/Ruinas` y `Vestido/Vegetacion`.

**El reparto es reproducible a proposito**: la variacion de posicion, giro y escala sale de
una funcion `pseudo(i, k)` deterministica, no de `random`. Volver a lanzar el script da el
mismo resultado, y se puede ajustar el radio o la cuenta sin que se descoloque todo.

**Lectura honesta:** los bloques con musgo funcionan muy bien y son lo que mas se parece a
`lam_05`. **La vegetacion sigue siendo escasa** frente a la lamina, que tiene sotobosque
denso; 35 plantas en 46 x 46 m se notan poco. Subir la cuenta es cambiar una constante, pero
conviene no invadir la arena.

### Segunda pasada de verde: 98 plantas mas (2026-08-15)

Total en El Claro: **133 plantas y 11 bloques de ruina**. Esta vez no en anillo uniforme sino
**agrupadas donde crecerian de verdad**:

- **5 matas al pie de cada bloque de ruina**, con radio en funcion del tamaño del bloque.
  Los 11 bloques colocados antes sirven de ancla; el script los localiza por nombre.
- **56 en banda contra los acantilados**, a radio 2150-2750 del centro de la plaza.

Se descartaron 13 posiciones por las mismas exclusiones de siempre (circulo de combate,
corredor a la puerta, entrada del jugador). El reparto sigue siendo determinista.

**CORRECCION, medido despues:** escribi aqui que "agrupar cambia mas que subir la cuenta".
**Es falso, o al menos no se sostiene con numeros.** Comparando las mismas regiones antes y
despues de meter las 98 plantas:

| Region | saturacion antes | despues |
|---|---|---|
| Borde derecho | 65.1% | 66.8% |
| Borde izquierdo | 53.2% | 55.0% |
| Centro de la arena | 49.0% | 50.7% |

**Menos de 2 puntos.** Duplicar largamente la cuenta de plantas no cambia la lectura.

**La razon, y la conclusion util:** 133 plantas de 1-2 m repartidas en 46 x 46 m son **una
planta por cada 16 m2**. A 30 m de distancia eso no tapiza nada, se agrupe como se agrupe.
Para acercarse a la lamina hacen falta **cientos o miles** de matas pequeñas, y eso es lo que
existe el **foliage instanciado** (Foliage / HISM). Como actores sueltos ni rinde ni se ve.

**Los actores sueltos sirven para los props que se leen de uno en uno** —los bloques de
ruina con musgo, que si funcionaron— **no para tapizar**.

## ~~PROXIMA SESION~~ — EL TELON 360 ESTA TERMINADO (cerrado 2026-08-15 15:50)

### Lo que quedo a medias: el panorama 360 como telon

**Objetivo:** sustituir los **196 montes de telon** (84 `Monte_Lejos`, 78 `Monte_Medio`,
34 `Gazebo_Monte`) por una imagen equirectangular en la cupula, para acercarse a las laminas
y de paso aliviar la VRAM, que va **1787 MB por encima**.

**Hecho y guardado:**

- Imagen analizada y **corregida**: `backdrops/Malkuth_Paisaje_360_8192x4096.png` era 8192 x
  4096 y 2:1 correctos, pero **la costura no casaba** (diferencia 12,9 contra 0,6 de dos
  columnas vecinas normales). Cosida con `scratchpad/coser_panorama.mjs` en una banda de
  96 px: **12,95 → 0,00**. El fichero bueno es `Malkuth_Paisaje_360_8K_cosido.png`.
- Importada como `T_DA_Malkuth_Panorama360`, `MaxTextureSize` 8192, sRGB.
- Creado `M_DA_Panorama360`: **Unlit y TwoSided**, con la textura al emisivo.
- Asignado al `SkyDomeMesh` del **Master** (o sea, valido para las 13 zonas de golpe).
- La cupula venia **aplastada** (escala 1000000 x **150000** x 1000000) porque el material
  procedural del Engine lo aprovecha. **Un equirectangular necesita esfera**: puesta a
  1000000 uniforme.
- Girada a **yaw -70**, que es la diferencia entre el punto mas brillante del panorama
  (azimut 220 dentro de la imagen) y nuestro sol (yaw 150).

**Lo que falta, y es el paso grande:**

1. **Ocultar los 196 montes.** Ahora tapan el panorama: desde el Jardin solo asoman nubes y
   un pico. Hacerlo por tandas y **verificando zona por zona**, porque algunos montes cierran
   agujeros del horizonte y al quitarlos puede abrirse un hueco. Ocultar, no borrar.
2. **Revisar la cota del horizonte.** El perfil de la imagen situa el horizonte al 45-50% de
   altura, pero la cupula puede necesitar un desplazamiento en Z para que la linea del
   panorama case con la del terreno.
3. **Comprobar las 13 zonas.** Es una sola cupula para todas; lo que mejore el Jardin puede
   estropear el Anfiteatro o el Puente.

### Estado de Malkuth al cerrar

- **Jardin**: coloso de angel encarando el sendero, esfinge borrada.
- **Mirador**: Sariel sobre la base, `PP_Mirador` propio a -1.9 EV, luces bajadas.
- **Santuario**: Cassiel junto al altar, sobre el sitio de su marcador.
- **El Claro**: suelo de tierra marron, hueste de 4 angeles **sobre DCS**, puerta monumental
  de 780 x 1048, 11 bloques de ruina con musgo y 133 plantas.
- **Anfiteatro**: telon cerrado, sin rendijas.

### Pendientes por orden de valor

1. Terminar el telon 360 (arriba).
2. **Auditar la VRAM**: 1787 MB de exceso. Lo de personaje ya esta acotado; el grueso son
   Megascans, los escaneos y las texturas de superficie a 4K.
3. **Foliage instanciado** en El Claro. Medido: 98 actores de planta mas movieron **menos de
   2 puntos** de saturacion. Los actores sueltos no tapizan, hacen falta miles de instancias.
4. **El Heraldo sin colocar**, por decision de Angel.
5. **Comportamientos de combate**: los cinco enemigos heredan el Behaviour Tree del Warrior
   tal cual. Diferenciar que el Arquero mantenga distancia y el Lancero cargue ya es diseño.
6. Assets que faltan segun el PDF: **tableta grabada y Fragmento** del Gazebo, **llave y
   baul** del Mirador, **angel guardian** del portal de Yesod, props del Santuario.

### Dos cosas operativas

- **El guardado de sublevel falla con Error Code 32** cada cierto tiempo, dejando un dialogo
  modal que cuelga el MCP. Se arregla **reiniciando el editor** (y `ModelContextProtocol.StartServer`
  despues). Ha pasado dos veces, las dos poco despues de commitear esos `.umap` a git; sin
  demostrar, pero vigilarlo.
- **Sin push todavia.** El repo es publico y llevamos ~17 commits sin subir.

---

## El telon 360, terminado (2026-08-15)

### La cupula estaba 8,4 grados por debajo de donde debia

Lo de "desde el Jardin solo asoman nubes" **no era culpa de los montes**, o no solo. El
`SkyDomeMesh` es `/Engine/BasicShapes/Sphere` —radio 50 a escala 1, o sea **500 km** con la
escala de 1000000— y venia en `z = -7.300.000`, que es el valor por defecto del template.

Eso deja al jugador **0,146 radios por encima del centro de la esfera**. Mirando al frente
se golpea la esfera a `asin(7,3/50) =` **8,4 grados de latitud**, asi que toda la imagen
aparecia **8,4 grados por debajo** de donde le tocaba: el paisaje se hundia bajo el horizonte
y en pantalla solo quedaba cielo.

**Arreglo: cupula a `z = 0`.** Con el centro a cota de ojo, latitud de la imagen y elevacion
de la vista coinciden. La diferencia entre z=0 y la cota real de los ojos (~160) es
0,0002 grados sobre un radio de 50 km: da igual.

Medido, no supuesto. Con la cupula centrada en la camara, en cuatro azimuts:

| Azimut | Franja izquierda | Franja centro |
|---|---|---|
| yaw 0 | 10,3 deg | 8,7 deg |
| yaw 270 | 19,9 deg | 4,4 deg / -2,1 deg |

Son la **linea de cumbres**, no el horizonte: en un paisaje de montaña el corte cielo/tierra
esta por encima del horizonte real, tanto como midan los picos. El minimo (**-2,1**) es lo
mas parecido al horizonte verdadero, o sea que con la cupula en z=0 la imagen cae **a menos
de 3 grados** de su sitio. Con `z = -7.300.000` estaba a 10.

**Como se midio, que sirve para la proxima vez:** dos capturas desde el mismo punto a
`pitch 0` y `pitch 10`. La linea del horizonte se movio de `y=457,5` a `y=560,5`, y de ahi
salen las dos constantes del encuadre: **centro optico `y=457,5`** (no es el centro del PNG,
porque la captura lleva margen gris) y **focal `f = 584 px`**. Con eso,
`elevacion = atan((457,5 - y) / 584) + pitch`. Hay un decodificador de PNG sin dependencias
en el scratchpad para sacar perfiles de luma por fila; `CaptureViewport` tambien devuelve
`cameraFOV` en la respuesta, que es mas directo.

### La nube volumetrica peleaba contra el panorama

Habia una **banda horizontal dura** cruzando todas las capturas a la altura del ojo, con
grumos blancos pegados encima de las montañas pintadas. No era la costura de la esfera:
**no se movia al mover la cupula**, porque es el actor `VolumetricCloud` del Master visto
casi de canto.

Con un panorama que ya trae sus nubes pintadas, la capa volumetrica sobra. **Apagada**
(`bVisible = false` en su `VolumetricCloudComponent`). Es un cambio de direccion de arte,
no tecnico: si Angel la quiere de vuelta es volver a poner la propiedad.

### Los montes eran 236, no 196

Al contarlos aparecieron **40 mas** de los que decian las notas:

| Zona | Level Instance | Montes | `.umap` guardado |
|---|---|---|---|
| Jardin | `LI_01_JardinGeometrico` | 50 | 15:37:59 |
| El Claro | `LI_04_ElClaro` | 56 | 15:40:03 |
| Mirador | `LI_03_MiradorSariel` | **30** | 15:40:49 |
| Gazebo | `LI_05_RuinasGazebo` | 34 | 15:41:43 |
| Puente | `LI_07_PuenteAscendente` | 56 | 15:43:04 |
| Yesod | `LI_13_PortalYesod` | **10** | 15:43:31 |
| | | **236** | |

Los que faltaban en el recuento son `Mirador_Monte` (30) y `Yesod_Monte` (10): no se llaman
`Monte_Lejos` ni `Monte_Medio`, y por eso se habian escapado.

**Ocultados, no borrados**: `bVisible = false` en el `StaticMeshComponent`. Se guarda en el
`.umap`, vale en editor y en juego, y volver atras es un booleano. La receta esta en
`Tools/MCP/montes_ocultar.py` (editar las dos constantes de arriba).

**Un solo ciclo `edit`/`commit` por Level Instance**, que es lo que dice la nota del 14/08:
encadenar varios sobre el mismo LI filtra un handle del `.umap` y el guardado falla para
siempre hasta reiniciar. Los seis commits se verificaron **por fecha en disco**, no por lo
que devolvia `commit_level_instance`.

**Lo que NO se toco: la colision.** Los 236 montes siguen colisionando, invisibles. Es
deliberado —asi el juego se comporta exactamente igual que antes y nadie se cae del mapa por
un muro que ya no se ve— pero hay que saberlo: **cualquier sonda de trazas sigue chocando
con ellos**, asi que los `probe_*.py` que miden techo de horizonte ya no dicen lo que se ve.

### Repaso zona por zona, con el visor en Lit

Sin agujeros en ninguna. Y no puede haberlos: la cupula es una esfera **completa**, tambien
cubre por debajo del horizonte, asi que donde antes un monte tapaba el vacio ahora hay
paisaje pintado.

| Zona | Como queda |
|---|---|
| Jardin | Lo que mas cambia. Cordillera enorme detras del seto, a la cota justa |
| Yesod | El mejor. A 130 m de altura, el valle pintado se lee como caida real |
| Anfiteatro | Picos asomando sobre las paredes de roca; no tenia montes, gana solo con la cota |
| Mirador | Panorama por el hueco entre acantilados |
| Gazebo | Se acabo la tapa: donde habia 34 montes ahora hay cordillera y cielo |
| El Claro | Encajonado, solo asoma cielo arriba. **Sus 56 montes no se veian desde dentro** |
| Santuario / Puente | Panorama por los huecos del dosel y a los lados del puente |

**Lectura honesta:** en el Jardin la transicion **es brusca**. El cesped acaba y empieza la
montaña pintada, sin nada en medio: falta plano intermedio. Ahora que ocultar y mostrar es
un booleano, la prueba barata es **volver a encender media docena de montes** —los mas bajos
y cercanos— como siluetas de termino medio, en vez de los 236.

### El modo de vista del viewport se volvio a torcer

Paso otra vez lo del 14/08: a mitad de sesion las capturas salieron sin color. Esta vez con
numero: **misma camara del Jardin, saturacion media 50,7% antes y 0,2% despues**. Y esta vez
con una correlacion util: **se torcio durante la tanda de seis ciclos `edit`/`commit` de
Level Instance**, entre la captura del Jardin y la del Claro.

Sigue sin poder arreglarse por MCP —no hay herramienta para ejecutar comandos de consola ni
para poner `ShowFlag.*`, solo `SearchCVars` que lee— asi que **hay que pedirle a Angel que
lo devuelva a `View Mode > Lit`**. Las trazas y las medidas numericas no se enteran; las
capturas si.

## Plano intermedio del Jardin y el coloso negro (2026-08-15, misma tarde)

### Los montes bajos no valian: hubo que subir un escalon

Primera eleccion, midiendo desde `PS_Master_Jardin`: seis `Monte_Medio` de cima **0,8-1,7
grados** de elevacion, a 736-914 m, repartidos de -46 a +52 de azimut. Encendidos y
commiteados.

**No se veian.** Comparando la franja del horizonte con la captura de antes: **2,5 puntos de
luma de diferencia y el 3% de los pixeles**. A esa altura los tapa la propia linea de arboles
del Jardin.

Los montes del Jardin no se reparten de forma continua: hay un grupo bajo (0,6-1,7) y otro
alto (4,7-8,8), sin nada en medio. Asi que la segunda eleccion son **seis del grupo alto**:
`Monte_Medio_45, _40, _39, _63, _60, _43`, de 4,7 a 6,8 grados y a 847-1061 m. Siguen muy por
debajo de las cumbres pintadas, que llegan a 20-30 grados, asi que hacen de silueta
intermedia sin volver a cerrar el horizonte. **Se evita el azimut 0-10**, que es donde esta
el coloso (az 3,4). Receta en `Tools/MCP/jardin_planointermedio.py`.

### El coloso negro eran DOS fallos, y el gordo no era el material

**Fallo 1, el material.** `tripo_mat_1504baa6` tenia el **mapa de rugosidad cableado a
`Metallic`**, y `Roughness` sin conectar. Ademas el nodo declaraba `SamplerType` **Color**
sobre una textura `TC_Masks` / `SRGB=false`: con esa discrepancia **el material no compilaba**
—su miniatura salia como una bola gris lisa, que es el material por defecto—. Arreglado:
sampler a `Masks`, `Metallic` suelto (0, que es lo que toca en una estatua de piedra) y la
rugosidad al canal **R** de `MP_Roughness`. La miniatura pasa a mostrar la piedra arenisca.

**Eso mejoro el detalle pero NO el negro.** De cerca ya se distinguian alas y drapeado; desde
el arranque del jugador seguia siendo una mancha (luma 18,6 -> 17,5, o sea nada).

**Fallo 2, y este era el bueno: no le llegaba ninguna luz direccional.** La cadena de
descartes, toda con numeros:

| Prueba | Resultado | Conclusion |
|---|---|---|
| Relleno direccional en canal 1 | coloso 17,5 | nada |
| El mismo relleno abierto al canal 0 | cesped 66 -> 73, **coloso igual** | la luz funciona, al coloso no le llega |
| Relleno a intensidad 20 | cesped 66 -> 106, **coloso 17,5 -> 7,9** | se oscurece: es la auto-exposicion. Recibe **cero** |
| Quitar el normal map | sin cambio | no son las tangentes |
| Forzar la normal a (0,0,-1) | sin cambio | no son las normales invertidas |
| **Foco puntual pegado al pecho** | **coloso 7,6 -> 97,6** | la malla y el material estan perfectos |
| Relleno direccional con `CastShadows = false` | coloso 18,6 -> 37,4; cara 1,2 -> 75,8 | parecia resuelto... |
| Lo mismo, tras recargarse el Level Instance | **cara de vuelta a 1,3** | ...pero **no aguanto** |
| Esa direccional a intensidad 30 | cara 1,3 | cero |
| Esa direccional abierta al canal 0, intensidad 30 | cesped 58 -> 130, **coloso 16,2 -> 7,4** | recibe cero, solo se mueve la exposicion |
| **Foco puntual otra vez, ya en canal 1** | **coloso 17,7 -> 237; cara 1,3 -> 255** | los puntuales SI llegan |

**Correccion de lo que se escribio primero:** el arreglo con `CastShadows = false` sobre una
direccional **no se sostuvo**. Funciono en una tanda de capturas y dejo de funcionar tras el
siguiente `commit_level_instance`, con el coloso volviendo a cara 1,3. Ya no se reproduce a
ninguna intensidad ni con el canal 0 abierto.

**Lo cierto, y verificado varias veces: a este actor NO le llega ninguna luz direccional, y
los puntuales le llegan perfectamente.** No se ha averiguado por que. La pista es la
distancia: esta a 266 m de la camara, mas alla de la distancia de sombra dinamica por
defecto.

**Lo que queda puesto:** `Luz_Relleno_Coloso`, un **PointLight** en el **Master**, `Movable`,
en `(-45000, -59500, 11000)` —unos 120 m por delante y por encima del coloso—, intensidad
**30000**, radio de atenuacion **60000**, `CastShadows = false`, 6500 K,
**`VolumetricScatteringIntensity = 0`** y **canal de iluminacion 1 solamente**. El unico
actor con canal 1 es el coloso, asi que el resto del Jardin no se entera. Resultado:
**cara 1,3 -> 80,2**, coloso entero 17,7 -> 49,4, y se lee la piedra, el drapeado y las manos.

Lo de `VolumetricScatteringIntensity = 0` no es capricho: **los canales de iluminacion NO
filtran la niebla volumetrica**. Una luz de relleno «solo para un actor» le mete luz a la
niebla de todo el nivel si no se le corta eso. Por lo mismo se **borro** la direccional de
relleno en vez de dejarla apagada.

**Calibrado de la intensidad** (la auto-exposicion enmascara, hay que ir por la cara):
8000000 -> 254 (reventada), 500000 -> 235, 60000 -> 136, **30000 -> 80**.

**Nacio `Stationary`.** `add_to_scene_from_class` crea las luces en Stationary y aqui no hay
iluminacion horneada: hasta ponerla en `Movable` no hace absolutamente nada.

### El visor del editor tiene `Show > Fog` APAGADO

Angel paso una captura de PIE y **el juego va cargado de niebla**: el coloso apenas se
adivina y el panorama sale lavado. En las capturas del editor no hay ni rastro de niebla, con
la misma camara.

**Consecuencia incomoda: todo lo que se ha juzgado a ojo en esta sesion —el telon 360
incluido— se juzgo SIN niebla.** Hay que repasarlo con niebla antes de darlo por bueno.

Valores actuales de `Fog_Malkuth`, para tenerlos a mano: `FogDensity` 0,006,
`FogHeightFalloff` 0,35, **`FogMaxOpacity` 0,45**, `StartDistance` 0, niebla volumetrica
**activada** con `VolumetricFogDistance` 22000 (220 m) y `VolumetricFogExtinctionScale` 0,35.
El actor esta a z=20000. El coloso, a 266 m, queda justo detras de los 220 m de niebla
volumetrica.

### Los seis montes del plano intermedio se ven poco

Medido ya en color, comparando con la captura sin ellos, en la franja del horizonte:

| Franja | delta de luma | pixeles cambiados |
|---|---|---|
| az -46..-25 | **9,0** | **9,5%** |
| az -25..-5 | 2,6 | 1,8% |
| az 25..45 | 2,9 | 3,3% |
| az 45..62 | 1,9 | 2,2% |

O sea: **solo se notan en el borde izquierdo**. Estan encendidos y verificados en el mundo
(`Monte_Medio_39, _40, _43, _45, _60, _63`), pero como plano intermedio aportan poco. Si se
quiere que la union cesped-panorama deje de ser un corte seco, el camino no es este: o son
mas montes, o es algo a media distancia de verdad (arboleda, ruina, un talud).

### Y el visor se volvio a torcer, ya con la causa clara

Tercera vez, y esta sin margen de duda: capturas a **56,1%** de saturacion, **un solo** ciclo
`edit_level_instance` / `commit_level_instance` sobre `LI_01_JardinGeometrico`, y la
siguiente captura a **0,2%**. No hace falta una tanda larga, con uno basta.

Practica que se deduce: **capturar antes de tocar un Level Instance**, y no encadenar
«edito, miro, edito, miro», porque cada edicion cuesta pedirle a Angel que devuelva el visor
a `View Mode > Lit`.

## Llave y baul reales, y la receta fija de Tripo (2026-08-15, noche)

Primeros dos de la lista de props de objetivo. Los zip de Tripo estan en
`D:\Game Projects\Dark Angels\World Assets\Malkuth\{llave,tesoro}\`, descomprimidos en
`ArtSource/Downloaded/Tripo/`.

### Lo importante: el importador de Tripo saca SIEMPRE los mismos tres fallos

Angel aviso de que estos traen el mismo esqueleto que la puerta del Claro. Confirmado, y hay
mas: **el material sale mal exactamente igual las tres veces** (puerta, coloso, y ahora llave
y baul). No es mala suerte, es lo que hace el importador. Para los que vengan:

1. **Cablea el mapa de RUGOSIDAD a `Metallic`** y deja `Roughness` sin conectar.
2. **Declara `SamplerType = Color`** en ese mapa de datos **y** deja la textura en sRGB /
   `TC_Default`. Hay que corregir **las dos cosas**: si solo se toca el nodo, el material no
   compila y salta `Sampler type is Masks, should be Color`.
3. **No importa el mapa metallic**, aunque venga dentro del `.fbm`. Hay que importarlo a mano.

**Como se detecta de un vistazo:** con el material sin compilar, la **miniatura del material
sale como una bola gris lisa**, que es el material por defecto. Si se ve la textura, compila.

**El patron bueno es el de la puerta del Claro** (`tripo_mat_f7da7eff`): basecolor -> BaseColor,
rugosidad por el **canal R** -> Roughness, y metallic -> **Multiply** -> Metallic. La
atenuacion del Multiply hace falta porque el mapa de Tripo declara casi todo como metal.
Valores usados: **0,5 en la llave** (es bronce de verdad) y **0,25 en el baul** (piedra clara
con herrajes).

Todo esto esta automatizado y es idempotente en `Tools/MCP/tripo_arreglar_material.py`:
se cambian las constantes de arriba y se lanza.

### Los dos assets

| | Llave | Baul |
|---|---|---|
| Asset | `SK_DA_Llave_Mirador` | `SK_DA_Baul` |
| Vertices | 33.357 | 48.009 |
| Huesos | 1 (`tripo_node_f84cc187`) | 1 (`tripo_node_f26e5120`) |
| Malla cruda | 0,34 x 0,12 x **0,98** uu | **0,98** x 0,68 x 0,72 uu |
| Escala puesta | 71 | 92 |
| Tamano final | 23 x 23 x 70 cm | 90 x 63 x 66 cm |

**Dos cosas practicas de estas mallas:**

- **El pivote viene en la base** (`base_local_z = 0`), asi que la z de destino es directamente
  la cota del suelo y **la escala es el tamano en centimetros**. Muy comodo.
- **Miden ~1 uu**, no ~98 como los personajes. La miniatura del asset **no sirve** para
  revisarlas: salen como una mota en medio del damero. Hay que colocarlas y capturar.

Texturas acotadas a `MaxTextureSize` **1024**: son props, y la VRAM sigue muy pasada.

### Sustituciones hechas

Habia placeholders con sitio y luz ya montados, asi que se reutilizo su transform:

| Placeholder borrado | Malla que tenia | Sustituido por | Donde |
|---|---|---|---|
| `Mirador_Llave` | `/Game/Fab/old-rusty-key/source/OldKey` | `SK_DA_Llave_Mirador` | (-16000, -23300), yaw 45 |
| `Mirador_Cofre` | `SM_OldWoodenChest` (Megascans) | `SK_DA_Baul` | (-15580, -22880, 317,5), yaw -155 |
| `SM_Cofre` | `SM_OldWoodenChest` (Megascans) | `SK_DA_Baul` -> `Santuario_Cofre` | (43880, 48620, 5,6), yaw -30 |

**La escala NO copia la del placeholder, a proposito.** El arcon de Megascans es ancho y bajo
(112 x 52 x 37 en local) y este es casi cubico: copiar proporciones lo habria deformado. Se
eligieron medidas de mundo real y el numero esta a mano en `Tools/MCP/colocar_props.py`.

**La llave flotaba, y ya lo hacia antes.** Sondeado con trazas: la cara del plinto esta en
**z=408**, el escalon de ±60 en 338 y el suelo del mirador en 318. El placeholder empezaba en
439,8, o sea **32 uu en el aire**. Angel decidio apoyarla: **base a 408**, cima a 477,6, con el
foco `Mirador_Luz_Llave` a 520, o sea 42 uu por encima de la cima. Verificado tras recargar el
Level Instance.

El cofre del Santuario si apoya bien; la traza vertical de su centro da 65,7 porque pega en el
monticulo de roca de delante, no en el suelo bajo el cofre.

### Dos cosas que salieron al mirarlo, y que son decision de Angel

- **El cofre del Santuario esta metido en una grieta entre dos rocas.** Desde cenit se ve
  perfecto; desde la altura del jugador, viniendo del altar, **no se ve nada**: lo tapan los
  bloques de piedra. Viene heredado del sitio del placeholder, pero ahora pesa mas porque es
  un objeto de objetivo. Moverlo es cambiar una coordenada.
- **La llave se lee oscura.** Es bronce oscuro en una zona al anochecer con `PP_Mirador` a
  -1,9 EV, y su foco esta en **150 candelas** con radio 800 (las notas del 14/08 hablaban de
  800 cd; alguien lo bajo despues). La silueta se entiende —vastago, anillo y paleton— pero el
  material no luce. Es el mismo tipo de decision que el relleno del coloso.
- Las dos luces del Mirador son **`Stationary`** y salen con una ✗ roja en su icono. No estan
  apagadas —se comprobo: `bVisible` y `bAffectsWorld` en true—: es el aviso de luz estacionaria
  con la iluminacion sin hornear.

## El Gazebo con sus tres piezas reales (2026-08-15, noche)

Rotonda, tableta grabada y Fragmento, los tres de Tripo, desde
`D:\Game Projects\Dark Angels\World Assets\Malkuth\{base para piedra,pieda con letras,fragmentos}\`.

**El fallo del importador se repite por quinta, sexta y septima vez.** La rotonda incluso
nombra sus texturas con otro esquema (`classical_ruin_columns_3d_model_*` en vez de
`tripo_node_*`) y trae **cinco** mapas en el `.fbm`, y aun asi el grafo sale identico:
rugosidad a `Metallic`, `Roughness` vacio, sampler en Color y el metallic sin importar.
`tripo_arreglar_material.py` lo arregla sin tocar nada mas que las constantes.

| | Fragmento | Tableta | Rotonda |
|---|---|---|---|
| Asset | `SK_DA_Fragmento` | `SK_DA_Tableta_Gazebo` | `SK_DA_Rotonda_Gazebo` |
| Vertices | 36.787 | 48.544 | **1.014.955** |
| Malla cruda | 0,62 x 0,40 x 0,98 | 0,63 x 0,37 x 0,98 | 0,98 x 0,98 x 0,81 |
| Escala | 113 | 225 | 818 |
| Tamano final | 83 x 74 x 110 cm | 143 x 82 x 220 cm | 800 x 799 x 665 cm |
| Atenuacion metallic | 0,6 (montura de oro) | 0,15 (piedra) | 0,15 (marmol) |
| `MaxTextureSize` | 1024 | **2048** | 2048 |

**La tableta va a 2048 a proposito**: el objetivo de la estacion es *leerla*, y la inscripcion
tiene que aguantar de cerca. El resto de props van a 1024.

**La rotonda pesa un millon de vertices.** El zip trae el FBX sin decimar, 56,8 MB. Esta en el
mismo orden que la puerta del Claro (1.009.712), asi que hay precedente, pero **son ya dos
props de un millon** y la VRAM sigue muy pasada. Si hace falta recortar, Tripo permite exportar
decimado.

### Colocacion

El Gazebo ya estaba compuesto con placeholders del mismo nombre y **con sus dos luces**
(`Gazebo_Luz_Tableta` y `Gazebo_Luz_Fragmento`, las dos a z=420), asi que aqui **si se calco la
escala del placeholder**, al contrario que con el bauil: se igualo la dimension que manda en
cada pieza (ancho en la rotonda, alto en tableta y Fragmento).

| Placeholder | Era | Ahora |
|---|---|---|
| `Gazebo_Rotonda` | 800 x 800 x 220, base 147 | 800 x 799 x 665, base 147, cima 812 |
| `Gazebo_Tableta` | 120 x 42 x 220, base 202, yaw 180 | 143 x 82 x 220, mismo sitio y giro |
| `Gazebo_Fragmento` | 64 x 63 x 110, base 282 | 83 x 74 x 110, base 282 |

El yaw 180 de la tableta es el bueno: deja la cara grabada mirando a **-Y**, que es por donde
sube el jugador desde las escaleras.

**El Fragmento se movio dos veces, y la segunda con medida.** Los dos estaban en el eje
x=64000, el Fragmento a y=16480 y la tableta a y=16920: desde la aproximacion, el Fragmento se
ponia justo delante. En la lamina va **al lado**. Primer intento a (63830, 16650) —mismo radio
desde el centro, 170 uu— y ahi **lo tapaba una columna**.

**Como se encontro el sitio bueno, que es la parte reutilizable:** las trazas no valen, porque
un SkeletalMesh **no colisiona** y las atraviesan. Asi que se capturo **la misma pose con la
rotonda visible y con la rotonda oculta, y se restaron las dos imagenes**: los pixeles que
cambian son exactamente la rotonda. Con eso sale la ocupacion de las columnas, columna de
pixeles a columna de pixeles, a la altura del Fragmento. Luego se proyectaron con
`WorldPosToScreenCoords` los 24 puntos del arco de radio 170 y se leyo la ocupacion de cada uno:

| Angulo | Posicion | Ocupacion |
|---|---|---|
| 180 | (63830, 16650) | **0,85** — donde estaba, tapado |
| 150 | (63853, 16735) | 0,19 |
| **135** | **(63880, 16770)** | **0,01** — elegido |
| 120 | (63915, 16797) | 0,00, pero pisa la tableta en pantalla |
| 270 | (64000, 16480) | 0,01, pero es el sitio original: delante de la tableta |

A 135 grados queda despejado de columnas **y** justo al lado de la tableta sin solaparla: en
pantalla la tableta ocupa de x=550 a 618 y el Fragmento de 627 a 671.

**Verificado con un numero, no a ojo:** contando pixeles claramente morados desde la pose de
aproximacion, el cristal paso de **0** (tapado por la columna) a **128**, que es lo mismo que
se ve en un primer plano sin obstaculos (126). **La tableta no se toco** en ningun momento.
Recetas en `Tools/MCP/gazebo_fragmento_al_lado.py` y `gazebo_rotonda_visible.py`.

### Truco util: capturar en color sin pedir el visor

Las capturas de esta tanda se tomaron **dentro de la sesion de edicion**, antes de commitear.
En modo edicion Unreal desatura todo **menos** el Level Instance que se esta editando, asi que
la zona que interesa sale en color y **no hace falta pedirle a Angel que devuelva
`View Mode > Lit`** despues del commit. Es la vuelta a lo del visor que se tuerce.

**Y `commit_level_instance` tambien miente al reves:** en el Mirador devolvio error ("may not
be in edit mode") y el `.umap` **si** se habia guardado, con el paquete limpio. Ya miente en
las dos direcciones; lo unico fiable sigue siendo la fecha en disco.

## Estatuas, fuente y puerta del puente (2026-08-15, cierre)

Tres tandas mas de Tripo, con la misma receta de siempre.

| Placeholder | Era | Ahora | Escala | Tamano final |
|---|---|---|---|---|
| `Claro_StatueAngel_L` / `_R` | `SM_DA_AngelV2`, recorte plano de 38 uu | `SK_DA_Estatua_Angel` | 370 | 125 x 105 x 362 cm |
| `SM_Altar_*` (4 piezas) | apilado `GardenFountain*` de Megascans | `SK_DA_Fuente_Santuario` | 281 | 200 x 275 x 155 cm |
| `Puente_Portal_L` / `_R` | dos pilares de 216 x 216 x 1104 | `SK_DA_Puerta_Templo` | 1241 | 1216 x 543 x 692 cm |

**Lo que NO se toco, y conviene que siga asi:** los cuatro
`Claro_Angel_Vigilante1/2`, `_Lancero` y `_Arquero` comparten la malla de
placeholder `SM_DA_AngelV2` con las estatuas, **pero son la hueste de enemigos**, no
decoracion. Filtrar por malla habria sido un error; hay que ir por nombre.

Se conservan `Luz_Altar` y `Puente_Luz_Portal_L`/`_R`: siguen iluminando el mismo punto.

**Sigue habiendo placeholders de silueta sin sustituir**, por si interesan: `SM_Cassiel` es
un `Plane` recortado junto al `NPC_Cassiel` de verdad, `Mirador_Estatua_Sariel` es otro
recorte junto a `NPC_Sariel`, y `Puente_Angel_Gigante` es la silueta blanca de 153 m del
fondo del puente.

### El problema de tamano, que ya son cuatro piezas

Tripo exporta el FBX **sin decimar** si no se le pide otra cosa, y eso da `.uasset` que **no
caben en GitHub**, cuyo limite duro son 100 MB por fichero:

| Asset | Vertices | Peso | Estado |
|---|---|---|---|
| `SK_DA_Puerta_Claro` | 1.009.712 | 227,6 MB | **ya commiteado** (sesion anterior) |
| `SK_DA_Coloso_Angel_V2` | — | 217,6 MB | **ya commiteado** (sesion anterior) |
| `SK_DA_Rotonda_Gazebo` | 1.014.955 | 230 MB | excluido hoy en `.gitignore` |
| `SK_DA_Puerta_Templo` | 1.041.136 | 233 MB | excluido hoy en `.gitignore` |

Los dos primeros **estan dentro de commits que aun no se han subido**, asi que el push
entero se rechaza. Ver el apartado siguiente.

### Cierre: puerta de Yesod y el coloso reutilizado

| Placeholder | Era | Ahora | Escala | Tamano final |
|---|---|---|---|---|
| `Yesod_Portal` | caja de 552 x 96 x 644 | `SK_DA_Puerta_Yesod` | 658 | 458 x 421 x 644 cm |
| `Puente_Angel_Gigante` | `SM_SM_DA_AngelSilueta`, recorte de 1350 de grosor estirado a 15355 | **`SK_DA_Coloso_Angel_V2`**, el mismo del Jardin | 8365 | 5830 x 5511 x 8193 cm |

Lo del coloso lo propuso Angel al ver la lamina 07, y es la decision mas barata de toda la
sesion: **es el mismo angel** y el asset ya estaba importado, asi que **no suma un solo byte**
al proyecto. Proporciones de esa malla, por si vuelve a hacer falta: **0,735 x 0,699 x 0,979**,
deducidas del actor del Jardin (14072 x 13387 x 18750 a escala 19143).

**Ojo, hereda el problema de luz:** al coloso **no le llega ninguna luz direccional** (ver el
apartado del Jardin). En el puente ademas el sol esta detras —yaw 270, contraluz deliberado—,
asi que ahora mismo se lee como **silueta negra**. Si se quiere ver la piedra hay que repetir
la receta del Jardin: un **PointLight** con `VolumetricScatteringIntensity = 0` en el **canal
de iluminacion 1**, y activar el canal 1 en el componente del coloso del puente.

### Resumen de todo lo sustituido

| Zona | Placeholder | Modelo real |
|---|---|---|
| Mirador | `Mirador_Llave` (OldKey, Fab) | `SK_DA_Llave_Mirador` |
| Mirador | `Mirador_Cofre` (SM_OldWoodenChest) | `SK_DA_Baul` |
| Santuario | `SM_Cofre` (SM_OldWoodenChest) | `SK_DA_Baul` |
| Santuario | `SM_Altar_*`, 4 piezas `GardenFountain*` | `SK_DA_Fuente_Santuario` |
| Gazebo | `Gazebo_Rotonda` | `SK_DA_Rotonda_Gazebo` |
| Gazebo | `Gazebo_Tableta` | `SK_DA_Tableta_Gazebo` |
| Gazebo | `Gazebo_Fragmento` | `SK_DA_Fragmento` |
| El Claro | `Claro_StatueAngel_L` y `_R` (`SM_DA_AngelV2`) | `SK_DA_Estatua_Angel` |
| Puente | `Puente_Portal_L` y `_R` | `SK_DA_Puerta_Templo` |
| Puente | `Puente_Angel_Gigante` (silueta) | `SK_DA_Coloso_Angel_V2` (reutilizado) |
| Yesod | `Yesod_Portal` | `SK_DA_Puerta_Yesod` |

**Placeholders de silueta que siguen sin sustituir:** `SM_Cassiel` y
`Mirador_Estatua_Sariel`, los dos planos recortados junto a sus NPC de verdad.

### El repo, desbloqueado y subido (2026-08-15 20:05)

**Ya esta todo en GitHub**: `707b2b8..154e7fe`, 25 commits. El repo estuvo 19 commits sin
subir porque `SK_DA_Puerta_Claro.uasset` (228 MB) y `SK_DA_Coloso_Angel_V2.uasset` (218 MB)
estaban **dentro de commits antiguos** y GitHub rechaza cualquier fichero de mas de 100 MB.

**Se saco con `filter-branch`, no con `filter-repo`:** `filter-repo` es un script de Python y
en esta maquina **no hay Python** —el `python` de la PATH es el stub de la Microsoft Store—,
asi que se uso lo que trae git de serie.

Lo que hizo que fuera seguro: **ninguno de los dos ficheros aparecia en el historial ya
publicado** (`git log origin/main -- <fichero>` daba 0). Por eso se pudo acotar la
reescritura al rango `origin/main..HEAD` y **el push salio sin `--force`**: `origin/main`
seguia siendo ancestro.

```
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --index-filter \
  "git rm --cached --ignore-unmatch '<fichero1>' '<fichero2>'" -- origin/main..HEAD
```

**Dos cosas que conviene saber si se repite:**

- **`filter-branch` borra tambien el fichero del disco**, no solo del historial. Son assets
  vivos del nivel, asi que **hay que copiarlos antes**. Aqui hay copia en
  `_Backups/assets_fuera_de_git/`. De hecho el borrado fallo —`unable to unlink ... Invalid
  argument`— porque **Unreal los tenia abiertos**, pero eso fue suerte, no plan.
- Red de seguridad que quedo puesta: la rama `respaldo-antes-de-filtrar`, el tag
  `respaldo-antes-de-filtrar-20260815` y los `refs/original/` que deja filter-branch. Se
  pueden borrar cuando se confirme que todo esta bien.

**Los cinco assets de mas de 100 MB estan fuera del repo** y documentados en el README:
`SK_DA_Puerta_Claro`, `SK_DA_Coloso_Angel_V2`, `SK_DA_Rotonda_Gazebo`, `SK_DA_Puerta_Templo`
y `SK_DA_Puerta_Yesod`. **Los niveles si se suben y los referencian**, asi que quien clone
vera referencias rotas hasta reimportarlos.

**La leccion, para los proximos modelos:** exportar **decimado** desde Tripo. Los cinco
rondan el millon de vertices porque el FBX sale sin decimar, y ademas la VRAM sigue 1787 MB
pasada.

## Salto rapido de zona en el HUD: TERMINADO (2026-08-15)

Montado y compilando. **Teclas NumPad 1-9 y 0** saltan a cada zona, con la leyenda dibujada pegada
al borde derecho. Las dos funciones viven en `BP_DA_HUD`:

- **`SaltoZonas_Dibujar`** — escrita por DSL, solo dibuja sobre `self`, que es el caso que el
  DSL hace bien. Se llama desde `ReceiveDrawHUD`.
- **`SaltoZonas_Tick`** — **montada nodo a nodo** (32 nodos), porque necesita targets. Se
  llama desde `EventTick`.

Recetas en `Tools/MCP/hud_salto_zonas.py` (construye las dos funciones),
`Tools/MCP/hud_enganchar.py` (mete las dos llamadas en el EventGraph) y
`Tools/MCP/hud_activar_debug.py` (las teclas y el actor activador).

### Por que no funcionaba a la primera: BP_DA_HUD no se instanciaba

El grafo estaba bien y compilaba, pero **no corria nada**. La cadena:

- El `GlobalDefaultGameMode` del proyecto es **`BP_DCSGameMode`** (`Config/DefaultEngine.ini`),
  no `BP_DA_GameMode`.
- El `HUDClass` de ese GameMode es el **`HUD` pelado del motor**, que no dibuja nada.
- El `DefaultGameMode` del World Settings del Master esta en **None**, asi que no lo corrige.
- Quien deberia arreglarlo es **`BP_DA_HUDSpawner`**, que en su BeginPlay hace
  `CreateWidget(WBP_DA_HUD)` + `ClientSetHUD(BP_DA_HUD)`... **pero ese actor no esta puesto
  en el mapa**.

O sea que **`BP_DA_HUD` es codigo muerto en juego**, y con el se pierden tambien el texto de
objetivo y el banner de zona que dibuja. Por eso en PIE solo se ve el HUD de DCS.

**Como se arreglo:** un actor propio y minimo, `BP_DA_DebugZonas`, colocado en el Master como
`DEBUG_SaltoZonas`, que en BeginPlay solo hace `ClientSetHUD(BP_DA_HUD_C)`. Se eligio eso y
**no** colocar el `BP_DA_HUDSpawner` entero **para no cambiar lo que se ve en juego**: el
spawner ademas mete `WBP_DA_HUD` en pantalla, que se solaparia con el HUD de DCS.

**Pendiente de decidir, aparte del debug:** que `WBP_DA_HUD` y el HUD del proyecto no salgan
en juego es un problema de verdad, no del debug. O se coloca el spawner, o se pone
`BP_DA_GameMode` en el World Settings del Master.

### Las teclas: dos familias descartadas antes de acertar

| Familia | Que paso |
|---|---|
| **1-9 y 0** | Las coge DCS para los hechizos (`IMC_Player`) |
| **F1-F10** | **Las coge el viewport de Unreal para los modos de vista.** F3 es wireframe, asi que al saltar aparecias en el escenario nuevo en wireframe |
| **NumPad 1-9 y 0** | Libres en los dos sitios. **Es la que quedo** |

Si algun dia hace falta cambiarlas —por ejemplo en un portatil sin bloque numerico— es
editar `TECLAS` y `ETIQUETAS` en `Tools/MCP/hud_teclas.py` y relanzar; cambia las teclas del
grafo y la leyenda a la vez. Otras familias libres: `LeftBracket`, `RightBracket`,
`Semicolon`, `Quote`, `Comma`, `Period`, `Slash`, `Backslash`, `Hyphen`, `Equals`.

**La leccion:** para un atajo de debug en PIE no valen ni las teclas que usa el juego ni las
que usa el editor. Las F estan cogidas por el viewport aunque el foco este en el juego.

### Las cinco trampas del toolset de Blueprints, que costaron toda la tarde

1. **El DSL no conecta los pines `Target`.** Reserva el pin llamado `self` y lo ata al propio
   blueprint, asi que **no puede llamar funciones sobre otros objetos**. Probado posicional,
   `:self` y `:Target`: los dos primeros compilan con *"This blueprint (self) is not a
   PlayerController, therefore ' Target ' must have a connection"* y el tercero da
   *"Unknown input pin"*. La salida es `create_node` + `connect_pins`, que usan
   `PinID {direction, index_id, node}` y si permiten conectar el target.
2. **`read_graph_dsl` no devuelve algo que `write_graph_dsl` acepte.** El lector saca los
   pines literales como `(bind _returnvalue_1 0.5)` y el escritor los rechaza con
   *"expression produced no output pin"*. **No se puede leer un grafo, retocarlo y
   reescribirlo.**
3. **El escritor compila en cada escritura**, asi que un grafo que no compila **no se puede
   ni vaciar**. La salida es `remove_function_graph` y volver a crearla.
4. **Hay que usar la ruta construida a mano** (`<blueprint>:<NombreFuncion>`), **no el
   `refPath` que devuelve `add_function_graph`**: con ese, `write_graph_dsl` no encuentra el
   nodo de entrada y falla con *"AddEvent|<nombre> does not exist"*.
5. **En un nodo de EVENTO el pin de ejecucion es el de indice 1**, no el 0: el 0 es el
   `OutputDelegate`. Conectar al 0 no da error y simplemente no hace nada.

Y dos detalles de nombres: el tipo para llamar a una funcion propia es
`CallFunction|<Nombre>` **sin guiones bajos** (`SaltoZonas_Dibujar` ->
`CallFunction|SaltoZonasDibujar`), y para el ancho de pantalla hay que usar
**`Viewport|GetViewportSize`** —sin pines de entrada, devuelve Vector2D— porque
`HUD|GetViewportSize` resuelve a un nodo cuyo Target es un PlayerController.

## Como se llego hasta aqui (2026-08-15)

**El objetivo:** botones/teclas para saltar a cualquier zona y poder verlas en juego.

**Primer hallazgo, que cambia el planteamiento:** las 13 zonas **no son mapas separados**.
Son Level Instances dentro de `L_DA_Malkuth_Master`; los `*_Sub.umap` son sus sublevels. Asi
que **no hay `OpenLevel` que valga**: es teletransportar al pawn dentro del mismo mapa, y
ademas es instantaneo, que para probar es mejor.

**Segundo:** el `PlayerControllerClass` del GameMode es el `PlayerController` pelado del
motor, sin blueprint propio, asi que el cursor esta oculto y `bEnableClickEvents` en false.
Para botones clicables harian falta los dos en true, y eso pelea con la camara al raton. Por
eso Angel acepto **teclas 1-9 y 0**, con la leyenda dibujada en el HUD.

**El HUD es `AHUD`** (`BP_DA_HUD`, con `ReceiveDrawHUD` ya implementado y asignado como
`HUDClass` del GameMode), asi que dibujar la leyenda ahi es directo.

### El bloqueo: el DSL de grafos no conecta los pines `Target`

`BlueprintTools.write_graph_dsl` **no puede llamar funciones sobre otros objetos**. Probado
de las tres formas y las tres fallan igual:

```
(Game|Player|WasInputKeyJustPressed pc :Key "One")                 ; posicional
(Game|Player|WasInputKeyJustPressed :self pc :Key "One")           ; keyword con el nombre real del pin
(Game|Player|WasInputKeyJustPressed :Target pc :Key "One")         ; keyword con el nombre visible
```

Las dos primeras compilan con
`"This blueprint (self) is not a PlayerController, therefore ' Target ' must have a connection"`
—o sea, crea el nodo pero deja `Target` sin conectar— y la tercera da
`Unknown input pin "Target". Input pins: ['self', 'Key']`.

La causa: **el DSL reserva el pin llamado `self`** y lo ata automaticamente al propio
blueprint, asi que no hay manera de meterle otro objeto. Afecta a **todo** lo que necesite
target: `WasInputKeyJustPressed` sobre el PlayerController y `SetActorLocation` sobre el pawn.

**Dos cosas mas que se aprendieron por el camino:**

- **`read_graph_dsl` no devuelve algo que `write_graph_dsl` acepte.** El lector saca los
  pines literales como `(bind _returnvalue_1 0.5)` y el escritor los rechaza con
  *"expression produced no output pin"*. **No se puede leer un grafo, retocarlo y
  reescribirlo**: hay que reconstruirlo a mano, con el riesgo que eso tiene en un grafo que
  ya funciona.
- **El escritor compila en cada escritura**, asi que un grafo que no compila **no se puede
  ni vaciar**: `write_graph_dsl` con el cuerpo vacio tambien falla. La salida es
  `remove_function_graph` y volver a crearla.

**Estado: `BP_DA_HUD` quedo intacto y compilando.** Se crearon dos funciones
(`SaltoZonas_Dibujar` y `SaltoZonas_Tick`), fallo el enganche de las teclas y **se borraron
las dos**, comprobando despues que el blueprint compila y que su `EventGraph` sigue igual.

### Como terminarlo

La via que si controla los pines es **construir el grafo nodo a nodo** con `create_node` +
`connect_pins`, que trabajan con `PinID {direction, index_id, node}` y por tanto permiten
conectar `Target` explicitamente. Son unos 32 nodos y ~70 conexiones —10 zonas x (rama +
lectura de tecla + SetActorLocation), mas `GetPlayerController` y `GetPlayerCharacter`— pero
se hace en un solo script con bucles.

Datos ya medidos, listos para usar (traza vertical sobre cada zona, +120 para no encajar al
jugador en el suelo):

| Tecla | Zona | Destino |
|---|---|---|
| 1 | Jardin | (-59649, -60004, 138) |
| 2 | Mirador | (-16000, -23800, 438) |
| 3 | El Claro | (44000, -13650, 84) |
| 4 | Gazebo | (64000, 15400, 184) |
| 5 | Santuario | (43940, 47600, 118) |
| 6 | Puente | (16000, 60000, 1532) |
| 7 | Yesod | (-92000, 16000, 13213) |
| 8 | Anfiteatro | (-73649, 41996, 136) |
| 9 | Elevador | (-74000, 8000, 94) |
| 0 | Gabriel | (-66000, -15000, 281) |

La traza de Gabriel C1 dio 28774, que es un tejado o un monte y no el suelo; por eso el 0
apunta a C2, que es el tramo central del pasillo de Gabriel.

El borrador del script, con la leyenda ya escrita y las zonas en una tabla facil de tocar,
esta en `Tools/MCP/hud_salto_zonas.py`.

## Sariel bajado del pedestal: HECHO PERO SIN GUARDAR (2026-08-15, cierre)

**Lo que pidio Angel:** bajar a Sariel de su base, quitar la base y ponerlo junto a la llave.
Las escalas se dejan como estan.

**Antes, la medida que aclaro el malentendido.** Parecia que los NPC eran mucho mas grandes
que el jugador, y no lo son:

| | Malla base | Escala | Alto final |
|---|---|---|---|
| **Jugador** (`SKM_Malakh_Own`) | 99,8 | **1,70** | **170** |
| NPC Sariel / Cassiel | 98,4 / 98,3 | 1,829 / 1,831 | 180 |
| Enemigos Vigilante / Lancero / Arquero | ~98,4 | ~1,828 | 180 |

Los cinco NPC y enemigos estan clavados en 180 y el jugador en 170: **6% de diferencia**. Lo
que hacia parecer gigante a Sariel era **`Mirador_EstatuaBase`**, un pedestal de 200 x 200 x
**150** sobre el que estaba subido.

**Los valores nuevos** (el suelo del mirador esta a z=318 en toda esa zona):

- `Mirador_EstatuaBase` — borrado
- `NPC_Sariel` — de (-16000, -22850, **468**) a **(-16150, -23180, 322)**, junto a la llave
- `Mirador_Luz_Estatua` — de (-16000, -23050, 620) a (-16150, -23120, 560)

Receta en `Tools/MCP/mirador_bajar_sariel.py`.

### Pero NO se pudo guardar: el `.umap` del Mirador esta bloqueado

Se cumplio la profecia de la nota del 14/08. Tras muchos ciclos `edit`/`commit` sobre **el
mismo** Level Instance en una sesion, Unreal filtra un handle sobre su `.umap` y a partir de
ahi **el guardado falla para siempre hasta reiniciar el editor**:

```
MoveFile was unable to move '...L_DA_Malkuth_Mirador_Sub.umap' ... (Error Code 32)
Error saving '...L_DA_Malkuth_Mirador_Sub.umap'
Message dialog: The asset ... failed to save.
```

`commit_level_instance` **devuelve exito igualmente** y encima recarga el LI, asi que los
cambios se deshacen solos y sin un solo error visible. **El ultimo guardado bueno del Mirador
es el de las 19:02:22** (la llave apoyada en el plinto); todo lo posterior se perdio.

**Para retomarlo:** reiniciar el editor, lanzar `ModelContextProtocol.StartServer` y volver a
pasar `mirador_bajar_sariel.py`. Son treinta segundos.

### Dos trampas nuevas, y las dos costaron un pase entero de trabajo

1. **Nunca editar con PIE corriendo.** El primer intento se hizo con PIE activo: `find_actors`
   devuelve entonces los actores del **mundo de PIE**, y todo lo que se les haga se pierde al
   parar. Se detecta porque las rutas llevan `UEDPIE_0_`, y porque `is_dirty` sobre el `.umap`
   contesta *"Asset does not exist"*.
2. **Filtrar por la ruta del asset, no por el nombre del sublevel.** Con el LI en edicion
   conviven dos copias de cada actor: la instanciada en `/Temp/...<Sub>_LevelInstance_...` y
   la real en `/Game/.../<Sub>`. Un filtro tipo `if SUBNIVEL in refPath` **casa con las dos**,
   y si toca la de `/Temp` el paquete **ni se marca sucio**: el commit recarga y todo vuelve
   atras. La comprobacion rapida es mirar `is_dirty` **antes** de commitear.

## PROXIMA SESION — empezar por aqui (escrito 2026-08-15)

**El telon 360 esta cerrado.** Cupula en z=0, 230 montes ocultos y 6 encendidos como plano
intermedio en el Jardin, nube volumetrica apagada, coloso arreglado.

### Por orden de valor

1. **Repasar el telon 360 CON NIEBLA.** Es lo primero porque invalida parte de lo juzgado: el
   visor del editor tiene `Show > Fog` apagado y el juego va cargado de niebla. Decidir si se
   toca `Fog_Malkuth` (los candidatos son `FogMaxOpacity` 0,45, `StartDistance` 0 y la niebla
   volumetrica a 220 m) o si el panorama tiene que convivir con ella.
2. **Plano intermedio del Jardin: los seis montes aportan poco** (9 puntos de luma en el
   borde izquierdo, 2-3 en el resto). Decidir si mas montes o algo a media distancia de
   verdad.
3. **Auditar la VRAM, otra vez.** El exceso medido era de **1787 MB** con los 236 montes
   renderizando. Ahora no renderizan: **volver a medir antes de tocar nada mas**, que el
   numero de partida ha cambiado. Lo gordo restante son Megascans, escaneos y texturas 4K.
4. **Foliage instanciado en El Claro.** Medido el 15/08: 98 actores de planta mas movieron
   **menos de 2 puntos** de saturacion. Hacen falta miles de instancias, no actores sueltos.
5. **Decidir la nube volumetrica.** Esta apagada. Si se quiere de vuelta, hay que resolver
   antes la banda dura que dibuja a la altura del ojo.
6. **El Heraldo sin colocar**, por decision de Angel.
7. **Comportamientos de combate**: los cinco enemigos heredan el Behaviour Tree del Warrior
   tal cual. Que el Arquero mantenga distancia y el Lancero cargue ya es diseño.
8. Assets que faltan segun el PDF: **tableta grabada y Fragmento** del Gazebo, **llave y
   baul** del Mirador, **angel guardian** del portal de Yesod, props del Santuario.

### Lo operativo, sin cambios

- **El guardado de sublevel falla con Error Code 32** cada cierto tiempo y deja un dialogo
  modal que cuelga el MCP. Se arregla reiniciando el editor (y `ModelContextProtocol.StartServer`
  despues). Esta sesion **no ha pasado**: seis commits seguidos, los seis verificados en disco.
- **El viewport se tuerce con cada ciclo de edicion de Level Instance.** Si las capturas salen
  grises, no buscar al actor culpable: pedir `View Mode > Lit`. Y **capturar antes de editar**,
  no despues.
- **Sin push todavia.** El repo es publico y seguimos con ~17 commits sin subir.

## Interaccion: enchufada a DCS, no montada aparte (2026-08-16)

Angel pidio un cartel abajo al acercarse a algo interactuable, con una tecla, y
que fuese global para marcar cualquier objeto. **Lo que habia que hacer no era
montarlo: era descubrir que DCS ya lo trae entero.**

### Lo que ya tenia DCS

| Pieza | Que es |
|---|---|
| `I_IsInteractable` | Interfaz con `Interact` y `GetInteractionMessage` |
| `WB_InteractionMessage` | El cartel, **ya dentro de `WB_InGame`** |
| `IA_Interact` | Ya mapeada, en `IMC_Player` |
| `BP_PickupActor` | El unico que la implementaba: el recogible de DCS |

La descripcion que trae escrita `GetInteractionMessage` lo dice sola: *"should
return word describing action that will be performed on interact e.g for Items -
Pickup, for NPC - talk etc."* O sea que **el verbo por objeto viene de serie**.

### Como detecta DCS (leido de `BP_CombatCharacter`)

Grafo colapsado *Interaction Events*, 34 nodos:

```
CheckForInteractable ->
  start = GetActorLocation,  end = start + ForwardVector * dist
  tipos = DCS|Utility|GetInteractableObjectTypes
  Collision|CapsuleTraceForObjects -> BreakHitResult -> SetInteractionActor
  Interaction|GetInteractionMessage (por interfaz) -> WB_InteractionMessage.UpdateWidget
EnhancedInputActionIA_Interact -> CanOpenUI? -> Interaction|Interact
```

**Traza de capsula hacia delante contra el TIPO DE OBJETO `Interactable`.** No es
solape ni traza contra la malla. De ahi salen los dos unicos requisitos:
`ObjectType = ECC_GameTraceChannel2` (que en `DefaultEngine.ini` se llama
"Interactable", con `bTraceType=False`, o sea canal de objeto) y
`CollisionEnabled = QueryOnly`. **La malla no necesita colision**, que menos mal
porque las de Tripo vienen sin ella.

Y ojo: **el volumen es el blanco al que hay que apuntar**, no un radio de
proximidad. La distancia la pone la traza del personaje.

### La tecla: la I estaba cogida

Angel pidio la **I** *"si es que aun no esta asignada para algo mas"*. Lo estaba.
Como el MCP no serializa el array `Mappings` y el sandbox de Python del editor no
deja `import unreal`, se decodifico **`IMC_Player.uasset` a mano** (parser en
`Tools/MCP/`, ver abajo). Las 63 asignaciones usan:

```
A C D E F I Q R S U W X
CapsLock LeftShift LeftControl Tab SpaceBar
LeftMouseButton RightMouseButton ThumbMouseButton2 MouseScrollUp/Down
```

La I es del inventario. Se penso en la G, y **Angel dio con el argumento bueno**:
si la mitad de las interacciones son recoger cosas, tener una tecla para
"interactuar" y otra para "recoger" es absurdo. **Se quedo la E**, la que ya usa
DCS.

### Lo que se anadio

`BP_DA_Interactuable` en `Content/DarkAngels/Blueprints/Interaccion/`:

- `Raiz` (Scene) -> `Malla` (SkeletalMesh, sin colision) y `Zona` (Box 60x60x90 a z=90)
- `Zona` con ObjectType `ECC_GameTraceChannel2` y `QueryOnly`
- variable `Verbo` (String, editable por instancia) -> lo que sale en el cartel
- `GetInteractionMessage` devuelve `Verbo`. **Ojo: la interfaz devuelve `Name`**,
  no String; el DSL mete solo la conversion `StringToName`.
- `Interact` se queda vacia, a proposito: el comportamiento aun no esta decidido

**Va ENCIMA del prop, no en su lugar.** El prop conserva malla, escala (los
cofres van a 92) y la animacion idle de los NPC, y el actor nuevo solo aporta
caja e interfaz. Marcar algo nuevo es soltarle uno encima.

| Actor | Zona | Sobre | Verbo |
|---|---|---|---|
| `Interact_Cofre` | Santuario | `Santuario_Cofre` | Abrir |
| `Interact_Cassiel` | Santuario | `NPC_Cassiel` | Hablar |
| `Interact_Llave` | Mirador | `Mirador_Llave` | Recoger |
| `Interact_CofreMirador` | Mirador | `Mirador_Cofre` | Abrir |
| `Interact_Sariel` | Mirador | `NPC_Sariel` | Hablar |

### Lo que NO se hizo, y por que

- **No se duplico `BP_PickupActor`**, que era la via facil para heredar la
  interfaz ya implementada. Es un asset de DCS, de pago, y este repo es publico:
  un duplicado suyo dentro de `/Game/DarkAngels/` acabaria subido a GitHub.
- **No se monto el sistema por tags** que se iba a hacer al principio (cartel
  dibujado desde `BP_DA_HUD`). Habria sido un sistema paralelo peor, con texto
  fijo, y colgando de un HUD que **solo se instancia por el parche de debug del
  salto de zonas**.

### Cuatro trampas nuevas del MCP

1. **No hay forma de declarar interfaces.** No existe herramienta, y
   `set_properties` sobre el blueprint no vale: resuelve al CDO
   (`Default__..._C`) y `ImplementedInterfaces` vive en el `UBlueprint`. Contesta
   *"the following properties could not be set: ImplementedInterfaces"*. **Lo
   marco Angel a mano** en Class Settings > Implemented Interfaces > Add.
2. **`read_graph_dsl` no abre grafos colapsados**: *"Cannot cast type
   'K2Node_Composite' to 'Blueprint'"*. Pero **`find_nodes` si funciona sobre
   ellos**, y con los `type_id` y las posiciones se reconstruye lo que hace. Asi
   se saco el `CapsuleTraceForObjects` de DCS.
3. **`set_properties` sobre un struct Vector solo aplica el primer campo.** Pedir
   `BoxExtent` (70,70,45) deja (70,60,90), con y/z en el valor del CDO y **sin un
   solo error**. Se rodea escalando el ACTOR: como estos son solo volumen,
   la escala solo toca la caja, y `RelativeLocation` escala con ella.
4. **En una INSTANCIA de blueprint el `refPath` del componente lleva su NOMBRE,
   no su clase.** En el CDO sale `Box_GEN_VARIABLE`, en la instancia sale `Zona`.
   Filtrar por `"BoxComponent" in refPath` no casa nunca y el ajuste se pierde en
   silencio.

Y una del editor, no del MCP: **el nivel actual cambia solo** entre el maestro y
un sublevel. Con el maestro abierto, tocar un actor de dentro da *"is inside
level instance ... which is not in edit mode"*. Los scripts miran
`get_current_level` y eligen camino.

### Scripts

- `Tools/MCP/interaccion_crear_bp.py` — crea el blueprint. Idempotente.
- `Tools/MCP/interaccion_mensaje.py` — escribe `GetInteractionMessage` por DSL.
- `Tools/MCP/interaccion_colocar.py` — coloca los volumenes de una zona. La caja
  se dimensiona con las medidas reales del prop (`get_actor_bounds`), con un
  minimo para que el blanco no quede imposible. **Una zona por lanzamiento.**
- `Tools/MCP/interaccion_ajustar_cajas.py` — redimensiona volumenes ya puestos.

## El conteo que ensena Tripo NO dice nada (2026-08-16)

Aviso corto pero importante, porque ya llevo una conclusion equivocada por aqui.

**La cifra de la vista previa de Tripo es un techo fijo, igual para todo.** Dos
modelos que no se parecen en nada:

| Modelo | Caras que anuncia la web |
|---|---|
| Cofre abierto | 1.929.711 |
| Alas de Cassiel | 1.929.560 |

Eso no es la densidad de la malla, es el limite de la previsualizacion HD.

**Y el FBX sigue saliendo SIN decimar**, como ya decia la nota de la rotonda:
los cinco props que rondan el millon de vertices —y que por eso pesan 233-243 MB
y se quedaron fuera del repo— salieron asi de Tripo.

**El error que cometi el 16/08:** el cofre abierto importo con 47.823 vertices y
di por hecho que Tripo exportaba decimado solo. **No: Angel le habia hecho remesh
antes de exportar** y no me lo habia dicho. La conclusion "no hace falta remesh"
es FALSA y el mensaje del commit `0f43202` la repite; vale esta nota, no aquel.

**Lo que hay que hacer:** remesh en Tripo antes de exportar, **45.000 vertices**
es la referencia —lo que pesan Cassiel (46.495) y el cofre cerrado (48.009)—.
Con geometria fina, como unas alas con plumas, comprobar que la silueta
sobrevive; si se pierde, el arreglo es SUBIR el conteo, no bajarlo: 80k siguen
siendo unos 15 MB, nada al lado de los 230 MB de un millon.

## Modo inspeccion: la camara se planta delante del objeto (2026-08-16)

Ya en `Interact`: al pulsar **E** sobre un interactuable la camara se pone
delante del objeto y lo encuadra entero; **la misma E vuelve al juego**.
Aprobado por Angel al segundo intento.

### El truco: no se toca la camara del jugador

El actor lleva un `CameraComponent` colgado en su **-X local**. Al entrar se
**gira el actor** para que ese -X apunte al jugador, con lo que la camara aparece
entre jugador y objeto, encarandolo, y despues `SetViewTargetWithBlend` hacia el
propio actor con 0,35 s de transicion. **Girar el actor es gratis** porque no
tiene malla visible: es solo volumen. Al salir, la vista vuelve al pawn.

### Los tres fallos de la primera version, y por que

1. **La camara salia siempre picada, mirando el objeto desde arriba.** Se copiaba
   la rotacion **entera** de `FindLookAtRotation`. El origen del jugador esta a
   la altura del pecho y el del objeto en el suelo, asi que el pitch miraba
   siempre hacia abajo. **Arreglo: romper el rotator y copiar solo el YAW**
   (`BreakRotator` -> `MakeRotator` con Roll y Pitch a 0). Con eso queda a nivel
   y de frente, que es el angulo que se quiere de un objeto.
2. **Se colaban el escudo y la espada del jugador en el encuadre.** No basta con
   esconder el pawn: hay que recorrer `GetAttachedActors` **en recursivo** y
   esconder tambien lo que lleve encajado.
3. **ESC no vale como tecla de salida.** En el editor Escape **para la sesion de
   PIE**, asi que dentro del editor no hay forma de probarlo. Se quito entero
   —tecla y cartel— y `Interact` paso a ser un **conmutador**: la misma E entra y
   sale.

### El aviso, sin HUD propio

`GetInteractionMessage` devuelve **"Aceptar"** mientras `Inspeccionando` esta a
true, y el verbo normal si no:

```
(return (Utilities|String|SelectString "Aceptar" (GetVerbo) (GetInspeccionando)))
```

Asi el cartel de DCS pasa solo de `[E] Recoger` a `[E] Aceptar` y **sobra
dibujar nada aparte**. Hubo un `Inspeccion_Dibujar` en `BP_DA_HUD` que pintaba
"ESC para salir" abajo al centro, y se retiro: un sitio menos donde mirar.
Detectaba si estabamos dentro comparando el **view target del PlayerController
con el pawn**, que es un truco util por si vuelve a hacer falta —no necesita que
nadie le escriba nada al HUD, y valdria con cualquier cosa que robe la camara.

### El encuadre

La distancia sale del tamanio de la caja `Zona` y del FOV. Con FOV 90 la mitad
del angulo horizontal es 45 grados (tan = 1) y en vertical, con 16:9, tan =
0,5625. **Manda casi siempre el vertical**, que es el lado corto:

```
d = max(ancho/2, alto*0.889) * 1.6
```

El margen empezo en 1,25 y se subio a 1,6 porque el cofre quedaba encima. La
altura de la camara es 90 sin escalar, el mismo valor que la caja, que escalado
cae justo a media altura del objeto.

| Objeto | Ancho x alto | Camara a |
|---|---|---|
| Llave | 80 x 70 | 100 |
| Cofre del Mirador | 129 x 70 | 104 |
| Cofre del Santuario | 140 x 90 | 128 |
| Sariel | 86 x 181 | 258 |
| Cassiel | 100 x 190 | 270 |

**Al anadir un interactuable nuevo hay que relanzar `interaccion_encuadre.py`**
en su zona, o su camara se queda con los 220 por defecto.

### Scripts

- `Tools/MCP/interaccion_inspeccionar.py` — monta el conmutador entero. Borra
  antes todo nodo del EventGraph que no sea un evento, asi que **es rehacer, no
  parchear**: si se cambia algo, se cambia aqui y se relanza.
- `Tools/MCP/interaccion_encuadre.py` — calcula la distancia de cada camara. Una
  zona por lanzamiento.
- `Tools/MCP/hud_quitar_inspeccion.py` — retiro del cartel de ESC del HUD.

### Dos detalles mas del MCP

- **Para CREAR un nodo de llamada a funcion propia el id pierde los guiones
  bajos** (`CallFunction|InspeccionTick`), pero **el nodo ya creado se reporta
  con ellos** (`|Inspeccion_Tick`). No son el mismo texto.
- **El `type_id` del nodo de tick es `AddEvent|EventTick`**, no `ReceiveTick`,
  que es como lo llama `list_events`. Nombre de evento y type_id de nodo no
  coinciden.
- No hay **nodo `Self`** creable: la referencia a uno mismo se saca por
  `GetZona` -> `Components|GetOwner`.

### Pendiente

- **`Interact` solo encuadra.** El comportamiento de verdad —que la llave se
  recoja, que el cofre se abra, que el NPC hable— sigue sin escribir.
- Si algun dia la llave y los cofres tienen que ir al inventario de verdad, lo
  suyo es que pasen a ser `BP_PickupActor` (o hijos suyos), que ya lo resuelve.

## El cofre del Santuario: sacado, orientado y encendido (2026-08-16)

Cuatro pasadas sobre el mismo prop, cada una commiteada y verificada en disco.

### Donde acabo

| | valor |
|---|---|
| Posicion | (44400, 48200), base z=12,5, tapa z=79 |
| Yaw | **-66,5** |
| Foco | `Luz_Cofre`, PointLight en (44207,4, 48116,3, 194) |

### La orientacion: el frente del modelo es su **-Y local**

El de Tripo no viene mirando a +X. La cara ancha —la del meandro y la cerradura— es el
**-Y local**, asi que para encarar un punto:

```python
yaw = math.degrees(math.atan2(dy, dx)) + 90.0
```

Se giro dos veces. Primero a **-37,5**, encarando el punto exacto de llegada del jugador.
Luego Angel pidio que mirase **al centro de la explanada**, que es la fuente en
(43940, 48000): salio **-66,5**, 29 grados mas. Es la buena, porque al centro es adonde
acaba plantandose el jugador cuando habla con Cassiel, no al punto por el que entro.

### El foco: cenital NO

El cofre habia caido en la sombra de la explanada y solo se distinguia por el brillo morado
de la cerradura. Se le puso PointLight propio, como ya tienen la llave del Mirador y el
Fragmento del Gazebo.

**El primer intento, a plomo sobre el cofre (z=229), no valia**: quemaba la tapa a blanco y
dejaba la cara frontal completamente negra —justo la que se quiere enseñar—. La captura no
deja lugar a dudas, el cofre se leia como una mancha negra con un filo blanco arriba.

Arreglado adelantandolo **210 uu hacia el centro de la explanada** (la direccion a la que
mira el cofre) y bajandolo: queda a **28,7 grados de elevacion** en vez de a plomo. Con eso
el frente se lee entero: paneles de piedra clara, herrajes oscuros y la gema morada al
centro.

**Regla que se saca de aqui:** un foco para *enseñar* un prop va delante de el, no encima.
Cenital solo si lo que interesa es la silueta contra el suelo.

### El presupuesto de luces estacionarias

Las Stationary tienen tope: **a partir de cuatro solapandose en un punto**, las sobrantes
caen a dinamicas y se pierde el lightmap. En el cofre ya llegaban dos —`Luz_Altar` a 502 con
radio 520, y `Luz_Cassiel` a 333—, asi que esta se quedo con **radio corto, 420**, y van
tres de cuatro. `santuario_luz_cofre.py` **cuenta las estacionarias que cubren el punto
antes de crear nada** y lo saca en el informe; conviene copiar ese chequeo al poner focos en
zonas que ya tengan iluminacion local.

### Convencion de luces del Santuario

Leida de las que ya habia, por si hace falta otra: `PointLight` | `Stationary` | 6500 K |
`Candelas` | radio 520. `Luz_Altar` z=215, intensidad 220, con sombras. `Luz_Cassiel` z=320,
intensidad 110, sin sombras. La nueva: z=194, intensidad 230, con sombras (para que el cofre
se apoye en el suelo en vez de flotar).

### Scripts

- `Tools/MCP/santuario_luz_cofre.py` — crea el foco. Abre la sesion de edicion del LI y **la
  deja abierta**.
- `Tools/MCP/santuario_luz_cofre_ajuste.py` — lo recoloca. **No vuelve a llamar a
  `edit_level_instance`** a proposito: encadenar ciclos edit/commit sobre el mismo LI es lo
  que acaba bloqueando el `.umap` con el Error Code 32.

Las capturas se tomaron **dentro de la sesion de edicion**, antes de commitear, que es
cuando el viewport todavia conserva el color.
