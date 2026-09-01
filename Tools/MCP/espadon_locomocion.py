# -*- coding: utf-8 -*-
"""Malakh deja de CAMINAR a una mano cuando lleva el Espadon.

    execute_python_code(code=open("Tools/MCP/espadon_locomocion.py").read())

EL DEFECTO. `espadon_montages.py` cambio los MONTAGES --ataques, rodadas,
reacciones--, pero no la LOCOMOCION: el idle, el andar y la guardia salen de los
blend spaces del AnimGraph, no de montages. Resultado: Malakh golpeaba a dos
manos y caminaba a una.

LO QUE ME ENCONTRE, Y QUE DEROGA LO QUE YO MISMO HABIA ESCRITO. Estaba anotado
que esto pedia "cirugia" porque DCS no contempla las dos manos. **Es falso, y lo
contrario esta a medio camino hecho:**

  - `E_CombatStyleAnim` YA tiene el valor `TwoHandedWeapon` (indice 4).
  - `BP_DCSLibrary.ConvertCombatStyleTagToAnim` YA mapea el tag
    `CombatStyle.Melee.Armed.TwoHandedWeapon` a ese indice.
  - Medido en PIE con el espadon equipado: el tag del componente de combate ES
    `CombatStyle.Melee.Armed.TwoHandedWeapon` y `CombatStyleAnim` vale 4.

Lo unico que faltaba era el POSE: en `ABP_CombatCharacter.GroundLocomotion`, el
`BlendListByEnum` tenia conectados los casos 0, 1, 2, 3 y 5 -- y el **4 suelto**.
DCS dejo el hueco hecho y sin rellenar.

QUE HACE ESTA PASADA
  1. `BS_DA_Espadon`: copia de `BS_1Hand` (mismos ejes Direction -180..180 y
     SpeedState 0..3, mismas 23 muestras) con cada animacion sustituida por su
     equivalente de combate del Two-Handed Sword Pack.
  2. Un `AnimGraphNode_BlendSpacePlayer` en `GroundLocomotion` con ese blend
     space, con `Direction` y `LocomotionSpeedState` en sus ejes, conectado al
     `BlendPose_4`.

LO QUE CUESTA, Y HAY QUE SABERLO. El punto 2 escribe sobre `ABP_CombatCharacter`,
que es de DCS y por tanto de pago: **si se reinstala el pack, se pierde**. Es una
modificacion viva mas, como el `enable_root_motion` de las secuencias. No habia
alternativa: el AnimGraph no se puede sobrescribir desde un hijo y duplicarlo
dentro de `DarkAngels/` esta prohibido por el repo publico.

LO QUE NO CUBRE. Es un reproductor de blend space, no una maquina de estados: las
otras cinco ramas SI tienen maquina (arranques, frenadas, giro sobre el sitio).
El andar y el idle salen bien; los giros bruscos no tendran el pivote que si
tienen a una mano. Cambiarlo pediria duplicar una maquina de estados entera, que
el MCP no expone.

LOS ENEMIGOS LO HEREDAN SOLOS: el Heraldo usa el mismo `ABP_CombatCharacter` y su
`DA_DA_Espadon` es `twoHanded=True`, asi que su estilo cae en el mismo caso 4.
Medido a medias, y conviene decirlo: verificado en PIE sobre MALAKH (foto de la
guardia a dos manos); en el Heraldo no se pudo escenificar porque no entra en
combate sin la percepcion real --teleportar al jugador se la rompe-- y
`CombatStyleAnim` no es editable en instancia.
"""
import unreal

BS_ORIG = "/Game/DynamicCombatSystem/DCS/Animations/OneHand/BS_1Hand"
BS_DEST = "/Game/DarkAngels/Animations/Espadon/BS_DA_Espadon"
ABP     = "/Game/DynamicCombatSystem/DCS/Animations/ABP_CombatCharacter"
GRAFO   = "GroundLocomotion"
PACK    = "/Game/Two_Handed_Sword/Animations/Sequence_UE5"

IDLE = "AS_Idle_Combat_Seq"

#: `Direction` es el eje X del blend space y en DCS el positivo es la DERECHA
#: (la muestra 90 del original es `Anim_1H_Walk_Right`).
def _por_direccion(familia, grados):
    if abs(grados) >= 180: return "AS_%s_Combat_B_180_Loop_Seq" % familia
    if grados == 135:  return "AS_%s_Combat_B_R_45_Loop_Seq" % familia
    if grados == -135: return "AS_%s_Combat_B_L_45_Loop_Seq" % familia
    if grados == 90:   return "AS_%s_Combat_F_R_90_Loop_Seq" % familia
    if grados == -90:  return "AS_%s_Combat_F_L_90_Loop_Seq" % familia
    if grados == 45:   return "AS_%s_Combat_F_R_45_Loop_Seq" % familia
    if grados == -45:  return "AS_%s_Combat_F_L_45_Loop_Seq" % familia
    return "AS_%s_Combat_F_0_Loop_Seq" % familia


def _indice_del_pack():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    return {str(a.package_name).split("/")[-1]: str(a.package_name)
            for a in ar.get_assets_by_path(PACK, recursive=True)}


def blend_space():
    """Copia BS_1Hand y le cambia las 23 animaciones por las del pack."""
    eal = unreal.EditorAssetLibrary
    idx = _indice_del_pack()
    if IDLE not in idx:
        raise RuntimeError("no esta el Two-Handed Sword Pack en " + PACK)
    if not eal.does_asset_exist(BS_DEST):
        if eal.duplicate_asset(BS_ORIG, BS_DEST) is None:
            raise RuntimeError("no pude duplicar " + BS_ORIG)
    bs = eal.load_asset(BS_DEST)
    # OJO: el editor devuelve COPIAS de los structs; hay que devolver cada una al
    # array y reasignar, igual que con las ranuras de equipo del Heraldo.
    nuevas = []
    for m in list(bs.get_editor_property("sample_data")):
        v = m.get_editor_property("sample_value")
        d, s = round(v.x), v.y
        familia = "Walk" if abs(s - 1.5) < 0.1 else ("Run" if s > 2.0 else None)
        nombre = IDLE if familia is None else _por_direccion(familia, d)
        if nombre not in idx:
            raise RuntimeError("falta la animacion " + nombre)
        m.set_editor_property("animation", eal.load_asset(idx[nombre]))
        nuevas.append(m)
    bs.set_editor_property("sample_data", nuevas)
    eal.save_asset(BS_DEST)


def _nodos():
    """Devuelve {tipo: [ids]} de los nodos que nos importan del AnimGraph."""
    import re
    out = {}
    for n in unreal.BlueprintService.get_nodes_in_graph(ABP, GRAFO):
        s = str(n)
        tipo = re.search(r'node_type: "([^"]+)"', s).group(1)
        out.setdefault(tipo, []).append(re.search(r'node_id: "([^"]+)"', s).group(1))
    return out


def cablear():
    """Mete el BlendSpacePlayer en el caso 4 del BlendListByEnum."""
    eal = unreal.EditorAssetLibrary
    ns = _nodos()
    enum = ns.get("AnimGraphNode_BlendListByEnum", [None])[0]
    if enum is None:
        raise RuntimeError("no encuentro el BlendListByEnum de GroundLocomotion")

    ya = ns.get("AnimGraphNode_BlendSpacePlayer", [])
    if not ya:
        r = unreal.BlueprintService.build_graph(
            ABP, GRAFO,
            [{"ref": "BS2H", "type": "spawner_key",
              "params": {"key": "NODE AnimGraphNode_BlendSpacePlayer"}}],
            [], [], False, False)
        if not r.success or r.nodes_created != 1:
            raise RuntimeError("no pude crear el BlendSpacePlayer")
        bsp = list(r.ref_to_node_id.values())[0] if hasattr(r.ref_to_node_id, "values") \
            else _nodos()["AnimGraphNode_BlendSpacePlayer"][0]
    else:
        bsp = ya[0]

    # el asset del blend space NO es un pin: se escribe en el struct del AnimNode
    bp = eal.load_asset(ABP)
    g = unreal.load_object(bp, GRAFO)
    obj = None
    for i in range(8):
        o = unreal.load_object(g, "AnimGraphNode_BlendSpacePlayer_%d" % i)
        if o is not None:
            obj = o
    if obj is None:
        raise RuntimeError("no encuentro el objeto del BlendSpacePlayer")
    nd = obj.get_editor_property("node")
    nd.set_editor_property("blend_space", eal.load_asset(BS_DEST))
    obj.set_editor_property("node", nd)

    unreal.BlueprintService.build_graph(
        ABP, GRAFO,
        [{"ref": "Dir", "type": "variable_get", "params": {"variable": "Direction"}},
         {"ref": "Vel", "type": "variable_get", "params": {"variable": "LocomotionSpeedState"}}],
        [{"from_": "Dir.Direction", "to": "%s.X" % bsp},
         {"from_": "Vel.LocomotionSpeedState", "to": "%s.Y" % bsp},
         {"from_": "%s.Pose" % bsp, "to": "%s.BlendPose_4" % enum}],
        [], True, True)
    unreal.BlueprintEditorLibrary.compile_blueprint(eal.load_asset(ABP))
    eal.save_asset(ABP)


def verificar():
    """Se relee todo: ni el guardado ni el `True` de build_graph son prueba."""
    import re
    eal = unreal.EditorAssetLibrary
    fallos = []

    bs = eal.load_asset(BS_DEST)
    if bs is None:
        return ["falta " + BS_DEST]
    ms = bs.get_editor_property("sample_data")
    if len(ms) != 23:
        fallos.append("el blend space tiene %d muestras y deberia tener 23" % len(ms))
    viejas = [m.get_editor_property("animation").get_name() for m in ms
              if "1H" in m.get_editor_property("animation").get_name()]
    if viejas:
        fallos.append("quedan animaciones de una mano: %s" % sorted(set(viejas)))

    ns = _nodos()
    enum = ns.get("AnimGraphNode_BlendListByEnum", [None])[0]
    bsp = ns.get("AnimGraphNode_BlendSpacePlayer", [None])[0]
    if enum is None or bsp is None:
        return fallos + ["falta el BlendListByEnum o el BlendSpacePlayer"]
    for nid, pines in ((enum, ("BlendPose_4",)), (bsp, ("X", "Y", "Pose"))):
        for p in unreal.BlueprintService.get_node_pins(ABP, GRAFO, nid):
            s = str(p)
            nom = re.search(r'pin_name: "([^"]+)"', s).group(1)
            if nom in pines and 'is_connected: True' not in s:
                fallos.append("el pin %s se quedo suelto" % nom)

    g = unreal.load_object(eal.load_asset(ABP), GRAFO)
    obj = None
    for i in range(8):
        o = unreal.load_object(g, "AnimGraphNode_BlendSpacePlayer_%d" % i)
        if o is not None: obj = o
    asignado = obj.get_editor_property("node").get_editor_property("blend_space") if obj else None
    if asignado is None or asignado.get_name() != "BS_DA_Espadon":
        fallos.append("el nodo no apunta a BS_DA_Espadon: %s" % asignado)
    return fallos


if __name__ == "__main__":
    blend_space()
    cablear()
    f = verificar()
    print("[OK] locomocion a dos manos cableada" if not f else "[FALLO]\n   " + "\n   ".join(f))
