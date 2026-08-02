# Dark Angels — POC

Prueba de concepto de un jefe gigante construida sobre **Dynamic Combat System (DCS)** en
Unreal Engine **5.8**.

## Qué hay en este repositorio

Solo el trabajo propio del proyecto:

```
Content/DarkAngels/          todo lo creado para la POC
├── Blueprints/
│   ├── Characters/          BP_DA_PlayerCharacter (hijo de BP_CombatCharacter)
│   └── Bosses/              BP_DA_GiantBoss + su IA corregida
├── Maps/                    L_DA_SeraphArena_POC (la arena)
└── ...
Config/                      configuracion del proyecto
DarkAngels_POC_Notas.md      notas de traspaso: el documento importante
```

## Lo que NO está, y por qué

Este repositorio **no incluye** los assets de terceros:

- `Content/DynamicCombatSystem` — asset comercial
- `Content/GiantBossProject` — asset de pago de Fab

Son productos de pago y redistribuirlos violaría su licencia. Para que el proyecto abra
correctamente hay que instalarlos desde tu propia cuenta de Fab / Epic, en esas mismas rutas.

Sin ellos el proyecto **no compila ni abre**: todo el trabajo de DarkAngels depende de ambos.

## Cómo retomar el trabajo

Leer **`DarkAngels_POC_Notas.md`**. Es el documento de traspaso entre sesiones y contiene el
estado real, las coordenadas verificadas del mapa, los defectos encontrados en los assets de
terceros y cómo se corrigieron, y las trampas del editor con las que ya nos hemos tropezado.

## Regla de oro del proyecto

`Content/DynamicCombatSystem` y `Content/GiantBossProject` son **referencia intacta**.
Nunca se modifican. Todo lo nuevo o corregido vive en `Content/DarkAngels`, como copias o
como clases hijas.
