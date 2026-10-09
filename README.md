# Meu Espaço

Site pessoal privado para fotos e vídeos, feito com Python + Flask.

## Recursos desta primeira versão

- Login por e-mail/senha.
- Login com Google (OIDC).
- Novos cadastros entram como `PENDING` e não acessam o conteúdo.
- Aprovação administrativa escolhendo:
  - Básico: somente conteúdo Público.
  - Normal: Público + Normal.
  - Administrador: tudo, inclusive Restrito.
- Usuário bloqueado não entra.
- Classificação de conteúdo: Público, Normal, Restrito.
- Curtidas por usuário.
- Favoritos por usuário.
- Visualizações por usuário, com intervalo configurável.
- Contador de visualizações/curtidas/favoritos configurável globalmente e por álbum.
- Painel administrativo.
- Logs de auditoria.
- Integração preparada para Google Drive.
- Visualizador de imagens com zoom e tela cheia.
- Player HTML5 para vídeos.
- Segurança: CSRF, hash de senha, sessão segura, autorização no backend e tokens Drive criptografados.

## Arquitetura

- Backend: Flask
- Banco: PostgreSQL em produção; SQLite para desenvolvimento
- ORM: SQLAlchemy
- Autenticação local: Flask-Login + Werkzeug password hashing
- Google: Authlib para login OIDC
- Google Drive: google-api-python-client / google-auth
- Frontend: Jinja2 + CSS/JS sem dependência pesada

## 1. Ambiente

Python 3.10+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

## 2. Configuração

Copie `.env.example` para `.env`.

Defina pelo menos:

```env
SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
ADMIN_EMAIL=seuemail@gmail.com
DATABASE_URL=sqlite:///meu_espaco.db
```

Para PostgreSQL, por exemplo:

```env
DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/meuespaco
```

## 3. Google Login

No Google Cloud Console:

1. Crie um projeto.
2. Ative a configuração de autenticação Google.
3. Crie credencial OAuth para Web application.
4. Adicione:
   - `http://localhost:5000/auth/google/callback`
5. Coloque no `.env`:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
```

O primeiro usuário cujo e-mail seja `ADMIN_EMAIL` é promovido automaticamente a administrador quando entrar/cadastrar.

## 4. Executar

```bash
flask --app app run --debug
```

Abra:

http://127.0.0.1:5000

## 5. Google Drive

A integração do Drive fica no menu administrativo.

O administrador conecta a conta que contém a biblioteca de fotos/vídeos.

O token de atualização é criptografado no banco com `TOKEN_ENCRYPTION_KEY`.

Gere uma chave Fernet:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Coloque o resultado em:

```env
TOKEN_ENCRYPTION_KEY=...
```

### Escopo usado

A integração usa leitura do Drive para que o site não precise tornar os arquivos públicos.

## 6. Segurança importante

- Nunca publique `.env`.
- Nunca publique credenciais OAuth.
- Use HTTPS em produção.
- Troque `SECRET_KEY` e `TOKEN_ENCRYPTION_KEY`.
- Faça backup do PostgreSQL.
- Para vídeos grandes, o endpoint de mídia usa Range quando possível.
- As permissões são verificadas no backend antes da entrega da mídia.

## Deploy gratuito inicial

Uma opção de teste é Render para o Flask. O plano gratuito atualmente permite web services e PostgreSQL, mas tem limitações: o web service dorme após inatividade e o Postgres gratuito tem ciclo de vida limitado. Para um site pessoal real, trate isso como ambiente inicial/teste.

Para o banco, Supabase Free é outra alternativa: PostgreSQL gerenciado, com limites gratuitos atuais de 500 MB de banco e 1 GB de Storage. Neste projeto, porém, as fotos/vídeos permanecem no Google Drive.

Cloudflare pode ficar na frente do domínio como CDN/HTTPS.

## Próxima etapa

Antes de publicar em produção, recomendo:

- migrations com Alembic/Flask-Migrate;
- recuperação de senha por e-mail;
- rate limiting de login;
- MFA para administradores;
- CSP/headers de segurança mais rígidos;
- paginação de galerias;
- thumbnails/cache;
- processamento de metadados do Drive;
- fila para sincronização do Drive;
- testes automatizados.
