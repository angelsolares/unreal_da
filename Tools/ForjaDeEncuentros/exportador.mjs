// Llevar el encuentro al editor, y traerlo de vuelta.
//
// Tres reglas, y las tres vienen de haberse quemado:
//
// 1. ESTO NO CAMBIA DE NIVEL. Coloca en el que tengas abierto y punto. La version
//    anterior creaba un nivel propio con new_level y dejo al editor sin mundo
//    cargado. Abrir mapas por Python es una operacion que en este proyecto tumba
//    el editor, y no vale la comodidad que da.
//
// 2. NO SE ESCRIBE EN UN NIVEL CARO SIN PEDIRLO. Si el nivel abierto es el
//    Malkuth Master o un _Sub, se bloquea salvo confirmacion expresa.
//
// 3. EL EDITOR MIENTE. Hay llamadas que devuelven exito sin haber hecho nada.
//    Aqui todo lo que se coloca se vuelve a LEER del editor y se compara con lo
//    que se pidio; lo que no cuadre sale en el informe.
//
// Y el offset: dentro de un _Sub los actores van en coordenadas del submapa, y
// la Level Instance les suma su transform. Escribir coordenadas del maestro
// dentro de un _Sub manda al actor a 66 km. Por eso `offset` es explicito.

import { python } from './puente.mjs';
import { oleadasDe } from './js/esquema.js';

/**
 * Donde BUSCAR el Blueprint de cada arquetipo.
 *
 * Ojo con quien manda: el JSON del encuentro NO lleva rutas (contrato §3), solo
 * el nombre de diseño. La equivalencia definitiva vive del lado de Unreal en un
 * Data Asset. Esta tabla es solo para que el exportador pueda colocar algo hoy;
 * el dia que exista ese Data Asset, sobra.
 */
// Ya NO hay suplente. El contrato lo dice claro: `BP_DA_WarriorAI` no es un
// arquetipo —es el generico sin equipo que invoca el GiantBoss— y colocarlo
// disfrazado de Vigilante era ensuciar la prueba. Los cinco Blueprints existen
// desde el 2026-08-23; si alguno faltara, el informe lo dice y no se coloca.
const BASE = '/Game/DarkAngels/Blueprints/Enemies/';

export const BLUEPRINTS = {
  lancero_del_alba:        { candidatas: [BASE + 'BP_DA_Lancero'] },
  arquero_del_firmamento:  { candidatas: [BASE + 'BP_DA_Arquero'] },
  escudero_celestial:      { candidatas: [BASE + 'BP_DA_Vigilante'] },
  elite_pesado:            { candidatas: [BASE + 'BP_DA_Heraldo'] },
  portador_del_estandarte: { candidatas: [BASE + 'BP_DA_Inspector'] }
};

const GROSOR_SELLO = 60;     // cm de espesor de las barreras del perimetro
const ALTURA_SELLO = 500;    // cm de alto: que no se salte
const TOLERANCIA = 2;        // cm de diferencia admitida al releer

/** Traduce el encuentro a lo que hay que colocar, ya en coordenadas de mundo. */
export function planificar(enc, opciones = {}) {
  // v2: el mapa es un nivel suelto, asi que el offset es 0 salvo que se pida.
  const off = opciones.offset || { x: 0, y: 0, z: 0 };
  const alMundo = (p, cota = 0) => ({
    x: Math.round(p.x + (off.x || 0)),
    y: Math.round(p.y + (off.y || 0)),
    z: Math.round((cota || 0) + (off.z || 0))
  });

  // Las oleadas del §6, numeradas. El indice es lo que se le escribe a cada
  // enemigo en Unreal: 1 entra al romper el sello, 2 cuando la 1 este limpia, y
  // asi. Es la unica forma que cabe hoy en `BP_DA_WeaponDropComponent`-style,
  // o sea un entero por instancia, sin arrays de structs — que por MCP se
  // comen el ultimo elemento.
  const olas = oleadasDe(enc).filter(o => !o.implicita);
  const indiceDeOleada = new Map();
  olas.forEach((o, i) => { for (const id of o.enemigos) indiceDeOleada.set(id, i + 1); });

  const enemigos = enc.enemigos.map(e => {
    const bp = BLUEPRINTS[e.arquetipo];
    return {
      id: e.id,
      clase: 'enemigo',
      arquetipo: e.arquetipo,
      // Se manda la lista y Unreal coge la primera que exista.
      candidatas: bp?.candidatas || [],
      // sin suplente: el contrato dice que BP_DA_WarriorAI no es un arquetipo
      etiqueta: `Forja_${e.arquetipo}_${e.etiqueta || String(e.id).slice(-4)}`.replace(/\s+/g, '_'),
      pos: alMundo(e.pos, e.cota),
      yaw: e.yaw ?? 180,
      drop: e.drop,
      oleada: indiceDeOleada.get(e.id) || 0     // 0 = sin oleadas, entra al principio
    };
  });

  // EL SELLO NO SE COLOCA A MANO. `BP_DA_Arena` se planta sus propios cuatro
  // muros en BeginPlay (ColocarMuros), con su trigger de entrada y sus bandas
  // de luz. Poner BlockingVolumes encima era duplicar la barrera y dejar fuera
  // todo lo demas que la arena trae: victoria, purga, checkpoint, watchdog y
  // reintento. Lo que se exportaba antes era un diorama, no un encuentro.
  //
  // OJO: la arena es CUADRADA (un solo RadioArena para X e Y) y el `bounds` del
  // encuentro es un rectangulo. Se coge el semilado MAYOR para que nada de lo
  // diseñado quede fuera del sello, y la diferencia se avisa.
  const bb = enc.arena.bounds;
  const centro = { x: (bb.min.x + bb.max.x) / 2, y: (bb.min.y + bb.max.y) / 2 };
  const semiX = (bb.max.x - bb.min.x) / 2;
  const semiY = (bb.max.y - bb.min.y) / 2;
  const radio = Math.round(Math.max(semiX, semiY));

  const arena = {
    clase: 'arena',
    etiqueta: 'Forja_Arena',
    pos: alMundo(centro, 0),
    radio,
    // AutoDetectarEnemigos los recoge solos por estar dentro del cuadrado; no
    // hay que enumerarlos. ReintentarAlMorir lo decide el encuentro.
    reintentar: !!(enc.arena && enc.arena.reintentarAlMorir),
    semiX: Math.round(semiX),
    semiY: Math.round(semiY)
  };

  // --- la geometria, que es lo que hace que la receta signifique algo --------
  //
  // Sin esto lo exportado es una caja vacia: el muro tras el que se cubren los
  // arqueros y el balcon a cota son PRECISAMENTE lo que crea la lectura del
  // §5.1 y lo que el simulador modela. Cubos de /Engine/BasicShapes escalados:
  // feos pero solidos, medibles y con la cota correcta. Vestirlos es trabajo de
  // arte, no del exportador.
  const caja = (r, clase, etiqueta, alturaZ, cotaBase) => {
    const anchoX = Math.abs(r.max.x - r.min.x);
    const anchoY = Math.abs(r.max.y - r.min.y);
    return {
      clase,
      etiqueta,
      // el cubo del motor mide 100 cm y su origen esta en el CENTRO
      pos: alMundo({ x: (r.min.x + r.max.x) / 2, y: (r.min.y + r.max.y) / 2 },
                   (cotaBase || 0) + alturaZ / 2),
      yaw: 0,
      escala: {
        x: +(anchoX / 100).toFixed(4),
        y: +(anchoY / 100).toFixed(4),
        z: +(alturaZ / 100).toFixed(4)
      }
    };
  };

  const solidos = [];
  for (const c of (enc.coberturas || [])) {
    solidos.push(caja(c, 'cobertura',
      `Forja_Cobertura_${c.id || solidos.length}`, c.altura || 200, c.cota || 0));
  }
  for (const pl of (enc.plataformas || [])) {
    // la plataforma es el SUELO a su cota: un tablero fino, no un bloque
    solidos.push(caja(pl, 'plataforma',
      `Forja_Plataforma_${pl.id || solidos.length}`, 40, (pl.cota || 0) - 40));
    // y cada acceso, una rampa: se coloca como cubo tumbado con el pitch justo
    for (const [k, ac] of (pl.accesos || []).entries()) {
      const dx = ac.hasta.x - ac.desde.x, dy = ac.hasta.y - ac.desde.y;
      const largo = Math.hypot(dx, dy);
      const subida = pl.cota || 0;
      solidos.push({
        clase: 'rampa',
        etiqueta: `Forja_Rampa_${pl.id || ''}_${k}`,
        pos: alMundo({ x: (ac.desde.x + ac.hasta.x) / 2,
                       y: (ac.desde.y + ac.hasta.y) / 2 }, subida / 2),
        yaw: Math.atan2(dy, dx) * 180 / Math.PI,
        pitch: -Math.atan2(subida, largo) * 180 / Math.PI,
        escala: {
          x: +(Math.hypot(largo, subida) / 100).toFixed(4),
          y: +((ac.ancho || 300) / 100).toFixed(4),
          z: 0.2
        }
      });
    }
  }

  // El arranque del jugador: un PlayerStart de verdad, no un TargetPoint. Sin
  // esto el encuentro no es jugable — apareces donde diga el GameMode.
  const marcas = [
    { clase: 'inicio', etiqueta: 'Forja_PlayerStart',
      pos: alMundo(enc.jugador.pos, enc.jugador.cota), yaw: enc.jugador.yaw ?? 0 },
    enc.arena.checkpoint && { clase: 'marca', etiqueta: 'Forja_Checkpoint',
      pos: alMundo(enc.arena.checkpoint) }
  ].filter(Boolean);

  // Suelo y luz. Un nivel de trabajo recien creado esta VACIO: sin suelo Malakh
  // se cae al vacio y sin luz no se ve nada, asi que el encuentro exportado no
  // seria jugable por mucho que los enemigos esten en su sitio.
  //
  // Solo se colocan si el nivel esta en blanco (lo decide el lado de Unreal
  // contando actores que no sean nuestros): si exportas sobre un mapa que ya
  // tiene terreno, poner un plano encima seria estropearlo.
  const escena = {
    suelo: {
      clase: 'suelo', etiqueta: 'Forja_Suelo',
      pos: alMundo(centro, -10),
      yaw: 0,
      // el plano del motor mide 100 cm; se pasa del radio para que haya
      // margen fuera del sello y no se vea el borde del mundo
      escala: { x: +((radio * 2.6) / 100).toFixed(3),
                y: +((radio * 2.6) / 100).toFixed(3), z: 1 }
    },
    luz: { clase: 'luz', etiqueta: 'Forja_Luz', pos: alMundo(centro, 1200), yaw: 0 }
  };

  // EL VOLUMEN DE NAVEGACION. Sin esto los enemigos PERCIBEN al jugador, le fijan
  // como objetivo... y no se mueven, porque no hay a donde pathfindear. Medido en
  // PIE el 25/08: el nivel exportado solo tenia `AbstractNavData`, la velocidad de
  // los de mele era 0 y `GetRandomReachablePointInRadius` devolvia None. Con el
  // volumen puesto, el `auto_create_navigation_data` del proyecto crea el
  // RecastNavMesh solo y el Lancero cruza 1.600 cm en diez segundos.
  //
  // Se pasa del radio a proposito (el suelo tambien) y cubre en Z desde bajo el
  // suelo hasta por encima del balcon mas alto: un balcon sin navmesh es un arquero
  // que no puede ni retroceder.
  const cotaMax = Math.max(0, ...(enc.plataformas || []).map(pl => pl.cota || 0));
  const navAlto = cotaMax + 700;
  const navegacion = {
    clase: 'navmesh', etiqueta: 'Forja_NavBounds',
    pos: alMundo(centro, navAlto / 2 - 250),
    yaw: 0,
    // el cubo del volumen mide 200 cm de lado
    escala: { x: +((radio * 2.1) / 200).toFixed(4),
              y: +((radio * 2.1) / 200).toFixed(4),
              z: +((navAlto + 500) / 200).toFixed(4) }
  };

  return {
    offset: off, enemigos, arena, solidos, marcas, escena, navegacion,
    oleadas: olas.map((o, i) => ({
      indice: i + 1, id: o.id, nombre: o.nombre,
      activacion: o.activacion, retardo: o.retardo, presencia: o.presencia,
      enemigos: o.enemigos.length
    }))
  };
}

// ------------------------------------------------------------------- exportar

/**
 * Nombres de nivel que NO se tocan sin decirlo a proposito. Malkuth Master es
 * horas de trabajo colocado a mano; llenarlo de actores por accidente seria
 * mucho mas caro de deshacer que de evitar.
 */
const NIVELES_PROTEGIDOS = [/Malkuth_Master/i, /_Sub$/i];

export async function exportar(cuerpo) {
  const { encuentro: enc, offset, confirmarNivel = false } = cuerpo;
  if (!enc?.enemigos) throw new Error('Falta el encuentro.');

  const plan = planificar(enc, { offset });

  // EL EXPORTADOR NO CAMBIA DE NIVEL. Nunca.
  //
  // La primera version llamaba a new_level/load_level para crear un nivel propio
  // del encuentro. Resultado: el editor se quedo SIN MUNDO CARGADO —ni actores ni
  // world— y hubo que reabrir el mapa a mano. Es el mismo agujero que ya estaba
  // documentado: cambiar de mapa por Python es una operacion que en este proyecto
  // tumba el editor. Aqui simplemente no se hace.
  //
  // Abres tu el nivel donde lo quieras, y esto coloca ahi. Mas aburrido y no se
  // come una tarde de trabajo.
  const datos = JSON.stringify({
    marca: `Forja:${enc.id}`,
    protegidos: NIVELES_PROTEGIDOS.map(r => r.source),
    confirmado: !!confirmarNivel,
    enemigos: plan.enemigos,
    oleadas: plan.oleadas,
    arena: plan.arena,
    solidos: plan.solidos,
    navegacion: plan.navegacion,
    marcas: plan.marcas,
    escena: plan.escena
  });

  const { salida } = await python(`
import unreal, json, re
D = json.loads(r'''${datos}''')

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

informe = {"nivel": None, "borrados": 0, "colocados": [], "avisos": [], "sinOleadas": []}

mundo = ues.get_editor_world()
if mundo is None:
    print(json.dumps({"bloqueado": "El editor no tiene ningun nivel abierto. Abre uno y vuelve a intentarlo."}))
    raise SystemExit

informe["nivel"] = mundo.get_name()

# Guardia: no llenar de actores un nivel caro sin que lo pidan a proposito.
if not D["confirmado"]:
    for patron in D["protegidos"]:
        if re.search(patron, informe["nivel"]):
            print(json.dumps({"bloqueado":
                "El nivel abierto es '" + informe["nivel"] + "', que esta protegido. "
                "Abre un nivel de trabajo, o marca la casilla de confirmar si de verdad quieres escribir ahi."}))
            raise SystemExit

# 2. Limpiar lo que puso una exportacion anterior. Solo lo NUESTRO: se reconoce
#    por la etiqueta de actor, nunca por la clase, para no barrer nada ajeno.
for a in subsys.get_all_level_actors():
    if D["marca"] in [str(t) for t in a.tags]:
        subsys.destroy_actor(a)
        informe["borrados"] += 1

def marcar(actor, spec):
    """Etiqueta y marca NADA MAS NACER.

    Si la colocacion revienta despues (poner una propiedad que no existe, por
    ejemplo), el actor ya queda reconocible y la siguiente pasada lo barre. Sin
    esto quedan huerfanos sin marca que ademas envenenan la deteccion de "nivel
    en blanco" para siempre. Paso de verdad con un DirectionalLight."""
    if actor is None:
        return None
    actor.set_actor_label(spec["etiqueta"])
    tags = [unreal.Name("Forja"), unreal.Name(D["marca"]), unreal.Name(spec["clase"])]
    # LA OLEADA VIAJA EN UN TAG, y se pone AQUI a proposito: esta funcion
    # REESCRIBE la lista entera de tags, asi que ponerlo despues lo borraria.
    #
    # El numero no vive en una variable del AI porque los cinco enemigos heredan
    # de BP_BaseAI, que es de DCS: seria una modificacion viva de un asset de
    # pago. Un tag lo tiene todo actor, se edita en Details > Actor > Tags y no
    # obliga a tocar ningun Blueprint. BP_DA_Arena lo lee al sellar.
    if int(spec.get("oleada", 0) or 0) > 1:
        tags.append(unreal.Name("Oleada" + str(int(spec["oleada"]))))
    actor.tags = tags
    return actor

def coloca(actor, spec):
    if actor is None:
        informe["avisos"].append("No se pudo crear " + spec["etiqueta"])
        return
    marcar(actor, spec)
    if "escala" in spec:
        s = spec["escala"]
        actor.set_actor_scale3d(unreal.Vector(s["x"], s["y"], s["z"]))
    # RELEER: no se apunta lo que se pidio, se apunta lo que el editor dice ahora.
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    informe["colocados"].append({
        "etiqueta": actor.get_actor_label(),
        "clase": spec["clase"],
        "pedido": [spec["pos"]["x"], spec["pos"]["y"], spec["pos"]["z"]],
        "real": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
        "yawReal": round(rot.yaw, 1)
    })

for e in D["enemigos"]:
    ruta = next((c for c in e["candidatas"] if unreal.EditorAssetLibrary.does_asset_exist(c)), None)
    if ruta is None:
        # Sin suplente a proposito: un enemigo que falta se DICE, no se disfraza.
        informe["avisos"].append(
            "FALTA el Blueprint de " + e["arquetipo"] + " ("
            + (e["candidatas"][0].split("/")[-1] if e["candidatas"] else "?")
            + "): " + e["etiqueta"] + " NO se coloca.")
        continue

    cls = unreal.EditorAssetLibrary.load_blueprint_class(ruta)
    # Rotator(roll, pitch, yaw) — comprobado en el editor. Y el convenio de yaw
    # coincide 1:1 con la herramienta: forward = (cos yaw, sin yaw).
    a = subsys.spawn_actor_from_class(cls,
        unreal.Vector(e["pos"]["x"], e["pos"]["y"], e["pos"]["z"]),
        unreal.Rotator(0, 0, e["yaw"]))
    coloca(a, e)
    # Releer el tag del actor vivo, que es lo unico que prueba que la oleada
    # viajo. marcar() lo pone, pero aqui se comprueba: el editor devuelve exito
    # en llamadas que no han hecho nada.
    if a is not None and int(e.get("oleada", 0) or 0) > 1:
        esperado = "Oleada" + str(int(e["oleada"]))
        if esperado not in [str(t) for t in a.tags]:
            informe["sinOleadas"].append(e["etiqueta"])
    if a and e["arquetipo"] == "portador_del_estandarte":
        informe["avisos"].append(
            "OJO con " + e["etiqueta"] + ": el aura de buff/debuff del Inspector no existe todavia. "
            "Hoy pelea como un Vigilante, asi que no midas nada que dependa de ese buff.")

# EL GAMEMODE DEL NIVEL. Sin esto sale BP_CombatCharacter -el personaje de demo
# de DCS- en vez de Malakh, y entonces no estas probando NADA de lo tuyo: ni la
# espada base, ni el ciclo de arma temporal, ni los descartes, ni el HUD.
# Verificado: exportado sin override, el pawn de PIE era BP_CombatCharacter_C.
GM = "/Game/DarkAngels/Blueprints/World/BP_DA_GameMode"
cls_gm = unreal.EditorAssetLibrary.load_blueprint_class(GM)
if cls_gm is None:
    informe["avisos"].append(
        "FALTA " + GM + ": el nivel se queda con el GameMode del proyecto y "
        "saldra el personaje de demo de DCS en vez de Malakh.")
else:
    ws = mundo.get_world_settings()
    antes = ws.get_editor_property("default_game_mode")
    ws.set_editor_property("default_game_mode", cls_gm)
    ahora = ws.get_editor_property("default_game_mode")
    informe["gamemode"] = {
        "antes": antes.get_name() if antes else None,
        "ahora": ahora.get_name() if ahora else None
    }
    if ahora is None or "BP_DA_GameMode" not in ahora.get_name():
        informe["avisos"].append("El GameMode del nivel NO quedo puesto: " + str(ahora))

# La ARENA: un solo actor que trae sello, victoria, purga, checkpoint, watchdog
# y reintento. Sin el, lo exportado no es jugable.
A = D["arena"]
ruta_arena = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena.BP_DA_Arena_C"
cls_arena = unreal.EditorAssetLibrary.load_blueprint_class(
    "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena")
if cls_arena is None:
    informe["avisos"].append("FALTA BP_DA_Arena: el encuentro se coloca SIN sello ni victoria.")
else:
    a = subsys.spawn_actor_from_class(cls_arena,
        unreal.Vector(A["pos"]["x"], A["pos"]["y"], A["pos"]["z"]),
        unreal.Rotator(0, 0, 0))
    marcar(a, A)
    if a is not None:
        a.set_editor_property("RadioArena", float(A["radio"]))
        a.set_editor_property("ReintentarAlMorir", bool(A["reintentar"]))
        # El margen entre oleadas. Es el hueco donde el jugador bebe y recoge lo
        # que solto el que acaba de caer; sin el, escalonar no descansa a nadie.
        if D.get("oleadas"):
            retardos = [o["retardo"] for o in D["oleadas"] if o["retardo"]]
            if retardos:
                try:
                    a.set_editor_property("RetardoEntreOleadas", float(max(retardos)))
                    leido = float(a.get_editor_property("RetardoEntreOleadas"))
                    if abs(leido - float(max(retardos))) > 0.01:
                        informe["avisos"].append(
                            "RetardoEntreOleadas pedido %s y el editor dice %s"
                            % (max(retardos), leido))
                except Exception:
                    informe["avisos"].append(
                        "BP_DA_Arena no tiene RetardoEntreOleadas: el margen entre"
                        " oleadas se queda en el que traiga por defecto.")
        # AutoDetectarEnemigos ya viene a True: recoge solo a los BP_BaseAI que
        # caigan dentro del cuadrado, asi que no hay que enumerarlos.
    coloca(a, A)
    if a is not None:
        leido = a.get_editor_property("RadioArena")
        if abs(leido - float(A["radio"])) > 0.5:
            informe["avisos"].append(
                "RadioArena pedido %s pero el editor dice %s" % (A["radio"], leido))
    if A["semiX"] != A["semiY"]:
        informe["avisos"].append(
            "La arena de Unreal es CUADRADA y el encuentro es %sx%s: se ha usado "
            "el semilado mayor (%s), asi que el sello queda mas ancho de lo "
            "diseñado en el lado corto." % (A["semiX"], A["semiY"], A["radio"]))

# El volumen de navegacion. Va SIEMPRE, no solo en nivel en blanco: sin el, los
# enemigos ven al jugador y no pueden ir a por el (medido en PIE, 25/08).
N = D["navegacion"]
nav = subsys.spawn_actor_from_class(unreal.NavMeshBoundsVolume,
    unreal.Vector(N["pos"]["x"], N["pos"]["y"], N["pos"]["z"]), unreal.Rotator(0, 0, 0))
marcar(nav, N)
if nav is not None:
    nav.set_actor_scale3d(unreal.Vector(N["escala"]["x"], N["escala"]["y"], N["escala"]["z"]))
    b = nav.get_actor_bounds(False)
    informe["colocados"].append({"etiqueta": N["etiqueta"], "clase": "navmesh",
        "pedido": [N["pos"]["x"], N["pos"]["y"], N["pos"]["z"]],
        "real": [round(b[0].x), round(b[0].y), round(b[0].z)],
        "extent": [round(b[1].x), round(b[1].y), round(b[1].z)]})
else:
    informe["avisos"].append("NO se pudo colocar el volumen de navegacion: los"
                             " enemigos veran al jugador pero no podran moverse.")

# Los solidos: coberturas, plataformas y rampas. Cubos del motor escalados.
cubo = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
for sdef in D["solidos"]:
    a = subsys.spawn_actor_from_class(unreal.StaticMeshActor,
        unreal.Vector(sdef["pos"]["x"], sdef["pos"]["y"], sdef["pos"]["z"]),
        unreal.Rotator(0, sdef.get("pitch", 0), sdef.get("yaw", 0)))
    marcar(a, sdef)
    if a is not None and cubo is not None:
        a.static_mesh_component.set_static_mesh(cubo)
        a.set_mobility(unreal.ComponentMobility.STATIC)
    coloca(a, sdef)

# Suelo y luz, SOLO si el nivel esta en blanco. Se cuenta antes de mirar nada
# mas: si hay algo que no sea nuestro, se supone que el mapa ya esta vestido.
# Los actores de navegacion NO cuentan como "ajenos": los crea el motor solo, en
# cuanto se coloca el volumen, y contarlos hacia que la propia exportacion se
# convenciera de que el nivel ya estaba habitado y se saltara el suelo y la luz.
IGNORAR = ("RecastNavMesh", "AbstractNavData", "NavMeshBoundsVolume",
           "NavigationData", "WorldPartitionMiniMap", "WorldDataLayers")
ajenos = [a for a in subsys.get_all_level_actors()
          if D["marca"] not in [str(t) for t in a.tags]
          and not a.get_actor_label().startswith("Forja_")
          and a.get_class().get_name() not in IGNORAR]
if ajenos:
    informe["avisos"].append(
        "El nivel ya tiene %d actores propios: NO se ha puesto suelo ni luz." % len(ajenos))
else:
    E = D["escena"]
    plano = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane")
    a = subsys.spawn_actor_from_class(unreal.StaticMeshActor,
        unreal.Vector(E["suelo"]["pos"]["x"], E["suelo"]["pos"]["y"], E["suelo"]["pos"]["z"]),
        unreal.Rotator(0, 0, 0))
    marcar(a, E["suelo"])
    if a is not None and plano is not None:
        a.static_mesh_component.set_static_mesh(plano)
        a.set_mobility(unreal.ComponentMobility.STATIC)
    coloca(a, E["suelo"])
    l = subsys.spawn_actor_from_class(unreal.DirectionalLight,
        unreal.Vector(E["luz"]["pos"]["x"], E["luz"]["pos"]["y"], E["luz"]["pos"]["z"]),
        unreal.Rotator(0, -50, -40))
    marcar(l, E["luz"])
    if l is not None:
        # el actor de luz no tiene set_mobility: la movilidad vive en su componente
        l.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    coloca(l, E["luz"])
    sk = subsys.spawn_actor_from_class(unreal.SkyLight,
        unreal.Vector(E["luz"]["pos"]["x"], E["luz"]["pos"]["y"], E["luz"]["pos"]["z"]),
        unreal.Rotator(0, 0, 0))
    marcar(sk, {"etiqueta": "Forja_Cielo", "clase": "luz"})
    if sk is not None:
        sk.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

# El arranque del jugador y el checkpoint.
for m in D["marcas"]:
    if m["clase"] == "inicio":
        a = subsys.spawn_actor_from_class(unreal.PlayerStart,
            unreal.Vector(m["pos"]["x"], m["pos"]["y"], m["pos"]["z"]),
            unreal.Rotator(0, 0, m.get("yaw", 0)))
    else:
        a = subsys.spawn_actor_from_class(unreal.TargetPoint,
            unreal.Vector(m["pos"]["x"], m["pos"]["y"], m["pos"]["z"]))
    coloca(a, m)

print(json.dumps(informe))
`);

  const informe = JSON.parse(salida.trim().split('\n').pop());

  if (informe.bloqueado) {
    const e = new Error(informe.bloqueado);
    e.codigo = 'nivel-protegido';
    throw e;
  }

  // La verificacion de verdad se hace AQUI, no en el editor: comparar lo pedido
  // con lo releido. Si algo no cuadra, sale con nombre y apellidos.
  informe.desviados = informe.colocados.filter(c =>
    c.pedido.some((v, i) => Math.abs(v - c.real[i]) > TOLERANCIA));
  const cuantos = clase => informe.colocados.filter(c => c.clase === clase).length;
  informe.resumen = {
    enemigos: cuantos('enemigo'),
    arena: cuantos('arena'),
    coberturas: cuantos('cobertura'),
    plataformas: cuantos('plataforma'),
    rampas: cuantos('rampa'),
    inicio: cuantos('inicio'),
    suelo: cuantos('suelo'),
    luz: cuantos('luz'),
    marcas: cuantos('marca'),
    pedidos: plan.enemigos.length,
    desviados: informe.desviados.length
  };
  // LAS OLEADAS SON PARTE DEL ENCUENTRO, NO UN ADORNO.
  //
  // `BP_DA_Arena` de hoy sabe sellar, vencer, purgar, reponer y vigilar, pero
  // NO sabe escalonar: sus propiedades son RadioArena, ReintentarAlMorir,
  // AutoDetectarEnemigos y Enemigos, y ninguna dice cuando entra cada uno
  // (leido del CDO el 2026-08-25). Mientras no exista, exportar una receta con
  // oleadas coloca a los cinco de golpe — que es un encuentro DISTINTO y, para
  // "Romper la linea", medido: 0% con espada sola contra el 94% escalonado.
  //
  // Se dice fuerte y se pone al principio del informe, porque el fallo de ayer
  // fue justo ese: exportar un diorama creyendo que era un encuentro.
  informe.oleadas = plan.oleadas;
  if (plan.oleadas.length && informe.sinOleadas?.length) {
    informe.avisos.unshift(
      `EL ESCALONADO NO HA VIAJADO: ${informe.sinOleadas.length} de ${plan.enemigos.length} enemigos se han `
      + `colocado sin numero de oleada porque su Blueprint no tiene la propiedad. `
      + `Tal como queda, los ${plan.enemigos.length} entran a la vez, que NO es el encuentro simulado. `
      + `Hace falta un entero "OleadaIndice" en el AI y que BP_DA_Arena active la oleada N+1 cuando la N `
      + `este limpia, esperando "RetardoEntreOleadas" segundos.`);
  }
  informe.offset = plan.offset;
  informe.guardado = false;
  informe.nota = 'El nivel NO se ha guardado. Revisalo en el editor y guarda tu.';
  return informe;
}

// ------------------------------------------------------------------- importar

/**
 * Trae de vuelta lo que hay colocado en el editor.
 * Sirve para dos cosas: cerrar el viaje de ida y vuelta (mover a un enemigo en
 * Unreal y volver a simular), y medir el suelo real en vez de un rectangulo.
 */
export async function importar(cuerpo = {}) {
  const offset = cuerpo.offset || { x: 0, y: 0, z: 0 };
  const { salida } = await python(`
import unreal, json
subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

mundo = ues.get_editor_world()
fuera = {"nivel": mundo.get_name() if mundo else None, "actores": []}
for a in subsys.get_all_level_actors():
    tags = [str(t) for t in a.tags]
    if "Forja" not in tags:
        continue
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    esc = a.get_actor_scale3d()
    fuera["actores"].append({
        "etiqueta": a.get_actor_label(),
        "clase": a.get_class().get_name(),
        "tags": tags,
        "pos": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
        "yaw": round(rot.yaw, 1),
        "escala": [round(esc.x, 3), round(esc.y, 3), round(esc.z, 3)]
    })
print(json.dumps(fuera))
`);

  const bruto = JSON.parse(salida.trim().split('\n').pop());
  const alLocal = (p) => ({
    x: Math.round(p[0] - (offset.x || 0)),
    y: Math.round(p[1] - (offset.y || 0))
  });

  return {
    nivel: bruto.nivel,
    offset,
    enemigos: bruto.actores.filter(a => a.tags.includes('enemigo')).map(a => ({
      etiqueta: a.etiqueta,
      pos: alLocal(a.pos),
      cota: Math.round(a.pos[2] - (offset.z || 0)),
      yaw: a.yaw
    })),
    sello: bruto.actores.filter(a => a.tags.includes('sello')).length,
    marcas: bruto.actores.filter(a => a.tags.includes('marca')).map(a => ({
      etiqueta: a.etiqueta, pos: alLocal(a.pos)
    })),
    total: bruto.actores.length
  };
}

export const TRABAJOS = { exportar, importar };
