# Vetas de Malakh — bonus por marca

Propuesta del 01/09/2026. Sustituye a los diez bonus de las *Fichas de Conjunciones* (`Kimi3/`)
por un sistema en **tres vetas**: el jugador recibe algo con la **primera marca** (Mirador), algo
más con la **segunda** (Gazebo) y el sello de la conjunción con la **tercera** (Gabriel), en vez
de esperar al cierre de Malkuth. Todo lo de abajo se apoya en piezas que ya existen en el
proyecto; la columna «gancho» dice cuál.

## Regla de entrega

| marcas | qué se activa | dónde se gana | dónde se juega |
|---|---|---|---|
| 1 | la **primera veta**, por la fuerza de esa marca | Sariel, en el Mirador | Mirador → Gazebo |
| 2 | la **segunda veta**, por el par (misma fuerza o mezcla) | La Fuente, en el Gazebo | Gazebo → Elevador (Gabriel incluido) |
| 3 | el **sello** de la conjunción (1–10) | Gabriel, en el Elevador | Yesod |

- Las vetas **no se pierden** al ganar la siguiente: en Yesod se llevan las tres.
- La lectura es la misma que hoy usa la veta visual: `LeerFuerza` 1/2/3 y `TotalMarcas` del
  GameState, sondeados por un componente (`BP_DA_Vetas`, hermano de `BP_DA_MarcasVisual`).
- El Debug HUD ya fuerza marcas (`DbgMarcaForzar`), así que cada veta se prueba sin jugar
  hasta el Mirador.
- El feedback es el que ya existe: color y brillo de la veta, hit-stop, sacudida, SoundCues.

## Primera veta (una marca)

| fuerza | nombre | qué hace | gancho existente |
|---|---|---|---|
| Gracia | **Luz que corrige** | Cada parry logrado devuelve 8 de vida y el aturdido dura 0,4 s más. | `PlaySuccessfullParryEffects` (override en `BP_Malakh_DCS`), `BP_StatsManagerComponent` (Health), duración del `Stun` en `F_StatusEffectParams` |
| Corrupción | **Hambre** | El combo tarda el doble en resetearse; a partir del 3.er golpe seguido, +15 % de daño. El arma divina se corrompe visualmente con el combo. | `ResetComboCounterWithDelay`, `GetComboCounter`, `AddModifier` (Damage), parámetro `Corrupcion` de `M_DA_ArmaDivina` |
| Voluntad | **Pie firme** | Inmune al Derribo (golpe de suelo del Gigante, arrojadizos) y la ventana de tech-roll dobla su tamaño. | `StatusEffectsToIgnore` de `BP_StatusEffectsComponent` (+Knockdown), `ANS_DA_TechWindow` |

## Segunda veta (dos marcas)

| par | nombre | qué hace | gancho existente |
|---|---|---|---|
| G+G | **Juicio** | Tres parries logrados seguidos sin recibir daño → 6 s de Juicio: todo golpe es crítico, con hit-stop y sacudida; la veta sube a brillo 40. Recibir daño reinicia la cuenta. | contador propio sobre `PlaySuccessfullParryEffects`, `CritMultiplier`, `BP_DA_NotifyHitStop`, `BP_DA_NotifySacudida`, `BrilloVena` |
| C+C | **Masacre** | Con combo ≥ 4 los enemigos no pueden bloquear: la guardia no existe. | `CanBeBlocked` (override: devuelve `combo < 4`) |
| V+V | **Silencio** | Un radio de 500 alrededor de Malakh donde el rayo celestial y la lluvia de flechas no hacen daño, y el estandarte del Heraldo no bonifica. | `BP_DA_AuraComponent` reutilizado como aura propia; comprobación en `BP_CelestialRay`, `BP_DA_FlechaLluvia`, `BP_DA_EstandartePlantado` |
| G+C | **Eclipse** | El golpe siguiente a un parry logrado hace ×2 y suelta el destello del arma. | `AddModifier` de un golpe, `BP_DA_DestelloDescarte` |
| G+V | **Heraldo** | Tras un parry, 3 s con +25 % de velocidad de ataque y regeneración de stamina ×2. | `AttackSpeed` (StatsManager), `SetRegenMultiplier` (StatsRegenerator) |
| C+V | **Renegado** | El arma arrojada (tecla G) derriba al que golpea y hace ×2. | `BP_DA_LanzaArrojada`, efecto `Knockdown` propio (`DA_DA_StatusEffect_Knockdown`) |

## Sello de la conjunción (tres marcas)

Se suma a las dos vetas anteriores; es lo que Malakh lleva a Yesod. La numeración es la del PDF.

| # | conjunción | sello |
|---|---|---|
| 1 | Ascendido (G G G) | Juicio dura 12 s y entrar en él cura un 25 %. |
| 2 | Corrupto (C C C) | Masacre desde el 3.er golpe, y cada muerte en cadena cura un 10 %. |
| 3 | Desatado (V V V) | El Silencio anula también el aura del Inspector y el Derribo del Gigante a cualquier distancia. |
| 4 | Eclipse Celestial (G G C) | Durante Juicio los golpes rompen guardia (Masacre sin combo). |
| 5 | Heraldo Libre (G G V) | Durante Juicio la esquiva no gasta stamina. |
| 6 | Eclipse Oscuro (C C G) | El golpe tras parry, con combo ≥ 4, derriba. |
| 7 | Renegado (C C V) | El arma arrojada vuelve a la ranura a los 6 s: se arroja sin perderla. |
| 8 | Libre Luminoso (V V G) | Dentro del Silencio los parries curan el doble. |
| 9 | Libre Oscuro (V V C) | Dentro del Silencio los enemigos no bloquean. |
| 10 | Convergente (G C V) | Resonancia: la veta activa rota sola cada 20 s entre las tres primeras vetas; la veta visual cambia de color con ella. |

## Remates (takedowns) atados a las vetas

Hoy `TryBackstab` acepta a cualquier enemigo a 150 uu por delante con la vida al 95 % o menos:
sale desde el primer golpe, y elige al azar entre los 10 takedowns de espada única. Los 10
duales no cuentan: no hay estilo dual en DCS y están sin anotar.

**Regla nueva.** Dos cosas escalan con las vetas: **cuándo** se permite el remate (umbral de
vida del enemigo) y **cuáles** salen (lista de índices que `GetBackstabMontages` ya recorre).

| estado | umbral de vida | remates disponibles | cámara cinematográfica |
|---|---|---|---|
| sin marcas | 25 % | 2: uno seco (10) y uno de dos golpes (07) | 0,3 |
| primera veta | 35 % | + los tres de su fuerza | 0,6 |
| segunda veta | 45 % | + los de la segunda fuerza (o los que falten si repite) | 0,6 |
| sello | 55 % | los diez | 1,0 |
| sello 2 · Corrupto | 65 % | los diez | 1,0 |
| Juicio activo | sin umbral, esos 6 s | los que haya | 1,0 |

Reparto por fuerza, medido por golpes del montage (20 sacudidas en total):

| fuerza | remates | por qué |
|---|---|---|
| Gracia | 01, 09, 10 | un solo golpe, secos (2,6–4,6 s) |
| Voluntad | 02, 05, 06, 07 | dos golpes |
| Corrupción | 03, 04, 08 | tres golpes, ensañados (4,2–5,3 s) |

- **Por qué 25 %**: la espada hace 20; en un Heraldo de 200 son 50 de vida, dos o tres golpes de
  acabar. Más abajo el remate no ahorra nada; el 95 % es un remate de un golpe y se queda solo
  como valor de pruebas del Debug HUD (`Fin_Indice`, `Fin_CamaraProbabilidad`).
- **Techo 55 %** (65 % para el Corrupto) para que ni con sello se parezca al 95 %.
- **Alternativa si el porcentaje se siente raro entre enemigos de vida distinta**: umbral en
  golpes, «vida restante ≤ N golpes del arma equipada» leyendo `Stat.Damage` del StatsManager,
  N = 2 de base y +1 por veta. Mismo coste; empezar con porcentaje.
- **Bosses fuera**: Gigante y Gabriel no aceptan remate a ningún umbral. Hoy nada lo impide
  salvo que su componente de estados rechace el Backstab; hay que dejarlo explícito.
- **Coste**: el umbral pasa de un 0,95 fijo a una variable que lee el componente de vetas, y la
  elección filtra por una lista de índices. Va en la primera sesión de montaje.

## Orden de montaje

1. `BP_DA_Vetas` (componente): sondeo cada 0,25 s de `LeerFuerza`, aplica y retira modificadores. Un día.
2. Primera veta, las tres. Todo son overrides y modificadores: una sesión, probable en la Forja con el Debug HUD.
3. Segunda veta: Juicio, Masacre y Eclipse primero (solo jugador); Silencio y Renegado tocan actores enemigos.
4. Sellos: solo cuando las dos vetas anteriores se hayan jugado.

## Estado: primera sesión montada (01/09/2026)

Hecho y verificado en PIE forzando marcas desde el GameState:

- **`BP_DA_Vetas`** (ActorComponent en `BP_Malakh_DCS`, latido cada 0,25 s como la veta visual):
  lee `TotalMarcas` y `FuerzaEnPaso(0)`/`(1)` (función nueva del GameState) y decide la primera
  veta por la fuerza de la **primera** marca. Con la secuencia 3, 1, 2 la veta es Voluntad.
- **Luz que corrige**: el parry logrado se detecta por `IsInState NewEnumerator3` del StateManager
  (no se puede sobrescribir `PlaySuccessfullParryEffects` sin perder al padre). Medido: vida
  60 → 68 → 76 con dos parries, una cura por parry, y nada con Corrupción.
- **Hambre**: con combo ≥ 3, `AddModifier` de +1,5 a `Stat.Damage` (base 10, o sea +15 %), y se
  retira al caer el combo. Medido 10 → 13 → 10 con el bonus de prueba a 3. El arma divina se
  corrompe por combo (0,12 por golpe hasta 0,5) vía `FijarCorrupcion`.
- **Pie firme**: `BP_DA_StatusEffectLogic_Knockdown` para el montage e interrumpe el estado si el
  dueño lleva la veta; `ANS_DA_TechWindow` dobla la ventana por `FactorVentanaTech` (2,0 medido).
  **El Derribo en vivo no se ha probado**: solo el flag y el factor.
- **Remates**: `TryBackstab` ya no lleva el 0,95 fijo: lee `UmbralRemate` (0,25 / 0,35 / 0,45 /
  0,55 medidos) y rechaza actores con tag `Boss` (puesto en `BP_DA_GiantBoss` y `BP_Gabriel`).
  `RematesPermitidos` medido: [9, 6] → + fuerza → los diez con tres marcas. `GetBackstabMontages`
  del FinisherLogic llama a `ElegirRemate` del jugador cuando `Fin_Indice` del Debug HUD es < 0.
- Utilidades de prueba en el componente (`DbgLeerVida`, `DbgLeerDano`, `DbgModificarVida`,
  `DbgForzarParry`, `DbgQuitarParry`): los GameplayTag no se construyen desde Python.

Aplazado a la segunda sesión: el +0,4 s de aturdido del parry (la duración vive en el asset de
Stun de DCS), el combo que tarda el doble en romperse (el retardo se fija en `MeleeAttack` de
DCS, no en el componente) y la probabilidad de cámara por veta (`Fin_CamaraProbabilidad` es una
variable del HUD regenerable y el DSL no escribe variables ajenas).

## Estado: segunda sesión montada (01/09/2026)

Segunda veta por pares, en el mismo `Latir` del componente. Verificado en PIE forzando marcas:

- **Juicio (G+G)**: tres parries logrados seguidos sin recibir daño (la cuenta se reinicia si la
  vida baja) → 6 s con +10 a `Stat.Damage` (base 10, o sea ×2) y la veta a brillo 40 por
  `FijarBrillo` de `BP_DA_MarcasVisual`. Medido: daño 10 → 20 al tercer parry, 10 a los 6 s.
  **No es crítico real**: Malakh no tiene `Stat.CritChance` ni `Stat.CritMultiplier`, así que el
  modificador de crítico se ignoraba; el doble de daño es el equivalente.
- **Eclipse (G+C)**: tras un parry, 3 s con +10 de daño. Medido 10 → 20 → 10. El destello del
  arma queda pendiente.
- **Heraldo (G+V)**: tras un parry, 3 s con `Stat.AttackSpeed.Melee` 1,0 → 1,25 (medido) y la
  regeneración de stamina ×2 por `SetRegenMultiplier` (no medida).
- **Masacre (C+C)**: con combo ≥ 4 el componente marca `MasacreActiva`, y `CanBlock` sobrescrito en
  Vigilante, Lancero, Heraldo e Inspector devuelve falso mientras dure. Ojo: la llamada a
  `TieneMasacre` tiene que ir en un `bind` con exec; inline dentro del `return` el compilador la
  poda y el bonus no existe (lo avisa como «pruned» en el log).
- **Renegado (C+V)**: `HandleHit` de `BP_DA_LanzaArrojada` aplica el daño dos veces y llama a
  `DerribarEnemigo` del jugador sobre el impactado.
- **Pie firme probado en vivo**: `DbgDerribarme` reproduce el derribo del Gigante (montage +
  estado); sin la veta el montage es `AM_DA_Knockdown`, con ella queda en `None`.
- **Silencio (V+V) sin montar**: toca `BP_CelestialRay`, `BP_DA_FlechaLluvia` y el estandarte.

## Estado: tercera sesión montada (01/09/2026)

Silencio, el destello de Eclipse y ocho de los diez sellos. Verificado en PIE forzando marcas:

- **Silencio (V+V)**: `EnSilencio(Lugar)` en el componente, radio 500 alrededor de Malakh. Medido:
  verdadero a 0 y 300 uu, falso a 900. Lo consultan el rayo celestial (no hace daño si el punto
  de impacto cae en Silencio), el aura del Inspector y del estandarte (no bonifica a enemigos
  dentro) y el `CanBlock` de los cuatro de melé. **Las flechas enemigas no se anulan**: son
  proyectiles de DCS y no se tocan.
- **Destello de Eclipse**: `BP_DA_DestelloDescarte` aparece en Malakh al activarse Eclipse; el
  actor vive menos de un segundo, así que se cuenta justo después del parry.
- **Sellos**, medidos uno a uno:
  - 1 Ascendido: Juicio dura 12 s y al entrar cura un 25 % del máximo (vida 22 → 55 con el +8 del parry).
  - 2 Corrupto: Masacre desde combo 3.
  - 3 Desatado: Silencio a cualquier distancia (verdadero a 5.000 uu).
  - 4 Eclipse Celestial: durante Juicio la guardia enemiga queda negada sin combo.
  - 5 Heraldo Libre: durante Juicio `Stat.Cost.Roll` pasa de 25 a 0 y vuelve a 25 al acabar.
  - 8 Libre Luminoso: el parry cura 16 aunque la primera veta sea Voluntad.
  - 9 Libre Oscuro: `BloqueoNegado` verdadero junto a Malakh y falso a 900 uu.
  - 10 Convergente: `VetaActiva` rota 1 → 2 → 3 cada 20 s y Luz, Hambre y Pie firme la siguen
    (medido: Hambre a los 10 s, Pie firme a los 22).
- **Sin montar**: 6 Eclipse Oscuro (el golpe tras parry con combo derriba: hace falta detectar el
  golpe que aterriza), 7 Renegado (que el arma arrojada vuelva a la ranura a los 6 s), y las curas
  por muerte en cadena del sello 2.

## Aviso de veta en el rótulo de zona (02/09/2026)

Al subir el número de marcas, el componente manda al rótulo de zona (`ShowZoneBanner` del HUD,
5 s) el nombre de lo que se acaba de abrir: «Primera veta · Hambre», «Segunda veta · Masacre»,
«Sello · Renegado». `UltimoTotal` guarda el último total visto (−1 al arrancar, para no avisar
de marcas ya ganadas al cargar); si el total baja, como al reiniciar la esfera en Yesod, se
resincroniza sin avisar y las marcas siguientes vuelven a anunciarse. Medido en PIE con las tres
subidas y con un reinicio.

## Sellos 6 y 7 (02/09/2026)

**En Fab no hay nada que sirva.** El catálogo libre solo ofrece sistemas de combate completos
(Melee Trace, Armor And Damage System, Multiplayer Combo Component) que sustituirían a DCS en vez
de engancharse a él, y la biblioteca propia no es accesible sin abrir el editor desde el
lanzador de Epic. El gancho estaba dentro de DCS.

- **Sello 6 · Eclipse Oscuro**, el golpe tras parry con combo derriba. El gancho natural era
  `PlayGetHitEffects` del enemigo, pero **es de forma evento y no se puede escribir en el hijo
  por MCP**: `add_function_graph` lo rechaza, el DSL no sabe crear el nodo de evento, y
  `add_event` lo coloca pero sigue sin poder darle cuerpo. Resuelto **desde el jugador**:
  `ProbarDerribo(Activo)` busca objetivo con `FindTarget` a 260 uu y compara su vida con la del
  latido anterior; si ha bajado, llama a `DerribarEnemigo`. El componente lo llama cada latido
  con `DebeDerribar()`, que exige sello 6, combo ≥ 4 y estar dentro de los 3 s posteriores a un
  parry. Medido en PIE: la puerta se abre al parry y se cierra sola a los 3 s. **El derribo en sí
  no se ha visto con un enemigo real**, solo la puerta y el cableado.
- **Sello 7 · Renegado**, el arma arrojada vuelve. No necesita gancho de golpe: el componente
  vigila el arma temporal del jugador por dos lectores nuevos (`LeerArmaPath` y
  `LeerMotivoSalida`, porque el DSL no crea getters de variables ajenas del jugador) y, al verla
  salir con motivo `DISCARD`, cuenta 6 s y llama a `DarArmaTemporal` con la ruta guardada. Medido
  en PIE: arrojada la lanza vuelve a la mano a los 6 s, y con otro sello no vuelve.

La cura por muerte en cadena del sello 2 quedo montada el 04/09/2026. No hay gancho de muerte:
`Kill` es del padre de DCS y tiene el mismo problema de forma que `PlayGetHitEffects`, asi que se
cuenta. `CurarCadena`, en su propio temporizador de 0,25 s para no tocar `Latir`, cuenta los
enemigos vivos a menos de `RadioCadena` (2.000) y, si el numero baja con el sello 2 y Masacre
activa, cura `CuraCadena` (10 %) de la vida maxima por cada baja. Medido en PIE con tres marcas
de Corrupcion y el combo a 4: la vida sube 50 -> 60 -> 70, diez por baja.

## Lo que hay que vigilar

- `CanBeBlocked` y `PlaySuccessfullParryEffects` son del padre `BP_CombatCharacter`; se sobrescriben en el hijo como se hizo con el Espadón, sin tocar el asset de pago.
- El parámetro `Corrupcion` solo existe en las armas sobre `M_DA_ArmaDivina` (Lanza, Trompeta). La espada de DCS no lo tiene: Hambre se ve en el arma divina y en la veta del cuerpo.
- Los números son de arranque; la Forja de Encuentros los mide.
