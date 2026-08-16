# Dark Angels — Malkuth: The Kingdom · Three.js POC

Prueba de concepto jugable del **Nivel 1: Malkuth (El Reino)** de *Dark Angels*, construida
con Three.js sobre Vite. Todo el arte 3D fue generado proceduralmente en Blender (kits
Malkuth) y exportado a GLB. El audio es 100% procedural vía WebAudio — no hay assets
binarios de sonido.

La intención del POC es validar **factibilidad y sensación** del loop principal antes de
una producción mayor: movimiento souls-like, combate con stamina, el sistema **Farsa**
(disfrázate de santo ante el Cielo), enemigos con jerarquía angelical, una trampa de
patrones, un altar checkpoint y el boss **Gabriel de las Puertas** con sus tres fases.

## Ejecutar

```bash
npm install
npm run dev      # http://localhost:5178
```

Otros comandos:

```bash
npm run build    # build de producción en dist/
npm test         # smoke test headless (node test/smoke.mjs) — 31 aserciones
```

## Controles

| Input | Acción |
|---|---|
| WASD | Mover (relativo a cámara) |
| Mouse | Órbita de cámara (click para pointer-lock) |
| Shift | Correr (drena stamina) |
| Espacio | Saltar · mantener en el aire: **planeo** (se desbloquea tras Gabriel) |
| Click izq | Ataque ligero (combo de 3) |
| Click izq mantenido | Ataque pesado |
| Click der mantenido | Bloqueo (−60% daño) · los primeros 0.2 s son **parry** |
| C | Esquiva con i-frames |
| Q | **Umbral Lunge** — dash oscuro (30 Corruptio); rompe el Escudo de Luz |
| R | Lágrima de Arrepentimiento (cura 50, 3 cargas) |
| E / F | Altar: descansar (checkpoint) / ofrecer Lágrima (+20% daño, 3 min) |
| 1 / 2 / 3 | Respuestas en el diálogo de Gabriel |
| H / Esc | Menú de pausa: controles, objetivo actual y brillo |

## Estructura del nivel (beat chart del LDD comprimido)

El Reino juzga en orden: **6 puertas doradas** bloquean el avance y cada una se abre
solo al completar su prueba (la línea de objetivo en el HUD muestra qué hacer y el
progreso en vivo; el menú de pausa con **H** repite el objetivo actual).

1. **El Jardín que Despierta** — tutorial de movimiento; setos ordenados, topiario sephirot, la estatua del Ángel Terrestre.
2. **Los Primeros Vigilantes** — 2 Messengers; el seto de espinas sella la retirada. *Puerta 1: derrotar a los 2.*
3. **Campo Abierto** — patrulla coordinada de 3; el mosaico central quema la Farsa (−10%). *Puerta 2: eliminar la patrulla (3/3).*
4. **La Falsa Paz** — **Arcángel** elite: Escudo de Luz al 70% (solo lo rompe Umbral Lunge), Rayo del Juicio al 40%. *Puerta 3: derrotarlo.*
5. **La Trampa Celestial** — puente de 80 m sobre el estanque espejo; rayos con telegrafía oro→blanco en ritmo litúrgico creciente. *Se completa cruzando.*
6. **Santuario de Malkuth** — zona segura, Altar de Contemplación, luz violeta guía. *Puerta 4: arrodillarse ante el Altar (E) — fija el checkpoint.*
7. **La Hueste Desciende** — anfiteatro, 3 oleadas (2/3/3). *Puerta 5: sobrevivir las 3 oleadas.*
8. **Gabriel de las Puertas** — boss de 3 fases: *El Laberinto* (juicio de diálogo con timer; la arrogancia invoca trampas), *La Duda* (los espejos drenan Farsa si los miras de cerca; invoca un Messenger), *El Juicio* (el laberinto se rompe; +50% daño oscuro recibido). *Puerta 6: superar el juicio.*
9. **Ascensión** — escalera de luz al portal de Yesod. Pantalla final con estadísticas.

Muerte con regla souls: revives en el último Altar (o en el jardín si aún no descansas),
los ángeles vuelven a la vida y a sus puestos, la Farsa máxima baja 10%, tu Corruptio
queda en la Mancha de Sombra, y el boss/prueba en curso se reinicia completo.

## Sistemas implementados

- **Farsa**: 100→0. ACEPTADO (≥70) los ángeles patrullan tranquilos; SOSPECHOSO (≥40) te observan; REVELADO (<40) hostilidad total. Cae al matar ángeles, pisar suelo sagrado, usar poderes oscuros y fallar respuestas. La muerte reduce el máximo un 10% (regla souls).
- **Corruptio**: recurso ganado al matar; alimenta Umbral Lunge.
- **Mancha de Sombra**: al morir, tu Corruptio queda donde caíste; recupérala volviendo.
- **IA angelical**: patrulla → observación (la cabeza te sigue, alas cerradas) → persecución → ataque con windup telegrafiado. Los Messengers aturden con trompeta cada 8 s en combate.
- **Muerte angelical**: los ángeles no dejan cadáver — se disuelven en plumas y luz (regla del GDD).
- **Audio procedural**: pad sagrado desafinado (quinta abierta + detune), campanas, ruido de impacto, trompeta serrucha; la intensidad sigue al combate.

## Pipeline de arte (Blender → GLB)

Los modelos vienen de los kits generados en `ArtSource/Blender/`:

- `scripts/export_poc_glb.py` — exporta el manifiesto curado (62 GLB) desde
  `SM_Malkuth_GardenKit.blend` y `SM_Malkuth_AllKits.blend`, e incluye el kitbash de
  `SM_AngelTerrestrial` (cuerpo de Arcángel en piedra sobre base con raíces).
- `scripts/build_malakh.py` — genera `SK_Malakh_Placeholder` (jugador) con alas nombradas
  `Malakh_Wing_L/R` para animación procedural.
- `scripts/export_missing.py` — exportador puntual de objetos sueltos.

Las alas de los ángeles se animan por huesos (`wing_root_l/r`, `wing_01_l/r`) desde código;
los rigs no traen animaciones horneadas.

## Estructura del código

```
src/
  core/     Engine (renderer + bloom), Input (pointer lock), Assets (GLB cache), Audio (WebAudio)
  world/    SkyDome (cielo dorado + polen), MalkuthLevel (9 zonas, colisiones, triggers), FX (partículas, telegrafías)
  gameplay/ Player (Malakh), Enemies (Angel/Messenger/Archangel), Gabriel (boss), Systems (Farsa, Snare, Altar, Waves)
  ui/       HUD (barras, Farsa, boss, banners, diálogo)
test/     smoke.mjs (31 aserciones headless)
```

## Limitaciones conocidas (es un POC)

- Colisiones AABB/círculo simplificadas; sin física real.
- Malakh es un placeholder procedural sin rig; las animaciones son procedurales.
- Sin pathfinding: los ángeles persiguen en línea recta (los colisiones los contienen).
- El "planeo" se desbloquea tras Gabriel pero el nivel termina ahí — es gancho para Yesod.
