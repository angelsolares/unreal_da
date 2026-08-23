# Contrato del emulador de encuentros — JSON ⇄ Unreal

Documento compartido entre **la sesión del emulador (HTML)** y **la sesión de Unreal**.
Si algo de aquí cambia, se cambia aquí primero y se sube el `schemaVersion`.

Estado: **v2 propuesta** (v1 es el JSON de `romper-la-linea` del 2026-08-23).

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
