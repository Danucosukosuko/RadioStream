#!/usr/bin/env python3
"""
RadioStream - main.py
Este código está bajo GNU GPLv3
"""
import os
import json
import secrets
from functools import wraps
from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from flask import (
    Flask, request, render_template_string, redirect, url_for,
    session, flash
)

# ---------------- Paths y constantes ----------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
STATIC_DIR = BASE_DIR / "static"
COVER_FILENAME = "cover.png"
BACKGROUND_FILENAME = "background.png"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
DEFAULT_PORT = 4080

STATIC_DIR.mkdir(exist_ok=True)

# ---------------- Tema por defecto ----------------
DEFAULT_THEME = {
    "body_bg": "#0f172a",
    "card_bg": "linear-gradient(180deg,#071028 0%, #071b2a 100%)",
    "cover_bg": "#0b1220",
    "accent1": "#00c2a8",
    "accent2": "#007a66",
    "text": "#e6eef8",
    "muted": "#9fb3cf"
}

# ---------------- Config load/save ----------------
def load_config():
    if not CONFIG_PATH.exists():
        default = {
            "port": DEFAULT_PORT,
            "station_label": "RadioStream",
            "description": "Descripción breve de la emisora.",
            "audio_url": "",
            "username": "admin",
            "password_hash": generate_password_hash("admin"),
            "secret_key": secrets.token_hex(32),
            "theme": DEFAULT_THEME,
            "background_enabled": False,
            "background_filename": "",
        }
        save_config(default)
        return default
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg.setdefault("port", DEFAULT_PORT)
    cfg.setdefault("station_label", "RadioStream")
    cfg.setdefault("description", "Descripción breve de la emisora.")
    cfg.setdefault("audio_url", "")
    cfg.setdefault("username", "admin")
    cfg.setdefault("password_hash", generate_password_hash("admin"))
    cfg.setdefault("secret_key", secrets.token_hex(32))
    cfg.setdefault("theme", DEFAULT_THEME)
    cfg.setdefault("background_enabled", False)
    cfg.setdefault("background_filename", "")
    return cfg

def save_config(cfg):
    tmp = CONFIG_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    tmp.replace(CONFIG_PATH)

config = load_config()

# ---------------- Flask app ----------------
app = Flask(__name__, static_folder=str(STATIC_DIR))
app.secret_key = config.get("secret_key") or secrets.token_hex(32)

# ---------------- Utilidades ----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cover_exists():
    return (STATIC_DIR / COVER_FILENAME).exists()

def background_exists():
    return (STATIC_DIR / BACKGROUND_FILENAME).exists()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("user") != config.get("username"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated

# ---------------- Templates ----------------
# Página pública principal (incluye modal embed con opción autoplay)
INDEX_HTML = """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ station_label }} — RadioStream</title>
<style>
  :root{
    --body-bg: {{ theme.body_bg }};
    --card-bg: {{ theme.card_bg }};
    --cover-bg: {{ theme.cover_bg }};
    --accent1: {{ theme.accent1 }};
    --accent2: {{ theme.accent2 }};
    --text-color: {{ theme.text }};
    --muted: {{ theme.muted }};
  }
  html,body{height:100%;margin:0}
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;background:var(--body-bg);color:var(--text-color);display:flex;align-items:center;justify-content:center;padding:20px;min-height:100vh;overflow-x:hidden;}
  #bg { position:fixed; inset:0; z-index:0; background-position:center; background-size:cover; filter: blur(10px) saturate(1.05); transform: scale(1.05); transition: opacity .4s ease; }
  #bg.hidden { opacity:0; pointer-events:none; } #bg.visible { opacity:1; }
  #bg-overlay { position:fixed; inset:0; background:rgba(2,6,23,0.45); z-index:0; pointer-events:none; transition:opacity .4s ease; }

  .wrap { position:relative; z-index:2; width:100%; max-width:1000px; display:flex; justify-content:center; }
  .card{ width:100%; max-width:1000px; background:var(--card-bg); border-radius:16px; padding:20px; box-shadow:0 6px 30px rgba(2,6,23,0.6);
        display:grid; grid-template-columns:420px 1fr; gap:20px; align-items:center; transition: all .35s cubic-bezier(.2,.9,.2,1); position:relative; }

  .card.minimized{ position:fixed; left:50%; bottom:16px; transform:translateX(-50%); width:520px; max-width:calc(100% - 32px); border-radius:12px; padding:10px 14px; display:flex; align-items:center; gap:12px; z-index:9999; }

  .cover{ width:100%; height:420px; border-radius:16px; display:flex; align-items:center; justify-content:center; overflow:hidden; background:var(--cover-bg); border:4px solid rgba(255,255,255,0.03); flex:0 0 420px; }
  .card.minimized .cover{ width:72px; height:72px; border-radius:10px; flex:0 0 72px; overflow:hidden; border:2px solid rgba(255,255,255,0.04); }
  .cover img{ width:100%; height:100%; object-fit:cover; display:block; }
  .no-cover{ color:var(--muted); font-size:20px; text-align:center; padding:10px; }
  .meta{ padding:10px; display:flex; flex-direction:column; gap:8px; }
  .card.minimized .meta{ padding:0; flex:1; justify-content:center; }
  h1{ margin:0 0 8px 0; font-size:24px; }
  /* Descripción un pelín más grande */
  p.desc{ margin:0 0 8px 0; color:var(--muted); font-size:15px; }
  .controls{ display:flex; gap:12px; align-items:center; }
  .play-btn{ position:relative; width:64px; height:64px; border-radius:50%; display:flex; align-items:center; justify-content:center; background:linear-gradient(180deg,var(--accent1),var(--accent2)); box-shadow:0 6px 20px rgba(0,0,0,0.5); cursor:pointer; border:none; font-size:26px; color:white; }
  .play-btn[disabled]{ opacity:0.6; cursor:not-allowed }
  .stop-btn{ position:relative; width:64px; height:64px; border-radius:12px; display:flex; align-items:center; justify-content:center; background:linear-gradient(180deg,#e05555,#b02020); box-shadow:0 6px 20px rgba(0,0,0,0.5); cursor:pointer; border:none; color:white; font-size:20px; }
  .spinner{ position:absolute; width:30px; height:30px; border-radius:50%; left:50%; top:50%; transform:translate(-50%,-50%); border:4px solid rgba(255,255,255,0.12); border-top-color: rgba(255,255,255,0.95); animation: spin 1s linear infinite; display:none; }
  @keyframes spin { to { transform: translate(-50%,-50%) rotate(360deg); } }
  .info{ font-size:13px; color:var(--muted); margin-left:8px; }
  .small{ font-size:12px; color:var(--muted); margin-top:4px; }
  .admin-link{ position:fixed; right:14px; top:14px; background:#111827; color:var(--text-color); padding:8px 12px; border-radius:10px; text-decoration:none; z-index:10000; display:inline-flex; gap:8px; align-items:center; }
  .embed-btn { background:#1f2937; color:var(--text-color); padding:8px 10px; border-radius:8px; border:none; cursor:pointer; }
  .minimize-btn{ background:transparent; border:1px solid rgba(255,255,255,0.05); padding:8px; border-radius:8px; color:var(--muted); cursor:pointer; }
  footer{ margin-top:8px; color:var(--muted); font-size:12px; }

  /* Modal embed */
  .modal { position:fixed; inset:0; display:none; align-items:center; justify-content:center; z-index:12000; background:rgba(0,0,0,0.45); }
  .modal.show{ display:flex; }
  .modal-box { background: #071024; padding:18px; border-radius:10px; width:90%; max-width:680px; color:var(--text-color); box-shadow:0 10px 40px rgba(2,6,23,0.7); }
  .modal-box textarea{ width:100%; height:90px; padding:10px; border-radius:8px; background:#0b1220; color:var(--text-color); border:1px solid rgba(255,255,255,0.04); }
  .modal-row{display:flex;align-items:center;gap:8px;margin-top:8px}
  .modal-actions{ display:flex; gap:8px; justify-content:flex-end; margin-top:10px; }

  @media(max-width:640px){
    .card{ grid-template-columns:1fr; max-width:calc(100% - 32px); }
    .cover{ height:320px; }
    .card.minimized{ width:calc(100% - 32px); left:16px; transform:none; }
  }
</style>
</head>
<body>
  {% if background_enabled and background_filename %}
    <div id="bg" class="visible" style="background-image: url('{{ url_for('static', filename=background_filename) }}');"></div>
    <div id="bg-overlay"></div>
  {% else %}
    <div id="bg" class="hidden"></div>
    <div id="bg-overlay" style="opacity:0"></div>
  {% endif %}

  <a class="admin-link" href="{{ url_for('admin') }}">
    ⚙️ Admin
    <button id="openEmbed" class="embed-btn" title="Obtener iframe">Embed</button>
  </a>

  <div class="wrap">
    <div id="card" class="card" role="region" aria-label="RadioStream player">
      <div class="cover" aria-hidden="true">
        {% if cover %}
          <img src="{{ url_for('static', filename=cover_filename) }}" alt="Cover">
        {% else %}
          <div class="no-cover">No cover found</div>
        {% endif %}
      </div>

      <div class="meta">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <h1 id="stationLabel">{{ station_label }}</h1>
            <p class="desc" id="stationDesc">{{ description }}</p>
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
            <button id="minimizeBtn" class="minimize-btn" title="Minimizar" aria-pressed="false">—</button>
            <div style="height:6px"></div>
          </div>
        </div>

        <div style="display:flex;align-items:center;gap:12px;">
          <button id="playBtn" class="play-btn" title="Play" aria-pressed="false">
            <span id="playIcon">▶</span>
            <span class="spinner" id="spinner" role="status" aria-hidden="true"></span>
          </button>

          <div class="info" aria-live="polite">
            <div id="status">Listo para reproducir</div>
            <div class="small">Fuente: <em>oculta</em></div>
          </div>
        </div>

        <footer>
          <div id="footerInfo">Reproductor RadioStream</div>
        </footer>
      </div>
    </div>
  </div>

  <!-- Modal embed -->
  <div id="embedModal" class="modal" role="dialog" aria-hidden="true">
    <div class="modal-box" role="document" aria-label="Embed code">
      <h3>Iframe para embeber</h3>
      <p class="small" style="color:var(--muted)">Copia el código y pégalo donde quieras.</p>

      <div class="modal-row">
        <label style="color:var(--muted)"><input type="checkbox" id="autoplayCheck"> Autoplay (&nbsp;?autoplay=1&nbsp;)</label>
      </div>

      <textarea id="embedCode" readonly></textarea>
      <div class="modal-actions">
        <button id="copyEmbed" class="embed-btn">Copiar</button>
        <button id="closeModal" class="embed-btn">Cerrar</button>
      </div>
    </div>
  </div>

  <audio id="player" preload="none"></audio>

<script>
  const playBtn = document.getElementById("playBtn");
  const player = document.getElementById("player");
  const audioUrl = "{{ audio_url|e }}";
  const status = document.getElementById("status");
  const spinner = document.getElementById("spinner");
  const playIcon = document.getElementById("playIcon");
  const card = document.getElementById("card");
  const minimizeBtn = document.getElementById("minimizeBtn");

  const openEmbed = document.getElementById("openEmbed");
  const embedModal = document.getElementById("embedModal");
  const embedCode = document.getElementById("embedCode");
  const copyEmbed = document.getElementById("copyEmbed");
  const closeModal = document.getElementById("closeModal");
  const autoplayCheck = document.getElementById("autoplayCheck");

  let playing = false;
  let loading = false;
  let minimized = false;
  let intentionalStop = false;

  function showSpinner(v){
    spinner.style.display = v ? "block" : "none";
    playIcon.style.opacity = v ? "0" : "1";
  }

  function setPlayState(p){
    playing = p;
    if(playing){
      playBtn.className = "stop-btn";
      playIcon.textContent = "■";
      playIcon.style.opacity = 1;
      status.textContent = "Reproduciendo";
      playBtn.setAttribute("aria-pressed","true");
    } else {
      playBtn.className = "play-btn";
      playIcon.textContent = "▶";
      playIcon.style.opacity = 1;
      status.textContent = "Pausado";
      playBtn.setAttribute("aria-pressed","false");
    }
  }

  player.addEventListener("playing", () => {
    loading = false;
    playBtn.disabled = false;
    showSpinner(false);
    setPlayState(true);
  });

  player.addEventListener("canplay", () => {
    if (loading) {
      player.play().catch(()=>{});
    }
  });

  player.addEventListener("error", (e) => {
    if(intentionalStop){
      intentionalStop = false;
      return;
    }
    loading = false;
    playBtn.disabled = false;
    showSpinner(false);
    setPlayState(false);
    console.error("Audio error", e);
    alert("Error al cargar el stream. Revisa la URL o el CORS del servidor de audio.");
  });

  player.addEventListener("pause", ()=> {
    if(player.src === "") setPlayState(false);
  });

  playBtn.addEventListener("click", async () => {
    if(loading) return;

    if(!playing){
      if(!audioUrl){
        alert("No hay URL de audio configurada. Ve a /admin y pon una URL.");
        return;
      }
      loading = true;
      intentionalStop = false;
      playBtn.disabled = true;
      showSpinner(true);
      status.textContent = "Cargando...";
      player.src = audioUrl;
      player.crossOrigin = "anonymous";

      try {
        await player.play();
      } catch (err){
        loading = false;
        playBtn.disabled = false;
        showSpinner(false);
        console.error("Play promise rejected:", err);
        alert("No se pudo iniciar la reproducción automáticamente. Interactúa con la página o revisa la URL/CORS.");
      }
    } else {
      intentionalStop = true;
      player.pause();
      player.currentTime = 0;
      player.src = "";
      loading = false;
      showSpinner(false);
      setPlayState(false);
      playBtn.disabled = false;
      setTimeout(() => { intentionalStop = false; }, 700);
    }
  });

  function setMinimized(v){
    minimized = v;
    if(minimized){
      card.classList.add("minimized");
      minimizeBtn.textContent = "⬆";
      minimizeBtn.title = "Restaurar";
      minimizeBtn.setAttribute("aria-pressed","true");
      document.body.style.paddingBottom = "90px";
    } else {
      card.classList.remove("minimized");
      minimizeBtn.textContent = "—";
      minimizeBtn.title = "Minimizar";
      minimizeBtn.setAttribute("aria-pressed","false");
      document.body.style.paddingBottom = "";
    }
  }

  minimizeBtn.addEventListener("click", () => setMinimized(!minimized));
  card.addEventListener("dblclick", () => { if(minimized) setMinimized(false); });

  // Embed modal handling
  openEmbed.addEventListener("click", (e) => {
    e.preventDefault();
    const base = "{{ embed_url }}";
    // empezamos sin autoplay
    autoplayCheck.checked = false;
    const code = `<iframe src="${base}" width="420" height="180" frameborder="0" allow="autoplay; encrypted-media" sandbox="allow-scripts allow-same-origin"></iframe>`;
    embedCode.value = code;
    embedModal.classList.add("show");
    embedModal.setAttribute("aria-hidden","false");
  });

  autoplayCheck.addEventListener("change", () => {
    const base = "{{ embed_url }}";
    const has = autoplayCheck.checked;
    const url = has ? `${base}?autoplay=1` : base;
    const code = `<iframe src="${url}" width="420" height="180" frameborder="0" allow="autoplay; encrypted-media" sandbox="allow-scripts allow-same-origin"></iframe>`;
    embedCode.value = code;
  });

  closeModal.addEventListener("click", () => {
    embedModal.classList.remove("show");
    embedModal.setAttribute("aria-hidden","true");
  });

  copyEmbed.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(embedCode.value);
      copyEmbed.textContent = "Copiado ✓";
      setTimeout(()=> copyEmbed.textContent = "Copiar", 1500);
    } catch (err) {
      console.error("Copy failed", err);
      alert("No se pudo copiar automáticamente. Selecciona el texto y cópialo manualmente.");
    }
  });

  // Cerrar modal al pulsar fuera
  embedModal.addEventListener("click", (ev) => {
    if(ev.target === embedModal) {
      embedModal.classList.remove("show");
      embedModal.setAttribute("aria-hidden","true");
    }
  });

  // Restaurar minimizado según sessionStorage
  window.addEventListener("beforeunload", () => {
    sessionStorage.setItem("radiostream_minimized", minimized ? "1" : "0");
  });
  document.addEventListener("DOMContentLoaded", () => {
    if(sessionStorage.getItem("radiostream_minimized")==="1") setMinimized(true);
  });
</script>
</body>
</html>
"""

# Embed minimal page (para iframe). Soporta ?autoplay=1 y añade slider de volumen.
EMBED_HTML = """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RadioStream Embed</title>
<style>
  :root{
    --accent1: {{ theme.accent1 }};
    --accent2: {{ theme.accent2 }};
    --text: {{ theme.text }};
    --muted: {{ theme.muted }};
  }
  html,body{margin:0;padding:8px;font-family:system-ui,Arial;background:transparent;color:var(--text)}
  .box{background:rgba(10,10,10,0.6);backdrop-filter:blur(4px);border-radius:8px;padding:8px;display:flex;gap:10px;align-items:center;}
  .cover{width:64px;height:64px;border-radius:6px;overflow:hidden;background:#031018;flex:0 0 64px}
  .cover img{width:100%;height:100%;object-fit:cover}
  .info{flex:1;min-width:0}
  .title{font-size:14px;margin:0 0 4px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .desc{font-size:11px;margin:0;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .controls{display:flex;flex-direction:column;align-items:center;gap:6px}
  .play{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(180deg,var(--accent1),var(--accent2));color:white;border:none;cursor:pointer;font-size:18px}
  .play[disabled]{opacity:0.6;cursor:not-allowed}
  .spinner{ width:20px;height:20px;border-radius:50%;border:3px solid rgba(255,255,255,0.12);border-top-color:white; animation:spin .9s linear infinite; display:none }
  @keyframes spin{ to{ transform:rotate(360deg); } }

  /* Slider styles - use accent color */
  .vol-wrap{display:flex;flex-direction:column;align-items:center;gap:6px;width:130px}
  .vol-label{font-size:11px;color:var(--muted)}
  input[type=range].vol{
    -webkit-appearance: none; width:100%; height:6px; border-radius:6px; background:linear-gradient(90deg,var(--accent1),var(--accent2));
    outline:none;
  }
  input[type=range].vol::-webkit-slider-thumb {
    -webkit-appearance: none; appearance:none; width:16px; height:16px; border-radius:50%;
    background: white; box-shadow: 0 2px 6px rgba(0,0,0,0.4); cursor:pointer;
  }
  .powered{ font-size:10px;color:var(--muted); text-align:center; margin-top:6px }
</style>
</head>
<body>
  <div class="box" role="region" aria-label="Embed RadioStream">
    <div class="cover">
      {% if cover %}
        <img src="{{ url_for('static', filename=cover_filename) }}" alt="Cover">
      {% else %}
        <div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--muted);font-size:12px">No cover</div>
      {% endif %}
    </div>

    <div class="info">
      <div class="title">{{ station_label }}</div>
      <div class="desc">{{ description }}</div>
    </div>

    <div class="controls" style="flex-direction:row;gap:10px;align-items:center">
      <div style="display:flex;flex-direction:column;align-items:center">
        <button id="play" class="play" title="Play">▶</button>
        <div class="spinner" id="spinner" aria-hidden="true"></div>
      </div>

      <div class="vol-wrap" aria-hidden="false">
        <div class="vol-label">Vol: <span id="volPerc">100%</span></div>
        <input id="volSlider" class="vol" type="range" min="0" max="100" value="100" step="1" aria-label="Volumen">
      </div>
    </div>
  </div>

  <div class="powered">Powered by RadioStream</div>

  <audio id="player" preload="none"></audio>

<script>
  const params = new URLSearchParams(location.search);
  const autoplay = params.get("autoplay") === "1";

  const audioUrl = "{{ audio_url|e }}";
  const play = document.getElementById("play");
  const spinner = document.getElementById("spinner");
  const player = document.getElementById("player");
  const volSlider = document.getElementById("volSlider");
  const volPerc = document.getElementById("volPerc");

  let loading = false;
  let playing = false;
  let intentional = false;

  function showSpinner(v){ spinner.style.display = v ? "block" : "none"; play.style.opacity = v ? "0.35" : "1"; play.disabled = v; }

  // Inicial volumen desde slider (0-100 -> 0.0-1.0)
  function applyVolumeFromSlider() {
    const v = Math.max(0, Math.min(100, Number(volSlider.value)));
    player.volume = v / 100;
    volPerc.textContent = `${v}%`;
  }
  applyVolumeFromSlider();

  player.addEventListener("playing", () => { loading = false; showSpinner(false); play.textContent = "■"; playing = true; });
  player.addEventListener("pause", ()=> { if(player.src === "") { play.textContent = "▶"; playing=false; }});
  player.addEventListener("error", (e)=>{ if(intentional){ intentional=false; return; } showSpinner(false); playing=false; play.textContent = "▶"; console.error("Embed audio error", e); });

  play.addEventListener("click", async ()=>{
    if(loading) return;
    if(!playing){
      if(!audioUrl){ alert("Stream no configurado"); return; }
      loading = true; intentional = false; showSpinner(true);
      player.src = audioUrl; player.crossOrigin = "anonymous";
      // aplicar volumen actual antes de play
      applyVolumeFromSlider();
      try{
        await player.play();
      }catch(e){
        loading=false; showSpinner(false);
        console.error("Autoplay/play error:",e);
        // No hacemos alert ruidoso aquí; en embed preferimos no molestar
      }
    } else {
      intentional = true;
      player.pause(); player.currentTime = 0; player.src="";
      showSpinner(false); playing=false; play.textContent = "▶";
      setTimeout(()=> intentional=false,500);
    }
  });

  // slider events
  volSlider.addEventListener("input", () => {
    applyVolumeFromSlider();
  });
  volSlider.addEventListener("change", () => {
    applyVolumeFromSlider();
  });

  // si llega autoplay param, intentar iniciar
  if(autoplay && audioUrl){
    // intentar un play con small delay para que eventos se preparen
    setTimeout(async () => {
      try {
        loading = true;
        showSpinner(true);
        player.src = audioUrl;
        player.crossOrigin = "anonymous";
        applyVolumeFromSlider();
        await player.play();
      } catch (e) {
        console.error("Autoplay intent failed:", e);
        loading = false;
        showSpinner(false);
        // No alert en iframe
      }
    }, 120);
  }
</script>
</body>
</html>
"""

# ---------------- Rutas ----------------
@app.route("/")
def index():
    cover = cover_exists()
    bg_exists = background_exists()
    theme = config.get("theme", DEFAULT_THEME)
    embed_url = url_for("embed", _external=True)
    return render_template_string(
        INDEX_HTML,
        cover=cover,
        cover_filename=COVER_FILENAME,
        background_enabled=config.get("background_enabled", False),
        background_filename=config.get("background_filename", BACKGROUND_FILENAME) if config.get("background_filename") else BACKGROUND_FILENAME,
        background_exists=bg_exists,
        station_label=config.get("station_label", ""),
        description=config.get("description", ""),
        audio_url=config.get("audio_url", ""),
        theme=theme,
        embed_url=embed_url
    )

@app.route("/embed")
def embed():
    """Página ligera pensada para incluir en un iframe. Soporta ?autoplay=1"""
    cover = cover_exists()
    theme = config.get("theme", DEFAULT_THEME)
    return render_template_string(
        EMBED_HTML,
        cover=cover,
        cover_filename=COVER_FILENAME,
        station_label=config.get("station_label", ""),
        description=config.get("description", ""),
        audio_url=config.get("audio_url", ""),
        theme=theme
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        cfg_user = config.get("username", "admin")
        cfg_hash = config.get("password_hash", "")
        if u == cfg_user and check_password_hash(cfg_hash, p):
            session["user"] = u
            flash("Acceso concedido. Bienvenido 😀")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin"))
        else:
            flash("Usuario o contraseña incorrectos.")
            return redirect(url_for("login"))
    # simple login template
    return render_template_string("""
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Login</title>
<style>body{font-family:system-ui;background:#071022;color:#dbeafe;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}.box{background:#0b1726;padding:28px;border-radius:12px;width:360px}</style>
</head><body><div class="box"><h2>Admin Login 🔐</h2>{% with messages = get_flashed_messages() %}{% if messages %}<div style="background:#042f2a;padding:8px;border-radius:8px;margin-bottom:10px;color:#b3f0df">{{ messages[0] }}</div>{% endif %}{% endwith %}<form method="post"><label>Usuario</label><input name="username" required style="width:100%;padding:8px;margin:6px 0"><label>Contraseña</label><input name="password" type="password" required style="width:100%;padding:8px;margin:6px 0"><button style="width:100%;padding:10px;margin-top:8px;background:#065f46;color:white;border:none;border-radius:8px">Entrar</button></form></div></body></html>
""")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Sesión cerrada.")
    return redirect(url_for("login"))

# Admin template (compacto) - añade preview en tiempo real a la derecha
ADMIN_HTML = """
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin — RadioStream</title>
<style>body{font-family:system-ui;background:#071022;color:#e6eef8;margin:0;padding:20px}.wrap{max-width:1200px;margin:20px auto;background:#071628;padding:18px;border-radius:12px}label{display:block;font-size:13px;margin-top:8px;color:#9fb3cf}input,textarea{width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.05);background:#031020;color:#e6eef8}textarea{min-height:120px} .right-card{background:#0b1726;padding:12px;border-radius:10px}.preview{width:100%;height:220px;border-radius:12px;display:flex;align-items:center;justify-content:center;overflow:hidden;background:#00111b;border:2px dashed rgba(255,255,255,0.03)}.btn-save{background:#0ea5a4;color:#012;padding:10px;border-radius:8px;border:none}.btn-logout{background:#ef4444;color:white;padding:10px;border-radius:8px;border:none}
.admin-grid{display:grid;grid-template-columns:1fr 420px;gap:18px}
.live-preview{background:linear-gradient(180deg,#071028,#071b2a);border-radius:10px;padding:12px;color:#e6eef8}
.live-preview .cover{width:100%;height:160px;border-radius:8px;overflow:hidden;background:#08121a;display:flex;align-items:center;justify-content:center}
.live-preview .cover img{width:100%;height:100%;object-fit:cover}
.live-preview h3{margin:8px 0 4px 0;font-size:18px}
.live-preview p{margin:0;color:#9fb3cf;font-size:14px}
.preview-controls{display:flex;gap:10px;align-items:center;margin-top:8px}
.color-swatch{width:28px;height:28px;border-radius:6px;border:1px solid rgba(255,255,255,0.06)}
.small-muted{font-size:12px;color:#9fb3cf;margin-top:8px}
</style>
</head><body>
<div style="display:flex;justify-content:space-between;align-items:center;max-width:1200px;margin:10px auto;"><div>Logged in as <strong>{{ current_user }}</strong> ✅</div><div><a href="{{ url_for('index') }}" style="margin-right:10px;color:#9fb3cf;text-decoration:none">← Ver sitio</a><a href="{{ url_for('logout') }}" class="btn-logout">Cerrar sesión</a></div></div>

<div class="wrap">
  <h1>Panel de administración ⚙️ — RadioStream</h1>
  {% with messages = get_flashed_messages() %}{% if messages %}<div style="background:#042f2a;padding:8px;border-radius:8px;margin-bottom:10px;color:#b3f0df">{{ messages[0] }}</div>{% endif %}{% endwith %}

  <form method="post" enctype="multipart/form-data" style="margin-top:12px">
    <div class="admin-grid">
      <div>
        <label>Label de la emisora</label><input id="fieldStation" name="station_label" value="{{ station_label|e }}" required>
        <label>Descripción (pequeña)</label><textarea id="fieldDesc" name="description">{{ description|e }}</textarea>
        <label>URL online del audio (stream)</label><input id="fieldAudio" name="audio_url" value="{{ audio_url|e }}" placeholder="https://...">
        <label>Cambiar puerto (reinicia para aplicar)</label><input name="port" value="{{ port }}" pattern="\\d*">
        <hr style="margin:12px 0;border:none;border-top:1px solid rgba(255,255,255,0.04)">
        <label>Nuevo usuario (vacío = no cambiar)</label><input name="new_user" placeholder="nuevo usuario">
        <label>Nueva contraseña (vacío = no cambiar)</label><input name="new_pass" type="password" placeholder="nueva contraseña">
        <div style="margin-top:12px;"><button class="btn-save" type="submit">💾 Guardar cambios</button>
        <button name="restore_colors" value="1" style="margin-left:8px;background:#111827;color:#fff;padding:10px;border-radius:8px;border:none">🎨 Restaurar colores</button></div>
        <div style="margin-top:8px;color:#9fb3cf">Al cambiar el puerto reinicia el servidor para aplicar.</div>
      </div>

      <div>
        <!-- Live preview -->
        <div class="right-card">
          <div class="small-muted">Vista previa en tiempo real (antes de guardar)</div>
          <div id="adminPreview" class="live-preview" role="region" aria-label="Vista previa">
            <div id="previewBg" style="border-radius:8px;padding:8px;background-size:cover;background-position:center;">
              <div class="cover" id="previewCoverContainer">
                {% if cover %}
                  <img id="previewCover" src="{{ url_for('static', filename=cover_filename) }}" alt="Cover preview">
                {% else %}
                  <div id="previewNoCover" style="color:#9fb3cf">No cover</div>
                {% endif %}
              </div>
              <h3 id="previewTitle">{{ station_label }}</h3>
              <p id="previewDesc">{{ description }}</p>
              <div class="preview-controls">
                <div style="display:flex;align-items:center;gap:8px">
                  <button style="width:44px;height:44px;border-radius:50%;background:#07a08b;border:none;color:white">▶</button>
                  <div style="font-size:12px;color:#9fb3cf">Vol: 100%</div>
                </div>
                <div style="margin-left:auto;display:flex;align-items:center;gap:8px">
                  <div class="color-swatch" id="swBody" title="Body color"></div>
                  <div class="color-swatch" id="swCard" title="Card color"></div>
                  <div class="color-swatch" id="swAccent" title="Accent"></div>
                </div>
              </div>
            </div>
          </div>

          <hr style="margin:12px 0;border:none;border-top:1px solid rgba(255,255,255,0.04)">

          <label>Cover actual</label><div class="preview">{% if cover %}<img id="currentCover" src="{{ url_for('static', filename=cover_filename) }}" style="width:100%;height:100%;object-fit:cover">{% else %}<div style="color:#9fb3cf">No cover</div>{% endif %}</div>
          <label>Subir cover</label><input id="coverFile" type="file" name="cover_file" accept="image/*">
          <hr style="margin:10px 0;border:none;border-top:1px solid rgba(255,255,255,0.04)">
          <label>Background actual</label><div class="preview" style="height:120px">{% if background_exists %}<img id="currentBg" src="{{ url_for('static', filename=background_filename) }}" style="width:100%;height:100%;object-fit:cover">{% else %}<div style="color:#9fb3cf">No background</div>{% endif %}</div>
          <label>Subir background</label><input id="bgFile" type="file" name="background_file" accept="image/*">
          <div style="display:flex;gap:8px;align-items:center;margin-top:8px"><label style="color:#9fb3cf">Activar background</label><input id="bgEnabled" type="checkbox" name="background_enabled" value="1" {% if background_enabled %}checked{% endif %}><button name="remove_background" value="1" style="margin-left:auto;background:#7f1d1d;color:white;padding:8px;border-radius:8px;border:none">Quitar background</button></div>
          <hr style="margin:10px 0;border:none;border-top:1px solid rgba(255,255,255,0.04)">

          <label>Colores (pickers)</label>
          <div style="display:flex;gap:8px;margin-top:8px">
            <input id="bodyColor" type="color" name="body_bg" value="{{ theme.body_bg_hex }}" style="width:46px;height:34px">
            <input id="cardColor" type="color" name="card_bg" value="{{ theme.card_hex }}" style="width:46px;height:34px">
            <input id="accentColor" type="color" name="accent1" value="{{ theme.accent1 }}" style="width:46px;height:34px">
            <input id="textColor" type="color" name="text" value="{{ theme.text }}" style="width:46px;height:34px">
          </div>
          <div style="margin-top:12px;color:#9fb3cf">Puerto actual: <strong>{{ port }}</strong></div>
        </div>
      </div>
    </div>
  </form>
</div>

<!-- Live preview script: actualiza vista previa según cambios en inputs (sin guardar) -->
<script>
(function(){
  // elementos
  const previewRoot = document.getElementById("adminPreview");
  const previewTitle = document.getElementById("previewTitle");
  const previewDesc = document.getElementById("previewDesc");
  const previewCover = document.getElementById("previewCover");
  const previewNoCover = document.getElementById("previewNoCover");
  const previewBg = document.getElementById("previewBg");

  const fieldStation = document.getElementById("fieldStation");
  const fieldDesc = document.getElementById("fieldDesc");
  const fieldAudio = document.getElementById("fieldAudio");

  const coverFile = document.getElementById("coverFile");
  const bgFile = document.getElementById("bgFile");
  const bgEnabled = document.getElementById("bgEnabled");

  const bodyColor = document.getElementById("bodyColor");
  const cardColor = document.getElementById("cardColor");
  const accentColor = document.getElementById("accentColor");
  const textColor = document.getElementById("textColor");

  const swBody = document.getElementById("swBody");
  const swCard = document.getElementById("swCard");
  const swAccent = document.getElementById("swAccent");

  // helpers
  function safeText(v){ return v === null || v === undefined || v === "" ? "&nbsp;" : v; }

  // inicializar preview con valores actuales
  previewTitle.textContent = fieldStation.value || "RadioStream";
  previewDesc.textContent = fieldDesc.value || "Descripción breve de la emisora.";

  // colores iniciales
  function applyColors(){
    const body = bodyColor.value || "{{ theme.body_bg }}";
    const card = cardColor.value || "{{ theme.card_bg }}";
    const accent = accentColor.value || "{{ theme.accent1 }}";
    const text = textColor.value || "{{ theme.text }}";
    // actualizar swatches
    swBody.style.background = body;
    swCard.style.background = card;
    swAccent.style.background = accent;
    // aplicar estilo al preview
    previewRoot.style.background = card;
    previewRoot.style.color = text;
    previewRoot.style.setProperty("--accent1", accent);
    // si body es sólido, usarlo como fondo del contenedor
    previewRoot.style.setProperty("--body-bg", body);
    previewBg.style.backgroundColor = body;
  }
  applyColors();

  // listeners textuales
  fieldStation.addEventListener("input", () => { previewTitle.textContent = fieldStation.value || "RadioStream"; });
  fieldDesc.addEventListener("input", () => { previewDesc.textContent = fieldDesc.value || "Descripción breve de la emisora."; });
  fieldAudio.addEventListener("input", () => {
    // opcional: podríamos mostrar la URL o estado; por ahora dejamos sin cambios visuales
  });

  // file previews (cover)
  coverFile.addEventListener("change", (e) => {
    const f = e.target.files && e.target.files[0];
    if(!f){ return; }
    const url = URL.createObjectURL(f);
    if(previewCover){
      previewCover.src = url;
      previewCover.style.display = "";
      if(previewNoCover) previewNoCover.style.display = "none";
    } else {
      // crear img si no existía
      const img = document.createElement("img");
      img.id = "previewCover";
      img.src = url;
      img.style.width = "100%";
      img.style.height = "100%";
      img.style.objectFit = "cover";
      const container = document.getElementById("previewCoverContainer");
      container.innerHTML = "";
      container.appendChild(img);
    }
  });

  // background preview
  bgFile.addEventListener("change", (e) => {
    const f = e.target.files && e.target.files[0];
    if(!f){ return; }
    const url = URL.createObjectURL(f);
    previewBg.style.backgroundImage = `url('${url}')`;
    previewBg.style.backgroundSize = "cover";
    previewBg.style.backgroundPosition = "center";
    // si bgEnabled no está marcado, marcarlo visualmente
    if(!bgEnabled.checked){
      bgEnabled.checked = true;
    }
  });

  // checkbox enable/disable background
  bgEnabled.addEventListener("change", () => {
    if(bgEnabled.checked){
      previewBg.style.filter = ""; // normal
      previewBg.style.opacity = "1";
    } else {
      previewBg.style.backgroundImage = "";
      previewBg.style.backgroundColor = ""; // dejar color según body
    }
  });

  // colores
  [bodyColor, cardColor, accentColor, textColor].forEach((el) => {
    el.addEventListener("input", () => {
      applyColors();
    });
  });

  // si al cargar no hay cover, mantener placeholder visible
  if(!document.getElementById("previewCover")){
    if(previewNoCover) previewNoCover.style.display = "";
  }

})();
</script>

</body></html>
"""

# ---------------- Rutas admin y funcionalidades ----------------
@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if request.method == "POST":
        if request.form.get("restore_colors"):
            config["theme"] = DEFAULT_THEME.copy()
            save_config(config)
            flash("Colores restaurados a los valores por defecto 🎨")
            return redirect(url_for("admin"))

        if request.form.get("remove_background"):
            try:
                p = STATIC_DIR / BACKGROUND_FILENAME
                if p.exists():
                    p.unlink()
            except Exception as e:
                app.logger.debug("No se pudo borrar background: %s", e)
            config["background_enabled"] = False
            config["background_filename"] = ""
            save_config(config)
            flash("Background eliminado y desactivado.")
            return redirect(url_for("admin"))

        station_label = request.form.get("station_label", "").strip()
        description = request.form.get("description", "").strip()
        audio_url = request.form.get("audio_url", "").strip()
        port = request.form.get("port", "").strip()
        new_user = request.form.get("new_user", "").strip()
        new_pass = request.form.get("new_pass", "").strip()

        body_bg = request.form.get("body_bg", "").strip()
        card_bg_hex = request.form.get("card_bg", "").strip()
        accent1 = request.form.get("accent1", "").strip()
        text_color = request.form.get("text", "").strip()

        background_enabled = True if request.form.get("background_enabled") else False

        if port:
            try:
                port_int = int(port)
                if not (1 <= port_int <= 65535):
                    flash("Puerto fuera de rango (1-65535).")
                    return redirect(url_for("admin"))
            except ValueError:
                flash("Puerto inválido.")
                return redirect(url_for("admin"))
        else:
            port_int = config.get("port", DEFAULT_PORT)

        # cover
        file = request.files.get("cover_file")
        if file and file.filename:
            filename = secure_filename(file.filename)
            if allowed_file(filename):
                save_path = STATIC_DIR / COVER_FILENAME
                file.save(save_path)
                flash("Imagen cover subida correctamente.")
            else:
                flash("Tipo de archivo no permitido para la imagen de cover.")
                return redirect(url_for("admin"))

        # background
        bfile = request.files.get("background_file")
        if bfile and bfile.filename:
            bf = secure_filename(bfile.filename)
            if allowed_file(bf):
                save_path = STATIC_DIR / BACKGROUND_FILENAME
                bfile.save(save_path)
                config["background_filename"] = BACKGROUND_FILENAME
                flash("Imagen de background subida correctamente.")
            else:
                flash("Tipo de archivo no permitido para background.")
                return redirect(url_for("admin"))

        changed_port = port_int != config.get("port", DEFAULT_PORT)
        if station_label:
            config["station_label"] = station_label
        config["description"] = description
        config["audio_url"] = audio_url
        config["port"] = port_int

        if new_user:
            config["username"] = new_user
            session["user"] = new_user
        if new_pass:
            config["password_hash"] = generate_password_hash(new_pass)

        theme = config.get("theme", DEFAULT_THEME.copy())
        if body_bg:
            theme["body_bg"] = body_bg
        if card_bg_hex:
            theme["card_bg"] = card_bg_hex
            theme["card_hex"] = card_bg_hex
        if accent1:
            theme["accent1"] = accent1
        if text_color:
            theme["text"] = text_color

        config["theme"] = theme
        config["background_enabled"] = bool(background_enabled)
        if config["background_enabled"] and not background_exists():
            config["background_enabled"] = False
            flash("No hay imagen de background subida: sube una y marca 'Activar background' de nuevo.")

        if "secret_key" not in config:
            config["secret_key"] = secrets.token_hex(32)
            app.secret_key = config["secret_key"]

        save_config(config)
        if changed_port:
            flash(f"Configuración guardada. Puerto cambiado a {port_int}. Reinicia el servidor para aplicar el nuevo puerto.")
        else:
            flash("Configuración guardada correctamente.")
        return redirect(url_for("admin"))

    theme = config.get("theme", DEFAULT_THEME.copy())
    card_hex = theme.get("card_hex") or ( "#071028" if theme.get("card_bg","").startswith("linear-gradient") else theme.get("card_bg",""))
    theme_for_admin = {
        "body_bg": theme.get("body_bg", DEFAULT_THEME["body_bg"]),
        "card_hex": card_hex,
        "accent1": theme.get("accent1", DEFAULT_THEME["accent1"]),
        "text": theme.get("text", DEFAULT_THEME["text"]),
        "card_bg": theme.get("card_bg", DEFAULT_THEME["card_bg"]),
        "cover_bg": theme.get("cover_bg", DEFAULT_THEME["cover_bg"]),
        "muted": theme.get("muted", DEFAULT_THEME["muted"])
    }
    theme_for_admin["body_bg_hex"] = theme_for_admin["body_bg"]
    theme_for_admin["accent1"] = theme_for_admin["accent1"]
    theme_for_admin["text"] = theme_for_admin["text"]

    return render_template_string(
        ADMIN_HTML,
        current_user=session.get("user"),
        station_label=config.get("station_label", ""),
        description=config.get("description", ""),
        audio_url=config.get("audio_url", ""),
        port=config.get("port", DEFAULT_PORT),
        cover=cover_exists(),
        cover_filename=COVER_FILENAME,
        background_exists=background_exists(),
        background_filename=config.get("background_filename", BACKGROUND_FILENAME),
        background_enabled=config.get("background_enabled", False),
        theme=theme_for_admin
    )

# ---------------- Run ----------------
if __name__ == "__main__":
    port_to_use = config.get("port", DEFAULT_PORT)
    print("------------------------------------------------------------")
    print("RadioStream - servidor de administración")
    print(f"Escuchando en http://0.0.0.0:{port_to_use}")
    print("Accede a /admin para configurar. Credenciales por defecto: admin / admin")
    print("Usa /embed (o /embed?autoplay=1) para el reproductor embebible (iframe).")
    print("Para que un cambio de puerto tome efecto debes reiniciar el servidor.")
    print("------------------------------------------------------------")
    app.run(host="0.0.0.0", port=port_to_use, debug=False)
