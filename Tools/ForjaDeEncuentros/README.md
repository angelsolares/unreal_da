# Forja de Encuentros — Fases A y B

Banco de pruebas para los encuentros de Malkuth, según
`Dark_Angels_Divine_Weapon_Corruption_Combat_Loop_v2.pdf`.

**No forma parte del juego.** Es una herramienta externa: HTML + JS sin dependencias.

Existe para contestar con números la afirmación del §5.2 del PDF, que hasta ahora
nadie había medido:

> la ruta táctica ideal debe reducir tiempo, riesgo o recursos, **pero nunca ser requisito**

---

## Arrancar

```bash
node Tools/ForjaDeEncuentros/serve.mjs
```

Y abrir `http://localhost:5175`. Hace falta el servidor porque los módulos ES no
cargan desde `file://`.

Sin navegador, desde la línea de comandos:

```bash
node Tools/ForjaDeEncuentros/pruebas/humo.mjs
```

| script | para qué |
|---|---|
| `pruebas/humo.mjs [encuentro]` | lote completo + veredicto. Comprueba también el determinismo. |
| `pruebas/escala.mjs` | ¿cuántos enemigos aguanta la espada, y cuánto cambia con armas? |
| `pruebas/lanza.mjs` | composiciones elegidas para que **sí** se recoja cada arma |
| `pruebas/diag.mjs` | techo de la espada y daño necesario para este encuentro |
| `pruebas/traza.mjs [semilla] [politica]` | una sola partida, evento a evento |
| `pruebas/atasco.mjs [politica]` | busca la primera partida que agota el tiempo y la disecciona |

Encuentros incluidos: `romper-la-linea` (§6.1) y `cadena-perfecta` (§6.5).

---

## Qué hay montado (Fase A)

**Esquema `Encuentro`** (`js/esquema.js`) — el contrato con Unreal. Los nombres de
campo son los que tendrá el Data Asset del "Encounter Definition" (§11.1), para que
exportar sea un volcado y no una traducción. Todo en **centímetros**, con origen
local al encuentro; el offset de la Level Instance se suma al exportar.

**Editor 2D en planta** — arena, coberturas con altura, plataformas con cota y
accesos, enemigos con anillos de alcance y conos de visión. Dos capas que son el
§5.1 hecho imagen: **mapa de presión** (dónde castigan los arqueros, con línea de
visión real) y **líneas de visión** desde el seleccionado.

**Simulador determinista** (`js/sim.js`) — tick fijo de 1/30 s, RNG sembrada,
sin render. 800 partidas en ~3 s. Modela: acercamiento con rodeo de obstáculos,
compromiso de animación, ventanas activas, esquiva con i-frames, bloqueo con coste
de stamina y guard break, aguante/stagger, pociones, proyectiles con vuelo y
absorción por cobertura, cotas con acceso por rampa.

**Cinco políticas** (`js/politicas.js`). Las dos que importan son la comparación
del §5.2:

| política | qué es |
|---|---|
| `cercano` | espada sola, sin tocar el suelo. **La puerta anti-soft-lock.** |
| `guionizada` | espada sola, tu orden. Aísla cuánto aporta el orden sin armas. |
| `ventaja` | tu orden + recoge armas + las sacrifica. **La ruta que el PDF quiere.** |
| `codicioso` | el más cercano, y recoge todo lo que ve. |
| `aleatoria` | orden distinto por semilla. |

**Panel de veredicto** (`js/lote.js`) — ocho puertas, cada una referenciada a su
sección del PDF. Cuando la de "ganable" se pone roja, `js/diagnostico.js` calcula
el **techo de la espada** y busca por bisección el daño que haría falta.

## Fase B: el ciclo del arma temporal

`js/armas.js` implementa las tres reglas que no se negocian (§3, §4.1 y la REGLA
DE SEAL BREAK): la espada base nunca desaparece, el swap es irreversible, y **no
hay durabilidad** — un arma solo termina por swap, descarte, agotar su recurso
natural o el seal break. La corrupción visual no se modela: es cosmética y no toca
la vida útil.

`datos/armas.json` define las cinco familias del §4. Es **diseño, no medida**, y
por eso vive aparte de `calibracion.json`. Cada familia se diferencia por alcance
y ritmo, no por números de daño: la lanza vale 340 cm frente a los 180 de la
espada, el espadón ignora la guardia y pega a varios, el escudo cambia cómo se
navega la arena.

Modelado: drops con TTL y política por enemigo (garantizado / estándar / piedad /
ninguno), recogida con ventana de vulnerabilidad, swap irreversible con purga del
off-hand ante armas a dos manos, munición del arco, los cinco ataques de descarte
(proyectil, AoE, impacto y zona), bloqueo mejorado del escudo que además para
flechas, y purga total al romper el sello.

**Calibración** (`datos/calibracion.json`) — cada valor lleva su procedencia:
`medido`, `parcial` o `ESTIMADO`. La interfaz lo enseña con una etiqueta de color.

---

## Lo medido en el editor (23/08/2026)

| valor | número | de dónde |
|---|---|---|
| Malakh: vida / stamina | 100 / 100 | `BP_Malakh_DCS` → StatsManager |
| Malakh: velocidad | 400 cm/s | `CharMoveComp.MaxWalkSpeed` |
| Malakh: cápsula / giro | r 42 / 540°/s | `CollisionCylinder`, `RotationRate` |
| Malakh: daño por golpe | 20 | `Stat.Damage` 10 + `DA_SteelSword` +10 |
| Ataque ligero / pesado | 1,500 s / 2,300 s | `M_1H_LightAttack_01`, `M_1H_HeavyAttack_01` |
| Parry / reacción a golpe | 1,082 s / 0,687 s | `Anim_1HS_Parry`, `Anim_1HS_GetHitFront_Add` |
| Poción | 25 HP | `DA_HealthPotion.value` |
| Lancero: vida / velocidad | 100 / 600 cm/s | `BP_DA_Lancero` |
| Lancero: ataque | 2,000 s | `M_AI_LightAttack_01` |

**Sin medir todavía** (marcado en la interfaz): las ventanas activas dentro de cada
montage —los AnimNotify son propiedad protegida desde Python, hay que leerlos en
PIE—, el alcance real de las trazas de arma, y la esquiva entera (duración,
distancia, i-frames).

---

## Lo que salió (y no es cómodo)

**1. El Lancero corre a 600 y Malakh a 400. Los dos números están medidos.**
De un Lancero no se puede huir jamás. Es herencia de DCS; conviene confirmar que
es la decisión que quieres.

**2. Con los números actuales, el techo de la espada sola son ~2-3 enemigos.**

| composición | victorias | tiempo |
|---|---|---|
| 1 Escudero | 100% | 13,7 s |
| 2 Escuderos | 100% | 30,9 s |
| 2 Escuderos + Lancero | 72% | 66,5 s |
| + 1 Arquero | 0% | — |

Las recetas del §6 del PDF piden **cinco**. "Romper la línea" se gana el **13%** de
las veces con espada sola, así que hoy incumple el criterio de aceptación del §12
("un encounter de prueba… sigue siendo ganable sólo con espada").

**3. Y no se arregla con daño.** La bisección dice que ni con 120 de daño por golpe
—seis veces el actual— pasa la puerta, ni bajando la vida enemiga al 30%. El
problema no es el DPS: es que tres o más enemigos cuerpo a cuerpo no dejan hueco
para comprometer 1,5 s de animación, y los arqueros del balcón castigan el traslado.

Las palancas que sí mueven la aguja, por orden de coste:

- **menos enemigos simultáneos** — escalonar la entrada, o hacer que los arqueros
  tarden en tener línea de tiro
- **más pociones** (`malakh.pocion.cantidad`) — la más barata de todas
- **geometría** — cobertura en el trayecto al balcón, o un segundo acceso
- **enfriamientos enemigos más largos** — `recarga` por arquetipo

---

## Lo que salió en la Fase B

**4. Las armas temporales SÍ pagan, y bastante.** En "Romper la línea":

| política | gana | tiempo | daño | armas/partida |
|---|---|---|---|---|
| Espada · el más cercano | 23% | 119,6 s | 176 | 0 |
| Espada · tu orden | 31% | 123,8 s | 174 | 0 |
| **Ruta de ventaja** | **44%** | 118,2 s | 172 | 2,43 |

+21 puntos de victoria solo por recoger lo que sueltan. La mecánica del PDF se
sostiene: la puerta "las armas temporales pagan" sale **verde**.

**5. Pero la lanza casi no se usa como lanza.** El reparto de daño de la ruta de
ventaja es 100% espada base y 0% lanza, con 0,81 descartes por partida. Es decir:
la coge y la tira casi inmediatamente. Eso es fiel a la cadena del §6.5 —
*"Lanza → arrojar Lanza al Arquero"*— pero significa que **el moveset de melé de
la lanza no está aportando nada**. Y hay una consecuencia dura: el arrojado hace
65 y un Arquero tiene 100 de vida, así que **la cadena del PDF no resuelve al
arquero**: lo deja a 35 y sin lanza.

Donde la lanza sí paga como arma es cuando no hay a quién tirársela:

| composición | Δtiempo con lanza |
|---|---|
| 2 Lanceros (cae uno → lanza) | **−23%** |
| Lancero + Escudero | −5% |
| Lancero + Arquero | −3% |

**6. Poner el arma anti-guardia en el enemigo con guardia es circular.** El
espadón del Elite se recoge 0,01 veces por partida: para matar al Elite haría
falta el espadón, que solo suelta el Elite. El §6.4 ya lo resuelve —dice *"eliminar
Elite **secundario**/portador de arma pesada"*— y conviene respetarlo: el guard
break tiene que venir de otro cuerpo.

**7. Un arquero que retrocede sin límite hace tablas eternas.** Su retroceso y las
esquivas de Malakh se cancelaban y la arena no se cerraba nunca. Está resuelto con
`segundosDeRetirada: 3` en la calibración, marcado como decisión de diseño: **si al
implementarlo en DCS el arquero puede huir sin fin, ese encuentro no se cerrará.**

---

## Lo que este modelo NO sabe

Importa tanto como lo que sabe, porque **todo tira del veredicto hacia abajo**:
la puerta de "ganable" es un **suelo**, no un techo.

- Malakh no usa la cobertura contra los arqueros: cruza a pecho descubierto.
- No hay parry, que es la opción de más habilidad de DCS.
- No arrastra enemigos a un cuello de botella para pelearlos de uno en uno.
- La IA enemiga no flanquea ni se coordina.
- La fórmula de armadura está desactivada (`reglas.factorArmadura: 0`) porque no se
  ha medido la de DCS.

Si aquí sale verde, en manos de un jugador decente sale más verde.

---

Y una más, que la Fase B añade: **ningún número de `armas.json` está medido.** Son
la primera propuesta de diseño. El arrojado de lanza es lo único que ya existe en
el proyecto, y sus números reales deberían sustituir a los de aquí.

---

## Lo que falta

- **Fase C** — vista 3D con Three.js. Hay terreno hecho: `ThreeJSPOC/` ya tiene los
  GLB de Malakh, el Arcángel y las armas, así que se puede pasar de primitivos a
  siluetas reales y comprobar la señal "Silueta / arma" del §5.1 desde la entrada.
- **Fase D** — capa de IA: crítico de encuentro, generador de variantes con JSON
  validado por esquema, narrador de la partida. Con proxy local para la clave.
- **Fase E** — export/import por MCP: volcar el JSON a actores y Blocking Volumes,
  e importar la geometría real de Malkuth para planificar sobre suelo verdadero.

Antes de la Fase B conviene **cerrar la calibración en PIE**: las ventanas activas,
el alcance de las trazas y la esquiva. Son los tres números de los que más depende
el veredicto y los tres que hoy están estimados.
