/*
 * Offline texture generator for Reien.
 *
 * This file is intentionally NOT loaded by index.html. It is the canonical
 * source used by tools/bake_textures.py to bake expensive procedural canvas
 * textures into static WebP assets under assets/textures/.
 *
 * Keep the drawing code in sync with the visuals that shipped in v1.4.0.
 */
(function () {
  'use strict';

  // Convert a grayscale height canvas into a Tangent-Space Normal Map (RGB)
  function heightToNormalCanvas(heightCanvas, strength) {
    strength = strength === undefined ? 4.0 : strength;
    const w = heightCanvas.width, h = heightCanvas.height;
    const src = heightCanvas.getContext('2d').getImageData(0, 0, w, h).data;
    const normCanvas = document.createElement('canvas');
    normCanvas.width = w; normCanvas.height = h;
    const nCtx = normCanvas.getContext('2d');
    const dstImg = nCtx.createImageData(w, h);
    const dst = dstImg.data;

    const getH = (x, y) => {
      const cx = (x + w) % w;
      const cy = (y + h) % h;
      return src[(cy * w + cx) * 4] / 255.0;
    };

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const hL = getH(x - 1, y);
        const hR = getH(x + 1, y);
        const hU = getH(x, y - 1);
        const hD = getH(x, y + 1);
        let nx = (hL - hR) * strength;
        let ny = (hU - hD) * strength;
        let nz = 1.0;
        const len = Math.hypot(nx, ny, nz);
        nx /= len; ny /= len; nz /= len;
        const idx = (y * w + x) * 4;
        dst[idx]     = Math.floor((nx * 0.5 + 0.5) * 255);
        dst[idx + 1] = Math.floor((ny * 0.5 + 0.5) * 255);
        dst[idx + 2] = Math.floor((nz * 0.5 + 0.5) * 255);
        dst[idx + 3] = 255;
      }
    }
    nCtx.putImageData(dstImg, 0, 0);
    return normCanvas;
  }

  // 2.1 High-Detail 3D Cobblestone + Wet Mortar Crevices PBR
  function createCobblestonePBR() {
    const size = 256;
    const colCanvas = document.createElement('canvas');
    const hgtCanvas = document.createElement('canvas');
    const rghCanvas = document.createElement('canvas');
    colCanvas.width = hgtCanvas.width = rghCanvas.width = size;
    colCanvas.height = hgtCanvas.height = rghCanvas.height = size;

    const cCtx = colCanvas.getContext('2d');
    const hCtx = hgtCanvas.getContext('2d');
    const rCtx = rghCanvas.getContext('2d');

    // Deep mortar crevices base (dark, low height, wet/shiny roughness)
    cCtx.fillStyle = '#3b424c'; cCtx.fillRect(0, 0, size, size);
    hCtx.fillStyle = '#181818'; hCtx.fillRect(0, 0, size, size);
    rCtx.fillStyle = '#141414'; rCtx.fillRect(0, 0, size, size); // wet glossy crevices!

    // Draw staggered rows of hand-carved stones
    const rows = 8, cols = 6;
    const cellW = size / cols, cellH = size / rows;
    const stonePalettes = ['#8c857b', '#7d7870', '#9a9186', '#6e737b', '#847c74', '#948b7f'];

    for (let r = -1; r <= rows; r++) {
      for (let c = -1; c <= cols; c++) {
        const offsetX = (r % 2) * (cellW * 0.5);
        const cx = c * cellW + offsetX + cellW * 0.5 + (Math.sin(r * 7 + c * 13) * 3);
        const cy = r * cellH + cellH * 0.5 + (Math.cos(r * 11 + c * 5) * 2);
        const rw = cellW * 0.43;
        const rh = cellH * 0.41;

        // Stone Height Dome (3D rounded relief)
        const hGrad = hCtx.createRadialGradient(cx - 2, cy - 2, 2, cx, cy, Math.max(rw, rh));
        hGrad.addColorStop(0, '#ffffff');
        hGrad.addColorStop(0.72, '#cccccc');
        hGrad.addColorStop(0.95, '#444444');
        hGrad.addColorStop(1, '#181818');
        hCtx.fillStyle = hGrad;
        hCtx.beginPath();
        hCtx.ellipse(cx, cy, rw, rh, 0, 0, Math.PI * 2);
        hCtx.fill();

        // Stone Albedo Color with edge bevel highlight
        const baseCol = stonePalettes[Math.abs(r * 5 + c * 3) % stonePalettes.length];
        const cGrad = cCtx.createRadialGradient(cx - 3, cy - 3, 2, cx, cy, Math.max(rw, rh));
        cGrad.addColorStop(0, '#b5ada2');
        cGrad.addColorStop(0.65, baseCol);
        cGrad.addColorStop(0.95, '#4a4e54');
        cGrad.addColorStop(1, '#2d3238');
        cCtx.fillStyle = cGrad;
        cCtx.beginPath();
        cCtx.ellipse(cx, cy, rw, rh, 0, 0, Math.PI * 2);
        cCtx.fill();

        // Roughness (matte stone top, glossy wet edges)
        rCtx.fillStyle = '#a8a8a8';
        rCtx.beginPath();
        rCtx.ellipse(cx, cy, rw * 0.85, rh * 0.85, 0, 0, Math.PI * 2);
        rCtx.fill();
      }
    }

    return {
      colCanvas,
      normCanvas: heightToNormalCanvas(hgtCanvas, 5.5),
      rghCanvas
    };
  }

  // 2.2 Lush Mossy Grass & Clover Terrain PBR
  function createGrassTerrainPBR() {
    const size = 256;
    const colCanvas = document.createElement('canvas');
    const hgtCanvas = document.createElement('canvas');
    colCanvas.width = hgtCanvas.width = size;
    colCanvas.height = hgtCanvas.height = size;
    const cCtx = colCanvas.getContext('2d');
    const hCtx = hgtCanvas.getContext('2d');

    cCtx.fillStyle = '#38562b'; cCtx.fillRect(0, 0, size, size);
    hCtx.fillStyle = '#606060'; hCtx.fillRect(0, 0, size, size);

    // Dappled moss patches & micro-blades
    for (let i = 0; i < 900; i++) {
      const x = Math.random() * size;
      const y = Math.random() * size;
      const r = 4 + Math.random() * 14;
      const g = cCtx.createRadialGradient(x, y, 1, x, y, r);
      g.addColorStop(0, i % 3 === 0 ? 'rgba(78, 118, 52, 0.35)' : 'rgba(42, 72, 34, 0.35)');
      g.addColorStop(1, 'rgba(56, 86, 43, 0)');
      cCtx.fillStyle = g;
      cCtx.beginPath(); cCtx.arc(x, y, r, 0, Math.PI * 2); cCtx.fill();

      // Blade height stroke
      hCtx.strokeStyle = i % 2 === 0 ? 'rgba(220,220,220,0.45)' : 'rgba(40,40,40,0.45)';
      hCtx.lineWidth = 1.5;
      hCtx.beginPath();
      hCtx.moveTo(x, y);
      hCtx.lineTo(x + (Math.random() - 0.5) * 4, y - 4 - Math.random() * 5);
      hCtx.stroke();
    }

    return {
      colCanvas,
      normCanvas: heightToNormalCanvas(hgtCanvas, 3.2)
    };
  }

  // 2.3 Gnarled Tree Bark PBR (with vertical ridges & moss)
  function createBarkPBR() {
    const size = 256;
    const colCanvas = document.createElement('canvas');
    const hgtCanvas = document.createElement('canvas');
    colCanvas.width = hgtCanvas.width = size;
    colCanvas.height = hgtCanvas.height = size;
    const cCtx = colCanvas.getContext('2d');
    const hCtx = hgtCanvas.getContext('2d');

    cCtx.fillStyle = '#4a3225'; cCtx.fillRect(0, 0, size, size);
    hCtx.fillStyle = '#808080'; hCtx.fillRect(0, 0, size, size);

    for (let x = 0; x < size; x += 4) {
      const shade = Math.sin(x * 0.25) * 20;
      cCtx.fillStyle = shade > 0 ? '#5c3e2e' : '#362218';
      cCtx.fillRect(x, 0, 3, size);
      hCtx.fillStyle = shade > 0 ? '#d0d0d0' : '#303030';
      hCtx.fillRect(x, 0, 3, size);
    }

    return {
      colCanvas,
      normCanvas: heightToNormalCanvas(hgtCanvas, 4.5)
    };
  }

  // 2.4 High-Resolution Botanical Sakura Sprig Texture (真・五瓣櫻花枝葉簇)
  function createDetailedSakuraSprigTexture() {
    const c = document.createElement('canvas');
    c.width = 512; c.height = 512;
    const ctx = c.getContext('2d');

    // Helper to paint a single 5-petal cherry blossom flower with notched tips & stamen
    function drawSakuraFlower(fx, fy, radius, rot, tone) {
      ctx.save();
      ctx.translate(fx, fy);
      ctx.rotate(rot);

      for (let p = 0; p < 5; p++) {
        ctx.save();
        ctx.rotate((p * Math.PI * 2) / 5);
        const pGrad = ctx.createLinearGradient(0, 0, 0, -radius);
        if (tone === 'deep') {
          pGrad.addColorStop(0, '#e11d48');
          pGrad.addColorStop(0.35, '#fb7185');
          pGrad.addColorStop(1, '#ffe4e6');
        } else if (tone === 'light') {
          pGrad.addColorStop(0, '#f43f5e');
          pGrad.addColorStop(0.3, '#fda4af');
          pGrad.addColorStop(1, '#ffffff');
        } else {
          pGrad.addColorStop(0, '#be123c');
          pGrad.addColorStop(0.35, '#f472b6');
          pGrad.addColorStop(1, '#fce7f3');
        }
        ctx.fillStyle = pGrad;

        // Notched sakura petal shape
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.bezierCurveTo(-radius * 0.55, -radius * 0.35, -radius * 0.65, -radius * 0.85, -radius * 0.14, -radius);
        ctx.lineTo(0, -radius * 0.82); // characteristic sakura V-notch!
        ctx.lineTo(radius * 0.14, -radius);
        ctx.bezierCurveTo(radius * 0.65, -radius * 0.85, radius * 0.55, -radius * 0.35, 0, 0);
        ctx.closePath();
        ctx.fill();

        // Subtle petal rim highlight
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.55)';
        ctx.lineWidth = 1.2;
        ctx.stroke();
        ctx.restore();
      }

      // Golden-pink stamen filaments in center
      ctx.fillStyle = '#be185d';
      ctx.beginPath(); ctx.arc(0, 0, radius * 0.14, 0, Math.PI * 2); ctx.fill();
      for (let s = 0; s < 10; s++) {
        const sa = (s / 10) * Math.PI * 2;
        const sr = radius * 0.28;
        ctx.strokeStyle = '#fda4af';
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(sa) * sr, Math.sin(sa) * sr); ctx.stroke();
        ctx.fillStyle = '#fef08a';
        ctx.beginPath(); ctx.arc(Math.cos(sa) * sr, Math.sin(sa) * sr, 1.8, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();
    }

    // Draw fine dark twigs behind blossoms
    ctx.strokeStyle = '#4a2c20';
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(256, 460); ctx.quadraticCurveTo(240, 260, 120, 110);
    ctx.moveTo(250, 340); ctx.quadraticCurveTo(320, 230, 400, 140);
    ctx.moveTo(210, 230); ctx.quadraticCurveTo(150, 240, 85, 270);
    ctx.stroke();

    // Layer 42 detailed cherry blossoms in a lush botanical bouquet
    const tones = ['mid', 'light', 'deep'];
    for (let i = 0; i < 42; i++) {
      const angle = (i / 42) * Math.PI * 2 + (i % 5) * 0.4;
      const dist = 25 + (i % 7) * 28;
      const fx = 256 + Math.cos(angle) * dist;
      const fy = 245 + Math.sin(angle) * dist;
      const rad = 26 + (i % 4) * 7;
      drawSakuraFlower(fx, fy, rad, i * 1.1, tones[i % 3]);
    }

    return c;
  }

  // 2.5 Pine Needle Branchlet Texture (細緻松針枝條)
  function createPineBranchTexture() {
    const c = document.createElement('canvas');
    c.width = 256; c.height = 256;
    const ctx = c.getContext('2d');

    for (let cluster = 0; cluster < 14; cluster++) {
      const cx = 128 + Math.cos(cluster * 1.7) * (30 + (cluster % 4) * 18);
      const cy = 128 + Math.sin(cluster * 1.7) * (30 + (cluster % 4) * 18);
      for (let n = 0; n < 28; n++) {
        const a = (n / 28) * Math.PI * 2;
        const len = 24 + (n % 3) * 10;
        const grad = ctx.createLinearGradient(cx, cy, cx + Math.cos(a) * len, cy + Math.sin(a) * len);
        grad.addColorStop(0, '#064e3b');
        grad.addColorStop(0.65, '#15803d');
        grad.addColorStop(1, '#86efac');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(a) * len, cy + Math.sin(a) * len);
        ctx.stroke();
      }
    }
    return c;
  }

  window.ReienTextureGen = {
    heightToNormalCanvas,
    createCobblestonePBR,
    createGrassTerrainPBR,
    createBarkPBR,
    createDetailedSakuraSprigTexture,
    createPineBranchTexture
  };
})();
