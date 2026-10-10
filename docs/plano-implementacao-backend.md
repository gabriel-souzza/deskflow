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

### 1.3 Aplicação (Use Cases — parcial)
- [x] `CreateBookingUseCase` e `CancelBookingUseCase` orquestram os endpoints via interfaces e Unit of Work
- [x] `ReleaseExpiredBookingsUseCase` é chamado pelo scheduler
- [ ] Completar stubs: bloqueio de feriados, geração diária, fila de espera, sincronização de ponto e relatórios
- [ ] Adicionar testes comportamentais para cada caso de uso

### 1.4 Adapters (Interface Adapters)
- [x] Controllers FastAPI: reservas, check-in, administração, relatórios e espaços
- [x] Repositórios PostgreSQL ativos para booking, employee, quota, workspace e auditoria são exercitados no fluxo transacional
- [x] Testes SQLite exercitam os adapters de persistência, incluindo janela e waitlist
- [x] Eventos: `SsePublisher`, `AuditLogHandler`, `QuotaAlertHandler`, `WaitlistHandler`

### 1.5 Infra (Frameworks & Drivers)
- [x] `database.py` (SQLAlchemy 2.0 async engine + session)
- [x] `security.py` (JWT/OAuth2)
- [x] `qr_generator.py` (`qrcode` + `pillow`)
- [x] `models.py` (ORM — 9 tabelas do DER)
- [x] `migrations/alembic.ini` + `env.py` + migrations `001` e `002`

### 1.6 Testes (TDD — Pirâmide)
- [x] Domínio e controllers: testes pytest com FastAPI TestClient
- [x] Integração API + persistência em SQLite, incluindo rollback por cota insuficiente
- [x] Teste PostgreSQL opt-in aplica migrations e valida reserva/reembolso quando `TEST_DATABASE_URL` está definido
- [x] Gate de 80% cobre controllers, eventos, adapters, casos de uso ativos, domínio, infraestrutura e bootstrap
- [ ] Casos de uso restantes permanecem incompletos e são explicitamente omitidos da métrica

---

## 2. LACUNAS RESTANTES (NÃO-BLOQUEANTES PARA BACKEND)

Conforme `documento-software.md` e `escopo-arquitetura-deskflow.md`:

| Lacuna | Onde deveria estar | Impacto |
|---|---|---|
| **Frontend** (`apps/web/`) | `Next.js 15 + shadcn/ui + TanStack Query` | Não impede API backend funcionar |
| **Migrations completas** (versões adicionais) | `migrations/versions/` para alterações futuras | `001` cobre o DER inicial; novas versões para futuras alterações |
| **Use cases restantes** | Geração diária, relatórios, waitlist, feriados, quota e ponto | Stubs ou ainda não conectados; fora do gate até implementação |
| **Teste PostgreSQL real executado** | Rodar `test_postgres_booking.py` com `TEST_DATABASE_URL` | O teste está pronto; requer serviço PostgreSQL disponível |
| **Monitoramento / Métricas** | Prometheus, logging estruturado (`structlog`) | Documentado em `escopo-arquitetura-deskflow.md` §2; não implementado |
| **Geração diária (UC16)** | `GenerateDailyAvailabilityUseCase` + job diário | Use case ainda não implementado; sem geração automática de janelas |
| **Notificação da fila (UC05)** | `NotifyWaitlistUseCase` + eventos SSE | Use case ainda não implementado; vagas liberadas não notificam a fila |

---

## 3. ORDEM DE IMPLEMENTAÇÃO (TDD — JÁ EXECUTADA)

Conforme §10 de `documento-software.md`:

### Sprint 1 — Fundação do Domínio (✅ CONCLUÍDO)
- `TimeSlot.__post_init__` (I1)
- `BookingWindowRepository.count_by_window()` (I2 — capacidade)
- `QuotaPeriod.consume()` (I3)
- `Booking.confirm()` (I4)

### Sprint 2 — Motor de Agendamento (🟡 PARCIAL)
- `ReleaseExpiredBookingsUseCase.execute()` (PENDING → EXPIRED) está ligado ao scheduler
- Reserva/cancelamento são orquestrados por use cases; repositories e Unit of Work fazem a persistência atômica
- Confirmação por QR está implementada no controller
- Fila de espera ainda não notifica automaticamente quando uma vaga é liberada

### Sprint 3 — Frontend e Relatórios (⏳ DEPENDE DO FRONTEND)
- `GenerateReportUseCase.execute()` (CSV/PDF)
- Controllers retornam 200/400/409/402
- SSE stream (`SsePublisher`)

---

## 4. CRITÉRIOS DE ACEITAÇÃO

Os fluxos de reserva/cancelamento têm testes de use case, API e persistência. O teste PostgreSQL real está disponível, mas precisa de `TEST_DATABASE_URL` e não foi executado neste ambiente. Nem todos os RFs têm caso de uso completo; rastreabilidade documental não substitui esses testes.

---

## 5. COMANDOS PARA EXECUTAR

```bash
# Setup (uv — gerenciador moderno)
cd backend
uv sync --all-extras --no-dev

# Migrations
uv run alembic upgrade head

# Testes (pirâmide TDD)
uv run pytest src/tests/domain -v
uv run pytest src/tests/application -v

# Docker Compose (API + PostgreSQL)
docker-compose up -d

# Executar API
python src/main.py
```

---

## 6. CONCLUSÃO

A API REST, reservas/cancelamentos transacionais e o fluxo de expiração estão ligados a casos de uso. O gate cobre 80% dos módulos implementados; stubs continuam explicitamente excluídos. Permanecem pendentes fila de espera, geração diária, relatórios via application, ativação do teste PostgreSQL em ambiente com banco e monitoramento.
