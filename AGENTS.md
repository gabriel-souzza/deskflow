# AGENTS.md — Guia para Agentes de IA

Este guia define convenções, comandos e regras de decisão para agentes de IA que trabalham no projeto DeskFlow.

## Domínio do Projeto

Plataforma de gestão de espaços híbridos: reserva de estações/salas com check-in via QR Code, cotas por centro de custo, fila de espera, relatórios de utilização.

**Ler primeiro** antes de qualquer tarefa:
- `docs/documento-software.md` — especificação completa (requisitos, UML, DDD, TDD)
- `docs/deskflow_ideacao_arquitetura.md` — decisão arquitetural (Ramo C: agregados imutáveis)
- `docs/escopo-arquitetura-deskflow.md` — escopo funcional e stack
- `README.md` — overview rápido

## Stack e Convenções

| Camada | Tecnologia | Convenção |
|--------|-----------|-----------|
| Domínio (Python) | `dataclasses(frozen=True, slots=True)` | Sem dependência de framework/ORM. Testável com pytest sem I/O. |
| Application (Python) | Classes com construtor injetando dependências | 1 use case por caso de uso. Depende só de interfaces de repository. |
| Adapter (Python) | SQLAlchemy 2.0 + FastAPI | Implementações concretas de repository e controllers. |
| Frontend (TypeScript) | Next.js 15 + shadcn/ui + TanStack Query + Zod | Zod como single source of truth para validação. |
| Banco | PostgreSQL + Alembic | Migrações versionadas. |

## Regras de Design (Invariantes do Domínio)

Todas as invariantes I1–I6 do `documento-software.md` §10 são **invioláveis**. Implementar como:

| # | Invariante | Onde mora |
|---|------------|-----------|
| I1 | Slot em grid 15min | `TimeSlot.__post_init__` |
| I2 | Capacity nunca excedida | `AvailabilityWindow.is_full(count)` + UNIQUE constraint em `booking_windows` |
| I3 | Quota monotonic | `QuotaPeriod.consume()` |
| I4 | Estados unidirecionais | `Booking.confirm/cancel` |
| I5 | Booking + Quota atomic | Transação no `CreateBookingUseCase` |
| I6 | Sem sobreposição | Lock otimista via `version_id` em `availability_windows` |

## Estrutura de Pastas (Clean Architecture)

```
src/
├── domain/           # entidades, value objects, interfaces de repository
│   ├── entities/
│   ├── value_objects/
│   └── repositories/  # apenas interfaces (ABCs)
├── application/      # use cases
│   └── use_cases/
├── adapters/
│   ├── controllers/  # FastAPI REST
│   └── repositories/ # implementações SQLAlchemy
└── infra/
    ├── database.py
    ├── migrations/   # Alembic
    └── security.py
```

**Regra de dependência:** Domain → Application → Adapters → Infra. **Nenhuma lib de infra dentro de domain/application.**

## Convenções de Código

### Python (domínio)

- `dataclass(frozen=True, slots=True)` para entidades e value objects
- `__post_init__` para validações (raise `DomainError` subclasses)
- Nenhum `import` de SQLAlchemy, FastAPI ou qualquer lib de I/O
- Métodos que retornam novo estado: usar `dataclasses.replace(self, ...)` para preservar imutabilidade

### Python (use cases)

- Construtor recebe **interfaces** de repository (não implementações)
- Cada use case é uma classe com método `execute(cmd: Command) -> Result`
- Publicar domain events via `EventBus` (não chamar adapters direto)

### TypeScript (frontend)

- Zod schema → `z.infer<typeof X>` para tipos
- Componentes em `apps/web/src/features/<feature>/components/`
- Hooks em `apps/web/src/features/<feature>/hooks/`
- `apps/web/src/features/<feature>/domain/` para lógica pura (testável sem React)

## TDD (red → green → refactor)

**Sempre de dentro pra fora:**

1. **Domínio primeiro** — `pytest src/tests/domain` (rápido, sem I/O)
   - `TimeSlot` rejeita slot inválido
   - `AvailabilityWindow.is_full(count)` retorna true quando count >= seats
   - `QuotaPeriod.consume()` levanta `QuotaExceededError` quando excede
   - `Booking.confirm()` levanta `InvalidStateTransitionError` quando não PENDING
2. **Application** — `pytest src/tests/application` (com fake/in-memory repository)
3. **Adapter** — `pytest src/tests/adapters` (TestClient FastAPI, Testcontainers PostgreSQL)
4. **Integration** — `pytest src/tests/integration` (poucos, lentos)

## Comandos Úteis

```bash
# Setup
pip install -r requirements.txt
alembic upgrade head
npm install

# Testes
pytest src/tests/domain -v        # rápido
pytest src/tests/application -v
pytest src/tests/adapters -v
pytest src/tests/integration -v

# Lint e typecheck
ruff check src/
mypy src/domain src/application
npm run lint
npm run typecheck

# Banco
alembic revision --autogenerate -m "mensagem"
alembic downgrade -1
```

## Glossário de Termos

Ver `docs/documento-software.md` §11.1. Linguagem ubíqua: usar os mesmos termos em código, comentários e commits (Booking, AvailabilityWindow, QuotaPeriod, Waitlist, CostCenter, Employee).

## Não Fazer

- ❌ Importar SQLAlchemy ou FastAPI dentro de arquivos em `src/domain/`
- ❌ Adicionar coluna/tabela sem migration Alembic
- ❌ Trocar status de Booking sem passar por `confirm()` / `cancel()`
- ❌ Usar mocks de entidade de domínio (mocar apenas repository/gateway)
- ❌ Adicionar dependência paga sem aprovação
- ❌ Implementar fora de ordem (banco antes de domínio)
- ❌ Traduzir termos do domínio para jargão técnico genérico (Manager, Helper, Processor)

## Ao Adicionar uma Feature

1. Atualizar `docs/documento-software.md` primeiro (requisito → UC → classe → diagrama)
2. Adicionar invariante em §10 (DDD)
3. Adicionar teste na pirâmide TDD correspondente
4. Atualizar `CHANGELOG.md`
5. Atualizar `AGENTS.md` se houver nova convenção

## Stack Canônica

- Python 3.12+ (`dataclass` slots, `match`, `type` aliases)
- FastAPI 0.115+ (Pydantic v2)
- SQLAlchemy 2.0 (async com `asyncpg`)
- Alembic 1.13+
- pytest 8+ com `pytest-asyncio`
- Next.js 15 (App Router)
- TypeScript 5+ (strict + noUncheckedIndexedAccess)
- shadcn/ui + Tailwind 4
- TanStack Query 5
- Zod 3+
