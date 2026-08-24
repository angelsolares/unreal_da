# Forja de Encuentros — Fases A a E

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
cargan desde `file://`. Sin instalar nada: Three.js va vendorizado y la capa de IA
se apaga sola si no está configurada.

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
| `pruebas/lectura.mjs [encuentro]` | qué se ve desde la puerta, enemigo a enemigo (§5.1) |
| `pruebas/ejes3d.mjs` | el mapeo de ejes de la vista 3D, sin navegador |
| `pruebas/variantes.mjs` | la tubería de la IA **sin gastar una llamada** |
| `pruebas/solidos.mjs` | recorre partidas enteras comprobando que nadie atraviesa un muro |

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

## Fase C: la vista 3D, y lo que la planta no puede contestar

Botón **Vista 3D** sobre el lienzo. Misma simulación, otro renderer: Three.js
vendorizado en `vendor/three/` (720 KB, sin CDN, se carga solo cuando se pide).

Cuatro cámaras:

| cámara | para qué |
|---|---|
| Órbita | repasar el trazado entero |
| **Ojos de Malakh en la entrada** | **la prueba del §5.1**, con FOV 70 como el juego |
| Tras Malakh | seguir la partida testigo en tercera persona |
| Cenital | contrastar contra la planta 2D |

Durante la reproducción, **planta y 3D enseñan lo mismo**: barra de vida sobre cada
agente, el glifo de lo que está haciendo (`!` levanta el arma, `✳` el golpe está
saliendo, `~` esquiva, `▮` bloquea, `+` bebe, `⌾` recoge arma, `×` aturdido) y un
destello de impacto — rojo si el golpe entró, azul si lo paró la guardia. Hay una
leyenda en la esquina, porque un `✳` no significa nada por sí solo. Un golpe que no
aturde no deja estado, así que el destello es la única forma de ver que a alguien le
están dando.

La silueta **es** la señal. Cada arquetipo lleva su arma con su tamaño real: la
lanza mide 3,2 m y se ve desde la puerta, el escudo va pegado al cuerpo y apenas
cambia el contorno. Eso es lo que hay que poder juzgar mirando, no leyendo la
ficha. Durante la reproducción, Malakh cambia de arma en la mano, la espada base
se guarda cuando empuña algo a dos manos, las armas caídas brillan en el suelo y
los muertos se quedan tumbados donde cayeron.

## Fase D: la capa de IA

Pestaña **IA** en el panel derecho. Es **opcional**: sin ella todo lo demás
funciona igual.

```bash
npm install openai
export OPENAI_API_KEY=...          # en PowerShell: $env:OPENAI_API_KEY="..."
node serve.mjs
```

Modelo por defecto **GPT 5.6 Sol** (`gpt-5.6-sol`). Si el identificador de la API
no es exactamente ése, se cambia sin tocar código:

```bash
export OPENAI_MODEL=el-id-correcto
```

La clave vive **solo en el proceso del servidor** (`ia.mjs`), nunca en el
navegador: una clave en el navegador es una clave publicada. El módulo se carga
de forma perezosa, así que quien no use la IA no paga la dependencia — y si falta
la clave o el paquete, la pestaña se apaga sola y dice por qué.

### Tres trabajos, y ninguno decide nada

| botón | qué hace |
|---|---|
| **Criticar** | lee el encuentro *y sus números*, y opina en el vocabulario del PDF: qué funciona, el problema más grave, si la señal del §5.1 existe, y **un** cambio concreto |
| **Proponer 3 variantes** | devuelve composiciones nuevas con la misma arena, en JSON validado por esquema |
| **Narrar** | convierte el log de la partida testigo en la "historia de combate recordable" del §15 |

### La regla: la IA propone, el simulador dispone

Una variante generada **no se enseña hasta que se ha jugado**. El flujo es:

1. El modelo devuelve una **propuesta estrecha** (composición y geometría), no un
   Encuentro completo. La arena, el sello y el checkpoint los hereda del actual:
   son decisiones de nivel, y las reglas que el PDF da por sentadas no se negocian
   con un modelo.
2. `expandirPropuesta()` la convierte en un Encuentro real, descartando lo que no
   existe (un arquetipo inventado se cae, un drop inventado baja a "estándar").
3. `validar()` + 100 partidas.
4. Se muestran **ordenadas por lo que dice el veredicto**, con su semáforo de
   nueve puertas, no por el orden en que las escupió el modelo.

Lo que ves en pantalla no es "lo que dijo el modelo", es "lo que dijo el modelo,
y esto es lo que pasa cuando se juega". Si el veredicto la tumba, se enseña
tumbada.

`pruebas/variantes.mjs` prueba toda esa tubería con respuestas de mentira —
incluidas las malas— sin gastar una llamada.

---

**La puerta nueva de la Fase C: `js/lectura.js`.** El §5.1 apuesta toda la mecánica a que la
silueta comunique la estrategia —*"Lanza larga y brillante visible desde
entrada"*— y eso nadie lo había comprobado. Ahora se mide: desde los ojos de
Malakh en la puerta, para cada enemigo, si está tapado, a qué distancia, y cuántos
grados de silueta ocupa (y qué parte de esa silueta es el arma, porque si el arma
no se distingue la señal no existe). Vive aparte de la vista 3D a propósito: así
el veredicto lo usa sin navegador y las pruebas de node lo cubren. La casilla
**Líneas desde la entrada** lo pinta en la escena: verde legible, rojo tapado.

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
| Malakh: sprint | 550 cm/s | `BP_MovementSpeedComponent` — los enemigos van a 600 |
| Ataque ligero: dura / golpea / ventana | 1,000 s / 0,40 s / 0,117 s | `M_1H_LightAttack_01` y `_02`, notify `ANS_HitBox` |
| Ataque pesado: dura / golpea / ventana | 1,212 s / 0,53 s / 0,121 s | `M_1H_HeavyAttack_01` y `_02` |
| Esquiva: dura / i-frames / cuesta | 0,917 s / 0,107–0,459 s / 25 | `M_Roll`, notify `IsImmortal`, `Stat.Cost.Roll` |
| Alcance: ligero / pesado | 179 cm / 174 cm | pose evaluada a lo largo del `ANS_HitBox` |
| Bloqueo con espada sola | −55% | `DA_SteelSword.BlockValue` (el escudo vale 100) |
| Parry / reacción a golpe | 0,700 s / 0,750 s | `M_1H_Parry`, `M_GetHitFront_Add` |
| Poción: cura / te clava | 25 HP / 1,893 s | `DA_HealthPotion`, `M_DrinkPotion` |
| Stamina: regen / retraso | 35/s / 1 s | `RegeneratedStats` |
| Lancero: vida / velocidad | 100 / 600 cm/s | `BP_DA_Lancero` |
| Lancero: ataque | 2,000 s | `M_AI_LightAttack_01` |

**La trampa que se llevó por delante la mitad de estos números: `rate_scale`.**
Ningún montage de DCS se reproduce a velocidad 1. El ligero va a 1,50, el pesado a
1,90, el rodillo a 1,50. Leer `sequence_length` sin dividir por `rate_scale` alarga
cada animación entre un 50% y un 90%, y eso es exactamente lo que hacía la
calibración anterior. Los tiempos de arriba ya están en segundos reales.

**Y los AnimNotify sí se leen**: `unreal.AnimationLibrary.get_animation_notify_events`.
Lo de que eran "propiedad protegida" era falso — estaba buscando la propiedad en el
asset en vez de la librería.

**El alcance sí se puede medir**, y no hace falta PIE. La receta, que sirve para
cualquier arma:

1. `AnimMontageService.list_anim_segments(montage, 0)` da la **secuencia** fuente y
   su `anim_start_pos` — los montages pesados arrancan en 0,100, así que el tiempo
   del notify hay que desplazarlo antes de evaluar nada.
2. El `ANS_HitBox` es un notify **de estado**: tiene duración. El alcance es el
   máximo del barrido, no el valor del instante en que se dispara. Al disparar, la
   punta de la espada está a 50 cm; el pico llega 0,1 s después, a 180.
3. `secuencia.get_anim_pose_at_time(t, ...)` da la pose. Se cuelga la hoja del
   socket `sword_use` (hueso `hand_r`) y se mide del hueso **`root`** al extremo
   más lejano — del root, no del origen del componente, porque la cápsula sigue al
   root motion y estas animaciones avanzan 89 cm.

> **Dos trampas que cuestan una tarde.** Pedirle la pose a un `AnimMontage` en vez
> de a la secuencia revienta el editor con un assert y el intérprete de Python **no
> vuelve** hasta reiniciar. Y en Python el constructor es
> `unreal.Rotator(roll, pitch, yaw)`: poner el yaw primero te da un pitch, y la
> espada acaba apuntando bajo tierra con una cifra creíble.

**Sin medir todavía**: la distancia del rodillo (root motion del montage de roll) y
el multiplicador de daño del pesado, que vive en el grafo del `BP_CombatComponent`.

---

## ⚠️ Las cifras de las tres secciones siguientes son de ANTES de medir

El 2026-08-23 se midió el motor en dos tandas. Primero los cinco enemigos, y
cambiaron **a peor**: corren todos a 600 (no 350–420), el arquero pega 30 (no 16),
el lancero 30 (no 14), el escudero 20 (no 12), el Heraldo **no** tiene guardia y el
Inspector **sí**. Después Malakh, y cambió **a mejor**: su ataque ligero dura 1,0 s
y no 1,5, y el pesado 1,21 y no 2,3 — un 50% y un 90% más de daño por segundo del
que este simulador le suponía. A cambio, rodar le cuesta 25 de stamina y no 10
(cuatro esquivas y se queda seco), bloquear con la espada sola le quita el 55% y no
el 70%, y beber le clava 1,9 s.

**Y una tercera pasada el 24/08: los enemigos otra vez, esta vez de la pose.** Tres
premisas del diseño no sobrevivieron:

- **La lanza no da alcance.** 245 cm contra los 241 de la espada. Cuatro centímetros.
  Mide 175 de largo, pero se agarra a un tercio del asta. Y los cuatro de melé
  **comparten animación**: no existe animación de lanza ni de hacha.
- **El Arquero no tiene límite de alcance.** Gravedad 0, 4 s de vida, 3500 cm/s →
  14 000 cm. Dispara desde donde sea con tal de verte.
- **Bloquean cuatro de los cinco**, no uno. En DCS se bloquea con el arma: escudo 100%,
  lanza y hacha 75%. Lo de «sin escudo no bloquea» era invención mía.

**Dónde queda el techo con todo medido:**

| | espada sola gana |
|---|---|
| 2 enemigos | **95%** |
| 3 enemigos en campo abierto | **0%** |
| «Romper la línea» entera, 5 enemigos | **0%**, 200 muertes de 200 |

El techo son **dos enemigos**, y la caída del tercero es un acantilado, no una
pendiente. Lo que la herramienta existía para responder ya está respondido, y la
respuesta es que ese encuentro no cumple el §5.2.

Lo de abajo sigue valiendo como razonamiento y como historia de qué se rompió y por
qué, pero las cifras concretas hay que releerlas de `datos/calibracion.json` y de una
simulación nueva. El detalle está en los §6.1.b, §6.11, §6.12 y §6.13 del contrato.

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

## Lo que salió en la Fase C

**8. «Romper la línea» sí se lee; «Cadena perfecta» no.** Desde la puerta:

| encuentro | qué se ve |
|---|---|
| Romper la línea | las 5 siluetas, la más pequeña a 3,1° |
| Cadena perfecta | el Arquero y el Elite **tapados** por las columnas |

En «Cadena perfecta» ninguno de los dos tapados es llave táctica, así que la
puerta no salta — pero significa que el jugador entra sin saber que al fondo hay
un Elite. Puede ser lo que quieres (una emboscada) o un descuido; el documento
no lo dice, y ahora al menos la decisión es consciente.

**9. La lanza se lee, el escudo no.** El Lancero de «Cadena perfecta» ocupa 18,5°
de silueta y el **72% de eso es la lanza**. El Escudero ocupa 5,1° y solo el 47%
es el escudo. La señal «ese lleva una herramienta» funciona con las armas largas
y es casi nula con el escudo: si quieres que el jugador vea de lejos que ahí hay
un escudo que coger, no bastará la silueta — hará falta color, brillo o VFX.

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

Y una advertencia sobre la Fase C: **el límite de lectura (40 m) y el ancho que
añade cada arma a la silueta son suposiciones de diseño**, no medidas. Están
declaradas en `js/lectura.js`. El día que haya una arena real en Unreal, esos dos
números se calibran con una captura y el veredicto se vuelve mucho más fiable.

---

## Fase E: el puente con Unreal

Pestaña **Unreal**. El servidor de la Forja habla con el MCP del editor por
JSON-RPC en `127.0.0.1:8000`; el navegador no toca el editor directamente.

**Exportar** coloca el encuentro en el nivel abierto: los enemigos con su
Blueprint, el sello del §7 como `BlockingVolume` por cada lado del perímetro, y
`TargetPoint` en entrada, trigger y checkpoint. Todo va etiquetado `Forja` y
`Forja:<id>`, así que volver a exportar limpia lo suyo y no toca nada más.

**Leer lo que hay en el editor** trae de vuelta las posiciones y las compara con
el JSON: te dice cuáles se han movido y cuánto, y ofrece traer esos cambios al
encuentro. Ese es el bucle que cierra la fase — colocar a ojo en Unreal y volver
a simular.

### Tres decisiones que vienen de haberse quemado

**Esto no cambia de nivel.** La primera versión creaba un nivel propio con
`new_level`. Tras esa llamada el editor se queda sin mundo unos segundos y parece
roto — no lo está, pero el diagnóstico equivocado casi lleva a "arreglarlo" con un
`load_level`, que en este proyecto sí tumba el editor de verdad. Ahora abres tú el
nivel y la herramienta coloca ahí.

**Malkuth Master y los `_Sub` están protegidos.** Sin marcar la casilla de
confirmar, la exportación se niega. Volcarle un encuentro encima por descuido sería
mucho más caro de deshacer que de evitar.

**Todo lo que se escribe se vuelve a leer.** El editor devuelve éxito en llamadas
que no han hecho nada, así que el informe compara lo pedido con lo que el editor
dice tener, coordenada a coordenada. En la prueba real: 12 actores, 0 desviados, e
ida y vuelta exacta.

### Lo que hay que saber antes de usarlo

- **El offset del submapa no es opcional.** Dentro de un `_Sub` los actores van en
  coordenadas del submapa y la Level Instance les suma su transform. Exportar con
  offset 0 a un `_Sub` manda el encuentro a kilómetros de donde toca.
- **Los cinco arquetipos ya tienen Blueprint propio** (`BP_DA_Vigilante`,
  `BP_DA_Lancero`, `BP_DA_Arquero`, `BP_DA_Heraldo`, `BP_DA_Inspector`), cerrado en
  el §1.2 del contrato. Ya no hay suplentes. **El aura del Inspector también existe
  ya** (`BP_DA_AuraComponent`, +15 de daño a cada aliado a menos de 1200 cm mientras
  viva) y el simulador la aplica. Lo que le falta es efecto visual: el jugador sufre
  el buff sin ver de dónde viene.
- **El nivel no se guarda.** Eso lo decides tú después de mirarlo.

---

## Lo que falta

- **Siluetas reales en la 3D.** `ThreeJSPOC/` ya tiene los GLB de Malakh, el
  Arcángel y las armas. Los primitivos bastan para juzgar posición y oclusión,
  pero para juzgar *lectura* de silueta el modelo real diría más.


La calibración está cerrada por los dos lados —los cinco enemigos y Malakh, medidos
del motor el 23 y el 24/08/2026— salvo dos cosas: la distancia del rodillo y el
multiplicador de daño del ataque pesado. Ninguna de las dos mueve un veredicto por
sí sola, así que no corre prisa.
