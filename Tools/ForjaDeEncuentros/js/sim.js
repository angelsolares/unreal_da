// Simulador determinista del encuentro.
//
// Reglas de la casa:
//  - Nada de Math.random: todo sale del Azar sembrado, o el lote de 200 partidas
//    no compara politicas, compara ruido.
//  - Nada de render aqui dentro: esto tiene que poder correr 1000 veces sin pintar.
//  - Todo numero de balance viene de calibracion.json o armas.json, nunca a pelo.

import { Azar } from './rng.js';
import { obstaculosDe, dentroDeRect, centroDeRect, poliDeRect, oleadasDe } from './esquema.js';
import {
  dist, resta, suma, escala, normaliza, largo, yawDe, giraHacia, deltaAngulo,
  dentroDePoligono, hayVision, empujaFuera, segmentoCortaPoligono, centroide
} from './geometria.js';
import {
  perfilAtaque, perfilBloqueo, descarteDe, equipar, gastarRecurso,
  consumirPorDescarte, consumirOffHandPorDescarte, purgarPorSeal, decideDrop
} from './armas.js';

export const ESTADOS = {
  LIBRE: 'libre',
  ANTICIPACION: 'anticipacion',
  ACTIVO: 'activo',
  RECUPERACION: 'recuperacion',
  ESQUIVA: 'esquiva',
  CURANDO: 'curando',
  RECOGIENDO: 'recogiendo',
  ATURDIDO: 'aturdido',
  MUERTO: 'muerto'
};

const AGUANTE_POR_DEFECTO = { arquero_del_firmamento: 20, elite_pesado: 120 };
const REGEN_AGUANTE = 20;
/** Segundos que la stamina tarda en volver a subir tras gastarla. Medido 23/08. */
const PAUSA_STAMINA = 1.0;
const RADIO_ALERTA_ALIADOS = 900;

export class Simulacion {
  constructor(encuentro, calibracion, armas, politica, semilla, opciones = {}) {
    this.enc = encuentro;
    this.cal = calibracion;
    this.armas = armas;
    this.politica = politica;
    this.azar = new Azar(semilla);
    this.semilla = semilla;
    this.dt = calibracion.reglas.dt;
    this.tiempoLimite = opciones.tiempoLimite ?? calibracion.reglas.tiempoLimite;
    this.grabar = opciones.grabar || false;
    this.cadaCuantosFotogramas = opciones.cadaCuantosFotogramas || 2;

    this.t = 0;
    this.tick = 0;
    this.proyectiles = [];
    this.drops = [];
    this.zonas = [];
    this.eventos = [];
    this.fotogramas = [];
    this.terminada = false;
    this.razonFin = null;
    this._contadorDrops = 0;
    this.maxDropsSimultaneos = 0;
    // Cuantos le llegaron a la vez. Es LA cifra de la activacion escalonada: el
    // techo de la espada sola son dos, y el tercero es un acantilado.
    this.maxEnemigosALaVez = 0;

    this._montar();
    if (this.politica.iniciar) this.politica.iniciar(this);
  }

  // ------------------------------------------------------------------ montaje

  _montar() {
    const cal = this.cal;
    const m = cal.malakh;
    this.malakh = {
      id: 'malakh',
      bando: 'malakh',
      nombre: 'Malakh',
      pos: { ...this.enc.jugador.pos },
      cota: 0,
      yaw: 0,
      radio: m.radio,
      hp: m.hp, hpMax: m.hp,
      stamina: m.stamina, staminaMax: m.stamina,
      aguante: 100, aguanteMax: 100,
      estado: ESTADOS.LIBRE,
      tEstado: 0,
      accion: null,
      objetivoId: null,
      perfil: m,
      bloqueando: false,
      // --- armas temporales (Fase B) ---
      temporal: null,
      offHand: null,
      armasRecogidas: [],
      descartesUsados: 0,
      tUltimaArma: null,
      // --- consumibles y estadistica ---
      pociones: m.pocion ? m.pocion.cantidad : 0,
      pocionesBebidas: 0,
      curacionTotal: 0,
      danoRecibido: 0,
      golpesAsestados: 0,
      golpesFallados: 0,
      esquivasLogradas: 0
    };
    this.malakh.cota = this.enc.jugador.cota || 0;
    this.malakh.yaw = yawDe(resta(centroDeRect(this.enc.arena.bounds), this.malakh.pos));

    this.enemigos = this.enc.enemigos.map(e => {
      const p = cal.arquetipos[e.arquetipo];
      if (!p) throw new Error(`Arquetipo desconocido en calibracion: ${e.arquetipo}`);
      const aguante = AGUANTE_POR_DEFECTO[e.arquetipo] ?? 40;
      return {
        id: e.id,
        bando: 'enemigo',
        arquetipo: e.arquetipo,
        nombre: p.nombre,
        etiqueta: e.etiqueta || '',
        drop: e.drop,
        pos: { ...e.pos },
        cota: e.cota || 0,
        yaw: e.yaw ?? 180,
        radio: p.radio,
        hp: p.hp, hpMax: p.hp,
        aguante, aguanteMax: aguante,
        estado: ESTADOS.LIBRE,
        tEstado: 0,
        accion: null,
        recarga: this.azar.rango(0, p.recarga * 0.5),
        alertado: false,
        perfil: p,
        danoInfligido: 0,
        tMuerte: null
      };
    });

    this.agentes = [this.malakh, ...this.enemigos];
    // Muros Y plataformas: desde abajo una plataforma es un bloque, no aire.
    this.coberturas = obstaculosDe(this.enc);
    this.plataformas = this.enc.plataformas || [];
    this._montarOleadas();
  }

  /**
   * Activacion escalonada (§6). El techo de la espada sola son DOS enemigos y el
   * tercero es un acantilado, no una pendiente: la palanca mas barata de todas
   * las que quedaban era escalonar la entrada, no bajarle la vida a nadie.
   *
   * Un encuentro sin `oleadas` declaradas monta UNA sola, implicita, con todo el
   * mundo dentro y activacion `inicio`. Ahi no cambia nada de lo que ya habia:
   * cada enemigo sigue despertando por su propio `rangoAggro`.
   */
  _montarOleadas() {
    this.oleadas = oleadasDe(this.enc).map(o => ({ ...o, activada: false, tDisparo: null, tActiva: null }));
    const porEnemigo = new Map();
    for (const o of this.oleadas) for (const id of o.enemigos) porEnemigo.set(id, o);

    for (const E of this.enemigos) {
      const o = porEnemigo.get(E.id) || this.oleadas[0];
      E.oleadaId = o.id;
      E.presencia = o.presencia;
      E.activo = false;
      // `entra` significa que todavia no esta en la arena: no ocupa sitio, no
      // recibe golpes y no se lee desde la puerta.
      E.presente = o.presencia !== 'entra';
    }

    for (const o of this.oleadas) {
      // La primera oleada NO se da por alertada: sus enemigos ven venir a Malakh
      // como siempre. Las siguientes entran ya lanzadas, que es lo que significa
      // que una oleada se "active".
      if (o.activacion.tipo === 'inicio') this._activarOleada(o, false);
    }
  }

  _activarOleada(o, alertar = true) {
    if (o.activada) return;
    o.activada = true;
    o.tActiva = this.t;
    for (const id of o.enemigos) {
      const E = this.enemigos.find(e => e.id === id);
      if (!E || E.estado === ESTADOS.MUERTO) continue;
      E.activo = true;
      E.presente = true;
      if (alertar) E.alertado = true;
    }
    if (!o.implicita) {
      this._evento('oleada', { oleada: o.id, nombre: o.nombre, enemigos: o.enemigos.length, t: +this.t.toFixed(2) });
    }
  }

  /** ¿Se cumple ya la condicion de esta oleada? */
  _condicionCumplida(o) {
    const a = o.activacion || {};
    switch (a.tipo) {
      case 'inicio': return true;
      case 'tiempo': return this.t >= (a.segundos ?? 0);
      case 'bajas': return this.enemigos.filter(e => e.estado === ESTADOS.MUERTO).length >= (a.cuantas ?? 0);
      case 'oleadaLimpia': {
        const previa = this.oleadas.find(x => x.id === a.oleada);
        if (!previa || !previa.activada) return false;
        return previa.enemigos.every(id => {
          const E = this.enemigos.find(e => e.id === id);
          return !E || E.estado === ESTADOS.MUERTO;
        });
      }
      default: return false;
    }
  }

  _pasoOleadas() {
    for (const o of this.oleadas) {
      if (o.activada) continue;
      if (o.tDisparo == null) {
        if (!this._condicionCumplida(o)) continue;
        o.tDisparo = this.t + (o.retardo || 0);
      }
      if (this.t >= o.tDisparo) this._activarOleada(o, true);
    }
    this._despertarPorProximidad();
  }

  /**
   * Un dormido al que te acercas se levanta, aunque su oleada no haya entrado.
   *
   * Existe porque escalonar de uno en uno deja a cuatro de los cinco quietos casi
   * todo el encuentro, y uno de ellos plantado en mitad del claro. El simulador ya
   * despertaba AL QUE LE PEGAS (ver _aplicarDano); el motor no, y con un radio por
   * encima del alcance de mele las dos cosas acaban siendo casi la misma.
   *
   * OJO AL RADIO: pasarse reconstruye la pareja simultanea que la receta evita a
   * proposito, y dos cuerpos a la vez no se ganan con espada sola. Se despierta al
   * enemigo SUELTO, nunca a su oleada entera.
   */
  _despertarPorProximidad() {
    const R = this.cal.arena?.radioDespertar || 0;
    if (R <= 0) return;
    const M = this.malakh;
    if (!M || M.estado === ESTADOS.MUERTO) return;
    for (const E of this.enemigos) {
      if (E.activo || !E.presente || E.estado === ESTADOS.MUERTO) continue;
      // 3D, con la cota: es lo que mide el `GetDistanceTo` del motor. En planta, un
      // arquero de balcon se despertaria desde abajo sin que puedas ni verle.
      const dz = (E.cota || 0) - (M.cota || 0);
      if (Math.hypot(dist(E.pos, M.pos), dz) > R) continue;
      E.activo = true;
      E.alertado = true;
      this._evento('despertar', { agente: E.id, oleada: E.oleadaId, motivo: 'proximidad' });
    }
  }

  // -------------------------------------------------------------------- bucle

  correr() {
    while (!this.terminada) this.paso();
    return this.resultado();
  }

  paso() {
    if (this.terminada) return;
    const dt = this.dt;

    // La velocidad de cada agente, para que quien dispara pueda ADELANTAR el tiro.
    // Se toma ANTES de mover a nadie en este tick, o sea que es la del tick anterior:
    // es exactamente lo que el motor tiene disponible cuando lanza la flecha.
    for (const a of this.agentes) {
      a._vel = a._posPrev
        ? { x: (a.pos.x - a._posPrev.x) / dt, y: (a.pos.y - a._posPrev.y) / dt }
        : { x: 0, y: 0 };
      a._posPrev = { x: a.pos.x, y: a.pos.y };
    }

    this._pasoOleadas();
    this._pasoProyectiles(dt);
    this._pasoDrops(dt);
    this._pasoZonas(dt);
    this._pasoMalakh(dt);
    for (const e of this.enemigos) this._pasoEnemigo(e, dt);
    this._separarAgentes();

    for (const a of this.agentes) {
      if (a.estado === ESTADOS.MUERTO) continue;
      a.aguante = Math.min(a.aguanteMax, a.aguante + REGEN_AGUANTE * dt);
    }
    // LA PAUSA DE 1 s TRAS GASTAR, que estaba MEDIDA desde el 23/08 y sin cablear.
    // La procedencia de `malakh.regenStamina` lo dice literal: "1,75 cada 0,05 s = 35/s,
    // y se corta 1 s despues de gastar". Solo se habia implementado la primera mitad.
    //
    // Sin la pausa, la defensa de Malakh es GRATIS y con ella se cae media calibracion:
    // bloquear cuesta 22 por golpe parado y dos Escuderos pegan cada 1,1 s, o sea 20/s
    // de gasto contra 35/s de regeneracion. La guardia no se rompia jamas. Medido: en
    // 100 partidas contra dos Escuderos la stamina no bajo de 100 NI UNA VEZ, Malakh
    // eligio `bloquear` 2419 veces por partida y el combate duro 111 s costando 18 de
    // daño. Un combate de casi dos minutos que cuesta el 18% de la vida no es un
    // combate, es una espera.
    if (this.malakh.stamina < this.malakh.staminaMax &&
        this.t - (this.malakh.tUltimoGasto ?? -Infinity) >= PAUSA_STAMINA) {
      this.malakh.stamina = Math.min(
        this.malakh.staminaMax,
        this.malakh.stamina + this.cal.malakh.regenStamina * dt
      );
    }

    this.t += dt;
    this.tick += 1;
    this.maxDropsSimultaneos = Math.max(this.maxDropsSimultaneos, this.drops.length);
    this.maxEnemigosALaVez = Math.max(
      this.maxEnemigosALaVez,
      this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO && e.activo && e.alertado).length);
    if (this.grabar && this.tick % this.cadaCuantosFotogramas === 0) this._grabarFotograma();
    this._comprobarFin();
  }

  _comprobarFin() {
    const vivos = this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO);
    if (this.malakh.hp <= 0) {
      this.terminada = true; this.razonFin = 'muerte';
      this._evento('derrota', { motivo: 'Malakh cae' });
    } else if (vivos.length === 0) {
      this.terminada = true; this.razonFin = 'victoria';
      this._evento('victoria', { tiempo: this.t });
      // REGLA DE SEAL BREAK: todo lo temporal se desmaterializa (§ prompt maestro).
      const purgado = purgarPorSeal(this.malakh);
      this.drops = [];
      if (purgado.length) this._evento('sealBreak', { purgado });
    } else if (this.t >= this.tiempoLimite) {
      this.terminada = true; this.razonFin = 'tiempo';
      this._evento('derrota', { motivo: `Se agoto el limite de ${this.tiempoLimite}s`, vivos: vivos.length });
    }
  }

  // ------------------------------------------------------------------- Malakh

  _pasoMalakh(dt) {
    const M = this.malakh;
    if (M.estado === ESTADOS.MUERTO) return;

    // Se muestrea en TODOS los ticks. Si solo se midiera al atacar, el "anterior"
    // seria de hace medio segundo y la lectura no valdria nada.
    M.alejandose = this._seAleja(M, this.agente(M.objetivoId), dt);

    M.bloqueando = false;
    M.tEstado += dt;

    if (M.estado === ESTADOS.ATURDIDO) {
      if (M.tEstado >= M.accion.duracion) this._aLibre(M);
      return;
    }

    if (M.estado === ESTADOS.CURANDO) {
      if (M.tEstado >= M.accion.duracion) {
        const cura = Math.min(M.accion.curacion, M.hpMax - M.hp);
        M.hp += cura;
        M.curacionTotal += cura;
        this._evento('curado', { agente: M.id, cura: +cura.toFixed(1), restantes: M.pociones });
        this._aLibre(M);
      }
      return;
    }

    if (M.estado === ESTADOS.RECOGIENDO) {
      if (M.tEstado >= M.accion.duracion) {
        this._completarRecogida(M.accion.dropId);
        this._aLibre(M);
      }
      return;
    }

    if (M.estado === ESTADOS.ESQUIVA) {
      const a = M.accion;
      this._mover(M, escala(a.dir, (a.distancia / a.duracion) * dt));
      if (M.tEstado >= a.duracion) this._aLibre(M);
      return;
    }

    if (M.estado !== ESTADOS.LIBRE) {
      this._avanzarAtaque(M, dt);
      return;
    }

    // --- libre: decide la politica ---
    const intencion = this.politica.decidir(this, M);
    M.objetivoId = intencion.objetivo || M.objetivoId;
    const obj = this.agente(M.objetivoId);

    if (intencion.accion === 'esquivar' && M.stamina >= this.cal.malakh.esquiva.costeStamina) {
      this._iniciarEsquiva(M, intencion.direccion);
      return;
    }

    if (intencion.accion === 'beber' && M.pociones > 0) {
      const p = this.cal.malakh.pocion;
      M.pociones -= 1;
      M.pocionesBebidas += 1;
      M.estado = ESTADOS.CURANDO;
      M.tEstado = 0;
      M.accion = { duracion: p.duracion, curacion: p.curacion };
      this._evento('bebe', { agente: M.id, restantes: M.pociones });
      return;
    }

    // --- recoger un arma del suelo (§4.1) ---
    if (intencion.accion === 'recoger') {
      const drop = this.drops.find(d => d.id === intencion.dropId);
      if (drop) {
        if (dist(M.pos, drop.pos) <= this.armas.reglas.radioRecogida &&
            Math.abs((drop.cota || 0) - M.cota) <= 120) {
          M.estado = ESTADOS.RECOGIENDO;
          M.tEstado = 0;
          M.accion = { duracion: this.armas.reglas.duracionRecogida, dropId: drop.id };
          return;
        }
        this._avanzarHacia(M, { pos: drop.pos, cota: drop.cota, radio: 0 }, 0, dt);
        return;
      }
    }

    // --- ataque de descarte (§3.2): sacrificar el arma por un remate ---
    if (intencion.accion === 'descartar') {
      const d = descarteDe(M, this.armas);
      if (d) { this._iniciarDescarte(M, d); return; }
    }

    if (obj && obj.estado !== ESTADOS.MUERTO) {
      M.yaw = giraHacia(M.yaw, yawDe(resta(obj.pos, M.pos)), M.perfil.velocidadGiro * dt);
    }

    if (intencion.accion === 'bloquear') {
      M.bloqueando = true;
      const f = perfilBloqueo(M, this.cal, this.armas).factorVelocidad;
      // `avanzarA` cruza la arena tras el escudo. Tiene que ir por el mismo
      // camino que todo lo demas —rampas y rodeos incluidos—, o Malakh se queda
      // empujando la pared de la torre con el escudo en alto para siempre.
      const destino = intencion.avanzarA ? this.agente(intencion.avanzarA) : null;
      if (destino && destino.estado !== ESTADOS.MUERTO) {
        const alcance = perfilAtaque(M, this.cal, this.armas, false).alcance;
        this._avanzarHacia(M, destino, alcance * 0.7, dt * f);
      } else if (intencion.direccion) {
        this._mover(M, escala(normaliza(intencion.direccion), M.perfil.velocidad * f * dt));
      }
      // El giro va DESPUES de moverse: el escudo mira a quien dispara, no a
      // donde se anda. Andar de lado tras la guardia es justo el gesto.
      if (intencion.mirarA) {
        M.yaw = giraHacia(M.yaw, yawDe(resta(intencion.mirarA, M.pos)), M.perfil.velocidadGiro * dt);
      }
      return;
    }

    if (intencion.accion === 'reposicionar' && intencion.direccion) {
      this._mover(M, escala(normaliza(intencion.direccion), M.perfil.velocidad * dt));
      return;
    }

    if (intencion.accion === 'atacar' || intencion.accion === 'atacarPesado') {
      const perfil = perfilAtaque(M, this.cal, this.armas, intencion.accion === 'atacarPesado');
      // La embestida deja LANZAR el ataque desde mas lejos, contando con que el cuerpo
      // cubre el resto — PERO SOLO CONTRA QUIEN SE ACERCA. Medido: abrirla siempre da
      // -19% contra dos Lanceros y +84% contra el Arquero del balcon, porque te
      // comprometes desde 336, embistes 112, el arquero ya no esta y la recuperacion se
      // la come (1% de victorias, 1.8 ataques por combate). Un jugador no hace eso: no
      // carga contra quien huye. La condicion es esa, y no un porcentaje inventado.
      const abre = perfil.embestidaAbreAtaque && (perfil.embestida || 0) > 0 && !M.alejandose;
      const alcanceIniciando = perfil.alcance + (abre ? perfil.embestida : 0);
      if (obj && this._enAlcance(M, obj, alcanceIniciando) && M.stamina >= (perfil.costeStamina || 0)) {
        if (!perfil.necesitaVision ||
            hayVision(M.pos, M.cota, obj.pos, obj.cota, this.coberturas, this.cal.malakh.alturaOjos)) {
          this._iniciarAtaque(M, perfil);
          return;
        }
      }
    }

    if (obj && obj.estado !== ESTADOS.MUERTO) {
      const perfil = perfilAtaque(M, this.cal, this.armas, false);
      // Un arma de rango no sirve de nada contra lo que no se ve, y la distancia
      // de parada no puede seguir siendo la del arma. Con el Arco en la mano y
      // un balcon tapando al objetivo, Malakh se plantaba a 17 m —"ya estoy en
      // alcance"— sin linea de tiro y sin acercarse, hasta que saltaba el
      // watchdog. Medido: 180 s parado a 5 m de un escudero con 16 de vida.
      const ciego = perfil.necesitaVision &&
        !hayVision(M.pos, M.cota, obj.pos, obj.cota, this.coberturas, this.cal.malakh.alturaOjos);
      // Quien embiste NO se planta en la cara: se queda fuera y entra de golpe. Si la
      // parada no se extiende tambien, la puerta de ataque abierta no sirve de nada
      // —cuando ataca ya esta pegado— y el arma pierde su gesto entero.
      const fuera = perfil.embestidaAbreAtaque && !M.alejandose ? (perfil.embestida || 0) : 0;
      const parada = (ciego ? this.cal.malakh.ataqueLigero.alcance
                            : perfil.alcance + fuera) * 0.7;
      this._avanzarHacia(M, obj, parada, dt);
    }
  }

  _iniciarEsquiva(M, direccion) {
    const e = this.cal.malakh.esquiva;
    M.stamina -= e.costeStamina;
    M.tUltimoGasto = this.t;
    M.estado = ESTADOS.ESQUIVA;
    M.tEstado = 0;
    M.accion = { ...e, dir: normaliza(direccion || { x: -1, y: 0 }) };
    this._evento('esquiva', { agente: M.id });
  }

  _completarRecogida(dropId) {
    const i = this.drops.findIndex(d => d.id === dropId);
    if (i < 0) return;
    const drop = this.drops[i];
    this.drops.splice(i, 1);
    const M = this.malakh;
    for (const ev of equipar(M, drop.familia, this.armas, drop.origenId)) {
      this._evento(ev.tipo, { agente: M.id, ...ev });
    }
    M.armasRecogidas.push({ familia: drop.familia, t: +this.t.toFixed(2), origen: drop.origenId });
    M.tUltimaArma = this.t;
  }

  _iniciarDescarte(M, d) {
    M.estado = ESTADOS.ANTICIPACION;
    M.tEstado = 0;
    M.accion = {
      ...d,
      esDescarte: true,
      ventana: d.ventana ?? 0.12,
      arco: d.arco ?? 360,
      yaGolpeo: false,
      dano: d.dano + (d.danoPorFlechaRestante ? d.danoPorFlechaRestante * (M.temporal?.municion || 0) : 0)
    };
    M.descartesUsados += 1;
    const ev = M.temporal ? consumirPorDescarte(M) : consumirOffHandPorDescarte(M);
    this._evento('descarte', { agente: M.id, nombre: d.nombre, arma: ev?.arma, objetivo: M.objetivoId });
  }

  // -------------------------------------------------------------------- enemigos

  _pasoEnemigo(E, dt) {
    if (E.estado === ESTADOS.MUERTO) return;
    // Su oleada no ha entrado todavia: esta plantado y quieto, o ni siquiera
    // esta. Sigue contando como vivo para la victoria, que es lo que hace que
    // escalonar no sea lo mismo que quitar enemigos.
    if (!E.activo) return;
    const M = this.malakh;
    E.tEstado += dt;
    E.recarga = Math.max(0, E.recarga - dt);

    if (E.estado === ESTADOS.ATURDIDO) {
      if (E.tEstado >= E.accion.duracion) this._aLibre(E);
      return;
    }
    if (E.estado !== ESTADOS.LIBRE) {
      this._avanzarAtaque(E, dt);
      return;
    }

    if (!E.alertado) {
      const d = dist(E.pos, M.pos);
      const ve = hayVision(E.pos, E.cota, M.pos, M.cota, this.coberturas, this.cal.malakh.alturaOjos);
      if (d <= E.perfil.rangoAggro && ve) this._alertar(E);
      else return;
    }

    E.yaw = giraHacia(E.yaw, yawDe(resta(M.pos, E.pos)), E.perfil.velocidadGiro * dt);

    if (E.arquetipo === 'arquero_del_firmamento') this._pasoArquero(E, dt);
    else this._pasoCuerpoACuerpo(E, dt);
  }

  _alertar(E) {
    if (E.alertado) return;
    E.alertado = true;
    this._evento('alerta', { agente: E.id });
    for (const otro of this.enemigos) {
      if (otro.alertado || otro.estado === ESTADOS.MUERTO) continue;
      // El grito no cruza oleadas: si despertase a la siguiente, escalonar la
      // entrada no serviria de nada.
      if (!otro.activo) continue;
      if (dist(otro.pos, E.pos) <= RADIO_ALERTA_ALIADOS) otro.alertado = true;
    }
  }

  /**
   * CUANDO decide atacar y SI el golpe llega son dos numeros distintos, y el
   * motor los tiene separados de verdad: el Behaviour Tree lanza el ataque con
   * un decorador de distancia (DistanceToTarget < 250, o sea 208 de centro a
   * superficie), mientras que el golpe solo toca si el arma llega — 171 cm la
   * espada, medido de la pose. El enemigo AMAGA a maxima distancia y falla.
   *
   * Meterlos en un solo numero deja al enemigo congelado: se para donde le dice
   * su MoveTo (200) y nunca entra en el rango de golpe, asi que no ataca jamas.
   */
  /**
   * EL RODEO, y por que existe.
   *
   * Hasta el 25/08 el enemigo se plantaba en `distanciaPreferida` y picaba cada vez
   * que la recarga se lo permitia. Medido en PIE contra un Malakh pasivo —la misma
   * condicion en los dos lados— eso daba 240 de daño en 16 s con una pareja, y el
   * motor da 45. Cinco veces mas violento.
   *
   * El arbol no pelea asi. Bajo su puerta de combate hay un Selector con TRES ramas y
   * la primera es un ESTRAFE: `Chance 30` envuelto en un `TimeLimit` (5 s por
   * defecto) que hace un bucle de Walk + MoveTo alrededor del jugador. O sea que
   * casi un tercio de los ciclos de decision se van en rodear sin atacar. Y cuando
   * si ataca, lo hace DESPUES de un MoveTo que le mete encima: medido en PIE, se
   * asientan entre 108 y 165 de centro a centro, no a distancia de arma.
   *
   * Los dos numeros salen del propio arbol (Chance 30, TimeLimit 5 s), no de un
   * ajuste a ojo. Lo que NO cierra del todo es el ritmo de daño: ver la nota de
   * `arquetipos.*.probabilidadRodeo` en calibracion.json.
   */
  _pasoCuerpoACuerpo(E, dt) {
    const M = this.malakh;
    const p = E.perfil;

    if ((E.rodeando || 0) > 0) {
      E.rodeando -= dt;
      const hacia = normaliza(resta(M.pos, E.pos));
      const lado = E.sentidoRodeo || 1;
      this._mover(E, escala({ x: -hacia.y * lado, y: hacia.x * lado }, this._velocidadDe(E) * dt));
      E.yaw = giraHacia(E.yaw, yawDe(hacia), (p.velocidadGiro || 360) * dt);
      return;
    }

    const d = dist(E.pos, M.pos) - M.radio;
    const decide = p.distanciaDecision ?? p.alcanceAtaque;
    if (d > decide) {
      this._avanzarHacia(E, M, p.distanciaPreferida, dt);
      return;
    }
    if (E.recarga <= 0 && Math.abs(deltaAngulo(E.yaw, yawDe(resta(M.pos, E.pos)))) < 35) {
      // La rama de estrafe del arbol se come el ciclo entero: ni ataca ni recarga
      // mientras rodea.
      if (this.azar.probabilidad(p.probabilidadRodeo ?? 0)) {
        E.rodeando = p.duracionRodeo ?? 0;
        E.sentidoRodeo = this.azar.probabilidad(0.5) ? 1 : -1;
        return;
      }
      this._iniciarAtaque(E, { ...p.ataque, alcance: p.alcanceAtaque, dano: this._danoDe(E) });
    }
  }

  _pasoArquero(E, dt) {
    const M = this.malakh;
    const p = E.perfil;
    const d = dist(E.pos, M.pos);
    const ve = hayVision(E.pos, E.cota, M.pos, M.cota, this.coberturas, this.cal.malakh.alturaOjos);

    // Retirada con presupuesto. Un arquero que retrocede sin limite contra un
    // Malakh que tiene que esquivar flechas produce tablas eternas: los dos
    // movimientos se cancelan y la arena no se cierra nunca. Agotado el
    // presupuesto se planta y dispara a bocajarro.
    if (d < p.distanciaMinima && (E.tRetirada || 0) < (p.segundosDeRetirada ?? Infinity)) {
      E.tRetirada = (E.tRetirada || 0) + dt;
      this._mover(E, escala(normaliza(resta(E.pos, M.pos)), this._velocidadDe(E) * dt));
      return;
    }
    if (d > p.distanciaMinima * 1.4) E.tRetirada = 0;   // recupera el presupuesto al abrir hueco
    if (!ve) {
      const hacia = normaliza(resta(M.pos, E.pos));
      this._mover(E, escala({ x: -hacia.y, y: hacia.x }, this._velocidadDe(E) * 0.6 * dt));
      return;
    }
    if (d > p.alcanceAtaque) { this._avanzarHacia(E, M, p.distanciaPreferida, dt); return; }
    if (E.recarga <= 0) {
      this._iniciarAtaque(E, { ...p.ataque, alcance: p.alcanceAtaque, dano: this._danoDe(E), proyectil: true, velocidad: p.velocidadProyectil });
    }
  }

  // ---------------------------------------------------------------- ataques

  _iniciarAtaque(A, perfil) {
    A.estado = ESTADOS.ANTICIPACION;
    A.tEstado = 0;
    A.accion = { ...perfil, yaGolpeo: false };
    // Embestida: el ataque adelanta el cuerpo antes de golpear.
    //
    // O TODOS O NINGUNO — esta es la regla, y saltarsela costo una tarde.
    //
    // El aviso original decia "no uses embestida, el avance ya esta dentro de
    // `alcance`", y era cierto MIENTRAS `alcance` fuera el numero completo (243 de la
    // espada, 245 del Lancero: desde donde el atacante se compromete hasta la punta,
    // root motion incluido). Anadir embestida encima contaba el avance dos veces.
    //
    // El 25/08 se partio en dos el de Malakh (327 instantaneo + 106 de avance) para
    // que el simulador MOVIERA el cuerpo, que era lo que faltaba. Pero las armas de
    // armas.json se quedaron enteras, con `alcance` 448 y sin embestida — o sea que
    // cada arma del suelo cobraba 121 cm de alcance instantaneo sobre la espada, un
    // regalo que no sale de ninguna medicion. Eso, y no sus verbos, era TODO el
    // efecto que la matriz atribuia a los counters: al partirlas igual, Cierre paso
    // de -61% a -7% y Mole de -57% a +8%.
    //
    // Asi que la regla no es "no uses embestida": es que `alcance` y `embestida`
    // tienen que estar partidos IGUAL en los dos bandos y en todas las armas. Si
    // tocas uno, tocalos todos.
    if (perfil.embestida) {
      const blanco = A.bando === 'malakh' ? this.agente(A.objetivoId) : this.malakh;
      if (blanco && blanco.estado !== ESTADOS.MUERTO) {
        const hueco = dist(A.pos, blanco.pos) - (blanco.radio || 0) - perfil.alcance * 0.6;
        A.accion.embestidaRestante = Math.max(0, Math.min(perfil.embestida, hueco));
        A.accion.embestidaDir = normaliza(resta(blanco.pos, A.pos));
      } else {
        A.accion.embestidaRestante = 0;
      }
    }
    if (A.bando === 'malakh') {
      A.stamina -= perfil.costeStamina || 0;
      A.tUltimoGasto = this.t;
    }
    this._evento('ataque', {
      agente: A.id,
      pesado: !!perfil.esPesado,
      arma: perfil.familia || null,
      objetivo: A.bando === 'malakh' ? A.objetivoId : 'malakh'
    });
  }

  _avanzarAtaque(A, dt) {
    const a = A.accion;
    const t = A.tEstado;
    const ini = a.impacto, fin = a.impacto + (a.ventana ?? 0.12);

    if (t < ini) A.estado = ESTADOS.ANTICIPACION;
    else if (t <= fin) A.estado = ESTADOS.ACTIVO;
    else A.estado = ESTADOS.RECUPERACION;

    // El avance se gasta durante la anticipacion, y va por _mover: muros, barandillas
    // y limites de arena valen igual que andando.
    if (a.embestidaRestante > 0 && t < ini && ini > 0) {
      const paso = Math.min(a.embestidaRestante, (a.embestida / ini) * dt);
      this._mover(A, escala(a.embestidaDir, paso));
      a.embestidaRestante -= paso;
    }

    if (A.estado === ESTADOS.ACTIVO && !a.yaGolpeo) {
      a.yaGolpeo = true;
      if (a.tipo === 'zona') this._plantarZona(A, a);
      else if (a.tipo === 'aoe') this._golpeEnArea(A, a);
      else if (a.proyectil || a.tipo === 'proyectil') this._lanzarProyectil(A, a);
      else this._resolverGolpeCuerpoACuerpo(A, a);

      if (A.bando === 'malakh' && a.gastaMunicion) {
        const ev = gastarRecurso(A, a.gastaMunicion);
        if (ev) this._evento(ev.tipo, { agente: A.id, arma: ev.arma });
      }
    }

    if (t >= a.duracion) {
      if (A.bando === 'enemigo') A.recarga = A.perfil.recarga;
      this._aLibre(A);
    }
  }

  _resolverGolpeCuerpoACuerpo(A, a) {
    const candidatos = A.bando === 'malakh'
      ? this.enemigosEnEscena()
      : [this.malakh];

    let alcanzado = false;
    for (const O of candidatos) {
      if (Math.abs((O.cota || 0) - (A.cota || 0)) > 120) continue;
      if (dist(A.pos, O.pos) - O.radio > a.alcance) continue;
      if (Math.abs(deltaAngulo(A.yaw, yawDe(resta(O.pos, A.pos)))) > (a.arco || 90) / 2) continue;
      this._aplicarDano(O, a.dano, A, a);
      alcanzado = true;
      if (A.bando === 'malakh' && !a.multiObjetivo) break;
    }
    if (A.bando === 'malakh') {
      if (alcanzado) A.golpesAsestados += 1; else A.golpesFallados += 1;
    }
  }

  _golpeEnArea(A, a) {
    const candidatos = A.bando === 'malakh'
      ? this.enemigosEnEscena()
      : [this.malakh];
    let alcanzado = false;
    for (const O of candidatos) {
      if (Math.abs((O.cota || 0) - (A.cota || 0)) > 120) continue;
      if (dist(A.pos, O.pos) - O.radio > a.radio) continue;
      this._aplicarDano(O, a.dano, A, a);
      alcanzado = true;
    }
    if (A.bando === 'malakh') { if (alcanzado) A.golpesAsestados += 1; else A.golpesFallados += 1; }
  }

  _plantarZona(A, a) {
    this.zonas.push({
      pos: { ...A.pos },
      radio: a.radio,
      ttl: a.duracionZona,
      factorDano: a.factorDanoEnemigo ?? 1,
      factorVelocidad: a.factorVelocidadEnemigo ?? 1
    });
    this._evento('zona', { agente: A.id, radio: a.radio, duracion: a.duracionZona });
  }

  _pasoZonas(dt) {
    this.zonas = this.zonas.filter(z => (z.ttl -= dt) > 0);
  }

  /**
   * Daño de un enemigo, aura incluida.
   *
   * `BP_DA_AuraComponent` (contrato §1.2, en Unreal desde el 23/08/2026):
   * mientras el portador viva, todo aliado dentro de `RadioAura` lleva un
   * modificador de `Stat.Damage`. Al morir el portador, o al salirse del radio,
   * se retira solo. Dos portadores apilan, porque son dos componentes.
   *
   * Se evalua al ARRANCAR el ataque. El motor lo reevalua en cada pasada, pero
   * entre arrancar y golpear pasan ~0,6 s y nadie cruza 1200 cm en eso.
   *
   * El portador no se buffea a si mismo: el componente recorre aliados.
   */
  _danoDe(E) {
    const aura = this.cal.aura;
    if (!aura) return E.perfil.dano;
    let extra = 0;
    for (const P of this.enemigos) {
      if (P === E || P.arquetipo !== aura.arquetipo) continue;
      if (P.estado === ESTADOS.MUERTO || !P.presente) continue;
      if (dist(P.pos, E.pos) > aura.radio) continue;
      extra += aura.bonificacion;
    }
    return E.perfil.dano + extra;
  }

  _modificadorZona(agente, campo) {
    let f = 1;
    for (const z of this.zonas) {
      if (dist(agente.pos, z.pos) <= z.radio) f *= z[campo];
    }
    return f;
  }

  _velocidadDe(A) {
    const base = A.perfil.velocidad;
    return A.bando === 'enemigo' ? base * this._modificadorZona(A, 'factorVelocidad') : base;
  }

  _lanzarProyectil(A, a) {
    const objetivo = A.bando === 'malakh' ? this.agente(A.objetivoId) : this.malakh;
    if (!objetivo || objetivo.estado === ESTADOS.MUERTO) return;

    // SE APUNTA A DONDE VA A ESTAR, NO A DONDE ESTA. Es la misma formula que el motor:
    // posicion del objetivo mas su velocidad por el tiempo de vuelo (ver
    // `GetLocAndDirToSpawnArrow`). Sin esto el simulador apuntaba al sitio que el blanco
    // acababa de dejar: con la flecha a 3500 y Malakh a 400, en los 0,4 s de vuelo de un
    // tiro de 1.400 cm se movia 170 cm, y su capsula mide 42 de radio. Medido en la
    // receta, 300 partidas: el Arquero acertaba el 9% de sus disparos (0,4 impactos por
    // partida de 4,8 tiros) mientras que en el motor, jugado, metio TRES en 18 s. No era
    // la esquiva —solo 0,2 esquivas por partida con una flecha en vuelo— era la punteria.
    const vel = a.velocidad || 3500;
    const tv = dist(objetivo.pos, A.pos) / vel;
    const v = objetivo._vel || { x: 0, y: 0 };
    const prediccion = { x: objetivo.pos.x + v.x * tv, y: objetivo.pos.y + v.y * tv };

    this.proyectiles.push({
      pos: { ...A.pos },
      cota: A.cota,
      dir: normaliza(resta(prediccion, A.pos)),
      velocidad: a.velocidad || 3500,
      dano: a.dano,
      aturde: !!a.aturde,
      rompeGuardia: !!a.rompeGuardia,
      origenId: A.id,
      bando: A.bando,
      vida: (a.alcance || 2600) / (a.velocidad || 3500) + 0.2
    });
    this._evento('disparo', { agente: A.id, arma: a.familia || null, descarte: !!a.esDescarte });
    if (A.bando === 'malakh') A.golpesAsestados += 0;   // el impacto lo cuenta el proyectil
  }

  _pasoProyectiles(dt) {
    const vivos = [];
    for (const p of this.proyectiles) {
      const antes = { ...p.pos };
      p.pos = suma(p.pos, escala(p.dir, p.velocidad * dt));
      p.vida -= dt;

      let parado = false;
      for (const c of this.coberturas) {
        if (!c.bloqueaVision) continue;
        const cima = (c.cota || 0) + (c.altura || 0);
        if (cima <= p.cota + this.cal.malakh.alturaOjos - 10) continue;
        if (segmentoCortaPoligono(antes, p.pos, c.poli)) { parado = true; break; }
      }
      if (parado) { this._evento('proyectilParado', { origen: p.origenId }); continue; }

      const objetivos = p.bando === 'malakh'
        ? this.enemigosEnEscena()
        : [this.malakh];
      let impacto = false;
      for (const O of objetivos) {
        if (O.estado === ESTADOS.MUERTO) continue;
        if (dist(p.pos, O.pos) > O.radio + 15) continue;
        this._aplicarDano(O, p.dano, this.agente(p.origenId),
                          { aturde: p.aturde, rompeGuardia: p.rompeGuardia, proyectil: true });
        impacto = true;
        break;
      }
      if (impacto) continue;
      if (p.vida > 0) vivos.push(p);
    }
    this.proyectiles = vivos;
  }

  _aplicarDano(O, cantidad, origen, a = {}) {
    if (O.estado === ESTADOS.MUERTO) return;

    // Al que le pegas, despierta — el, no su oleada. Asi el jugador puede ir a
    // buscar de uno en uno a los que esperan, que es una tactica legitima y no
    // un agujero: le cuesta el desplazamiento y le junta a los suyos igual.
    if (O.bando === 'enemigo' && !O.activo) {
      O.activo = true;
      this._evento('despierta', { agente: O.id, oleada: O.oleadaId });
      this._alertar(O);
    }

    // i-frames de la esquiva
    if (O.bando === 'malakh' && O.estado === ESTADOS.ESQUIVA) {
      const e = this.cal.malakh.esquiva;
      if (O.tEstado >= e.iframeInicio && O.tEstado <= e.iframeFin) {
        O.esquivasLogradas += 1;
        this._evento('esquivado', { agente: O.id, de: origen?.id });
        return;
      }
    }

    let dano = cantidad;
    let bloqueado = false;

    // EL ESCUDO ENCAJA (§4, «Escudo Celestial»): cubre cuando TU no puedes.
    //
    // Esto salio de una medida que desmintio dos diseños seguidos. Contra un
    // arquero, «avanzar bloqueando» daba +35% de daño (atacaba el sintoma
    // equivocado: las flechas del trayecto ya se esquivan). Y la segunda
    // hipotesis —que te matan las de bocajarro mientras estas clavado
    // atacando— tambien era falsa. Instrumentado el receptor, el reparto real
    // de las flechas que ENTRAN es este:
    //
    //     estado de Malakh al recibir flecha: { esquiva: 2 }
    //
    // El 100%. Rueda a tiempo, pero los i-frames cubren de 0,107 a 0,459 de un
    // rodillo que dura 0,917: el 60% del rodillo es vulnerable, y ahi es donde
    // aterrizan. No es que no se defienda — es que se defiende y aun asi le
    // rozan.
    //
    // Entonces el Escudo Celestial no hace invulnerable: HACE BARATOS LOS
    // ERRORES. Mitiga siempre que Malakh esta en un estado en el que no puede
    // levantar la guardia —rodando, atacando, bebiendo, recogiendo— porque el
    // escudo lo lleva en el brazo igual. Pasivo, sin pedirle nada al jugador.
    if (O.bando === 'malakh' && a.proyectil && O.estado !== ESTADOS.LIBRE) {
      const b = perfilBloqueo(O, this.cal, this.armas);
      if (b.mitigacionPasiva) {
        dano *= 1 - b.mitigacionPasiva;
        this._evento('encaja', { agente: O.id, de: origen?.id, estado: O.estado });
      }
    }

    // ARMADURA DE COMPROMISO — lo que hace viable un arma pesada.
    //
    // Medido: el Espadon hace exactamente lo que promete —cero golpes
    // bloqueados y un 45% mas de dps contra guardia— y AUN ASI recibe el doble
    // de castigo (4,0 golpes contra 2,0), porque cada animacion mas larga es una
    // ventana mas ancha para que te peguen. En este motor un arma lenta sin nada
    // que la compense es estrictamente peor, por buena que sea su propiedad.
    //
    // Es el mismo problema que resuelve el hyperarmor de cualquier action RPG:
    // plantas los pies, encajas el golpe y sigues. Sin esto, «pesado» no es una
    // fantasia jugable, es una trampa.
    // Solo contra el melé, y no es un parche: plantar los pies te deja encajar
    // un espadazo y seguir, no te salva de una flecha en la cara. Sin esa
    // condicion el Espadon salia el mejor de CUATRO de los cinco casos —incluido
    // el arquero— y entonces deja de ser un counter para ser un arma mejor.
    if (O.bando === 'malakh' && !a.proyectil && O.accion?.armaduraDeCompromiso &&
        (O.estado === ESTADOS.ANTICIPACION || O.estado === ESTADOS.ACTIVO ||
         O.estado === ESTADOS.RECUPERACION)) {
      dano *= 1 - O.accion.armaduraDeCompromiso;
    }

    // Guardia de Malakh. El Escudo Celestial la mejora mucho y ademas para flechas.
    if (O.bando === 'malakh' && O.bloqueando && origen) {
      const b = perfilBloqueo(O, this.cal, this.armas);
      const puedeParar = !a.proyectil || b.paraProyectiles;
      const frontal = Math.abs(deltaAngulo(O.yaw, yawDe(resta(origen.pos, O.pos)))) < b.arco / 2;
      if (frontal && puedeParar) {
        if (O.stamina >= b.costeStaminaPorGolpe) {
          O.stamina -= b.costeStaminaPorGolpe;
          O.tUltimoGasto = this.t;
          dano *= 1 - b.reduccion;
          bloqueado = true;
        } else {
          O.stamina = 0; O.aguante = 0; O.tUltimoGasto = this.t;
          this._evento('guardiaRota', { agente: O.id, de: origen.id });
        }
      }
    }

    // Guardia del enemigo. El espadon y el bash la ignoran (guard break).
    const guardia = O.perfil?.guardia || 0;
    if (!a.rompeGuardia && guardia > 0 && origen) {
      const frontal = Math.abs(deltaAngulo(O.yaw, yawDe(resta(origen.pos, O.pos)))) < 70;
      if (frontal && this.azar.probabilidad(guardia)) {
        dano *= 1 - (O.perfil.reduccionGuardia ?? 0.75);
        bloqueado = true;
      }
    }

    if (O.bando === 'enemigo') dano *= this._modificadorZona(O, 'factorDano');

    const factor = this.cal.reglas.factorArmadura || 0;
    if (factor > 0) dano = Math.max(1, dano - factor);

    // EMPUJE. Estaba MEDIDO en la calibracion desde el 23/08 (20 cm el ligero,
    // 45 el pesado) y el simulador no lo miraba. Importa mas de lo que parece:
    // en un juego donde los enemigos corren a 600 y Malakh a 400, apartar es la
    // UNICA forma de fabricar espacio. Retroceder no existe.
    //
    // Y a diferencia de aturdir, no invita a la codicia: al que empujas no se
    // queda ahi ofreciendote la nuca, se levanta lejos y tiene que volver.
    if (a.empuje && !bloqueado && O.estado !== ESTADOS.MUERTO && origen && O !== origen) {
      const fuera = normaliza(resta(O.pos, origen.pos));
      if (largo(fuera) > 0) this._mover(O, escala(fuera, a.empuje));
    }

    O.hp -= dano;
    // Cuando le entro el ultimo golpe. Un golpe que no aturde no deja estado, y
    // sin esto ni la planta ni la 3D pueden enseñar que a alguien le estan dando.
    O.tUltimoGolpe = this.t;
    O.ultimoGolpeBloqueado = bloqueado;
    if (O.bando === 'malakh') O.danoRecibido += dano;
    if (origen && origen.bando === 'enemigo') origen.danoInfligido += dano;

    this._evento('golpe', {
      de: origen?.id, a: O.id, dano: +dano.toFixed(1), bloqueado,
      arma: a.familia || null, descarte: !!a.esDescarte,
      hpRestante: Math.max(0, +O.hp.toFixed(1))
    });

    // LA LANZA PARA (§4, «Lanza del Alba»).
    //
    // Su premisa de diseño era el alcance, y el alcance NO EXISTE: 245 cm
    // contra los 241 de la espada, porque los cuatro de melé comparten
    // animacion. Y tampoco se puede espaciar a nadie, que corren a 600 y
    // Malakh a 400. Lo que si puede hacer un asta es NEGAR EL TURNO: clavarla
    // en quien viene lanzado o en quien esta levantando el arma.
    //
    // Es condicional a proposito. Aturdir siempre seria un arma mejor; aturdir
    // solo a quien cierra o amaga es una HERRAMIENTA, y hay que saber cuando
    // usarla.
    let interrumpe = false;
    if (a.interrumpe && O.bando === 'enemigo' && origen) {
      const amagando = O.estado === ESTADOS.ANTICIPACION;
      const cerrando = O.estado === ESTADOS.LIBRE &&
        dist(O.pos, origen.pos) - (origen.radio || 0) > (O.perfil?.alcanceAtaque ?? 0);
      interrumpe = amagando || cerrando;
      if (interrumpe) this._evento('interrumpido', { agente: O.id, de: origen.id });
    }

    if (!bloqueado) {
      O.aguante -= dano * (a.esPesado || a.aturde || interrumpe ? 2 : 1);
      if (a.aturde || interrumpe) O.aguante = Math.min(O.aguante, 0);
      if (O.aguante <= 0 && O.estado !== ESTADOS.MUERTO) {
        O.aguante = O.aguanteMax;
        O.estado = ESTADOS.ATURDIDO;
        O.tEstado = 0;
        O.accion = { duracion: this.cal.malakh.reaccionGolpe };
        if (O.bando === 'enemigo') O.recarga = Math.max(O.recarga, O.perfil.recarga * 0.5);
        this._evento('aturdido', { agente: O.id });
      }
    }

    if (O.hp <= 0) {
      O.hp = 0;
      O.estado = ESTADOS.MUERTO;
      O.accion = null;
      if (O.bando === 'enemigo') {
        O.tMuerte = this.t;
        this._evento('baja', { agente: O.id, arquetipo: O.arquetipo, t: +this.t.toFixed(2), drop: O.drop });
        this._quizaSoltarArma(O);
      }
    }
  }

  // ------------------------------------------------------------------- drops

  _quizaSoltarArma(E) {
    const familia = E.perfil.arma;
    if (!familia || !this.armas.familias[familia]) return;
    if (!decideDrop(E, familia, this.armas)) {
      this._evento('sinDrop', { agente: E.id, ranura: E.drop });
      return;
    }
    const drop = {
      id: `drop_${++this._contadorDrops}`,
      familia,
      pos: { ...E.pos },
      cota: E.cota,
      ttl: this.armas.reglas.ttlEnSuelo,
      origenId: E.id
    };
    this.drops.push(drop);
    this._evento('suelta', { agente: E.id, arma: familia, drop: drop.id, ranura: E.drop });
  }

  _pasoDrops(dt) {
    const vivos = [];
    for (const d of this.drops) {
      d.ttl -= dt;
      if (d.ttl > 0) vivos.push(d);
      else this._evento('dropExpirado', { drop: d.id, arma: d.familia });
    }
    this.drops = vivos;
  }

  // -------------------------------------------------------------- movimiento

  _avanzarHacia(A, objetivo, distanciaParada, dt) {
    const ruta = this._rutaHacia(A, objetivo);
    const destino = ruta.punto;
    const parada = ruta.intermedio ? 0 : distanciaParada;
    const radio = ruta.intermedio ? 0 : (objetivo.radio || 0);
    const d = dist(A.pos, destino) - radio;
    if (d <= parada) return;

    let dir = normaliza(resta(destino, A.pos));

    // EL RODEO NO SE APLICA CUANDO YA VAMOS A UN PUNTO INTERMEDIO. Si `_rutaHacia`
    // mando a la rampa, la ruta ya esta resuelta y el obstaculo en medio es
    // normalmente LA PROPIA PLATAFORMA sobre la que estamos: rodearla manda a un
    // vertice fuera del rectangulo, y la barandilla de `_mover` lo rechaza, asi que el
    // agente se queda clavado. Medido: Malakh quieto en (1280,1000) sobre el balcon
    // sur, con el vertice fijo en (1047,652) y velocidad cero.
    let bloqueo = ruta.intermedio ? null : this._coberturaEnMedio(A.pos, destino);
    // Un rodeo que acaba de demostrar que no mueve no se vuelve a intentar en 2 s.
    if (bloqueo && A._rodeoVetado && A._rodeoVetado.id === bloqueo.id &&
        this.t < A._rodeoVetado.hasta) bloqueo = null;
    if (bloqueo) {
      // MEMORIA DE RODEO. Sin ella la eleccion avariciosa se recalcula cada tick y hace
      // ping-pong: al acercarse a la esquina elegida, esa esquina cae dentro del radio
      // de "ya estoy" de `_verticeDeRodeo`, se descarta, y la mas barata pasa a ser la
      // del otro extremo del muro. Medido el 25/08 con la calibracion escalada: Malakh
      // oscilando entre x=-362 y x=-349 durante 180 s con un Escudero vivo a 655 cm.
      //
      // Lo que faltaba no era una ruta mejor —la buena existia: bordear el muro por
      // debajo en linea recta— sino COMPROMETERSE con ella. Se recalcula solo cuando
      // cambia el obstaculo o cuando ya se ha llegado al vertice.
      const llegado = A._rodeo && dist(A.pos, A._rodeo.punto) < 60;
      if (!A._rodeo || A._rodeo.id !== bloqueo.id || llegado) {
        const vertice = this._verticeDeRodeo(A.pos, destino, bloqueo);
        A._rodeo = vertice ? { id: bloqueo.id, punto: vertice } : null;
      }
      if (A._rodeo) dir = normaliza(resta(A._rodeo.punto, A.pos));
    } else {
      A._rodeo = null;
    }
    A.yaw = giraHacia(A.yaw, yawDe(dir), (A.perfil.velocidadGiro || 360) * dt);

    // UN RODEO QUE NO TE MUEVE NO ES UN RODEO. La memoria de arriba arregla el
    // ping-pong pero abre un fallo peor: si el vertice elegido cae FUERA de la arena,
    // `_mover` lo rechaza entero, el agente no avanza ni un centimetro, y como nunca
    // llega al vertice tampoco recalcula. Se queda clavado para siempre.
    //
    // Medido con el alcance 327: el Escudero de la primera oleada 30 s inmovil en
    // (-2200,-85) —pegado al muro oeste— con Malakh vivo a 470 cm y ambos `libre`.
    // De ahi salian la mayoria de los 77 combates que agotaban el reloj.
    //
    // El arreglo es medir, no adivinar: si tras moverse sigue donde estaba, se veta
    // ese rodeo y se reintenta RECTO en el mismo tick. Recto contra un muro si
    // funciona, porque `_mover` desliza por el eje que si cabe.
    const antes = A.pos;
    this._mover(A, escala(dir, this._velocidadDe(A) * dt));
    if (A._rodeo && dist(antes, A.pos) < 0.01) {
      A._rodeoVetado = { id: A._rodeo.id, hasta: this.t + 2 };
      A._rodeo = null;
      const recto = normaliza(resta(destino, A.pos));
      A.yaw = giraHacia(A.yaw, yawDe(recto), (A.perfil.velocidadGiro || 360) * dt);
      this._mover(A, escala(recto, this._velocidadDe(A) * dt));
    }
  }

  /**
   * A donde hay que ir de verdad para llegar al objetivo.
   *
   * OTRO QUE ESTABA ROTO. La version anterior decidia por DIFERENCIA DE COTA: si
   * los dos estaban a la misma altura, camino recto. Con dos torres gemelas eso
   * es falso —para ir de una a otra hay que bajar y volver a subir— y el
   * resultado era que Malakh se quedaba varado en la torre que acababa de
   * limpiar, apretandose contra la barandilla mientras el arquero de la torre de
   * enfrente le mataba a placer. Medido: 130 s de partida y muerte con los cinco
   * enemigos a la vista.
   *
   * Ahora la pregunta es EN QUE PLATAFORMA esta cada uno. Distinta plataforma =
   * hay que bajar de la mia (o subir a la suya), aunque midan lo mismo.
   */
  _rutaHacia(A, objetivo) {
    const plataformaDe = (pos, cota) => ((cota || 0) <= 50 ? null
      : this.plataformas.find(p => dentroDeRect(pos, p) &&
          Math.abs((p.cota || 0) - (cota || 0)) <= 50) || null);

    const miPlat = plataformaDe(A.pos, A.cota);
    const suPlat = plataformaDe(objetivo.pos, objetivo.cota);
    if (miPlat === suPlat) return { punto: objetivo.pos, intermedio: false };

    // Primero se baja de la propia; solo si no estoy en ninguna, se sube a la suya.
    const plat = miPlat || suPlat;
    const subiendo = !miPlat;
    if (!plat || !plat.accesos || !plat.accesos.length) {
      return { punto: objetivo.pos, intermedio: false };
    }

    // Una rampa tiene dos extremos: `desde` al pie y `hasta` arriba. Para subir
    // se va al pie; para bajar, al remate de arriba. Antes era un punto suelto y
    // no se sabia por donde se entraba.
    let mejor = null, mejorD = Infinity;
    for (const r of plat.accesos) {
      const boca = subiendo ? r.desde : r.hasta;
      if (!boca) continue;
      const d = dist(A.pos, boca);
      if (d < mejorD) { mejorD = d; mejor = { boca, rampa: r }; }
    }
    if (!mejor) return { punto: objetivo.pos, intermedio: false };

    // Al pisar la boca, se recorre la rampa. No se simula la subida paso a paso:
    // lo que importa del encuentro es cuanto se tarda en llegar, y eso ya lo
    // cobra el rodeo hasta la boca.
    if (mejorD < 120) {
      A.cota = subiendo ? plat.cota : 0;
      A.pos = { ...(subiendo ? mejor.rampa.hasta : mejor.rampa.desde) };
      return { punto: objetivo.pos, intermedio: false };
    }
    return { punto: mejor.boca, intermedio: true };
  }

  _coberturaEnMedio(a, b) {
    for (const c of this.coberturas) {
      if (!c.bloqueaPaso) continue;
      if (segmentoCortaPoligono(a, b, c.poli)) return c;
    }
    return null;
  }

  /**
   * Por que esquina rodear un muro.
   *
   * ESTO ESTABA ROTO Y NADIE LO SABIA. La version anterior cogia la esquina de
   * menor coste total sin mirar si ya estabas en ella: al llegar al vertice, esa
   * misma esquina seguia siendo la mas barata (coste de ida ~0), asi que la
   * direccion era un vector de ocho centimetros y Malakh se quedaba temblando en
   * la punta del muro hasta que saltaba el watchdog. Medido: con UN muro en el
   * camino, 180 s de partida y cero daño, porque no llegaba nunca.
   *
   * Es la razon por la que "poner cobertura" nunca habia funcionado como palanca
   * de diseño, y el §6.16 —cortarle la vision al Arquero ES la respuesta— no se
   * podia ni probar.
   *
   * Ahora: se descarta la esquina en la que ya estas, y se prefiere una a la que
   * se pueda ir en linea recta. Sigue siendo un rodeo avaricioso, no una malla de
   * navegacion: con un laberinto no basta.
   */
  _verticeDeRodeo(desde, hasta, cobertura) {
    // Radio de "ya estoy en esa esquina". Estuvo en 120 y era demasiado: al
    // acercarse a la esquina buena se descartaba antes de haberla doblado, y la
    // unica que quedaba era la del otro extremo del muro. Malakh se pasaba la
    // partida yendo y viniendo entre las dos puntas del balcon. Con un radio del
    // orden de su capsula, la esquina deja de contar solo cuando de verdad esta
    // encima y ya la ha rebasado.
    const YA_ESTOY = 45;
    let mejor = null, mejorCoste = Infinity;
    let respaldo = null, respaldoCoste = Infinity;
    for (const p of cobertura.poli) {
      const fuera = empujaFuera(p, cobertura.poli, 90);
      const salida = dist(desde, fuera);
      if (salida < YA_ESTOY) continue;
      const coste = salida + dist(fuera, hasta);
      if (!segmentoCortaPoligono(desde, fuera, cobertura.poli)) {
        if (coste < mejorCoste) { mejorCoste = coste; mejor = fuera; }
      } else if (coste < respaldoCoste) {
        respaldoCoste = coste; respaldo = fuera;
      }
    }
    return mejor || respaldo;
  }

  _mover(A, delta) {
    let p = suma(A.pos, delta);

    // Quien esta en alto se queda en alto: un balcon tiene barandilla.
    if ((A.cota || 0) > 50) {
      const plat = this.plataformas.find(pl =>
        Math.abs((pl.cota || 0) - A.cota) <= 50 && dentroDeRect(A.pos, pl));
      if (plat && !dentroDeRect(p, plat)) {
        const soloX = { x: p.x, y: A.pos.y }, soloY = { x: A.pos.x, y: p.y };
        if (dentroDeRect(soloX, plat)) p = soloX;
        else if (dentroDeRect(soloY, plat)) p = soloY;
        else p = A.pos;
      }
    }

    for (const c of this.coberturas) {
      if (!c.bloqueaPaso) continue;
      if ((c.cota || 0) + (c.altura || 0) <= (A.cota || 0) + 20) continue;
      if (dentroDePoligono(p, c.poli)) p = empujaFuera(p, c.poli, A.radio + 5);
    }

    // EL MURO SE RECORTA, NO SE REVIERTE, y esto no es cosmetica: revertir es una
    // TRAMPA DE UN SOLO SENTIDO. `_separarAgentes` y `empujaFuera` mueven agentes sin
    // pasar por aqui, asi que uno puede acabar UNOS MILIMETROS fuera del rectangulo.
    // A partir de ese momento las tres opciones de la version antigua —los dos ejes
    // sueltos y quedarse— caen todas fuera, y el agente se queda inmovil PARA SIEMPRE
    // sin poder volver a entrar.
    //
    // Medido con el alcance 327: el Escudero en x=-2200.1 (el muro esta en -2200),
    // pidiendo (0,+6.17) cada tick durante 30 s y recibiendo (0,0), con Malakh vivo a
    // 475 cm. La mayoria de los 77 combates que agotaban el reloj eran esto.
    //
    // Recortar cada eje a su rango cumple las dos cosas: desliza a lo largo del muro
    // igual que antes, y a quien este fuera lo devuelve dentro en el primer paso.
    const bb = this.enc.arena.bounds;
    p = {
      x: Math.min(Math.max(p.x, bb.min.x), bb.max.x),
      y: Math.min(Math.max(p.y, bb.min.y), bb.max.y)
    };
    A.pos = p;
  }

  _separarAgentes() {
    const vivos = this.agentes.filter(a => a.estado !== ESTADOS.MUERTO && a.presente !== false);
    for (let i = 0; i < vivos.length; i++) {
      for (let j = i + 1; j < vivos.length; j++) {
        const a = vivos[i], b = vivos[j];
        if (Math.abs((a.cota || 0) - (b.cota || 0)) > 100) continue;
        const min = a.radio + b.radio;
        const d = dist(a.pos, b.pos);
        if (d >= min || d < 1e-3) continue;
        const empuje = escala(normaliza(resta(b.pos, a.pos)), (min - d) / 2);
        a.pos = resta(a.pos, empuje);
        b.pos = suma(b.pos, empuje);
      }
    }
    // Separar puede meter a alguien DENTRO de un muro: el empujon de arriba no
    // sabe nada de geometria. Sin este repaso, dos agentes apretandose contra un
    // pilar acababan dentro de el, y en la vista 3D se veia al personaje metido
    // en la caja. El solido gana siempre.
    for (const a of vivos) this._sacarDeSolidos(a);
  }

  _sacarDeSolidos(A) {
    for (const c of this.coberturas) {
      if (!c.bloqueaPaso) continue;
      if ((c.cota || 0) + (c.altura || 0) <= (A.cota || 0) + 20) continue;
      if (dentroDePoligono(A.pos, c.poli)) A.pos = empujaFuera(A.pos, c.poli, A.radio + 5);
    }
  }

  // ------------------------------------------------------------------ apoyo

  _aLibre(A) { A.estado = ESTADOS.LIBRE; A.tEstado = 0; A.accion = null; }

  agente(id) { return this.agentes.find(a => a.id === id) || null; }

  /** Vivos, TODOS: incluye a los que esperan su oleada. Es lo que cierra la arena. */
  enemigosVivos() { return this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO); }

  /** Los que estan plantados en la arena, activos o esperando. Reciben golpes. */
  enemigosEnEscena() { return this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO && e.presente); }

  /** Los que estan peleando ahora mismo. Es contra quien decide una politica. */
  enemigosActivos() { return this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO && e.activo); }

  /** Oleadas que todavia no han entrado. */
  oleadasPendientes() { return (this.oleadas || []).filter(o => !o.activada); }

  /**
   * ¿Se esta ALEJANDO el objetivo? Se mide sobre la distancia, no sobre el arquetipo:
   * un Lancero que rodea tambien se aleja, y un Arquero acorralado contra la
   * barandilla ya no.
   *
   * VA SUAVIZADO, Y ESTO NO ES COSMETICA. Con un booleano por tick, la distancia de
   * parada saltaba entre 157 y 235 en ticks alternos y Malakh se pasaba el combate
   * retrocediendo y avanzando en el sitio: 1.8 ataques por combate y 1% de victorias
   * contra el Arquero. Una media movil de la velocidad radial lo deja quieto.
   */
  _seAleja(A, O, dt) {
    if (!O) { A._velRadial = 0; return false; }
    const d = dist(A.pos, O.pos);
    const mismo = A._idObjetivo === O.id;
    if (mismo && A._distObjetivo != null && dt > 0) {
      const v = (d - A._distObjetivo) / dt;
      A._velRadial = 0.85 * (A._velRadial || 0) + 0.15 * v;
    } else {
      A._velRadial = 0;
    }
    A._distObjetivo = d;
    A._idObjetivo = O.id;
    return (A._velRadial || 0) > 40;   // cm/s: por debajo es baile, no retirada
  }

  _enAlcance(A, O, alcance) {
    if (Math.abs((O.cota || 0) - (A.cota || 0)) > 120) return false;
    return dist(A.pos, O.pos) - O.radio <= alcance;
  }

  amenazaInminente(anticipacion = 0.25) {
    const M = this.malakh;
    for (const E of this.enemigos) {
      if (E.estado === ESTADOS.MUERTO || !E.accion) continue;
      if (E.estado !== ESTADOS.ANTICIPACION) continue;
      const falta = E.accion.impacto - E.tEstado;
      if (falta < 0 || falta > anticipacion) continue;
      if (E.accion.proyectil) return { de: E, falta };
      if (dist(E.pos, M.pos) - M.radio <= E.accion.alcance * 1.15) return { de: E, falta };
    }
    for (const p of this.proyectiles) {
      if (p.bando === 'malakh') continue;
      const d = dist(p.pos, M.pos);
      if (d / p.velocidad <= anticipacion) return { de: this.agente(p.origenId), falta: d / p.velocidad, proyectil: p };
    }
    return null;
  }

  _evento(tipo, datos) {
    this.eventos.push({ t: +this.t.toFixed(3), tipo, ...datos });
  }

  _grabarFotograma() {
    const M = this.malakh;
    this.fotogramas.push({
      t: +this.t.toFixed(3),
      arma: M.temporal?.familia || null,
      offHand: M.offHand?.familia || null,
      municion: M.temporal?.municion ?? null,
      agentes: this.agentes.map(a => ({
        id: a.id, x: Math.round(a.pos.x), y: Math.round(a.pos.y),
        cota: a.cota, yaw: Math.round(a.yaw), hp: Math.round(a.hp),
        hpMax: a.hpMax,
        estado: a.bloqueando ? 'bloqueando' : a.estado,
        // Un enemigo de una oleada que no ha entrado: o no esta (`presente`), o
        // esta plantado sin hacer nada (`dormido`). Sin esto la reproduccion
        // enseña cinco peleando cuando pelean dos.
        presente: a.presente !== false,
        dormido: a.bando === 'enemigo' && !a.activo && a.estado !== ESTADOS.MUERTO,
        // Destello de impacto: dura un cuarto de segundo, lo justo para verse.
        golpeado: (this.t - (a.tUltimoGolpe ?? -99)) < 0.25,
        golpeBloqueado: !!a.ultimoGolpeBloqueado
      })),
      proyectiles: this.proyectiles.map(p => ({ x: Math.round(p.pos.x), y: Math.round(p.pos.y), bando: p.bando })),
      drops: this.drops.map(d => ({ x: Math.round(d.pos.x), y: Math.round(d.pos.y), familia: d.familia })),
      zonas: this.zonas.map(z => ({ x: Math.round(z.pos.x), y: Math.round(z.pos.y), radio: z.radio }))
    });
  }

  resultado() {
    const M = this.malakh;
    const bajas = this.eventos.filter(e => e.tipo === 'baja');
    const danoPorFuente = {};
    const danoPorArma = {};
    for (const ev of this.eventos) {
      if (ev.tipo !== 'golpe') continue;
      if (ev.a === 'malakh') {
        const f = this.agente(ev.de);
        const clave = f ? f.arquetipo : 'desconocido';
        danoPorFuente[clave] = (danoPorFuente[clave] || 0) + ev.dano;
      } else if (ev.de === 'malakh') {
        const clave = ev.arma || 'espada_base';
        danoPorArma[clave] = (danoPorArma[clave] || 0) + ev.dano;
      }
    }
    return {
      semilla: this.semilla,
      victoria: this.razonFin === 'victoria',
      razonFin: this.razonFin,
      tiempo: +this.t.toFixed(2),
      danoRecibido: +M.danoRecibido.toFixed(1),
      hpFinal: Math.max(0, +M.hp.toFixed(1)),
      pocionesBebidas: M.pocionesBebidas,
      golpesAsestados: M.golpesAsestados,
      golpesFallados: M.golpesFallados,
      esquivasLogradas: M.esquivasLogradas,
      enemigosVivos: this.enemigosVivos().length,
      ordenDeBajas: bajas.map(b => ({ id: b.agente, arquetipo: b.arquetipo, t: b.t })),
      armasRecogidas: M.armasRecogidas,
      descartesUsados: M.descartesUsados,
      maxDropsSimultaneos: this.maxDropsSimultaneos,
      maxEnemigosALaVez: this.maxEnemigosALaVez,
      oleadas: (this.oleadas || []).filter(o => !o.implicita).map(o => ({
        id: o.id, nombre: o.nombre, enemigos: o.enemigos.length,
        activada: o.activada, t: o.tActiva == null ? null : +o.tActiva.toFixed(2)
      })),
      danoPorFuente,
      danoPorArma,
      eventos: this.eventos,
      fotogramas: this.fotogramas
    };
  }
}
