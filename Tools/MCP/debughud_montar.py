import json

# DA Debug HUD (fase 1) — arquitectura base + seccion WORLD.
#
# COMO ENCAJA CON LO QUE YA HAY, sin romperlo:
#
#   BP_DA_HUD (el AHUD del juego, ya existente)
#     - dibuja objetivo, banner de zona y el panel de salto por NumPad
#     - se le anaden DOS FUNCIONES VACIAS, `DbgTick` y `DbgDibujar`, y sus dos
#       llamadas a la cabeza de EventTick y ReceiveDrawHUD. Nada mas. Vacias no
#       hacen nada, asi que el juego sigue igual.
#
#   BP_DA_DebugHUD (nuevo, hijo de BP_DA_HUD, en /Game/DarkAngels/Debug)
#     - SOBREESCRIBE esas dos funciones: aqui vive TODO el Debug HUD
#     - hereda intacto lo que dibuja el padre, sin tocar su grafo
#
# Por que no se sobreescriben directamente ReceiveDrawHUD/EventTick: en 5.8 no
# existe nodo "call to parent function" (comprobado con find_node_types), asi
# que sobreescribir un evento del padre PERDERIA lo que el padre dibuja. Las dos
# funciones-gancho son la unica forma de extender sin perder nada.
#
# POR QUE NO HAY AddHitBox: ese nodo pide Vector2D y en este build **no existe
# ningun nodo MakeVector2D**. Los clics se resuelven a mano: se lee la posicion
# del raton y se compara contra los rectangulos. Sale mejor, ademas, porque la
# lista de destinos puede crecer sin anadir un boton ni un nombre de hit box.
#
# LA TECLA: ni F8 ni ninguna F. En PIE, F8 es Eject/Possess del editor y F1-F10
# las captura el viewport para los modos de vista (ya mordio con el salto de
# zona, ver las notas). Se usan Period (.) y Decimal (. del teclado numerico),
# libres en el juego y en el editor.

CARPETA = "/Game/DarkAngels/Debug"
PADRE = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
HIJO = CARPETA + "/BP_DA_DebugHUD.BP_DA_DebugHUD"
DATOS = CARPETA + "/DA_DA_DebugDestinos.DA_DA_DebugDestinos"

# Diagnostico: abre el panel solo en el primer frame y cuenta los widgets que
# encuentra. Sirve para probar el ciclo completo de abrir/ocultar sin poder
# teclear. Dejar en False para el uso normal.
AUTO_ABRIR = False

TECLAS = ["Period", "Decimal"]
PESTANAS = ["WORLD", "PLAYER", "COMBAT", "AI", "BOSS", "STORY", "FINISHERS",
            "WEAPON"]

# --- Geometria del panel.
#
# NADA de aqui es una coordenada final: son medidas en "unidades de panel" que
# se convierten en cada frame con dos cosas de tiempo de ejecucion:
#
#   `esc` = DbgEscala, el zoom del panel, ajustable desde el propio HUD
#   `px`  = borde izquierdo, calculado del ancho del viewport para centrarlo
#
# Todo pasa por los ayudantes X() / Y() / SC(), y de ahi salen A LA VEZ el
# dibujado y el enrutado de clics: por construccion no se pueden descuadrar.
PY, PW = 92.0, 580.0        # PY es fijo: deja hueco al banner de objetivo
TAB_W, TAB_H, TAB_SEP = 139.0, 28.0, 143.0
TAB_Y0 = 46.0               # desplazamiento desde el borde superior del panel
FILA = 26.0                 # alto de fila de la lista de destinos
BOTON_H = 26.0
# El cue de click. NO usar los UI_*_MS: los MetaSounds de UI matan el editor.
CUE_CLICK = "/Game/CustomAssets/CommentaryBox/Audio/Text_Pop_Cue.Text_Pop_Cue"
# La lista arranca en 238 y el titulo TELEPORT se dibuja 26 por encima (212).
# El bloque de INFORMACION acaba en 190, asi que quedan 22 de separacion: lo
# mismo que hay entre sus propias lineas. Con los valores anteriores (204 y 210)
# el titulo se comia la linea de FPS.
LISTA_Y0 = 238.0
# Tamano por defecto: un paso por encima del anterior, que se leia justo.
#
# El techo no es el gusto sino la pantalla. Para que 1.30 siguiera cabiendo se
# apretaron los espaciados verticales (bloque de informacion y filas de
# botones): el contenido paso de ~750 a ~700 unidades, que a 1.30 son ~910 px
# mas los 92 del margen superior. En un viewport de 964 el boton de cerrar
# entra; lo unico que puede quedar rozando el borde es la linea de mensaje.
# Para eso estan los botones de tamano, y viven en la CABECERA justo por esto.
ESCALA_DEF = 1.30
ESCALA_MIN, ESCALA_MAX, ESCALA_PASO = 0.8, 2.2, 0.15
TAM_MENOS, TAM_MAS = 400.0, 440.0   # botones de zoom, en la cabecera

VARIABLES = [
    ("DbgVisible", "bool", None), ("DbgTab", "int", None),
    ("DbgFps", "float", None), ("DbgLineas", "string", "ARRAY"),
    ("DbgGuardadaLoc", "Vector", None), ("DbgGuardadaRot", "Rotator", None),
    ("DbgTieneGuardada", "bool", None), ("DbgInicioLoc", "Vector", None),
    ("DbgInicioRot", "Rotator", None), ("DbgTieneInicio", "bool", None),
    ("DbgMensaje", "string", None), ("DbgHabilitado", "bool", None),
    ("DbgEscala", "float", None),
    ("DbgSobreBoton", "bool", None),
    # --- PLAYER ---
    ("DbgGod", "bool", None), ("DbgManaInf", "bool", None),
    ("DbgMovMult", "float", None),
    # --- AI ---
    ("DbgTipos", "string", "ARRAY"), ("DbgEncuentros", "string", "ARRAY"),
    ("DbgTipoSel", "int", None), ("DbgCantSel", "int", None),
    ("DbgDistSel", "float", None),
    ("DbgCongelada", "bool", None), ("DbgApagada", "bool", None),
    ("DbgIgnorar", "bool", None),
    # --- BOSS ---
    ("DbgBosses", "string", "ARRAY"), ("DbgBossSel", "int", None),
    # --- STORY ---
    ("DbgCheckSel", "int", None),
    # --- COMBAT ---
    ("DbgDmgMult", "float", None), ("DbgEnemyMult", "float", None),
    ("DbgOneHit", "bool", None), ("DbgCfgLista", "bool", None), ("DbgLogOn", "bool", None),
    ("DbgLog", "string", "ARRAY"),
    ("DbgLastHP", "float", None), ("DbgLastHPObj", "float", None),
    ("DbgTrazas", "bool", None), ("DbgColisiones", "bool", None),
]

# --- API de DCS que usa la pestana PLAYER -----------------------------------
#
# NADA de esto toca variables internas: son las funciones publicas del propio
# DCS, que se ofrecen como MENSAJES DE INTERFAZ (`Interface|GetStatValue`,
# `Reactions|Kill`...). Las funciones de los componentes NO son invocables por
# esta API — solo sus accesores de variable— asi que la via buena es esta.
DCS_STATS = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/StatsManager/"
             "BP_StatsManagerComponent.BP_StatsManagerComponent_C")
DCS_TARGET = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/"
              "BP_DynamicTargetingComponent.BP_DynamicTargetingComponent_C")
RESPAWN = "/Game/DarkAngels/Blueprints/World/BP_RespawnVolume.BP_RespawnVolume_C"
DATOS_ENEM = CARPETA + "/DA_DA_DebugEnemigos.DA_DA_DebugEnemigos"
FILA_AI = 24.0
DCS_AI = "/Game/DynamicCombatSystem/DCS/Blueprints/AI/BP_BaseAI.BP_BaseAI_C"
DA_ARENA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena.BP_DA_Arena_C"
DCS_COLL = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/CollisionHandler/"
            "BP_CollisionHandlerComponent.BP_CollisionHandlerComponent_C")
TAG_DMG = "Stat.Damage"
LOG_MAX = 8
TAG_HP = "Stat.Health.Current"
TAG_HP_MAX = "Stat.Health.Max"
TAG_MANA = "Stat.Mana.Current"
TAG_MANA_MAX = "Stat.Mana.Max"

ORO = "(Utilities|Struct|MakeLinearColor 1.0 0.86 0.42 1.0)"
HUESO = "(Utilities|Struct|MakeLinearColor 0.88 0.91 0.97 1.0)"
GRIS = "(Utilities|Struct|MakeLinearColor 0.55 0.58 0.66 1.0)"
FONDO = "(Utilities|Struct|MakeLinearColor 0.02 0.02 0.05 0.86)"
BOTON = "(Utilities|Struct|MakeLinearColor 0.14 0.15 0.21 0.95)"
BOTON_ON = "(Utilities|Struct|MakeLinearColor 0.35 0.28 0.10 0.95)"


def bp(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def ast(t, a):
    return execute_tool("editor_toolset.toolsets.asset.AssetTools." + t,
                        json.dumps(a))["returnValue"]


def obj(t, a):
    return execute_tool("editor_toolset.toolsets.object.ObjectTools." + t,
                        json.dumps(a))["returnValue"]


def SC(v):
    """Una medida (ancho, alto, tamano de letra) escalada."""
    return "(* %.2f esc)" % v


def X(desplazamiento):
    """X final desde el borde izquierdo del panel."""
    return "(+ px %s)" % SC(desplazamiento)


def Y(desplazamiento):
    """Y final desde el borde superior del panel."""
    return "(+ %.1f %s)" % (PY, SC(desplazamiento))


def texto(x, y, cadena, color=HUESO, escala=1.0):
    """DrawText posicional: self, Text, Color, X, Y, Font=0, Scale.

    El Font va a 0 a proposito: con una fuente distance-field el canvas no
    dibuja nada (ya paso), y con 0 cae a la del motor, que si sale."""
    return '  (HUD|DrawText self %s %s %s %s 0 %s)' % (cadena, color, x, y, SC(escala))


def rect(x, y, w, h, color):
    return '  (HUD|DrawRect self %s %s %s %s %s)' % (color, x, y, w, h)


# Cabecera obligatoria de toda funcion que dibuje o que resuelva clics: define
# el zoom y el borde izquierdo del panel.
BIND_GEO = ('  (bind esc (Variables|Default|GetDbgEscala))\n'
            '  (bind px (- (* (.x (Viewport|GetViewportSize)) 0.5) %s))' % SC(PW / 2.0))


def tab_pos(i):
    """(desplazamiento en X, desplazamiento en Y) desde la esquina del panel."""
    return (6.0 + (i % 4) * TAB_SEP, TAB_Y0 + (i // 4) * 32.0)


# ###########################################################################
# ##  DEUDA SALDADA el 2026-08-24 — pero la regla sigue en pie             ##
# ###########################################################################
#
# Durante un dia este script fue POR DETRAS del asset: tres mejoras se habian
# hecho por CIRUGIA sobre `BP_DA_DebugHUD` (create_node/connect_pins) y nunca
# se portaron aqui, asi que una pasada se las llevaba por delante. Paso de
# verdad el 2026-08-23 a las 15:38 y hubo que recuperar el .uasset con
# `git checkout`.
#
# YA ESTAN LAS TRES AQUI: los sonidos (`dsl_sonar_panel`, `dsl_sonar_click`),
# el resalte de hover (`dsl_hover_boton`, `dsl_hover_tabs`) y el spawn encarado
# (el `FindLookAtRotation` dentro de `dsl_spawn_uno`). La pasada es segura.
#
# La comprobacion, por si alguien vuelve a hacer cirugia y se olvida de portarla:
#
#   python -c "import debughud_montar as d; print(hasattr(d,'dsl_hover_boton'))"
#
# Se pregunta por la FUNCION, no por el nombre en texto: este comentario ya los
# menciona y un grep se enganaria.
#
# LA REGLA DE FONDO NO CAMBIA: sobre este Blueprint no se hace cirugia. Lo que
# no entre por aqui, se pierde en la siguiente regeneracion. Y la regeneracion
# es TODO O NADA: un corte a mitad te deja sin panel.
# ###########################################################################

# ---------------------------------------------------------------- grafos

def dsl_permitido():
    """El interruptor por el que pasa TODA accion de debug antes de hacer nada.

    NO se usa la configuracion de build, y no por pereza: `Development|
    GetBuildConfiguration` **no se puede cablear a nada desde Blueprint por
    esta API**. Probadas y fallidas las tres vias: `==` directo, dentro de un
    `and`, y por el pin comodin de `EnumtoString` — incluso conectando a mano
    con `connect_pins`, que da "Could not connect pin ReturnValue to
    Enumerator". Y no existe `SwitchonEBuildConfiguration` ni un getter de
    console variable.

    La proteccion de verdad para Shipping es otra, y es mas fuerte que un `if`:
    la carpeta /Game/DarkAngels/Debug esta en DirectoriesToNeverCook, asi que
    en un build empaquetado **estos assets no existen**, y el actor del nivel
    los pide por referencia BLANDA, que devuelve nulo sin romper nada.
    Este booleano es solo el interruptor manual, para apagarlo en el editor."""
    return ('(fn DbgPermitido ()\n'
            '  (return (Variables|Default|GetDbgHabilitado)))')


# ------------------------------------------------------- hover y sonido de UI
#
# PORTADO DEL ASSET el 2026-08-23. Estas cuatro se habian hecho por cirugia
# (`create_node`/`connect_pins`) sobre el .uasset y NO estaban aqui, asi que la
# regeneracion del 15:38 se las llevo por delante. Se recuperaron con
# `git checkout` del binario y se leyeron con `read_graph_dsl`.
#
# OJO al portar desde el lector: `read_graph_dsl` COLAPSA los nodos de varias
# salidas. `Game|Player|GetMousePosition` devuelve (LocationX, LocationY,
# ReturnValue) EN ESE ORDEN -medido con get_node_type_pins el 24/08; el
# comentario decia (bool, X, Y) y por eso el multi-bind cableaba al reves- y
# el lector lo
# imprime como si fuera un valor suelto repetido cuatro veces. Pegarlo tal cual
# crea cuatro nodos y cablea el pin equivocado. Por eso aqui va con multi-bind.

def dsl_hover_boton():
    """Resalte del boton bajo el raton. La llama `DbgBoton` al final.

    El alto que asume (26*esc) es el de un boton; las pestañas miden 28*esc y
    reusan esta funcion — 2 px de diferencia, imperceptible."""
    return ('(fn DbgHoverBoton (X Y W)\n'
            '  (bind esc (Variables|Default|GetDbgEscala))\n'
            '  (bind alto (* %.1f esc))\n'
            '  (bind (mx my hay) (Game|Player|GetMousePosition'
            ' (Game|GetPlayerController 0)))\n'
            '  (if (and hay (and (and (>= mx X) (< mx (+ X W)))'
            ' (and (>= my Y) (< my (+ Y alto)))))\n'
            '    (Variables|Default|SetDbgSobreBoton true)\n'
            '    (HUD|DrawRect self'
            ' (Utilities|Struct|MakeLinearColor 1.0 1.0 1.0 0.13) X Y W alto)\n'
            '    (HUD|DrawRect self'
            ' (Utilities|Struct|MakeLinearColor 1.0 0.78 0.3 1.0)'
            ' X Y (* 4.0 esc) alto)))' % BOTON_H)


def dsl_hover_tabs():
    """Lo que `DbgBoton` no cubre: las 7 pestañas y los dos botones TAM +/-,
    que `DbgDibujar` pinta con DrawRect sueltos.

    Recalcula sus 9 rects con la MISMA formula que `DbgClick`, para que no se
    puedan descuadrar."""
    lin = []
    lin.append('(fn DbgHoverTabs ()\n')
    lin.append('  (bind esc (Variables|Default|GetDbgEscala))\n')
    lin.append('  (bind vp (Math|Conversions|ToVector(Vector2D)'
               ' (Viewport|GetViewportSize)))\n')
    lin.append('  (bind base (- (* (.x vp) 0.5) (* 290.0 esc)))\n')
    lin.append('  (bind fila1 (+ 92.0 (* 46.0 esc)))\n')
    lin.append('  (bind fila2 (+ 92.0 (* 78.0 esc)))\n')
    lin.append('  (bind w (* 139.0 esc))\n')
    for y in ("fila1", "fila2"):
        for dx in (6.0, 149.0, 292.0, 435.0):
            if y == "fila2" and dx == 435.0:
                continue          # la fila 2 solo tiene 3 pestañas
            lin.append('  (CallFunction|DbgHoverBoton :X (+ base (* %.1f esc))'
                       ' :Y %s :W w)\n' % (dx, y))
    for dx in (400.0, 440.0):
        lin.append('  (CallFunction|DbgHoverBoton :X (+ base (* %.1f esc))'
                   ' :Y (+ 92.0 (* 10.0 esc)) :W (* 30.0 esc))\n' % dx)
    lin.append('  (return))')
    return "".join(lin)


def dsl_sonar_click():
    """Suena solo si el clic cayo en un boton, no en hueco. Va empalmada en la
    ENTRADA de `DbgClick`, que es cuando `DbgSobreBoton` aun vale del ultimo
    dibujado."""
    return ('(fn DbgSonarClick ()\n'
            '  (if (Variables|Default|GetDbgSobreBoton)\n'
            '    (Audio|PlaySound2D "%s" 0.7))\n'
            '  (return))' % CUE_CLICK)


def dsl_sonar_panel():
    """El mismo cue al abrir y cerrar, distinguidos por TONO: 1.25 al abrir,
    0.75 al cerrar.

    Se llama DESPUES del `SetDbgVisible` para que lea el estado ya cambiado y
    elija el tono sola."""
    return ('(fn DbgSonarPanel ()\n'
            '  (if (Variables|Default|GetDbgVisible)\n'
            '    (Audio|PlaySound2D "%s" 0.8 1.25)\n'
            '    (else\n'
            '      (Audio|PlaySound2D "%s" 0.8 0.75)))\n'
            '  (return))' % (CUE_CLICK, CUE_CLICK))


def dsl_boton():
    # Recibe X/Y/W ya en pixeles; el alto y el texto los escala ella misma.
    return ('(fn DbgBoton (X Y W Etiqueta Encendido)\n'
            '  (bind esc (Variables|Default|GetDbgEscala))\n'
            '  (if Encendido\n'
            + rect("X", "Y", "W", SC(BOTON_H), BOTON_ON) + '\n'
            '    (else\n'
            + rect("X", "Y", "W", SC(BOTON_H), BOTON) + '))\n'
            + texto("(+ X %s)" % SC(10.0), "(+ Y %s)" % SC(4.0), "Etiqueta") + '\n'
            # El resalte va al FINAL, encima de lo ya pintado.
            '  (CallFunction|DbgHoverBoton :X X :Y Y :W W)\n'
            '  (return))')


def dsl_escalar():
    """Cambia el zoom del panel desde el propio panel, con tope arriba y abajo."""
    return ('(fn DbgEscalar (Delta)\n'
            '  (bind v (+ (Variables|Default|GetDbgEscala) Delta))\n'
            '  (Variables|Default|SetDbgEscala'
            ' (select (< v %.2f) %.2f (select (> v %.2f) %.2f v)))\n'
            '  (Variables|Default|SetDbgMensaje "Tamano del panel cambiado")\n'
            '  (return))'
            % (ESCALA_MIN, ESCALA_MIN, ESCALA_MAX, ESCALA_MAX))


def dsl_cargar():
    # Los destinos se leen del Data Asset una sola vez y se cachean.
    return ('(fn DbgCargar ()\n'
            '  (CallFunction|DbgCfgCargar)\n'
            '  (if (> (Utilities|Array|Length (Variables|Default|GetDbgLineas)) 0)\n'
            '    (return))\n'
            '  (bind datos (Variables|Default|GetDbgDatos))\n'
            '  (Utilities|IsValid datos\n'
            '    (:"Is Valid"\n'
            '      (Variables|Default|SetDbgLineas'
            ' (Class|BPDADebugDestinos|GetDestinos :self datos)))\n'
            '    (:"Is Not Valid")))')


def dsl_campo():
    # Campo N de la linea del destino I. Formato de linea:
    #   Nombre | Categoria | X=.. Y=.. Z=.. | P=.. Y=.. R=.. | Descripcion
    return ('(fn DbgCampo (Indice Campo)\n'
            '  (bind lineas (Variables|Default|GetDbgLineas))\n'
            '  (if (not (Utilities|Array|IsValidIndex lineas Indice))\n'
            '    (return ""))\n'
            '  (bind partes (Utilities|String|ParseIntoArray'
            ' (Utilities|Array|Get(acopy) lineas Indice) "|" true))\n'
            '  (if (not (Utilities|Array|IsValidIndex partes Campo))\n'
            '    (return ""))\n'
            '  (return (Utilities|String|Trim (Utilities|Array|Get(acopy) partes Campo))))')


def dsl_ocultar_juego():
    """Apaga los widgets UMG del juego mientras el panel esta abierto.

    NO es una cuestion de orden de dibujado y no se puede arreglar moviendo las
    llamadas: Slate compone los widgets UMG **siempre por encima** del canvas
    del HUD, asi que las barras de vida y los slots de arma/escudo/objeto de DCS
    se pintan sobre el panel hagas lo que hagas. La unica salida es esconderlos.

    Se guarda la lista de los que se escondieron y solo se restauran esos: si se
    encendieran todos a la vuelta, apareceria en pantalla algun menu que estaba
    oculto a proposito."""
    diag = ('    (Development|PrintString'
            ' :InString (Utilities|String|Append "DBG widgets encontrados: "'
            ' (Utilities|String|ToString(Integer) (Utilities|Array|Length ws)))'
            ' :bPrintToScreen false :bPrintToLog true :Duration 8.0)\n'
            if AUTO_ABRIR else '')
    diag2 = ('    (Development|PrintString'
             ' :InString (Utilities|String|Append "DBG widgets ocultados: "'
             ' (Utilities|String|ToString(Integer)'
             ' (Utilities|Array|Length (Variables|Default|GetDbgOcultadas))))'
             ' :bPrintToScreen false :bPrintToLog true :Duration 8.0)\n'
             if AUTO_ABRIR else '')
    # Sonda incondicional: mide a la vez el parametro que llega y cuantos
    # widgets encuentra, sin depender de en que rama entre ni del orden de
    # pines de SelectString (que ya me ha enganado hoy).
    entrada = ('  (Development|PrintString :InString'
               ' (Utilities|String|Append'
               ' (Utilities|String|Append "DBG entra Ocultar="'
               ' (Utilities|String|ToString(Boolean) Ocultar))'
               ' (Utilities|String|Append "  widgets="'
               ' (Utilities|String|ToString(Integer) (Utilities|Array|Length'
               ' (Widget|GetAllWidgetsOfClass :WidgetClass "/Script/UMG.UserWidget"'
               ' :TopLevelOnly true)))))'
               ' :bPrintToScreen false :bPrintToLog true :Duration 8.0)\n'
               if AUTO_ABRIR else '')
    return ('(fn DbgOcultarJuego (Ocultar)\n'
            + entrada +
            '  (if Ocultar\n'
            '    (bind ws (Widget|GetAllWidgetsOfClass'
            ' :WidgetClass "/Script/UMG.UserWidget" :TopLevelOnly true))\n'
            + diag +
            '    (for w ws\n'
            '      (if (Widget|IsVisible :self w)\n'
            '        (Utilities|Array|Add'
            ' :TargetArray (Variables|Default|GetDbgOcultadas) :NewItem w)\n'
            '        (Widget|SetVisibility :self w :InVisibility "Hidden")))\n'
            + diag2 +
            '    (else\n'
            '      (for w (Variables|Default|GetDbgOcultadas)\n'
            '        (Widget|SetVisibility :self w :InVisibility "Visible"))\n'
            '      (Utilities|Array|Clear'
            ' :TargetArray (Variables|Default|GetDbgOcultadas))))\n'
            '  (return))')


def dsl_toggle():
    sonda = ('  (Development|PrintString :InString "DBG toggle"'
             ' :bPrintToScreen false :bPrintToLog true :Duration 5.0)\n'
             if AUTO_ABRIR else '')
    # OJO CON EL ORDEN, que aqui hubo un fallo de los silenciosos:
    #
    # Antes se calculaba `v = (not DbgVisible)` y se usaba en varios sitios
    # DESPUES de haber hecho `SetDbgVisible(v)`. Pero `not` y el getter son
    # nodos PUROS: **se reevaluan cada vez que alguien tira de su salida**, no
    # se calculan una vez. Asi que el primer consumidor recibia `true` y el
    # segundo —ya con la variable cambiada— recibia `false`. Resultado:
    # `DbgOcultarJuego` se llamaba con Ocultar=false y no escondia nada, sin
    # error ninguno. Se cazo imprimiendo el parametro dentro de la funcion.
    #
    # La regla: escribir la variable PRIMERO y que todos los demas LEAN LA
    # VARIABLE, que ya no cambia. Un `bind` sobre un nodo puro no cachea nada.
    return ('(fn DbgToggle ()\n'
            + sonda +
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Variables|Default|SetDbgVisible'
            ' (not (Variables|Default|GetDbgVisible)))\n'
            # DESPUES del Set, para que lea el estado ya cambiado
            # y elija el tono solo.
            '  (CallFunction|DbgSonarPanel)\n'
            '  (CallFunction|DbgOcultarJuego'
            ' :Ocultar (Variables|Default|GetDbgVisible))\n'
            '  (bind pc (Game|GetPlayerController 0))\n'
            '  (Class|PlayerController|SetShowMouseCursor :self pc'
            ' :bShowMouseCursor (Variables|Default|GetDbgVisible))\n'
            '  (bind pawn (Game|GetPlayerPawn 0))\n'
            '  (Utilities|IsValid pawn\n'
            '    (:"Is Valid"\n'
            '      (if (Variables|Default|GetDbgVisible)\n'
            '        (Input|DisableInput :self pawn :PlayerController pc)\n'
            '        (else\n'
            # Al cerrar no basta con EnableInput: eso solo repone el componente
            # de input del pawn. Si algo dejo desequilibrado el contador de
            # IgnoreMoveInput, WASD sigue muerto y el resto del input funciona,
            # que es exactamente como se manifesto el fallo.
            '          (Input|EnableInput :self pawn :PlayerController pc)\n'
            '          (Input|ResetIgnoreMoveInput :self pc)\n'
            '          (Input|SetInputModeGameOnly :PlayerController pc))))\n'
            '    (:"Is Not Valid")))')


def dsl_tick():
    # Sobreescribe la funcion vacia del padre. Se llama desde EventTick.
    l = ['(fn DbgTick ()',
         '  (if (not (CallFunction|DbgPermitido))',
         '    (return false))',
         '  (bind dt (Utilities|Time|GetWorldDeltaSeconds))',
         '  (if (> dt 0.0)',
         '    (Variables|Default|SetDbgFps',
         '      (+ (* (Variables|Default|GetDbgFps) 0.9) (* (/ 1.0 dt) 0.1))))',
         '  (bind pc (Game|GetPlayerController 0))',
         '  (bind pawn (Game|GetPlayerPawn 0))',
         # El punto de arranque se guarda una vez, para "RESPAWN AT START".
         '  (if (not (Variables|Default|GetDbgTieneInicio))',
         '    (Utilities|IsValid pawn',
         '      (:"Is Valid"',
         '        (Variables|Default|SetDbgInicioLoc'
         ' (Transformation|GetActorLocation :self pawn))',
         '        (Variables|Default|SetDbgInicioRot'
         ' (Pawn|GetControlRotation :self (Game|GetPlayerController 0)))',
         '        (Variables|Default|SetDbgTieneInicio true)'
         + ('\n        (Development|PrintString :InString "DBG primer frame"'
            ' :bPrintToScreen false :bPrintToLog true :Duration 5.0)'
            '\n        (CallFunction|DbgToggle)' if AUTO_ABRIR else '') + ')',
         '      (:"Is Not Valid")))']
    cond = " ".join('(Game|Player|WasInputKeyJustPressed :self pc :Key "%s")' % k
                    for k in TECLAS)
    # God Mode / recurso infinito / velocidad: se mantienen desde el tick, y
    # solo cuando hace falta (dentro comprueba los tres interruptores).
    l.append('  (CallFunction|DbgMantener)')
    l.append('  (CallFunction|DbgLogTick)')
    l.append('  (CallFunction|DbgOlvidarTick)')
    l.append('  (if (or %s)' % cond)
    l.append('    (CallFunction|DbgToggle))')
    # El clic se resuelve a mano; ver la cabecera del fichero.
    l.append('  (if (and (Variables|Default|GetDbgVisible)'
             ' (Game|Player|WasInputKeyJustPressed :self pc :Key "LeftMouseButton"))')
    l.append('    (bind (mx my ok) (Game|Player|GetMousePosition :self pc))')
    l.append('    (if ok')
    l.append('      (CallFunction|DbgClick :MX mx :MY my)))')
    l.append('  (return false))')
    return "\n".join(l)


def dsl_dibujar():
    """Marco, cabecera y pestanas; luego delega en la pestana activa."""
    l = ['(fn DbgDibujar ()',
         '  (if (not (Variables|Default|GetDbgVisible))',
         '    (return false))',
         '  (if (not (CallFunction|DbgPermitido))',
         '    (return false))',
         '  (CallFunction|DbgCargar)',
         # Reset por frame del flag de hover: lo pone a false ANTES de repintar,
         # y cada DbgBoton que pase por debajo del raton lo vuelve a poner.
         '  (Variables|Default|SetDbgSobreBoton false)',
         BIND_GEO,
         '  (bind n (Utilities|Array|Length (Variables|Default|GetDbgLineas)))',
         # WORLD crece con la lista de destinos; las demas tienen alto fijo, y
         # AI es la mas alta porque lleva dos listas y el bloque de objetivo.
         '  (bind alto (* (select (== (Variables|Default|GetDbgTab) 0)'
         ' (+ 444.0 (* n %.1f))'
         ' (select (== (Variables|Default|GetDbgTab) 3) 760.0 (select (== (Variables|Default|GetDbgTab) 4) 700.0 (select (== (Variables|Default|GetDbgTab) 6) 682.0 (select (== (Variables|Default|GetDbgTab) 2) 720.0 (select (== (Variables|Default|GetDbgTab) 7) 420.0 660.0)))))) esc))' % FILA,
         rect("px", "%.1f" % PY, SC(PW), "alto", FONDO),
         rect("px", "%.1f" % PY, SC(PW), SC(3.0), ORO),
         texto(X(14.0), Y(12.0), '"DARK ANGELS - DEV TOOLS"', ORO, 1.35),
         # Zoom del panel: los dos botones viven en la CABECERA a proposito,
         # para que se puedan alcanzar aunque el panel se salga por abajo.
         rect(X(TAM_MENOS), Y(10.0), SC(30.0), SC(24.0), BOTON),
         texto(X(TAM_MENOS + 10.0), Y(13.0), '"-"', ORO, 1.1),
         rect(X(TAM_MAS), Y(10.0), SC(30.0), SC(24.0), BOTON),
         texto(X(TAM_MAS + 9.0), Y(13.0), '"+"', ORO, 1.1),
         texto(X(TAM_MENOS - 34.0), Y(14.0), '"TAM"', GRIS, 0.85),
         texto(X(500.0), Y(14.0), '"[ . ]"', GRIS, 0.85)]
    # Pestanas: WORLD activa, el resto marcadas como pendientes.
    for i, nombre in enumerate(PESTANAS):
        x, y = tab_pos(i)
        l.append('  (bind act%d (== (Variables|Default|GetDbgTab) %d))' % (i, i))
        l.append('  (if act%d' % i)
        l.append(rect(X(x), Y(y), SC(TAB_W), SC(TAB_H), BOTON_ON))
        l.append('    (else')
        # Dos cierres: uno para el (else y otro para el (if.
        l.append(rect(X(x), Y(y), SC(TAB_W), SC(TAB_H), BOTON) + '))')
        # WORLD, PLAYER, COMBAT y AI ya estan; BOSS y STORY pendientes.
        etiqueta = '"%s"' % nombre if i < 8 else '"%s  --"' % nombre
        l.append(texto(X(x + 12.0), Y(y + 4.0), etiqueta,
                       ORO if i < 8 else GRIS, 1.0))
    # El hover de las 7 pestañas y los dos TAM: aqui, que es el unico punto por
    # el que pasan todos los caminos y donde la tira ya esta pintada.
    l.append('  (CallFunction|DbgHoverTabs)')
    l.append('  (if (== (Variables|Default|GetDbgTab) 0)')
    l.append('    (CallFunction|DbgTabWorld)')
    l.append('    (else')
    l.append('      (if (== (Variables|Default|GetDbgTab) 1)')
    l.append('        (CallFunction|DbgTabPlayer)')
    l.append('        (else')
    l.append('          (if (== (Variables|Default|GetDbgTab) 2)')
    l.append('            (CallFunction|DbgTabCombat)')
    l.append('            (else')
    l.append('              (if (== (Variables|Default|GetDbgTab) 3)')
    l.append('                (CallFunction|DbgTabAI)')
    l.append('                (else')
    l.append('                  (if (== (Variables|Default|GetDbgTab) 4)')
    l.append('                    (CallFunction|DbgTabBoss)')
    l.append('                    (else')
    l.append('                      (if (== (Variables|Default|GetDbgTab) 5)')
    l.append('                        (CallFunction|DbgTabStory)')
    l.append('                        (else')
    l.append('                          (if (== (Variables|Default|GetDbgTab) 6)')
    l.append('                            (CallFunction|DbgTabFinishers)')
    l.append('                            (else')
    l.append('                              (if (== (Variables|Default|GetDbgTab) 7)')
    l.append('                                (CallFunction|DbgTabWeapon)')
    l.append('                                (else')
    l.append('                                  (CallFunction|DbgTabPendiente)))))))))))))))))')
    l.append('  (return false))')
    return "\n".join(l)


def dsl_pendiente():
    return ('(fn DbgTabPendiente ()\n'
            + BIND_GEO + '\n'
            + texto(X(20.0), Y(200.0),
                    '"Esta seccion todavia no esta construida."', GRIS, 1.1) + '\n'
            + texto(X(20.0), Y(226.0),
                    '"Fase 1: solo WORLD."', GRIS, 1.0) + '\n'
            '  (return false))')


# ------------------------------------------------------- acciones de WORLD

def dsl_teleport():
    return ('(fn DbgTeleport (Indice)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (bind (v okv) (Utilities|String|StringToVector'
            ' (CallFunction|DbgCampo :Indice Indice :Campo 2)))\n'
            '  (bind (r okr) (Utilities|String|StringToRotator'
            ' (CallFunction|DbgCampo :Indice Indice :Campo 3)))\n'
            '  (bind pawn (Game|GetPlayerPawn 0))\n'
            '  (Utilities|IsValid pawn\n'
            '    (:"Is Valid"\n'
            '      (if okv\n'
            '        (Transformation|SetActorLocationAndRotation :self pawn'
            ' :NewLocation v :NewRotation r :bSweep false :bTeleport true)\n'
            # La que se ve es la de la camara: el pawn de DCS no gira con ella,
            # asi que sin esto aterrizas mirando a donde mirabas antes.
            '        (Pawn|SetControlRotation :self (Game|GetPlayerController 0)'
            ' :NewRotation r)\n'
            # STATE PRESET: si la linea del destino trae un SEXTO campo, se
            # aplica como objetivo del HUD al llegar. Asi un destino puede
            # dejarte el estado de prueba puesto ("boss listo para pelear")
            # sin tocar ningun SaveGame: ObjectiveIndex es estado de sesion.
            '        (bind obj (CallFunction|DbgCampo :Indice Indice :Campo 5))\n'
            '        (if (> (Utilities|String|Len obj) 0)\n'
            '          (Variables|Default|SetObjectiveIndex'
            ' (Utilities|String|StringToInteger obj)))\n'
            '        (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "Teleport: " (CallFunction|DbgCampo :Indice Indice :Campo 0)))\n'
            '        (else\n'
            '          (Variables|Default|SetDbgMensaje'
            ' "Coordenadas mal escritas en el Data Asset"))))\n'
            '    (:"Is Not Valid")))')


def dsl_guardar():
    return ('(fn DbgGuardarPos ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (bind pawn (Game|GetPlayerPawn 0))\n'
            '  (Utilities|IsValid pawn\n'
            '    (:"Is Valid"\n'
            '      (Variables|Default|SetDbgGuardadaLoc'
            ' (Transformation|GetActorLocation :self pawn))\n'
            '      (Variables|Default|SetDbgGuardadaRot'
            ' (Pawn|GetControlRotation :self (Game|GetPlayerController 0)))\n'
            '      (Variables|Default|SetDbgTieneGuardada true)\n'
            '      (Variables|Default|SetDbgMensaje "Posicion guardada"))\n'
            '    (:"Is Not Valid")))')


def dsl_ir_guardada():
    return ('(fn DbgIrAGuardada ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (if (not (Variables|Default|GetDbgTieneGuardada))\n'
            '    (Variables|Default|SetDbgMensaje "No hay ninguna posicion guardada")\n'
            '    (return))\n'
            '  (bind pawn (Game|GetPlayerPawn 0))\n'
            '  (Utilities|IsValid pawn\n'
            '    (:"Is Valid"\n'
            '      (Transformation|SetActorLocationAndRotation :self pawn'
            ' :NewLocation (Variables|Default|GetDbgGuardadaLoc)'
            ' :NewRotation (Variables|Default|GetDbgGuardadaRot)'
            ' :bSweep false :bTeleport true)\n'
            '      (Pawn|SetControlRotation :self (Game|GetPlayerController 0)'
            ' :NewRotation (Variables|Default|GetDbgGuardadaRot))\n'
            '      (Variables|Default|SetDbgMensaje "De vuelta a la posicion guardada"))\n'
            '    (:"Is Not Valid")))')


def dsl_copiar():
    # Imprime la linea EXACTA que hay que pegar en el Data Asset para convertir
    # el sitio donde estas en un destino nuevo. No hay nodo de portapapeles en
    # Blueprint (comprobado), asi que va a pantalla y al log.
    return ('(fn DbgCopiarTransform ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (bind pawn (Game|GetPlayerPawn 0))\n'
            '  (Utilities|IsValid pawn\n'
            '    (:"Is Valid"\n'
            '      (bind linea (Utilities|String|Append\n'
            '        (Utilities|String|Append\n'
            '          (Utilities|String|Append\n'
            '            (Utilities|String|Append "NuevoDestino | Recorrido | "\n'
            '              (Utilities|String|ToString(Vector)'
            ' (Transformation|GetActorLocation :self pawn)))\n'
            '            " | ")\n'
            '          (Utilities|String|ToString(Rotator)'
            ' (Pawn|GetControlRotation :self (Game|GetPlayerController 0))))\n'
            '        " | descripcion"))\n'
            '      (Development|PrintString :InString linea :bPrintToScreen true'
            ' :bPrintToLog true :Duration 30.0)\n'
            '      (Variables|Default|SetDbgMensaje'
            ' "Linea de destino impresa en pantalla y en el log"))\n'
            '    (:"Is Not Valid")))')


def dsl_velocidad():
    return ('(fn DbgVelocidad (Valor)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Utilities|Time|SetGlobalTimeDilation :TimeDilation Valor)\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "Velocidad de juego: "'
            ' (Utilities|String|ToString(Float) Valor))))')


def dsl_reiniciar():
    return ('(fn DbgReiniciarNivel ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Development|ExecuteConsoleCommand :Command "RestartLevel"))')


def dsl_respawn():
    # "Respawn" honesto: devuelve al jugador al punto donde arranco el nivel.
    # No se toca el sistema de muerte/respawn de DCS, que es gameplay.
    return ('(fn DbgRespawnInicio ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (if (not (Variables|Default|GetDbgTieneInicio))\n'
            '    (Variables|Default|SetDbgMensaje "Todavia no se ha leido el punto de inicio")\n'
            '    (return))\n'
            '  (bind pawn (Game|GetPlayerPawn 0))\n'
            '  (Utilities|IsValid pawn\n'
            '    (:"Is Valid"\n'
            '      (Transformation|SetActorLocationAndRotation :self pawn'
            ' :NewLocation (Variables|Default|GetDbgInicioLoc)'
            ' :NewRotation (Variables|Default|GetDbgInicioRot)'
            ' :bSweep false :bTeleport true)\n'
            '      (Pawn|SetControlRotation :self (Game|GetPlayerController 0)'
            ' :NewRotation (Variables|Default|GetDbgInicioRot))\n'
            '      (Variables|Default|SetDbgMensaje "De vuelta al punto de inicio"))\n'
            '    (:"Is Not Valid")))')


# ---------------------------------------------------------- PLAYER: acciones
#
# Todo pasa por la API publica de DCS. Se usan tres mensajes de interfaz:
#   Interface|GetStatValue (self, StatTag, IncludeModifiers) -> Value
#   Interface|ModifyStat   (self, StatTag, Value)   <- suma un delta
#   Reactions|Kill         (self)
# y el componente se saca con GetComponentByClass, sin castear a clases de DCS.

def stats(var="sm"):
    """Coge el StatsManager del jugador."""
    return ('  (bind %s (Actor|GetComponentbyClass :self (Game|GetPlayerPawn 0)'
            ' :ComponentClass "%s"))' % (var, DCS_STATS))


def leer(tag, comp="sm"):
    return ('(Interface|GetStatValue :self %s'
            ' :StatTag (GameplayTags|MakeLiteralGameplayTag :Value "%s")'
            ' :IncludeModifiers true)' % (comp, tag))


def sumar(tag, valor, comp="sm"):
    return ('  (Interface|ModifyStat :self %s'
            ' :StatTag (GameplayTags|MakeLiteralGameplayTag :Value "%s")'
            ' :Value %s)' % (comp, tag, valor))


def dsl_vida():
    """Pone la vida a una fraccion del maximo, con la API de stats de DCS.

    ModifyStat suma un delta, asi que el objetivo se alcanza sumando
    (max * fraccion - actual). No se escribe la stat a pelo ni se tocan
    valores internos."""
    return ('(fn DbgVida (Fraccion)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            + stats() + '\n'
            '  (bind maxv ' + leer(TAG_HP_MAX) + ')\n'
            '  (bind act ' + leer(TAG_HP) + ')\n'
            + sumar(TAG_HP, "(- (* maxv Fraccion) act)") + '\n'
            '  (Variables|Default|SetDbgMensaje "Vida ajustada"))')


def dsl_matar():
    """Kill Player: deja la vida a 0 por la via de stats de DCS.

    DCS tiene su muerte oficial (`Reactions|Kill`), pero **no se puede llamar
    desde aqui**: el pin `self` de un mensaje de interfaz esta tipado como la
    interfaz y solo acepta un objeto de una clase que la implemente. Para
    conseguir esa referencia haria falta castear el Pawn a `BP_CombatCharacter`,
    y por esta API **no existe ningun nodo de cast a clases de DCS** (probado:
    ni CastToBPCombatCharacter ni conversiones a interfaz).
    Con los COMPONENTES si se puede, porque `GetComponentByClass` con la clase
    fijada ya devuelve el tipo concreto — de ahi que el resto de PLAYER si use
    la API oficial.

    Poner la vida a 0 es la mejor aproximacion disponible. Queda por comprobar
    en juego si DCS dispara la muerte al llegar a 0 por esta via o solo dentro
    de su TakeDamage."""
    return ('(fn DbgMatar ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            + stats() + '\n'
            '  (bind act ' + leer(TAG_HP) + ')\n'
            + sumar(TAG_HP, "(- 0.0 act)") + '\n'
            '  (Variables|Default|SetDbgMensaje "Vida a 0"))')


def dsl_god():
    return ('(fn DbgGodToggle ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Variables|Default|SetDbgGod (not (Variables|Default|GetDbgGod)))\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "God Mode: "'
            ' (Utilities|String|ToString(Boolean) (Variables|Default|GetDbgGod)))))')


def dsl_mana_inf():
    return ('(fn DbgManaToggle ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Variables|Default|SetDbgManaInf (not (Variables|Default|GetDbgManaInf)))\n'
            '  (Variables|Default|SetDbgMensaje "Recurso infinito cambiado"))')


def dsl_mov():
    return ('(fn DbgMov (Mult)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Variables|Default|SetDbgMovMult Mult)\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "Velocidad de movimiento x"'
            ' (Utilities|String|ToString(Float) Mult))))')


def dsl_mantener():
    """God Mode y recurso infinito, llamado desde el tick.

    NO intercepta el dano: DCS aplica el golpe normalmente —con su reaccion,
    su sonido y su animacion— y aqui se repone la vida al maximo. Es la unica
    via sin modificar el pipeline de combate de DCS, que era el requisito.
    Ver la limitacion en las notas: un golpe mayor que la vida MAXIMA puede
    matar antes de que llegue esta reposicion.

    Tambien mantiene la velocidad de movimiento: el componente de DCS reescribe
    MaxWalkSpeed cada frame, asi que el multiplicador hay que reaplicarlo."""
    # SALIDA TEMPRANA, de la revision final: esto corre en CADA frame, y sin la
    # guarda hacia un GetComponentByClass por frame aunque los tres
    # interruptores estuvieran apagados — que es el caso normal. Con la guarda,
    # apagado no cuesta mas que tres lecturas de bool.
    return ('(fn DbgMantener ()\n'
            '  (if (and (and (not (Variables|Default|GetDbgGod))\n'
            '                (not (Variables|Default|GetDbgManaInf)))\n'
            '           (== (Variables|Default|GetDbgMovMult) 1.0))\n'
            '    (return))\n'
            '  (bind pawn (Game|GetPlayerPawn 0))\n'
            '  (Utilities|IsValid pawn\n'
            '    (:"Is Valid"\n'
            + stats() + '\n'
            '      (if (Variables|Default|GetDbgGod)\n'
            '        (bind mx ' + leer(TAG_HP_MAX) + ')\n'
            '        (bind ac ' + leer(TAG_HP) + ')\n'
            '        (if (< ac mx)\n'
            + sumar(TAG_HP, "(- mx ac)") + '))\n'
            '      (if (Variables|Default|GetDbgManaInf)\n'
            '        (bind mmx ' + leer(TAG_MANA_MAX) + ')\n'
            '        (bind mac ' + leer(TAG_MANA) + ')\n'
            '        (if (< mac mmx)\n'
            + sumar(TAG_MANA, "(- mmx mac)") + '))\n'
            '      (if (!= (Variables|Default|GetDbgMovMult) 1.0)\n'
            # GetCharacterMovement pide un Character, no un Pawn: hay que
            # cogerlo con GetPlayerCharacter, no con GetPlayerPawn.
            '        (bind cm (Class|Character|GetCharacterMovement'
            ' :self (Game|GetPlayerCharacter 0)))\n'
            '        (Class|CharacterMovementComponent|SetMaxWalkSpeed :self cm'
            ' :MaxWalkSpeed (* 600.0 (Variables|Default|GetDbgMovMult)))))\n'
            # Sin `(return)` detras: el IsValid es multi-exec y TERMINA el flujo,
            # asi que cualquier cosa despues es codigo inalcanzable y se rechaza.
            '    (:"Is Not Valid")))')


def dsl_reset_player():
    return ('(fn DbgResetPlayer ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Variables|Default|SetDbgGod false)\n'
            '  (Variables|Default|SetDbgManaInf false)\n'
            '  (Variables|Default|SetDbgMovMult 1.0)\n'
            '  (Utilities|Time|SetGlobalTimeDilation :TimeDilation 1.0)\n'
            '  (CallFunction|DbgVida :Fraccion 1.0)\n'
            '  (Variables|Default|SetDbgMensaje'
            ' "Reset: vida, velocidad, god mode y dilatacion"))')


# ------------------------------------------------- la pestana WORLD y clics
#
# La geometria de los botones se calcula UNA vez aqui y de ella salen tanto el
# dibujado como el enrutado de clics: no pueden quedar descuadrados.
#
# `yb` es la Y donde acaba la lista de destinos, que depende de cuantos haya:
# en DSL es una expresion, no un numero.

def desde_yb(yb, off):
    """Y final a `off` unidades por debajo del final de la lista."""
    return "(+ %s %s)" % (yb, SC(off))


def filas_botones(yb):
    """[(titulo, y_titulo, y_botones, [(x, w, etiqueta, accion, encendido)]), ...]

    Las X y anchos son unidades de panel: quien dibuje los pasa por X()/SC()."""
    x0 = 8.0
    return [
        ("PLAYER POSITION", desde_yb(yb, 4.0), desde_yb(yb, 22.0), [
            (x0, 182.0, "SAVE POSITION", "(CallFunction|DbgGuardarPos)", "false"),
            (x0 + 190.0, 182.0, "GO TO SAVED", "(CallFunction|DbgIrAGuardada)",
             "(Variables|Default|GetDbgTieneGuardada)"),
            (x0 + 380.0, 182.0, "COPY TRANSFORM", "(CallFunction|DbgCopiarTransform)",
             "false"),
        ]),
        ("GAME SPEED", desde_yb(yb, 54.0), desde_yb(yb, 72.0), [
            (x0 + i * 112.0, 108.0, e, "(CallFunction|DbgVelocidad :Valor %s)" % v, "false")
            for i, (e, v) in enumerate([("0.1x", "0.1"), ("0.25x", "0.25"),
                                        ("0.5x", "0.5"), ("1x", "1.0"),
                                        ("2x", "2.0")])
        ]),
        ("LEVEL", desde_yb(yb, 104.0), desde_yb(yb, 122.0), [
            (x0, 278.0, "RESTART LEVEL", "(CallFunction|DbgReiniciarNivel)", "false"),
            (x0 + 286.0, 278.0, "RESPAWN AT START", "(CallFunction|DbgRespawnInicio)",
             "false"),
        ]),
        ("", None, desde_yb(yb, 152.0), [
            (x0, 564.0, "CLOSE DEBUG HUD", "(CallFunction|DbgToggle)", "false"),
        ]),
    ]


def dsl_tab_world():
    l = ['(fn DbgTabWorld ()',
         BIND_GEO,
         '  (bind n (Utilities|Array|Length (Variables|Default|GetDbgLineas)))',
         '  (bind pawn (Game|GetPlayerPawn 0))',
         '  (bind loc (Transformation|GetActorLocation :self pawn))',
         '  (bind rot (Pawn|GetControlRotation :self (Game|GetPlayerController 0)))',
         '  (bind nivel (Game|GetCurrentLevelName true))']
    y = 116.0
    l.append(texto(X(16.0), Y(y), '"INFORMACION"', ORO, 1.05))
    datos = [
        ('(Utilities|String|Append "Level:  " nivel)', 20.0),
        ('(Utilities|String|Append "Loc:  " (Utilities|String|ToString(Vector) loc))', 38.0),
        ('(Utilities|String|Append "Rot camara:  "'
         ' (Utilities|String|ToString(Rotator) rot))', 56.0),
        ('(Utilities|String|Append'
         ' (Utilities|String|Append "FPS:  "'
         ' (Utilities|String|ToString(Float) (Variables|Default|GetDbgFps)))'
         ' (Utilities|String|Append "     Time Dilation:  "'
         ' (Utilities|String|ToString(Float) (Utilities|Time|GetGlobalTimeDilation))))', 74.0),
    ]
    for expr, dy in datos:
        l.append(texto(X(16.0), Y(y + dy), expr, HUESO, 0.95))

    l.append(texto(X(16.0), Y(LISTA_Y0 - 26.0), '"TELEPORT"', ORO, 1.05))
    l.append('  (for i (range n)')
    l.append('    (bind fy (+ %s (* i %s)))' % (Y(LISTA_Y0), SC(FILA)))
    l.append('    ' + rect(X(8.0), "fy", SC(PW - 16.0), SC(FILA - 3.0), BOTON).strip())
    l.append('    ' + texto(X(18.0), "(+ fy %s)" % SC(3.0),
                            '(CallFunction|DbgCampo :Indice i :Campo 0)', HUESO, 1.0).strip())
    l.append('    ' + texto(X(210.0), "(+ fy %s)" % SC(4.0),
                            '(CallFunction|DbgCampo :Indice i :Campo 1)', GRIS, 0.85).strip())
    l.append('    ' + texto(X(320.0), "(+ fy %s)" % SC(4.0),
                            '(CallFunction|DbgCampo :Indice i :Campo 4)', GRIS, 0.8).strip())
    l.append('    )')

    yb = '(+ %s (* n %s))' % (Y(LISTA_Y0), SC(FILA))
    for titulo, y_tit, y_bot, botones in filas_botones(yb):
        if y_tit:
            l.append(texto(X(16.0), y_tit, '"%s"' % titulo, ORO, 1.05))
        for x, w, etiqueta, _accion, encendido in botones:
            # X y W tienen que ir ya en pixeles: el boton solo escala su alto.
            l.append('  (CallFunction|DbgBoton :X %s :Y %s :W %s'
                     ' :Etiqueta "%s" :Encendido %s)'
                     % (X(x), y_bot, SC(w), etiqueta, encendido))
    l.append(texto(X(16.0), desde_yb(yb, 180.0),
                   '(Variables|Default|GetDbgMensaje)', ORO, 0.95))
    l.append('  (return false))')
    return "\n".join(l)


# ------------------------------------------------------------- AI: acciones
#
# Los enemigos generados aqui se apuntan en `DbgSpawned`, un array de Actor.
# CLEAR recorre ESE array y nada mas: por construccion no puede tocar un enemigo
# narrativo ni uno colocado a mano en el nivel, aunque sea de la misma clase.
# Es mas fiable que etiquetar, que dependeria de leer bien la etiqueta.

def dsl_cargar_enem():
    sonda = ('  (Development|PrintString :InString'
             ' (Utilities|String|Append'
             ' (Utilities|String|Append "DBG tipos="'
             ' (Utilities|String|ToString(Integer)'
             ' (Utilities|Array|Length (Variables|Default|GetDbgTipos))))'
             ' (Utilities|String|Append "  nombre0=["'
             ' (Utilities|String|Append'
             ' (CallFunction|DbgCampoTipo :Indice 0 :Campo 0) "]")))'
             ' :bPrintToScreen false :bPrintToLog true :Duration 8.0)\n'
             if AUTO_ABRIR else '')
    return ('(fn DbgCargarEnem ()\n'
            + sonda +
            '  (if (> (Utilities|Array|Length (Variables|Default|GetDbgTipos)) 0)\n'
            '    (return))\n'
            '  (bind d (Variables|Default|GetDbgDatosEnem))\n'
            '  (Utilities|IsValid d\n'
            '    (:"Is Valid"\n'
            '      (Variables|Default|SetDbgTipos'
            ' (Class|BPDADebugEnemigos|GetTipos :self d))\n'
            '      (Variables|Default|SetDbgEncuentros'
            ' (Class|BPDADebugEnemigos|GetEncuentros :self d)))\n'
            '    (:"Is Not Valid")))')


# POR QUE EL TROCEO ESTA DUPLICADO EN DOS FUNCIONES Y NO EN UNA COMPARTIDA:
#
# Se intentaron las dos formas "limpias" y las dos devuelven cadena vacia, sin
# error ni aviso:
#
#   1. Una funcion con `(if (== Cual 0) (return A) (else (return B)))`.
#   2. Una funcion que delega en otra: `(return (CallFunction|DbgTrozo ...))`.
#
# En la 2 el grafo se lee perfecto —`(bind _valor (CallFunction|DbgCampoTipo
# _index))`— pero **el valor de retorno de una llamada a otra funcion propia no
# llega a la salida**. Comprobado en juego que las piezas sueltas SI funcionan:
# leer el array da "Vigilante | /Game/..." y trocear un literal da "Uno".
#
# Lo que si funciona es la forma de `DbgCampo` (la de WORLD, que lleva
# funcionando desde la fase 1): trocear EN LINEA, sin llamar a nadie. Asi que
# se copia esa forma tal cual. La duplicacion es el precio de que funcione.
#
# OJO CON `Trim`: en Unreal **solo quita los espacios de DELANTE**; los de
# detras los quita `TrimTrailing`, y hay que encadenar los dos.

def _troceo(nombre, variable):
    return ('(fn %s (Indice Campo)\n'
            '  (bind lineas (Variables|Default|Get%s))\n'
            '  (if (not (Utilities|Array|IsValidIndex lineas Indice))\n'
            '    (return ""))\n'
            '  (bind partes (Utilities|String|ParseIntoArray'
            ' (Utilities|Array|Get(acopy) lineas Indice) "|" true))\n'
            '  (if (not (Utilities|Array|IsValidIndex partes Campo))\n'
            '    (return ""))\n'
            '  (return (Utilities|String|TrimTrailing (Utilities|String|Trim'
            ' (Utilities|Array|Get(acopy) partes Campo)))))' % (nombre, variable))


def dsl_campo_tipo():
    return _troceo("DbgCampoTipo", "DbgTipos")


def dsl_campo_enc():
    return _troceo("DbgCampoEnc", "DbgEncuentros")


def dsl_spawn_uno():
    """Genera UN enemigo delante del jugador y lo apunta en el registro.

    Sitio seguro: se parte de la posicion del jugador, se avanza por su vector
    hacia delante y se desplaza de lado segun el indice para que no salgan
    apilados; despues se PROYECTA AL NAVMESH, que es lo que evita que aparezcan
    dentro de geometria. Si la proyeccion falla se usa el punto crudo, para no
    quedarse sin spawn."""
    return ('(fn DbgSpawnUno (RutaClase Lado)\n'
            '  (bind pawn (Game|GetPlayerPawn 0))\n'
            '  (bind base (+ (Transformation|GetActorLocation :self pawn)\n'
            '    (+ (* (Transformation|GetActorForwardVector :self pawn)'
            ' (Variables|Default|GetDbgDistSel))\n'
            '       (* (Transformation|GetActorRightVector :self pawn)'
            ' (* Lado 120.0)))))\n'
            '  (bind (destino ok) (AI|Navigation|ProjectPointtoNavigation'
            ' :Point base :QueryExtent'
            ' (Math|Vector|MakeVector :X 600.0 :Y 600.0 :Z 600.0)))\n'
            # La ruta llega como TEXTO (viene del Data Asset), y el pin de carga
            # pide una referencia blanda: hay que pasar por MakeSoftClassPath y
            # ToSoftClassReference. Un string suelto no conecta ahi.
            '  (bind clase (Utilities|LoadClassAssetBlocking'
            ' :AssetClass (Utilities|ToSoftClassReference'
            ' :SoftClassPath (Utilities|MakeSoftClassPath :PathString RutaClase))))\n'
            # CastToActorClass tiene pines de ejecucion (no es puro), asi que el
            # spawn va DENTRO de su rama :then.
            '  (bind ac (Utilities|Casting|CastToActorClass :Class clase)\n'
            '    (:then\n'
            # ENCARADO AL JUGADOR. Sin esto el MakeTransform nace con rotacion
            # literal 0,0,0 y todo enemigo invocado mira a +X: como el cono de
            # AIPerception de DCS es de 75 grados, uno que nazca de espaldas NO
            # TE VE NUNCA si te quedas quieto. Medido: 0 flechas en 25 s con yaw
            # 0 contra 9 girado. Solo el yaw, para que no salga inclinado si el
            # suelo del spawn esta a otra altura.
            '      (bind mirar (Math|Rotator|FindLookAtRotation'
            ' :Start (select ok destino base)'
            ' :Target (Transformation|GetActorLocation :self pawn)))' '\n'
            '      (bind nuevo (Game|SpawnActorfromClass :Class ac'
            ' :SpawnTransform (Math|Transform|MakeTransform'
            ' :Location (select ok destino base)'
            ' :Rotation (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0'
            ' :Yaw (.yaw mirar)))'
            ' :CollisionHandlingOverride "AdjustIfPossibleButAlwaysSpawn"))\n'
            '      (Utilities|Array|Add :TargetArray (Variables|Default|GetDbgSpawned)'
            ' :NewItem nuevo))\n'
            '    (:CastFailed)))')


def dsl_spawn():
    return ('(fn DbgSpawn ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (CallFunction|DbgCargarEnem)\n'
            '  (bind ruta (CallFunction|DbgCampoTipo'
            ' :Indice (Variables|Default|GetDbgTipoSel) :Campo 1))\n'
            '  (for i (range (Variables|Default|GetDbgCantSel))\n'
            '    (CallFunction|DbgSpawnUno :RutaClase ruta :Lado (- i 1)))\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "Spawn: "'
            ' (Utilities|String|Append'
            ' (Utilities|String|ToString(Integer) (Variables|Default|GetDbgCantSel))'
            ' (Utilities|String|Append " x "'
            ' (CallFunction|DbgCampoTipo'
            ' :Indice (Variables|Default|GetDbgTipoSel) :Campo 0))))))')


def dsl_encuentro():
    """Lanza un preset: "0:2, 2:1" = dos del tipo 0 y uno del tipo 2."""
    return ('(fn DbgEncuentro (Indice)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (CallFunction|DbgCargarEnem)\n'
            '  (bind grupos (Utilities|String|ParseIntoArray'
            ' (CallFunction|DbgCampoEnc'
            ' :Indice Indice :Campo 1) "," true))\n'
            '  (for g grupos\n'
            '    (bind par (Utilities|String|ParseIntoArray'
            ' (Utilities|String|Trim g) ":" true))\n'
            '    (bind tipo (Utilities|String|StringToInteger'
            ' (Utilities|Array|Get(acopy) par 0)))\n'
            '    (bind cuantos (Utilities|String|StringToInteger'
            ' (Utilities|Array|Get(acopy) par 1)))\n'
            '    (bind ruta (CallFunction|DbgCampoTipo'
            ' :Indice tipo :Campo 1))\n'
            '    (for j (range cuantos)\n'
            '      (CallFunction|DbgSpawnUno :RutaClase ruta :Lado (- j 1))))\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "Encuentro: "'
            ' (CallFunction|DbgCampoEnc'
            ' :Indice Indice :Campo 0))))')


def dsl_limpiar():
    return ('(fn DbgLimpiar ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (bind lista (Variables|Default|GetDbgSpawned))\n'
            '  (bind n (Utilities|Array|Length lista))\n'
            '  (for e lista\n'
            '    (Actor|DestroyActor :self e))\n'
            '  (Utilities|Array|Clear :TargetArray (Variables|Default|GetDbgSpawned))\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "Enemigos de debug borrados: "'
            ' (Utilities|String|ToString(Integer) n))))')


def dsl_ia_logica():
    """Freeze/Unfreeze usando la IA que ya hay: StopLogic / RestartLogic sobre
    el Behavior Tree de cada `BP_BaseAI`."""
    return ('(fn DbgIALogica (Congelar)\n'
            '  (Variables|Default|SetDbgCongelada Congelar)\n'
            '  (for e (Actor|GetAllActorsOfClass :ActorClass "' + DCS_AI + '")\n'
            '    (bind c (AI|GetAIController :ControlledActor e))\n'
            '    (if Congelar\n'
            '      (AI|Logic|StopLogic :self c :Reason "DA Debug HUD")\n'
            '      (else\n'
            '        (AI|Logic|RestartLogic :self c))))\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|SelectString "IA congelada" "IA reanudada" Congelar)))')


def dsl_ia_apagar():
    # Disable AI va un paso mas alla que Freeze: ademas de parar el arbol, deja
    # de tickear el actor entero.
    return ('(fn DbgIAApagar (Apagar)\n'
            '  (Variables|Default|SetDbgApagada Apagar)\n'
            '  (for e (Actor|GetAllActorsOfClass :ActorClass "' + DCS_AI + '")\n'
            '    (Actor|Tick|SetActorTickEnabled :self e :bEnabled (not Apagar)))\n'
            '  (CallFunction|DbgIALogica :Congelar Apagar)\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|SelectString "IA apagada" "IA encendida" Apagar)))')


def dsl_ignorar():
    """Ignore Player: se le borra la percepcion a cada IA.

    Con el interruptor puesto se repite desde el tick, porque si no volverian a
    verte al instante siguiente. Restore Aggro lo apaga y ellos vuelven a
    percibir solos."""
    return ('(fn DbgIgnorarToggle (Ignorar)\n'
            '  (Variables|Default|SetDbgIgnorar Ignorar)\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|SelectString "Los enemigos te ignoran"'
            ' "Aggro restaurado" Ignorar)))')


def dsl_olvidar_tick():
    return ('(fn DbgOlvidarTick ()\n'
            '  (if (not (Variables|Default|GetDbgIgnorar))\n'
            '    (return))\n'
            '  (for e (Actor|GetAllActorsOfClass :ActorClass "' + DCS_AI + '")\n'
            '    (bind c (AI|GetAIController :ControlledActor e))\n'
            '    (bind p (AI|Perception|GetAIPerceptionComponent :self c))\n'
            '    (Utilities|IsValid p\n'
            '      (:"Is Valid"\n'
            '        (AI|Perception|ForgetAll :self p))\n'
            '      (:"Is Not Valid")))\n'
            '  (return))')


def dsl_reset_arena():
    return ('(fn DbgResetArena ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (CallFunction|DbgLimpiar)\n'
            '  (CallFunction|DbgIAApagar :Apagar false)\n'
            '  (CallFunction|DbgIgnorarToggle :Ignorar false)\n'
            '  (Variables|Default|SetDbgMensaje'
            ' "Arena limpia: enemigos de debug fuera y IA restaurada"))')


# ----------------------------------------------------------- BOSS: acciones
#
# QUE SE PUEDE Y QUE NO, y por que. Los dos bosses no comparten arquitectura:
#
#   BP_DA_GiantBoss  lleva el StatsManager de DCS, asi que su vida se toca por
#                    la misma via oficial que PLAYER y COMBAT.
#   BP_Gabriel       hereda de BP_Archangel, un Character con `HP` suelto y sin
#                    StatsManager. Para escribir ese `HP` haria falta una
#                    referencia TIPADA al actor, y `GetAllActorsOfClass`
#                    devuelve `Actor` a secas: por esta API no hay cast a clases
#                    del proyecto. Su vida NO es alcanzable desde aqui.
#
# FASES: ninguno de los dos tiene un sistema formal. Lo que hay son BANDERAS
# que pone la propia logica del boss (`Phase`, `bPhase2Triggered`,
# `bPhase3Triggered` en Gabriel; `FaseRitual`, que es el paso del guion, en el
# Giant). Escribirlas desde fuera pondria la bandera SIN ejecutar la transicion,
# que es justo lo que el encargo prohibe. Por eso los botones de fase estan
# preparados pero apagados.

def boss_ref(var="jefe"):
    """Encuentra en el mundo el actor del boss seleccionado.

    Se carga la clase desde la ruta de texto del Data Asset (misma cadena que el
    spawner: MakeSoftClassPath -> ToSoftClassReference -> LoadClassAssetBlocking)
    y se coge el primero que haya colocado."""
    return ('  (bind ruta (CallFunction|DbgCampoBoss'
            ' :Indice (Variables|Default|GetDbgBossSel) :Campo 1))\n'
            '  (bind cls (Utilities|LoadClassAssetBlocking'
            ' :AssetClass (Utilities|ToSoftClassReference'
            ' :SoftClassPath (Utilities|MakeSoftClassPath :PathString ruta))))\n')


def dsl_campo_boss():
    # Troceo EN LINEA, como DbgCampoTipo: delegar en otra funcion propia
    # devuelve vacio (ver las notas de la fase 4).
    return _troceo("DbgCampoBoss", "DbgBosses")


def dsl_cargar_boss():
    return ('(fn DbgCargarBoss ()\n'
            '  (if (> (Utilities|Array|Length (Variables|Default|GetDbgBosses)) 0)\n'
            '    (return))\n'
            '  (bind d (Variables|Default|GetDbgDatosEnem))\n'
            '  (Utilities|IsValid d\n'
            '    (:"Is Valid"\n'
            '      (Variables|Default|SetDbgBosses'
            ' (Class|BPDADebugEnemigos|GetBosses :self d)))\n'
            '    (:"Is Not Valid")))')


def dsl_boss_vida():
    """Vida del boss por el StatsManager de DCS, si lo lleva.

    Mismo mecanismo que PLAYER: ModifyStat suma un delta, asi que para dejarlo
    al 50% se suma (max*0.5 - actual). Si el boss no tiene StatsManager no pasa
    nada y se avisa en la linea de mensaje."""
    return ('(fn DbgBossVida (Fraccion)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            + boss_ref() +
            '  (bind ac (Utilities|Casting|CastToActorClass :Class cls)\n'
            '    (:then\n'
            '      (bind lista (Actor|GetAllActorsOfClass :ActorClass ac))\n'
            '      (if (> (Utilities|Array|Length lista) 0)\n'
            '        (bind jefe (Utilities|Array|Get(acopy) lista 0))\n'
            '        (bind sm (Actor|GetComponentbyClass :self jefe'
            ' :ComponentClass "' + DCS_STATS + '"))\n'
            '        (Utilities|IsValid sm\n'
            '          (:"Is Valid"\n'
            '            (bind mx ' + leer(TAG_HP_MAX, "sm") + ')\n'
            '            (bind ah ' + leer(TAG_HP, "sm") + ')\n'
            '            ' + sumar(TAG_HP, "(- (* mx Fraccion) ah)", "sm").strip() + '\n'
            '            (Variables|Default|SetDbgMensaje "Vida del boss ajustada"))\n'
            '          (:"Is Not Valid"\n'
            '            (Variables|Default|SetDbgMensaje'
            ' "Este boss no usa el StatsManager de DCS: su vida no es alcanzable")))\n'
            '        (else\n'
            '          (Variables|Default|SetDbgMensaje'
            ' "No hay ningun actor de ese boss en el nivel"))))\n'
            '    (:CastFailed)))')


# ---------------------------------------------------------- STORY: acciones
#
# NO HAY QUEST SYSTEM NI REGISTRO DE FLAGS EN EL PROYECTO. Comprobado: el estado
# narrativo vive repartido por actor en el nivel — `HasFired` en cada
# `BP_DA_ZoneTrigger`, `Abierto`/`Cerrado` en los interactuables, `bDone` en el
# portal, `bInteractPrev` en el altar— y esos son inalcanzables desde aqui,
# porque haria falta una referencia TIPADA al actor.
#
# El unico flag GLOBAL y real es el objetivo del HUD: `ObjectiveIndex`,
# `ObjectiveText` y `GuiaBloqueada`. Y esos SI se pueden tocar, porque el Debug
# HUD **hereda de BP_DA_HUD**: son variables propias, no ajenas.
#
# Se escribe `ObjectiveIndex` a pelo y no por `SetObjective` a proposito: esa
# funcion solo avanza (progresion monotona, para que volver atras no te cambie
# el objetivo), y para probar hace falta poder RETROCEDER.

def dsl_objetivo():
    return ('(fn DbgObjetivo (Delta)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (bind n (+ (Variables|Default|GetObjectiveIndex) Delta))\n'
            '  (Variables|Default|SetObjectiveIndex (select (< n 0) 0 n))\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "Objetivo del HUD: "'
            ' (Utilities|String|ToString(Integer)'
            ' (Variables|Default|GetObjectiveIndex)))))')


def dsl_guia():
    return ('(fn DbgGuiaToggle ()\n'
            '  (Variables|Default|SetGuiaBloqueada'
            ' (not (Variables|Default|GetGuiaBloqueada)))\n'
            '  (Variables|Default|SetDbgMensaje "Guia bloqueada cambiada"))')


def dsl_checkpoint():
    """Recorre los BP_RespawnVolume del nivel y lleva al seleccionado.

    Su variable `RespawnLocation` no es alcanzable (referencia tipada), pero la
    POSICION DEL ACTOR si, y es donde esta el checkpoint. Esto no toca ningun
    save: es solo un teleport."""
    return ('(fn DbgCheckpoint (Delta Ir)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (bind vols (Actor|GetAllActorsOfClass :ActorClass "' + RESPAWN + '"))\n'
            '  (bind n (Utilities|Array|Length vols))\n'
            '  (if (== n 0)\n'
            '    (Variables|Default|SetDbgMensaje'
            ' "No hay ningun BP_RespawnVolume en el nivel abierto")\n'
            '    (return))\n'
            '  (bind i (+ (Variables|Default|GetDbgCheckSel) Delta))\n'
            '  (Variables|Default|SetDbgCheckSel'
            ' (select (< i 0) (- n 1) (select (>= i n) 0 i)))\n'
            '  (if Ir\n'
            '    (bind v (Utilities|Array|Get(acopy) vols'
            ' (Variables|Default|GetDbgCheckSel)))\n'
            '    (bind pawn (Game|GetPlayerPawn 0))\n'
            '    (Transformation|SetActorLocationAndRotation :self pawn'
            ' :NewLocation (+ (Transformation|GetActorLocation :self v)'
            ' (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 120.0))'
            ' :NewRotation (Pawn|GetControlRotation'
            ' :self (Game|GetPlayerController 0))'
            ' :bSweep false :bTeleport true))\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append'
            ' (Utilities|String|Append "Checkpoint "'
            ' (Utilities|String|ToString(Integer)'
            ' (Variables|Default|GetDbgCheckSel)))'
            ' (Utilities|String|Append " de "'
            ' (Utilities|String|ToString(Integer) n)))))')


def dsl_reset_story():
    """Limpia SOLO los overrides de debug.

    No toca `ObjectiveIndex`, que es progresion real del juego, ni ningun
    SaveGame: aqui no se escribe ninguno. Lo unico que hay que limpiar es el
    checkpoint temporal de debug y el indice de recorrido."""
    return ('(fn DbgResetStory ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Variables|Default|SetDbgTieneGuardada false)\n'
            '  (Variables|Default|SetDbgCheckSel 0)\n'
            '  (Variables|Default|SetDbgMensaje'
            ' "Overrides de debug limpiados (el progreso real no se toca)"))')


def dsl_marcas_borrar():
    """Borra contadores, historico y flags del GameState.

    Existe por una razon practica: `BP_DA_Decision` tiene una guarda `Elegida`
    que solo deja elegir UNA vez, asi que sin esto hay que reiniciar PIE para
    poder probar otra opcion de la misma Marca."""
    return ('(fn DbgMarcasBorrar ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Class|BPDAGameState|BorrarTodo :self'
            ' (Utilities|Casting|CastToBP_DA_GameState (Game|GetGameState)))\n'
            '  (Variables|Default|SetDbgMensaje'
            ' "Marcas, historico y flags borrados"))')


def dsl_marcas_reiniciar():
    """Pone a cero los contadores de la esfera y CONSERVA el historico.

    Es lo que pasa de verdad al cruzar a la siguiente Sephirah: las Marcas no se
    borran nunca, pero la cuenta local vuelve a empezar."""
    return ('(fn DbgMarcasReiniciar ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Class|BPDAGameState|ReiniciarEsfera :self'
            ' (Utilities|Casting|CastToBP_DA_GameState (Game|GetGameState))'
            ' :NuevaEsfera "MALKUTH")\n'
            '  (Variables|Default|SetDbgMensaje'
            ' "Contadores de la esfera a cero (el historico se conserva)"))')


# --------------------------------------------------------- COMBAT: acciones
#
# COMO FUNCIONA EL MULTIPLICADOR DE DANO, que es lo que importa entender:
#
# NO se toca el pipeline de combate de DCS ni se intercepta el golpe. Lo que se
# mueve es la STAT de la que DCS saca el dano: `Stat.Damage`, con la misma API
# publica que PLAYER (`Interface|ModifyStat`). El calculo del golpe, el bloqueo,
# el parry y las reacciones siguen siendo los de DCS, intactos.
#
# Y no hace falta guardar el valor base de nadie: el ajuste se hace SIEMPRE
# relativo al multiplicador anterior. Si ahora la stat vale `base * anterior` y
# se quiere `base * nuevo`, el delta es `valor_actual * (nuevo/anterior - 1)`.
# Volver a x1 devuelve exactamente el valor original, tambien en los enemigos,
# cada uno con el suyo.

def dsl_dano_jugador():
    return ('(fn DbgDanoJugador (Mult)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            + stats() + '\n'
            '  (bind d ' + leer(TAG_DMG) + ')\n'
            '  (bind ant (Variables|Default|GetDbgDmgMult))\n'
            + sumar(TAG_DMG, "(* d (- (/ Mult ant) 1.0))") + '\n'
            '  (Variables|Default|SetDbgDmgMult Mult)\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "Dano del jugador x"'
            ' (Utilities|String|ToString(Float) Mult))))')


def dsl_one_hit():
    # One Hit Kill no es un sistema aparte: es el mismo multiplicador puesto muy
    # alto, asi que se apaga volviendo a x1 y no deja rastro.
    return ('(fn DbgOneHitToggle ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Variables|Default|SetDbgOneHit (not (Variables|Default|GetDbgOneHit)))\n'
            '  (if (Variables|Default|GetDbgOneHit)\n'
            '    (CallFunction|DbgDanoJugador :Mult 999.0)\n'
            '    (else\n'
            '      (CallFunction|DbgDanoJugador :Mult 1.0)))\n'
            '  (return))')


def dsl_dano_enemigo():
    """Mismo ajuste relativo, pero recorriendo los enemigos vivos.

    Los que aparezcan DESPUES nacen con su dano normal: hay que volver a pulsar
    el multiplicador. Reengancharlo al spawner es cosa de la fase AI."""
    return ('(fn DbgDanoEnemigo (Mult)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (bind ant (Variables|Default|GetDbgEnemyMult))\n'
            '  (bind enemigos (Actor|GetAllActorsOfClass :ActorClass "' + DCS_AI + '"))\n'
            '  (for e enemigos\n'
            '    (bind sm (Actor|GetComponentbyClass :self e'
            ' :ComponentClass "' + DCS_STATS + '"))\n'
            '    (bind d ' + leer(TAG_DMG, "sm") + ')\n'
            '    ' + sumar(TAG_DMG, "(* d (- (/ Mult ant) 1.0))", "sm").strip() + ')\n'
            '  (Variables|Default|SetDbgEnemyMult Mult)\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append'
            ' (Utilities|String|Append "Dano enemigo x"'
            ' (Utilities|String|ToString(Float) Mult))'
            ' (Utilities|String|Append "  en "'
            ' (Utilities|String|Append'
            ' (Utilities|String|ToString(Integer)'
            ' (Utilities|Array|Length enemigos)) " enemigos")))))')


def dsl_log_toggle():
    return ('(fn DbgLogToggle ()\n'
            '  (Variables|Default|SetDbgLogOn (not (Variables|Default|GetDbgLogOn)))\n'
            '  (Utilities|Array|Clear :TargetArray (Variables|Default|GetDbgLog))\n'
            '  (Variables|Default|SetDbgMensaje "Combat log cambiado"))')


def dsl_trazas():
    """Enciende el debug QUE YA TRAE DCS, no uno nuevo.

    `BP_CollisionHandlerComponent` es quien hace las trazas de arma, y tiene su
    propia variable `Debug` que dibuja la traza. Se activa en el jugador y en
    todos los enemigos vivos."""
    return ('(fn DbgTrazasToggle ()\n'
            '  (Variables|Default|SetDbgTrazas (not (Variables|Default|GetDbgTrazas)))\n'
            '  (bind v (Variables|Default|GetDbgTrazas))\n'
            '  (bind ch (Actor|GetComponentbyClass :self (Game|GetPlayerPawn 0)'
            ' :ComponentClass "' + DCS_COLL + '"))\n'
            '  (Class|BPCollisionHandlerComponent|SetDebug :self ch :Debug v)\n'
            '  (bind enemigos (Actor|GetAllActorsOfClass :ActorClass "' + DCS_AI + '"))\n'
            '  (for e enemigos\n'
            '    (bind che (Actor|GetComponentbyClass :self e'
            ' :ComponentClass "' + DCS_COLL + '"))\n'
            '    (Class|BPCollisionHandlerComponent|SetDebug :self che :Debug v))\n'
            '  (Variables|Default|SetDbgMensaje "Trazas de arma (debug de DCS)"))')


def dsl_colisiones():
    # Las capsulas de colision las dibuja el propio motor: no hace falta nada
    # nuestro, solo el show flag.
    return ('(fn DbgColisionesToggle ()\n'
            '  (Variables|Default|SetDbgColisiones'
            ' (not (Variables|Default|GetDbgColisiones)))\n'
            '  (Development|ExecuteConsoleCommand :Command "show Collision")\n'
            '  (Variables|Default|SetDbgMensaje "Capsulas de colision (show Collision)"))')


def dsl_reset_combat():
    return ('(fn DbgResetCombat ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (CallFunction|DbgDanoJugador :Mult 1.0)\n'
            '  (CallFunction|DbgDanoEnemigo :Mult 1.0)\n'
            '  (Variables|Default|SetDbgOneHit false)\n'
            '  (Variables|Default|SetDbgLogOn false)\n'
            '  (Utilities|Array|Clear :TargetArray (Variables|Default|GetDbgLog))\n'
            '  (Utilities|Time|SetGlobalTimeDilation :TimeDilation 1.0)\n'
            '  (if (Variables|Default|GetDbgTrazas)\n'
            '    (CallFunction|DbgTrazasToggle))\n'
            '  (if (Variables|Default|GetDbgColisiones)\n'
            '    (CallFunction|DbgColisionesToggle))\n'
            '  (Variables|Default|SetDbgMensaje "Reset del debug de combate"))')


# ------------------------------------------------- COMBAT: el arma temporal
#
# Los cinco puntos del §10 del PDF que faltaban. Todo pasa por castear el Pawn
# a `BP_DA_PlayerCharacter` -que SI se puede, porque es Blueprint nuestro; con
# las clases de DCS no habria nodo de cast (ver dsl_matar)- y llamar a la API
# que vive en el jugador. Ahi es donde tiene que estar la logica: el HUD solo
# dispara, para que valga tambien desde consola o desde otra herramienta.

def jugador_accion(nombre, cuerpo, mensaje):
    """Molde: castea el Pawn a BP_DA_PlayerCharacter y ejecuta `cuerpo`.

    El `IsValid` del cast TERMINA el flujo (nada puede ir detras), asi que el
    mensaje va DENTRO de la rama valida y no despues."""
    return ('(fn NOMBRE ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (bind j (Utilities|Casting|CastToBP_DA_PlayerCharacter (Game|GetPlayerPawn 0)))\n'
            '  (Utilities|IsValid j\n'
            '    (:"Is Valid"\n'
            'CUERPO'
            '      (Variables|Default|SetDbgMensaje "MENSAJE"))\n'
            '    (:"Is Not Valid"\n'
            '      (Variables|Default|SetDbgMensaje "No es el Malakh de DA"))))'
            ).replace("NOMBRE", nombre).replace("CUERPO", cuerpo).replace("MENSAJE", mensaje)


def dsl_dar_arma(clave, ruta, etiqueta):
    """GIVE TEMPORARY WEAPON — §10, primera linea.

    Da el arma, la EQUIPA y arranca la corrupcion: el mismo camino que recoger
    una del suelo. Si solo la metiera en el inventario el boton mentiria —
    parece que te la ha dado y no la llevas en la mano."""
    return jugador_accion(
        "DbgDarArma" + clave,
        '      (Class|BPDAPlayerCharacter|DarArmaTemporal j "' + ruta + '")\n',
        "Arma temporal: " + etiqueta)


def dsl_corrupcion(clave, valor, etiqueta):
    """SET VISUAL CORRUPTION STAGE — §10, tercera linea.

    Los cuatro estados del §3.1 son COSMETICOS: mueven el parametro `Corrupcion`
    de `M_DA_ArmaDivina` en el material dinamico del arma en mano y nada mas. No
    tocan vida util, que es justo lo que el PDF prohibe."""
    return jugador_accion(
        "DbgCorrupcion" + clave,
        '      (Class|BPDAPlayerCharacter|FijarCorrupcion j ' + valor + ')\n',
        "Corrupcion: " + etiqueta)


def dsl_forzar_descarte():
    """FORCE DISCARD ATTACK — §10.

    Llama al mismo `ArrojarLanza` que la tecla, asi que respeta el enrutado por
    familia: la lanza se arroja, la trompeta se clava, y con cualquier otra no
    pasa nada."""
    return jugador_accion(
        "DbgForzarDescarte",
        '      (Class|BPDAPlayerCharacter|ArrojarLanza j)\n',
        "Descarte forzado")


def dsl_municion_toggle():
    """INFINITE AMMO ON/OFF — §10.

    Toggle con temporizador de 1 s, no un "dame 99 flechas": el PDF pide
    municion infinita, y rellenar una sola vez se agota igual."""
    return jugador_accion(
        "DbgMunicionToggle",
        '      (Class|BPDAPlayerCharacter|AlternarMunicionInfinita j)\n',
        "Municion infinita alternada")


# ---------------------------------------------------------- COMBAT: la arena
#
# No hay "arena seleccionada": el criterio es DONDE ESTAS. Los tres botones
# actuan sobre la arena en cuya caja caiga el jugador, con el mismo test que
# usa `BuscarEnemigos` del propio `BP_DA_Arena` — caja exacta por
# `InverseTransformLocation`, no un radio, para que las esquinas cuenten.
# Si no estas dentro de ninguna, el mensaje lo dice y no pasa nada.
#
# Los tres pasan por `DbgPermitido` como el resto de acciones destructivas.

def arena_accion(nombre, guarda, cuerpo, mensaje):
    """Fabrica una accion de arena. `guarda` es una condicion extra en DSL
    (o "true"), `cuerpo` las sentencias a ejecutar sobre la arena `a`."""
    return ('(fn %s ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (bind jug (Transformation|GetActorLocation'
            ' (Game|GetPlayerCharacter 0)))\n'
            '  (Variables|Default|SetDbgMensaje'
            ' "No estas dentro de ninguna arena")\n'
            '  (for a (Actor|GetAllActorsOfClass "%s")\n'
            '    (bind rel (Math|Transform|InverseTransformLocation'
            ' (Transformation|GetActorTransform a) jug))\n'
            '    (bind ab (Math|Vector|VectorGetAbs rel))\n'
            '    (bind r (Class|BPDAArena|GetRadioArena a))\n'
            '    (if (and (and (< (.x ab) r) (< (.y ab) r)) %s)\n'
            '%s'
            '      (Variables|Default|SetDbgMensaje "%s"))))'
            % (nombre, DA_ARENA, guarda, cuerpo, mensaje))


def dsl_arena_sellar():
    # Sellar una arena ya sellada volveria a tomar la instantanea; se evita.
    return arena_accion(
        "DbgArenaSellar",
        "(!= (Class|BPDAArena|GetEstado a) 1)",
        "      (Class|BPDAArena|Sellar a)\n",
        "Arena sellada")


def dsl_arena_abrir():
    # Abrir a mano tiene que devolver tambien el objetivo del HUD, o se queda
    # con el texto de la arena y su indice +100 bloqueando a los ZoneTrigger.
    return arena_accion(
        "DbgArenaAbrir",
        "(== (Class|BPDAArena|GetEstado a) 1)",
        "      (Class|BPDAArena|RestaurarObjetivo a)\n"
        "      (Class|BPDAArena|Abrir a)\n",
        "Arena abierta")


def dsl_arena_reiniciar():
    # Solo con la arena sellada: si no lo esta, `PuntoEntrada` no vale nada y
    # el reinicio teletransportaria al jugador al origen del mundo.
    return arena_accion(
        "DbgArenaReiniciar",
        "(== (Class|BPDAArena|GetEstado a) 1)",
        "      (Class|BPDAArena|ReiniciarEncuentro a)\n",
        "Encuentro reiniciado")


def dsl_log_linea():
    return ('(fn DbgLogLinea (Texto)\n'
            '  (Utilities|Array|Add :TargetArray (Variables|Default|GetDbgLog)'
            ' :NewItem Texto)\n'
            '  (if (> (Utilities|Array|Length (Variables|Default|GetDbgLog)) %d)\n'
            '    (Utilities|Array|RemoveIndex'
            ' :TargetArray (Variables|Default|GetDbgLog) :IndexToRemove 0))\n'
            '  (return))' % LOG_MAX)


def dsl_log_tick():
    """El log NO engancha eventos de combate: los observa.

    No hay forma de suscribirse al dano de DCS desde aqui (ver las notas), asi
    que se vigila la vida del jugador y la de su objetivo, y cada bajada se
    anota. Por eso el log dice victima, dano y vida restante, pero NO puede
    decir atacante, nombre del ataque, bloqueo, parry ni critico.

    Solo corre con el log encendido: apagado no cuesta nada."""
    return ('(fn DbgLogTick ()\n'
            '  (if (not (Variables|Default|GetDbgLogOn))\n'
            '    (return))\n'
            + stats() + '\n'
            '  (bind hp ' + leer(TAG_HP) + ')\n'
            '  (bind ant (Variables|Default|GetDbgLastHP))\n'
            '  (if (and (< hp ant) (> ant 0.0))\n'
            '    (CallFunction|DbgLogLinea :Texto'
            ' (Utilities|String|Append'
            ' (Utilities|String|Append "Malakh  |  Damage "'
            ' (Utilities|String|ToString(Integer)'
            ' (Math|Float|Truncate (- ant hp))))'
            ' (Utilities|String|Append "  |  HP "'
            ' (Utilities|String|ToString(Integer) (Math|Float|Truncate hp))))))\n'
            '  (Variables|Default|SetDbgLastHP hp)\n'
            '  (bind tc (Actor|GetComponentbyClass :self (Game|GetPlayerPawn 0)'
            ' :ComponentClass "' + DCS_TARGET + '"))\n'
            '  (bind obj (Class|BPDynamicTargetingComponent|GetSelectedActor :self tc))\n'
            '  (Utilities|IsValid obj\n'
            '    (:"Is Valid"\n'
            '      (bind smo (Actor|GetComponentbyClass :self obj'
            ' :ComponentClass "' + DCS_STATS + '"))\n'
            '      (bind hpo ' + leer(TAG_HP, "smo") + ')\n'
            '      (bind anto (Variables|Default|GetDbgLastHPObj))\n'
            '      (if (and (< hpo anto) (> anto 0.0))\n'
            '        (CallFunction|DbgLogLinea :Texto'
            ' (Utilities|String|Append'
            ' (Utilities|String|Append'
            ' (Utilities|String|Append "Malakh -> "'
            ' (Utilities|String|ToString(Object) obj))'
            ' (Utilities|String|Append "  |  Damage "'
            ' (Utilities|String|ToString(Integer)'
            ' (Math|Float|Truncate (- anto hpo)))))'
            ' (Utilities|String|Append "  |  HP "'
            ' (Utilities|String|ToString(Integer) (Math|Float|Truncate hpo))))))\n'
            '      (Variables|Default|SetDbgLastHPObj hpo))\n'
            '    (:"Is Not Valid")))')


# ------------------------------------------------------------ PLAYER: pintar
#
# Igual que en WORLD: la geometria se define UNA vez aqui y de ella salen el
# dibujado y los clics.

def filas_player():
    """[(titulo, y_titulo, y_botones, [(x, w, etiqueta, accion, encendido)])]"""
    x0, w3, w5 = 8.0, 182.0, 108.0
    pct = lambda f: "(CallFunction|DbgVida :Fraccion %s)" % f
    return [
        ("HEALTH", 130.0, 176.0, [
            (x0, w3, "HEAL FULL", pct("1.0"), "false"),
            (x0 + 190.0, w3, "SET HP 75%", pct("0.75"), "false"),
            (x0 + 380.0, w3, "SET HP 50%", pct("0.5"), "false"),
        ]),
        ("", None, 208.0, [
            (x0, w3, "SET HP 25%", pct("0.25"), "false"),
            (x0 + 190.0, w3, "SET HP 10%", pct("0.1"), "false"),
            (x0 + 380.0, w3, "KILL PLAYER", "(CallFunction|DbgMatar)", "false"),
        ]),
        ("GOD MODE", 244.0, 266.0, [
            (x0, 278.0, "GOD MODE", "(CallFunction|DbgGodToggle)",
             "(Variables|Default|GetDbgGod)"),
            (x0 + 286.0, 278.0, "INFINITE RESOURCE", "(CallFunction|DbgManaToggle)",
             "(Variables|Default|GetDbgManaInf)"),
        ]),
        ("MOVEMENT", 302.0, 324.0, [
            (x0 + i * 112.0, w5, e, "(CallFunction|DbgMov :Mult %s)" % v,
             "(== (Variables|Default|GetDbgMovMult) %s)" % v)
            for i, (e, v) in enumerate([("x0.5", "0.5"), ("x1", "1.0"),
                                        ("x1.5", "1.5"), ("x2", "2.0"),
                                        ("RESET", "1.0")])
        ]),
        # ABILITIES: DCS SI tiene sistema de habilidades (BP_AbilityComponent),
        # pero no tiene desbloqueo ni cooldowns: la habilidad viene del objeto
        # equipado y su coste se paga en Stat.Mana. Asi que lo unico real es el
        # recurso infinito, que ya esta arriba. El resto se deja a la vista,
        # apagado, y sin inventar un sistema paralelo.
        ("ABILITIES", 360.0, 404.0, [
            (x0, w3, "-- UNLOCK ALL", "(CallFunction|DbgNadaAun)", "false"),
            (x0 + 190.0, w3, "-- RESET ABILITIES", "(CallFunction|DbgNadaAun)", "false"),
            (x0 + 380.0, w3, "-- NO COOLDOWNS", "(CallFunction|DbgNadaAun)", "false"),
        ]),
        ("", None, 470.0, [
            (x0, 564.0, "RESET PLAYER STATE", "(CallFunction|DbgResetPlayer)", "false"),
        ]),
    ]


def dsl_nada_aun():
    return ('(fn DbgNadaAun ()\n'
            '  (Variables|Default|SetDbgMensaje'
            ' "Sin sistema detras todavia: ver ABILITIES en las notas"))')


def dsl_tab_player():
    l = ['(fn DbgTabPlayer ()',
         BIND_GEO,
         '  (bind pawn (Game|GetPlayerPawn 0))',
         stats(),
         '  (bind hp ' + leer(TAG_HP) + ')',
         '  (bind hpmax ' + leer(TAG_HP_MAX) + ')']
    # Linea de vida: actual / maximo y porcentaje.
    l.append(texto(X(16.0), Y(152.0),
                   '(Utilities|String|Append'
                   ' (Utilities|String|Append "HP:  "'
                   ' (Utilities|String|Append (Utilities|String|ToString(Float) hp)'
                   ' (Utilities|String|Append "  /  "'
                   ' (Utilities|String|ToString(Float) hpmax))))'
                   ' (Utilities|String|Append "     "'
                   ' (Utilities|String|Append'
                   ' (Utilities|String|ToString(Integer)'
                   ' (Math|Float|Truncate (* (/ hp hpmax) 100.0))) "%")))',
                   HUESO, 1.0))
    for titulo, y_tit, y_bot, botones in filas_player():
        if y_tit:
            l.append(texto(X(16.0), Y(y_tit), '"%s"' % titulo, ORO, 1.05))
        for x, w, etiqueta, _accion, encendido in botones:
            l.append('  (CallFunction|DbgBoton :X %s :Y %s :W %s'
                     ' :Etiqueta "%s" :Encendido %s)'
                     % (X(x), Y(y_bot), SC(w), etiqueta, encendido))
    l.append(texto(X(16.0), Y(382.0),
                   '"El coste de habilidad se paga en Mana: usa INFINITE RESOURCE."',
                   GRIS, 0.8))

    # --- PLAYER DEBUG INFO ---
    l.append(texto(X(16.0), Y(506.0), '"PLAYER DEBUG INFO"', ORO, 1.05))
    l.append('  (bind vel (Transformation|GetVelocity :self pawn))')
    # IsFalling/IsCrouching viven en el COMPONENTE de movimiento, no en el
    # Character ni en el Pawn.
    l.append('  (bind cm (Class|Character|GetCharacterMovement'
             ' :self (Game|GetPlayerCharacter 0)))')
    l.append('  (bind obj (Actor|GetComponentbyClass :self pawn'
             ' :ComponentClass "%s"))' % DCS_TARGET)
    filas = [
        ('(Utilities|String|Append "Velocity:  "'
         ' (Utilities|String|ToString(Float) (Math|Vector|VectorLength vel)))', 528.0),
        ('(Utilities|String|Append "Movement:  "'
         ' (Utilities|String|Append'
         ' (Utilities|String|SelectString "cayendo" "en suelo"'
         ' (Movement|IsFalling :self cm))'
         ' (Utilities|String|SelectString "  agachado" ""'
         ' (Movement|IsCrouching :self cm))))', 548.0),
        ('(Utilities|String|Append "Target:  "'
         ' (Utilities|String|ToString(Object)'
         ' (Class|BPDynamicTargetingComponent|GetSelectedActor :self obj)))', 568.0),
        # "Vivo" se deduce de la vida y no de `CanBeAttacked|IsAlive`, por el
        # mismo motivo que Kill: el pin de interfaz no acepta el Pawn.
        ('(Utilities|String|Append "Is Dead:  "'
         ' (Utilities|String|SelectString "SI" "NO" (<= hp 0.0)))', 588.0),
        ('(Utilities|String|Append "God Mode:  "'
         ' (Utilities|String|Append'
         ' (Utilities|String|ToString(Boolean) (Variables|Default|GetDbgGod))'
         ' (Utilities|String|Append "     Mov x"'
         ' (Utilities|String|ToString(Float) (Variables|Default|GetDbgMovMult)))))', 608.0),
    ]
    for expr, y in filas:
        l.append(texto(X(16.0), Y(y), expr, HUESO, 0.95))
    l.append(texto(X(16.0), Y(636.0),
                   '(Variables|Default|GetDbgMensaje)', ORO, 0.95))
    # Aviso bien visible mientras God Mode este puesto.
    l.append('  (if (Variables|Default|GetDbgGod)')
    l.append(texto(X(300.0), Y(244.0), '"[ ACTIVO ]"', ORO, 1.0))
    l.append('    )')
    l.append('  (return false))')
    return "\n".join(l)


# ------------------------------------------------------------ COMBAT: pintar

def filas_combat():
    x0 = 8.0
    dmg = lambda v: "(CallFunction|DbgDanoJugador :Mult %s)" % v
    ene = lambda v: "(CallFunction|DbgDanoEnemigo :Mult %s)" % v
    act = lambda v: "(== (Variables|Default|GetDbgDmgMult) %s)" % v
    acte = lambda v: "(== (Variables|Default|GetDbgEnemyMult) %s)" % v
    return [
        ("PLAYER DAMAGE", 130.0, 152.0, [
            (x0 + i * 94.0, 90.0, e, dmg(v), act(v))
            for i, (e, v) in enumerate([("x0", "0.0"), ("x0.5", "0.5"), ("x1", "1.0"),
                                        ("x2", "2.0"), ("x5", "5.0"), ("x10", "10.0")])
        ]),
        ("", None, 190.0, [
            (x0, 278.0, "ONE HIT KILL", "(CallFunction|DbgOneHitToggle)",
             "(Variables|Default|GetDbgOneHit)"),
            (x0 + 286.0, 278.0, "COMBAT LOG", "(CallFunction|DbgLogToggle)",
             "(Variables|Default|GetDbgLogOn)"),
        ]),
        ("ENEMY DAMAGE", 228.0, 250.0, [
            (x0 + i * 112.0, 108.0, e, ene(v), acte(v))
            for i, (e, v) in enumerate([("x0", "0.0"), ("x0.5", "0.5"), ("x1", "1.0"),
                                        ("x2", "2.0"), ("x5", "5.0")])
        ]),
        ("COMBAT SPEED", 288.0, 310.0, [
            (x0 + i * 142.0, 138.0, e, "(CallFunction|DbgVelocidad :Valor %s)" % v,
             "false")
            for i, (e, v) in enumerate([("0.1x", "0.1"), ("0.25x", "0.25"),
                                        ("0.5x", "0.5"), ("1x", "1.0")])
        ]),
        ("VISUAL DEBUG", 348.0, 370.0, [
            (x0, 278.0, "WEAPON TRACES", "(CallFunction|DbgTrazasToggle)",
             "(Variables|Default|GetDbgTrazas)"),
            (x0 + 286.0, 278.0, "COLLISION CAPSULES",
             "(CallFunction|DbgColisionesToggle)",
             "(Variables|Default|GetDbgColisiones)"),
        ]),
        # Seis no caben a 114/110: el panel mide PW=580 y empieza en x0=8, o sea
        # 564 utiles. A 94 de paso y 90 de ancho el ultimo acaba en 568.
        # El ESCUDO se queda el ultimo a proposito: es off-hand, y el §10 del PDF
        # lo pide en su propia linea junto al Force Shield Discard que aun no hay.
        ("TEMPORARY WEAPON", 408.0, 430.0, [
            (x0 + i * 94.0, 90.0, e, "(CallFunction|DbgDarArma%s)" % c, "false")
            for i, (c, e) in enumerate([("Lanza", "LANZA"), ("Trompeta", "TROMPETA"),
                                        ("Hacha", "HACHA"), ("Espadon", "ESPADON"),
                                        ("Arco", "ARCO"), ("Escudo", "ESCUDO")])
        ]),
        ("CORRUPTION STAGE", 468.0, 490.0, [
            (x0 + i * 142.0, 138.0, e, "(CallFunction|DbgCorrupcion%s)" % c, "false")
            for i, (c, e) in enumerate([("Cel", "CELESTIAL"), ("Tai", "TAINTED"),
                                        ("Cor", "CORRUPTA"), ("Fra", "FRACTURED")])
        ]),
        ("", None, 528.0, [
            (x0, 278.0, "FORCE DISCARD", "(CallFunction|DbgForzarDescarte)", "false"),
            (x0 + 286.0, 278.0, "INFINITE AMMO", "(CallFunction|DbgMunicionToggle)",
             "(Class|BPDAPlayerCharacter|GetMunicionInfinita (Utilities|Casting|CastToBP_DA_PlayerCharacter (Game|GetPlayerPawn 0)))"),
        ]),
        ("ARENA YOU ARE IN", 588.0, 610.0, [
            (x0, 182.0, "SEAL ARENA", "(CallFunction|DbgArenaSellar)", "false"),
            (x0 + 190.0, 182.0, "OPEN ARENA", "(CallFunction|DbgArenaAbrir)", "false"),
            (x0 + 380.0, 182.0, "RESTART FIGHT",
             "(CallFunction|DbgArenaReiniciar)", "false"),
        ]),
        ("", None, 648.0, [
            (x0, 564.0, "RESET COMBAT DEBUG", "(CallFunction|DbgResetCombat)", "false"),
        ]),
    ]


def dsl_tab_combat():
    l = ['(fn DbgTabCombat ()', BIND_GEO]
    for titulo, y_tit, y_bot, botones in filas_combat():
        if y_tit:
            l.append(texto(X(16.0), Y(y_tit), '"%s"' % titulo, ORO, 1.05))
        for x, w, etiqueta, _accion, encendido in botones:
            l.append('  (CallFunction|DbgBoton :X %s :Y %s :W %s'
                     ' :Etiqueta "%s" :Encendido %s)'
                     % (X(x), Y(y_bot), SC(w), etiqueta, encendido))
    # El log, ultimas lineas. Va a Y fija, NO detras de la ultima fila: si se
    # anade un grupo a `filas_combat()` hay que bajar estas tres Y y subir el
    # alto del panel para COMBAT en `dsl_dibujar()`, o el titulo del log se come
    # los botones de la ultima fila. Paso el 2026-08-23 al meter la arena.
    l.append(texto(X(16.0), Y(512.0), '"COMBAT LOG"', ORO, 1.05))
    l.append('  (bind lg (Variables|Default|GetDbgLog))')
    l.append('  (bind nl (Utilities|Array|Length lg))')
    l.append('  (for i (range nl)')
    l.append('    ' + texto(X(16.0), "(+ %s (* i %s))" % (Y(534.0), SC(20.0)),
                            '(Utilities|Array|Get(acopy) lg i)', HUESO, 0.9).strip())
    l.append('    )')
    l.append(texto(X(16.0), Y(696.0),
                   '(Variables|Default|GetDbgMensaje)', ORO, 0.95))
    l.append('  (return false))')
    return "\n".join(l)


def dsl_click_combat():
    l = ['(fn DbgClickCombat (MX MY)', BIND_GEO]
    for _t, _yt, y_bot, botones in filas_combat():
        for x, w, _etiqueta, accion, _enc in botones:
            l.append('  (if %s' % caja("MX", "MY", X(x), Y(y_bot),
                                       SC(w), SC(BOTON_H)))
            l.append('    ' + accion)
            l.append('    (return))')
    l.append('  (return false))')
    return "\n".join(l)


# ---------------------------------------------------------------- AI: pintar
#
# Las listas de tipos y de encuentros son dinamicas (salen del Data Asset), asi
# que van como filas con UN solo rectangulo de clic cada una, igual que la lista
# de teleports: anadir un enemigo o un preset no obliga a tocar el grafo.

AI_TIPOS_Y = 152.0
AI_ENC_Y = 552.0


def filas_ai():
    x0, w3, w5 = 8.0, 182.0, 108.0
    cant = lambda n: "(Variables|Default|SetDbgCantSel %s)" % n
    dist = lambda d: "(Variables|Default|SetDbgDistSel %s)" % d
    return [
        ("QUANTITY", 306.0, 326.0, [
            (x0 + i * 112.0, w5, e, cant(v),
             "(== (Variables|Default|GetDbgCantSel) %s)" % v)
            for i, (e, v) in enumerate([("1", "1"), ("2", "2"), ("3", "3"),
                                        ("5", "5"), ("10", "10")])
        ]),
        ("SPAWN DISTANCE", 362.0, 382.0, [
            (x0 + i * 142.0, 138.0, e, dist(v),
             "(== (Variables|Default|GetDbgDistSel) %s)" % v)
            for i, (e, v) in enumerate([("3m", "300.0"), ("5m", "500.0"),
                                        ("10m", "1000.0"), ("20m", "2000.0")])
        ]),
        ("", None, 418.0, [
            (x0, 278.0, "SPAWN", "(CallFunction|DbgSpawn)", "false"),
            (x0 + 286.0, 278.0, "CLEAR DEBUG ENEMIES", "(CallFunction|DbgLimpiar)",
             "false"),
        ]),
        ("AI CONTROLS", 452.0, 472.0, [
            (x0, w3, "FREEZE AI", "(CallFunction|DbgIALogica :Congelar true)",
             "(Variables|Default|GetDbgCongelada)"),
            (x0 + 190.0, w3, "DISABLE AI", "(CallFunction|DbgIAApagar :Apagar true)",
             "(Variables|Default|GetDbgApagada)"),
            (x0 + 380.0, w3, "IGNORE PLAYER",
             "(CallFunction|DbgIgnorarToggle :Ignorar true)",
             "(Variables|Default|GetDbgIgnorar)"),
        ]),
        ("", None, 502.0, [
            (x0, w3, "UNFREEZE AI", "(CallFunction|DbgIALogica :Congelar false)",
             "false"),
            (x0 + 190.0, w3, "ENABLE AI", "(CallFunction|DbgIAApagar :Apagar false)",
             "false"),
            (x0 + 380.0, w3, "RESTORE AGGRO",
             "(CallFunction|DbgIgnorarToggle :Ignorar false)", "false"),
        ]),
        ("", None, 700.0, [
            (x0, 564.0, "CLEAR DEBUG ARENA", "(CallFunction|DbgResetArena)", "false"),
        ]),
    ]


def dsl_tab_ai():
    l = ['(fn DbgTabAI ()', BIND_GEO, '  (CallFunction|DbgCargarEnem)',
         '  (bind tipos (Variables|Default|GetDbgTipos))',
         '  (bind nt (Utilities|Array|Length tipos))']
    l.append(texto(X(16.0), Y(130.0), '"ENEMY TYPE"', ORO, 1.05))
    l.append('  (for i (range nt)')
    l.append('    (bind ty (+ %s (* i %s)))' % (Y(AI_TIPOS_Y), SC(FILA_AI)))
    l.append('    (bind sel (== i (Variables|Default|GetDbgTipoSel)))')
    l.append('    (if sel')
    l.append('    ' + rect(X(8.0), "ty", SC(PW - 16.0), SC(FILA_AI - 3.0),
                           BOTON_ON).strip())
    l.append('      (else')
    l.append('    ' + rect(X(8.0), "ty", SC(PW - 16.0), SC(FILA_AI - 3.0),
                           BOTON).strip() + '))')
    l.append('    ' + texto(X(18.0), "(+ ty %s)" % SC(2.0),
                            '(CallFunction|DbgCampoTipo'
                            ' :Indice i :Campo 0)', HUESO, 0.95).strip())
    l.append('    )')

    for titulo, y_tit, y_bot, botones in filas_ai():
        if y_tit:
            l.append(texto(X(16.0), Y(y_tit), '"%s"' % titulo, ORO, 1.05))
        for x, w, etiqueta, _accion, encendido in botones:
            l.append('  (CallFunction|DbgBoton :X %s :Y %s :W %s'
                     ' :Etiqueta "%s" :Encendido %s)'
                     % (X(x), Y(y_bot), SC(w), etiqueta, encendido))

    # Encuentros (presets), lista dinamica igual que los tipos.
    l.append(texto(X(16.0), Y(532.0), '"ENCOUNTER PRESETS"', ORO, 1.05))
    l.append('  (bind encs (Variables|Default|GetDbgEncuentros))')
    l.append('  (bind ne (Utilities|Array|Length encs))')
    l.append('  (for i (range ne)')
    l.append('    (bind ey (+ %s (* i %s)))' % (Y(AI_ENC_Y), SC(FILA_AI)))
    l.append('    ' + rect(X(8.0), "ey", SC(PW - 16.0), SC(FILA_AI - 3.0),
                           BOTON).strip())
    l.append('    ' + texto(X(18.0), "(+ ey %s)" % SC(2.0),
                            '(CallFunction|DbgCampoEnc'
                            ' :Indice i :Campo 0)', HUESO, 0.95).strip())
    l.append('    )')

    # --- SELECTED ENEMY DEBUG: el objetivo actual del jugador ---
    l.append(texto(X(16.0), Y(614.0), '"SELECTED ENEMY"', ORO, 1.05))
    l.append('  (bind pawn (Game|GetPlayerPawn 0))')
    l.append('  (bind tc (Actor|GetComponentbyClass :self pawn'
             ' :ComponentClass "%s"))' % DCS_TARGET)
    l.append('  (bind obj (Class|BPDynamicTargetingComponent|GetSelectedActor'
             ' :self tc))')
    l.append('  (Utilities|IsValid obj')
    l.append('    (:"Is Valid"')
    l.append('      (bind smo (Actor|GetComponentbyClass :self obj'
             ' :ComponentClass "%s"))' % DCS_STATS)
    l.append('      ' + texto(X(16.0), Y(636.0),
                              '(Utilities|String|Append "Name:  "'
                              ' (Utilities|String|ToString(Object) obj))',
                              HUESO, 0.9).strip())
    l.append('      ' + texto(X(16.0), Y(656.0),
                              '(Utilities|String|Append'
                              ' (Utilities|String|Append "HP:  "'
                              ' (Utilities|String|ToString(Integer)'
                              ' (Math|Float|Truncate ' + leer(TAG_HP, "smo") + ')))'
                              ' (Utilities|String|Append "     Dist:  "'
                              ' (Utilities|String|ToString(Integer)'
                              ' (Math|Float|Truncate (/ (Math|Vector|VectorLength'
                              ' (- (Transformation|GetActorLocation :self obj)'
                              ' (Transformation|GetActorLocation :self pawn)))'
                              ' 100.0)))))', HUESO, 0.9).strip())
    l.append('      ' + texto(X(16.0), Y(676.0),
                              '(Utilities|String|Append "Controller:  "'
                              ' (Utilities|String|ToString(Object)'
                              ' (AI|GetAIController :ControlledActor obj)))',
                              HUESO, 0.9).strip())
    l.append('      )')
    l.append('    (:"Is Not Valid"')
    l.append('      ' + texto(X(16.0), Y(636.0),
                              '"Sin objetivo: fija a un enemigo para verlo aqui."',
                              GRIS, 0.85).strip())
    # Sin `(return false)` al final: el IsValid es multi-exec y cierra el flujo.
    l.append('      )))')
    return "\n".join(l)


def dsl_click_ai():
    l = ['(fn DbgClickAI (MX MY)', BIND_GEO,
         '  (bind nt (Utilities|Array|Length (Variables|Default|GetDbgTipos)))',
         '  (bind ne (Utilities|Array|Length (Variables|Default|GetDbgEncuentros)))']
    # Lista de tipos: un rectangulo, la fila sale de la Y del raton.
    l.append('  (bind fint (+ %s (* nt %s)))' % (Y(AI_TIPOS_Y), SC(FILA_AI)))
    l.append('  (if (and (and (>= MX %s) (< MX %s))'
             ' (and (>= MY %s) (< MY fint)))'
             % (X(8.0), X(PW - 8.0), Y(AI_TIPOS_Y)))
    l.append('    (Variables|Default|SetDbgTipoSel'
             ' (Math|Float|Truncate (/ (- MY %s) %s)))' % (Y(AI_TIPOS_Y), SC(FILA_AI)))
    l.append('    (return))')
    l.append('  (bind fine (+ %s (* ne %s)))' % (Y(AI_ENC_Y), SC(FILA_AI)))
    l.append('  (if (and (and (>= MX %s) (< MX %s))'
             ' (and (>= MY %s) (< MY fine)))'
             % (X(8.0), X(PW - 8.0), Y(AI_ENC_Y)))
    l.append('    (CallFunction|DbgEncuentro :Indice'
             ' (Math|Float|Truncate (/ (- MY %s) %s)))' % (Y(AI_ENC_Y), SC(FILA_AI)))
    l.append('    (return))')
    for _t, _yt, y_bot, botones in filas_ai():
        for x, w, _etiqueta, accion, _enc in botones:
            l.append('  (if %s' % caja("MX", "MY", X(x), Y(y_bot),
                                       SC(w), SC(BOTON_H)))
            l.append('    ' + accion)
            l.append('    (return))')
    l.append('  (return false))')
    return "\n".join(l)


# -------------------------------------------------------------- BOSS: pintar

BOSS_LISTA_Y = 152.0


def filas_boss():
    x0, w3, w5 = 8.0, 182.0, 108.0
    vida = lambda f: "(CallFunction|DbgBossVida :Fraccion %s)" % f
    nada = "(CallFunction|DbgNadaAun)"
    return [
        ("HEALTH", 240.0, 262.0, [
            (x0 + i * 112.0, w5, e, vida(v), "false")
            for i, (e, v) in enumerate([("100%", "1.0"), ("75%", "0.75"),
                                        ("50%", "0.5"), ("25%", "0.25"),
                                        ("10%", "0.1")])
        ]),
        ("", None, 294.0, [
            (x0, 278.0, "KILL BOSS", vida("0.0"), "false"),
        ]),
        # Fases: preparadas y APAGADAS. Ver la explicacion en las acciones.
        ("PHASE CONTROL   (sin sistema formal de fases)", 332.0, 354.0, [
            (x0, w5, "-- START", nada, "false"),
            (x0 + 112.0, w5, "-- PHASE 1", nada, "false"),
            (x0 + 224.0, w5, "-- PHASE 2", nada, "false"),
            (x0 + 336.0, w5, "-- PHASE 3", nada, "false"),
            (x0 + 448.0, w5, "-- NEXT", nada, "false"),
        ]),
        ("BOSS STATES   (sin sistema de stagger ni finisher)", 392.0, 414.0, [
            (x0, w3, "-- FORCE STAGGER", nada, "false"),
            (x0 + 190.0, w3, "-- RESET STAGGER", nada, "false"),
            (x0 + 380.0, w3, "-- FINISHER", nada, "false"),
        ]),
        ("CINEMATICS / QTE   (sistemas aun no existentes)", 452.0, 474.0, [
            (x0, w3, "-- INTRO CINEMATIC", nada, "false"),
            (x0 + 190.0, w3, "-- MID CINEMATIC", nada, "false"),
            (x0 + 380.0, w3, "-- TRIGGER QTE", nada, "false"),
        ]),
        ("", None, 506.0, [
            (x0, w3, "-- QTE SUCCESS", nada, "false"),
            (x0 + 190.0, w3, "-- QTE FAILURE", nada, "false"),
            (x0 + 380.0, w3, "-- RESTART BOSS", nada, "false"),
        ]),
    ]


def dsl_tab_boss():
    l = ['(fn DbgTabBoss ()', BIND_GEO, '  (CallFunction|DbgCargarBoss)',
         '  (bind nb (Utilities|Array|Length (Variables|Default|GetDbgBosses)))']
    l.append(texto(X(16.0), Y(130.0), '"BOSS SELECTION"', ORO, 1.05))
    l.append('  (for i (range nb)')
    l.append('    (bind by (+ %s (* i %s)))' % (Y(BOSS_LISTA_Y), SC(FILA_AI)))
    l.append('    (if (== i (Variables|Default|GetDbgBossSel))')
    l.append('    ' + rect(X(8.0), "by", SC(PW - 16.0), SC(FILA_AI - 3.0),
                           BOTON_ON).strip())
    l.append('      (else')
    l.append('    ' + rect(X(8.0), "by", SC(PW - 16.0), SC(FILA_AI - 3.0),
                           BOTON).strip() + '))')
    l.append('    ' + texto(X(18.0), "(+ by %s)" % SC(2.0),
                            '(CallFunction|DbgCampoBoss :Indice i :Campo 0)',
                            HUESO, 0.95).strip())
    l.append('    )')

    for titulo, y_tit, y_bot, botones in filas_boss():
        if y_tit:
            l.append(texto(X(16.0), Y(y_tit), '"%s"' % titulo, ORO, 0.95))
        for x, w, etiqueta, _accion, encendido in botones:
            l.append('  (CallFunction|DbgBoton :X %s :Y %s :W %s'
                     ' :Etiqueta "%s" :Encendido %s)'
                     % (X(x), Y(y_bot), SC(w), etiqueta, encendido))

    # --- BOSS DEBUG INFO: solo lo que se puede leer de verdad ---
    l.append(texto(X(16.0), Y(546.0), '"BOSS DEBUG INFO"', ORO, 1.05))
    l.append('  (bind pawn (Game|GetPlayerPawn 0))')
    l.append(boss_ref().rstrip())
    l.append('  (bind ac2 (Utilities|Casting|CastToActorClass :Class cls)')
    l.append('    (:then')
    l.append('      (bind lst (Actor|GetAllActorsOfClass :ActorClass ac2))')
    l.append('      (if (> (Utilities|Array|Length lst) 0)')
    l.append('        (bind jf (Utilities|Array|Get(acopy) lst 0))')
    l.append('        (bind smj (Actor|GetComponentbyClass :self jf'
             ' :ComponentClass "%s"))' % DCS_STATS)
    l.append('        ' + texto(X(16.0), Y(568.0),
                                '(Utilities|String|Append "Boss:  "'
                                ' (Utilities|String|ToString(Object) jf))',
                                HUESO, 0.9).strip())
    l.append('        ' + texto(X(16.0), Y(588.0),
                                '(Utilities|String|Append'
                                ' (Utilities|String|Append "HP:  "'
                                ' (Utilities|String|ToString(Integer)'
                                ' (Math|Float|Truncate ' + leer(TAG_HP, "smj") + ')))'
                                ' (Utilities|String|Append "  /  "'
                                ' (Utilities|String|ToString(Integer)'
                                ' (Math|Float|Truncate ' + leer(TAG_HP_MAX, "smj") + '))))',
                                HUESO, 0.9).strip())
    l.append('        ' + texto(X(16.0), Y(608.0),
                                '(Utilities|String|Append "Distancia a Malakh:  "'
                                ' (Utilities|String|ToString(Integer)'
                                ' (Math|Float|Truncate (/ (Math|Vector|VectorLength'
                                ' (- (Transformation|GetActorLocation :self jf)'
                                ' (Transformation|GetActorLocation :self pawn)))'
                                ' 100.0))))', HUESO, 0.9).strip())
    l.append('        ' + texto(X(16.0), Y(628.0),
                                '"Phase / State / Stagger / Active Attack:  '
                                'no accesibles (ver notas)"', GRIS, 0.8).strip())
    l.append('        (else')
    l.append('          ' + texto(X(16.0), Y(568.0),
                                  '"Ese boss no esta colocado en el nivel abierto."',
                                  GRIS, 0.85).strip() + ')))')
    # Tres cierres: el (:CastFailed, el (bind ac2 y el (fn.
    l.append('    (:CastFailed)))')
    return "\n".join(l)


def dsl_click_boss():
    l = ['(fn DbgClickBoss (MX MY)', BIND_GEO,
         '  (bind nb (Utilities|Array|Length (Variables|Default|GetDbgBosses)))']
    l.append('  (bind finb (+ %s (* nb %s)))' % (Y(BOSS_LISTA_Y), SC(FILA_AI)))
    l.append('  (if (and (and (>= MX %s) (< MX %s))'
             ' (and (>= MY %s) (< MY finb)))'
             % (X(8.0), X(PW - 8.0), Y(BOSS_LISTA_Y)))
    l.append('    (Variables|Default|SetDbgBossSel'
             ' (Math|Float|Truncate (/ (- MY %s) %s)))'
             % (Y(BOSS_LISTA_Y), SC(FILA_AI)))
    l.append('    (return))')
    for _t, _yt, y_bot, botones in filas_boss():
        for x, w, _etiqueta, accion, _enc in botones:
            l.append('  (if %s' % caja("MX", "MY", X(x), Y(y_bot),
                                       SC(w), SC(BOTON_H)))
            l.append('    ' + accion)
            l.append('    (return))')
    l.append('  (return false))')
    return "\n".join(l)


# ------------------------------------------------------------- STORY: pintar

def filas_story():
    x0, w3, w5 = 8.0, 182.0, 108.0
    nada = "(CallFunction|DbgNadaAun)"
    return [
        ("STORY FLAGS   (el objetivo del HUD es el unico flag global real)",
         130.0, 174.0, [
             (x0, w3, "OBJETIVO  -1", "(CallFunction|DbgObjetivo :Delta -1)", "false"),
             (x0 + 190.0, w3, "OBJETIVO  +1", "(CallFunction|DbgObjetivo :Delta 1)",
              "false"),
             (x0 + 380.0, w3, "GUIA BLOQUEADA", "(CallFunction|DbgGuiaToggle)",
              "(Variables|Default|GetGuiaBloqueada)"),
         ]),
        ("CHECKPOINTS   (BP_RespawnVolume del nivel)", 212.0, 234.0, [
            (x0, w3, "ANTERIOR",
             "(CallFunction|DbgCheckpoint :Delta -1 :Ir false)", "false"),
            (x0 + 190.0, w3, "SIGUIENTE",
             "(CallFunction|DbgCheckpoint :Delta 1 :Ir false)", "false"),
            (x0 + 380.0, w3, "IR AL CHECKPOINT",
             "(CallFunction|DbgCheckpoint :Delta 0 :Ir true)", "false"),
        ]),
        ("CHECKPOINT TEMPORAL DE DEBUG   (nunca toca un save)", 272.0, 294.0, [
            (x0, 278.0, "SET DEBUG CHECKPOINT", "(CallFunction|DbgGuardarPos)",
             "(Variables|Default|GetDbgTieneGuardada)"),
            (x0 + 286.0, 278.0, "RESPAWN AT DEBUG CP",
             "(CallFunction|DbgIrAGuardada)", "false"),
        ]),
        # MARCAS: la primera seccion de STORY con sistema de verdad detras.
        # Sustituye a PUZZLES y COLLECTIBLES, que eran botones muertos.
        ("MARCAS   (BP_DA_GameState)", 332.0, 354.0, [
            (x0, w3, "BORRAR TODO", "(CallFunction|DbgMarcasBorrar)", "false"),
            (x0 + 190.0, w3, "REINICIAR ESFERA",
             "(CallFunction|DbgMarcasReiniciar)", "false"),
        ]),
        ("", None, 452.0, [
            (x0, 564.0, "RESET STORY DEBUG", "(CallFunction|DbgResetStory)", "false"),
        ]),
    ]


def dsl_tab_story():
    l = ['(fn DbgTabStory ()', BIND_GEO]
    for titulo, y_tit, y_bot, botones in filas_story():
        if y_tit:
            l.append(texto(X(16.0), Y(y_tit), '"%s"' % titulo, ORO, 0.95))
        for x, w, etiqueta, _accion, encendido in botones:
            l.append('  (CallFunction|DbgBoton :X %s :Y %s :W %s'
                     ' :Etiqueta "%s" :Encendido %s)'
                     % (X(x), Y(y_bot), SC(w), etiqueta, encendido))
    # Estado real, leido de las variables heredadas del HUD del juego.
    l.append(texto(X(16.0), Y(152.0),
                   '(Utilities|String|Append'
                   ' (Utilities|String|Append "ObjectiveIndex:  "'
                   ' (Utilities|String|ToString(Integer)'
                   ' (Variables|Default|GetObjectiveIndex)))'
                   ' (Utilities|String|Append "     "'
                   ' (Utilities|String|ToString(Text)'
                   ' (Variables|Default|GetObjectiveText))))', HUESO, 0.9))
    # Estado de las Marcas. Se lee por FUNCION y no por variable: el DSL no sabe
    # crear el getter de una variable de otro blueprint.
    l.append('  (bind gs (Utilities|Casting|CastToBP_DA_GameState (Game|GetGameState)))')
    l.append(texto(X(16.0), Y(376.0),
                   '(Class|BPDAGameState|Resumen :self gs)', HUESO, 0.95))
    l.append(texto(X(16.0), Y(398.0),
                   '(Utilities|String|Append "Marcas:  "'
                   ' (Class|BPDAGameState|Historial :self gs))', GRIS, 0.85))
    l.append('  (bind vols (Actor|GetAllActorsOfClass :ActorClass "%s"))' % RESPAWN)
    l.append(texto(X(16.0), Y(486.0),
                   '(Utilities|String|Append'
                   ' (Utilities|String|Append "Checkpoints en el nivel:  "'
                   ' (Utilities|String|ToString(Integer)'
                   ' (Utilities|Array|Length vols)))'
                   ' (Utilities|String|Append "     seleccionado:  "'
                   ' (Utilities|String|ToString(Integer)'
                   ' (Variables|Default|GetDbgCheckSel))))', HUESO, 0.9))
    l.append(texto(X(16.0), Y(508.0),
                   '"Un destino de WORLD puede llevar objetivo: sexto campo de su linea."',
                   GRIS, 0.8))
    l.append(texto(X(16.0), Y(534.0),
                   '(Variables|Default|GetDbgMensaje)', ORO, 0.95))
    l.append('  (return false))')
    return "\n".join(l)


def dsl_click_story():
    l = ['(fn DbgClickStory (MX MY)', BIND_GEO]
    for _t, _yt, y_bot, botones in filas_story():
        for x, w, _etiqueta, accion, _enc in botones:
            l.append('  (if %s' % caja("MX", "MY", X(x), Y(y_bot),
                                       SC(w), SC(BOTON_H)))
            l.append('    ' + accion)
            l.append('    (return))')
    l.append('  (return false))')
    return "\n".join(l)


def caja(mx, my, x, y, w, h):
    return ('(and (and (>= %s %s) (< %s (+ %s %s))) (and (>= %s %s) (< %s (+ %s %s))))'
            % (mx, x, mx, x, w, my, y, my, y, h))


# ------------------------------------------------- acciones de FINISHERS
#
# Los valores del finisher NO viven en el panel: viven en BP_DA_HUD, el PADRE,
# y de ahi los lee BP_DA_FinisherLogic al empezar cada ejecucion. Por eso se
# tocan con `Variables|Default|Set...`: son variables HEREDADAS. El DSL se come
# el guion bajo, asi que `SetFinDilatacion` escribe `Fin_Dilatacion`
# (comprobado leyendo el grafo de vuelta, no supuesto).
#
# Estan en el HUD y no en el CDO de la logica porque la logica se instancia y
# se destruye en cada finisher, y a un CDO no se le puede escribir desde juego.

FIN_DEFECTO = [("Dilatacion", 0.65), ("MatarEn", 0.9),
               ("CamaraLado", 200.0), ("CamaraAlto", -20.0),
               ("CamaraFrente", 0.7), ("CamaraFOV", 80.0)]

FIN_ETIQ = {"Dilatacion": "Camara lenta", "HitStopEn": "Golpe en",
            "MatarEn": "Muerte en", "CamaraLado": "Distancia",
            "CamaraAlto": "Altura", "CamaraFrente": "Tres cuartos",
            "CamaraFOV": "FOV"}


def dsl_fin_fijar():
    """Valor absoluto: lo usan los cinco presets de camara lenta."""
    return ('(fn DbgFinDilFijar (Valor)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Variables|Default|SetFinDilatacion Valor)\n'
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "Camara lenta:  x"'
            ' (Utilities|String|ToString(Float) Valor)))\n'
            '  (return))')


def dsl_fin_delta(nombre):
    """Suma un paso. Una funcion por variable, para no cablear enums."""
    return ('(fn DbgFin%s (Delta)\n' % nombre +
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (Variables|Default|SetFin%s'
            ' (+ (Variables|Default|GetFin%s) Delta))\n' % (nombre, nombre) +
            '  (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "%s:  "'
            ' (Utilities|String|ToString(Float)'
            ' (Variables|Default|GetFin%s))))\n' % (FIN_ETIQ[nombre], nombre) +
            '  (return))')


def dsl_fin_reset():
    l = ['(fn DbgFinReset ()',
         '  (if (not (CallFunction|DbgPermitido))',
         '    (return))']
    for n, v in FIN_DEFECTO:
        l.append('  (Variables|Default|SetFin%s %.3f)' % (n, v))
    l.append('  (Variables|Default|SetDbgMensaje'
             ' "Finishers: valores por defecto")')
    l.append('  (return))')
    return "\n".join(l)


def filas_finishers():
    x0, w6, w4 = 8.0, 88.0, 137.0
    dil = lambda v: '(CallFunction|DbgFinDilFijar :Valor %.2f)' % v
    act = lambda v: '(== (Variables|Default|GetFinDilatacion) %.2f)' % v
    # Ordenados de mas rapido a mas lento. MUY RAPIDA pasa de 1.0: no es camara
    # lenta suave, es ACELERAR el finisher, que es la unica forma de que se note
    # "rapido" de verdad (0.85 sigue siendo lento, solo poco).
    return [
        ("VELOCIDAD DEL FINISHER   (preset, o numero exacto abajo)",
         130.0, 152.0, [
             (x0, w6, "MUY RAPIDA", dil(1.5), act(1.5)),
             (x0 + 92.0, w6, "SIN", dil(1.0), act(1.0)),
             (x0 + 184.0, w6, "RAPIDA", dil(0.85), act(0.85)),
             (x0 + 276.0, w6, "NORMAL", dil(0.65), act(0.65)),
             (x0 + 368.0, w6, "LENTA", dil(0.35), act(0.35)),
             (x0 + 460.0, w6, "MUY LENTA", dil(0.15), act(0.15)),
         ]),
        ("", None, 184.0, [
            (x0, w4, "VELOC  - 0.05",
             "(CallFunction|DbgFinDilatacion :Delta -0.05)", "false"),
            (x0 + 141.0, w4, "VELOC  + 0.05",
             "(CallFunction|DbgFinDilatacion :Delta 0.05)", "false"),
        ]),
        ("ENCUADRE   (relativo al centro de la capsula del angel, no al suelo)",
         220.0, 242.0, [
            (x0, w4, "ALTURA  - 10",
             "(CallFunction|DbgFinCamaraAlto :Delta -10.0)", "false"),
            (x0 + 141.0, w4, "ALTURA  + 10",
             "(CallFunction|DbgFinCamaraAlto :Delta 10.0)", "false"),
            (x0 + 282.0, w4, "DIST  - 20",
             "(CallFunction|DbgFinCamaraLado :Delta -20.0)", "false"),
            (x0 + 423.0, w4, "DIST  + 20",
             "(CallFunction|DbgFinCamaraLado :Delta 20.0)", "false"),
        ]),
        ("", None, 274.0, [
            (x0, w4, "3/4  - 0.1",
             "(CallFunction|DbgFinCamaraFrente :Delta -0.1)", "false"),
            (x0 + 141.0, w4, "3/4  + 0.1",
             "(CallFunction|DbgFinCamaraFrente :Delta 0.1)", "false"),
            (x0 + 282.0, w4, "FOV  - 5",
             "(CallFunction|DbgFinCamaraFOV :Delta -5.0)", "false"),
            (x0 + 423.0, w4, "FOV  + 5",
             "(CallFunction|DbgFinCamaraFOV :Delta 5.0)", "false"),
        ]),
        ("QUE TAKEDOWN SALE   (para repetir el que estas arreglando)",
         310.0, 332.0, [
            (x0, w4, "< ANTERIOR",
             "(CallFunction|DbgFinIndice :Delta -1)", "false"),
            (x0 + 141.0, w4, "SIGUIENTE >",
             "(CallFunction|DbgFinIndice :Delta 1)", "false"),
            (x0 + 282.0, 278.0, "AL AZAR",
             "(CallFunction|DbgFinIndice :Delta 0)",
             "(< (Variables|Default|GetFinIndice) 0)"),
        ]),
        ("PUNTO DE MUERTE   (fraccion del montage; bajarlo evita el despertar)",
         372.0, 394.0, [
            (x0, w4, "MUERTE  - 0.05",
             "(CallFunction|DbgFinMatarEn :Delta -0.05)", "false"),
            (x0 + 141.0, w4, "MUERTE  + 0.05",
             "(CallFunction|DbgFinMatarEn :Delta 0.05)", "false"),
            (x0 + 282.0, 278.0, "VALORES POR DEFECTO",
             "(CallFunction|DbgFinReset)", "false"),
        ]),
    ]


def dsl_tab_finishers():
    l = ['(fn DbgTabFinishers ()', BIND_GEO]
    for titulo, y_tit, y_bot, botones in filas_finishers():
        if y_tit:
            l.append(texto(X(16.0), Y(y_tit), '"%s"' % titulo, ORO, 0.95))
        for x, w, etiqueta, _accion, encendido in botones:
            l.append('  (CallFunction|DbgBoton :X %s :Y %s :W %s'
                     ' :Etiqueta "%s" :Encendido %s)'
                     % (X(x), Y(y_bot), SC(w), etiqueta, encendido))
    l.append(texto(X(16.0), Y(436.0), '"VALORES EN USO"', ORO, 0.95))
    for i, (n, _v) in enumerate(FIN_DEFECTO):
        l.append(texto(X(16.0), Y(458.0 + i * 22.0),
                       '(Utilities|String|Append "%s:   "'
                       ' (Utilities|String|ToString(Float)'
                       ' (Variables|Default|GetFin%s)))' % (FIN_ETIQ[n], n),
                       HUESO, 0.9))
    l.append(texto(X(16.0), Y(414.0),
                   '(Utilities|String|Append "Takedown en uso:   "'
                   ' (select (< (Variables|Default|GetFinIndice) 0) "al azar"'
                   ' (Utilities|String|Append "fijo, el numero "'
                   ' (Utilities|String|ToString(Integer)'
                   ' (+ (Variables|Default|GetFinIndice) 1)))))', HUESO, 0.9))
    l.append(texto(X(16.0), Y(618.0),
                   '"Se aplican al siguiente finisher: no hace falta recompilar."',
                   GRIS, 0.8))
    l.append(texto(X(16.0), Y(640.0),
                   '(Variables|Default|GetDbgMensaje)', ORO, 0.95))
    l.append('  (return false))')
    return "\n".join(l)


def dsl_click_finishers():
    l = ['(fn DbgClickFinishers (MX MY)', BIND_GEO]
    for _t, _yt, y_bot, botones in filas_finishers():
        for x, w, _etiqueta, accion, _enc in botones:
            l.append('  (if %s' % caja("MX", "MY", X(x), Y(y_bot),
                                       SC(w), SC(BOTON_H)))
            l.append('    ' + accion)
            l.append('    (return))')
    l.append('  (return false))')
    return "\n".join(l)


def dsl_fin_indice():
    return ('(fn DbgFinIndice (Delta)\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (if (== Delta 0)\n'
            '    (Variables|Default|SetFinIndice -1)\n'
            '    (Variables|Default|SetDbgMensaje "Finisher:  al azar")\n'
            '    (else\n'
            '      (bind ahora (Variables|Default|GetFinIndice))\n'
            '      (bind bruto (+ (select (< ahora 0) 0 ahora) Delta))\n'
            '      (bind final (select (< bruto 0) 9 (select (> bruto 9) 0 bruto)))\n'
            '      (Variables|Default|SetFinIndice final)\n'
            '      (Variables|Default|SetDbgMensaje'
            ' (Utilities|String|Append "Finisher fijo:  numero "'
            ' (Utilities|String|ToString(Integer) (+ final 1))))))\n'
            '  (return))')


# ------------------------------------------------- guardado de la config
#
# El panel vive y muere con el PIE: sus valores vuelven al defecto en cada
# Play. Esto los escribe a disco en un SaveGame propio y los relee al arrancar,
# para no tener que reconfigurar lo mismo cada vez.
#
# Se guarda en CADA clic del panel, no en cada accion: un solo gancho al final
# de DbgClick cubre botones, cambio de pestana y zoom, en vez de diez llamadas
# repartidas que hay que acordarse de mantener.
#
# NO se guardan God mode, One Hit Kill ni los multiplicadores de dano: esos no
# son un numero, son cambios que el panel APLICA a las stats del jugador, y
# restaurarlos al arrancar seria revivir un estado, no leer una preferencia.
# Ademas asustaria abrir el juego y ser invencible sin saber por que.

CFG = "/Game/DarkAngels/Debug/BP_DA_DebugConfig.BP_DA_DebugConfig_C"
RANURA = "DA_DebugPanel"

# (variable del SaveGame, variable del HUD). Se guardan TODAS; lo que cambia es
# como se restauran, y por eso estan en tres grupos.
CFG_TODO = [
    # FINISHERS y presentacion del panel
    ("Dilatacion", "FinDilatacion"), ("MatarEn", "FinMatarEn"),
    ("CamaraLado", "FinCamaraLado"), ("CamaraAlto", "FinCamaraAlto"),
    ("CamaraFrente", "FinCamaraFrente"), ("CamaraFOV", "FinCamaraFOV"),
    ("Indice", "FinIndice"), ("Escala", "DbgEscala"), ("Tab", "DbgTab"),
    # selecciones de AI, BOSS y STORY
    ("TipoSel", "DbgTipoSel"), ("CantSel", "DbgCantSel"),
    ("DistSel", "DbgDistSel"), ("BossSel", "DbgBossSel"),
    ("CheckSel", "DbgCheckSel"),
    # banderas que el tick LEE: basta con escribirlas
    ("God", "DbgGod"), ("ManaInf", "DbgManaInf"), ("LogOn", "DbgLogOn"),
    ("OneHit", "DbgOneHit"),
    # checkpoint temporal de debug
    ("TieneGuardada", "DbgTieneGuardada"), ("GuardadaLoc", "DbgGuardadaLoc"),
    ("GuardadaRot", "DbgGuardadaRot"),
    # estos se guardan pero NO se escriben al cargar: se reaplican (ver abajo)
    ("MovMult", "DbgMovMult"), ("DmgMult", "DbgDmgMult"),
    ("EnemyMult", "DbgEnemyMult"), ("Trazas", "DbgTrazas"),
    ("Colisiones", "DbgColisiones"), ("Congelada", "DbgCongelada"),
    ("Apagada", "DbgApagada"), ("Ignorar", "DbgIgnorar"),
]

# Lo que NO se restaura escribiendo la variable, porque el boton no guarda un
# numero: CAMBIA el juego. Escribir el booleano dejaria el boton encendido y el
# efecto apagado, que es peor que no guardarlo.
CFG_SOLO_GUARDAR = {"MovMult", "DmgMult", "EnemyMult", "Trazas", "Colisiones",
                    "Congelada", "Apagada", "Ignorar"}

# OJO con los defectos del CDO de BP_DA_DebugConfig. Los float nacen a 0, y al
# cargar una partida guardada ANTES de que existiera un campo, ese campo vuelve
# como 0. Con MovMult eso significa `SetMaxWalkSpeed(600 * 0)` cada tick desde
# DbgMantener: el jugador no se mueve y TODO lo demas funciona, que despista
# muchisimo. Los multiplicadores tienen que nacer a 1.0 (y Escala a 1.3).
# Si se regenera la clase de config, hay que volver a dejarlos asi.
CFG_DEFECTOS = {"MovMult": 1.0, "DmgMult": 1.0, "EnemyMult": 1.0, "Escala": 1.3}


def dsl_cfg_guardar():
    l = ['(fn DbgCfgGuardar ()',
         '  (bind sg (SaveGame|CreateSaveGameObject :SaveGameClass "%s"))' % CFG,
         '  (bind cfg (Utilities|Casting|CastToBP_DA_DebugConfig sg))']
    for destino, origen in CFG_TODO:
        # El DSL RESERVA el pin `self`: sin nombrarlo, `cfg` se va al pin del
        # valor y la pasada revienta a mitad.
        l.append('  (Class|BPDADebugConfig|Set%s :self cfg :%s'
                 ' (Variables|Default|Get%s))' % (destino, destino, origen))
    l.append('  (SaveGame|SaveGametoSlot :SaveGameObject cfg'
             ' :SlotName "%s" :UserIndex 0)' % RANURA)
    l.append('  (return))')
    return "\n".join(l)


def dsl_cfg_cargar():
    """Una sola vez, con guarda: leer disco cada frame seria absurdo."""
    l = ['(fn DbgCfgCargar ()',
         '  (if (Variables|Default|GetDbgCfgLista)',
         '    (return))',
         '  (Variables|Default|SetDbgCfgLista true)',
         '  (if (not (SaveGame|DoesSaveGameExist :SlotName "%s" :UserIndex 0))' % RANURA,
         '    (return))',
         '  (bind sg (SaveGame|LoadGamefromSlot :SlotName "%s" :UserIndex 0))' % RANURA,
         '  (bind cfg (Utilities|Casting|CastToBP_DA_DebugConfig sg))']
    # 1) los que se restauran escribiendo
    for origen, destino in CFG_TODO:
        if origen in CFG_SOLO_GUARDAR:
            continue
        l.append('  (Variables|Default|Set%s (Class|BPDADebugConfig|Get%s cfg))'
                 % (destino, origen))
    # 2) los que hay que REAPLICAR llamando a la misma accion del boton.
    #    Los multiplicadores modifican stats, asi que se les pasa el valor.
    l.append('  (CallFunction|DbgMov :Mult (Class|BPDADebugConfig|GetMovMult cfg))')
    l.append('  (CallFunction|DbgDanoJugador'
             ' :Mult (Class|BPDADebugConfig|GetDmgMult cfg))')
    l.append('  (CallFunction|DbgDanoEnemigo'
             ' :Mult (Class|BPDADebugConfig|GetEnemyMult cfg))')
    #    La AI ya recibe el valor por parametro.
    l.append('  (CallFunction|DbgIALogica'
             ' :Congelar (Class|BPDADebugConfig|GetCongelada cfg))')
    l.append('  (CallFunction|DbgIAApagar'
             ' :Apagar (Class|BPDADebugConfig|GetApagada cfg))')
    l.append('  (CallFunction|DbgIgnorarToggle'
             ' :Ignorar (Class|BPDADebugConfig|GetIgnorar cfg))')
    #    Estos dos son toggles sin parametro: solo se llaman si estaban puestos,
    #    porque arrancan apagados y la llamada los enciende.
    l.append('  (if (Class|BPDADebugConfig|GetTrazas cfg)')
    l.append('    (CallFunction|DbgTrazasToggle))')
    l.append('  (if (Class|BPDADebugConfig|GetColisiones cfg)')
    l.append('    (CallFunction|DbgColisionesToggle))')
    l.append('  (Variables|Default|SetDbgMensaje'
             ' "Config del panel recuperada del disco")')
    l.append('  (return))')
    return "\n".join(l)


def dsl_click():
    l = ['(fn DbgClick (MX MY)',
         # El sonido va en la ENTRADA, antes de resolver nada: asi lee el
         # DbgSobreBoton del ultimo dibujado y solo suena si el clic cayo en un
         # boton, no en hueco.
         '  (CallFunction|DbgSonarClick)',
         BIND_GEO,
         '  (bind n (Utilities|Array|Length (Variables|Default|GetDbgLineas)))']
    # Los dos botones de tamano, en la cabecera.
    for off, delta in [(TAM_MENOS, -ESCALA_PASO), (TAM_MAS, ESCALA_PASO)]:
        l.append('  (if %s' % caja("MX", "MY", X(off), Y(10.0),
                                   SC(30.0), SC(24.0)))
        l.append('    (CallFunction|DbgEscalar :Delta %.2f)' % delta)
        l.append('    (return))')
    for i, _nombre in enumerate(PESTANAS):
        x, y = tab_pos(i)
        l.append('  (if %s' % caja("MX", "MY", X(x), Y(y),
                                   SC(TAB_W), SC(TAB_H)))
        l.append('    (Variables|Default|SetDbgTab %d)' % i)
        l.append('    (return))')
    # Cada pestana resuelve sus propios clics, igual que dibuja los suyos: asi
    # los botones de WORLD no responden estando en PLAYER.
    l.append('  (if (== (Variables|Default|GetDbgTab) 0)')
    l.append('    (CallFunction|DbgClickWorld :MX MX :MY MY)')
    l.append('    (else')
    l.append('      (if (== (Variables|Default|GetDbgTab) 1)')
    l.append('        (CallFunction|DbgClickPlayer :MX MX :MY MY)')
    l.append('        (else')
    l.append('          (if (== (Variables|Default|GetDbgTab) 2)')
    l.append('            (CallFunction|DbgClickCombat :MX MX :MY MY)')
    l.append('            (else')
    l.append('              (if (== (Variables|Default|GetDbgTab) 3)')
    l.append('                (CallFunction|DbgClickAI :MX MX :MY MY)')
    l.append('                (else')
    l.append('                  (if (== (Variables|Default|GetDbgTab) 4)')
    l.append('                    (CallFunction|DbgClickBoss :MX MX :MY MY)')
    l.append('                    (else')
    l.append('                      (if (== (Variables|Default|GetDbgTab) 5)')
    l.append('                        (CallFunction|DbgClickStory :MX MX :MY MY)')
    l.append('                        (else')
    l.append('                          (if (== (Variables|Default|GetDbgTab) 6)')
    l.append('                            (CallFunction|DbgClickFinishers :MX MX :MY MY)')
    l.append('                            (else')
    l.append('                              (if (== (Variables|Default|GetDbgTab) 7)')
    l.append('                                (CallFunction|DbgClickWeapon :MX MX :MY MY))))))))))))))))')
    l.append('  (CallFunction|DbgCfgGuardar)')
    l.append('  (return false))')
    return "\n".join(l)



# ---------------------------------------------------------------- WEAPON
#
# SHOW WEAPON STATE — §10 del PDF. Es la unica pestaña de SOLO LECTURA: no
# tiene un boton, y por eso `DbgClickWeapon` esta vacia. Se deja igualmente
# porque el despachador llama a una por pestaña y una funcion que no existe
# no pasa el PREVUELO.
#
# LOS DATOS NO SE LEEN AQUI. El DSL no sabe construir el getter de una variable
# de OTRO blueprint (ver la nota de `unreal-mcp-limites-blueprint`), asi que la
# lectura vive en `BP_DA_PlayerCharacter.DbgEstadoArma`, que devuelve las cuatro
# cadenas ya formateadas. Aqui solo se destructura y se pinta.
#
# LO QUE FALTA, y queda escrito en el propio panel para que no se olvide: el
# ENEMIGO DE ORIGEN. El §10 lo pide, pero el pickup ocurre dentro de DCS y el
# drop no guarda quien lo solto; ponerlo pide tocar `BP_DA_WeaponDropComponent`
# y el camino de recogida, que es un asset de pago.


def dsl_tab_weapon():
    """SHOW WEAPON STATE — §10. Solo lectura: ni un boton.

    Dos trampas del DSL, las dos pagadas aqui:
      - `Utilities|IsValid` con ramas es TERMINAL: no admite NADA detras, ni
        un (return false).
      - y el cierre de cada rama va PEGADO a la ultima sentencia. Un ")" en su
        propia linea se lee como sentencia suelta y da "Unexpected )".

    Los datos NO se leen aqui: el DSL no sabe construir el getter de una
    variable de OTRO blueprint, asi que la lectura vive en
    `BP_DA_PlayerCharacter.DbgEstadoArma`, que devuelve las cuatro cadenas ya
    formateadas. Aqui solo se destructuran y se pintan."""
    l = ['(fn DbgTabWeapon ()', BIND_GEO]
    l.append(texto(X(16.0), Y(60.0), '"WEAPON STATE"', ORO, 1.15))
    l.append('  (bind j (Utilities|Casting|CastToBP_DA_PlayerCharacter'
             ' (Game|GetPlayerPawn 0)))')
    l.append('  (Utilities|IsValid j')
    l.append('    (:"Is Valid"')
    l.append('      (bind (arma tipo seg mot)'
             ' (Class|BPDAPlayerCharacter|DbgEstadoArma j))')
    filas = [(96.0, '"ARMA"', 'arma'),
             (126.0, '"TIPO"', 'tipo'),
             (156.0, '"SEGUNDOS CON ELLA"', 'seg'),
             (186.0, '"ULTIMA SALIDA"', 'mot')]
    for y, etiqueta, var in filas:
        l.append('      ' + texto(X(16.0), Y(y), etiqueta, GRIS, 0.95).strip())
        l.append('      ' + texto(X(250.0), Y(y), var, HUESO, 1.0).strip())
    l.append('      ' + texto(X(16.0), Y(216.0),
             '"ENEMIGO DE ORIGEN"', GRIS, 0.95).strip())
    l.append('      ' + texto(X(250.0), Y(216.0),
             '"-- sin registrar: el pickup vive en DCS"', GRIS, 1.0).strip())
    # La ultima del "Is Valid": su cierre va pegado.
    l.append('      ' + texto(X(16.0), Y(256.0),
             '"ULTIMA SALIDA se escribe en Swap / Discard / Seal Break."',
             GRIS, 0.85).strip() + ')')
    l.append('    (:"Is Not Valid"')
    # Y la ultima de todo cierra rama, IsValid y fn.
    l.append('      ' + texto(X(16.0), Y(96.0),
             '"No es el Malakh de DA."', GRIS, 1.0).strip() + ')))')
    return "\n".join(l)

def dsl_click_weapon():
    """Sin botones: WEAPON solo lee. Ver la nota de arriba."""
    return ('(fn DbgClickWeapon (MX MY)\n'
            '  (return false))')

def dsl_click_world():
    l = ['(fn DbgClickWorld (MX MY)',
         BIND_GEO,
         '  (bind n (Utilities|Array|Length (Variables|Default|GetDbgLineas)))']
    # La lista de destinos: un solo rectangulo y la fila se saca de la Y del
    # raton, para que anadir destinos no obligue a tocar este grafo.
    l.append('  (bind fin (+ %s (* n %s)))' % (Y(LISTA_Y0), SC(FILA)))
    l.append('  (if (and (and (>= MX %s) (< MX %s))'
             ' (and (>= MY %s) (< MY fin)))'
             % (X(8.0), X(PW - 8.0), Y(LISTA_Y0)))
    l.append('    (CallFunction|DbgTeleport :Indice'
             ' (Math|Float|Truncate (/ (- MY %s) %s)))' % (Y(LISTA_Y0), SC(FILA)))
    l.append('    (return))')
    yb = '(+ %s (* n %s))' % (Y(LISTA_Y0), SC(FILA))
    for _titulo, _y_tit, y_bot, botones in filas_botones(yb):
        for x, w, _etiqueta, accion, _enc in botones:
            l.append('  (if %s' % caja("MX", "MY", X(x), y_bot,
                                       SC(w), SC(BOTON_H)))
            l.append('    ' + accion)
            l.append('    (return))')
    l.append('  (return false))')
    return "\n".join(l)


def dsl_click_player():
    l = ['(fn DbgClickPlayer (MX MY)', BIND_GEO]
    for _titulo, _y_tit, y_bot, botones in filas_player():
        for x, w, _etiqueta, accion, _enc in botones:
            l.append('  (if %s' % caja("MX", "MY", X(x), Y(y_bot),
                                       SC(w), SC(BOTON_H)))
            l.append('    ' + accion)
            l.append('    (return))')
    l.append('  (return false))')
    return "\n".join(l)


def tiene_salida(ruta_grafo):
    """True si la funcion tiene nodo de resultado, o sea, algun valor de salida."""
    for n in bp("find_nodes", {"graph": {"refPath": ruta_grafo}, "title": ""}):
        if "FunctionResult" in n["refPath"]:
            return True
    return False


def run():
    out = {}

    # --- 1. Los dos ganchos vacios en el HUD del juego ---
    padre = {"refPath": PADRE}
    graf_padre = [g["refPath"].split(":")[-1] for g in bp("list_graphs", {"blueprint": padre})]
    for nombre in ["DbgTick", "DbgDibujar"]:
        if nombre in graf_padre and not tiene_salida(PADRE + ":" + nombre):
            # Version anterior sin valor de retorno: una funcion del padre sin
            # salida se hereda con "forma de evento" y entonces el hijo NO la
            # puede sobreescribir como funcion. Se rehace con salida.
            bp("remove_function_graph", {"blueprint": padre, "graph_name": nombre})
            graf_padre.remove(nombre)
        if nombre not in graf_padre:
            # Para add_function_param hay que usar el grafo que DEVUELVE
            # add_function_graph; la ruta construida a mano no resuelve aqui
            # (para write_graph_dsl es justo al reves).
            g = bp("add_function_graph", {"blueprint": padre, "graph_name": nombre})
            bp("add_function_param", {"graph": g, "param_name": "Hecho",
                                      "param_type": "bool", "input_param": False})
            bp("write_graph_dsl", {"graph": g,
                                   "code": "(fn %s ()\n  (return false))" % nombre})
    bp("compile_blueprint", {"blueprint": padre})
    out["ganchos_padre"] = ["DbgTick", "DbgDibujar"]

    # --- 2. El hijo: se REGENERA ENTERO en cada pasada ---
    #
    # Por que borrarlo y rehacerlo en vez de ir actualizando: `write_graph_dsl`
    # sobre una funcion que ya tiene cuerpo **no lo reemplaza, anade otra copia**
    # y deja la anterior huerfana. Tras cinco pasadas habia cinco copias de cada
    # funcion y el asset pesaba 11 MB. Y borrar las funciones una a una tampoco
    # vale: en cuanto falta una, las que la llaman no compilan.
    #
    # Se puede borrar sin miedo porque **nadie lo referencia de forma dura**: el
    # actor del nivel lo pide por ruta blanda. Eso si, este blueprint es
    # generado: lo que se toque a mano dentro se pierde en la siguiente pasada.
    grafos = [
        ("DbgPermitido", dsl_permitido, [("Permitido", "bool", False)]),
        ("DbgEscalar", dsl_escalar, [("Delta", "float", True)]),
        # Las cuatro del resalte y el sonido van AQUI, ANTES de sus
        # llamadores: DbgBoton llama a DbgHoverBoton, DbgDibujar a
        # DbgHoverTabs, DbgClick a DbgSonarClick y DbgToggle a
        # DbgSonarPanel. Estaban escritas mas arriba pero NUNCA
        # registradas, asi que la pasada moria en DbgClick con
        # "CallFunction|DbgSonarClick does not exist".
        ("DbgHoverBoton", dsl_hover_boton, [("X", "float", True),
                                            ("Y", "float", True),
                                            ("W", "float", True)]),
        ("DbgHoverTabs", dsl_hover_tabs, []),
        ("DbgSonarClick", dsl_sonar_click, []),
        ("DbgSonarPanel", dsl_sonar_panel, []),
        ("DbgBoton", dsl_boton, [("X", "float", True), ("Y", "float", True),
                                 ("W", "float", True), ("Etiqueta", "string", True),
                                 ("Encendido", "bool", True)]),
        ("DbgCampo", dsl_campo, [("Indice", "int", True), ("Campo", "int", True),
                                 ("Valor", "string", False)]),
        ("DbgOcultarJuego", dsl_ocultar_juego, [("Ocultar", "bool", True)]),
        ("DbgToggle", dsl_toggle, []),
        ("DbgTeleport", dsl_teleport, [("Indice", "int", True)]),
        ("DbgGuardarPos", dsl_guardar, []),
        ("DbgIrAGuardada", dsl_ir_guardada, []),
        ("DbgCopiarTransform", dsl_copiar, []),
        ("DbgVelocidad", dsl_velocidad, [("Valor", "float", True)]),
        ("DbgReiniciarNivel", dsl_reiniciar, []),
        ("DbgRespawnInicio", dsl_respawn, []),
        # --- PLAYER ---
        ("DbgNadaAun", dsl_nada_aun, []),
        ("DbgVida", dsl_vida, [("Fraccion", "float", True)]),
        ("DbgMatar", dsl_matar, []),
        ("DbgGodToggle", dsl_god, []),
        ("DbgManaToggle", dsl_mana_inf, []),
        ("DbgMov", dsl_mov, [("Mult", "float", True)]),
        ("DbgMantener", dsl_mantener, []),
        ("DbgResetPlayer", dsl_reset_player, []),
        # --- AI ---
        ("DbgCampoTipo", dsl_campo_tipo, [("Indice", "int", True), ("Campo", "int", True), ("Valor", "string", False)]),
        ("DbgCampoEnc", dsl_campo_enc, [("Indice", "int", True), ("Campo", "int", True), ("Valor", "string", False)]),
        ("DbgCargarEnem", dsl_cargar_enem, []),
        ("DbgSpawnUno", dsl_spawn_uno, [("RutaClase", "string", True),
                                        ("Lado", "int", True)]),
        ("DbgSpawn", dsl_spawn, []),
        ("DbgEncuentro", dsl_encuentro, [("Indice", "int", True)]),
        ("DbgLimpiar", dsl_limpiar, []),
        ("DbgIALogica", dsl_ia_logica, [("Congelar", "bool", True)]),
        ("DbgIAApagar", dsl_ia_apagar, [("Apagar", "bool", True)]),
        ("DbgIgnorarToggle", dsl_ignorar, [("Ignorar", "bool", True)]),
        ("DbgOlvidarTick", dsl_olvidar_tick, []),
        ("DbgResetArena", dsl_reset_arena, []),
        # --- COMBAT (el orden importa: primero las que llaman las demas) ---
        ("DbgDanoJugador", dsl_dano_jugador, [("Mult", "float", True)]),
        ("DbgDanoEnemigo", dsl_dano_enemigo, [("Mult", "float", True)]),
        ("DbgOneHitToggle", dsl_one_hit, []),
        ("DbgLogToggle", dsl_log_toggle, []),
        ("DbgLogLinea", dsl_log_linea, [("Texto", "string", True)]),
        ("DbgLogTick", dsl_log_tick, []),
        ("DbgTrazasToggle", dsl_trazas, []),
        ("DbgColisionesToggle", dsl_colisiones, []),
        ("DbgArenaSellar", dsl_arena_sellar, []),
        ("DbgArenaAbrir", dsl_arena_abrir, []),
        ("DbgArenaReiniciar", dsl_arena_reiniciar, []),
        ("DbgDarArmaLanza", lambda c='Lanza', r='/Game/DarkAngels/Weapons/Items/DA_DA_Lanza.DA_DA_Lanza', e='Lanza del Alba': dsl_dar_arma(c, r, e), []),
        ("DbgDarArmaTrompeta", lambda c='Trompeta', r='/Game/DarkAngels/Weapons/Items/DA_DA_Trompeta.DA_DA_Trompeta', e='Trompeta del Juicio': dsl_dar_arma(c, r, e), []),
        ("DbgDarArmaHacha", lambda c='Hacha', r='/Game/DarkAngels/Weapons/Items/DA_DA_HachaMano.DA_DA_HachaMano', e='Hacha': dsl_dar_arma(c, r, e), []),
        ("DbgDarArmaEspadon", lambda c='Espadon', r='/Game/DynamicCombatSystem/DCS/Blueprints/Items/ObjectItems/Instances/DA_GreatAxe.DA_GreatAxe', e='Espadon': dsl_dar_arma(c, r, e), []),
        ("DbgDarArmaArco", lambda c='Arco', r='/Game/DynamicCombatSystem/ArcheryModule/Blueprints/Items/ObjectItems/Instances/DA_ElvenBow.DA_ElvenBow', e='Arco del Firmamento': dsl_dar_arma(c, r, e), []),
        ("DbgDarArmaEscudo", lambda c='Escudo', r='/Game/DynamicCombatSystem/DCS/Blueprints/Items/ObjectItems/Instances/DA_WoodenShield.DA_WoodenShield', e='Escudo Celestial': dsl_dar_arma(c, r, e), []),
        ("DbgCorrupcionCel", lambda c='Cel', v='0.0', e='Celestial': dsl_corrupcion(c, v, e), []),
        ("DbgCorrupcionTai", lambda c='Tai', v='0.33', e='Tainted': dsl_corrupcion(c, v, e), []),
        ("DbgCorrupcionCor", lambda c='Cor', v='0.66', e='Corrupta': dsl_corrupcion(c, v, e), []),
        ("DbgCorrupcionFra", lambda c='Fra', v='1.0', e='Fractured': dsl_corrupcion(c, v, e), []),
        ("DbgForzarDescarte", dsl_forzar_descarte, []),
        ("DbgMunicionToggle", dsl_municion_toggle, []),
        ("DbgResetCombat", dsl_reset_combat, []),
        # --- BOSS ---
        ("DbgCampoBoss", dsl_campo_boss, [("Indice", "int", True), ("Campo", "int", True), ("Valor", "string", False)]),
        ("DbgCargarBoss", dsl_cargar_boss, []),
        ("DbgBossVida", dsl_boss_vida, [("Fraccion", "float", True)]),
        # --- STORY ---
        ("DbgObjetivo", dsl_objetivo, [("Delta", "int", True)]),
        ("DbgGuiaToggle", dsl_guia, []),
        ("DbgCheckpoint", dsl_checkpoint, [("Delta", "int", True), ("Ir", "bool", True)]),
        ("DbgResetStory", dsl_reset_story, []),
        ("DbgMarcasBorrar", dsl_marcas_borrar, []),
        ("DbgMarcasReiniciar", dsl_marcas_reiniciar, []),
        # --- FINISHERS ---
        ("DbgFinDilFijar", dsl_fin_fijar, [("Valor", "float", True)]),
        ("DbgFinDilatacion", lambda n='Dilatacion': dsl_fin_delta(n), [("Delta", "float", True)]),
        ("DbgFinHitStopEn", lambda n='HitStopEn': dsl_fin_delta(n), [("Delta", "float", True)]),
        ("DbgFinMatarEn", lambda n='MatarEn': dsl_fin_delta(n), [("Delta", "float", True)]),
        ("DbgFinCamaraLado", lambda n='CamaraLado': dsl_fin_delta(n), [("Delta", "float", True)]),
        ("DbgFinCamaraAlto", lambda n='CamaraAlto': dsl_fin_delta(n), [("Delta", "float", True)]),
        ("DbgFinCamaraFrente", lambda n='CamaraFrente': dsl_fin_delta(n), [("Delta", "float", True)]),
        ("DbgFinCamaraFOV", lambda n='CamaraFOV': dsl_fin_delta(n), [("Delta", "float", True)]),
        ("DbgFinIndice", dsl_fin_indice, [("Delta", "int", True)]),
        ("DbgFinReset", dsl_fin_reset, []),
        # Estas tres van aqui y no arriba: DbgCfgCargar llama a las
        # acciones de PLAYER, AI y COMBAT, y el generador exige que
        # lo llamado exista ANTES que quien llama.
        ("DbgCfgGuardar", dsl_cfg_guardar, []),
        ("DbgCfgCargar", dsl_cfg_cargar, []),
        ("DbgCargar", dsl_cargar, []),
        ("DbgTabPendiente", dsl_pendiente, []),
        ("DbgTabPlayer", dsl_tab_player, []),
        ("DbgTabCombat", dsl_tab_combat, []),
        ("DbgTabAI", dsl_tab_ai, []),
        ("DbgTabBoss", dsl_tab_boss, []),
        ("DbgTabStory", dsl_tab_story, []),
        ("DbgTabFinishers", dsl_tab_finishers, []),
        ("DbgTabWeapon", dsl_tab_weapon, []),
        ("DbgTabWorld", dsl_tab_world, []),
        ("DbgClickWorld", dsl_click_world, [("MX", "float", True),
                                            ("MY", "float", True)]),
        ("DbgClickPlayer", dsl_click_player, [("MX", "float", True),
                                              ("MY", "float", True)]),
        ("DbgClickCombat", dsl_click_combat, [("MX", "float", True),
                                              ("MY", "float", True)]),
        ("DbgClickAI", dsl_click_ai, [("MX", "float", True), ("MY", "float", True)]),
        ("DbgClickBoss", dsl_click_boss, [("MX", "float", True), ("MY", "float", True)]),
        ("DbgClickStory", dsl_click_story, [("MX", "float", True), ("MY", "float", True)]),
        ("DbgClickFinishers", dsl_click_finishers, [("MX", "float", True), ("MY", "float", True)]),
        ("DbgClickWeapon", dsl_click_weapon, [("MX", "float", True), ("MY", "float", True)]),
        ("DbgClick", dsl_click, [("MX", "float", True), ("MY", "float", True)]),
        # Los dos ganchos, ya como sobreescritura de funcion (el padre las
        # declara con valor de retorno justo para que esto sea posible).
        ("DbgTick", dsl_tick, []),
        ("DbgDibujar", dsl_dibujar, []),
    ]

    # ------------------------------------------------------------------
    # PREVUELO: ninguna funcion puede llamar a otra que no este en la
    # lista. Se comprueba ANTES de borrar nada, porque la regeneracion es
    # todo o nada: si revienta a mitad te quedas sin panel y hay que sacarlo
    # de git. Paso de verdad el 2026-08-24: las cuatro funciones del resalte
    # y el sonido estaban escritas pero sin registrar, y la pasada murio en
    # DbgClick con 'CallFunction|DbgSonarClick does not exist'.
    # PREVUELO 0: los PARENTESIS de cada funcion tienen que cuadrar.
    #
    # Anadido el 2026-08-26 despues de perder el panel TRES veces seguidas. El
    # error del escritor es "Unexpected )" y NO dice en que funcion, asi que se
    # busca a ciegas mientras el asset ya esta borrado y hay que sacarlo de git
    # en cada intento. El fallo real estaba en `dsl_click`: al meter una pestana
    # nueva en el despacho anidado sobraba un cierre, y la pestana nueva —que
    # era lo sospechoso— estaba bien.
    #
    # Contar parentesis no valida la gramatica, pero pilla el 90% de los
    # destrozos al tocar los despachos, que es donde de verdad se rompe.
    descuadradas = {}
    for nombre, hacer, _p in grafos:
        cuerpo = hacer()
        abre, cierra = cuerpo.count("("), cuerpo.count(")")
        if abre != cierra:
            descuadradas[nombre] = {"abre": abre, "cierra": cierra}
    if descuadradas:
        return {'ABORTADO': 'parentesis descuadrados; no se ha tocado el asset',
                'funciones': descuadradas}

    registradas = {n for n, _, _ in grafos}
    faltan = {}
    for nombre, hacer, _p in grafos:
        for trozo in hacer().split('CallFunction|')[1:]:
            llamada = ''
            for ch in trozo:
                if not (ch.isalnum() or ch == '_'):
                    break
                llamada += ch
            if llamada and llamada not in registradas:
                faltan.setdefault(llamada, []).append(nombre)
    if faltan:
        return {'ABORTADO': 'hay llamadas a funciones sin registrar',
                'faltan': {k: sorted(set(v)) for k, v in faltan.items()}}

    hijo = {"refPath": HIJO}
    out["regenerado"] = False
    if ast("exists", {"path": HIJO.split(".")[0]}):
        ast("delete", {"path": HIJO.split(".")[0]})
        out["regenerado"] = True
    bp("create", {"folder_path": CARPETA, "asset_name": HIJO.split("/")[-1].split(".")[0],
                  "asset_type": {"refPath": PADRE + "_C"}})

    for nombre, tipo, cont in VARIABLES:
        args = {"blueprint": hijo, "name": nombre, "type_name": tipo}
        if cont:
            args["container_type"] = cont
        bp("add_variable", args)
    # La referencia al Data Asset de destinos, con su valor por defecto puesto:
    # asi el HUD no tiene ninguna ruta escrita dentro del grafo.
    bp("add_object_variable", {"blueprint": hijo, "name": "DbgDatos",
                               "object_class": {"refPath": CARPETA +
                                                "/BP_DA_DebugDestinos."
                                                "BP_DA_DebugDestinos_C"}})
    # Los widgets del juego que se escondieron al abrir el panel, para poder
    # devolverlos exactamente como estaban.
    bp("add_object_variable", {"blueprint": hijo, "name": "DbgOcultadas",
                               "object_class": {"refPath": "/Script/UMG.UserWidget"},
                               "container_type": "ARRAY"})
    # El registro de enemigos generados por la herramienta. CLEAR borra ESTO y
    # nada mas: por construccion no puede tocar un enemigo del nivel.
    bp("add_object_variable", {"blueprint": hijo, "name": "DbgSpawned",
                               "object_class": {"refPath": "/Script/Engine.Actor"},
                               "container_type": "ARRAY"})
    bp("add_object_variable", {"blueprint": hijo, "name": "DbgDatosEnem",
                               "object_class": {"refPath": CARPETA +
                                                "/BP_DA_DebugEnemigos."
                                                "BP_DA_DebugEnemigos_C"}})
    bp("compile_blueprint", {"blueprint": hijo})
    cdo = bp("get_default_object", {"blueprint": hijo})
    obj("set_properties", {"instance": cdo,
                           "values": json.dumps({"DbgDatos": DATOS,
                                                 "DbgHabilitado": True,
                                                 "DbgEscala": ESCALA_DEF,
                                                 "DbgMovMult": 1.0,
                                                 "DbgDmgMult": 1.0,
                                                 "DbgEnemyMult": 1.0,
                                                 "DbgDatosEnem": DATOS_ENEM,
                                                 "DbgCantSel": 1,
                                                 "DbgDistSel": 500.0})})
    out["datos_enlazados"] = json.loads(obj("get_properties",
                                            {"instance": cdo,
                                             "properties": ["DbgDatos"]}))
    out["variables"] = bp("list_variables", {"blueprint": hijo})

    # --- 3. Los grafos, en orden de dependencia: una funcion no se puede
    # --- escribir antes que las que llama.
    # El blueprint acaba de nacer, asi que todas las funciones son nuevas.
    for nombre, hacer, params in grafos:
        # Un grafo recien creado NO responde a la ruta construida a mano dentro
        # de la misma pasada: hay que usar el objeto que devuelve la creacion.
        g = bp("add_function_graph", {"blueprint": hijo, "graph_name": nombre})
        for pn, pt, es_entrada in params:
            bp("add_function_param", {"graph": g, "param_name": pn,
                                      "param_type": pt, "input_param": es_entrada})
        bp("write_graph_dsl", {"graph": g, "code": hacer()})
    bp("compile_blueprint", {"blueprint": hijo})
    out["grafos"] = [g["refPath"].split(":")[-1] for g in bp("list_graphs", {"blueprint": hijo})]

    # --- 4. Enganchar los dos ganchos a los eventos del padre ---
    out["enganche"] = enganchar()

    # Lista vacia = guarda todo lo sucio. Pasar las rutas una a una fallo con
    # "Asset does not exist" justo despues de recompilar.
    ast("save_assets", {"asset_paths": []})
    return out


def enganchar():
    """Mete las llamadas a DbgTick/DbgDibujar a la CABEZA de los dos eventos.

    A la cabeza y no al final porque encontrar el final de una cadena que acaba
    en ramas es fragil. El panel va pegado al borde IZQUIERDO, y lo que dibuja
    el HUD del juego (objetivo arriba-centro, banner abajo-centro, salto de zona
    a la derecha) no lo pisa, asi que el orden de dibujado da igual.
    """
    eg = {"refPath": PADRE + ":EventGraph"}
    res = {}
    # Los nodos NO se identifican por su refPath (son K2Node_Event_2 y demas):
    # hay que mirarles el type_id.
    def tipo(n):
        return bp("get_node_infos", {"nodes": [n]})[0]["type_id"]

    # OJO CON EL type_id DE UNA LLAMADA A FUNCION PROPIA: es `|DbgTick`, con la
    # CATEGORIA VACIA, no `CallFunction|DbgTick`. Por creer lo segundo, la
    # limpieza no reconocia nada y cada pasada del script **encadenaba un par de
    # llamadas mas** sin borrar las anteriores: se juntaron 16.
    #
    # Y no es cosmetico. Con 16 llamadas, `DbgTick` corre 16 veces por frame y
    # `WasInputKeyJustPressed` devuelve true en todas: una sola pulsacion abria y
    # cerraba el panel 16 veces. Numero par, no se veia nada.
    def es_dbg(n):
        t = tipo(n)
        return t.endswith("|DbgTick") or t.endswith("|DbgDibujar")

    nuevos = []

    for marca, funcion, y in [("AddEvent|EventReceiveDrawHUD", "DbgDibujar", 2000),
                              ("AddEvent|EventTick", "DbgTick", 2400)]:
        ev = None
        for n in bp("find_nodes", {"graph": eg, "title": "", "entry_points_only": True}):
            if tipo(n) == marca:
                ev = n
                break
        if ev is None:
            res[marca] = "evento no encontrado"
            continue

        # Se recorre la cadena desde el evento saltando los nodos Dbg que haya
        # acumulados, para quedarse con el primer nodo DEL JUEGO. Ese es el que
        # hay que volver a enganchar; borrar los Dbg sin esto partiria la cadena
        # y el HUD del juego dejaria de dibujar.
        #
        # OJO: en un nodo de EVENTO el pin de ejecucion es el indice 1 (el 0 es
        # el OutputDelegate). En una llamada a funcion, el 0.
        def sigue_de(nodo, indice):
            for p in bp("get_node_infos", {"nodes": [nodo]})[0]["output_pins"]:
                if p["pin_id"]["index_id"] == indice and p["connected_pins"]:
                    return p["connected_pins"][0]
            return None

        seguia = sigue_de(ev, 1)
        viejos = []
        while seguia is not None:
            nodo = {"refPath": seguia["node"]["refPath"]}
            if not es_dbg(nodo):
                break
            viejos.append(nodo)
            seguia = sigue_de(nodo, 0)
        for v in viejos:
            bp("delete_node", {"node": v})
        res[marca + "_duplicados_borrados"] = len(viejos)

        llamada = bp("create_node", {"graph": eg, "type_id": "CallFunction|" + funcion,
                                     "pos": {"x": 400, "y": y}})
        def pin(nodo, direccion, indice):
            return {"direction": direccion, "index_id": indice,
                    "node": {"refPath": nodo["refPath"]}}
        bp("connect_pins", {"output_pin": pin(ev, "EGPD_Output", 1),
                            "input_pin": pin(llamada, "EGPD_Input", 0)})
        if seguia is not None:
            bp("connect_pins", {"output_pin": pin(llamada, "EGPD_Output", 0),
                                "input_pin": seguia})
        res[marca] = "enganchado" + ("" if seguia is None else " y reencadenado")
        nuevos.append(llamada["refPath"])

    # Barrido final: los duplicados que quedaron sueltos fuera de la cadena en
    # pasadas anteriores. No ejecutan nada, pero ensucian el grafo y confunden
    # a la siguiente limpieza.
    sueltos = 0
    for n in bp("find_nodes", {"graph": eg, "title": ""}):
        if n["refPath"] in nuevos or not es_dbg(n):
            continue
        bp("delete_node", {"node": n})
        sueltos += 1
    res["huerfanos_barridos"] = sueltos

    bp("compile_blueprint", {"blueprint": {"refPath": PADRE}})
    return res
