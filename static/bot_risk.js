/* Minimal collector: pointer events -> feature window -> POST -> overlay */

const BotRisk = (() => {
  function nowMs() { return performance.now(); }

  function quantile(arr, q) {
    if (!arr.length) return 0;
    const a = [...arr].sort((x,y)=>x-y);
    const pos = (a.length - 1) * q;
    const base = Math.floor(pos);
    const rest = pos - base;
    return a[base + 1] !== undefined ? a[base] + rest * (a[base + 1] - a[base]) : a[base];
  }

  function mean(arr) {
    if (!arr.length) return 0;
    return arr.reduce((s,x)=>s+x,0) / arr.length;
  }

  function std(arr) {
    if (arr.length < 2) return 0;
    const m = mean(arr);
    const v = arr.reduce((s,x)=>s+(x-m)*(x-m),0) / (arr.length - 1);
    return Math.sqrt(v);
  }

  function angleBetween(v1x, v1y, v2x, v2y) {
    const dot = v1x*v2x + v1y*v2y;
    const n1 = Math.hypot(v1x, v1y);
    const n2 = Math.hypot(v2x, v2y);
    if (n1 === 0 || n2 === 0) return 0;
    const c = Math.min(1, Math.max(-1, dot / (n1*n2)));
    return Math.acos(c);
  }

  function computeFeatures(points) {
    // points: [{t,x,y,type,isTrusted,pointerType}]
    const n = points.length;
    if (n < 5) return null;

    const dt = [];
    const speed = [];
    let pathLen = 0;

    const turnAngles = [];
    for (let i = 1; i < n; i++) {
      const a = points[i-1], b = points[i];
      const dti = Math.max(0.5, b.t - a.t); // avoid zeros
      dt.push(dti);

      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.hypot(dx, dy);
      pathLen += dist;

      speed.push((dist / dti) * 1000.0); // px/s
    }

    // turning angle (use consecutive segments)
    for (let i = 2; i < n; i++) {
      const p0 = points[i-2], p1 = points[i-1], p2 = points[i];
      const v1x = p1.x - p0.x, v1y = p1.y - p0.y;
      const v2x = p2.x - p1.x, v2y = p2.y - p1.y;
      turnAngles.push(Math.abs(angleBetween(v1x, v1y, v2x, v2y)));
    }

    const start = points[0], end = points[n-1];
    const displacement = Math.hypot(end.x - start.x, end.y - start.y);
    const straightness = pathLen > 0 ? Math.min(1, displacement / pathLen) : 0;

    const trustedRatio = points.filter(p => p.isTrusted).length / n;

    return {
      n,
      mean_dt: mean(dt),
      std_dt: std(dt),
      p90_dt: quantile(dt, 0.90),

      mean_speed: mean(speed),
      std_speed: std(speed),
      max_speed: speed.length ? Math.max(...speed) : 0,

      straightness,
      mean_abs_turn: mean(turnAngles),

      trusted_ratio: trustedRatio,
      pointer_type: points[0].pointerType || null,
    };
  }

  async function postJSON(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  }

  function start(opts) {
    const {
      scoreEndpoint,
      collectHumanEndpoint,
      overlayProbEl,
      overlayMetaEl,
      collectBtn,
      collectStatusEl,
      target = window,
      windowMs = 2500,
      minPoints = 25,
    } = opts;

    let buf = [];
    let t0 = nowMs();
    let lastFeatures = null;

    function pushPoint(e, type) {
      // Restrict to primary pointer to reduce noise
      const t = nowMs() - t0;
      buf.push({
        t,
        x: e.clientX,
        y: e.clientY,
        type,
        isTrusted: !!e.isTrusted,
        pointerType: e.pointerType || "mouse",
      });
    }

    target.addEventListener("pointermove", (e) => pushPoint(e, "m"), { passive: true });
    target.addEventListener("pointerdown", (e) => pushPoint(e, "d"));
    target.addEventListener("pointerup", (e) => pushPoint(e, "u"));

    async function tick() {
      try {
        if (buf.length >= minPoints) {
          const features = computeFeatures(buf);
          if (features) {
            lastFeatures = features;
            const out = await postJSON(scoreEndpoint, features);
            const pct = Math.round(out.bot_probability * 100);
            overlayProbEl.textContent = `${pct}%`;
            overlayMetaEl.textContent = `${out.model} | raw=${out.raw_score.toFixed(3)}`;
          }
        }
      } catch (err) {
        overlayMetaEl.textContent = `score error: ${err.message}`;
      } finally {
        buf = [];
        t0 = nowMs();
        setTimeout(tick, windowMs);
      }
    }

    tick();

    if (collectBtn && collectHumanEndpoint) {
      collectBtn.addEventListener("click", async () => {
        if (!lastFeatures) {
          collectStatusEl.textContent = "Pas encore de fenêtre exploitable (bouge/clic un peu).";
          return;
        }
        try {
          await postJSON(collectHumanEndpoint, lastFeatures);
          collectStatusEl.textContent = "Sample humain enregistré ✅";
          setTimeout(()=>collectStatusEl.textContent="", 1500);
        } catch (err) {
          collectStatusEl.textContent = `Collect error: ${err.message}`;
        }
      });
    }
  }

  return { start };
})();
