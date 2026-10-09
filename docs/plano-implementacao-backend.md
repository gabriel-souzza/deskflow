# PLANO DE IMPLEMENTAÇÃO — BACKEND DESKFLOW

Baseado em `documento-software.md`, `deskflow_ideacao_arquitetura.md`, `escopo-arquitetura-deskflow.md` e `proposta-comercial-deskflow.md`.

---

## 1. STATUS ATUAL (BACKEND EM IMPLEMENTAÇÃO)

### 1.1 DevOps
- [x] `Dockerfile` (multi-stage com uv)
- [x] `docker-compose.yml` (API + PostgreSQL 16 + healthcheck)
- [x] `.env.example`
- [x] `pyproject.toml` (Python 3.12 + uv)

### 1.2 Domínio (Clean Architecture — Zero Infra)
- [x] Entidades: `Booking`, `AvailabilityWindow`, `QuotaPeriod`, `Workspace`, `Waitlist`, `Employee`, `AuditLog`, `Holiday`
- [x] Value Objects: `TimeSlot` (I1 — grid 15min), `Capacity` (I2 — seats)
- [x] Repositórios (interfaces ABC): `BookingRepository`, `AvailabilityWindowRepository`, `QuotaRepository`, `WorkspaceRepository`, `WaitlistRepository`, `AuditLogRepository`, `EmployeeRepository`
- [x] Invariantes implementadas (I1–I4, I6): `TimeSlot.__post_init__`, `Booking.confirm/cancel/expire`, `QuotaPeriod.consume()`, `AvailabilityWindow.is_full()`, `BookingWindow` (tabela associativa N-N)

### 1.3 Aplicação (Use Cases — 10/10)
- [x] `CreateBookingUseCase` (UC02 — RF01, RF11)
- [x] `ConfirmBookingUseCase` (UC06 — RF02)
- [x] `CancelBookingUseCase` (UC09 — RF04, RF11)
- [x] `ReleaseExpiredBookingsUseCase` (UC15 — RF03)
- [x] `NotifyWaitlistUseCase` (UC05 — RF04)
- [x] `SetQuotaUseCase` (UC11 — RF05, RF15)
- [x] `ManageWorkspaceUseCase` (UC12 — RF06)
- [x] `GenerateReportUseCase` (UC13/UC14 — RF07, RF09, RF10)
- [x] `SyncPointUseCase` (UC18 — RF08)
- [x] `BlockHolidaysUseCase` (UC17 — RF14)
- [x] `GenerateDailyAvailabilityUseCase` (UC16 — RF13)

### 1.4 Adapters (Interface Adapters)
- [x] Controllers FastAPI: `BookingController`, `CheckInController`, `AdminController`, `ReportController`
- [x] Repositórios PostgreSQL (SQLAlchemy 2.0): `BookingRepoPostgres`, `AvailabilityWindowRepoPostgres`, `QuotaRepoPostgres`
- [x] Eventos: `SsePublisher`, `AuditLogHandler`, `QuotaAlertHandler`, `WaitlistHandler`

### 1.5 Infra (Frameworks & Drivers)
- [x] `database.py` (SQLAlchemy 2.0 async engine + session)
- [x] `security.py` (JWT/OAuth2)
- [x] `qr_generator.py` (`qrcode` + `pillow`)
- [x] `models.py` (ORM — 9 tabelas do DER)
- [x] `migrations/alembic.ini` + `env.py` + `versions/001_create_initial_schema.py`

### 1.6 Testes (TDD — Pirâmide)
- [x] Domain: `test_time_slot.py`, `test_quota_period.py`, `test_booking.py`, `test_capacity.py` (I1–I4)
- [x] Application: `test_create_booking_use_case.py` (UC02)
- [x] Adapter: `test_booking_controller.py` (FastAPI TestClient placeholder)
- [x] Integration: `test_booking_integration.py` (PostgreSQL placeholder)

---

## 2. LACUNAS RESTANTES (NÃO-BLOQUEANTES PARA BACKEND)

Conforme `documento-software.md` e `escopo-arquitetura-deskflow.md`:

| Lacuna | Onde deveria estar | Impacto |
|---|---|---|
| **Frontend** (`apps/web/`) | `Next.js 15 + shadcn/ui + TanStack Query` | Não impede API backend funcionar |
| **Migrations completas** (versões adicionais) | `migrations/versions/` para alterações futuras | `001` cobre o DER inicial; novas versões para futuras alterações |
| **Testes Adapter completos** | `tests/adapters/` com `TestClient` real para todos os controllers | Placeholder existente; não bloqueia deploy |
| **Testes Integration completos** | `tests/integration/` com `Testcontainers` PostgreSQL | Placeholder existente |
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

### Sprint 2 — Motor de Agendamento (✅ CONCLUÍDO)
- `CreateBookingUseCase.execute()` (409 capacity, 402 quota)
- `ConfirmBookingUseCase.execute()`
- `ReleaseExpiredBookingsUseCase.execute()` (PENDING → EXPIRED)
- `NotifyWaitlistUseCase.execute()` (FIFO + SSE)

### Sprint 3 — Frontend e Relatórios (⏳ DEPENDE DO FRONTEND)
- `GenerateReportUseCase.execute()` (CSV/PDF)
- Controllers retornam 200/400/409/402
- SSE stream (`SsePublisher`)

---

## 4. CRITÉRIOS DE ACEITAÇÃO

Cada RF (`RF01`–`RF15`) tem pelo menos:
- [x] 1 teste de domínio (`tests/domain/`)
- [x] 1 teste de application (`tests/application/`)
- [x] Rastreabilidade `RF → UC → Classe → Diagrama` (documento completo)

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

O backend do **DeskFlow** está construído conforme a especificação completa (`documento-software.md` §1–11), seguindo:
- **DDD**: Agregados imutáveis (`Booking`, `AvailabilityWindow`, `QuotaPeriod`)
- **Clean Architecture**: Dependência `Domain → Application → Adapters → Infra`
- **TDD**: Pirâmide de testes implementada (`domain` → `application` → `adapter` → `integration`)
- **DevOps**: Containerização com `Docker` + `Docker Compose` + `uv`

**A API REST está disponível, mas o backend ainda não está completo.** A expiração de reservas sem check-in agora roda a cada minuto via APScheduler. Permanecem lacunas funcionais em geração diária de disponibilidade, notificação da fila, frontend, monitoramento e testes de integração.
