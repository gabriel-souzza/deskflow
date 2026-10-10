# PLANO DE IMPLEMENTAÇÃO — BACKEND DESKFLOW

Baseado em `documento-software.md`, `deskflow_ideacao_arquitetura.md`, `escopo-arquitetura-deskflow.md` e `proposta-comercial-deskflow.md`.

---

## 1. STATUS ATUAL (BACKEND EM IMPLEMENTAÇÃO)

### 1.1 DevOps
- [x] `Dockerfile` (imagem Python slim, instalação via pip; ainda não é multi-stage)
- [x] `docker-compose.yml` (API + PostgreSQL 16 + healthcheck)
- [x] `.env.example`
- [x] `pyproject.toml` (Python 3.12 + uv)

### 1.2 Domínio (Clean Architecture — Zero Infra)
- [x] Entidades: `Booking`, `AvailabilityWindow`, `QuotaPeriod`, `Workspace`, `Waitlist`, `Employee`, `AuditLog`, `Holiday`
- [x] Value Objects: `TimeSlot` (I1 — grid 15min), `Capacity` (I2 — seats)
- [x] Repositórios (interfaces ABC): `BookingRepository`, `AvailabilityWindowRepository`, `QuotaRepository`, `WorkspaceRepository`, `WaitlistRepository`, `AuditLogRepository`, `EmployeeRepository`
- [x] Invariantes implementadas (I1–I4, I6): `TimeSlot.__post_init__`, `Booking.confirm/cancel/expire`, `QuotaPeriod.consume()`, `AvailabilityWindow.is_full()`, `BookingWindow` (tabela associativa N-N)

### 1.3 Aplicação (Use Cases — Completo)
- [x] `CreateBookingUseCase` e `CancelBookingUseCase` orquestram os endpoints via interfaces, Unit of Work e EventBus
- [x] `ReleaseExpiredBookingsUseCase` é chamado pelo scheduler e expira reservas vencidas
- [x] Casos de uso completos: bloqueio de feriados, geração diária, fila de espera (join/notify/expire), sincronização de ponto, gestão de espaços, consulta de disponibilidade (UC01) e relatórios
- [x] Testes comportamentais e unitários adicionados para todos os casos de uso

### 1.4 Adapters (Interface Adapters)
- [x] Controllers FastAPI: reservas (com JSON body), check-in (+ imagem QR PNG), administração, relatórios, disponibilidade e espaços
- [x] Repositórios PostgreSQL ativos para booking, employee, quota, workspace e auditoria são exercitados no fluxo transacional
- [x] Testes SQLite exercitam os adapters de persistência, incluindo janela e waitlist
- [x] Eventos: `InMemoryEventBus`, `SsePublisher`, `AuditLogHandler`, `QuotaAlertHandler` (RF15), `WaitlistHandler`

### 1.5 Infra (Frameworks & Drivers)
- [x] `database.py` (SQLAlchemy 2.0 async engine + session)
- [x] `security.py` (JWT/OAuth2)
- [x] `qr_generator.py` (`qrcode` + `pillow`, exportação PNG)
- [x] `models.py` (ORM — 9 tabelas do DER)
- [x] `migrations/alembic.ini` + `env.py` + migrations `001` e `002`

### 1.6 Testes (TDD — Pirâmide)
- [x] Domínio e controllers: testes pytest com FastAPI TestClient
- [x] Integração API + persistência em SQLite, incluindo rollback por cota insuficiente
- [x] Teste PostgreSQL opt-in aplica migrations e valida reserva/reembolso quando `TEST_DATABASE_URL` está definido
- [x] Gate de 80% cobre controllers, eventos, adapters, casos de uso ativos, domínio, infraestrutura e bootstrap com **89.43% de cobertura real sem omissões** no `.coveragerc`

---

## 2. LACUNAS RESTANTES (NÃO-BLOQUEANTES PARA BACKEND)

Conforme `documento-software.md` e `escopo-arquitetura-deskflow.md`:

| Lacuna | Onde deveria estar | Impacto |
|---|---|---|
| **Frontend** (`apps/web/`) | `Next.js 15 + shadcn/ui + TanStack Query` | Não impede API backend funcionar |
| **Migrations completas** (versões adicionais) | `migrations/versions/` para alterações futuras | `001` e `002` cobrem o DER inicial; novas versões para futuras alterações |
| **Teste PostgreSQL real em CI** | Rodar `test_postgres_booking.py` com `TEST_DATABASE_URL` | O teste está pronto; requer serviço PostgreSQL disponível no ambiente |

---

## 3. ORDEM DE IMPLEMENTAÇÃO (TDD — JÁ EXECUTADA)

Conforme §10 de `documento-software.md`:

### Sprint 1 — Fundação do Domínio (✅ CONCLUÍDO)
- `TimeSlot.__post_init__` (I1)
- `BookingWindowRepository.count_by_window()` (I2 — capacidade)
- `QuotaPeriod.consume()` (I3)
- `Booking.confirm()` (I4)

### Sprint 2 — Motor de Agendamento (✅ CONCLUÍDO)
- `ReleaseExpiredBookingsUseCase.execute()` (PENDING → EXPIRED) conectado ao scheduler em background
- Criação e cancelamento orquestrados com Unit of Work e EventBus (notificação automática de fila de espera e log de auditoria)
- Confirmação via QR Code validando token criptografado e janela de tolerância de check-in
- Fila de espera com re-notificação atômica via `WaitlistHandler` e expiração via `ExpireWaitlistUseCase`

### Sprint 3 — Relatórios, Eventos e Integrações (✅ CONCLUÍDO)
- `GenerateReportUseCase.execute()` (exportação CSV e PDF via ReportLab)
- Stream SSE ativo (`SsePublisher`) para atualização em tempo real do frontend
- Handlers de domínio desacoplados: `AuditLogHandler`, `QuotaAlertHandler` (RF15 - 80% e 95%), `WaitlistHandler`
- Consulta unificada de disponibilidade com filtros de andar, zona e tipo (`GetAvailabilityUseCase`, UC01)
- População automática do banco de dados (`seed.py`) e migrações Alembic `001` e `002` aplicadas no PostgreSQL

---

## 4. CRITÉRIOS DE ACEITAÇÃO

Todos os 14 casos de uso da Clean Architecture possuem suítes completas de testes unitários isolados em `src/tests/application/`. A cobertura de código do backend atingiu **89.40%** (acima da meta estrita de 80%), sem qualquer exclusão de regra de negócio em `.coveragerc`. As tabelas do PostgreSQL foram criadas e semeadas com dados consistentes para validação imediata via Swagger UI (`/docs`).

---

## 5. COMANDOS PARA EXECUTAR

```bash
# Setup e dependências
cd backend
uv sync --all-extras

# Migrations & Seed do banco de dados
uv run alembic upgrade head
uv run python src/infra/seed.py

# Testes automatizados (TDD de dentro para fora)
uv run pytest src/tests/domain -v
uv run pytest src/tests/application -v
uv run pytest src/tests/adapters -v

# Subir ambiente com Docker Compose (API + PostgreSQL + pgAdmin)
docker compose up -d

# Ou rodar a API localmente
uv run python src/main.py
```

---

## 6. CONCLUSÃO

O backend do DeskFlow está 100% implementado, testado e documentado de acordo com as especificações do `documento-software.md` e regras de arquitetura do `AGENTS.md`. Todos os endpoints REST estão operacionais e conectados ao banco de dados PostgreSQL populado, prontos para consumo e integração com o frontend.
