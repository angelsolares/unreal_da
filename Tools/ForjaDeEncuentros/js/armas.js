// Ciclo de vida del arma temporal (§3, §4.1 y la REGLA DE SEAL BREAK del PDF).
//
// Las tres reglas que no se negocian, porque son el diseño:
//   1. La espada base NUNCA desaparece. Siempre hay loadout valido.
//   2. El swap es IRREVERSIBLE: la anterior se desmaterializa, no vuelve al suelo.
//   3. NO hay durabilidad. Un arma temporal solo termina por swap, descarte,
//      agotar su recurso natural (flechas) o el seal break.
//
// La corrupcion visual no se modela: es cosmetica y no toca la vida util (§3).

/** Perfil de ataque efectivo de Malakh ahora mismo. */
export function perfilAtaque(M, cal, armas, pesado = false) {
  const t = M.temporal;
  if (t) {
    const fam = armas.familias[t.familia];
    const p = pesado ? (fam.ataquePesado || fam.ataqueLigero) : fam.ataqueLigero;
    if (p) return { ...p, familia: t.familia, esPesado: pesado };
  }
  const base = pesado ? cal.malakh.ataquePesado : cal.malakh.ataqueLigero;
  return {
    ...base,
    dano: (cal.malakh.danoBase + cal.malakh.armaBase.dano) * (pesado ? (base.multiplicadorDano || 1) : 1),
    familia: null,
    esPesado: pesado
  };
}

/** Perfil de bloqueo efectivo: el escudo celestial mejora mucho al bloqueo a pelo. */
export function perfilBloqueo(M, cal, armas) {
  if (M.offHand) {
    const fam = armas.familias[M.offHand.familia];
    if (fam?.bloqueo) return { ...fam.bloqueo, conEscudo: true };
  }
  return { ...cal.malakh.bloqueo, conEscudo: false };
}

export function descarteDe(M, armas) {
  if (!M.temporal) return null;
  return armas.familias[M.temporal.familia]?.descarte || null;
}

/** ¿Puede esta familia convivir con un off-hand? */
export function fuerzaSoltarOffHand(familia, armas) {
  return !!armas.familias[familia]?.dosManos;
}

/**
 * Equipa un arma recogida. Devuelve una lista de eventos para el log.
 * Aqui vive la regla del swap irreversible.
 */
export function equipar(M, familia, armas, origenId) {
  const fam = armas.familias[familia];
  const eventos = [];
  if (!fam) return eventos;

  if (fam.esOffHand) {
    if (M.temporal && fuerzaSoltarOffHand(M.temporal.familia, armas)) {
      // Lleva algo a dos manos: el escudo no cabe. Se purga la principal.
      eventos.push({ tipo: 'desmaterializa', arma: M.temporal.familia, motivo: 'incompatible-off-hand' });
      M.temporal = null;
    }
    if (M.offHand) {
      eventos.push({ tipo: 'desmaterializa', arma: M.offHand.familia, motivo: 'swap-off-hand' });
    }
    M.offHand = { familia, origenId };
    eventos.push({ tipo: 'equipa', arma: familia, ranura: 'off-hand', origen: origenId });
    return eventos;
  }

  if (M.temporal) {
    eventos.push({ tipo: 'desmaterializa', arma: M.temporal.familia, motivo: 'swap' });
  }
  M.temporal = {
    familia,
    origenId,
    municion: fam.recurso?.tipo === 'municion' ? fam.recurso.cantidad : null
  };
  if (fuerzaSoltarOffHand(familia, armas) && M.offHand) {
    eventos.push({ tipo: 'desmaterializa', arma: M.offHand.familia, motivo: 'arma-a-dos-manos' });
    M.offHand = null;
  }
  eventos.push({ tipo: 'equipa', arma: familia, ranura: 'principal', origen: origenId });
  return eventos;
}

/** Descuenta el recurso natural. Si se agota, el arma termina — no por desgaste, por munición. */
export function gastarRecurso(M, cantidad) {
  if (!M.temporal || M.temporal.municion == null) return null;
  M.temporal.municion -= cantidad;
  if (M.temporal.municion > 0) return null;
  const familia = M.temporal.familia;
  M.temporal = null;
  return { tipo: 'agotada', arma: familia };
}

export function consumirPorDescarte(M) {
  if (!M.temporal) return null;
  const familia = M.temporal.familia;
  const municion = M.temporal.municion;
  M.temporal = null;
  return { tipo: 'sacrificada', arma: familia, municionRestante: municion };
}

export function consumirOffHandPorDescarte(M) {
  if (!M.offHand) return null;
  const familia = M.offHand.familia;
  M.offHand = null;
  return { tipo: 'sacrificada', arma: familia, ranura: 'off-hand' };
}

/** REGLA DE SEAL BREAK (§ del prompt maestro): al ganar, todo lo temporal se va. */
export function purgarPorSeal(M) {
  const purgado = [];
  if (M.temporal) { purgado.push(M.temporal.familia); M.temporal = null; }
  if (M.offHand) { purgado.push(M.offHand.familia); M.offHand = null; }
  return purgado;
}

/**
 * ¿Este enemigo suelta arma al morir?
 *
 * Dos booleanos y ninguna probabilidad, porque eso es lo que sabe hacer
 * BP_DA_WeaponDropComponent: DropMainHandWeapon y DropOffHandWeapon. Las cuatro
 * politicas del §8 —garantizado, estandar, piedad, ninguno— no se pueden
 * implementar hoy, y simularlas seria medir algo que el juego no puede hacer.
 * Vuelven el dia que el componente tenga probabilidad.
 *
 * La ranura la decide el ARMA, no el enemigo: el escudo es off-hand, todo lo
 * demas es principal.
 */
export function decideDrop(enemigo, familia, armas) {
  const esOffHand = !!armas.familias[familia]?.esOffHand;
  const d = enemigo.drop || {};
  return esOffHand ? !!d.secundaria : !!d.principal;
}

export function etiquetaFamilia(familia, armas) {
  return armas.familias[familia]?.nombre || familia || 'Espada de Malakh';
}
