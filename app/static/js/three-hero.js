/**
 * SecondSpark — High-Resolution Realtime Interactive 3D Cyber Core & Energy Gyroscope
 * Features: High-poly cybernetic quantum core, dual orbital gyroscope rings,
 *           drag-to-rotate with kinetic momentum, click-to-pulse shockwave,
 *           dynamic electric arcs, 500-particle spiral nebula, mouse tracking.
 */

(function () {
  const container = document.getElementById('hero-3d-canvas-wrap');
  if (!container) return;

  function hasWebGL() {
    try {
      const c = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
    } catch (e) { return false; }
  }

  // 2D Canvas Fallback
  function init2DFallback() {
    const canvas = document.createElement('canvas');
    canvas.id = 'hero-3d-canvas';
    container.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    let W = (canvas.width = container.clientWidth);
    let H = (canvas.height = container.clientHeight);
    window.addEventListener('resize', () => { W = canvas.width = container.clientWidth; H = canvas.height = container.clientHeight; });

    const pts = Array.from({ length: 45 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.8, vy: (Math.random() - 0.5) * 0.8,
      r: Math.random() * 3 + 1.5, pulse: Math.random() * Math.PI * 2
    }));

    let t = 0;
    function draw() {
      ctx.clearRect(0, 0, W, H);
      t += 0.02;
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > W) p.vx *= -1;
        if (p.y < 0 || p.y > H) p.vy *= -1;
        for (let j = i + 1; j < pts.length; j++) {
          const q = pts[j];
          const dx = p.x - q.x, dy = p.y - q.y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < 110) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = `rgba(53,201,138,${(1 - d / 110) * 0.5})`;
            ctx.lineWidth = 1; ctx.stroke();
          }
        }
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * (1 + 0.3 * Math.sin(t * 2 + p.pulse)), 0, Math.PI * 2);
        ctx.fillStyle = '#35C98A'; ctx.fill();
      }
      requestAnimationFrame(draw);
    }
    draw();
  }

  if (typeof THREE === 'undefined' || !hasWebGL()) {
    init2DFallback();
    return;
  }

  try {
    let W = container.clientWidth, H = container.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 1000);
    camera.position.set(0, 0, 24);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'high-performance' });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    renderer.domElement.id = 'hero-3d-canvas';
    renderer.domElement.style.cursor = 'grab';
    container.appendChild(renderer.domElement);

    // Root Assembly Group
    const rootAssembly = new THREE.Group();
    scene.add(rootAssembly);

    /* ══════════════════════════════════════════════
       HIGH-RESOLUTION MATERIALS
    ══════════════════════════════════════════════ */
    // Metallic Titanium / Obsidian Shaders
    const darkMetalMat = new THREE.MeshStandardMaterial({
      color: 0x111827,
      metalness: 0.85,
      roughness: 0.2,
      wireframe: false
    });

    // Emerald Crystal Core
    const emeraldCoreMat = new THREE.MeshStandardMaterial({
      color: 0x35C98A,
      emissive: 0x187046,
      emissiveIntensity: 0.45,
      metalness: 0.65,
      roughness: 0.15,
      transparent: true,
      opacity: 0.92
    });

    // Outer Wireframe Cage
    const wireGlowMat = new THREE.MeshBasicMaterial({
      color: 0x5EEAD4,
      wireframe: true,
      transparent: true,
      opacity: 0.45
    });

    // Glowing Neon Rings
    const neonRingMat = new THREE.MeshStandardMaterial({
      color: 0x35C98A,
      emissive: 0x35C98A,
      emissiveIntensity: 0.8,
      metalness: 0.9,
      roughness: 0.1
    });

    const outerRingMat = new THREE.MeshStandardMaterial({
      color: 0x38BDF8,
      emissive: 0x0284C7,
      emissiveIntensity: 0.35,
      metalness: 0.8,
      roughness: 0.25
    });

    /* ══════════════════════════════════════════════
       CENTRAL QUANTUM CORE
    ══════════════════════════════════════════════ */
    const coreGroup = new THREE.Group();
    rootAssembly.add(coreGroup);

    // Inner Glowing Core (Icosahedron high-poly)
    const innerCoreGeo = new THREE.IcosahedronGeometry(2.2, 1);
    const innerCore = new THREE.Mesh(innerCoreGeo, emeraldCoreMat);
    coreGroup.add(innerCore);

    // Outer Faceted Cage (Dual geometry)
    const outerCageGeo = new THREE.IcosahedronGeometry(2.65, 0);
    const outerCage = new THREE.Mesh(outerCageGeo, wireGlowMat);
    coreGroup.add(outerCage);

    // Central Floating Spark Nucleus
    const nucleusGeo = new THREE.SphereGeometry(0.8, 32, 32);
    const nucleusMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF });
    const nucleus = new THREE.Mesh(nucleusGeo, nucleusMat);
    coreGroup.add(nucleus);

    /* ══════════════════════════════════════════════
       ORBITAL GYROSCOPE RINGS
    ══════════════════════════════════════════════ */
    const ringsGroup = new THREE.Group();
    rootAssembly.add(ringsGroup);

    // Ring 1 (Inner fast gyro)
    const ringGeo1 = new THREE.TorusGeometry(4.2, 0.08, 24, 100);
    const gyroRing1 = new THREE.Mesh(ringGeo1, neonRingMat);
    gyroRing1.rotation.x = Math.PI / 3;
    ringsGroup.add(gyroRing1);

    // Ring 2 (Middle gyro with nodes)
    const ringGeo2 = new THREE.TorusGeometry(5.6, 0.06, 24, 100);
    const gyroRing2 = new THREE.Mesh(ringGeo2, outerRingMat);
    gyroRing2.rotation.y = Math.PI / 4;
    gyroRing2.rotation.x = Math.PI / 6;
    ringsGroup.add(gyroRing2);

    // Ring 3 (Outer planetary tracking ring)
    const ringGeo3 = new THREE.TorusGeometry(7.2, 0.04, 16, 120);
    const gyroRing3 = new THREE.Mesh(ringGeo3, new THREE.MeshBasicMaterial({ color: 0x35C98A, transparent: true, opacity: 0.35 }));
    gyroRing3.rotation.x = Math.PI / 2.2;
    ringsGroup.add(gyroRing3);

    /* ══════════════════════════════════════════════
       ORBITING CYBERNETIC SATELLITE MODULES
    ══════════════════════════════════════════════ */
    const satellites = [];
    const SATELLITE_COUNT = 14;

    const satGeos = [
      new THREE.BoxGeometry(0.65, 0.65, 0.65),
      new THREE.OctahedronGeometry(0.55, 0),
      new THREE.TetrahedronGeometry(0.6, 0),
      new THREE.CylinderGeometry(0.25, 0.25, 0.7, 8)
    ];

    for (let i = 0; i < SATELLITE_COUNT; i++) {
      const geo = satGeos[i % satGeos.length];
      const mat = (i % 2 === 0) ? emeraldCoreMat : darkMetalMat;
      const mesh = new THREE.Mesh(geo, mat);

      const orbitRadius = 6.2 + Math.random() * 2.8;
      const angle = (i / SATELLITE_COUNT) * Math.PI * 2;
      const speed = (0.35 + Math.random() * 0.45) * (i % 2 === 0 ? 1 : -1);
      const elevation = (Math.random() - 0.5) * 5;

      mesh.userData = {
        orbitRadius,
        angle,
        speed,
        elevation,
        rotSpeedX: (Math.random() - 0.5) * 0.04,
        rotSpeedY: (Math.random() - 0.5) * 0.04
      };

      mesh.position.set(Math.cos(angle) * orbitRadius, elevation, Math.sin(angle) * orbitRadius);
      rootAssembly.add(mesh);
      satellites.push(mesh);
    }

    /* ══════════════════════════════════════════════
       500-PARTICLE SPIRAL NEBULA & SPARKS
    ══════════════════════════════════════════════ */
    const particleCount = 450;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const particleScales = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      const radius = 2.5 + Math.random() * 14;
      const theta = Math.random() * Math.PI * 2;
      const phi = (Math.random() - 0.5) * Math.PI * 0.8;

      positions[i * 3]     = radius * Math.cos(theta) * Math.cos(phi);
      positions[i * 3 + 1] = radius * Math.sin(phi) * 0.8;
      positions[i * 3 + 2] = radius * Math.sin(theta) * Math.cos(phi);
      particleScales[i]    = Math.random();
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0x35C98A,
      size: 0.16,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending
    });

    const particleSystem = new THREE.Points(particleGeo, particleMat);
    rootAssembly.add(particleSystem);

    /* ══════════════════════════════════════════════
       DYNAMIC ELECTRIC ARCS (Lines)
    ══════════════════════════════════════════════ */
    const arcGroup = new THREE.Group();
    rootAssembly.add(arcGroup);

    function updateArcs(time) {
      while (arcGroup.children.length > 0) arcGroup.remove(arcGroup.children[0]);

      for (let i = 0; i < satellites.length; i += 2) {
        const sat = satellites[i];
        const dist = sat.position.length();
        if (dist < 9.5) {
          const arcGeo = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(
              sat.position.x * 0.5 + Math.sin(time * 5 + i) * 0.3,
              sat.position.y * 0.5 + Math.cos(time * 5 + i) * 0.3,
              sat.position.z * 0.5
            ),
            sat.position
          ]);
          const alpha = 0.25 + 0.25 * Math.sin(time * 6 + i);
          const arcMat = new THREE.LineBasicMaterial({ color: 0x35C98A, transparent: true, opacity: alpha });
          arcGroup.add(new THREE.Line(arcGeo, arcMat));
        }
      }
    }

    /* ══════════════════════════════════════════════
       DYNAMIC LIGHTING
    ══════════════════════════════════════════════ */
    const ambientLight = new THREE.AmbientLight(0xFFFFFF, 1.2);
    scene.add(ambientLight);

    // Glowing core point light
    const coreLight = new THREE.PointLight(0x35C98A, 4, 30);
    coreLight.position.set(0, 0, 0);
    scene.add(coreLight);

    // Orbiting rim light (Sky blue)
    const rimLight = new THREE.PointLight(0x38BDF8, 2.5, 40);
    rimLight.position.set(8, 12, 10);
    scene.add(rimLight);

    // Secondary warm spark light
    const sparkLight = new THREE.PointLight(0x10B981, 2, 25);
    sparkLight.position.set(-8, -6, -8);
    scene.add(sparkLight);

    /* ══════════════════════════════════════════════
       INTERACTIVE MOUSE DRAG, INERTIA & PARALLAX
    ══════════════════════════════════════════════ */
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };
    let dragVelocity = { x: 0, y: 0 };
    let mouseParallax = { x: 0, y: 0 };
    let scrollYOffset = 0;
    let shockwaveScale = 1.0;

    const dom = renderer.domElement;

    dom.addEventListener('mousedown', (e) => {
      isDragging = true;
      dom.style.cursor = 'grabbing';
      previousMousePosition = { x: e.clientX, y: e.clientY };
      dragVelocity = { x: 0, y: 0 };
    });

    window.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        dom.style.cursor = 'grab';
      }
    });

    window.addEventListener('mousemove', (e) => {
      // Parallax coords (-1 to +1)
      mouseParallax.x = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseParallax.y = (e.clientY / window.innerHeight - 0.5) * 2;

      if (isDragging) {
        const deltaX = e.clientX - previousMousePosition.x;
        const deltaY = e.clientY - previousMousePosition.y;

        dragVelocity.x = deltaX * 0.006;
        dragVelocity.y = deltaY * 0.006;

        rootAssembly.rotation.y += dragVelocity.x;
        rootAssembly.rotation.x += dragVelocity.y;

        previousMousePosition = { x: e.clientX, y: e.clientY };
      }
    });

    // Touch events for mobile/tablet interactive drag
    dom.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        isDragging = true;
        previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        dragVelocity = { x: 0, y: 0 };
      }
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (isDragging && e.touches.length === 1) {
        const deltaX = e.touches[0].clientX - previousMousePosition.x;
        const deltaY = e.touches[0].clientY - previousMousePosition.y;

        dragVelocity.x = deltaX * 0.008;
        dragVelocity.y = deltaY * 0.008;

        rootAssembly.rotation.y += dragVelocity.x;
        rootAssembly.rotation.x += dragVelocity.y;

        previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      }
    }, { passive: true });

    window.addEventListener('touchend', () => { isDragging = false; });

    // Click to emit shockwave pulse
    dom.addEventListener('click', () => {
      shockwaveScale = 1.65;
      coreLight.intensity = 8.0;
      setTimeout(() => { coreLight.intensity = 4.0; }, 250);
    });

    window.addEventListener('scroll', () => {
      scrollYOffset = window.scrollY;
    }, { passive: true });

    window.addEventListener('resize', () => {
      W = container.clientWidth;
      H = container.clientHeight;
      camera.aspect = W / H;
      camera.updateProjectionMatrix();
      renderer.setSize(W, H);
    });

    /* ══════════════════════════════════════════════
       PHYSICS & ANIMATION LOOP
    ══════════════════════════════════════════════ */
    const clock = new THREE.Clock();
    let arcTimer = 0;

    function animate() {
      requestAnimationFrame(animate);
      const dt = clock.getDelta();
      const time = clock.getElapsedTime();

      // Inertia & Damping when not dragging
      if (!isDragging) {
        dragVelocity.x *= 0.94;
        dragVelocity.y *= 0.94;
        rootAssembly.rotation.y += dragVelocity.x + 0.12 * dt;
        rootAssembly.rotation.x += dragVelocity.y;

        // Subtle return to neutral tilt
        rootAssembly.rotation.x += (mouseParallax.y * 0.2 - rootAssembly.rotation.x) * 0.03;
      }

      // Shockwave decay
      shockwaveScale += (1.0 - shockwaveScale) * 0.1;
      coreGroup.scale.setScalar(shockwaveScale);

      // Core pulsating rotation
      const corePulse = 1.0 + 0.05 * Math.sin(time * 3);
      innerCore.scale.setScalar(corePulse);
      innerCore.rotation.y = time * 0.5;
      innerCore.rotation.z = time * 0.3;

      outerCage.rotation.y = -time * 0.35;
      outerCage.rotation.x = time * 0.25;

      nucleus.scale.setScalar(0.7 + 0.25 * Math.sin(time * 6));

      // Gyroscope ring independent kinematics
      gyroRing1.rotation.z = time * 0.45;
      gyroRing1.rotation.y = time * 0.25;

      gyroRing2.rotation.x = -time * 0.35;
      gyroRing2.rotation.z = time * 0.2;

      gyroRing3.rotation.z = time * 0.15;

      // Orbiting Satellites
      satellites.forEach(sat => {
        const u = sat.userData;
        u.angle += u.speed * dt;
        sat.position.x = Math.cos(u.angle) * u.orbitRadius;
        sat.position.z = Math.sin(u.angle) * u.orbitRadius;
        sat.position.y = u.elevation + Math.sin(time * 2 + u.angle) * 0.6;

        sat.rotation.x += u.rotSpeedX;
        sat.rotation.y += u.rotSpeedY;
      });

      // Particle system slow cosmic spin
      particleSystem.rotation.y = time * 0.06;
      particleSystem.rotation.x = Math.sin(time * 0.04) * 0.1;

      // Update electric spark arcs
      arcTimer++;
      if (arcTimer % 2 === 0) updateArcs(time);

      // Camera parallax response to scroll
      camera.position.y += (-scrollYOffset * 0.005 - camera.position.y) * 0.06;

      // Core light dynamic brightness pulse
      coreLight.intensity = 3.5 + 1.2 * Math.sin(time * 4);

      renderer.render(scene, camera);
    }

    animate();

  } catch (err) {
    console.warn('Three.js failed, using fallback:', err);
    init2DFallback();
  }
})();
