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
AUTO_ABRIR = True

TECLAS = ["Period", "Decimal"]
PESTANAS = ["WORLD", "PLAYER", "COMBAT", "AI", "BOSS", "STORY"]

# --- Geometria del panel. De aqui salen A LA VEZ el dibujado y los clics, para
# --- que no puedan desincronizarse.
PX, PY, PW = 40.0, 60.0, 580.0
TAB_W, TAB_H, TAB_SEP = 186.0, 28.0, 191.0
TAB_Y0 = PY + 46.0
FILA = 26.0          # alto de fila de la lista de destinos
BOTON_H = 26.0
LISTA_Y0 = PY + 262.0

VARIABLES = [
    ("DbgVisible", "bool", None), ("DbgTab", "int", None),
    ("DbgFps", "float", None), ("DbgLineas", "string", "ARRAY"),
    ("DbgGuardadaLoc", "Vector", None), ("DbgGuardadaRot", "Rotator", None),
    ("DbgTieneGuardada", "bool", None), ("DbgInicioLoc", "Vector", None),
    ("DbgInicioRot", "Rotator", None), ("DbgTieneInicio", "bool", None),
    ("DbgMensaje", "string", None), ("DbgHabilitado", "bool", None),
]

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


def texto(x, y, cadena, color=HUESO, escala=1.0):
    """DrawText posicional: self, Text, Color, X, Y, Font=0, Scale.

    El Font va a 0 a proposito: con una fuente distance-field el canvas no
    dibuja nada (ya paso), y con 0 cae a la del motor, que si sale."""
    return '  (HUD|DrawText self %s %s %s %s 0 %.2f)' % (cadena, color, x, y, escala)


def rect(x, y, w, h, color):
    return '  (HUD|DrawRect self %s %s %s %s %s)' % (color, x, y, w, h)


def tab_pos(i):
    return (PX + 6.0 + (i % 3) * TAB_SEP, TAB_Y0 + (i // 3) * 32.0)


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


def dsl_boton():
    return ('(fn DbgBoton (X Y W Etiqueta Encendido)\n'
            '  (if Encendido\n'
            + rect("X", "Y", "W", "%.1f" % BOTON_H, BOTON_ON) + '\n'
            '    (else\n'
            + rect("X", "Y", "W", "%.1f" % BOTON_H, BOTON) + '))\n'
            + texto("(+ X 10.0)", "(+ Y 4.0)", "Etiqueta") + '\n'
            '  (return))')


def dsl_cargar():
    # Los destinos se leen del Data Asset una sola vez y se cachean.
    return ('(fn DbgCargar ()\n'
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
    return ('(fn DbgOcultarJuego (Ocultar)\n'
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
    return ('(fn DbgToggle ()\n'
            '  (if (not (CallFunction|DbgPermitido))\n'
            '    (return))\n'
            '  (bind v (not (Variables|Default|GetDbgVisible)))\n'
            '  (Variables|Default|SetDbgVisible v)\n'
            '  (CallFunction|DbgOcultarJuego :Ocultar v)\n'
            '  (bind pc (Game|GetPlayerController 0))\n'
            '  (Class|PlayerController|SetShowMouseCursor :self pc :bShowMouseCursor v)\n'
            '  (bind pawn (Game|GetPlayerPawn 0))\n'
            '  (Utilities|IsValid pawn\n'
            '    (:"Is Valid"\n'
            '      (if v\n'
            '        (Input|DisableInput :self pawn :PlayerController pc)\n'
            '        (else\n'
            '          (Input|EnableInput :self pawn :PlayerController pc))))\n'
            '    (:"Is Not Valid")))')


def dsl_tick():
    # Sobreescribe la funcion vacia del padre. Se llama desde EventTick.
    l = ['(fn DbgTick ()']
    if AUTO_ABRIR:
        # Sonda: donde se corta la cadena. Se imprime el permiso, el delta y si
        # el pawn es valido, que son las tres puertas antes del auto-abrir.
        l.append('  (Development|PrintString :InString'
                 ' (Utilities|String|Append "DBG permitido="'
                 ' (Utilities|String|SelectString "SI" "NO"'
                 ' (CallFunction|DbgPermitido)))'
                 ' :bPrintToScreen false :bPrintToLog true :Duration 1.0)')
        l.append('  (Development|PrintString :InString'
                 ' (Utilities|String|Append "DBG dt="'
                 ' (Utilities|String|ToString(Float)'
                 ' (Utilities|Time|GetWorldDeltaSeconds)))'
                 ' :bPrintToScreen false :bPrintToLog true :Duration 1.0)')
        l.append('  (Utilities|IsValid (Game|GetPlayerPawn 0)')
        l.append('    (:"Is Valid"')
        l.append('      (Development|PrintString :InString "DBG pawn OK"'
                 ' :bPrintToScreen false :bPrintToLog true :Duration 1.0))')
        l.append('    (:"Is Not Valid"')
        l.append('      (Development|PrintString :InString "DBG pawn NULO"'
                 ' :bPrintToScreen false :bPrintToLog true :Duration 1.0)))')
    l += ['  (if (not (CallFunction|DbgPermitido))',
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
         + ('\n        (CallFunction|DbgToggle)' if AUTO_ABRIR else '') + ')',
         '      (:"Is Not Valid")))']
    cond = " ".join('(Game|Player|WasInputKeyJustPressed :self pc :Key "%s")' % k
                    for k in TECLAS)
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
         '  (bind n (Utilities|Array|Length (Variables|Default|GetDbgLineas)))',
         '  (bind alto (+ 518.0 (* n %.1f)))' % FILA,
         rect("%.1f" % PX, "%.1f" % PY, "%.1f" % PW, "alto", FONDO),
         rect("%.1f" % PX, "%.1f" % PY, "%.1f" % PW, "3.0", ORO),
         texto("%.1f" % (PX + 14.0), "%.1f" % (PY + 12.0),
               '"DARK ANGELS - DEV TOOLS"', ORO, 1.35),
         texto("%.1f" % (PX + 400.0), "%.1f" % (PY + 16.0),
               '"[ . ] cerrar"', GRIS, 0.9)]
    # Pestanas: WORLD activa, el resto marcadas como pendientes.
    for i, nombre in enumerate(PESTANAS):
        x, y = tab_pos(i)
        l.append('  (bind act%d (== (Variables|Default|GetDbgTab) %d))' % (i, i))
        l.append('  (if act%d' % i)
        l.append(rect("%.1f" % x, "%.1f" % y, "%.1f" % TAB_W, "%.1f" % TAB_H, BOTON_ON))
        l.append('    (else')
        # Dos cierres: uno para el (else y otro para el (if.
        l.append(rect("%.1f" % x, "%.1f" % y, "%.1f" % TAB_W, "%.1f" % TAB_H, BOTON) + '))')
        etiqueta = '"%s"' % nombre if i == 0 else '"%s  --"' % nombre
        l.append(texto("%.1f" % (x + 12.0), "%.1f" % (y + 4.0), etiqueta,
                       ORO if i == 0 else GRIS, 1.0))
    l.append('  (if (== (Variables|Default|GetDbgTab) 0)')
    l.append('    (CallFunction|DbgTabWorld)')
    l.append('    (else')
    l.append('      (CallFunction|DbgTabPendiente)))')
    l.append('  (return false))')
    return "\n".join(l)


def dsl_pendiente():
    y = PY + 200.0
    return ('(fn DbgTabPendiente ()\n'
            + texto("%.1f" % (PX + 20.0), "%.1f" % y,
                    '"Esta seccion todavia no esta construida."', GRIS, 1.1) + '\n'
            + texto("%.1f" % (PX + 20.0), "%.1f" % (y + 26.0),
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


# ------------------------------------------------- la pestana WORLD y clics
#
# La geometria de los botones se calcula UNA vez aqui y de ella salen tanto el
# dibujado como el enrutado de clics: no pueden quedar descuadrados.
#
# `yb` es la Y donde acaba la lista de destinos, que depende de cuantos haya:
# en DSL es una expresion, no un numero.

def filas_botones(yb):
    """[(y_expr, [(x, w, etiqueta, accion_dsl, encendido_expr)]), ...]"""
    x0 = PX + 8.0
    return [
        ("PLAYER POSITION", "(+ %s 8.0)" % yb, "(+ %s 30.0)" % yb, [
            (x0, 182.0, "SAVE POSITION", "(CallFunction|DbgGuardarPos)", "false"),
            (x0 + 190.0, 182.0, "GO TO SAVED", "(CallFunction|DbgIrAGuardada)",
             "(Variables|Default|GetDbgTieneGuardada)"),
            (x0 + 380.0, 182.0, "COPY TRANSFORM", "(CallFunction|DbgCopiarTransform)",
             "false"),
        ]),
        ("GAME SPEED", "(+ %s 70.0)" % yb, "(+ %s 92.0)" % yb, [
            (x0 + i * 112.0, 108.0, e, "(CallFunction|DbgVelocidad :Valor %s)" % v, "false")
            for i, (e, v) in enumerate([("0.1x", "0.1"), ("0.25x", "0.25"),
                                        ("0.5x", "0.5"), ("1x", "1.0"),
                                        ("2x", "2.0")])
        ]),
        ("LEVEL", "(+ %s 132.0)" % yb, "(+ %s 154.0)" % yb, [
            (x0, 278.0, "RESTART LEVEL", "(CallFunction|DbgReiniciarNivel)", "false"),
            (x0 + 286.0, 278.0, "RESPAWN AT START", "(CallFunction|DbgRespawnInicio)",
             "false"),
        ]),
        ("", None, "(+ %s 200.0)" % yb, [
            (x0, 564.0, "CLOSE DEBUG HUD", "(CallFunction|DbgToggle)", "false"),
        ]),
    ]


def dsl_tab_world():
    l = ['(fn DbgTabWorld ()',
         '  (bind n (Utilities|Array|Length (Variables|Default|GetDbgLineas)))',
         '  (bind pawn (Game|GetPlayerPawn 0))',
         '  (bind loc (Transformation|GetActorLocation :self pawn))',
         '  (bind rot (Pawn|GetControlRotation :self (Game|GetPlayerController 0)))',
         '  (bind nivel (Game|GetCurrentLevelName true))']
    y = PY + 130.0
    l.append(texto("%.1f" % (PX + 16.0), "%.1f" % y, '"INFORMACION"', ORO, 1.05))
    datos = [
        ('(Utilities|String|Append "Level:  " nivel)', 24.0),
        ('(Utilities|String|Append "Loc:  " (Utilities|String|ToString(Vector) loc))', 46.0),
        ('(Utilities|String|Append "Rot camara:  "'
         ' (Utilities|String|ToString(Rotator) rot))', 68.0),
        ('(Utilities|String|Append'
         ' (Utilities|String|Append "FPS:  "'
         ' (Utilities|String|ToString(Float) (Variables|Default|GetDbgFps)))'
         ' (Utilities|String|Append "     Time Dilation:  "'
         ' (Utilities|String|ToString(Float) (Utilities|Time|GetGlobalTimeDilation))))', 90.0),
    ]
    for expr, dy in datos:
        l.append(texto("%.1f" % (PX + 16.0), "%.1f" % (y + dy), expr, HUESO, 0.95))

    l.append(texto("%.1f" % (PX + 16.0), "%.1f" % (LISTA_Y0 - 26.0),
                   '"TELEPORT"', ORO, 1.05))
    l.append('  (for i (range n)')
    l.append('    (bind fy (+ %.1f (* i %.1f)))' % (LISTA_Y0, FILA))
    l.append('    ' + rect("%.1f" % (PX + 8.0), "fy", "%.1f" % (PW - 16.0),
                           "%.1f" % (FILA - 3.0), BOTON).strip())
    l.append('    ' + texto("%.1f" % (PX + 18.0), "(+ fy 3.0)",
                            '(CallFunction|DbgCampo :Indice i :Campo 0)', HUESO, 1.0).strip())
    l.append('    ' + texto("%.1f" % (PX + 210.0), "(+ fy 4.0)",
                            '(CallFunction|DbgCampo :Indice i :Campo 1)', GRIS, 0.85).strip())
    l.append('    ' + texto("%.1f" % (PX + 320.0), "(+ fy 4.0)",
                            '(CallFunction|DbgCampo :Indice i :Campo 4)', GRIS, 0.8).strip())
    l.append('    )')

    yb = '(+ %.1f (* n %.1f))' % (LISTA_Y0, FILA)
    for titulo, y_tit, y_bot, botones in filas_botones(yb):
        if y_tit:
            l.append(texto("%.1f" % (PX + 16.0), y_tit, '"%s"' % titulo, ORO, 1.05))
        for x, w, etiqueta, _accion, encendido in botones:
            l.append('  (CallFunction|DbgBoton :X %.1f :Y %s :W %.1f'
                     ' :Etiqueta "%s" :Encendido %s)'
                     % (x, y_bot, w, etiqueta, encendido))
    l.append(texto("%.1f" % (PX + 16.0), "(+ %s 236.0)" % yb,
                   '(Variables|Default|GetDbgMensaje)', ORO, 0.95))
    l.append('  (return false))')
    return "\n".join(l)


def caja(mx, my, x, y, w, h):
    return ('(and (and (>= %s %s) (< %s (+ %s %s))) (and (>= %s %s) (< %s (+ %s %s))))'
            % (mx, x, mx, x, w, my, y, my, y, h))


def dsl_click():
    l = ['(fn DbgClick (MX MY)',
         '  (bind n (Utilities|Array|Length (Variables|Default|GetDbgLineas)))']
    for i, _nombre in enumerate(PESTANAS):
        x, y = tab_pos(i)
        l.append('  (if %s' % caja("MX", "MY", "%.1f" % x, "%.1f" % y,
                                   "%.1f" % TAB_W, "%.1f" % TAB_H))
        l.append('    (Variables|Default|SetDbgTab %d)' % i)
        l.append('    (return))')
    # La lista de destinos: un solo rectangulo y la fila se saca de la Y del
    # raton, para que anadir destinos no obligue a tocar este grafo.
    l.append('  (bind fin (+ %.1f (* n %.1f)))' % (LISTA_Y0, FILA))
    l.append('  (if (and (and (>= MX %.1f) (< MX %.1f))'
             ' (and (>= MY %.1f) (< MY fin)))'
             % (PX + 8.0, PX + PW - 8.0, LISTA_Y0))
    l.append('    (CallFunction|DbgTeleport :Indice'
             ' (Math|Float|Truncate (/ (- MY %.1f) %.1f)))' % (LISTA_Y0, FILA))
    l.append('    (return))')
    yb = '(+ %.1f (* n %.1f))' % (LISTA_Y0, FILA)
    for _titulo, _y_tit, y_bot, botones in filas_botones(yb):
        for x, w, _etiqueta, accion, _enc in botones:
            l.append('  (if %s' % caja("MX", "MY", "%.1f" % x, y_bot,
                                       "%.1f" % w, "%.1f" % BOTON_H))
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
    bp("compile_blueprint", {"blueprint": hijo})
    cdo = bp("get_default_object", {"blueprint": hijo})
    obj("set_properties", {"instance": cdo,
                           "values": json.dumps({"DbgDatos": DATOS,
                                                 "DbgHabilitado": True})})
    out["datos_enlazados"] = json.loads(obj("get_properties",
                                            {"instance": cdo,
                                             "properties": ["DbgDatos"]}))
    out["variables"] = bp("list_variables", {"blueprint": hijo})

    # --- 3. Los grafos, en orden de dependencia: una funcion no se puede
    # --- escribir antes que las que llama.
    grafos = [
        ("DbgPermitido", dsl_permitido, [("Permitido", "bool", False)]),
        ("DbgBoton", dsl_boton, [("X", "float", True), ("Y", "float", True),
                                 ("W", "float", True), ("Etiqueta", "string", True),
                                 ("Encendido", "bool", True)]),
        ("DbgCargar", dsl_cargar, []),
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
        ("DbgTabPendiente", dsl_pendiente, []),
        ("DbgTabWorld", dsl_tab_world, []),
        ("DbgClick", dsl_click, [("MX", "float", True), ("MY", "float", True)]),
        # Los dos ganchos, ya como sobreescritura de funcion (el padre las
        # declara con valor de retorno justo para que esto sea posible).
        ("DbgTick", dsl_tick, []),
        ("DbgDibujar", dsl_dibujar, []),
    ]
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

    for marca, funcion, y in [("AddEvent|EventReceiveDrawHUD", "DbgDibujar", 2000),
                              ("AddEvent|EventTick", "DbgTick", 2400)]:
        # Se borra la llamada anterior si la hay: si el gancho del padre se
        # rehizo, el nodo viejo apunta a una funcion que ya no existe.
        for n in bp("find_nodes", {"graph": eg, "title": ""}):
            if tipo(n) == "CallFunction|" + funcion:
                bp("delete_node", {"node": n})
        ev = None
        for n in bp("find_nodes", {"graph": eg, "title": "", "entry_points_only": True}):
            if tipo(n) == marca:
                ev = n
                break
        if ev is None:
            res[marca] = "evento no encontrado"
            continue
        llamada = bp("create_node", {"graph": eg, "type_id": "CallFunction|" + funcion,
                                     "pos": {"x": 400, "y": y}})
        # OJO: en un nodo de EVENTO el pin de ejecucion es el indice 1. El 0 es
        # el OutputDelegate, y conectarlo ahi no da error: simplemente no hace
        # nada. Ya mordio al montar el salto de zona.
        info = bp("get_node_infos", {"nodes": [ev]})
        seguia = None
        for p in info[0]["output_pins"]:
            if p["pin_id"]["index_id"] == 1 and p["connected_pins"]:
                seguia = p["connected_pins"][0]
                break
        def pin(nodo, direccion, indice):
            return {"direction": direccion, "index_id": indice,
                    "node": {"refPath": nodo["refPath"]}}
        bp("connect_pins", {"output_pin": pin(ev, "EGPD_Output", 1),
                            "input_pin": pin(llamada, "EGPD_Input", 0)})
        if seguia is not None:
            bp("connect_pins", {"output_pin": pin(llamada, "EGPD_Output", 0),
                                "input_pin": seguia})
        res[marca] = "enganchado" + ("" if seguia is None else " y reencadenado")
    bp("compile_blueprint", {"blueprint": {"refPath": PADRE}})
    return res
