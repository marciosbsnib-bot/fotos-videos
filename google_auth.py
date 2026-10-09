from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, redirect, request, url_for, session, flash, render_template
from flask_login import login_user
from models import db, User

oauth = OAuth()
google_bp = Blueprint("google", __name__, url_prefix="/auth")


def init_google(app):
    oauth.init_app(app)
    oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        client_kwargs={"scope": "openid email profile"},
    )
    app.register_blueprint(google_bp)


@google_bp.get("/google")
def google_login():
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        flash("Google Login ainda não foi configurado.", "error")
        return redirect(url_for("login"))
    redirect_uri = current_app.config.get("GOOGLE_REDIRECT_URI") or url_for("google.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@google_bp.get("/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = oauth.google.userinfo()

    email = userinfo["email"].strip().lower()
    name = userinfo.get("name") or email.split("@")[0]
    sub = userinfo["sub"]

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, name=name, google_sub=sub, status="PENDING", access_level="NONE")
        db.session.add(user)
        db.session.commit()
    elif not user.google_sub:
        user.google_sub = sub
        db.session.commit()

    if user.status == "PENDING":
        return render_template("pending.html", user=user)
    if user.status != "APPROVED":
        flash("Esta conta está bloqueada.", "error")
        return redirect(url_for("login"))

    login_user(user)
    return redirect(url_for("index"))
