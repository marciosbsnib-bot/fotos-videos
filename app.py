import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, send_file, session, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, User, Media, Album, Like, Favorite, View, AuditLog, SiteSetting
from drive_service import DriveService, DriveConfigError
from google_auth import init_google

# Permite que a biblioteca aceite o cabeçalho HTTPS vindo do Proxy do Render
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

load_dotenv()

app = Flask(__name__)

# Correção completa de Proxy do Render para repassar proto, host e port
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///meu_espaco.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

db.init_app(app)
csrf = CSRFProtect(app)

app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET")
app.config["GOOGLE_REDIRECT_URI"] = os.environ.get("GOOGLE_REDIRECT_URI")

init_google(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para continuar."

with app.app_context():
    db.create_all()
    admin_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    if admin_email:
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                name="Administrador",
                status="APPROVED",
                access_level="ADMIN",
                password_hash=generate_password_hash(os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "troque-esta-senha")),
            )
            db.session.add(admin)
            db.session.commit()
        elif admin.access_level != "ADMIN" or admin.status != "APPROVED":
            admin.access_level = "ADMIN"
            admin.status = "APPROVED"
            db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.context_processor
def inject_globals():
    return {
        "settings": {
            "show_views": get_setting("show_views", "1") == "1",
            "show_likes": get_setting("show_likes", "1") == "1",
            "show_favorites": get_setting("show_favorites", "1") == "1",
        }
    }


def get_setting(key, default=None):
    item = SiteSetting.query.filter_by(key=key).first()
    return item.value if item else default


def set_setting(key, value):
    item = SiteSetting.query.filter_by(key=key).first()
    if not item:
        item = SiteSetting(key=key)
        db.session.add(item)
    item.value = str(value)
    db.session.commit()


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.access_level != "ADMIN" or current_user.status != "APPROVED":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def approved_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.status == "PENDING":
            return render_template("pending.html", user=current_user)
        if current_user.status != "APPROVED":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def can_view(media):
    if current_user.access_level == "ADMIN":
        return True
    if current_user.status != "APPROVED":
        return False
    if media.access_classification == "PUBLIC":
        return current_user.access_level in {"BASIC", "NORMAL"}
    if media.access_classification == "NORMAL":
        return current_user.access_level == "NORMAL"
    return False


def audit(action, media_id=None, details=None):
    if not current_user.is_authenticated:
        return
    db.session.add(AuditLog(
        user_id=current_user.id,
        media_id=media_id,
        action=action,
        details=details or {},
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        user_agent=request.headers.get("User-Agent", "")[:500],
    ))
    db.session.commit()


@app.get("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    if current_user.status == "PENDING":
        return render_template("pending.html", user=current_user)
    if current_user.status != "APPROVED":
        return render_template("blocked.html")
    albums = Album.query.order_by(Album.created_at.desc()).all()
    visible = [a for a in albums if current_user.access_level == "ADMIN" or
               (a.access_classification == "PUBLIC" and current_user.access_level in {"BASIC", "NORMAL"}) or
               (a.access_classification == "NORMAL" and current_user.access_level == "NORMAL")]
    return render_template("home.html", albums=visible)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
            flash("E-mail ou senha inválidos.", "error")
            return render_template("login.html")

        if user.status == "PENDING":
            return render_template("pending.html", user=user)
        if user.status != "APPROVED":
            flash("Esta conta está bloqueada.", "error")
            return render_template("login.html")

        login_user(user)
        audit("LOGIN")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.post("/register")
def register():
    email = request.form.get("email", "").strip().lower()
    name = request.form.get("name", "").strip()
    password = request.form.get("password", "")

    if not email or not name or len(password) < 8:
        flash("Informe nome, e-mail e uma senha de pelo menos 8 caracteres.", "error")
        return redirect(url_for("login"))

    user = User.query.filter_by(email=email).first()
    if user:
        if user.status == "PENDING":
            return render_template("pending.html", user=user)
        flash("Este e-mail já está cadastrado.", "error")
        return redirect(url_for("login"))

    user = User(
        email=email,
        name=name,
        password_hash=generate_password_hash(password),
        status="PENDING",
        access_level="NONE",
    )
    db.session.add(user)
    db.session.commit()
    return render_template("pending.html", user=user)


@app.get("/logout")
@login_required
def logout():
    audit("LOGOUT")
    logout_user()
    return redirect(url_for("login"))


@app.get("/albums/<int:album_id>")
@approved_required
def album(album_id):
    item = db.session.get(Album, album_id)
    if not item:
        abort(404)
    if current_user.access_level != "ADMIN":
        if item.access_classification == "RESTRICTED":
            abort(403)
        if item.access_classification == "NORMAL" and current_user.access_level != "NORMAL":
            abort(403)

    media = item.media.order_by(Media.created_at.desc()).all()
    media = [m for m in media if can_view(m)]
    return render_template("album.html", album=item, media=media)


@app.get("/media/<int:media_id>")
@approved_required
def media_view(media_id):
    media = db.session.get(Media, media_id)
    if not media or not can_view(media):
        abort(404)

    now = datetime.now(timezone.utc)
    cooldown = int(os.environ.get("VIEW_COOLDOWN_MINUTES", "30"))
    last = View.query.filter_by(user_id=current_user.id, media_id=media.id).order_by(View.viewed_at.desc()).first()
    should_count = not last or (now - last.viewed_at.replace(tzinfo=timezone.utc)) >= timedelta(minutes=cooldown)

    if should_count:
        db.session.add(View(user_id=current_user.id, media_id=media.id, viewed_at=now))
        db.session.commit()
        audit("VIEW", media.id)

    liked = Like.query.filter_by(user_id=current_user.id, media_id=media.id).first() is not None
    favorite = Favorite.query.filter_by(user_id=current_user.id, media_id=media.id).first() is not None
    view_count = View.query.filter_by(media_id=media.id).count()
    like_count = Like.query.filter_by(media_id=media.id).count()
    favorite_count = Favorite.query.filter_by(media_id=media.id).count()

    return render_template(
        "viewer.html",
        media=media,
        liked=liked,
        favorite=favorite,
        view_count=view_count,
        like_count=like_count,
        favorite_count=favorite_count,
    )


@app.post("/media/<int:media_id>/like")
@approved_required
def toggle_like(media_id):
    media = db.session.get(Media, media_id)
    if not media or not can_view(media):
        abort(404)
    like = Like.query.filter_by(user_id=current_user.id, media_id=media.id).first()
    if like:
        db.session.delete(like)
        action = "UNLIKE"
    else:
        db.session.add(Like(user_id=current_user.id, media_id=media.id))
        action = "LIKE"
    db.session.commit()
    audit(action, media.id)
    return redirect(request.referrer or url_for("media_view", media_id=media.id))


@app.post("/media/<int:media_id>/favorite")
@approved_required
def toggle_favorite(media_id):
    media = db.session.get(Media, media_id)
    if not media or not can_view(media):
        abort(404)
    fav = Favorite.query.filter_by(user_id=current_user.id, media_id=media.id).first()
    if fav:
        db.session.delete(fav)
        action = "UNFAVORITE"
    else:
        db.session.add(Favorite(user_id=current_user.id, media_id=media.id))
        action = "FAVORITE"
    db.session.commit()
    audit(action, media.id)
    return redirect(request.referrer or url_for("media_view", media_id=media.id))


@app.get("/favorites")
@approved_required
def favorites():
    items = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.created_at.desc()).all()
    media = [x.media for x in items if can_view(x.media)]
    return render_template("collection.html", title="Favoritos", media=media)


@app.get("/likes")
@approved_required
def likes():
    items = Like.query.filter_by(user_id=current_user.id).order_by(Like.created_at.desc()).all()
    media = [x.media for x in items if can_view(x.media)]
    return render_template("collection.html", title="Curtidas", media=media)


@app.get("/media/<int:media_id>/stream")
@approved_required
def stream_media(media_id):
    media = db.session.get(Media, media_id)
    if not media or not can_view(media):
        abort(404)
    if not media.drive_file_id:
        abort(404)
    try:
        drive = DriveService()
        path = drive.download_to_temp(media.drive_file_id)
        return send_file(path, mimetype=media.mime_type or "application/octet-stream", conditional=True, etag=True)
    except DriveConfigError:
        abort(503)


# ---------------- ADMIN ----------------

@app.get("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "users": User.query.count(),
        "pending": User.query.filter_by(status="PENDING").count(),
        "albums": Album.query.count(),
        "media": Media.query.count(),
        "likes": Like.query.count(),
        "favorites": Favorite.query.count(),
        "views": View.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@app.get("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@app.post("/admin/users/<int:user_id>/approve")
@admin_required
def admin_approve_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    level = request.form.get("access_level")
    if level not in {"BASIC", "NORMAL"}:
        abort(400)
    user.status = "APPROVED"
    user.access_level = level
    db.session.commit()
    audit("APPROVE_USER", details={"target_user_id": user.id, "level": level})
    flash("Usuário aprovado.", "success")
    return redirect(url_for("admin_users"))


@app.post("/admin/users/<int:user_id>/level")
@admin_required
def admin_change_level(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    level = request.form.get("access_level")
    if level not in {"BASIC", "NORMAL", "ADMIN"}:
        abort(400)
    user.access_level = level
    user.status = "APPROVED"
    db.session.commit()
    audit("CHANGE_USER_LEVEL", details={"target_user_id": user.id, "level": level})
    return redirect(url_for("admin_users"))


@app.post("/admin/users/<int:user_id>/block")
@admin_required
def admin_block_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        abort(400)
    user.status = "BLOCKED"
    db.session.commit()
    audit("BLOCK_USER", details={"target_user_id": user.id})
    return redirect(url_for("admin_users"))


@app.get("/admin/albums")
@admin_required
def admin_albums():
    albums = Album.query.order_by(Album.created_at.desc()).all()
    return render_template("admin/albums.html", albums=albums)


@app.post("/admin/albums")
@admin_required
def admin_create_album():
    name = request.form.get("name", "").strip()
    classification = request.form.get("classification", "PUBLIC")
    if not name or classification not in {"PUBLIC", "NORMAL", "RESTRICTED"}:
        abort(400)
    db.session.add(Album(name=name, access_classification=classification))
    db.session.commit()
    return redirect(url_for("admin_albums"))


@app.post("/admin/albums/<int:album_id>/classification")
@admin_required
def admin_album_classification(album_id):
    album = db.session.get(Album, album_id)
    if not album:
        abort(404)
    classification = request.form.get("classification")
    if classification not in {"PUBLIC", "NORMAL", "RESTRICTED"}:
        abort(400)
    album.access_classification = classification
    db.session.commit()
    audit("CHANGE_ALBUM_CLASSIFICATION", details={"album_id": album.id, "classification": classification})
    return redirect(url_for("admin_albums"))


@app.get("/admin/settings")
@admin_required
def admin_settings():
    return render_template(
        "admin/settings.html",
        show_views=get_setting("show_views", "1") == "1",
        show_likes=get_setting("show_likes", "1") == "1",
        show_favorites=get_setting("show_favorites", "1") == "1",
    )


@app.post("/admin/settings")
@admin_required
def admin_settings_save():
    set_setting("show_views", "1" if request.form.get("show_views") else "0")
    set_setting("show_likes", "1" if request.form.get("show_likes") else "0")
    set_setting("show_favorites", "1" if request.form.get("show_favorites") else "0")
    flash("Configurações salvas.", "success")
    return redirect(url_for("admin_settings"))


@app.get("/admin/logs")
@admin_required
def admin_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(500).all()
    return render_template("admin/logs.html", logs=logs)


@app.get("/admin/drive")
@admin_required
def admin_drive():
    connected = SiteSetting.query.filter_by(key="drive_refresh_token").first() is not None
    return render_template("admin/drive.html", connected=connected)


@app.get("/admin/drive/connect")
@admin_required
def admin_drive_connect():
    try:
        drive = DriveService()
        auth_url, state = drive.authorization_url()
        session["drive_oauth_state"] = state
        return redirect(auth_url)
    except DriveConfigError as exc:
        flash(str(exc), "error")
        return redirect(url_for("admin_drive"))


@app.get("/admin/drive/callback")
@admin_required
def admin_drive_callback():
    try:
        drive = DriveService()
        drive.handle_callback(request.url, session.get("drive_oauth_state"))
        audit("DRIVE_CONNECTED")
        flash("Google Drive conectado.", "success")
    except Exception as exc:
        flash(f"Não foi possível conectar o Drive: {exc}", "error")
    return redirect(url_for("admin_drive"))


@app.post("/admin/drive/sync")
@admin_required
def admin_drive_sync():
    folder_id = request.form.get("folder_id", "").strip()
    album_name = request.form.get("album_name", "").strip()
    classification = request.form.get("classification", "PUBLIC")
    if not folder_id or not album_name or classification not in {"PUBLIC", "NORMAL", "RESTRICTED"}:
        flash("Informe a pasta do Drive, nome do álbum e classificação.", "error")
        return redirect(url_for("admin_drive"))
    try:
        drive = DriveService()
        files = drive.list_folder(folder_id)
        album = Album.query.filter_by(drive_folder_id=folder_id).first()
        if not album:
            album = Album(name=album_name, drive_folder_id=folder_id, access_classification=classification)
            db.session.add(album)
            db.session.flush()
        else:
            album.name = album_name
            album.access_classification = classification
        count = 0
        for f in files:
            mime = f.get("mimeType", "")
            if not (mime.startswith("image/") or mime.startswith("video/")):
                continue
            media = Media.query.filter_by(drive_file_id=f["id"]).first()
            if not media:
                media = Media(album_id=album.id, drive_file_id=f["id"], name=f.get("name", "Sem nome"), mime_type=mime, access_classification=classification)
                db.session.add(media)
                count += 1
            else:
                media.album_id = album.id
                media.name = f.get("name", media.name)
                media.mime_type = mime
                media.access_classification = classification
        db.session.commit()
        audit("DRIVE_SYNC", details={"folder_id": folder_id, "files_added": count})
        flash(f"Sincronização concluída: {count} novos arquivos.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Falha ao sincronizar o Drive: {exc}", "error")
    return redirect(url_for("admin_drive"))


@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="Você não tem permissão para acessar este conteúdo."), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="Conteúdo não encontrado."), 404


if __name__ == "__main__":
    app.run(debug=True)