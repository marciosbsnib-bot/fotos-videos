
import os
import secrets
from urllib.parse import urlencode

import requests
from cryptography.fernet import Fernet

from models import db, SiteSetting
import box_service

BOX_AUTH_URL = "https://account.box.com/api/oauth2/authorize"
BOX_TOKEN_URL = "https://api.box.com/oauth2/token"
BOX_API_URL = "https://api.box.com/2.0"


class BoxServiceError(RuntimeError):
    pass


class BoxService:
    def __init__(self):
        self.client_id = os.getenv("BOX_CLIENT_ID")
        self.client_secret = os.getenv("BOX_CLIENT_SECRET")
        self.redirect_uri = os.getenv("BOX_REDIRECT_URI")
        self.encryption_key = os.getenv("TOKEN_ENCRYPTION_KEY")

        if not all([
            self.client_id,
            self.client_secret,
            self.redirect_uri,
            self.encryption_key,
        ]):
            raise BoxServiceError(
                "Configure BOX_CLIENT_ID, BOX_CLIENT_SECRET, "
                "BOX_REDIRECT_URI e TOKEN_ENCRYPTION_KEY no Render."
            )

    def _fernet(self):
        return Fernet(self.encryption_key.encode())

    def authorization_url(self, state):
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        return BOX_AUTH_URL + "?" + urlencode(params)

    def _save_refresh_token(self, refresh_token):
        encrypted = self._fernet().encrypt(
            refresh_token.encode()
        ).decode()

        item = SiteSetting.query.filter_by(
            key="box_refresh_token"
        ).first()

        if item is None:
            item = SiteSetting(
                key="box_refresh_token",
                value=encrypted,
            )
            db.session.add(item)
        else:
            item.value = encrypted

        db.session.commit()

    def handle_callback(self, code):
        response = requests.post(
            BOX_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
            },
            timeout=30,
        )

        if not response.ok:
            raise BoxServiceError(
                f"O Box recusou a autorização (HTTP {response.status_code}). "
                "Confira as configurações OAuth do aplicativo."
            )

        tokens = response.json()
        refresh_token = tokens.get("refresh_token")

        if not refresh_token:
            raise BoxServiceError(
                "O Box não retornou um refresh token."
            )

        self._save_refresh_token(refresh_token)

    def _access_token(self):
        item = SiteSetting.query.filter_by(
            key="box_refresh_token"
        ).first()

        if item is None:
            raise BoxServiceError(
                "Box ainda não conectado. Conecte a conta pelo painel."
            )

        refresh_token = self._fernet().decrypt(
            item.value.encode()
        ).decode()

        response = requests.post(
            BOX_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=30,
        )

        if not response.ok:
            raise BoxServiceError(
                f"Não foi possível renovar o acesso ao Box "
                f"(HTTP {response.status_code}). Reconecte a conta."
            )

        tokens = response.json()

        # O Box pode emitir um novo refresh token durante a renovação.
        new_refresh_token = tokens.get("refresh_token")
        if new_refresh_token:
            self._save_refresh_token(new_refresh_token)

        access_token = tokens.get("access_token")
        if not access_token:
            raise BoxServiceError(
                "O Box não retornou um token de acesso."
            )

        return access_token

    def _get(self, endpoint, params=None, allow_redirects=True):
        token = self._access_token()

        response = requests.get(
            BOX_API_URL + endpoint,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=60,
            allow_redirects=allow_redirects,
        )

        if response.status_code == 401:
            raise BoxServiceError(
                "O Box recusou o acesso. Reconecte a conta."
            )

        return response

    def list_folder(self, folder_id="0"):
        files = []
        marker = None

        while True:
            params = {
                "limit": 1000,
                "fields": "id,name,type,size,modified_at,extension",
                "usemarker": "true",
            }

            if marker:
                params["marker"] = marker

            response = self._get(
                f"/folders/{folder_id}/items",
                params=params,
            )

            if not response.ok:
                raise BoxServiceError(
                    f"Falha ao listar a pasta do Box "
                    f"(HTTP {response.status_code}). "
                    "Confira o ID da pasta e as permissões do aplicativo."
                )

            data = response.json()
            files.extend(
                item for item in data.get("entries", [])
                if item.get("type") == "file"
            )

            marker = data.get("next_marker")
            if not marker:
                break

        return files

    def download_url(self, file_id):
        response = self._get(
            f"/files/{file_id}/content",
            allow_redirects=False,
        )

        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location")
            if location:
                return location

        raise BoxServiceError(
            f"Não foi possível abrir o arquivo no Box "
            f"(HTTP {response.status_code})."
        )
