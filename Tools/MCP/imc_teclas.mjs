// Lee las asignaciones tecla<->accion de un InputMappingContext directamente del
// .uasset. Hace falta porque el MCP no serializa el array de structs `Mappings`
// y el sandbox de Python del editor no deja importar `unreal`.
import fs from 'node:fs';

const file = process.argv[2];
const b = fs.readFileSync(file);
let o = 0;
const i32 = () => { const v = b.readInt32LE(o); o += 4; return v; };
const u32 = () => { const v = b.readUInt32LE(o); o += 4; return v; };
const u16 = () => { const v = b.readUInt16LE(o); o += 2; return v; };
const fstr = () => {
  const n = i32();
  if (n === 0) return '';
  if (n > 0) { const s = b.toString('latin1', o, o + n - 1); o += n; return s; }
  const m = -n; let s = '';
  for (let k = 0; k < m - 1; k++) s += String.fromCharCode(b.readUInt16LE(o + k * 2));
  o += m * 2; return s;
};

u32();                                   // Tag
const legacy = i32();
if (legacy !== -4) i32();                // LegacyUE3Version
i32();                                   // FileVersionUE4
const verUE5 = legacy <= -8 ? i32() : 0;
i32();                                   // licensee
// Ojo: `o += i32()*20` NO vale, JS captura `o` antes de que i32() lo avance.
const cvCount = i32();
o += cvCount * 20;                       // custom versions: FGuid + int32
const totalHeader = i32();
fstr();                                  // folder name
u32();                                   // package flags
const nameCount = i32(), nameOffset = i32();
if (verUE5 >= 1008) { i32(); i32(); }    // soft object paths
fstr();                                  // localization id
i32(); i32();                            // gatherable text
const exportCount = i32(), exportOffset = i32();
const importCount = i32(), importOffset = i32();

o = nameOffset;
const names = [];
for (let n = 0; n < nameCount; n++) { names.push(fstr()); u16(); u16(); }
const fname = () => { const idx = i32(); i32(); return names[idx] ?? `?${idx}`; };

// --- imports: se prueban las dos zancadas posibles y se queda la que resuelve ---
function leerImports(conOptional) {
  o = importOffset;
  const out = [];
  for (let n = 0; n < importCount; n++) {
    fname(); fname(); i32();             // ClassPackage, ClassName, OuterIndex
    out.push(fname());                   // ObjectName
    if (conOptional) i32();              // bImportOptional
  }
  return out;
}
let imports = leerImports(true);
if (!imports.some(n => n.startsWith('IA_'))) imports = leerImports(false);

// --- las propiedades del export: se busca el arranque valido ---
function tag(pos) {
  o = pos;
  const name = fname(), type = fname();
  return { name, type, size: i32(), arrayIndex: i32(), fin: o };
}
let inicio = -1;
for (let p = totalHeader; p < totalHeader + 256; p++) {
  try {
    const t = tag(p);
    if (t.name === 'Mappings' && t.type === 'ArrayProperty') { inicio = p; break; }
  } catch { /* sigue probando */ }
}
if (inicio < 0) { console.log('no se encontro el array Mappings'); process.exit(1); }

const t = tag(inicio);
o = t.fin;
fname();                                 // InnerType
if (b[o++] === 1) o += 16;               // guid opcional del tag
const cuenta = i32();
// tag del struct interior
fname(); fname(); i32(); i32(); fname(); o += 16;
if (b[o++] === 1) o += 16;

const filas = [];
for (let e = 0; e < cuenta; e++) {
  const fila = { accion: null, tecla: null };
  for (;;) {
    const name = fname();
    if (name === 'None') break;
    const type = fname(), size = i32(); i32();
    if (type === 'StructProperty') { fname(); o += 16; }
    else if (type === 'ArrayProperty' || type === 'EnumProperty') fname();
    else if (type === 'BoolProperty') { fila[name] = b[o++] === 1; }
    if (b[o++] === 1) o += 16;
    const valor = o;
    if (name === 'Action') {
      const idx = b.readInt32LE(valor);
      fila.accion = idx < 0 ? imports[-idx - 1] : `export${idx}`;
    } else if (name === 'Key') {
      // FKey no guarda el FName pelado: dentro lleva otra propiedad etiquetada
      // `KeyName` (NameProperty), y el valor de verdad viene despues de ella.
      o = valor;
      fname(); fname(); i32(); i32();
      if (b[o++] === 1) o += 16;
      fila.tecla = fname();
    }
    o = valor + size;
  }
  filas.push(fila);
}

console.log(`${file.split(/[\\/]/).pop()}  —  ${filas.length} asignaciones\n`);
const porTecla = new Map();
for (const f of filas) {
  if (!f.tecla || /^Gamepad|^Mouse2D$/.test(f.tecla)) continue;
  if (!porTecla.has(f.tecla)) porTecla.set(f.tecla, []);
  porTecla.get(f.tecla).push(f.accion);
}
for (const [k, v] of [...porTecla].sort()) console.log(k.padEnd(20), [...new Set(v)].join(', '));
