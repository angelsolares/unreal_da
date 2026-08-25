# Estado contra el PDF v2 — *Divine Weapon Corruption + Encounter Combat Loop*

Auditoría del 2026-08-24 contra
`Dark_Angels_Divine_Weapon_Corruption_Combat_Loop_v2.pdf` (14 páginas).

**Cómo se hizo:** lo marcado ✅ VERIFICADO se comprobó **en PIE o leyendo el asset**, no las
notas. El resto se leyó del código del generador y de los Blueprints. Las notas de traspaso
ya se equivocaron una vez este mes afirmando cosas que el motor desmentía, así que aquí solo
vale lo medido.

**Titular:** de las 13 fases y bloques del PDF, **el bucle de arena está entero** y **el ciclo
de arma temporal casi**. Lo que falta se concentra en dos sitios: **las recetas de encuentro
sin montar** y **el director de drops**.

**Puesta al día del 2026-08-25:** «Romper la línea» (§6.1) pasa de perderse el 100% de las
veces a ganarse el **94% solo con la espada**, sin cambiar un número de la calibración: lo que
cambió es **cuándo entra cada enemigo**. La receta está medida y validada en la Forja, y lo que
la separa del juego son dos datos que a `BP_DA_Arena` le faltan. Detalle en el §6.

---

## Resumen por sección

| § | Bloque | Estado |
|---|---|---|
| 3.1 | Persistencia y estados del ciclo | 🟢 completo, salvo progresión de corrupción |
| 3.2 | Ataque de descarte por familia | 🟢 **5 de 5** (el escudo, pendiente de ver el rebote en PIE) |
| 4 | Arsenal de oportunidad | 🟢 las 5 familias existen; **counters medidos el 25/08**, 3 de 5 en banda y las otras 2 con diagnóstico |
| 4.1 | Reglas de pickup | 🟠 falta la regla de dos manos vs. escudo |
| 5 | Orden de bajas implícito | 🟠 falta la reacción enemiga |
| 6 | Recetas de encuentro | 🟠 **1 de 5 diseñada y validada**, ninguna en el nivel todavía |
| 7 | Arenas selladas | 🟢 completo |
| 8 | Sistema de drops | 🔴 sin las 4 políticas |
| 9 | Feedback visual/audio/UX | 🟢 casi; falta VFX del descarte |
| 10 | Integración con DA Debug HUD | 🟠 faltan 6 entradas |
| 11 | Guía técnica / arquitectura | 🟢 adaptado a DCS, sin sistemas paralelos |
| 12 | Criterios de aceptación | 🟠 **10 de 12** |
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

### 3. El director de drops (§8)

Las cuatro políticas —Guaranteed Tactical / Standard Opportunity / **Mercy Drop** / No Drop—
no existen. `BP_DA_WeaponDropComponent` tiene **dos booleanos por mano y nada más**:

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

### La regla de dos manos vs. escudo (§4.1)

El PDF: *«Definir explícitamente qué armas a dos manos obligan a soltar el escudo.»*

✅ **VERIFICADO en PIE:** al dar la Lanza —que es a dos manos— `BP_DI_WoodenShield_C` **sigue
equipado**. La regla no está definida ni en un sitio ni en otro.

### La corrupción no progresa (§3.1)

Los cuatro estados (Celestial / Tainted / Corrupted / Fractured) existen **solo como botón de
debug**. En juego, `CorromperArmaTemporal` salta a 0,45 al recoger y ahí se queda.

✅ **VERIFICADO en PIE:** con el hacha varios minutos en la mano,
`MID_M_WeaponSet_0 → Corrupcion = 0.45`, sin moverse.

El PDF dice *«**puede** progresar por uso, tiempo portado o beats»*, así que es opcional —
pero hoy los cuatro estados no los ve nadie que no abra el HUD.

### Seis entradas del Debug HUD (§10)

De la lista del §10 faltan:

- ~~Give Arco~~ — **hecho el 24/08.** La fila tiene ya los seis: LANZA, TROMPETA, HACHA,
  ESPADON, **ARCO** y ESCUDO, verificado en el panel en PIE.
- **Force Shield Discard** — no existe el descarte, así que tampoco el botón.
- **Show Weapon State** — arma actual, **enemigo de origen**, moveset, off-hand compatible,
  ammo y **motivo de salida** (Swap / Discard / Seal Break). No hay nada de esto.
- **Show recommended tactical chain** (DEBUG ONLY).
- **Highlight Guaranteed Tactical Drops** (DEBUG ONLY).
- **Watchdog status en pantalla**: hoy el watchdog existe y funciona, pero **escupe al log**;
  el PDF lo quiere visible (enemies alive, victory condition, barrier state).

### La reacción enemiga (§5.1)

*«Arquero retrocede al ver a Malakh con lanza»* — la única señal del §5.1 que es lógica y no
layout. No implementada. Las otras cinco (posición, presión, silueta, geometría, timing) son
trabajo de construir las arenas, o sea el punto 2 de arriba.

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

## Criterios de aceptación del §12: 10 de 12

| criterio | |
|---|---|
| Vuelve a la espada al cambiar / sacrificar / purgar | ✅ |
| Recoger una Lanza y sentir el cambio de rango/moveset | ✅ |
| Escudo Celestial como off-hand junto con la espada | ⚠️ funciona, pero ya lo lleva de base |
| Corrupción visual sin reducir vida útil | ✅ |
| Al cambiar/purgar nunca queda sin loadout válido | ✅ verificado |
| **Al menos un** ataque de descarte funcional | ✅ (hay dos) |
| **Encounter de prueba con orden de bajas ventajoso** | ⚠️ diseñado y validado en la Forja (94% con espada sola, −25% de daño con armas); falta montarlo, y para eso `BP_DA_Arena` tiene que saber escalonar |
| La arena se sella tras el trigger y se abre al vencer | ✅ |
| Al morir, checkpoint previo y poder retirarse | ✅ |
| Reset limpia enemigos/drops sin tocar NPCs externos | ✅ |
| Debug HUD: dar armas, estados, ammo, descarte, reset | ⚠️ sin arco ni Show Weapon State |
| Nada de debug accesible en Shipping | ✅ |

---

## Orden sugerido para cerrar

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
