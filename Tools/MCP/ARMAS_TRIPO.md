# Armas nuevas con Tripo — ficha de encargo

Medido sobre los assets reales el 2026-08-22. Todo lo de aqui son numeros
comprobados, no estimaciones.

## Lo que hay hoy

| arma | malla | tris | material | texturas |
|---|---|---|---|---|
| Steel Sword | `SM_SteelSword` | 824 | `M_WeaponSet_1` | **ninguna** (3 nodos, 0 parametros) |
| Great Axe | `SM_GreatAxe` | 628 | `M_WeaponSet_2` | ninguna |
| Wooden Shield | `SM_WoodenShield` | 1.272 | `M_WeaponSet_1` — **el mismo que la espada** | ninguna |
| Elven Bow | `SK_ElvenBow` (esqueleto propio + `ABP_ElvenBow`) | — | `M_ElvenBow` | 29 nodos, **9 parametros de color** |

Consecuencia: espada / hacha / escudo **no se pueden retexturizar** porque no
tienen textura ninguna. El arco si, y ademas conviene: su cuerda la anima
`ABP_ElvenBow` y un modelo de Tripo llegaria sin ese rig.

## Ficha para la espada

Copia las medidas del `SM_SteelSword` para que las animaciones y los diez
finishers del Sword Takedown sigan cuadrando sin retocar nada.

- **Tamano total**: X 25,7 · Y 4,4 · **Z 138,8** cm. Escala del componente 1:1,
  asi que el tamano de la malla es el tamano en juego.
- **Pivote** en (0,0,0), con la caja centrada en z = −48,9: o sea el pivote cae
  **cerca de la empunadura** y la hoja cuelga hacia **−Z**. Ojo, el hacha usa el
  convenio contrario (pivote abajo, cabeza hacia +Z).
- **Grosor por Y**, anchura por X.
- Compensacion que ya aplica el displayed item: `rel_loc z = −6`,
  `rel_rot = (pitch 0, yaw 180, roll 180)`. Si la malla nueva viene con otra
  orientacion, se corrige ahi y no se toca nada mas.
- **Presupuesto de triangulos**: la actual tiene 824 y un LOD. Con 3.000–8.000
  vas sobradisimo; Tripo entrega decenas de miles, hay que decimar.
- **Texturas** a `MaxTextureSize` 1024.

## Donde van los assets

**Nunca dentro de `Content/DynamicCombatSystem/`**: esa carpeta esta en el
`.gitignore` y no viaja al repo.

Ya creados y listos para recibir la malla nueva:

- `/Game/DarkAngels/Weapons/Items/DA_DA_Espada` — copia de `DA_SteelSword`,
  con `displayedItem` ya apuntando al de abajo.
- `/Game/DarkAngels/Weapons/DisplayedItems/BP_DI_DA_Espada` — copia de
  `BP_DI_SteelSword`, hoy con `SM_SteelSword` puesta.

Para estrenar el modelo de Tripo basta con **cambiar la malla del
`StaticMeshComponent` de `BP_DI_DA_Espada`** y ajustar `rel_loc` / `rel_rot`.
Nada mas: `GetCollidingComponents` devuelve todos los `MeshComponent` del
objeto, asi que la deteccion de golpe funciona con la malla que le pongas —
**no hay que anadir sockets ni marcadores de traza**.

Las mallas y materiales nuevos, en `/Game/DarkAngels/Weapons/Meshes/` y
`/Game/DarkAngels/Weapons/Materials/`.

## Trampas de Tripo que aplican aqui

Receta completa en la memoria `tripo-pipeline-malkuth`. Las tres que muerden:

1. **Pedir el export CON texturas** (40–50 MB). El `tripo_convert` pelado
   (0,2–2 MB) viene sin material.
2. **El material sale mal siempre y de la misma forma**: la rugosidad cableada
   a `Metallic`, `Roughness` vacio, y el mapa metallic sin importar. Hay que
   rehacerlo, y corregir `SRGB=false` + `TC_Masks` **en la textura Y**
   `SamplerType = Masks` **en el nodo**. Con solo una de las dos, el material
   no compila y la miniatura sale como bola gris lisa.
3. **El pivote de los props de Tripo va en la base.** En un arma lo quieres en
   la empunadura. Se compensa con `rel_loc`, pero si ademas viene girada
   necesitas tambien `rel_rot`.

## Modelo de datos, por si haces mas armas

`DA_DA_Espada` (instancia de `BP_DA_Item_MeleeWeapon`) expone:

- `weaponType` — enum `E_WeaponType`: **None, Sword, Axe, Bow, Spell, Rifle,
  Pistol, Shotgun**. No hay Lanza ni Alabarda ni Estandarte.
- `twoHanded` (bool), `blockValue` (0-100)
- `modifiers` — array de (GameplayTag de stat, valor). La espada trae
  `Stat.Damage` 10; el hacha `Stat.Damage` 20 y `Stat.AttackSpeed.Melee` −0,2.
- `displayedItem` — la clase visual
- **`ability`** — una clase `BP_Ability`, y **hoy esta a `None` en todas las
  armas**. Es el gancho libre donde encaja el "ataque de descarte" del GDD.

Montajes disponibles: solo `1H`, `U` (desarmado), `Common` y los de arqueria.
**No existe tabla de dos manos**: el GreatAxe reusa las animaciones de una mano.

---

# Ficha para la LANZA (primer modelo, decidido el 2026-08-22)

Va a usar las animaciones de **una mano**, porque DCS no tiene set de dos manos
ni de asta. Eso manda sobre el diseno:

- **Largo total 170–190 cm. No mas.** La espada mide 138,8 y el hacha 144,3, y
  los dos usan ese mismo set de animacion. Una pica de 250–300 cm barreria el
  suelo y atravesaria al personaje en cada mandoble.
- **Pivote a un tercio desde el regaton**, no en la base. Asi no sobresalen mas
  de ~125 cm por delante de la mano, que es lo que sobresale hoy la espada
  (su caja va de z −118,3 a +20,5 respecto del pivote).
- **Punta hacia −Z**, como la espada, para reaprovechar el
  `rel_rot = (0, 180, 180)` que ya trae el displayed item.
- Grosor por Y, anchura de la moharra por X.
- 3.000–8.000 triangulos, texturas a 1024.

**Que sea jabalina y no pica** encaja ademas con el ataque de descarte del GDD
—arrojarla para empalar— y con que `BP_BaseMovingProjectile` ya existe: el
lanzamiento sale barato reusando lo de la flecha.

En el data asset: `weaponType = Sword` (no hay Lanza en `E_WeaponType`) y
`twoHanded = false`, que es lo que hace que el escudo NO se oculte y el estilo
resuelva a `CombatStyle.Melee.Armed.OneHandedWeapon`.

---

# La lanza, importada (2026-08-23) — lo que la practica corrigio de la ficha

- El export de Tripo (remesheado por Angel) llego a **14.004 triangulos** y
  **una sola textura: basecolor 4096** (sin normal/roughness/metallic). Para un
  arma basta: material propio `M_DA_Lanza` = basecolor + Roughness 0.5 +
  Metallic 0.4 constantes. `MaxTextureSize` 1024.
- **La malla vino con el convenio del HACHA, no el de la espada**: pivote en la
  base, punta hacia **+Z**, 98,19 uu de largo. Asi que el DI bueno para copiar
  era `BP_DI_DA_HachaMano` (rotacion identidad), no el de la espada.
- Numeros finales del componente en `BP_DI_DA_Lanza`: escala **1.7823**
  (98,19 -> 175 cm), `rel_loc z = -58.3` (empunadura a 1/3 del regaton),
  `rel_rot = (0, 90, 0)` — **yaw 90 obligatorio**: el plano de la hoja venia
  en Y y espada/hacha lo llevan en X; sin el giro, en los mandobles de una
  mano la moharra se ve DE CANTO y desaparece (se descubrio en una captura
  de Angel jugando).
- Regla rapida para el proximo modelo: mirar en que eje es ANCHA la malla.
  El plano ancho debe acabar en el **X del socket**; si viene en Y, yaw 90.
- `DA_DA_Lanza`: **twoHanded = TRUE** — el escudo se oculta solo
  (`IsHidden=True` en el DI del escudo, verificado en PIE) y el estilo
  resuelve a `CombatStyle.Melee.Armed.TwoHandedWeapon`, que reusa las
  animaciones de una mano igual que el GreatAxe. Icono: `T_DA_Lanza_Icon`
  (del `lanza.png` de Angel).
