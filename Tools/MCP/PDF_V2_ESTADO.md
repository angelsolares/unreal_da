# Estado contra el PDF v2 — *Divine Weapon Corruption + Encounter Combat Loop*

Auditoría del 2026-08-24 contra
`Dark_Angels_Divine_Weapon_Corruption_Combat_Loop_v2.pdf` (14 páginas),
**repasada frase a frase el 2026-08-26** — ese repaso está en la sección siguiente y es lo
primero que hay que leer: corrige siete cosas que este documento daba por donde no estaban.

**Cómo se hizo:** lo marcado ✅ VERIFICADO se comprobó **en PIE o leyendo el asset**, no las
notas. El resto se leyó del código del generador y de los Blueprints. Las notas de traspaso
ya se equivocaron una vez este mes afirmando cosas que el motor desmentía, así que aquí solo
vale lo medido.

**Titular:** de las 13 fases y bloques del PDF, **el bucle de arena está entero**, **el ciclo
de arma temporal también** —las cuatro salidas del §3, incluida la de agotar el recurso
natural— y **las cinco recetas del §6 están montadas y exportadas**. **Los doce criterios de
aceptación del §12 están en verde**, aunque uno de ellos esté medido y no jugado.

**Desde el 27/08 no queda NADA del PDF por construir**: el §9 y el §10 se cerraron esa noche
(la sección siguiente) y las dos señales lógicas del §5.1 también. Lo que queda es **jugar los
cinco niveles**, tres divergencias que son decisiones de Angel, y dos opcionales que el propio
PDF marca como tales.

---

## Puesta al día del 2026-08-27: los tres flecos, cerrados y probados en PIE

Los tres bloques que quedaban «en corto», hechos en una sesión nocturna y VERIFICADOS en
juego (fotos en la sesión):

- **§9, el destello del descarte**: `BP_DA_DestelloDescarte`, un actor efímero (0,8 s) que
  `ArrojarLanza` — el despachador común de las cinco familias — spawnea a los pies de Malakh
  antes de enrutar el montaje: disco celestial en expansión (el material del pilar) + pulso
  de luz azul, un solo latido. Probado arrojando la Lanza.
- **§10, el resto del Debug HUD**: pestaña **ARENA** nueva (novena; la rejilla de pestañas
  pasó a 5 por fila) con el watchdog EN PANTALLA —estado del sello, oleada actual/máx,
  vivos/por venir/válidos y un veredicto que es LA MISMA condición de apertura de emergencia
  de `VigilarArena`—, la **cadena táctica** (una línea por enemigo: oleada + nombre +
  `[MUERTO]`/`*DROP GARANTIZADO*`, calculada de lo que la arena ya sabe: sus oleadas y las
  políticas de drop del §8) y el botón **HIGHLIGHT GUARANTEED DROPS** (esferas de debug 4 s).
  Y WEAPON pasa de 4 a 6 filas: **FLECHAS** (la cuenta real) y **ENEMIGO DE ORIGEN** — la
  nota «el pickup vive en DCS» era falsa desde que existe `BP_DA_DroppedWeapon`, y ahora
  `DropOne` anota el dueño, el arma caída lo lleva, y `CanjearTemporal` se lo pasa al
  jugador. Verificado con una recogida real: `Forja_lancero_del_alba_lancero_de_la_linea`.
- **§5.1, las dos señales lógicas**: el salto atrás de los Arqueros y el arranque del aura —
  el detalle en su sección, incluida la corrección del «450» y la trampa de la traza de
  suelo que tiró a los dos arqueros del balcón en la primera pasada.

**Tres trampas nuevas de las herramientas, pagadas y documentadas** (en las memorias y en
las cabeceras de los scripts): el borrado del asset del HUD miente en TODAS las vías (la cura
es borrar el `.uasset` a disco con el editor cerrado y regenerar sobre el hueco); un nodo de
interfaz con exec (`IsAlive`) dentro de una expresión queda SIN ejecutar y devuelve false sin
que la relectura lo delate; y al crear llamadas por cirugía, el candidato ajeno lleva su
Target LLAMADO `self` pero tipado de otra clase — la firma del propio es `Self Object
Reference`.

Herramientas nuevas: `aura_arranque.py`, `jugador_seniales.py`, `arma_origen.py`,
`descarte_destello.py` (+`_crear`), `arena_hud.py`, y el generador del HUD con la pestaña.

---

## Puesta al día del 2026-08-26 (tarde): repaso frase a frase contra el PDF

Se releyó el PDF **entero, las 14 páginas** y se comprobó cada afirmación contra el motor y
los assets, no contra estas notas. Salieron tres huecos que este documento no listaba y cuatro
cosas que daba por pendientes y ya estaban. Lo verificado ese día lleva la marca 🔬.

**Lo que se destapó:**

1. ~~**§12 criterio 1: falta la cuarta cláusula.**~~ — **CERRADO el 26/08.** El PDF pide volver
   a la espada cuando la temporal *«se cambia, se sacrifica, **agota su recurso natural** o es
   purgada»*, y este documento había reescrito el criterio sin la tercera. 🔬 El `EventGraph`
   del jugador son 16 nodos y **ninguno miraba las flechas**: con el arco a cero te quedabas
   con un arco inútil hasta cambiar de arma o romper el sello — que es justo la trampa que el
   §5.2 no quiere («cualquier encuentro se completa sin depender de un drop»).

   Hecho en `Tools/MCP/arma_sin_municion.py`. **Un temporizador que corre sólo mientras llevas
   un arma temporal**: `SustituirArmaTemporal` —el embudo único del canje— arranca
   `VigilarMunicion` cada 0,5 s, y la función se apaga sola en cuanto no hay arma o en cuanto
   acaba de devolver la espada. En el Tick sería al revés: pagarlo siempre para usarlo casi
   nunca. El arma se clasifica por `GetObjectName` = `DA_ElvenBow`, el mismo idioma con el que
   `ArrojarLanza` ya elige el montaje de descarte de cada familia.

   **Motivo de salida nuevo: `AMMO OUT`.** Son cuatro y ya salen en la pestaña WEAPON sin
   tocar el HUD.

   ✅ **PROBADO EN PIE** los tres casos (`arma_sin_municion_probar.py`, cinco pasos):

   | caso | resultado |
   |---|---|
   | arco con 12 flechas, 11,7 s | sigue en la mano — no dispara de más |
   | el carcaj a 0 | `arma=''`, `motivo='AMMO OUT'`, y `BP_DI_SteelSword_C` en la mano |
   | con MUNICIÓN INFINITA puesta | sigue en la mano — el debug no te desarma |
   | segundo arco tras el primero | vuelve a caer: el vigilante se rearma |

   **Y tres decisiones que van dentro:** el carcaj **no** se toca (las flechas son equipo base,
   no del arco robado); con munición infinita no dispara (es un botón de debug, y su razón de
   ser es la contraria); y **un arco recogido con cero flechas se cae solo a los 0,5 s**, que
   no es efecto colateral sino lo correcto — un arco sin munición es exactamente la trampa que
   el §5.2 prohíbe, y así el drop nunca te deja peor que antes de tocarlo.
2. **§9 «Arma disponible»** — **el brillo, hecho el 26/08; falta el sonido.**

   **Y antes, una corrección de este mismo documento:** el 26/08 dije aquí que «no existe
   ningún feedback» porque miré `BP_DA_WeaponDropComponent` —el componente que *suelta* el
   arma— en vez de `BP_DA_DroppedWeapon`, que es el arma soltada. **El componente no tiene ni
   un nodo de VFX y eso era cierto; el actor sí.** Ya había un `PointLightComponent` (`Luz`) y
   un `PulsarLuz` latiéndole la intensidad en el Tick. Lo que no había era color —salía
   blanca— ni forma de verla de lejos: una luz puntual se apaga con la distancia.

   Montado en `Tools/MCP/arma_pilar_luz.py`: un **pilar de luz celestial** que sale del arma,
   1.200 uu de alto (unos 6,7 Malakhs), con `M_DA_HazLuz` —el mismo haz aditivo que usan los
   orbes de las Sefirot— a través de `MI_DA_PilarArma`. Y la `Luz` que ya estaba pasa a azul
   (0.20, 0.50, 1.0) con 900 de atenuación: el pilar te dice **dónde** desde el otro lado de
   la arena, la luz te dice **qué** cuando llegas. Un solo latido para los dos.

   ✅ **PROBADO EN PIE**, jugando *romper-la-linea*: se sella la arena, cae el Lancero y su
   Lanza del Alba queda bajo el haz. Legible a 25 m.

   **Tres cosas que sólo se vieron jugando, y por eso hay que jugar:**

   - **Salía torcido.** El arma cae con física y al posarse `Posar` le pasa al ACTOR la
     rotación con la que quedó el mesh, así que cualquier hijo del root hereda el tumbo:
     medido, arma en (−2354, −156, 115) y su pilar en (−2284, 388, **−127**), metido en el
     suelo. Ahora el transform lo fija `PulsarLuz` en coordenadas de mundo.
   - **Salía blanco.** `M_DA_HazLuz` es aditivo: con `Brillo 3` satura los tres canales y el
     azul celeste acaba siendo un tubo de neón. Con 1,1 sobrevive.
   - **Salía de un extremo del arma, y era un tubo de plástico.** Estaba centrado en el
     pivote —que en las armas de DCS está en la empuñadura— y era un cilindro cerrado, con su
     tapa recortada contra el cielo. Ahora se centra en el **centro de la caja del mesh** y
     toma de diámetro su lado mayor (la lanza pide 171 cm), y es un **cono**: la base envuelve
     el arma y se afila hacia arriba, que es como se lee un haz.

   **El sonido, hecho el mismo día.** `SC_DA_ArmaDisponible`, un SoundCue —no un MetaSound:
   esos matan el editor en este proyecto— que se dispara al final de `MontarPilar`, junto al
   brillo, porque los dos anuncian lo mismo y separarlos sería que un día uno suene y el otro
   no. **Dos capas, porque en el proyecto no hay ningún sonido celestial**: se listaron los 151
   SoundWaves de `/Game` que no son de DCS y son ambientes de pueblo, pasos, fuego y truenos.
   `WAV_UnsheathSword` subido de tono dice **arma**; `WAV_PotionHeal` bajado y flojo dice
   **celestial**. Con su atenuación (radio 2.500, caída 6.000) para que diga *dónde*.
   Cambiarlo el día que haya un campanazo de verdad es tocar dos rutas en
   `arma_sonido_disponible.py`: ni el grafo del cue ni el blueprint se enteran.

   **Y una trampa que costó el editor entero:** un `SoundNodeMixer` guarda un array
   `InputVolume` con **una entrada por hijo**. Dejarlo vacío no da ningún error — el asset se
   crea, se guarda y se relee perfecto—, y a la primera vez que el cue **suena** el motor
   indexa `InputVolume[0]` sobre un array de cero y se lleva el editor por delante
   (`Assertion failed: (Index >= 0) & (Index < ArrayNum)`). Pasó al matar al Lancero en PIE.
   Sin pérdida, porque estaba todo guardado, pero la lección es que **un SoundCue mal formado
   no se detecta releyéndolo: se detecta sonando.**

   ✅ Con el arreglo, la misma prueba en PIE: el arma cae, `MontarPilar` llega hasta el final
   —o sea que el `PlaySoundAtLocation` corrió—, el cue está cargado (2,50 s) y el editor sigue
   en pie. **Lo que no puedo hacer yo es oírlo**: eso es de Angel.

   **Lo que falta del §9:** sólo el **VFX del descarte**.
3. ~~**§11.3 snapshot mínimo: 4 de 8.**~~ — **6 de 8, cerrado el 26/08.** El agujero era que
   `TomarInstantanea` guardaba vida, stamina, pociones, posición de entrada y transforms de
   los enemigos, pero **no las flechas** — y el carcaj de 30 es equipo base, así que era el
   único recurso del jugador que se filtraba entre intentos: morir con 8 y reintentar te metía
   otra vez con 8. Hecho en `Tools/MCP/arena_flechas.py`.

   ✅ **PROBADO EN PIE** sobre `L_Forja_romper-la-linea` (`arena_flechas_probar.py`):
   30 de partida → puestas a 17 → `FlechasAlSellar = 17` → gastadas a 3 → `ReiniciarEncuentro`
   → **17**. Y verificado en el grafo que los **dos** `BreakFStoredItem` cuelgan del pin
   `Amount` (índice 2, Integer), no del `Id`.

   **Las dos que quedan fuera, y no es olvido:** el *arma temporal + off-hand + su corrupción*
   —el propio §7.2 dice que «si el checkpoint es el estándar previo al sello, normalmente sólo
   habrá equipo base», y aquí siempre lo es, porque el Seal Break purga al salir de la arena
   anterior— y los *cooldowns*, que el PDF condiciona a «si DCS lo expone de forma estable»
   y hoy no hay vía leída y verificada para eso.

   **Y de paso, dos trampas nuevas del escritor de grafos**, que están en la cabecera de
   `arena_flechas.py`: `ReiniciarEncuentro` **no se puede reescribir** (`Game|SpawnActor` se
   lee pero no se escribe, así que la restauración vive en `RestaurarFlechas` y en el grafo
   viejo se injerta un solo nodo por cirugía); y un `Break` **hay que destructurarlo**
   —`(bind (_id _it _am) …)`— porque copiar la forma corta que imprime el lector conecta el
   primer pin y revienta.

**Lo que ya estaba y este documento negaba:**

4. **El aura del Portador SÍ está en el motor**, y esto deroga el aviso que salía en cada
   exportación. 🔬 `BP_DA_Inspector.uasset` trae `BP_DA_AuraComponent`; el componente vive en
   `Blueprints/Combat/` con `RadioAura = 1200` y `Bonificacion = 15` leídos del CDO, y
   `L_Forja_el-estandarte-vive.umap` lo referencia. La calibración del simulador dice
   exactamente lo mismo, sumado como **plano** en `sim.js._danoDe`. El aviso muerto vivía en
   `exportador.mjs` y hoy es una **comprobación de verdad**: lee el componente del actor
   colocado y sólo grita si falta o si sus números no son los que el simulador asumió.
5. **Force Shield Discard ya funciona**, aunque no tenga botón propio. 🔬 `ArrojarLanza` —la
   tecla y el botón FORCE DISCARD— tiene **cinco ramas con cinco montajes**, una por familia.
   El docstring de `dsl_forzar_descarte` decía «con cualquier otra no pasa nada»: corregido.
6. **INFINITE AMMO existe** en la pestaña COMBAT (`AlternarMunicionInfinita`, toggle con
   temporizador). Lo que falta del §10 es **mostrar** el ammo en WEAPON, no darlo.
7. **`L_Forja_romper-la-linea.umap` ya no está a medias.** 🔬 1 Lancero, 2 Arqueros,
   2 Vigilantes, `BP_DA_Arena` y `PlayerStart`.

**Divergencias deliberadas del PDF, que hasta hoy no estaban escritas aquí:**

| § | el PDF pide | lo montado | por qué |
|---|---|---|---|
| 6.3 | 1 Portador + **2 Lanceros + 2 Escuderos** | **4 enemigos: falta un Escudero** | en `notasDiseno`: con los cinco se ganaba el 36% y 2.534 de 5.000 partidas agotaban el límite de 180 s |
| 4.1 | el arma queda en el mundo «una ventana breve y clara» | `DropLifeSpan = 0`, para siempre, en los cinco | decisión de la POC; el suelo no se satura porque el swap es irreversible |
| 6.4 | «Elite con **gran guardia**» | `elite_pesado` tiene `guardia 0.4`, la misma que el escudero y el lancero | sin decidir: el guard break del Espadón rompe una guardia que no es grande |

---

**Puesta al día del 2026-08-25:** «Romper la línea» (§6.1) pasa de perderse el 100% de las
veces a ganarse el **94% solo con la espada**, sin cambiar un número de la calibración: lo que
cambió es **cuándo entra cada enemigo**. La receta está medida y validada en la Forja, y lo que
la separa del juego son dos datos que a `BP_DA_Arena` le faltan. Detalle en el §6.

---

## Resumen por sección

| § | Bloque | Estado |
|---|---|---|
| 3.1 | Persistencia y estados del ciclo | 🟢 el ciclo entero — **las cuatro salidas** desde el 26/08 (SWAP, DISCARD, SEAL BREAK y AMMO OUT); sólo falta la progresión de corrupción, que el PDF marca opcional |
| 3.2 | Ataque de descarte por familia | 🟢 **5 de 5**, verificado sobre el grafo: cinco ramas, cinco montajes |
| 4 | Arsenal de oportunidad | 🟢 las 5 familias existen; **counters medidos el 25/08**, 3 de 5 en banda y las otras 2 con diagnóstico |
| 4.1 | Reglas de pickup | 🟠 completa salvo la «ventana breve y clara»: hoy el arma se queda para siempre (`DropLifeSpan = 0`) |
| 5 | Orden de bajas implícito | 🟢 las dos señales lógicas del §5.1 están (26/08 noche): salto atrás de los Arqueros al ver la Lanza —por evento, no por umbral— y el aura del Portador arrancando «tras pocos segundos». El resto es layout de arenas |
| 6 | Recetas de encuentro | 🟢 **5 de 5 montadas y en el motor** (26/08, banda 70-94% con espada sola); falta jugarlas. El §6.3 va con 4 enemigos y no 5, por el reloj |
| 7 | Arenas selladas | 🟢 completo |
| 8 | Sistema de drops | 🟢 las 4 políticas: motor 25/08, simulador+exportador+piedad AND 26/08 |
| 9 | Feedback visual/audio/UX | 🟢 **entero** desde el 27/08: pilar + sonido del arma disponible, y el destello celestial del descarte (probado en PIE arrojando la Lanza) |
| 10 | Integración con DA Debug HUD | 🟢 **entero** desde el 27/08: pestaña ARENA nueva (watchdog en pantalla, cadena táctica, highlight de drops) y WEAPON con 6 filas (ammo y enemigo de origen). Fuera de la letra del PDF quedan solo el moveset y la compatibilidad off-hand como texto propio |
| 11 | Guía técnica / arquitectura | 🟢 adaptado a DCS, sin sistemas paralelos. Snapshot del §11.3: **6 de 8** desde el 26/08 |
| 12 | Criterios de aceptación | 🟢 **12 de 12** desde el 26/08; el del encuentro, medido pero sin jugar |
| 13 | Orden de implementación (fases) | 🟠 fases 1-8 hechas, 9 a medias, 10 sin empezar |

---

## 🔴 Lo que falta de verdad

### 1. Tres de los cinco ataques de descarte (§3.2)

La tabla del PDF pide uno por familia. Hay dos:

| familia | descarte que pide el PDF | estado |
|---|---|---|
| Lanza | arrojarla para empalar | ✅ `M_DA_ArrojarLanza` + notify |
| Estandarte | clavarlo para una última zona | ✅ `M_DA_ClavarEstandarte` + zona de 15 s |
| **Espadón/Alabarda** | golpe de suelo de stagger/guard break | ✅ **`M_DA_GolpeDeSuelo`** (24/08) |
| **Escudo** | shield bash final o lanzamiento | ✅ **Muro del Escudero** (24/08): plantado 12 s, rebota proyectiles y amortigua el melé en 600 uu |
| **Arco** | consumir las flechas en una descarga | ✅ **`M_DA_LluviaFirmamento`** (24/08) |

**Hecho el 24/08.** El golpe de suelo daña, derriba y lanza a todo enemigo en 600 uu. Medido
en PIE con cinco en corro: vida 100 → 40 en los cinco, todos por el aire (z 116 → 212) y en el
suelo 1 s después, de pie a los 3 s. Sin `HitData.CanBeBlocked`, que un guard break bloqueable
no rompe ninguna guardia. La caída sale del **Knockdown & Get-Up Pack** de Raise Creation
(`AS_KG_Heavy`, la única que sube antes de caer).

**La Lluvia del Firmamento** (24/08) cierra la cuarta familia. Radio 450 uu a 1.600 del
jugador — sin solaparse con los 600 del golpe de suelo—, con 1,2 s de telegrafiado y un anillo
en el suelo que marca donde va a caer. **El daño es 3 × las flechas que te queden**, así que es
el único descarte cuya potencia acumulas: medido en PIE, 30 flechas = 90 de daño, los tres de
dentro a 10 de vida y el de 1.200 uu intacto. Tope de 24 flechas en pantalla; por encima sube el
daño, no el número. Malakh no se hace daño si se mete dentro.

**Y el agujero de fondo, tapado:** el último caso de `ArrojarLanza` era un `elif` sobre el arma
arrojadiza, así que **todo lo demás caía por un camino vacío** — con el hacha, FORCE DISCARD no
hacía nada. Ahora es un `else` que va al golpe de suelo, así que **ninguna arma temporal se
queda sin remate**. Al escudo y al arco les falta su gesto propio del §3.2, no un descarte.

### 2. Las recetas de encuentro (§6) — «Romper la línea» ya cuadra sobre el papel

El PDF trae cinco composiciones con su ruta de ventaja: *Romper la línea*, *La lluvia del
firmamento*, *El estandarte vive*, *Pesado contra pesado* y *Cadena perfecta*. **Ninguna está
montada en el juego todavía**, pero la 6.1 ya tiene una forma que el simulador aprueba.

**Lo que cambió el 25/08.** La receta se perdía **el 100% de las veces con espada sola** y el
techo medido eran dos enemigos. Con **activación escalonada** —cuatro oleadas, nunca más de dos
cuerpos a la vez— la misma composición del PDF (2 Escuderos + 1 Lancero + 2 Arqueros, sin tocar
un número de la calibración) se gana el **94%** solo con la espada, y recoger las armas baja el
daño recibido un **24%**. **Ninguna puerta del veredicto en rojo**: ocho de nueve en verde con
el lote por defecto, y con 2.000 partidas por política aparece un segundo ámbar de cola —
2 partidas de 10.000 agotan el límite de 180 s.

La novena, *«el orden de bajas ya cambia algo por sí solo»*, se queda en ámbar y **es
estructural**: los enemigos corren a 600 y Malakh a 400, así que elijas a quien elijas los
tienes encima en tres segundos. En este juego el orden que importa es el de las **armas**, y esa
puerta sí está verde.

**Lo que falta para que exista en el juego, y es lo siguiente:**

- ~~`BP_DA_Arena` no sabe escalonar~~ — **hecho el 25/08.** La arena tiene ya
  `RetardoEntreOleadas` (público, categoría *Oleadas*) y cuatro funciones nuevas: `LeerOleadas`,
  `AplicarOleadas`, `PedirSiguienteOleada` y `EntrarOleada`. Limpiar la oleada actual ya no abre
  el sello: pide la siguiente. ✅ **VERIFICADO sobre los actores del nivel** (sin PIE): 5
  enemigos detectados, `OleadasEnemigos = [1,1,2,3,4]`, `MaxOleada = 4`, y cada `EntrarOleada`
  incorpora exactamente a quien toca.
  **El número de oleada viaja en un Tag del actor** (`Oleada2`, `Oleada3`, `Oleada4`; sin tag =
  primera), no en una variable del AI: los cinco enemigos heredan de `BP_BaseAI`, que es de DCS,
  y meterle una variable sería una modificación viva de un asset de pago. El exportador lo
  escribe y lo relee. ✅ **PROBADO EN PIE el 25/08**: al sellar sólo corre el árbol de la
  oleada 1; cada oleada limpia despierta a la siguiente sin abrir el sello; y al caer el
  quinto, `Estado = 2` y los cuatro muros a `NO_COLLISION`.
- `L_Forja_romper-la-linea.umap` sigue **a medias**: ✅ verificado sobre el binario, tiene 3
  referencias a `BP_DA_Lancero` y **cero** a Vigilante, Arquero, `BP_DA_Arena` y `PlayerStart`.
- La arena de El Claro funciona, pero **no es ninguna de las cinco**.

Esto sigue bloqueando el criterio del §12 *«un encounter de prueba con un orden de bajas
ventajoso pero ganable sólo con espada»* — pero ya no por no saber qué construir, sino por no
tenerlo construido.

### 3. ~~El director de drops (§8)~~ — motor el 25/08, camino completo el 26/08

**El motor lo tenía desde el 25/08** (commit `52ddd94`, posterior a esta auditoría — que por
eso lo daba como no hecho): `AplicarPolitica` corre al morir el dueño, y las cuatro políticas
caben en dos números por instancia — `ProbabilidadDrop` (1.0 garantizado, 0.5 oportunidad,
0.0 nada) y `PiedadActiva`. El 26/08 se completó lo que faltaba del camino:

- **El simulador lo modela** (espejo de la fórmula del motor), con una garantía: el camino
  por defecto no tira ningún dado, así que las recetas de siempre son bit-idénticas.
- **El exportador escribe los cuatro campos** en el componente de cada enemigo — tapando de
  paso un agujero: hasta hoy nadie escribía `e["drop"]` y los niveles usaban los defectos
  de clase, dijera lo que dijera la receta.
- **La piedad es AND, no OR** («mucho tiempo sin herramienta Y presión alta», que es lo que
  dice el PDF): medido, con OR saltaba en el 76% de las partidas de lluvia-del-firmamento —
  un drop estándar disfrazado. Con AND salta en el 5-10%, solo tarde y herido, y la mitad de
  esas partidas se ganan. Corregido en el generador (`director_drops.py`) y en el grafo.
- **Primera adopción**: el segundo escudero de lluvia-del-firmamento es un Mercy Drop.
- `pruebas/director.mjs` en `npm test`: las cuatro políticas y la fórmula, 11 de 11.

La tabla de abajo era el estado ANTERIOR (dos booleanos por mano), y se deja como registro:

✅ **VERIFICADO leyendo los cinco assets:**

| enemigo | DropMainHand | DropOffHand | LifeSpan |
|---|---|---|---|
| Vigilante | False | **True** (suelta el escudo) | 0 = para siempre |
| Lancero / Arquero / Heraldo / Inspector | **True** | False | 0 |

Es determinista, que para las recetas guionizadas está **bien**. Lo que no hay es
probabilidad, ni contexto, ni el Mercy Drop del jugador que lleva rato sin herramienta.
El emulador ya renunció a modelarlo por esto mismo (§6.2 del contrato).

---

## 🟠 Lo que está a medias

### ~~El Arco y el Escudo chocan con el equipo base~~ (§4) — **resuelto el 24/08**

Malakh ya **no** lleva arco ni escudo — ni el `DA_GreatAxe` que también arrastraba sin que
nadie lo supiera. Arranca solo con `DA_SteelSword` y su carcaj de 30 flechas, que se conserva
porque si no el arco robado llegaría sin munición. El arco del Arquero y el escudo del
Vigilante vuelven a ser recompensa táctica, que es lo que el §4 les pide.

Y de paso salió a la luz que **el arma temporal iba siempre a la ranura de melé**, con lo que
un arco robado se equipaba pero no se veía. Corregido: ahora enruta por tipo de item.

Lo que sigue debajo es el diagnóstico original, que se deja por su valor de medida:

✅ **VERIFICADO en PIE** — el loadout de partida de Malakh son **cinco** displayed items:

```
BP_DI_SteelSword_C · BP_DI_WoodenShield_C · BP_DI_ElvenBow_C
BP_DI_Quiver_ElvenArrows_C · BP_DI_Potion_C
```

O sea: **Malakh ya lleva arco y escudo de serie**. Y el Arquero suelta `DA_ElvenBow` y el
Vigilante `DA_WoodenShield` — *los mismos items*. Robarlos no cambia nada, y el PDF los quiere
como «armas de oportunidad» que abren una ruta táctica (§4: *«Arco del Firmamento»*,
*«Escudo Celestial»*).

**Es una decisión de diseño, no un bug**, pero hay que tomarla: o Malakh empieza solo con
espada —y entonces el arco y el escudo vuelven a ser recompensa—, o las versiones celestiales
son items distintos y mejores. Tal como está, dos de las cinco familias no aportan lo que el
PDF promete.

### Volver a la espada cuando quieras (§5.2) — lo destapó la matriz de counters

El §5.2 promete que *«cualquier encuentro se completa sin depender de un drop»*, y hoy eso solo
se cumple a medias: se vuelve a la espada al **cambiar de arma, sacrificarla o purgarla**, pero
no cuando el jugador quiere.

✅ **MEDIDO el 25/08** en `pruebas/matriz.mjs`: con el Arco en la mano, dos Escuderos se ganan
el **42%** de las veces. Con el Estandarte, el 0%. Son muros, y no se arreglan calibrando.

Mientras no exista un «guardar arma temporal», **cada drop es también una trampa potencial** —
recoger el arco antes de una oleada de melé te deja peor que no haberlo tocado. Y eso bloquea
el director de drops del §8: repartiría trampas sin saberlo.

### ~~La regla de dos manos vs. escudo (§4.1)~~ — hecha el 25/08

El PDF: *«Definir explícitamente qué armas a dos manos obligan a soltar el escudo.»*

**Hecha en el mismo commit `52ddd94`** (posterior a esta auditoría): la regla vive en
`BP_DA_PlayerCharacter.AplicarReglaDosManos`, colgada de `SustituirArmaTemporal` — el embudo
único del canje. Es SIMÉTRICA a propósito: la ranura del escudo está escondida exactamente
cuando el arma en mano es a dos manos; escrita como «si es a dos manos, escóndelo» el escudo
se perdía para siempre al tocar una lanza. Los data assets ya traían `TwoHanded` (Lanza y
Trompeta True) y DCS no se toca. El párrafo de arriba era el diagnóstico del 24/08.

### La corrupción no progresa (§3.1)

Los cuatro estados (Celestial / Tainted / Corrupted / Fractured) existen **solo como botón de
debug**. En juego, `CorromperArmaTemporal` salta a 0,45 al recoger y ahí se queda.

✅ **VERIFICADO en PIE:** con el hacha varios minutos en la mano,
`MID_M_WeaponSet_0 → Corrupcion = 0.45`, sin moverse.

El PDF dice *«**puede** progresar por uso, tiempo portado o beats»*, así que es opcional —
pero hoy los cuatro estados no los ve nadie que no abra el HUD.

### ~~Las entradas del Debug HUD (§10)~~ — CERRADAS el 27/08 (ver la puesta al día); lo de abajo queda como registro

**Al día del 26/08.** De las trece que pide el §10 faltan **tres**: la cadena táctica, el
resalte de drops garantizados y el watchdog en pantalla. Otras dos están a medias: Show Weapon
State (sin enemigo de origen ni ammo) y Create/Respawn Pre-Combat Snapshot (hay checkpoint de
posición, no instantánea de arena). Lo tachado ya está hecho:

- ~~Give Arco~~ — **hecho el 24/08.** La fila tiene ya los seis: LANZA, TROMPETA, HACHA,
  ESPADON, **ARCO** y ESCUDO, verificado en el panel en PIE.
- ~~**Force Shield Discard**~~ — **cubierto desde el 24/08, sin botón propio.** `ArrojarLanza`
  —la tecla y el botón FORCE DISCARD— enruta por familia con cinco ramas, así que con el
  escudo en la mano FORCE DISCARD **es** el descarte del escudo. Verificado sobre el grafo el
  26/08.
- ~~**Infinite Ammo ON/OFF**~~ — **está**: `AlternarMunicionInfinita`, toggle con temporizador
  de 1 s (rellenar una vez se agotaría igual). Lo que falta es *mostrar* el ammo, no darlo.
- **Create / Respawn Pre-Combat Snapshot** — a medias: la pestaña STORY tiene SET DEBUG
  CHECKPOINT / IR AL CHECKPOINT, pero son de **posición**, no la instantánea de la arena
  (`TomarInstantanea`), que hoy sólo se dispara al sellar.
- ~~**Show Weapon State**~~ — **hecho el 26/08, a medias y con lo que falta escrito en el
  propio panel.** Pestaña **WEAPON**, la octava, de sólo lectura. Muestra el **arma actual**
  (nombre del asset), el **tipo** (la clase del item, que dice si es melé, arco o escudo),
  los **segundos que llevas con ella** y el **motivo de la última salida**.

  El motivo se registra de verdad, no se adivina: `MotivoSalidaArma` se escribe en los
  tres puntos por los que un arma temporal se va — `SustituirArmaTemporal` → SWAP,
  `ArrojarArmaTemporal` → DISCARD, `PurgarTemporales` → SEAL BREAK.

  **Faltan el enemigo de origen y el ammo**, y no por dejadez: el pickup ocurre dentro de
  DCS y el drop no guarda quién lo soltó. Registrarlo pide tocar
  `BP_DA_WeaponDropComponent` y el camino de recogida, que es asset de pago. El panel lo
  dice en pantalla («-- sin registrar: el pickup vive en DCS») en vez de fingir que está.
- **Show recommended tactical chain** (DEBUG ONLY).
- **Highlight Guaranteed Tactical Drops** (DEBUG ONLY).
- **Watchdog status en pantalla**: hoy el watchdog existe y funciona, pero **escupe al log**;
  el PDF lo quiere visible (enemies alive, victory condition, barrier state).

### ~~La reacción enemiga (§5.1)~~ — **cerrada el 26/08 (noche), y NO con un decorador**

Dos señales entraron, y las dos van por donde el propio proyecto había medido que tenían que ir:

**1. «Arquero retrocede al ver a Malakh con lanza» — por EVENTO, no por umbral.** Primero, una
corrección de este documento: el «puesto en 450» de la versión anterior era falso — **se
revirtió a 300 el mismo día**, y el porqué está medido en `bt_arquero_da.py`: la rama de huir
del árbol lleva un `Force Success` que **apaga el disparo** mientras el jugador esté dentro
del umbral, la EQS no tiene adónde mandar a un arquero cuyo balcón (400×550) es más pequeño
que el propio umbral, y el umbral mide en 2D — desde el balcón, 450 horizontales son 557 reales.
Cualquier número ahí solo compra una burbuja de silencio. Y un decorador propio que
distinguiera el arma heredaría los tres defectos.

La conclusión escrita allí era que la señal pide **un paso atrás visible**, y eso es lo
montado: en el momento en que Malakh ADQUIERE la Lanza —`SustituirArmaTemporal`, el embudo
único, así que vale para el pickup y para el give del HUD—, `AvisarLanza` hace que todo
Arquero vivo a menos de 2.500 dé un **salto atrás** (`LaunchCharacter` alejándose, 380
horizontal + 300 de brinco) **con comprobación de suelo**: los arqueros viven en balcones, y
sin el `LineTrace` el susto los tiraría a la arena y cambiaría el encuentro — si detrás no
hay suelo, ese arquero no salta. El árbol NO se toca: sigue disparando igual. La señal es un
gesto, no un estado.

**2. «Estandarte empieza buff tras pocos segundos» — el aura ya no nace encendida.** El
BeginPlay del componente corre al CARGAR el nivel, así que un retraso contado desde ahí se
consume antes de que llegues; y engancharlo a la arena dejaría colgados a los portadores
sueltos. Por eso el arranque es por proximidad: cuando el jugador entra en `RadioArranque`
(1500) empieza la cuenta de `RetrasoAura` (4 s), y al agotarse se monta el visual y empieza el
buff — te acercas, y a los pocos segundos el anillo se enciende y los aliados pegan más.
`SiempreActiva` se respeta. **Espejo exacto en el simulador** (`_pasoAura` + el gate en
`_danoDe`, números en `calibracion.json`) y `pruebas/aura.mjs` cubre el arranque: 9 de 9, y
`npm test` entero verde. Ambas señales, pendientes de verse en PIE.

Las otras cuatro señales del §5.1 (posición, presión, silueta, geometría) son layout de
arena, no lógica: se cierran construyendo encuentros, no código.

---

## 🟢 Lo que ya está entero

- **§7 Arenas selladas, completo.** Activación por trigger, checkpoint **fuera** del volumen,
  barreras con lectura diegética (canto, halo, bandas y audio), purga al romper el sello,
  muerte → reponer + rearmar sin reanudar sola, watchdog del §7.3 y las cinco reglas
  anti-soft-lock del §7.3.
- **§3.1 el ciclo del arma temporal.** ✅ Verificado hoy el punto más delicado, el **swap
  irreversible**: con la Lanza en la mano, dar el Hacha deja `BP_DI_DA_HachaMano_C` y la lanza
  **desaparece del todo** — no queda enganchada, ni en el suelo, ni recogible. (El
  `BP_DI_DA_Lanza_C` que aparece en el barrido del mundo es el de un Lancero vivo a 115 km,
  no un resto del swap.)
- **§11 sin sistemas paralelos.** Todo va sobre el Equipment, el StatsManager y los displayed
  items de DCS.
- **§12 la guarda de Shipping.** No es un `if`, que sería más débil:
  `/Game/DarkAngels/Debug` está en `DirectoriesToNeverCook` y el nivel lo pide por referencia
  **blanda** — en un build empaquetado los assets no existen y devuelve nulo sin romper nada.

---

## Criterios de aceptación del §12: 12 de 12

Al día del 2026-08-26. El último en caer fue el primero, con `AMMO OUT`. Uno de los doce
queda **medido pero no jugado**, y está dicho en su fila.

| criterio | |
|---|---|
| Vuelve a la espada al cambiar / sacrificar / **agotar su recurso natural** / purgar | ✅ **las cuatro** desde el 26/08, probadas en PIE (`AMMO OUT`) |
| Recoger una Lanza y sentir el cambio de rango/moveset | ✅ |
| Escudo Celestial como off-hand junto con la espada | ✅ desde el 24/08: Malakh ya no lo lleva de base, así que vuelve a ser recompensa |
| Corrupción visual sin reducir vida útil | ✅ |
| Al cambiar/purgar nunca queda sin loadout válido | ✅ verificado |
| **Al menos un** ataque de descarte funcional | ✅ (hay dos) |
| **Encounter de prueba con orden de bajas ventajoso** | ✅ los cinco, montados y exportados (banda 70-94% con espada sola). **Pendiente de confirmarlo jugándolo**: medido en la Forja, no en las manos |
| La arena se sella tras el trigger y se abre al vencer | ✅ |
| Al morir, checkpoint previo y poder retirarse | ✅ |
| Reset limpia enemigos/drops sin tocar NPCs externos | ✅ |
| Debug HUD: dar armas, estados, ammo, descarte, reset | ✅ las seis armas, los cuatro estados de corrupción, INFINITE AMMO, FORCE DISCARD y los tres de arena. Lo que falta del §10 no es de este criterio |
| Nada de debug accesible en Shipping | ✅ |

---

## Orden sugerido para cerrar — al día del 2026-08-26

**Con `AMMO OUT` cerrado, los doce criterios de aceptación del §12 están en verde.** Lo que
queda ya no es ningún criterio: es lectura, herramienta y decisiones.

1. **JUGAR LOS CINCO NIVELES.** Sigue siendo lo primero y ya es lo ÚNICO grande: todo lo
   demás del PDF está montado. Al jugar se ven de una pasada las señales nuevas: el pilar y
   el sonido del arma caída, el salto atrás de los Arqueros al robar la Lanza, el arranque
   del aura del Portador (en *el-estandarte-vive*), el destello del descarte, y la tecla `.`
   con las pestañas ARENA y WEAPON contando la pelea.
2. Decidir las tres divergencias de la tabla de arriba: el quinto enemigo del §6.3, la ventana
   de vida del drop (§4.1) y la «gran guardia» del elite (§6.4).
3. Opcionales por el propio PDF: progresión de corrupción (§3.1) y los cooldowns del snapshot
   (§11.3).

## Orden sugerido, el del 2026-08-24 (registro)

1. ~~Oleadas en `BP_DA_Arena`~~ — **hecho el 25/08**, y la receta ya está exportada a
   `L_Forja_romper-la-linea`. Lo siguiente es **jugarla en PIE**: confirmar que los dormidos no
   se mueven, que la oleada entra a los 3 s de limpiar la anterior, y que el sello se abre al
   caer el último. Eso cierra el criterio que falta del §12.
2. ~~El golpe de suelo del Espadón/Alabarda~~ — **hecho el 24/08.**
3. **Decidir qué pasa con el arco y el escudo base.** Es una decisión de Angel, y hasta que se
   tome, dos familias del §4 no significan nada.
4. **Show Weapon State en el HUD.** Es lo que hace depurable todo lo anterior: sin saber de
   qué enemigo vino el arma ni por qué se fue, cada prueba se mide a ciegas.
5. El resto —descarte de arco y escudo, progresión de corrupción, director de drops, reacción
   enemiga— es §13 fase 10, «polish», y puede esperar a que haya arenas que pulir.
