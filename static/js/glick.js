(() => {
  const loader = document.getElementById("glick-loader");
  const shell = document.getElementById("glick-shell");
  const form = document.getElementById("converter-form");
  const sourceText = document.getElementById("source-text");
  const resultText = document.getElementById("result-text");
  const convertButton = document.getElementById("convert-button");
  const swapButton = document.getElementById("swap-button");
  const copyButton = document.getElementById("copy-button");
  const clearButton = document.getElementById("clear-button");
  const statusLine = document.getElementById("status-line");

  let resizeTimer = 0;

  function setStatus(message, isError = false) {
    statusLine.textContent = message;
    statusLine.classList.toggle("is-error", isError);
    queueResizeMessage();
  }

  function selectedMode() {
    const input = form.querySelector('input[name="mode"]:checked');
    return input ? input.value : "encrypt";
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

    form.classList.add("is-working");
    convertButton.disabled = true;
    resultText.classList.remove("is-populated");
    setStatus("Converting");

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

      resultText.value = payload.result;
      resultText.classList.add("is-populated");
      setStatus("Converted");
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      form.classList.remove("is-working");
      convertButton.disabled = false;
      queueResizeMessage();
    }
  }

  function swapText() {
    const sourceValue = sourceText.value;
    sourceText.value = resultText.value;
    resultText.value = sourceValue;
    resultText.classList.toggle("is-populated", resultText.value.length > 0);
    setStatus("Swapped");
  }

  async function copyText() {
    if (!resultText.value) {
      setStatus("Nothing to copy");
      return;
    }

    try {
      await navigator.clipboard.writeText(resultText.value);
      setStatus("Copied");
    } catch {
      resultText.focus();
      resultText.select();
      setStatus("Select the output manually", true);
    }
  }

  function clearText() {
    sourceText.value = "";
    resultText.value = "";
    resultText.classList.remove("is-populated");
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
  swapButton.addEventListener("click", swapText);
  copyButton.addEventListener("click", copyText);
  clearButton.addEventListener("click", clearText);
})();
