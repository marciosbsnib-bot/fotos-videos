<div align="center">

# 🕹️ Sega Genesis Web Emulator

Emulador de Sega Genesis / Mega Drive corriendo 100% en el navegador — core **genesis_plus_gx** vía [EmulatorJS](https://emulatorjs.org/) (libretro/WASM). Sin instalación, sin backend: cargás tu ROM y jugás.

[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**[▶️ Abrir demo en vivo](https://lautarosantiago.github.io/genesis-web-emulator/)**

</div>

---

## Sobre el core

Se usa **genesis_plus_gx**, el core de Sega Genesis/Mega Drive (y Sega CD, Master System, Game Gear) del proyecto libretro/RetroArch. **BlastEm no tiene un port oficial a WebAssembly/libretro para correr en navegador**, así que se optó por genesis_plus_gx: es el core más preciso y activo disponible para web, con el mismo enfoque que usamos para GBA con mGBA.

## Características

- Corre 100% en el cliente, sin backend ni instalación.
- Carga de ROM `.md` / `.gen` / `.smd` / `.bin` / `.zip` manual desde el navegador (no se distribuye ninguna ROM en este repo).
- Controles por teclado (layout de 6 botones: A B C X Y Z), remapeables desde el menú del emulador.
- Pad digital transparente superpuesto a la pantalla (mouse/touch), visible también en fullscreen, con botones para agrandar/achicar.
- Botón x2 para activar/desactivar el avance rápido con un click.
- Guardado de partida (save states) persistente en el navegador, asociado al nombre del archivo cargado.

## Demo

👉 **https://lautarosantiago.github.io/genesis-web-emulator/**

![Demo del emulador funcionando](assets/demo.gif)

> Para que este link funcione hay que activar GitHub Pages en el repo (Settings → Pages → Branch: `main` → carpeta `/root`). Ver instrucciones más abajo.

## Uso local

1. Cloná el repositorio:
   ```bash
   git clone https://github.com/LautaroSantiago/genesis-web-emulator.git
   cd genesis-web-emulator
   ```

2. Levantá un servidor local (no funciona abriendo el `index.html` directo por `file://` en algunos navegadores):
   ```bash
   python3 -m http.server 8000
   ```

3. Abrí `http://localhost:8000` en el navegador y cargá tu archivo de ROM con el botón de la página.

## Controles por defecto

| Botón Genesis | Tecla |
|---|---|
| D-pad | Flechas ↑ ↓ ← → |
| A | `S` |
| B | `X` |
| C | `Z` |
| X | `Q` |
| Y | `A` |
| Z | `E` |
| Start | `Enter` |
| Mode / Select | `V` |
| Guardado rápido | `1` |
| Carga rápida | `2` |
| Cambiar slot | `3` |

Para remapear teclas: con el juego cargado, pasá el mouse por arriba de la pantalla, abrí el menú del emulador (ícono de engranaje) → **Control Settings**. También hay un botón **"Mostrar controles en pantalla"** para jugar con mouse/touch sin teclado, y un botón **"x2"** para el avance rápido.

## Activar el demo con GitHub Pages

```bash
# en la raíz del repo, después de pushear a main
git checkout -b gh-pages
git push -u origin gh-pages
```

O directamente desde GitHub: **Settings → Pages → Source: branch `main`, carpeta `/ (root)` → Save**. El link queda disponible en unos minutos en `https://lautarosantiago.github.io/genesis-web-emulator/`.

## Nota sobre ROMs

Este repositorio **no incluye ni distribuye ROMs**. Solo funciona con archivos que el usuario ya posee legalmente. El `.gitignore` excluye la carpeta `roms/` y las extensiones típicas de ROM para evitar subirlas por error.

## Tecnología

- [EmulatorJS](https://emulatorjs.org/) — frontend web para RetroArch (core `genesis_plus_gx`).
- HTML / CSS / JavaScript vanilla, sin dependencias de build.

## Autor

<div align="left">

[![GitHub](https://img.shields.io/badge/GitHub-LautaroSantiago-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/LautaroSantiago)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Lautaro%20Subeldia-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/lautaro-subeldia/)

</div>

## Licencia

MIT — ver [LICENSE](LICENSE). No aplica a EmulatorJS ni a los cores de terceros que se cargan desde su CDN, ni a ninguna ROM que el usuario utilice.
