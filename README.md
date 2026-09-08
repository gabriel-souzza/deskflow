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
| GET | `/api/v1/workspaces/{id}/availability` | Disponibilidade por dia |
| POST | `/api/v1/bookings` | Criar reserva |
| POST | `/api/v1/bookings/{id}/checkin` | Check-in via QR Code |
| DELETE | `/api/v1/bookings/{id}` | Cancelar reserva (2h antecedência) |
| GET | `/api/v1/reports/utilization` | Dashboard de utilização |
| GET | `/api/v1/reports/export` | Exportar CSV/PDF |
| GET | `/api/v1/admin/quotas` | Listar quotas por centro de custo |
| PUT | `/api/v1/admin/quotas/{id}` | Configurar quota |
| POST | `/api/v1/admin/workspaces` | Cadastrar espaço |
| GET | `/api/v1/availability/stream` | SSE stream de atualizações |

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

## Instalação

```bash
# Backend
cd src
pip install -r requirements.txt
alembic upgrade head

# Frontend
cd apps/web
npm install

# Testes
pytest src/tests/domain -v
pytest src/tests/application -v
```

## Licença

Proprietário — confidencial.