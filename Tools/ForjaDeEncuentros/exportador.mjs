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
      drop: e.drop
    };
  });

  // El sello del §7: una barrera por lado del perimetro.
  // bounds es un rectangulo alineado a los ejes (contrato §1.4): cuatro muros y
  // ninguna ambiguedad. Un poligono arbitrario queda fuera de v2 a proposito.
  const muros = [];
  const bb = enc.arena.bounds;
  const b = [
    { x: bb.min.x, y: bb.min.y }, { x: bb.max.x, y: bb.min.y },
    { x: bb.max.x, y: bb.max.y }, { x: bb.min.x, y: bb.max.y }
  ];
  for (let i = 0; i < b.length; i++) {
    const a = b[i], c = b[(i + 1) % b.length];
    const dx = c.x - a.x, dy = c.y - a.y;
    const largo = Math.hypot(dx, dy);
    if (largo < 1) continue;
    muros.push({
      clase: 'sello',
      etiqueta: `Forja_Sello_${i}`,
      pos: alMundo({ x: (a.x + c.x) / 2, y: (a.y + c.y) / 2 }, ALTURA_SELLO / 2),
      yaw: Math.atan2(dy, dx) * 180 / Math.PI,
      escala: {
        x: +(largo / 200).toFixed(4),
        y: +(GROSOR_SELLO / 200).toFixed(4),
        z: +(ALTURA_SELLO / 200).toFixed(4)
      }
    });
  }

  const marcas = [
    { clase: 'marca', etiqueta: 'Forja_Jugador', pos: alMundo(enc.jugador.pos, enc.jugador.cota) },
    enc.arena.trigger && { clase: 'marca', etiqueta: 'Forja_TriggerSello', pos: alMundo(enc.arena.trigger) },
    enc.arena.checkpoint && { clase: 'marca', etiqueta: 'Forja_Checkpoint', pos: alMundo(enc.arena.checkpoint) }
  ].filter(Boolean);

  return { offset: off, enemigos, muros, marcas };
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
    muros: plan.muros,
    marcas: plan.marcas
  });

  const { salida } = await python(`
import unreal, json, re
D = json.loads(r'''${datos}''')

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

informe = {"nivel": None, "borrados": 0, "colocados": [], "avisos": []}

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

def coloca(actor, spec):
    if actor is None:
        informe["avisos"].append("No se pudo crear " + spec["etiqueta"])
        return
    actor.set_actor_label(spec["etiqueta"])
    actor.tags = [unreal.Name("Forja"), unreal.Name(D["marca"]), unreal.Name(spec["clase"])]
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
    if a and e["arquetipo"] == "portador_del_estandarte":
        informe["avisos"].append(
            "OJO con " + e["etiqueta"] + ": el aura de buff/debuff del Inspector no existe todavia. "
            "Hoy pelea como un Vigilante, asi que no midas nada que dependa de ese buff.")

for m in D["muros"]:
    a = subsys.spawn_actor_from_class(unreal.BlockingVolume,
        unreal.Vector(m["pos"]["x"], m["pos"]["y"], m["pos"]["z"]),
        unreal.Rotator(0, 0, m["yaw"]))
    coloca(a, m)

for m in D["marcas"]:
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
  informe.resumen = {
    enemigos: informe.colocados.filter(c => c.clase === 'enemigo').length,
    sello: informe.colocados.filter(c => c.clase === 'sello').length,
    marcas: informe.colocados.filter(c => c.clase === 'marca').length,
    pedidos: plan.enemigos.length,
    desviados: informe.desviados.length
  };
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
