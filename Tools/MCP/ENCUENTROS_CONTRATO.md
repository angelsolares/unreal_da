# Contrato del emulador de encuentros — JSON ⇄ Unreal

Documento compartido entre **la sesión del emulador (HTML)** y **la sesión de Unreal**.
Si algo de aquí cambia, se cambia aquí primero y se sube el `schemaVersion`.

Estado: **v2 IMPLEMENTADA en el emulador** (2026-08-23). Los dos encuentros de
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

| arquetipo | Blueprint |
|---|---|
| `escudero_celestial` | `BP_DA_Vigilante` |
| `lancero_del_alba` | `BP_DA_Lancero` |
| `arquero_del_firmamento` | `BP_DA_Arquero` |
| *(falta nombre)* | `BP_DA_Heraldo` |
| *(falta nombre)* | `BP_DA_Inspector` |

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

**NavMesh.** Sin él los enemigos se quedan plantados: en El Claro el arquero disparó
**0 flechas en 25 segundos** exactamente por eso. Y aquí la geometría es dinámica —las
coberturas y plataformas salen del JSON—, así que un navmesh horneado una vez no las
conoce. El mapa necesita **RuntimeGeneration = Dynamic** y un volumen que lo cubra entero.
Es ajuste de proyecto, no de schema, pero conviene decidirlo antes de construir nada.

**Colisión de las coberturas.** Está bien separar `bloqueaVision` de `bloqueaPaso`, porque
la percepción de DCS traza contra el canal **Visibility**. Ojo: la barrera de la arena usa
el preset `InvisibleWall`, que **ignora Visibility** a propósito para no envenenar la
puntería. Una cobertura con `bloqueaVision: true` necesita colisión distinta.

---

## 6. Decisiones que tomó el emulador (2026-08-23)

Todo lo que el contrato no cerraba y hubo que resolver para poder implementar v2.
**Las tres primeras necesitan tu visto bueno**; el resto son mecánicas.

### 6.1 ⚠️ Los dos nombres que faltaban

| arquetipo | Blueprint | por qué |
|---|---|---|
| `portador_del_estandarte` | `BP_DA_Heraldo` | un heraldo porta el estandarte; encaja solo |
| `elite_pesado` | `BP_DA_Inspector` | **por descarte** |

«Inspector» no lee como «pesado con guardia y espadón». Si en Unreal el Inspector
es otra cosa —un enemigo que patrulla, que detecta, que investiga— esta fila está
mal y hay que cambiarla en `js/catalogo.js`. **Dímelo.**

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
