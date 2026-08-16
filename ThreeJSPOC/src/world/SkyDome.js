import * as THREE from 'three';

// Pale-gold divine sky: gradient dome, veiled central light, drifting pollen.
// Per the Art Bible: majesty through scale and light, never a generic fantasy sky.
export function createSky(scene) {
  const skyGeo = new THREE.SphereGeometry(700, 32, 20);
  const skyMat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    uniforms: {
      topColor: { value: new THREE.Color(0xf7e9c8) },     // warm white zenith
      midColor: { value: new THREE.Color(0xe8cf8e) },     // pale gold
      botColor: { value: new THREE.Color(0xc9a94b) },     // deeper gold horizon
      sunDir: { value: new THREE.Vector3(0.25, 0.75, 0.35).normalize() },
    },
    vertexShader: /* glsl */`
      varying vec3 vDir;
      void main() {
        vDir = normalize(position);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: /* glsl */`
      uniform vec3 topColor, midColor, botColor, sunDir;
      varying vec3 vDir;
      void main() {
        float h = clamp(vDir.y, -0.1, 1.0);
        vec3 col = mix(botColor, midColor, smoothstep(-0.05, 0.25, h));
        col = mix(col, topColor, smoothstep(0.25, 0.85, h));
        // Blinding central light — the presence above Malkuth
        float sun = pow(max(dot(normalize(vDir), sunDir), 0.0), 220.0);
        float halo = pow(max(dot(normalize(vDir), sunDir), 0.0), 14.0);
        col += vec3(1.0, 0.97, 0.88) * sun * 2.4;
        col += vec3(0.95, 0.85, 0.6) * halo * 0.35;
        gl_FragColor = vec4(col, 1.0);
      }`,
  });
  const sky = new THREE.Mesh(skyGeo, skyMat);
  sky.name = 'sky';
  scene.add(sky);

  // Slow ring of high cirrus — "hostia angelical" orbiting the light
  const ringGeo = new THREE.TorusGeometry(320, 26, 8, 64);
  const ringMat = new THREE.MeshBasicMaterial({
    color: 0xfff6dd, transparent: true, opacity: 0.16, depthWrite: false,
  });
  const ring = new THREE.Mesh(ringGeo, ringMat);
  ring.rotation.x = Math.PI / 2.25;
  ring.position.y = 190;
  scene.add(ring);

  scene.fog = new THREE.Fog(0xe6cf92, 90, 620);

  // Lighting: constant late-afternoon gold. Shadows never move — time does not pass.
  const sun = new THREE.DirectionalLight(0xffe9bb, 2.6);
  sun.position.set(60, 120, 45);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.left = -70;
  sun.shadow.camera.right = 70;
  sun.shadow.camera.top = 70;
  sun.shadow.camera.bottom = -70;
  sun.shadow.camera.far = 400;
  sun.shadow.bias = -0.0006;
  scene.add(sun);
  scene.add(sun.target);

  const hemi = new THREE.HemisphereLight(0xf7e6c0, 0x6f8f45, 0.7);
  scene.add(hemi);

  const ambient = new THREE.AmbientLight(0xfff2d5, 0.2);
  scene.add(ambient);

  return {
    sun, hemi, ring,
    update(t, playerPos) {
      ring.rotation.z = t * 0.005;
      // Keep the shadow camera glued to the player
      if (playerPos) {
        sun.position.set(playerPos.x + 60, 120, playerPos.z + 45);
        sun.target.position.copy(playerPos);
      }
    },
  };
}

// Floating golden pollen — the only thing that drifts in a windless world.
export function createPollen(scene, count = 700) {
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    pos[i * 3] = (Math.random() - 0.5) * 140;
    pos[i * 3 + 1] = Math.random() * 22 + 0.5;
    pos[i * 3 + 2] = Math.random() * 380 - 10;
  }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({
    color: 0xffe9a8, size: 0.09, transparent: true, opacity: 0.75,
    blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  scene.add(points);
  return {
    points,
    update(t) {
      points.rotation.y = Math.sin(t * 0.03) * 0.02;
      points.position.y = Math.sin(t * 0.22) * 0.35;
    },
  };
}
