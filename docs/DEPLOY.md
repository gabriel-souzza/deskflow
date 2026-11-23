# Deploy — Neon (PostgreSQL) + Docker Hub + Render (backend) + Vercel (frontend)

Este projeto usa um monorepo com:

- `backend/` — API FastAPI, construída em imagem Docker, enviada ao **Docker Hub** e publicada no **Render**.
- `Banco de Dados` — PostgreSQL gerenciado no **Neon.tech** (Serverless, gratuito e permanente).
- `frontend/` — Next.js 16, publicado na **Vercel**.
- `.github/workflows/ci-cd.yml` — pipeline de CI/CD automatizado no **GitHub Actions**.

## Visão geral do pipeline

```text
Pull request ──► testes do backend (pytest) + testes/build do frontend (vitest/next)
                         │
                         ▼
Push na main ──► testes passam
                         ├──► Docker build & push (Docker Hub) ──► Deploy no Render (Web Service)
                         └──► Deploy do frontend na Vercel
```

O deploy só acontece depois que os testes de backend e frontend passam. Em pull requests os testes rodam normalmente, mas nenhuma imagem é publicada e nenhum deploy é disparado.

Arquivos de infraestrutura:

| Arquivo | Função |
| --- | --- |
| `backend/Dockerfile` | Imagem de produção da API Python/FastAPI (compatível com a porta dinâmica `$PORT` do Render) |
| `backend/.dockerignore` | Reduz o contexto de build da imagem |
| `frontend/vercel.json` | Configuração do projeto Next.js na Vercel |
| `.github/workflows/ci-cd.yml` | Pipeline de testes, build/push no Docker Hub e deploys |

---

## 1. Banco de Dados no Neon.tech

Usamos o [Neon](https://neon.tech) em vez do banco nativo do Render, pois o plano Free do Neon é rápido, serverless e não expira em 30 dias.

### 1.1 Criar a instância no Neon

1. Acesse [Neon.tech](https://neon.tech) e crie uma conta (ou faça login com GitHub).
2. Clique em **New Project** e informe:
   - **Name**: `planos-didaticos` (ou nome de sua escolha)
   - **Region**: selecione a região mais próxima (ex.: `US East (Ohio)` ou `US East (N. Virginia)` — preferencialmente a mesma região do Web Service no Render).
   - **Postgres version**: 16 ou superior.
3. Clique em **Create Project**.

### 1.2 Obter e formatar a Connection String

Na tela inicial do projeto no Neon (*Dashboard*), copie a string de conexão em **Connection string**.

O formato padrão do Neon é:
```text
postgresql://neondb_owner:SENHA@ep-xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
```

> [!IMPORTANT]
> **Compatibilidade com asyncpg / SQLAlchemy:**
> O backend usa o driver assíncrono `asyncpg`. Embora o backend possua normalização automática de URL, a boa prática recomendada é definir o prefixo explícito `postgresql+asyncpg://`:
> ```text
> postgresql+asyncpg://neondb_owner:SENHA@ep-xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
> ```
> Guarde essa URL para configurar no Render no Passo 3.

---

## 2. Docker Hub (Repositório da Imagem)

O GitHub Actions fará o build e o push da imagem do backend para o Docker Hub automaticamente.

1. Acesse o [Docker Hub](https://hub.docker.com).
2. Crie uma conta (caso não possua) e anote seu **username** (ex: `seunome`).
3. Crie um repositório público ou privado chamado:
   - **Repository Name**: `planos-didaticos-backend`
4. Crie um **Personal Access Token**:
   - Vá em **Account Settings → Security → Personal access tokens → Generate new token**.
   - Dê uma descrição (ex.: `github-actions-ci-cd`) e selecione as permissões de **Read, Write, Delete**.
   - Copie o token gerado (será o secret `DOCKERHUB_TOKEN` no GitHub).

---

## 3. Backend no Render.com (via Imagem Docker Hub)

Como a imagem é construída pelo GitHub Actions e hospedada no Docker Hub, criamos o serviço no Render diretamente a partir de **Existing Image**.

### 3.1 Criar o Web Service a partir da imagem Docker

1. Acesse o [Render Dashboard](https://dashboard.render.com) e clique em **New + → Web Service**.
2. Selecione a opção **Existing Image** (ao lado de Git).
3. Em **Image URL**, informe o caminho da imagem no Docker Hub:
   ```text
   docker.io/SEU_DOCKERHUB_USERNAME/planos-didaticos-backend:latest
   ```
4. Se o repositório for privado no Docker Hub, clique em **Add Credentials** e informe seu usuário e token do Docker Hub.
5. Em **Instance Type**, escolha o plano **Free**.
6. Em **Region**, escolha preferencialmente a mesma região do banco Neon (ex: `Ohio` ou `Virginia`).

### 3.2 Configurar variáveis de ambiente no Render

Na seção **Environment Variables** do Web Service, adicione:

| Variável | Valor Exemplo | Descrição |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://neondb_owner:senha@ep-...neon.tech/neondb?sslmode=require` | Connection string do Neon formatada |
| `CORS_ORIGINS` | `https://seu-frontend.vercel.app,http://localhost:3000` | Origens autorizadas no CORS |
| `EMAIL_PROVIDER` | `resend` ou `brevo` | Provedor HTTP de e-mail (evita bloqueio SMTP no Render Free) |
| `EMAIL_API_KEY` | `re_123456...` | Chave de API do Resend ou Brevo |
| `EMAIL_FROM` | `nao-responda@seudominio.com` | Remetente verificado |
| `EMAIL_FROM_NAME` | `Planos Didáticos CEFET-MG` | Nome exibido no remetente |
| `TELEGRAM_BOT_TOKEN` | `opcional` | Token de bot do Telegram se habilitado |

### 3.3 Obter o Deploy Hook

1. Após criar o serviço, vá em **Service → Settings**.
2. Role até a seção **Deploy Hook**.
3. Clique em **Create Deploy Hook** (ou copie a URL gerada).
   - Formato: `https://api.render.com/deploy/srv-xxxxxxxxxxxxxxxx?key=yyyyyyyy`
4. Essa URL será cadastrada no secret `RENDER_DEPLOY_HOOK_URL` do GitHub para que a cada push no Docker Hub o Render seja acionado imediatamente.

> [!NOTE]
> Você também pode ativar **Auto-Deploy: Yes** no Render para que ele monitore atualizações na tag `:latest` da imagem no Docker Hub.

---

## 4. Frontend na Vercel

### 4.1 Importar o projeto

1. Acesse o [Vercel Dashboard](https://vercel.com/dashboard) e clique em **Add New → Project**.
2. Conecte o repositório do GitHub.
3. Em **Root Directory**, selecione `frontend`.
4. O framework detectado será **Next.js**. Mantenha os comandos padrão.
5. Clique em **Deploy** inicial e anote a URL gerada (ex.: `https://planos-didaticos.vercel.app`).
6. Atualize a variável `CORS_ORIGINS` no Render com a URL gerada da Vercel.

### 4.2 Obter credenciais para o pipeline

1. Crie um token pessoal na Vercel:
   - **Account Settings → Tokens → Create Token**. Guarde o valor para `VERCEL_TOKEN`.
2. Para obter os IDs da organização e do projeto:
   ```bash
   cd frontend
   npx vercel link
   cat .vercel/project.json
   ```
   O arquivo conterá:
   ```json
   {
     "orgId": "team_xxxxxxxxxxxxxxxx",
     "projectId": "prj_xxxxxxxxxxxxxxxx"
   }
   ```
   Guarde esses valores para os secrets `VERCEL_ORG_ID` e `VERCEL_PROJECT_ID`.

---

## 5. Secrets no GitHub Actions

No repositório do GitHub, vá em **Settings → Secrets and variables → Actions → New repository secret** e cadastre:

| Secret | Como obter |
| --- | --- |
| `DOCKERHUB_USERNAME` | Seu nome de usuário no Docker Hub |
| `DOCKERHUB_TOKEN` | Personal Access Token gerado no Docker Hub |
| `RENDER_DEPLOY_HOOK_URL` | Render → Web Service → Settings → Deploy Hook |
| `VERCEL_TOKEN` | Vercel → Account Settings → Tokens |
| `VERCEL_ORG_ID` | Obtido em `.vercel/project.json` |
| `VERCEL_PROJECT_ID` | Obtido em `.vercel/project.json` |

---

## 6. Como o pipeline automatizado funciona

O arquivo `.github/workflows/ci-cd.yml` é acionado a cada `push` na branch `main`:

1. **`backend-tests`**:
   - Configura Python 3.12, instala dependências e executa os testes unitários e de integração (`pytest -q`).
2. **`frontend-tests`**:
   - Configura Node.js 22, executa os testes do domínio rico/interface (`vitest run`) e valida o build de produção do Next.js 16 (`npm run build`).
3. **`docker-build-push`** (disparado após sucesso dos testes):
   - Faz login no Docker Hub via Buildx.
   - Constrói a imagem otimizada da pasta `backend/` usando cache do GitHub Actions (`gha`).
   - Publica as tags `:latest` e `:<commit-sha>` no Docker Hub: `SEU_USUARIO/planos-didaticos-backend`.
4. **`deploy-backend-render`** (disparado após o push da imagem):
   - Executa um `POST` no Deploy Hook do Render, instruindo o Render a baixar a nova imagem e atualizar o serviço sem downtime.
5. **`deploy-frontend`** (disparado após sucesso dos testes de frontend):
   - Baixa as configurações com `vercel pull`, compila via `vercel build --prod` e publica usando `vercel deploy --prebuilt --prod`.

---

## 7. Verificação e Testes Pós-Deploy

1. **GitHub Actions**: Acompanhe a aba **Actions** para verificar se todos os 5 jobs ficaram verdes.
2. **Docker Hub**: Confirme se o repositório `planos-didaticos-backend` recebeu as tags `:latest` e do commit atual.
3. **Render**: No painel de **Logs**, confira a inicialização da API FastAPI conectada ao Neon:
   ```text
   INFO: Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
   ```
4. **Health Check do Backend**:
   ```bash
   curl https://SEU-BACKEND.onrender.com/health
   # Resposta esperada: {"status":"ok"}
   ```
5. **Frontend**: Abra a URL da Vercel e teste a submissão offline-first de planos didáticos, a visualização de carga horária (RF11) e os campos configuráveis (RF04).

---

## 8. Troubleshooting

| Sintoma | Causa provável / Solução |
| --- | --- |
| Erro de conexão com banco no Render | Verifique se a string do Neon inclui `?sslmode=require` e se o prefixo é `postgresql+asyncpg://`. |
| `docker build` ou `push` falha no GitHub Actions | Verifique se os secrets `DOCKERHUB_USERNAME` e `DOCKERHUB_TOKEN` estão corretos e se o token tem permissão de escrita (*Write*). |
| Render não atualiza após o push da imagem | Certifique-se de que o secret `RENDER_DEPLOY_HOOK_URL` está configurado ou ative **Auto-Deploy: Yes** na configuração da imagem no Render. |
| API demora na primeira requisição | No plano Free do Render, serviços web hibernam após 15 min de inatividade; a primeira requisição demora ~45 segundos para reativar. |
| Deploy na Vercel falha com `ENOENT` | Certifique-se de que o comando `vercel build` seja executado da raiz do repositório, pois o **Root Directory** no painel da Vercel já aponta para `frontend`. |
| E-mails não chegam aos destinatários | O plano Free do Render bloqueia conexões SMTP convencionais (587/465). Use `EMAIL_PROVIDER=resend` (ou `brevo`) com a respectiva chave `EMAIL_API_KEY`. |
