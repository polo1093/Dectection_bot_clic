const ProgramRunner = (() => {
  function setOutput(outputEl, text) {
    outputEl.textContent = text || "";
    outputEl.scrollTop = outputEl.scrollHeight;
  }

  function estimateScreenRegion(target) {
    const rect = target.getBoundingClientRect();
    const scale = window.devicePixelRatio || 1;
    const viewport = window.visualViewport;
    const viewportLeft = viewport ? viewport.offsetLeft : 0;
    const viewportTop = viewport ? viewport.offsetTop : 0;
    const chromeLeft = Math.max(0, Math.round((window.outerWidth - window.innerWidth) / 2));
    const chromeTop = Math.max(0, window.outerHeight - window.innerHeight - chromeLeft);
    const screenLeft = Number.isFinite(window.screenLeft) ? window.screenLeft : window.screenX;
    const screenTop = Number.isFinite(window.screenTop) ? window.screenTop : window.screenY;
    const x1 = Math.round((screenLeft + chromeLeft + viewportLeft + rect.left) * scale);
    const y1 = Math.round((screenTop + chromeTop + viewportTop + rect.top) * scale);
    const x2 = Math.round((screenLeft + chromeLeft + viewportLeft + rect.right) * scale);
    const y2 = Math.round((screenTop + chromeTop + viewportTop + rect.bottom) * scale);
    return `${x1},${y1},${x2},${y2}`;
  }

  function describeWindow() {
    const screenLeft = Number.isFinite(window.screenLeft) ? window.screenLeft : window.screenX;
    const screenTop = Number.isFinite(window.screenTop) ? window.screenTop : window.screenY;
    return `fenetre=(${Math.round(screenLeft)},${Math.round(screenTop)}) viewport=${window.innerWidth}x${window.innerHeight} scale=${window.devicePixelRatio || 1}`;
  }

  async function getJSON(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async function postJSON(url, body) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  function renderPrograms(selectEl, programs) {
    selectEl.innerHTML = "";
    if (!programs.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "Aucun fichier dans mouse_programs/";
      selectEl.appendChild(option);
      return;
    }

    programs.forEach((program) => {
      const option = document.createElement("option");
      option.value = program.filename;
      option.textContent = program.filename;
      selectEl.appendChild(option);
    });
  }

  function start(opts) {
    const {
      programsEndpoint,
      runEndpoint,
      selectEl,
      regionEl,
      countEl,
      focusWaitEl,
      outputEl,
      refreshButton,
      runButton,
      estimateRegionButton,
      target,
    } = opts;

    async function refreshPrograms() {
      setOutput(outputEl, "Chargement des programmes...");
      try {
        const programs = await getJSON(programsEndpoint);
        renderPrograms(selectEl, programs);
        setOutput(outputEl, `${programs.length} programme(s) disponible(s).`);
      } catch (err) {
        setOutput(outputEl, `Erreur chargement programmes: ${err.message}`);
      }
    }

    async function runProgram() {
      const filename = selectEl.value;
      if (!filename) {
        setOutput(outputEl, "Aucun programme selectionne.");
        return;
      }

      regionEl.value = estimateScreenRegion(target);
      runButton.disabled = true;
      setOutput(
        outputEl,
        `Lancement de ${filename}...\nRegion visible: ${regionEl.value}\n${describeWindow()}\nF12 pour arreter.`
      );

      try {
        const result = await postJSON(runEndpoint, {
          filename,
          region: regionEl.value.trim(),
          count: Number(countEl.value),
          focus_wait: Number(focusWaitEl.value),
          timeout: 15,
          base_url: window.location.origin,
        });

        const output = [
          `ok=${result.ok}`,
          `returncode=${result.returncode ?? ""}`,
          `duration=${result.duration ? result.duration.toFixed(2) : "0.00"}s`,
          result.run_count ? `clicks=${result.run_count}/${result.requested_count ?? result.run_count}` : "",
          "",
          "STDOUT",
          result.stdout || "(vide)",
          "",
          "STDERR",
          result.stderr || "(vide)",
          result.error ? `\nERROR\n${result.error}` : "",
        ].join("\n");
        setOutput(outputEl, output);
      } catch (err) {
        setOutput(outputEl, `Erreur execution: ${err.message}`);
      } finally {
        runButton.disabled = false;
      }
    }

    refreshButton.addEventListener("click", refreshPrograms);
    runButton.addEventListener("click", runProgram);
    estimateRegionButton.addEventListener("click", () => {
      regionEl.value = estimateScreenRegion(target);
      setOutput(outputEl, `Region estimee: ${regionEl.value}\n${describeWindow()}`);
    });

    refreshPrograms();
  }

  return { start };
})();
