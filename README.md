# RadioStream

RadioStream es un reproductor web ligero con panel de administración diseñado para publicar y embeber un stream de audio (Icecast, Shoutcast, HTTP streams, etc.). Proporciona una interfaz pública para oyentes y un panel `/admin` para gestionar etiqueta, descripción, URL del stream, imágenes (cover / background) y tema visual.

---

## Resumen ejecutivo 🔧🎧

* Aplicación en **Flask** que sirve:

  * Página pública con reproductor (`/`) y cover/background.
  * Versión embebible (`/embed`) que soporta `?autoplay=1`.
  * Panel de administración (`/admin`) con subida de imágenes y ajuste de tema.
* Configuración persistente en `config.json`.
* Licencia: **GPLv3**.

---

## ¿Se puede cambiar la contraseña desde la web? ✅

Sí. Desde `/admin` existe el campo **"Nueva contraseña"** (`new_pass`). Al guardar:

* La contraseña se transforma con `werkzeug.security.generate_password_hash` y se guarda en `config.json` como `password_hash` (no se almacena en texto plano).
* Si se cambia el usuario (campo **"Nuevo usuario"**), la sesión se actualiza con el nuevo nombre para evitar cerrar la sesión inmediatamente.
* El mecanismo es local: `config.json` es el origen de la configuración y se actualiza de forma atómica al guardar.

Comando útil para generar un hash desde consola (si prefieres editar `config.json` manualmente):

```bash
python3 - <<'PY'
from werkzeug.security import generate_password_hash
print(generate_password_hash("tu_contraseña_segura"))
PY
```

---

## Instalación resumida (local) 🛠️

1. Crear entorno virtual e instalar dependencias:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Ejecutar:

```bash
python3 radiostream.py
```

Por defecto escucha en el puerto definido en `config.json` (por defecto `4080`). Accede a `/admin` para configuración inicial.

---

## Seguridad - puntos clave 🔒

* **Cambia credenciales por defecto** (`admin`/`admin`) inmediatamente.
* `secret_key` se genera en el primer arranque; revísalo si exposes la app públicamente.
* Usa HTTPS y un proxy (Nginx) en producción.
* Limita tamaño de uploads con `app.config['MAX_CONTENT_LENGTH']`.
* Asegúrate del CORS del servidor de audio (`Access-Control-Allow-Origin`) si el stream proviene de otro dominio.

---

## Comparativa concisa con Icecast 🆚 ❗

> Icecast es un servidor de streaming (media server). RadioStream es un **reproductor web y panel de administración** que consume streams (por ejemplo, generados por Icecast). La tabla aclara roles y capacidades.

### Comparativa: roles y uso

| Aspecto                             |                            RadioStream (este proyecto) 🎛️ | Icecast (servidor de audio) 🛰️                                         |
| ----------------------------------- | ---------------------------------------------------------: | ----------------------------------------------------------------------- |
| **Función principal**               | Reproductor web + UI de administración / embed del stream. | Servidor de streaming que distribuye audio (mountpoints).               |
| **Generación del stream**           |                   No: consume una URL de stream existente. | Sí: emite y distribuye streams (clients/relays).                        |
| **Almacenamiento de configuración** |                                     `config.json` (local). | Ficheros de configuración / runtime según instalación.                  |
| **Autenticación admin**             |         Simple (usuario + contraseña, editable desde web). | Autenticación para administración y/o subida de fuentes (configurable). |
| **Interfaz web**                    |       UI para oyentes y panel de administración integrado. | Panel administrativo limitado o externo según instalación.              |
| **Embebible (iframe)**              |      Sí — `/embed` con control de volumen y `?autoplay=1`. | No aplica: Icecast no es un reproductor; requiere cliente/players.      |
| **Transcodificación / relaying**    |                                              No (cliente). | Sí (según configuración y herramientas adicionales).                    |
| **Caso de uso típico**              |        Front-end para oyentes y panel de gestión sencillo. | Back-end para emitir y servir streams a multitud de clientes.           |

### Comparativa técnica breve

| Característica                   |                                          RadioStream | Icecast                                         |
| -------------------------------- | ---------------------------------------------------: | ----------------------------------------------- |
| Requiere servidor de streaming   |                                         No (consume) | Sí (provee)                                     |
| Gestión de usuarios de emisión   |                   No (depende del servidor de audio) | Sí (configurable)                               |
| CORS y reproducción en navegador | Depende del `Access-Control-Allow-Origin` del stream | Control total al servir el stream               |
| Uso recomendado                  |      Interfaz pública/embeds + administración básica | Orquestación y distribución de streams a escala |

---

## Prácticas recomendadas de despliegue 📦

* Ejecutar detrás de Nginx (proxy reverso) y habilitar HTTPS (Let’s Encrypt).
* Servir `static/` directamente desde Nginx en producción para rendimiento.
* Ejecutar con Gunicorn y supervisar con systemd.
* Mantener `config.json` y `static/` en volúmenes persistentes (si se usan contenedores).
* Hacer backups periódicos de `config.json`.

---

## Archivos relevantes del proyecto 📁

* `radiostream.py` — aplicación Flask principal.
* `config.json` — configuración persistente.
* `static/cover.png`, `static/background.png` — imágenes usadas por la UI.
* `LICENSE` — texto de **GPLv3**.
* `requirements.txt` — dependencias.

---

## Licencia 📜

RadioStream se distribuye bajo **GNU GPLv3**. El repositorio incluye el archivo `LICENSE` con el texto completo de la licencia. Al redistribuir o modificar la aplicación, respeta los términos de GPLv3.
