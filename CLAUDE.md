# Dark Angels — instrucciones de trabajo

POC sobre **Dynamic Combat System** en **Unreal Engine 5.8.1**. Las notas de traspaso
—el documento largo, con el porqué de cada decisión— están en
[`DarkAngels_POC_Notas.md`](DarkAngels_POC_Notas.md). Este archivo es solo el mapa de
lo que se puede hacer por MCP.

---

## La regla

**Da por hecho que se puede hacer.** El MCP de este proyecto expone **57 toolsets**
más una vía de escape que ejecuta Python arbitrario dentro del editor. La lista de
cosas realmente imposibles es corta y está abajo.

Antes de decirle a Angel "eso no se puede" o "eso es trabajo manual tuyo",
**hay que haberlo intentado por los tres caminos**:

1. El toolset específico (`call_tool`).
2. `execute_python_code` con la API `unreal` completa.
3. `discover_python_class` para encontrar el método que no conocías.

Durante esta POC se dijo cuatro veces "no puedo" y las cuatro era falso: la pantalla
de UMG, los splines de landscape, el foliage y comprobar los assets sin guardar.
Todas se podían.

---

## Los 57 toolsets

### Epic — núcleo del editor (19)

`ToolsetRegistry.AgentSkillToolset` · `EditorToolset.EditorAppToolset` ·
`EditorToolset.LogsToolset`

`ActorTools` · `AssetTools` · `BlueprintTools` · `CurveTableTools` · `DataAssetTools` ·
`DataTableTools` · `MaterialTools` · `MaterialInstanceTools` · `ObjectTools` ·
`PrimitiveTools` · `SceneTools` · `SkeletalMeshTools` · `StaticMeshTools` ·
`StringTableTools` · `TextureTools` · `ProgrammaticToolset`
(prefijo largo: `editor_toolset.toolsets.<x>.<X>Tools`)

### Epic — Niagara (5)

`NiagaraToolset_System` (46 herramientas: `CreateNiagaraSystem`, `AddEmitter`,
`AddModule`, `AddRenderer`, `GetStackIssues`, `ApplyStackIssueFix`…) ·
`_Assets` · `_Component` · `_Blueprint` · `_Info`

### VibeUE (33)

| familia | toolsets |
|---|---|
| **Mundo** | `ActorService` · `LandscapeService` (68 acciones: esculpido, erosión, splines, agujeros, análisis de pendiente) · `LandscapeMaterialService` · `FoliageService` · `MapBlockoutService` · `RuntimeVirtualTextureService` |
| **UI** | `WidgetService` (UMG completo: componentes, eventos, fuentes, animaciones, `CapturePreview`, PIE) |
| **Animación** | `AnimSequenceService` (84) · `AnimMontageService` · `AnimGraphService` · `SkeletonService` |
| **VFX** | `NiagaraService` · `NiagaraEmitterService` · `NiagaraScratchPadService` (Custom HLSL) |
| **Audio** | `MetaSoundService` · `SoundCueService` |
| **Lógica** | `BlueprintService` · `BehaviorTreeService` · `BlackboardService` · `StateTreeService` · `InputService` · `GameplayTagService` · `EnumStructService` |
| **Materiales** | `MaterialService` · `MaterialNodeService` · `UVMappingService` |
| **Proyecto** | `ProjectSettingsService` · `EngineSettingsService` · `AssetDiscoveryService` · `FabService` · `TransactionService` (undo/redo) · `ViewportService` · `PerformanceService` (Unreal Insights, CPU vs GPU bound) |

### Herramientas de nivel superior (7, sin `toolset_name`)

**`execute_python_code`** · `discover_python_class` · `discover_python_function` ·
`discover_python_module` · `list_python_subsystems` · `deep_research` · `terrain_data`

---

## Cómo se llama a cada cosa

```
list_toolsets()                          # los 57
describe_toolset("VibeUE.WidgetService") # esquemas — OJO: algunos pesan 88-278 KB
call_tool(toolset_name=..., tool_name=..., arguments={...})
```

- **Los nombres de herramienta van en PascalCase** (`ListWidgetBlueprints`), aunque la
  descripción del toolset los liste en snake_case.
- `describe_toolset` de un toolset grande **se guarda a fichero** en vez de responder.
  Sacar solo los nombres con `grep -o '"name":"[^"]*"'` antes de leer esquemas.
- Desde un script de `ue.mjs`, `execute_tool("VibeUE.X.Y", {...})` **también alcanza
  los toolsets de VibeUE**. Es la forma barata de barrer cientos de assets.

### La vía de escape

```python
execute_python_code(code="""
import unreal
lvl = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
print(lvl.get_current_level().get_outer().get_name())
""")
```

API `unreal` completa, subsistemas incluidos. **No confundir con el sandbox del
`ProgrammaticToolset`**, que solo permite `time, math, re, json, datetime, copy` —
esa restricción es de Epic y no aplica aquí.

---

## Lo que de verdad no se puede

Corto, y cada punto está verificado:

- **Declarar interfaces** en un Blueprint por DSL. Se rodea heredando.
- **Cambiar el número de puntos** de un spline del plugin Water: tumba el editor con
  un assert. Mover puntos existentes sí, mandando los tres arrays en una llamada.
- **Arrays de structs** por `ObjectTools.set_properties`: pierden el último elemento,
  y un struct suelto se escribe a medias sin dar error.
- **Hornear NavMesh** — no probado aún por `execute_python_code`; puede que sí se pueda.
- **Tripo3DUEBridge** queda desactivado: rompe cualquier compilación (le falta una
  `.lib` que su propio `Build.cs` exige).

Todo lo demás que en su día se dio por imposible **merece un segundo intento** con
`execute_python_code` antes de darlo por perdido.

---

## Antes de tocar nada

- **El editor miente en las dos direcciones.** `save_assets` devuelve `true` sin
  guardar, y el diálogo de fallo es un resumen agregado. **Releer siempre lo escrito**,
  campo a campo, y para lo crítico buscar el valor en el binario del `.uasset`.
- **Landscape y foliage editan solo el nivel actual.** Los mapas de Malkuth viven en
  Level Instances: hay que abrir el `_Sub` correcto primero.
- **El submapa tiene su propio espacio.** La LI suma el offset.
- **Compilar requiere cerrar el editor.** Cerrarlo con `CloseMainWindow` y **esperar a
  que el proceso desaparezca** (aquí tardó 109 s). Nunca `taskkill`: se pierde lo no
  guardado.
- Relanzar con el MCP ya arrancado:
  `UnrealEditor.exe "<proyecto>.uproject" -ExecCmds="ModelContextProtocol.StartServer"`
- **Activar más toolsets de Epic no exige recompilar**: los 27 de
  `Engine/Plugins/Experimental/Toolsets` traen su DLL. Quedan disponibles
  `UMGToolSet`, `PCGToolset`, `GameplayTagsToolset` y `StateTreeToolset`.

## Del repositorio

Solo sube **trabajo propio**. Los assets de pago (DCS, GiantBoss, Sword_Takedown) y
`Plugins/VibeUE` están en `.gitignore` y ahí se quedan.
