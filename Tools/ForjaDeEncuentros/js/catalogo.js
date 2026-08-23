// Catalogo del "Arsenal de oportunidad" (PDF §4) y de los arquetipos de enemigo.
//
// Los nombres de campo son los que queremos en el Data Asset de Unreal, para que
// exportar sea un volcado y no una traduccion. Si aqui cambia un nombre, cambia
// tambien en el exportador.

/** Familias de arma temporal. Fase A no las simula todavia: solo las declara. */
export const FAMILIAS = {
  lanza_del_alba: {
    id: 'lanza_del_alba',
    nombre: 'Lanza del Alba',
    fuente: 'lancero_del_alba',
    rol: 'Alcance / control',
    recurso: { tipo: 'persistencia' },
    dosManos: true,
    compatibleOffHand: false,
    objetivoIdeal: 'Arqueros protegidos, lineas, grupos compactos.',
    ataqueDescarte: {
      nombre: 'Arrojar la lanza',
      descripcion: 'Empala, interrumpe o fija a un enemigo; la lanza se consume al impactar.',
      implementado: true,
      nota: 'Ya existe en el proyecto como el primer BP_Ability-equivalente.'
    },
    color: '#e8c76a'
  },
  arco_del_firmamento: {
    id: 'arco_del_firmamento',
    nombre: 'Arco del Firmamento',
    fuente: 'arquero_del_firmamento',
    rol: 'Rango / precision',
    recurso: { tipo: 'municion', cantidad: 12 },
    dosManos: true,
    compatibleOffHand: false,
    objetivoIdeal: 'Enemigos lejanos, weak points, elementos ambientales.',
    ataqueDescarte: {
      nombre: 'Descarga final',
      descripcion: 'Consume las flechas restantes en una descarga o disparo perforante y desecha el arco.',
      implementado: false
    },
    color: '#9fd0e8'
  },
  escudo_celestial: {
    id: 'escudo_celestial',
    nombre: 'Escudo Celestial',
    fuente: 'escudero_celestial',
    rol: 'Defensa / parry',
    recurso: { tipo: 'persistencia' },
    dosManos: false,
    esOffHand: true,
    compatibleOffHand: true,
    objetivoIdeal: 'Flechas, presion frontal, acercamiento seguro.',
    ataqueDescarte: {
      nombre: 'Shield bash final',
      descripcion: 'Bash o lanzamiento; el escudo se desmaterializa despues del impacto.',
      implementado: false
    },
    color: '#c8d4e8'
  },
  espadon_alabarda: {
    id: 'espadon_alabarda',
    nombre: 'Espadon / Alabarda',
    fuente: 'elite_pesado',
    rol: 'Guard break / AoE',
    recurso: { tipo: 'persistencia' },
    dosManos: true,
    compatibleOffHand: false,
    objetivoIdeal: 'Escudos, elites, grupos cercanos.',
    ataqueDescarte: {
      nombre: 'Golpe de suelo',
      descripcion: 'Gran stagger / guard break; el arma se sacrifica al finalizar.',
      implementado: false
    },
    color: '#d89a7a'
  },
  estandarte_ritual: {
    id: 'estandarte_ritual',
    nombre: 'Estandarte ritual',
    fuente: 'portador_del_estandarte',
    rol: 'Control / zona',
    recurso: { tipo: 'persistencia' },
    dosManos: true,
    compatibleOffHand: false,
    objetivoIdeal: 'Buff/debuff de arena, control territorial.',
    ataqueDescarte: {
      nombre: 'Clavar el estandarte',
      descripcion: 'Crea una ultima zona de efecto y consume voluntariamente el estandarte.',
      implementado: false
    },
    color: '#b58ad8'
  }
};

/** Como se pinta y se lee cada arquetipo en el editor. Los numeros van en calibracion.json. */
export const ARQUETIPOS = {
  lancero_del_alba:        { color: '#e8c76a', glifo: 'L', silueta: 'larga',   dropPorDefecto: 'garantizado' },
  arquero_del_firmamento:  { color: '#9fd0e8', glifo: 'A', silueta: 'esbelta', dropPorDefecto: 'garantizado' },
  escudero_celestial:      { color: '#c8d4e8', glifo: 'E', silueta: 'ancha',   dropPorDefecto: 'estandar'   },
  elite_pesado:            { color: '#d89a7a', glifo: 'X', silueta: 'masiva',  dropPorDefecto: 'estandar'   },
  portador_del_estandarte: { color: '#b58ad8', glifo: 'P', silueta: 'alta',    dropPorDefecto: 'garantizado' }
};

/** Politica de drop segun §8. */
export const POLITICAS_DROP = {
  garantizado: { etiqueta: 'Guaranteed Tactical Drop', descripcion: 'Forma parte de la solucion elegante. Siempre aparece.' },
  estandar:    { etiqueta: 'Standard Opportunity Drop', descripcion: 'Probabilidad o regla contextual. Variedad, no necesidad.' },
  piedad:      { etiqueta: 'Mercy Drop', descripcion: 'El director lo eleva si el jugador lleva mucho sin herramienta y la presion es alta.' },
  ninguno:     { etiqueta: 'No Drop', descripcion: 'Su arma no añade valor o saturaria la arena.' }
};

export const ORDEN_ARQUETIPOS = Object.keys(ARQUETIPOS);
