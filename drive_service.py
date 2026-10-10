import os
import secrets
import tempfile

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from models import db, SiteSetting

# Desativa a verificação estrita para tolerar escopos retornados pelo Google
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


class DriveConfigError(RuntimeError):
    pass


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class DriveService:
    def __init__(self):
        self.client_id = os.getenv("DRIVE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("DRIVE_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("DRIVE_REDIRECT_URI") or os.getenv("GOOGLE_REDIRECT_URI")
        self.key = os.getenv("TOKEN_ENCRYPTION_KEY")

        if not self.client_id or not self.client_secret or not self.redirect_uri:
            raise DriveConfigError(
                "Configure DRIVE_CLIENT_ID, DRIVE_CLIENT_SECRET e DRIVE_REDIRECT_URI."
            )
        if not self.key:
            raise DriveConfigError("Configure TOKEN_ENCRYPTION_KEY para proteger o token do Drive.")

        # Força HTTPS na redirect_uri apenas em ambiente remoto (ex: Render), mantendo HTTP no localhost
        if self.redirect_uri and self.redirect_uri.startswith("http://") and "localhost" not in self.redirect_uri:
            self.redirect_uri = self.redirect_uri.replace("http://", "https://", 1)

    def _fernet(self):
        return Fernet(self.key.encode())

    def _flow(self, state=None):
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri],
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            state=state,
            autogenerate_code_verifier=False,
        )
        flow.redirect_uri = self.redirect_uri
        return flow

    def authorization_url(self):
        state = secrets.token_urlsafe(32)
        flow = self._flow(state=state)
        url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return url, state

    def handle_callback(self, authorization_response, state):
        # Garante que a URL tratada no callback seja HTTPS fora do ambiente local
        if authorization_response.startswith("http://") and "localhost" not in authorization_response:
            authorization_response = authorization_response.replace("http://", "https://", 1)

        flow = self._flow(state=state)
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials

        if not credentials.refresh_token:
            raise DriveConfigError("O Google não retornou refresh token. Reconecte com consentimento.")

        encrypted = self._fernet().encrypt(credentials.refresh_token.encode()).decode()
        item = SiteSetting.query.filter_by(key="drive_refresh_token").first()
        if not item:
            item = SiteSetting(key="drive_refresh_token", value=encrypted)
            db.session.add(item)
        else:
            item.value = encrypted
        db.session.commit()

    def credentials(self):
        item = SiteSetting.query.filter_by(key="drive_refresh_token").first()
        if not item:
            raise DriveConfigError("Google Drive ainda não conectado.")
        refresh_token = self._fernet().decrypt(item.value.encode()).decode()
        return Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=SCOPES,
        )

    def client(self):
        return build("drive", "v3", credentials=self.credentials(), cache_discovery=False)

    def list_folder(self, folder_id):
        service = self.client()
        q = f"'{folder_id}' in parents and trashed = false"
        return service.files().list(
            q=q,
            fields="files(id,name,mimeType,size,modifiedTime,thumbnailLink,webContentLink)",
            pageSize=1000,
            orderBy="name",
        ).execute().get("files", [])

    def download_to_temp(self, file_id):
        service = self.client()
        request = service.files().get_media(fileId=file_id)
        fd, path = tempfile.mkstemp(prefix="meu_espaco_")
        os.close(fd)
        with open(path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=8 * 1024 * 1024)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return path