# DeskFlow

Plataforma de gestão de espaços híbridos para controle de reservas de estações e salas com alocação dinâmica, check-in via QR Code, controle de cotas por centro de custo e relatórios de utilização.

## Problema

Transição para modelo híbrido com 500 colaboradores e 250 estações gera três ineficiências interdependentes:

1. **Overbooking em dias de pico** — capacidade insuficiente nos horários nobres
2. **No-show de 35%** — estações reservadas e vazias sem mecanismo de liberação
3. **Custo de ociosidade** — R$ 169.520/mês com 65% de utilização efetiva

## Solução

Motor de agendamento com:
- Grid de slots de 15min (08:00–18:00) com validação de conflitos em tempo real
- Check-in via QR Code com tolerância de 10 min (estações) / 15 min (salas) e liberação automática
- Cotas por centro de custo com visibilidade em tempo real
- Fila de espera FIFO com notificação SSE quando vaga surge
- Integração com sistema de ponto via REST para política presencial

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Next.js (TypeScript) + shadcn/ui + Tailwind + TanStack Query |
| Backend | Python (FastAPI) + SQLAlchemy 2.0 + Zod |
| Banco | PostgreSQL + Alembic |
| Realtime | Server-Sent Events (SSE) |
| QR Code | `qrcode` + `pillow` |
| Scheduler | APScheduler |
| Testes | pytest + dataclasses frozen |

## Arquitetura

```
src/
├── domain/           # Entidades, Value Objects, interfaces de repository
│   ├── entities/      # Booking, AvailabilityWindow, QuotaPeriod, Workspace, Waitlist, Employee, AuditLog, Holiday
│   ├── value_objects/ # TimeSlot, Capacity
│   └── repositories/ # Interfaces: BookingRepository, AvailabilityWindowRepository, etc.
├── application/      # Use Cases (Clean Architecture)
│   └── use_cases/    # CreateBooking, ConfirmBooking, CancelBooking, ReleaseExpired, NotifyWaitlist, SetQuota, GenerateReport, SyncPoint, BlockHolidays, GenerateDailyAvailability
├── adapters/
│   ├── controllers/  # FastAPI REST endpoints (boundary)
│   ├── repositories/ # Implementações PostgreSQL (SQLAlchemy 2.0)
│   └── events/       # SSE Publisher
└── infra/
    ├── database.py   # SQLAlchemy session
    ├── migrations/   # Alembic
    ├── security.py   # JWT/OAuth2
    └── qr_generator.py
```

**Invariantes de domínio (garantidas por código, não por convenção):**

| # | Invariante | Implementação |
|---|------------|---------------|
| I1 | Slot alinhado em grid de 15min | `TimeSlot.__post_init__` |
| I2 | AvailabilityWindow nunca excede capacidade | `AvailabilityWindow.is_full()` |
| I3 | QuotaPeriod nunca excede total_hours | `QuotaPeriod.consume()` |
| I4 | Transições de estado unidirecionais | `Booking.confirm/cancel` |
| I5 | Confirmação e consumo de quota atômicos | Use case orchestration |
| I6 | Sem sobreposição de reservas confirmadas | Lock otimista via `version_id` |

**Domínio puro (zero dependências externas):** todas as entidades e value objects são `dataclasses` com `frozen=True`. Testáveis sem mocks.

## Modelo de Dados

```
┌─────────────┐     ┌──────────────────────┐     ┌───────────────┐
│  Workspace  │────▶│  AvailabilityWindow   │◀────│ BookingWindow │
│  (estação/ │     │  (slot de 15min)     │     │  (junção N-N) │
│   sala)     │     │  version_id (lock)    │     └───────┬───────┘
└─────────────┘     └──────────────────────┘             │
        │                                            ┌─────▼─────┐
        │           ┌─────────────┐                  │  Booking  │
        │           │ QuotaPeriod │◀─────────────────│ (aggregate)│
        │           │ (por mês)   │                  └─────┬─────┘
        │           └─────────────┘                        │
        │           ┌─────────────┐                 ┌─────▼─────┐
        └──────────▶│  Employee   │────────────────▶│ CostCenter │
                    │             │                 │            │
                    └─────────────┘                 └────────────┘
```

**Estratégia de herança:** `Station` e `MeetingRoom` compartilham a tabela `workspaces` com discriminador `type`.

## API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/workspaces` | Listar espaços disponíveis |
| GET | `/api/v1/workspaces/{id}/availability?day=YYYY-MM-DD` | Disponibilidade em slots de 15 min |
| POST | `/api/v1/bookings` | Criar reserva `PENDING`; parâmetros: `workspace_id`, `employee_id`, `cost_center_id`, `slot_start`, `slot_end`; retorna `qr_token` assinado |
| POST | `/api/v1/bookings/{id}/checkin?qr_token=...` | Validar token QR e confirmar reserva dentro da tolerância |
| DELETE | `/api/v1/bookings/{id}` | Cancelar reserva com pelo menos 2h de antecedência e devolver a cota |
| GET | `/api/v1/reports/utilization?day=YYYY-MM-DD` | Dashboard calculado a partir das reservas persistidas (admin) |
| GET | `/api/v1/reports/export?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&format=csv\|pdf` | Baixar relatório CSV ou PDF (admin) |
| POST | `/api/v1/admin/accounts` | Criar conta de colaborador vinculada a centro de custo (admin); JSON com `name`, `email`, `password`, `cost_center_id` e `is_eligible_for_booking` opcional |
| POST | `/api/v1/auth/login` | Autenticar conta por email e senha; para testes, o campo `username` recebe o email cadastrado |
| GET | `/api/v1/admin/quotas` | Listar períodos de cota (admin) |
| PUT | `/api/v1/admin/quotas/{cost_center_id}` | Definir cota mensal; JSON: `{"monthly_quota_hours": 40}` (admin) |
| POST | `/api/v1/admin/workspaces` | Cadastrar espaço (admin) |
| GET | `/api/v1/availability/stream` | SSE com eventos de reservas e espaços |
| GET | `/docs` | Swagger / OpenAPI (interativo) |
| GET | `/redoc` | ReDoc (alternativo) |
| GET | `/openapi.json` | Schema OpenAPI JSON |
| GET | `/health` | Health check (status 200) |

Rotas administrativas e relatórios exigem `Authorization: Bearer <token>` com papel `admin`. Para criar uma conta no Swagger, autentique-se primeiro com `admin` / `admin123`, autorize com o JWT e chame `POST /api/v1/admin/accounts` com um centro de custo existente. A senha precisa ter pelo menos 12 caracteres; o cadastro não concede elegibilidade por padrão. O login demo `admin` / `admin123` é apenas para desenvolvimento. O stream SSE é mantido em memória por processo; com múltiplas instâncias, use um barramento compartilhado para distribuir eventos. `/health` verifica apenas se o processo responde, não a conexão com o banco.

## Testes

Pirâmide de testes:

```
      ┌─────────────┐
      │   e2e /     │  ← Mínimo (1–2 cenários críticos)
      │  integração │  ← PostgreSQL real, API HTTP
      ├─────────────┤
      │   adapter   │  ← FastAPI TestClient
      ├─────────────┤
      │ application │  ← pytest + fake repository
      ├─────────────┤
      │   domain    │  ← Muitos (pytest, dataclasses frozen)
      └─────────────┘
```

Cada RF tem pelo menos um teste de domínio que valida a regra de negócio e um teste de integração que valida a rastreabilidade.

## Documentação de Projeto

| Documento | Descrição |
|-----------|-----------|
| `docs/proposta-comercial-deskflow.md` | Proposta comercial, ROI, cronograma |
| `docs/diagnostico-operacional-deskflow.md` | Diagnóstico de problemas, matriz de riscos |
| `docs/escopo-arquitetura-deskflow.md` | Escopo funcional e arquitetura técnica |
| `docs/deskflow_ideacao_arquitetura.md` | Decisões arquiteturais (Ramo A/B/C) |
| `docs/documento-software.md` | Especificação completa (requisitos, UML, DDD, TDD) |
| `docs/plano-implementacao-backend.md` | Plano de implementação do backend (status, lacunas, TDD) |

## Documentação da API

A API é documentada automaticamente pelo **FastAPI** via **OpenAPI**:

- **Swagger UI** (interativo): `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Segurança

- **Autenticação**: JWT (HS256) via `infra/security.py`
- **Hashing**: PBKDF2-HMAC-SHA256 com salt aleatório para senhas de contas
- **HTTPS**: Obrigatório em produção (configuração do reverse proxy)
- **Tokens**: Emissão e validação de JWT para autorização de requisições protegidas

## Cobertura de Testes

Meta: **80% de cobertura** mantida para assegurar a confiabilidade das alterações.

- **Domain**: `src/tests/domain/` — invariantes I1-I6, Value Objects
- **Application**: `src/tests/application/` — use cases, orquestração de agregados
- **Adapter**: `src/tests/adapters/` — FastAPI TestClient
- **Integration**: `src/tests/integration/` — PostgreSQL real

```bash
# Executar com cobertura
cd backend
uv run pytest src/tests -v --cov=src --cov-report=term-missing --cov-fail-under=80
```


## Configuração

Variáveis de ambiente (`.env`):

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/deskflow
JWT_SECRET=your-secret-key
SSE_HEARTBEAT_INTERVAL=30
CHECKIN_TOLERANCE_MINUTES=10
CANCELLATION_MINIMUM_HOURS=2
SLOT_DURATION_MINUTES=15
```

## Instalação (uv - gerenciador de pacotes moderno)

```bash
# Backend - instala dependências com uv (3-5x mais rápido que pip)
uv sync --all-extras --no-dev
uv run alembic upgrade head

# Frontend
cd apps/web
npm install

# Testes
uv run pytest src/tests/domain -v
uv run pytest src/tests/application -v
```

## Execução com Docker Compose

```bash
# Subir API, PostgreSQL e pgAdmin
docker compose up -d --build

# Ver logs
docker compose logs -f api
```

O pgAdmin fica em `http://localhost:5050` (email `admin@deskflow.com`, senha `deskflow-dev-pgadmin` por padrão de desenvolvimento). Para registrar o servidor, use host `db`, porta `5432`, database `deskflow`, usuário `postgres` e senha `postgres`. Esses valores padrão são apenas para desenvolvimento; defina `PGADMIN_DEFAULT_EMAIL` e `PGADMIN_DEFAULT_PASSWORD` no `.env` para substituí-los.

## Status do Backend (Atualizado)

O backend está construído seguindo a arquitetura **Clean Architecture + DDD + TDD** definida no `documento-software.md`:

- **Domínio (`src/domain/`)**: 8 entidades + 2 VO + 6 repos ABC
- **Application**: 10 use cases completos
- **Adapters**: 4 controllers + 3 repos + 4 events
- **Infra**: `database.py`, `security.py`, `qr_generator.py`, `migrations/`
- **DevOps**: `uv`, Docker, docker-compose

**Correções aplicadas**: `Decimal`, `utcnow()` deprecated, `seats_available` duplicado, `employee.py` conflito, `time_slot.py` tipo.

## Licença

Proprietário — confidencial.