import * as THREE from 'three';

// Lightweight pooled particle bursts + combat telegraphs for the POC.
export class FX {
  constructor(scene) {
    this.scene = scene;
    this.bursts = [];
    this.telegraphs = [];
    this.arcs = [];
  }

  // Slash arc: a sweeping crescent that makes each swing readable.
  // dir flips the sweep for combo variety.
  slashArc(position, yaw, { color = 0xfff4d0, radius = 1.9, arc = Math.PI * 0.85, dur = 0.24, dir = 1 } = {}) {
    const geo = new THREE.RingGeometry(radius * 0.45, radius, 24, 1, 0, arc);
    geo.rotateX(Math.PI / 2); // lay flat (XZ plane)
    geo.rotateY(Math.PI / 2 - arc / 2); // center the crescent on local +Z
    const mat = new THREE.MeshBasicMaterial({
      color, transparent: true, opacity: 0.85, side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(position).add(new THREE.Vector3(0, 1.15, 0));
    mesh.rotation.y = yaw;
    this.scene.add(mesh);
    this.arcs.push({ mesh, t: 0, dur, dir });
  }

  // Feather + light dissolution when an angel dies (no human corpse — GDD rule).
  featherBurst(position, color = 0xfff4d0, count = 90, spread = 2.2) {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(count * 3);
    const vel = [];
    for (let i = 0; i < count; i++) {
      pos[i * 3] = position.x;
      pos[i * 3 + 1] = position.y + 1;
      pos[i * 3 + 2] = position.z;
      const a = Math.random() * Math.PI * 2;
      const r = Math.random() * spread;
      vel.push(new THREE.Vector3(Math.cos(a) * r, Math.random() * 3.2 + 1.2, Math.sin(a) * r));
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const mat = new THREE.PointsMaterial({
      color, size: 0.14, transparent: true, opacity: 1,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const pts = new THREE.Points(geo, mat);
    pts.frustumCulled = false;
    this.scene.add(pts);
    this.bursts.push({ pts, vel, life: 0, max: 1.6 });
  }

  // Purple-black corruptio motes
  corruptioBurst(position, count = 50) {
    this.featherBurst(position, 0x9e4dd8, count, 1.4);
  }

  // Ground telegraph for the Celestial Snare: gold glow -> white -> strike.
  spawnRayTelegraph(position, warnTime, onStrike) {
    const geo = new THREE.CircleGeometry(1.4, 24);
    const mat = new THREE.MeshBasicMaterial({
      color: 0xd4af37, transparent: true, opacity: 0.0, depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    const circle = new THREE.Mesh(geo, mat);
    circle.rotation.x = -Math.PI / 2;
    circle.position.copy(position).add(new THREE.Vector3(0, 0.06, 0));
    this.scene.add(circle);
    this.telegraphs.push({ circle, t: 0, warnTime, onStrike, struck: false, beam: null, beamT: 0 });
  }

  update(dt) {
    // Slash arcs: expand, sweep, fade
    for (let i = this.arcs.length - 1; i >= 0; i--) {
      const a = this.arcs[i];
      a.t += dt;
      const k = a.t / a.dur;
      a.mesh.scale.setScalar(0.7 + k * 0.6);
      a.mesh.rotation.y += dt * 7 * a.dir;
      a.mesh.material.opacity = 0.85 * (1 - k);
      if (k >= 1) {
        this.scene.remove(a.mesh);
        a.mesh.geometry.dispose();
        a.mesh.material.dispose();
        this.arcs.splice(i, 1);
      }
    }

    // Particle bursts
    for (let i = this.bursts.length - 1; i >= 0; i--) {
      const b = this.bursts[i];
      b.life += dt;
      const p = b.pts.geometry.attributes.position;
      for (let j = 0; j < b.vel.length; j++) {
        p.array[j * 3] += b.vel[j].x * dt;
        p.array[j * 3 + 1] += b.vel[j].y * dt;
        p.array[j * 3 + 2] += b.vel[j].z * dt;
        b.vel[j].y -= 2.2 * dt; // feathers settle
        b.vel[j].multiplyScalar(1 - 0.8 * dt);
      }
      p.needsUpdate = true;
      b.pts.material.opacity = 1 - b.life / b.max;
      if (b.life >= b.max) {
        this.scene.remove(b.pts);
        b.pts.geometry.dispose();
        b.pts.material.dispose();
        this.bursts.splice(i, 1);
      }
    }

    // Ray telegraphs
    for (let i = this.telegraphs.length - 1; i >= 0; i--) {
      const tg = this.telegraphs[i];
      tg.t += dt;
      if (!tg.struck) {
        const k = Math.min(tg.t / tg.warnTime, 1);
        tg.circle.material.opacity = 0.25 + k * 0.55;
        tg.circle.material.color.setHSL(0.12 - k * 0.12, 1.0, 0.55 + k * 0.4); // gold -> white
        tg.circle.scale.setScalar(1 + (1 - k) * 0.5);
        if (k >= 1) {
          tg.struck = true;
          const beamGeo = new THREE.CylinderGeometry(0.85, 1.1, 30, 12, 1, true);
          const beamMat = new THREE.MeshBasicMaterial({
            color: 0xfff8e0, transparent: true, opacity: 0.9,
            blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
          });
          tg.beam = new THREE.Mesh(beamGeo, beamMat);
          tg.beam.position.copy(tg.circle.position).add(new THREE.Vector3(0, 15, 0));
          this.scene.add(tg.beam);
          tg.onStrike && tg.onStrike(tg.circle.position);
        }
      } else {
        tg.beamT += dt;
        if (tg.beam) {
          tg.beam.material.opacity = Math.max(0, 0.9 - tg.beamT * 1.4);
          tg.beam.scale.x = tg.beam.scale.z = 1 + tg.beamT * 0.6;
        }
        tg.circle.material.opacity = Math.max(0, 0.8 - tg.beamT * 1.2);
        if (tg.beamT > 1.0) {
          this.scene.remove(tg.circle);
          if (tg.beam) this.scene.remove(tg.beam);
          this.telegraphs.splice(i, 1);
        }
      }
    }
  }
}
