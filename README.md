# Glick
Glickcrypt, otherwise known as Glick, is an all-encompassing program which pulls together my "xTREEM" encryption and decryption programs under 1 central, unified umbrella. While the code for encryption/decryption processing is identical, there are minor changes to the behavior of the programs so that they function in this new suite.

## Web UI

The Docker Compose setup builds the web app directly from the GitHub repository:

```sh
docker compose up --build
```

By default, the app is available at `http://localhost:8080`.

`compose.yaml` uses `https://github.com/kermitine/Glick-WEB.git#main` as the Docker build context, so push changes to `main` before expecting Compose to build them. The service also uses `pull_policy: build` and `build.pull: true` so Compose rebuilds from source and asks the builder to refresh referenced base images.

Optional settings:

```powershell
$env:GLICK_WEB_PORT = "8090"
$env:GLICK_FRAME_ANCESTORS = "'self' https://example.com"
docker compose up --build
```

## Embed

Use `/embed` for iframe placement. The app allows iframe framing by default and posts `glick-web:resize` messages to its parent window.

```html
<div class="glick-web-frame-wrap">
  <div class="glick-web-loader" id="glick-web-loader">
    <span></span>
    <strong>Loading Glick...</strong>
  </div>

  <iframe
    id="glick-web-converter"
    src="http://localhost:8080/embed"
    title="Glick Web converter"
    loading="lazy"
  ></iframe>
</div>

<script>
const glickWebIframe = document.getElementById("glick-web-converter");
const glickWebLoader = document.getElementById("glick-web-loader");
const glickWebLoaderText = glickWebLoader ? glickWebLoader.querySelector("strong") : null;
const glickWebOrigin = new URL(glickWebIframe.src, window.location.href).origin;
let glickWebReady = false;
let glickWebRetries = 0;
let glickWebTimer = null;

function showGlickWebFrame() {
  glickWebReady = true;
  clearTimeout(glickWebTimer);
  if (glickWebLoader) glickWebLoader.hidden = true;
  glickWebIframe.classList.add("is-loaded");
}

function retryGlickWebFrame() {
  if (!glickWebIframe || glickWebReady) return;

  if (glickWebRetries >= 3) {
    if (glickWebLoaderText) {
      glickWebLoaderText.textContent = "Glick is taking longer than expected. Refresh this page to try again.";
    }
    return;
  }

  glickWebRetries += 1;
  if (glickWebLoaderText) {
    glickWebLoaderText.textContent = `Retrying Glick... (${glickWebRetries}/3)`;
  }

  const nextUrl = new URL(glickWebIframe.src, window.location.href);
  nextUrl.searchParams.set("retry", Date.now().toString());
  glickWebIframe.classList.remove("is-loaded");
  glickWebIframe.src = nextUrl.toString();
  startGlickWebWatchdog();
}

function startGlickWebWatchdog() {
  clearTimeout(glickWebTimer);
  glickWebTimer = setTimeout(retryGlickWebFrame, 7000);
}

window.addEventListener("message", event => {
  if (event.origin !== glickWebOrigin) return;
  if (!event.data || event.data.type !== "glick-web:resize") return;

  showGlickWebFrame();
  glickWebIframe.style.height = `${Math.max(360, Math.min(event.data.height, 1600))}px`;
});

startGlickWebWatchdog();
</script>

<style>
.glick-web-frame-wrap {
  position: relative;
  width: 100%;
  min-height: 360px;
}

#glick-web-converter {
  display: block;
  width: 100%;
  height: 520px;
  border: 0;
  opacity: 0;
  transition: opacity 180ms ease;
}

#glick-web-converter.is-loaded {
  opacity: 1;
}

.glick-web-loader {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: grid;
  place-items: center;
  gap: 12px;
  align-content: center;
  min-height: 360px;
  border: 1px solid #303942;
  border-radius: 8px;
  background: #090c10;
  color: #f4f7f8;
  font: 16px/1.4 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.glick-web-loader span {
  width: 34px;
  height: 34px;
  border: 3px solid rgba(242, 31, 53, 0.24);
  border-top-color: #f21f35;
  border-radius: 50%;
  animation: glick-web-spin 800ms linear infinite;
}

.glick-web-loader[hidden] {
  display: none;
}

@keyframes glick-web-spin {
  to { transform: rotate(360deg); }
}
</style>
```

## CLI

For the original terminal flow, run:

```sh
python glick.py
```

## Dependencies

The CLI and web UI use Python's standard library for most behavior. Decryption uses PyEnchant and the `en_US` dictionary.

## License
This repository/project is licensed under the GNU Affero General Public v3.0-or-later. For more information, please consult the LICENSE file (located in the root of the project), or visit https://www.gnu.org/licenses/agpl-3.0.en.html to read the full license.


![kermitine](https://github.com/kermitine/kermitine/blob/b523c5954ea8820f70eb6ff786f2dbec7ce08955/images/kermitine.png)
