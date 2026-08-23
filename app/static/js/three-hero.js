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

    // Emerald Crystal Glass Logo Material (Matches #10B981 Theme)
    const emeraldCoreMat = new THREE.MeshStandardMaterial({
      color: 0x10B981,
      emissive: 0x059669,
      emissiveIntensity: 0.55,
      metalness: 0.45,
      roughness: 0.15,
      transparent: true,
      opacity: 0.95
    });

    // Second Spark (Cyan-Emerald Satellite) Material
    const cyanSparkMat = new THREE.MeshStandardMaterial({
      color: 0x5EEAD4,
      emissive: 0x10B981,
      emissiveIntensity: 0.65,
      metalness: 0.6,
      roughness: 0.12,
      transparent: true,
      opacity: 0.96
    });

    // Outer Wireframe Diamond Lattice
    const wireGlowMat = new THREE.MeshBasicMaterial({
      color: 0xA7F3D0,
      wireframe: true,
      transparent: true,
      opacity: 0.45
    });

    // Glowing Neon Rings
    const neonRingMat = new THREE.MeshStandardMaterial({
      color: 0x10B981,
      emissive: 0x10B981,
      emissiveIntensity: 0.85,
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
       3D SECONDSPARK LOGO CRYSTAL GEOMETRY GENERATOR
    ══════════════════════════════════════════════ */
    function createSparkGeometry(outerR, innerR, depth, bevel) {
      const shape = new THREE.Shape();
      const points = 8;
      for (let i = 0; i < points * 2; i++) {
        const angle = (i * Math.PI) / points - Math.PI / 2;
        const r = (i % 2 === 0) ? outerR : innerR;
        const x = Math.cos(angle) * r;
        const y = Math.sin(angle) * r;
        if (i === 0) shape.moveTo(x, y);
        else shape.lineTo(x, y);
      }
      shape.closePath();

      const extrudeSettings = {
        depth: depth,
        bevelEnabled: true,
        bevelSegments: 4,
        bevelThickness: bevel,
        bevelSize: bevel * 0.75,
        curveSegments: 12
      };

      const geo = new THREE.ExtrudeGeometry(shape, extrudeSettings);
      geo.center();
      return geo;
    }

    /* ══════════════════════════════════════════════
       3D SECONDSPARK CIRCULAR GLASS LOGO MEDAL
    ══════════════════════════════════════════════ */
    const coreGroup = new THREE.Group();
    rootAssembly.add(coreGroup);

    // Texture Loader for High-Res Circular Logo
    const textureLoader = new THREE.TextureLoader();
    const logoTexture = textureLoader.load('/static/images/brand-logo-circle.png');
    logoTexture.anisotropy = 16;

    // Translucent Glass Disc Base Material
    const glassDiscMat = new THREE.MeshStandardMaterial({
      color: 0xEEFFF6,
      emissive: 0x059669,
      emissiveIntensity: 0.25,
      metalness: 0.25,
      roughness: 0.1,
      transparent: true,
      opacity: 0.94
    });

    // Logo Disc Front Face Material
    const logoFaceMat = new THREE.MeshStandardMaterial({
      map: logoTexture,
      transparent: true,
      roughness: 0.15,
      metalness: 0.35,
      emissive: 0x10B981,
      emissiveIntensity: 0.18,
      side: THREE.DoubleSide
    });

    // Glass Token Cylinder Body (Upright facing camera)
    const discGeo = new THREE.CylinderGeometry(2.9, 2.9, 0.32, 64);
    discGeo.rotateX(Math.PI / 2);

    const discMesh = new THREE.Mesh(discGeo, [glassDiscMat, logoFaceMat, logoFaceMat]);
    coreGroup.add(discMesh);

    // Beveled Emerald Chrome Outer Rim
    const rimGeo = new THREE.TorusGeometry(2.92, 0.07, 24, 100);
    const rimMesh = new THREE.Mesh(rimGeo, neonRingMat);
    coreGroup.add(rimMesh);

    // 3D Floating Holographic Emerald Spark Waveform hovering in front of disc
    const waveformGroup = new THREE.Group();
    coreGroup.add(waveformGroup);
    waveformGroup.position.z = 0.22;

    // 3D Diamond Star Spark on Waveform
    const sparkGeo = createSparkGeometry(0.9, 0.28, 0.18, 0.08);
    const sparkMesh = new THREE.Mesh(sparkGeo, emeraldCoreMat);
    sparkMesh.position.set(-0.9, 0, 0.05);
    waveformGroup.add(sparkMesh);

    // 3D Floating Luminescent Quantum Nucleus Core
    const nucleusGeo = new THREE.SphereGeometry(0.35, 32, 32);
    const nucleusMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF });
    const nucleus = new THREE.Mesh(nucleusGeo, nucleusMat);
    nucleus.position.set(-0.9, 0, 0.1);
    waveformGroup.add(nucleus);

    // Secondary "Second Spark" Satellite Star Orbiting the Token
    const secondarySparkGroup = new THREE.Group();
    coreGroup.add(secondarySparkGroup);
    const secGeo = createSparkGeometry(0.75, 0.25, 0.15, 0.06);
    const secMesh = new THREE.Mesh(secGeo, cyanSparkMat);
    secondarySparkGroup.add(secMesh);
    secondarySparkGroup.position.set(2.4, 2.0, 0.8);

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

      // ══════════════════════════════════════════════════════
      // 2.4s Looping Breathing Glass & Atmospheric Glow Motion
      // ══════════════════════════════════════════════════════
      const loopPeriod = 2.4;
      const loopT = (time % loopPeriod) / loopPeriod;
      const breathingScale = 1.0 + 0.015 * Math.sin(2 * Math.PI * loopT);
      const glowPulse = 0.5 + 0.5 * Math.sin(2 * Math.PI * loopT);

      // Apply shockwave scale combined with 2.4s breathing scale
      coreGroup.scale.setScalar(shockwaveScale * breathingScale);

      // 3D Glass Logo Disc Gentle Floating Oscillation
      discMesh.rotation.z = Math.sin(time * 0.4) * 0.08;
      discMesh.position.z = Math.sin(time * 0.8) * 0.1;

      // Floating 3D Spark Waveform Hover Dynamics
      sparkMesh.rotation.y = time * 0.8;
      sparkMesh.rotation.z = time * 0.4;
      sparkMesh.scale.setScalar(1.0 + 0.1 * Math.sin(time * 3));

      waveformGroup.position.y = Math.sin(time * 1.5) * 0.08;

      // Secondary "Second Spark" Satellite Orbiting Motion around Token
      const secAngle = time * 0.85;
      secondarySparkGroup.position.x = Math.cos(secAngle) * 3.4;
      secondarySparkGroup.position.y = Math.sin(secAngle) * 2.4;
      secondarySparkGroup.position.z = Math.sin(time * 0.7) * 1.4;
      secondarySparkGroup.rotation.y = -time * 0.9;
      secondarySparkGroup.rotation.z = time * 0.6;
      secondarySparkGroup.scale.setScalar(0.9 + 0.15 * Math.sin(time * 3));

      // Quantum Luminescent Spark Nucleus
      nucleus.scale.setScalar(0.75 + 0.25 * Math.sin(time * 5));

      // Synchronized Atmospheric Glow Intensity
      emeraldCoreMat.emissiveIntensity = 0.45 + 0.25 * glowPulse;
      cyanSparkMat.emissiveIntensity = 0.55 + 0.25 * glowPulse;
      coreLight.intensity = (3.5 + 1.5 * glowPulse) * (shockwaveScale > 1.05 ? 1.8 : 1.0);

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
