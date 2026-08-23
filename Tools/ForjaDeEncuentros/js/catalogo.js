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

/**
 * Como se pinta y se lee cada arquetipo. Los numeros van en calibracion.json y
 * la descripcion de que hace cada uno en datos/arquetipos.json.
 *
 * `blueprint` es el nombre acordado con la sesion de Unreal (contrato §1.2). El
 * JSON del encuentro NO lo emite: la equivalencia vive del lado de Unreal en un
 * Data Asset. Aqui solo existe para que el exportador sepa que colocar.
 */
export const ARQUETIPOS = {
  lancero_del_alba: {
    color: '#e8c76a', glifo: 'L', silueta: 'larga',
    blueprint: 'BP_DA_Lancero', sueltaPorDefecto: true, armaEsOffHand: false
  },
  arquero_del_firmamento: {
    color: '#9fd0e8', glifo: 'A', silueta: 'esbelta',
    blueprint: 'BP_DA_Arquero', sueltaPorDefecto: true, armaEsOffHand: false
  },
  escudero_celestial: {
    color: '#c8d4e8', glifo: 'E', silueta: 'ancha',
    blueprint: 'BP_DA_Vigilante', sueltaPorDefecto: true, armaEsOffHand: true
  },
  elite_pesado: {
    // Cerrado en Unreal el 2026-08-23, y salio AL REVES de lo que supuse: el
    // Heraldo es el pesado. Le quitaron la lanza y el escudo y lleva DA_GreatAxe
    // a dos manos, asi que NO tiene guardia — justo lo contrario de lo que decia
    // mi calibracion.
    color: '#d89a7a', glifo: 'X', silueta: 'masiva',
    blueprint: 'BP_DA_Heraldo', sueltaPorDefecto: false, armaEsOffHand: false
  },
  portador_del_estandarte: {
    // El Inspector se queda con espada + escudo. Su valor es el buff/debuff...
    // que TODAVIA NO EXISTE. Hoy pelea como un Vigilante con otro nombre.
    color: '#b58ad8', glifo: 'P', silueta: 'alta',
    blueprint: 'BP_DA_Inspector', sueltaPorDefecto: true, armaEsOffHand: false,
    incompleto: 'Su aura de buff/debuff no existe todavia en Unreal: hoy pelea como un escudero.'
  }
};

/**
 * El drop son DOS BOOLEANOS, no una politica.
 *
 * BP_DA_WeaponDropComponent solo tiene DropMainHandWeapon y DropOffHandWeapon:
 * no existe probabilidad. Las cuatro politicas del §8 —garantizado, estandar,
 * piedad, ninguno— no se pueden implementar hoy, y fingirlas en el simulador
 * seria medir algo que el juego no sabe hacer. Vuelven cuando el componente
 * tenga probabilidad.
 */
export const RANURAS_DROP = {
  principal: { etiqueta: 'Arma principal', descripcion: 'DropMainHandWeapon del componente.' },
  secundaria: { etiqueta: 'Off-hand', descripcion: 'DropOffHandWeapon. Es la ranura del escudo.' }
};

export const ORDEN_ARQUETIPOS = Object.keys(ARQUETIPOS);
