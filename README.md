# sc2_overlay_for_OBS
OBS overlay suite for StarCraft II tournament casting. Auto-connects to the live game via a local proxy, showing real-time player names, races, and series score. / Suite de overlays para OBS para casteo de torneos de StarCraft II. Se conecta al juego en vivo vía proxy local, mostrando nombres, razas y marcador en tiempo real.

Overlays HTML/CSS/JS (sin Node.js) para transmitir estadísticas de partidas de **StarCraft II** en **OBS Studio**, pensados para casteo de torneos: nombres de jugadores, razas y registro de victorias/derrotas en tiempo real, leyendo directamente el estado del juego.

## Contenido del proyecto

| Archivo | Tipo | Descripción |
|---|---|---|
| `sc2_proxy.py` | Script Python independiente | Proxy CORS que se ejecuta manualmente (`python sc2_proxy.py`) en una consola aparte. Lee la API local de SC2 y expone/escribe los datos para que el overlay los consuma. |
| `sc2_proxy_for_obs.py` | Script para OBS | Misma función que `sc2_proxy.py`, pero empaquetado como **script de OBS** (`Tools -> Scripts`). Se inicia solo al abrir OBS y se detiene solo al cerrarlo, sin consola aparte. Incluye panel de estado en vivo y botón de verificación manual. |
| `SC2 Tournament Overlay.html` | Overlay principal | Fuente de navegador para OBS que muestra nombre, raza y marcador (victorias/derrotas) de la partida en curso, con diseño inspirado en StarCraft II y logos de raza. |
| `SC2 Session Stats Overlay.html` | Overlay secundario | Panel pequeño y semi-transparente para una esquina de pantalla, con el acumulado de la jornada: partidas jugadas, ganadas, perdidas y desglose contra cada raza. |
| `style.css` | Hoja de estilos | CSS compartido con la estética StarCraft II (fuentes Orbitron/Rajdhani, colores por raza, HUD angular). Usado por los overlays HTML. |
| `status.json` | Archivo de datos | Generado y actualizado automáticamente por el proxy. Es el "puente" de datos entre el juego y los overlays. No se edita a mano. |

## ¿Para qué está hecho?

SC2 no permite leer el estado de una partida desde un overlay web por CORS ni por seguridad del navegador. Este proyecto resuelve eso con una arquitectura de 3 capas:

```
SC2 (API local :6119/game)
        │
        ▼
   Proxy en Python (sc2_proxy.py o sc2_proxy_for_obs.py)
        │  escribe
        ▼
   status.json (en la misma carpeta)
        │  leen por fetch()
        ▼
Overlays HTML (Tournament Overlay / Session Stats Overlay) en OBS
```

- El **proxy** es el único componente que habla con SC2 directamente (`http://localhost:6119/game`, requiere lanzar el juego con `-gamestate 6119 -displaymode 1`).
- El proxy **escribe el resultado en `status.json`** de forma atómica (evita lecturas de JSON a medio escribir).
- Los **overlays HTML** nunca contactan a SC2 ni sufren problemas de CORS: solo leen `status.json` cada 1.5 segundos vía `fetch`.
- Ambos overlays identifican "quién soy yo" comparando la constante `MY_PLAYER_NAME` (definida al inicio del `<script>` de cada HTML) contra los nombres que entrega la API, así funcionan aunque el jugador aparezca como `players[0]` o `players[1]`, y aunque distintos miembros del equipo casteen partidas diferentes.

## Requisitos

- Windows (o el sistema donde corra SC2) con Python 3 instalado.
- StarCraft II lanzado con los flags:
  ```
  -gamestate 6119 -displaymode 1
  ```
- OBS Studio con **Browser Source**.
- Si se usa `sc2_proxy_for_obs.py`: el plugin de scripting Python de OBS habilitado (`Tools -> Scripts -> Python Settings`, apuntando a la carpeta de instalación de Python).

## Instalación

1. Descarga los 6 archivos y colócalos **todos en la misma carpeta**:
   ```
   /sc2-overlay/
     ├── sc2_proxy.py
     ├── sc2_proxy_for_obs.py
     ├── SC2 Tournament Overlay.html
     ├── SC2 Session Stats Overlay.html
     ├── style.css
     └── status.json
   ```
2. Elige **una** de las dos opciones para el proxy (no ambas al mismo tiempo, comparten el mismo puerto):
   - **Opción A — Manual (`sc2_proxy.py`)**: útil para pruebas rápidas o para usar el overlay fuera de OBS.
   - **Opción B — Automático (`sc2_proxy_for_obs.py`)**: recomendado para transmisiones, se integra al ciclo de vida de OBS.
3. Antes de usar cualquiera de los dos overlays HTML, abre el archivo con un editor de texto y cambia la constante al inicio del `<script>`:
   ```html
   <script>
     const MY_PLAYER_NAME = "Kvzonbr"; // <-- CAMBIA ESTO por tu usuario de SC2
   </script>
   ```
   Debe coincidir exactamente (mayúsculas/minúsculas incluidas) con el nombre que usas en el juego.

## Uso

### Opción A: proxy manual (`sc2_proxy.py`)

1. Lanza SC2 con los flags indicados arriba y entra a una partida.
2. Abre una consola (PowerShell/CMD) en la carpeta del proyecto y ejecuta:
   ```
   python sc2_proxy.py
   ```
3. Deja esa consola abierta mientras transmites; el proxy consulta la API de SC2 y actualiza `status.json` continuamente.
4. Agrega los overlays a OBS como **Browser Source**, apuntando al archivo HTML local (ver sección "Agregar a OBS").

### Opción B: proxy automático dentro de OBS (`sc2_proxy_for_obs.py`)

1. En OBS: **Tools -> Scripts -> pestaña "Python Settings"** y selecciona la carpeta de tu instalación de Python.
2. En la misma ventana, pestaña de scripts, botón **"+"** y selecciona `sc2_proxy_for_obs.py`.
3. El proxy se inicia automáticamente al cargar el script (y por lo tanto al abrir OBS con el script ya agregado) y se detiene solo al cerrar OBS.
4. Selecciona el script en la lista para ver el **panel de estado** ("Conectado a SC2", "Proxy activo, sin conexión a SC2", etc.) y usar el botón **"Verificar conexión ahora"** si quieres confirmar la conexión sin esperar el próximo ciclo (cada 15 segundos).

### Agregar los overlays a OBS

1. En OBS, agrega una fuente **Browser Source** (Fuente de navegador).
2. En "Local file" (Archivo local), selecciona `SC2 Tournament Overlay.html` (marcador principal) y/o `SC2 Session Stats Overlay.html` (estadística de la jornada).
3. Ajusta el tamaño de la fuente según el diseño (el Tournament Overlay ocupa más espacio; el Session Stats Overlay está pensado para una esquina, con fondo transparente).
4. Si haces cambios a los archivos HTML/CSS después, usa clic derecho sobre la fuente -> **"Actualizar caché de navegador"** para que OBS recargue los cambios.

## Cómo funciona cada overlay

### `SC2 Tournament Overlay.html`
- Muestra nombre y raza (con logo) de cada jugador de la partida actual, más el marcador de la serie en curso.
- El marcador se resetea automáticamente si cambia `MY_PLAYER_NAME` o si se detecta el inicio de una nueva partida.
- Detecta partidas consecutivas contra el mismo rival mediante caídas en `displayTime` (si baja más de 3 segundos respecto al último valor visto, se asume partida nueva).
- Ignora completamente los datos donde `isReplay` es `true` (no contabiliza repeticiones).
- Busca automáticamente un logo `[raza].png/jpg/svg` en la misma carpeta; si no lo encuentra, usa el diseño por defecto.

### `SC2 Session Stats Overlay.html`
- Panel compacto y semi-transparente pensado para dejar visible en una esquina toda la sesión de casteo.
- Acumula: partidas jugadas, ganadas, perdidas, y el desglose de victorias/derrotas contra cada raza (Terran/Protoss/Zerg).
- Los datos persisten en `localStorage` del navegador de OBS, así sobreviven a recargas de la fuente.
- Incluye botón "Reset" para reiniciar manualmente el conteo de la jornada.
- Aplica la misma lógica de identificación por `MY_PLAYER_NAME`, filtrado de replays y detección de partidas consecutivas que el overlay principal.

### `style.css`
- Hoja de estilos compartida: paleta de colores por raza, tipografías Orbitron/Rajdhani, indicador de conexión a la API, y estilo general "HUD" inspirado en StarCraft II.
- Se edita en un solo lugar y afecta a ambos overlays HTML que lo referencian (`<link rel="stylesheet" href="style.css">`).

### `sc2_proxy.py` / `sc2_proxy_for_obs.py`
- Ambos hacen lo mismo: consultan `http://localhost:6119/game` (API local que expone SC2 al lanzarse con los flags indicados) y escriben el resultado en `status.json` de forma atómica (usando un archivo temporal + `os.replace`), evitando que los overlays lean un JSON a medio escribir.
- `sc2_proxy.py` corre como script independiente en una consola.
- `sc2_proxy_for_obs.py` corre embebido en OBS como script (`obspython`), con inicio/parada automáticos ligados al ciclo de vida de OBS y un panel de estado visible en `Tools -> Scripts`.

### `status.json`
- Archivo generado automáticamente por el proxy activo. Contiene la última lectura de la API de SC2, por ejemplo:
  ```json
  {"isReplay": false, "displayTime": 187.0, "players": [
    {"id": 1, "name": "Kvzonbr", "type": "user", "race": "Terr", "result": "Undecided"},
    {"id": 2, "name": "A.I. 1 (Very Easy)", "type": "computer", "race": "random", "result": "Undecided"}
  ]}
  ```
- No debe editarse manualmente; si se borra, el proxy lo vuelve a crear en el siguiente ciclo.

## Solución de problemas

| Síntoma | Causa probable / solución |
|---|---|
| El overlay muestra "Sin conexión" | El proxy no está corriendo, o SC2 no fue lanzado con `-gamestate 6119 -displaymode 1`. Verifica con el navegador que `http://localhost:6119/game` responda. |
| Error de CORS en la consola de OBS | Ocurre si el overlay intenta leer directamente la API de SC2 en vez de `status.json`. Usa siempre el flujo proxy -> `status.json` -> overlay. |
| El proxy manual se cierra solo | Ejecútalo desde una consola (PowerShell/CMD) con `python sc2_proxy.py` y revisa que no haya errores de sintaxis en el archivo. |
| Cambios en HTML/CSS no se reflejan en OBS | Clic derecho en la fuente -> "Actualizar caché de navegador". |
| No contabiliza correctamente tras ver una repetición | Asegúrate de tener la versión del overlay que ignora `isReplay` y fuerza detección de partida nueva al volver de un replay (incluida en los archivos de esta entrega). |
| Se pierde una partida jugada dos veces seguidas contra el mismo rival | El overlay usa el `displayTime` para detectar reinicios; si el salto es menor a 3 segundos podría no detectarse, repórtalo si ocurre de forma consistente. |

## Notas para el equipo

- Cada persona que use estos overlays en su propia máquina debe **editar `MY_PLAYER_NAME`** en ambos archivos HTML para que las estadísticas se le atribuyan correctamente a su usuario.
- No ejecutar `sc2_proxy.py` y `sc2_proxy_for_obs.py` al mismo tiempo: ambos usan el puerto `6120` y chocarían entre sí.
- Todo el proyecto es **standalone**: no requiere Node.js, npm ni instalación de dependencias adicionales más allá de Python 3 (incluido en la instalación estándar de Windows/macOS/Linux con `http.server`, `urllib`, `json`, `threading` y `os`, todas librerías estándar).
