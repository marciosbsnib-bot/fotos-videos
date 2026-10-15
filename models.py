from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, JSON

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(320), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255))
    google_sub = db.Column(db.String(255), unique=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="PENDING", index=True)
    access_level = db.Column(db.String(20), nullable=False, default="NONE", index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.status == "APPROVED"

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    drive_folder_id = db.Column(db.String(255), unique=True)
    access_classification = db.Column(db.String(20), nullable=False, default="PUBLIC")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    media = db.relationship("Media", backref="album", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def cover_medias(self):
        """Retorna até 3 mídias recentes para compor a capa estilo mosaico."""
        return self.media.order_by(Media.created_at.desc()).limit(3).all()


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey("album.id"), nullable=False, index=True)
    drive_file_id = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(255))
    thumbnail_url = db.Column(db.Text)
    access_classification = db.Column(db.String(20), nullable=False, default="PUBLIC", index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    user = db.relationship("User")
    media = db.relationship("Media")
    __table_args__ = (UniqueConstraint("user_id", "media_id", name="uq_like_user_media"),)


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    user = db.relationship("User")
    media = db.relationship("Media")
    __table_args__ = (UniqueConstraint("user_id", "media_id", name="uq_fav_user_media"),)


class View(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=False)
    viewed_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    user = db.relationship("User")
    media = db.relationship("Media")


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    media_id = db.Column(db.Integer, db.ForeignKey("media.id"))
    action = db.Column(db.String(80), nullable=False, index=True)
    details = db.Column(JSON, default=dict)
    ip_address = db.Column(db.String(255))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    user = db.relationship("User")
    media = db.relationship("Media")


class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)