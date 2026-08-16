# Herramientas para hablarle al editor por MCP

Scripts de apoyo para manipular y **medir** Malkuth desde fuera del editor.
Contexto completo en `DarkAngels_POC_Notas.md`.

## `ue.mjs`

Cliente JSON-RPC del servidor MCP del editor (`http://127.0.0.1:8000/mcp`).

```bash
node ue.mjs shot salida.png <x> <y> <z> <pitch> <yaw>
node ue.mjs thumb salida.png /Game/Ruta/Al/Asset
node ue.mjs call <toolset|-> <tool> '<argsJson>'
node ue.mjs script fichero.py
```

Dos decisiones que no son arbitrarias:

- **Escribe los PNG a disco.** `CaptureViewport` devuelve el PNG en base64 y una captura de
  1208x928 son ~2.6 M de caracteres: no cabe en una respuesta de herramienta.
- **Usa `node:http`, no `fetch`.** undici corta a los 5 minutos con
  `UND_ERR_HEADERS_TIMEOUT`, y los barridos de cientos de actores tardan mas.

## Sondas (`probe_*.py`)

Van por `node ue.mjs script probe_x.py`. Todas imprimen numeros, no imagenes: **siguen
siendo validas aunque el viewport este en un modo de vista raro**.

| Script | Para que |
|---|---|
| `probe_arco.py` | Barrido de 360 desde un punto: donde el horizonte esta abierto al vacio |
| `probe_rendijas.py` | Barrido fino de un arco, para cazar rendijas que deja un telon |
| `probe_gaz_claro.py` | Perfil de techo (elevacion maxima con impacto) desde dos zonas |
| `probe_gaz360.py` | Perfil de techo en los 360, y avisa de agujeros |
| `probe_techo.py` | Igual pero identificando **que actor** forma el techo |
| `probe_rejilla.py` | Rejilla sobre el suelo: que porcentaje recibe sol directo |
| `probe_sol.py` | Traza hacia el sol desde puntos sueltos |
| `probe_bloqueo.py` | Que actores tapan el sol y a que cota tendrian que bajar |

## Level Instances

`li_edit.py` y `li_commit.py` abren y cierran un Level Instance por etiqueta (editar la
constante de arriba del fichero). **Sin `edit_level_instance` no se puede tocar nada**
dentro de una zona: tanto `set_properties` como `set_actor_transform` fallan.

`commit_level_instance` puede decir que si y no haber guardado: **comprobar la fecha del
`.umap` en disco**.
