(() => {
  const loader = document.getElementById("glick-loader");
  const shell = document.getElementById("glick-shell");
  const form = document.getElementById("converter-form");
  const sourceText = document.getElementById("source-text");
  const resultText = document.getElementById("result-text");
  const convertButton = document.getElementById("convert-button");
  const clearButton = document.getElementById("clear-button");
  const statusLine = document.getElementById("status-line");
  const processLog = document.getElementById("process-log");
  const consoleState = document.getElementById("console-state");

  let resizeTimer = 0;
  let activeRun = 0;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function setStatus(message, isError = false) {
    statusLine.textContent = message;
    statusLine.classList.toggle("is-error", isError);
    queueResizeMessage();
  }

  function selectedMode() {
    const input = form.querySelector('input[name="mode"]:checked');
    return input ? input.value : "encrypt";
  }

  function sleep(milliseconds) {
    return new Promise(resolve => {
      window.setTimeout(resolve, reduceMotion ? 0 : milliseconds);
    });
  }

  function setConsoleState(state) {
    consoleState.textContent = state;
  }

  function isWordStep(line) {
    return /^\d+:\s/.test(line);
  }

  function getResultChunks(text) {
    return text.match(/\S+\s*/g) || [];
  }

  async function typeResultChunk(chunk, runId) {
    for (const character of chunk) {
      if (runId !== activeRun) return false;

      resultText.value += character;
      resultText.scrollTop = resultText.scrollHeight;
      await sleep(24);
    }

    return true;
  }

  async function renderSyncedConversion(lines, result, runId) {
    const entries = Array.isArray(lines) && lines.length > 0 ? lines : ["no process data"];
    const resultChunks = getResultChunks(result);
    let nextChunk = 0;

    processLog.textContent = "";
    resultText.value = "";
    resultText.classList.remove("is-populated");
    setConsoleState("running");

    for (const line of entries) {
      if (runId !== activeRun) return false;

      processLog.textContent += `${line}\n`;
      processLog.scrollTop = processLog.scrollHeight;
      queueResizeMessage();

      if (isWordStep(line) && nextChunk < resultChunks.length) {
        const chunkFinished = await typeResultChunk(resultChunks[nextChunk], runId);
        if (!chunkFinished) return false;
        nextChunk += 1;
      } else {
        await sleep(170);
      }
    }

    while (nextChunk < resultChunks.length) {
      const chunkFinished = await typeResultChunk(resultChunks[nextChunk], runId);
      if (!chunkFinished) return false;
      nextChunk += 1;
    }

    resultText.value = result;
    resultText.classList.add("is-populated");
    setConsoleState("done");
    queueResizeMessage();
    return true;
  }

  function queueResizeMessage() {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(postResizeMessage, 60);
  }

  function postResizeMessage() {
    const height = Math.ceil(document.documentElement.scrollHeight);
    window.parent.postMessage({ type: "glick-web:resize", height }, "*");
  }

  function reveal() {
    if (loader) {
      loader.hidden = true;
    }

    if (shell) {
      shell.classList.add("is-loaded");
    }

    postResizeMessage();
  }

  async function convertText(event) {
    event.preventDefault();
    const runId = activeRun + 1;
    activeRun = runId;

    form.classList.add("is-working");
    convertButton.disabled = true;
    resultText.classList.remove("is-populated");
    resultText.value = "";
    setStatus("Converting");
    setConsoleState("queued");
    processLog.textContent = "starting\n";

    try {
      const response = await fetch("api/convert", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          mode: selectedMode(),
          text: sourceText.value,
        }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Conversion failed.");
      }

      const conversionFinished = await renderSyncedConversion(payload.steps, payload.result, runId);
      if (!conversionFinished) return;

      setStatus("Converted");
    } catch (error) {
      setStatus(error.message, true);
      setConsoleState("error");
      processLog.textContent += `error: ${error.message}\n`;
    } finally {
      if (runId === activeRun) {
        form.classList.remove("is-working");
        convertButton.disabled = false;
        queueResizeMessage();
      }
    }
  }

  function clearText() {
    activeRun += 1;
    form.classList.remove("is-working");
    convertButton.disabled = false;
    sourceText.value = "";
    resultText.value = "";
    resultText.classList.remove("is-populated");
    processLog.textContent = "waiting for input";
    setConsoleState("idle");
    setStatus("Ready");
    sourceText.focus();
  }

  window.addEventListener("load", () => {
    window.setTimeout(reveal, 180);
  });
  window.addEventListener("resize", queueResizeMessage);

  if ("ResizeObserver" in window) {
    const observer = new ResizeObserver(queueResizeMessage);
    observer.observe(document.documentElement);
    observer.observe(document.body);
  }

  form.addEventListener("submit", convertText);
  sourceText.addEventListener("input", queueResizeMessage);
  resultText.addEventListener("input", queueResizeMessage);
  clearButton.addEventListener("click", clearText);
})();
