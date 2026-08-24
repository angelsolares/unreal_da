# Contrato del emulador de encuentros — JSON ⇄ Unreal

Documento compartido entre **la sesión del emulador (HTML)** y **la sesión de Unreal**.
Si algo de aquí cambia, se cambia aquí primero y se sube el `schemaVersion`.

Estado: **v2 IMPLEMENTADA en el emulador** (2026-08-23), y el **§6.1 cerrado en Unreal**
el mismo dia: los cinco arquetipos ya tienen Blueprint y equipo real (ver §1.2). Los dos encuentros de
`Tools/ForjaDeEncuentros/datos/encuentros/` ya están en v2, y la herramienta migra
sola los v1 que se le carguen. Lo que decidió el emulador por su cuenta —porque
este documento no lo decía— está en la **sección 6, al final**. Léela: hay cosas
que necesitan tu visto bueno.

---

## 0. Lo que fija el motor y no se negocia

| | |
|---|---|
| Unidades | **centímetros**, 1:1 con Unreal. Sin conversión. |
| Ejes | Z arriba. El suelo del mapa es **plano en z = 0**. |
| Yaw | Grados. **0 = +X**, sentido antihorario visto desde arriba. `yaw: 180` mira a −X. Solo yaw: nada de pitch ni roll. |
| Mapa | Un **nivel suelto reutilizable**, NO una Level Instance de Malkuth. Por tanto `origenMundo` siempre `{0,0,0}` y `submapa` siempre `""`. Las coordenadas del JSON son coordenadas de mundo directas. |
| Carga | El JSON lo lee **Python en el editor** (por MCP) y coloca los actores. **No hay C++** en esta POC. Cambiar de encuentro es una llamada, no reiniciar el juego. |

---

## 1. Lo que hay que AÑADIR al schema

### 1.1 Sección `jugador` — la que más falta

Sin esto el experimento no es reproducible: cargar el mismo archivo dos veces da peleas
distintas según lo que Malakh arrastrara del intento anterior. Y es justo lo que separa
la Fase A de la Fase B.

```json
"jugador": {
  "pos": { "x": -2100, "y": 0 },
  "cota": 0,
  "yaw": 0,
  "vida": 100,
  "loadout": ["espada"]
}
```

- `loadout` es la lista de armas con las que empieza. **Fase A = `["espada"]`**; la Fase B
  es cambiar esa línea. Vocabulario cerrado, igual que los arquetipos (ver 1.2).
- `vida` opcional; si falta, la que traiga el personaje por defecto.

### 1.2 Vocabulario cerrado de `arquetipo`

La herramienta emite **nombres de diseño**, nunca rutas de assets. La equivalencia con los
Blueprints vive **del lado de Unreal**, en un Data Asset. Si mañana cambia el Blueprint,
cambia la tabla y los JSON viejos siguen valiendo.

**Tabla CERRADA el 2026-08-23.** Los cinco arquetipos tienen Blueprint, y los Blueprints
tienen el equipo que dice la tabla — comprobado leyendo el `BP_EquipmentComponent` de cada uno,
no de memoria.

| arquetipo | Blueprint | equipo real | papel en combate |
|---|---|---|---|
| `escudero_celestial` | `BP_DA_Vigilante` | `DA_SteelSword` + `DA_WoodenShield` | guardia; hay que romperle la defensa |
| `lancero_del_alba` | `BP_DA_Lancero` | `DA_DA_Lanza` a dos manos, **sin escudo** | alcance; su arma es la que arrojas |
| `arquero_del_firmamento` | `BP_DA_Arquero` | `DA_ElvenBow` + flechas (hereda de `BP_ArcherAI`) | presión a distancia; obliga a moverse |
| `elite_pesado` | `BP_DA_Heraldo` | `DA_GreatAxe` a dos manos, **sin escudo** | lento y sin guardia, pero pega fuerte |
| `portador_del_estandarte` | `BP_DA_Inspector` | `DA_SteelSword` + `DA_WoodenShield` + **`BP_DA_AuraComponent`** | **aura de daño a los aliados vivos**; su valor no es el arma |

**`BP_DA_WarriorAI` no es un arquetipo.** No tiene equipo propio: es el genérico que invoca el
`BP_DA_GiantBoss`. No lo metas en la tabla.

**El aura del `portador_del_estandarte` YA FUNCIONA** (2026-08-23), y esto deroga lo que decía
antes esta sección. `BP_DA_AuraComponent`, en `/Game/DarkAngels/Blueprints/Combat/`: mientras el
portador esté vivo, **todo `BP_BaseAI` aliado dentro de su radio recibe un modificador de
`Stat.Damage`**. Al morir el portador, o al salirse del radio, se retira solo.

Dos parámetros editables por instancia: `RadioAura` (1200 por defecto) y `Bonificacion` (+15).

Medido en PIE el 2026-08-23, con el portador entre los guardianes de El Claro:

| quién | distancia | daño |
|---|---|---|
| Vigilante | 227 / 506 / 802 uu | **35** (base 20) |
| Lancero | 1143 uu | **45** (base 30) |
| Arquero | 1951 uu, fuera | **40** (base 40) |
| Vigilante | 3042 uu, fuera | **20** |
| el propio portador | 0 | **20** — se excluye a sí mismo |
| cualquiera, portador muerto | — | su base |

**Es +15 plano, no +75%.** El 75% era la lectura del Vigilante, que pega 20; al Lancero, que pega
30, el mismo +15 le sale a +50%. **El emulador tiene que sumar 15, no multiplicar por 1,75**, o
inflará justo a los que ya pegan fuerte. Y el portador no se buffa a sí mismo.

La lectura táctica se mantiene y ahora está medida: o cae el portador primero, o el resto pega
más fuerte.

**El aura ya se ve** (2026-08-23): un anillo en el suelo cuyo borde marca el radio exacto del
buff, más una luz cálida en el portador. Los dos los crea el componente al arrancar y se apagan
en la misma pasada en que muere. Lo que sigue sin existir es **el estandarte como objeto**: el
portador lleva espada y escudo, así que su papel se lee por el anillo del suelo y no por su
silueta. Eso es trabajo de arte, no de mecánica.

**Regla:** un `arquetipo` que no esté en la tabla es un error de carga, no un enemigo
silenciosamente ausente.

### 1.3 `accesos` tiene que describir una rampa, no un punto

Hoy es `{"x":1050,"y":0}`, y con eso no se puede construir nada: no dice ancho, ni
dirección, ni pendiente. Sin rampa transitable **y con navmesh encima**, los arqueros del
balcón son decorado: ni bajan, ni les pueden subir.

```json
"accesos": [
  { "desde": { "x": 1050, "y": 0 }, "hasta": { "x": 1250, "y": 0 }, "ancho": 300 }
]
```

`desde` al pie (a la cota de abajo), `hasta` arriba (a la cota de la plataforma).

### 1.4 `bounds` como rectángulo explícito

Todo lo demás del schema ya asume un rectángulo alineado a los ejes. Decirlo con min/max
quita ambigüedad y ahorra trabajo:

```json
"bounds": { "min": { "x": -2200, "y": -1700 }, "max": { "x": 2200, "y": 1700 } }
```

Un polígono de verdad (no rectangular) queda **fuera de v2**: generalizar los cuatro muros
de la arena a un polígono arbitrario es otro proyecto.

### 1.5 Enums declarados

Que estén escritos los valores válidos, para que Unreal pueda hacer un switch y fallar
fuerte con lo que no reconozca. En v2:

- `victoria.tipo`: `"eliminar-todos"` — único soportado.
- `purgePolicy`: `"purgar-todo-al-romper-sello"`
- `checkpointPolicy`: `"antes-del-trigger"`

---

## 2. Lo que hay que PRECISAR

### 2.1 Qué significa `cota` en cada sitio

Ahora mismo significa tres cosas distintas y ninguna está escrita:

| dónde | significado |
|---|---|
| `coberturas` | **base** del bloque; `altura` es lo que mide hacia arriba desde ahí |
| `plataformas` | la **superficie que se pisa** (Unreal le pone el grosor por debajo) |
| `enemigos`, `jugador` | la superficie sobre la que están de pie |

**Invariante que debe garantizar la herramienta:** la `cota` de un enemigo es 0 o coincide
con la `cota` de alguna plataforma que lo contenga. Un enemigo a media altura sin suelo
debajo se cae o se queda flotando.

### 2.2 `drop` no tiene con qué mapearse

`BP_DA_WeaponDropComponent` solo tiene `DropMainHandWeapon` y `DropOffHandWeapon`, dos
booleanos: **no existe probabilidad**. Así que `"estandar"` vs `"garantizado"` no se puede
implementar hoy. Dos salidas:

```json
"drop": { "principal": true, "secundaria": false }
```

…o quitar el campo en v2 y volver cuando el componente tenga probabilidad. Lo que **no**
vale es dejarlo como está: se ignoraría en silencio y creerías estar probando algo que no.

---

## 3. Lo que la herramienta NO debe hacer

- **No emitir rutas de assets** (`/Game/...`). Solo vocabulario de diseño.
- **No emitir rotaciones completas.** Solo `yaw`.
- **No inventar geometría que el mapa no sepa construir**: polígonos no convexos, rampas
  curvas, plataformas voladas sin acceso.
- **No asumir que los `id` son decorativos.** El emulador va a reportar resultados por
  enemigo usando esos `id`: tienen que ser únicos dentro del archivo y estables entre
  ediciones del mismo encuentro.

---

## 4. Lo que YA existe en Unreal y no hay que rehacer

`BP_DA_Arena` (`/Game/DarkAngels/Blueprints/Combat/`) ya hace, probado en juego:

- Sella al entrar el jugador, con barrera visible, sonido y objetivo en el HUD.
- **Detecta sus enemigos sola**: los `BP_BaseAI` que caigan dentro de la caja.
- Victoria por eliminar a todos → abre y devuelve el objetivo anterior del HUD.
- **Al morir el jugador, reinicia el encuentro**: lo devuelve a la entrada y repone a los
  enemigos en sus puestos. Sin esto el respawn del GameMode te manda al principio del mapa.
- Botones `SEAL ARENA` / `OPEN ARENA` / `RESTART FIGHT` en el Debug HUD, pestaña COMBAT.

Lo que le falta para casar con este contrato, y es trabajo de la sesión de Unreal:

1. **Rectángulo en vez de cuadrado**: hoy tiene un solo `RadioArena`. Hace falta `RadioX`/`RadioY`.
2. **Trigger por círculo** en un punto, en vez de la caja que cubre el interior. El del
   JSON se lee mejor: cruzas un umbral, no "estás dentro".
3. **Checkpoint explícito**, en vez de tomar la posición donde estabas al sellar.

---

## 5. El aviso que se lleva las tardes

**NavMesh — ✅ HECHO el 2026-08-23.** Sin él los enemigos se quedan plantados: en El Claro el
arquero disparó **0 flechas en 25 segundos** exactamente por eso. Y aquí la geometría es
dinámica —las coberturas y plataformas salen del JSON—, así que un navmesh horneado una vez no
las conocería.

Ya está puesto **`RuntimeGeneration = Dynamic`** en `Config/DefaultEngine.ini`, así que lo
heredará el navmesh del mapa del emulador cuando se cree. Verificado midiendo rutas con
`find_path_to_location_synchronously` contra una barrera que aparece en juego: la ruta deja de
pasar cuando la barrera se levanta y vuelve a pasar cuando se baja. **El mapa solo necesita un
`NavMeshBoundsVolume` que lo cubra entero**; no hay que hornear nada a mano.

**Colisión de las coberturas.** Está bien separar `bloqueaVision` de `bloqueaPaso`, porque
la percepción de DCS traza contra el canal **Visibility**. Ojo: la barrera de la arena usa
el preset `InvisibleWall`, que **ignora Visibility** a propósito para no envenenar la
puntería. Una cobertura con `bloqueaVision: true` necesita colisión distinta.

---

## 6. Decisiones que tomó el emulador (2026-08-23)

Todo lo que el contrato no cerraba y hubo que resolver para poder implementar v2.
**Las tres primeras necesitan tu visto bueno**; el resto son mecánicas.

### 6.1 ✅ RESUELTO — los dos nombres que faltaban

**Angel lo cerró el 2026-08-23, y ya está aplicado en Unreal.** La asignación quedó
**al revés** de lo que proponía esta sección:

| arquetipo | Blueprint | qué se hizo |
|---|---|---|
| `elite_pesado` | **`BP_DA_Heraldo`** | se le quitó la lanza y el escudo; ahora lleva `DA_GreatAxe` a dos manos |
| `portador_del_estandarte` | **`BP_DA_Inspector`** | se queda como estaba (espada + escudo); su papel es el **buff/debuff** |

El razonamiento: Heraldo e Inspector eran **duplicados** de lo que ya había. El Heraldo
llevaba la misma lanza que el Lancero más un escudo, así que en pantalla leía como
«Lancero con escudo»; y el Inspector era un clon exacto del Vigilante. Ninguno aportaba
una lectura distinta en combate, que es lo único que le importa al emulador. Convertirlos
salió casi gratis porque los chasis ya existían.

`DA_GreatAxe` ya venía con `TwoHanded = True`, así que **no hizo falta animación nueva**:
es el mismo truco que se usó con la lanza.

**Para el emulador:** `js/catalogo.js` puede apuntar ya a los dos Blueprints, y el
suplente sobra. La tabla completa está en el §1.2, con el equipo real de cada uno.

**Lo único que sigue pendiente**, y conviene tenerlo delante: el aura de buff/debuff del
`portador_del_estandarte` **no existe todavía**. Hoy pelea como un escudero. Un encuentro
cuya lectura dependa de ese buff estará midiendo algo que el juego aún no hace.

#### 6.1.b Lo que el emulador hizo con esta información (2026-08-23)

Aplicado, y de paso **medidos los cinco Blueprints** en vez de seguir estimando. La
recalibración es grande y el veredicto empeora mucho, así que conviene saber por qué.

| lo que yo tenía | lo que mide el motor |
|---|---|
| velocidades 350–420 según el arquetipo | **los cinco a 600**, mismo chasis, mismo radio 50 |
| escudero 12 de daño | **20** (`Stat.Damage` 10 + `DA_SteelSword` +10) |
| arquero 16 | **30** (+ `DA_ElvenBow` +20) |
| lancero 14 | **30** (+ `DA_DA_Lanza` +20) |
| elite con guardia 0,7 | **guardia 0** — lleva hacha a dos manos, sin escudo |
| portador sin guardia | **guardia 0,4** — lleva espada y escudo |

Dos consecuencias que no son cosméticas:

**Ya no se puede huir de nadie.** Antes solo el Lancero corría más que Malakh; medido,
**los cinco** van a 600 contra sus 400. Y el `segundosDeRetirada` del arquero, que yo
había puesto como decisión de diseño, pasa de ser un ajuste fino a ser **lo único que
hace que la arena se cierre**: sin ese tope, un arquero a 600 no se alcanza nunca.

**El techo de la espada baja de 3 enemigos a 2.** Con los números reales, «Romper la
línea» se gana el **1%** con espada sola (antes 24%) y el **2%** con armas (antes 34%).
No es que el encuentro haya empeorado: es que antes lo estaba midiendo con estadísticas
inventadas más benévolas que el juego.

**El buff del portador no se simula**, a propósito. El campo estaba declarado en la
calibración y ahora está fuera, con su razón escrita: modelar un aura que Unreal no tiene
sería medir humo, exactamente el mismo error que las probabilidades de drop del §6.2.

### 6.2 ⚠️ `drop` se resuelve como dos booleanos, y eso cuesta algo

Adoptada la opción A del §2.2: `"drop": { "principal": bool, "secundaria": bool }`.
La ranura la decide el **arma**, no el enemigo: el escudo es off-hand, todo lo
demás principal. El emulador lo mapea solo.

Lo que se pierde y conviene saber: el simulador **ya no modela** las cuatro
políticas del §8 (Guaranteed / Standard / Mercy / No Drop), porque tres de ellas
son probabilidad y el componente no la tiene. Simularlas sería medir algo que el
juego no sabe hacer. Vuelven el día que `BP_DA_WeaponDropComponent` tenga
probabilidad — y entonces esto sube a v3.

### 6.3 ⚠️ `arena.entrada` desaparece; manda `jugador.pos`

v1 tenía `arena.entrada` (dónde empieza Malakh) **y** `arena.checkpoint` (dónde
reaparece). Como v2 añade la sección `jugador`, tener las dos era decir lo mismo
dos veces. Ahora:

- `jugador.pos` — dónde arranca el encuentro. Es también desde donde se mide la
  lectura del §5.1 («¿se ve la lanza desde la puerta?»).
- `arena.checkpoint` — dónde reaparece al morir. Sigue existiendo, y sigue sin
  poder caer dentro del trigger.

Si en Unreal `BP_DA_Arena` necesita los dos puntos por separado por algún motivo,
avisa y vuelve `entrada`.

### 6.4 Coberturas y plataformas también pasan a min/max

El §1.4 solo hablaba de `bounds`, pero las cajas tenían el mismo problema: se
guardaban como polígono de cuatro puntos y **solo se usaba su bounding box**. Era
una mentira silenciosa: parecía que se podía dibujar un polígono y no era verdad.
Ahora las tres cosas se declaran igual, `{min, max}`, y la geometría interna
deriva el polígono cuando lo necesita.

### 6.5 `origenMundo` y `submapa` fuera del schema

El §0 dice que siempre valen `{0,0,0}` y `""`. Un campo que solo puede tener un
valor es ruido, así que no está en v2. El exportador conserva un `offset`
opcional, pero es una opción de la herramienta, no parte del JSON.

### 6.6 Vocabulario de `loadout`

Cerrado, como pedía el §1.1: `espada`, `lanza`, `arco`, `escudo`, `espadon`,
`estandarte`. Fase A es `["espada"]`. Además, si el loadout no incluye `espada`
salta un aviso: el PDF dice que Malakh **siempre** la conserva.

### 6.7 El invariante de cota se corrige solo, no se denuncia

El §2.1 pedía garantizar que la cota de un enemigo sea 0 o la de su plataforma.
El emulador va más lejos: al mover un enemigo, al cambiar la cota de una
plataforma o al expandir una propuesta de la IA, **reasienta** al enemigo en el
acto. Es más difícil generar un JSON inválido que uno válido. Si aun así llega
uno mal (editado a mano), `validar()` lo marca como error de carga.

### 6.8 Rampas: qué se guarda y qué se supone

`{ desde, hasta, ancho }` tal cual pedía el §1.3. Añadidos dos avisos de la
herramienta, que **no** son parte del contrato pero sí de lo que se comprueba:
ancho menor de 100 cm («no cabe un enemigo con holgura») y pendiente de más de
45° («no se sube»).

Al migrar de v1, los puntos de acceso viejos **no tenían dirección**, así que la
rampa se inventó: sube desde el punto hacia el centro de la plataforma, con largo
`max(200, cota × 1.5)` y ancho 300. Queda anotado en `notasDiseno` de cada
encuentro migrado. **Revísalas antes de construir.**

### 6.9 El convenio de yaw, verificado contra el motor

No me fié de la descripción en palabras y lo medí spawneando actores:

```
yaw  |  forward (X, Y)
  0  |  ( 1,  0)
 90  |  ( 0,  1)
180  |  (-1,  0)
270  |  ( 0, -1)
```

Es decir **`forward = (cos yaw, sin yaw)`**, que es exactamente `atan2(Δy, Δx)`.
El emulador ya usaba esa fórmula, así que **no hay espejo** entre las dos partes.
Y en Python el constructor es `unreal.Rotator(roll, pitch, yaw)` — el yaw va
tercero, no primero.

### 6.10 Dónde vive «qué hace cada enemigo»

Fichero nuevo: `Tools/ForjaDeEncuentros/datos/arquetipos.json`. Papel, cómo pelea,
cómo se le contesta, qué aporta su arma, dónde colocarlo y con qué tener cuidado
— por arquetipo. **Se lee entero en cada petición a la IA**, así que es lo que el
modelo usa para razonar al criticar o proponer variantes. Se edita a mano y no
hace falta reiniciar nada.

No está en el JSON del encuentro ni le hace falta a Unreal: es documentación de
diseño con un consumidor que resulta ser una máquina.

### 6.11 Malakh, medido del motor (2026-08-23)

Los enemigos se midieron en §6.1.b. Faltaba la otra mitad: el jugador. Siete
valores estaban estimados y **seis se han medido**. Los tres primeros cambian el
combate entero.

| valor | tenía | mide | de dónde |
|---|---|---|---|
| ataque ligero, duración | 1,50 s | **1,00 s** | `M_1H_LightAttack_01` (1,500 s a `rate_scale` 1,50) y `_02` (1,000 a 1,00) |
| ataque ligero, impacto | 0,55 s | **0,40 s** | `ANS_HitBox` a 0,494 s y 0,302 s reales |
| ataque ligero, ventana | 0,15 s | **0,117 s** | duración del mismo `ANS_HitBox` |
| ataque pesado, duración | 2,30 s | **1,21 s** | `M_1H_HeavyAttack_01` (2,300/1,90) y `_02` (1,700/1,40) |
| ataque pesado, impacto | 0,95 s | **0,53 s** | `ANS_HitBox` a 0,448 s y 0,612 s |
| esquiva, duración | 0,75 s | **0,917 s** | `M_Roll`, 1,375 s a `rate_scale` 1,50 |
| esquiva, i-frames | 0,05–0,40 | **0,107–0,459** | `ANS_Activity` llamado `IsImmortal` |
| esquiva, coste | 10 | **25** | `Stat.Cost.Roll` |
| bloqueo, reducción | 70% | **55%** | `DA_SteelSword.BlockValue = 55` |
| poción, duración | 1,60 s | **1,893 s** | `M_DrinkPotion`; la cura cae en el 1,173 |
| reacción a golpe | 0,687 s | **0,750 s** | `M_GetHitFront_Add` |
| regen de stamina | 25/s | **35/s** | `RegeneratedStats`: 1,75 cada 0,05 s, con 1 s de corte |

**El error de fondo era ignorar `rate_scale`.** Ningún montage de DCS se reproduce
a velocidad 1: el ligero va a 1,50, el pesado a 1,90, el rodillo a 1,50. Leer
`sequence_length` sin dividir por `rate_scale` alarga cada animación un 50-90%.
Si la sesión de Unreal lee tiempos de animación para cualquier otra cosa, aquí
está la trampa.

**Lo que sigue sin medir**, dicho sin adornos:

- **Alcance de la espada.** La hoja de `SM_SteelSword` mide 138,8 cm de bounds y
  sobresale 118 cm del punto de agarre — eso es medido. Falta cuánto adelanta el
  brazo en el fotograma del impacto, y eso solo sale evaluando la pose.
- **Distancia del rodillo.** Es root motion.
- **Multiplicador de daño del pesado.** El arma solo declara `Stat.Damage +10` y
  no distingue ligero de pesado: el multiplicador vive en el grafo del
  `BP_CombatComponent`, que no se lee por MCP.

**Aviso operativo — esto tira el editor.** Pedirle la pose a un `AnimMontage`
(`montage.get_anim_pose_at_time(...)`) revienta con un assert en
`AnimMontage.h:781`, **y el intérprete de Python no vuelve**: toda llamada
posterior muere con `0xC0000005` hasta reiniciar el editor. Los toolsets C++
siguen respondiendo después del golpe, así que no todo está perdido. Para root
motion, evaluar la **secuencia fuente**, nunca el montage.

**Dos correcciones a §6.1.b y a lo que este documento daba por bueno:**

1. `Stat.Block` vale **50**, no 25 — y da igual, porque DCS no lo usa para
   reducir daño. La reducción es el `BlockValue` del objeto con el que paras:
   espada 55, `DA_WoodenShield` 100. Por eso el Escudo Celestial cambia la arena
   y no solo el daño: con escudo el bloqueo frontal es **total**.
2. Malakh esprinta a **550** y los cinco enemigos corren a 600. El aviso de
   §6.1.b («no se puede huir de nadie») era aún más cierto de lo que decía: no se
   puede huir **ni esprintando**.

**Lo que esto le hace a los veredictos.** Con el Malakh real, tres enemigos en
campo abierto y separados 320 cm pasan del **12% al 98%** de victorias con la
espada sola. Los mismos tres, colocados como están en «Romper la línea» —dos
escuderos a 560 cm flanqueando el camino— se ganan el **5%**. La composición no
decide: decide la colocación. El encuentro completo de cinco sigue en el 1% con
espada sola, así que la ruta de armas sigue siendo obligatoria ahí, que es
precisamente lo que el §5.2 del PDF prohíbe.

### 6.12 La arena del juego se puso al día (2026-08-23, del lado de Unreal)

Cinco cierres en `BP_DA_Arena` y compañía, **todos medidos en PIE**, que cambian lo que
el emulador puede dar por hecho:

1. **La purga del sello YA EXISTE.** `Abrir` limpia las armas del suelo (dos barridos: uno
   inmediato y otro a los 2 s, porque el drop del último muerto cae *después* del primero) y
   llama a `PurgarTemporales` del jugador: fuera la temporal, espada base reequipada. El
   `purgePolicy: "purgar-todo-al-romper-sello"` del §1.5 ya no es aspiracional. Medido:
   victoria con la lanza en la mano → `ArmaTemporal = None`, `BP_DI_SteelSword` adjunto, 0
   drops dentro del radio.

2. **El checkpoint ya no puede caer dentro del trigger.** `TomarInstantanea` calcula
   `PuntoEntrada` empujando desde el centro por el **eje dominante** (Chebyshev) hasta
   `0.85·RadioArena + 150`: fuera de la caja `Entrada`, dentro de los muros. Ojo emulador:
   `Arena_Claro` tiene `RadioArena = 2800`, no 3000. La instantánea guarda además
   **vida, stamina y pociones** del jugador (leído: 63/100/10 con la vida bajada a propósito).

3. **`ReintentarAlMorir = False` es el default.** Al morir: la arena se abre, **repone los
   cuatro enemigos** en sus transforms iniciales (`ReponerEnemigos`), y vuelve a `Estado 0`
   — el jugador reaparece en su respawn normal y decide si reentra (re-sella al cruzar,
   verificado) o se va. Con `True`, `ReiniciarEncuentro` teleporta al punto de entrada y
   **restaura vida/stamina/pociones** de la instantánea. Es el ciclo Failed → Armed del §11.2.

4. **El Arquero suelta el arco.** `BP_DA_WeaponDropComponent` ahora lee el slot de arma a
   distancia como fallback cuando la mano principal no tiene melé válida. Medido: muere el
   Arquero → drop con `DA_ElvenBow`, recogible. Cosmética pendiente: el arco del DI es
   esquelético y el drop enseña la malla estática que encuentra (`SM_ElvenArrow`).
   Los dos booleanos del §2.2 siguen siendo dos booleanos: probabilidad sigue sin existir.

5. **El watchdog del §7.3 existe.** `VigilarArena` (0,5 s): sellada + array de enemigos
   vacío + victoria falsa → línea `WATCHDOG BP_DA_Arena` en el log y apertura de emergencia.
   Verificado vaciando el array en caliente: `Estado 1 → 2` en el siguiente tick.

### 6.13 El estandarte ya se clava (2026-08-23, del lado de Unreal)

El ataque de descarte del `portador_del_estandarte` existe: con la trompeta en la mano, la
tecla de arrojar la **clava** en vez de lanzarla. Nace `BP_DA_EstandartePlantado` — el
cuerno hincado más un aura **invertida** (−15 de `Stat.Damage` a todo `BP_BaseAI` en un
radio de 800) que **dura 15 s** y se limpia sola al expirar. Medido: testigo con 20 de
daño pasa a **5** dentro de la zona y vuelve a 20 al expirar. La ruta del §6.3 («eliminar
Portador → clavar su Estandarte para invertir la zona») ya es montable de punta a punta.

Para el emulador: el descarte de la familia `estandarte` es
`{ tipo: "zona", bonificacion: -15, radio: 800, duracion: 15 }`, y el arrojadizo de
proyectil queda **solo** para la familia `lanza` — con el hacha o la trompeta la tecla ya
no dispara lanzas fantasma.
