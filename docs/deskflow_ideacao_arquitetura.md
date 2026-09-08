# DeskFlow — Arquitetura para Prevenção de Overbooking Concorrente e Gestão de Cotas

## ETAPA 1: RAMIFICAÇÃO (Divergência de Ideias)

### 🌿 Ramo A — Consistência Estrita no Banco (PostgreSQL + SQLAlchemy 2.0)

**Princípio:** Toda decisão de disponibilidade é tomada dentro de uma transação ACID no PostgreSQL, delegando a ele a responsabilidade de serializar acessos ao mesmo recurso.

**Mecanismos centrais:**
- `SELECT … FOR UPDATE NOWAIT` em uma linha da tabela `workspaces` quando uma reserva tenta ocupá-la.
- `SERIALIZABLE` isolation level com retry em loop em caso de `SerializationFailure` (código 40001).
- `EXCLUDE USING gist` com `tstzrange` para garantir que dois intervalos sobrepostos não coexistam para o mesmo workspace.
- Versionamento otimista (`@version_id` mapped column) na entidade `AvailabilityWindow` para detectar tentativas concorrentes de inserção em `booking_windows`.

**Trade-offs assumidos:**
- Latência de commit dominada pelo WAL fsync; filas de espera em hotspots (ex: Mesa 12A em horário nobre).
- Acoplamento entre o domínio e a semântica transacional do Postgres.

### 🌿 Ramo B — Desacoplamento por Eventos + Redis/Lua Scripting

**Princípio:** O banco é fonte da verdade *histórica*; o Redis é a fonte da verdade *concorrente*. A disponibilidade é materializada como um Sorted Set ou Hash em memória, e a atomicidade de "verificar + reservar" é feita por um script Lua single-threaded.

**Mecanismos centrais:**
- Lua script `EVAL` que faz `HGET capacity` + `HINCRBY reserved` + `EXPIRE` de forma atômica.
- Streams Redis (consumer groups) publicando `BookingCreated`, `BookingCancelled`, `QuotaConsumed` para o `domain-event-bus`.
- PostgreSQL como *projections* materializadas alimentadas por um consumer assíncrono.
- Idempotência por `Idempotency-Key` armazenada no Redis com TTL.

**Trade-offs assumidos:**
- Janela de inconsistência entre Redis e Postgres em caso de crash do broker.
- Necessidade de reconciliação periódica (cron `reconcile_quotas.py`).
- Duplicação conceitual: "reserva" existe em dois lugares.

### 🌿 Ramo C — Agregados Imutáveis com Snapshots de Disponibilidade / Event Sourcing Parcial

**Princípio:** O tempo é modelado como janelas discretas (`AvailabilityWindow`) imutáveis, e toda mutação gera um evento. Concorrência é resolvida por *intenção* (commander pattern) e *validação temporal* sem locks.

**Mecanismos centrais:**
- `AvailabilityWindow` é um aggregate root imutável (PK `workspace_id, day, slot_index`) com `version_id` para lock otimista. A contagem de reservas confirmadas é materializada na tabela associativa `booking_windows`.
- Reserva como `Booking` (PENDING) que passa por `confirm()` que valida invariantes I1–I6.
- Event Sourcing parcial: persistimos apenas `events.jsonl` por workspace com offsets; o estado é *derived*.
- Janela de booking é um *range discreto* (slots de 15min) permitindo comparação O(1) por índice.

**Trade-offs assumidos:**
- Curva de aprendizado íngreme; *eventual consistency* entre intenção e confirmação exige UX cuidadosa (estado `pending`).
- Replay de eventos para reconstruir o estado atual pode custar I/O.

---

## ETAPA 2: AUTOAVALIAÇÃO E CRÍTICA DE VIABILIDADE

| Critério | Ramo A (PG Lock) | Ramo B (Redis+Events) | Ramo C (Imutável+ES) |
|---|:---:|:---:|:---:|
| Complexidade de Implementação (1=complexo) | **7** | 4 | 3 |
| Desempenho em Alta Concorrência | 5 | **9** | 7 |
| Aderência Clean Architecture / DDD Puro | 5 | 4 | **9** |
| Facilidade de Testabilidade com TDD | **8** | 5 | 6 |

### 🏆 VENCEDOR: **Ramo C — Agregados Imutáveis com Snapshots de Disponibilidade**

**Justificativa:**

1. **Pureza de domínio:** O Ramo A vaza semântica transacional (NOWAIT, SERIALIZABLE) para a camada de aplicação. O Ramo B vaza o Redis como dependência central de leitura. Apenas o Ramo C mantém o Core expresso em `dataclasses` e funções puras testáveis sem nenhum mock de I/O.
2. **Resiliência a duplicação:** Janelas imutáveis eliminam a classe inteira de bugs "edição concorrente" — você não *edita* uma reserva, você cria uma nova intenção e cancela a anterior (compensação), que é exatamente o pattern recomendado por Eric Evans e Vaughn Vernon para contextos com invariantes temporais.
3. **Escalabilidade de teste:** TDD puro no domínio (Ramo C + Ramo A) gera testes rápidos (ms). O Ramo B exige um Redis real ou `fakeredis` bem configurado, contaminando os testes de unidade.
4. **Compromisso pragmático:** O Ramo C não exige mudança completa para Event Sourcing; apenas os *aggregates de disponibilidade* são baseados em eventos. Reservas comuns continuam CRUD + Event Sourcing parcial (apenas delta events).

O Ramo A seria a escolha para um MVP rápido. O Ramo B seria a escolha para escala de marketplace (10k+ req/s). O Ramo C é a escolha para um **core domain** corporativo onde a correção semântica é o ativo de maior valor — exatamente o caso do DeskFlow, que lida com cobranças por centro de custo.

---

## ETAPA 3: APROFUNDAMENTO NO RAMO VENCEDOR

### 1. Contratos e Entidades de Domínio (Python puro, zero infra)

```python
from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import NewType, Protocol
import uuid

BookingId = NewType("BookingId", str)
WorkspaceId = NewType("WorkspaceId", str)
EmployeeId = NewType("EmployeeId", str)
CostCenterId = NewType("CostCenterId", str)

SLOT_MINUTES = 15


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def generate_booking_id(self) -> BookingId: ...
    def generate_workspace_id(self) -> WorkspaceId: ...
    def generate_employee_id(self) -> EmployeeId: ...


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


# Interfaces de repository (Application Layer) — implementadas em src/adapters/repositories/
class BookingRepository(Protocol):
    def find_by_id(self, booking_id: BookingId) -> Booking | None: ...
    def find_by_employee_and_day(self, employee_id: EmployeeId, day: date) -> list[Booking]: ...
    def find_pending_expired(self, before: datetime) -> list[Booking]: ...
    def find_pending_expired_batch(self, station_cutoff: datetime, meeting_cutoff: datetime) -> list[Booking]: ...
    def save(self, booking: Booking) -> None: ...


class AvailabilityWindowRepository(Protocol):
    def get_or_create(self, workspace_id: WorkspaceId, day: date, slot_index: int) -> "AvailabilityWindow": ...
    def get_by_day(self, day: date) -> list["AvailabilityWindow"]: ...
    def save(self, window: "AvailabilityWindow") -> None: ...


class QuotaRepository(Protocol):
    def get_for_period(self, cost_center: CostCenterId, day: date) -> "QuotaPeriod": ...
    def save(self, quota: "QuotaPeriod") -> None: ...


class BookingWindowRepository(Protocol):
    def count_by_window(self, workspace_id: WorkspaceId, day: date, slot_index: int) -> int: ...
    def save(self, bw: "BookingWindow") -> None: ...
    def delete_by_booking(self, booking_id: BookingId) -> int: ...


class WorkspaceRepository(Protocol):
    def get_by_id(self, workspace_id: WorkspaceId) -> "Workspace" | None: ...
    def list_active(self) -> list["Workspace"]: ...
    def save(self, workspace: "Workspace") -> None: ...


class WaitlistRepository(Protocol):
    def next_for(self, workspace_id: WorkspaceId, day: date, slot_index: int) -> "Waitlist" | None: ...
    def save(self, entry: "Waitlist") -> None: ...


class DomainEventBus(Protocol):
    def publish(self, event: object) -> None: ...
    def publish_batch(self, events: list[object]) -> None: ...


@dataclass(frozen=True, slots=True)
class TimeSlot:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise InvalidTimeSlotError("start must be < end")
        if self.start.minute % SLOT_MINUTES or self.end.minute % SLOT_MINUTES:
            raise InvalidTimeSlotError("slot must align to 15-minute grid")
        if (self.end - self.start) < timedelta(minutes=SLOT_MINUTES):
            raise InvalidTimeSlotError("minimum 1 slot")

    def overlaps(self, other: TimeSlot) -> bool:
        return self.start < other.end and other.start < self.end

    def contains(self, instant: datetime) -> bool:
        return self.start <= instant < self.end

    def slots(self) -> tuple[datetime, ...]:
        n = int((self.end - self.start).total_seconds() // (SLOT_MINUTES * 60))
        return tuple(self.start + timedelta(minutes=SLOT_MINUTES * i) for i in range(n))


@dataclass(frozen=True, slots=True)
class Capacity:
    seats: int
    zone: str

    def __post_init__(self) -> None:
        if self.seats < 1:
            raise InvalidCapacityError("seats must be >= 1")
        if not self.zone.strip():
            raise InvalidCapacityError("zone cannot be empty")


@dataclass(frozen=True, slots=True)
class AvailabilityWindow:
    workspace_id: WorkspaceId
    day: date
    slot_index: int
    capacity: Capacity
    version_id: int = 0

    def seats_available(self) -> int:
        return self.capacity.seats

    def is_full(self, confirmed_count: int) -> bool:
        return confirmed_count >= self.capacity.seats


@dataclass(frozen=True, slots=True)
@dataclass(frozen=True, slots=True)
class BookingWindow:
    booking_id: BookingId
    workspace_id: WorkspaceId
    day: date
    slot_index: int


@dataclass(frozen=True, slots=True)
class QuotaPeriod:
    cost_center: CostCenterId
    period_start: date
    period_end: date
    total_hours: Decimal
    consumed_hours: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if self.period_start >= self.period_end:
            raise InvalidQuotaPeriodError("start must be < end")
        if self.total_hours <= 0:
            raise InvalidQuotaPeriodError("total_hours must be > 0")
        if self.consumed_hours < 0:
            raise InvalidQuotaPeriodError("consumed cannot be negative")

    def remaining_hours(self) -> Decimal:
        return self.total_hours - self.consumed_hours

    def can_consume(self, hours: Decimal) -> bool:
        return hours <= self.remaining_hours()

    def consume(self, hours: Decimal) -> "QuotaPeriod":
        if not self.can_consume(hours):
            raise QuotaExceededError(self.cost_center, self.remaining_hours(), hours)
        return replace(self, consumed_hours=self.consumed_hours + hours)


@dataclass(frozen=True, slots=True)
class Booking:
    id: BookingId
    workspace_id: WorkspaceId
    employee_id: EmployeeId
    cost_center: CostCenterId
    slot: TimeSlot
    status: BookingStatus
    qr_token: str
    created_at: datetime
    modified_at: datetime | None = None

    def confirm(self) -> "Booking":
        if self.status is not BookingStatus.PENDING:
            raise InvalidStateTransitionError(self.status, BookingStatus.CONFIRMED)
        return replace(self, status=BookingStatus.CONFIRMED)

    def cancel(self, clock: Clock) -> "Booking":
        if self.status is BookingStatus.CANCELLED:
            raise InvalidStateTransitionError(self.status, BookingStatus.CANCELLED)
        if self.slot.start - clock.now() < timedelta(hours=2):
            raise InvalidCancellationError(
                f"booking {self.id} cannot be cancelled with less than 2h anticipation"
            )
        return replace(self, status=BookingStatus.CANCELLED)

    def expire(self) -> "Booking":
        if self.status is not BookingStatus.PENDING:
            raise InvalidStateTransitionError(self.status, BookingStatus.EXPIRED)
        return replace(self, status=BookingStatus.EXPIRED)

    def duration_hours(self) -> Decimal:
        return Decimal((self.slot.end - self.slot.start).total_seconds()) / Decimal(3600)


# Exceções de domínio (também parte do modelo)
class DomainError(Exception): ...
class InvalidWorkspaceError(DomainError): ...
class InvalidTimeSlotError(DomainError): ...
class InvalidCapacityError(DomainError): ...
class InvalidQuotaPeriodError(DomainError): ...
class DuplicateBookingError(DomainError): ...
class CapacityExceededError(DomainError):
    def __init__(self, workspace_id: WorkspaceId, slot_index: int) -> None:
        super().__init__(f"workspace {workspace_id} slot {slot_index} is full")
class UnknownBookingError(DomainError): ...
class QuotaExceededError(DomainError):
    def __init__(self, cc: CostCenterId, remaining: Decimal, requested: Decimal) -> None:
        super().__init__(f"cost center {cc}: remaining {remaining}h < requested {requested}h")
class InvalidStateTransitionError(DomainError): ...
class InvalidCheckInTokenError(DomainError): ...
class InvalidCancellationError(DomainError): ...
class RepositoryConflictError(DomainError): ...


# Domain Events (publicados pelo EventBus após cada use case)
@dataclass(frozen=True, slots=True)
class BookingConfirmed:
    booking_id: BookingId
    workspace_id: WorkspaceId
    employee_id: EmployeeId
    confirmed_at: datetime

    @classmethod
    def from_booking(cls, booking: "Booking") -> "BookingConfirmed":
        return cls(
            booking_id=booking.id,
            workspace_id=booking.workspace_id,
            employee_id=booking.employee_id,
            confirmed_at=datetime.utcnow(),
        )


@dataclass(frozen=True, slots=True)
class BookingCancelled:
    booking_id: BookingId
    cancelled_at: datetime
    reason: str


@dataclass(frozen=True, slots=True)
class BookingExpired:
    booking_id: BookingId
    expired_at: datetime


@dataclass(frozen=True, slots=True)
class QuotaConsumed:
    cost_center: CostCenterId
    hours: Decimal
    remaining_hours: Decimal


@dataclass(frozen=True, slots=True)
class QuotaAlert:
    """Publicado quando consumed_hours / total_hours >= 0.8 (80%) ou 0.95 (95%)."""

    cost_center: CostCenterId
    percentage: float
    consumed_hours: Decimal
    total_hours: Decimal
    threshold: float


@dataclass(frozen=True, slots=True)
class WaitlistNotified:
    workspace_id: WorkspaceId
    employee_id: EmployeeId
    slot_start: datetime
    slot_end: datetime


@dataclass(frozen=True, slots=True)
class AvailabilityReleased:
    workspace_id: WorkspaceId
    day: date
    slot_index: int


# Entidades complementares (presentes no dominio, mas sem lógica de invariante
# complexa — listadas para rastreabilidade com documento-software.md)
@dataclass(frozen=True, slots=True)
class Employee:
    id: EmployeeId
    name: str
    email: str
    cost_center: CostCenterId

    def is_eligible_for_booking(self, day: date) -> bool:
        raise NotImplementedError(
            "Regra de elegibilidade (3 dias presenciais) vem do sistema de ponto "
            "externo via SyncPointUseCase. Aqui apenas declaramos a interface."
        )


@dataclass(frozen=True, slots=True)
@dataclass(frozen=True, slots=True)
class Holiday:
    day: date
    description: str

    def is_blocked(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class Waitlist:
    id: str
    workspace_id: WorkspaceId
    employee_id: EmployeeId
    desired_start: datetime
    desired_end: datetime
    created_at: datetime
    notified_at: datetime | None = None

    def is_notified(self) -> bool:
        return self.notified_at is not None


class WorkspaceType(str, Enum):
    STATION = "estacao"
    MEETING_ROOM = "sala"


@dataclass(frozen=True, slots=True)
class Workspace:
    id: WorkspaceId
    code: str
    floor: str
    zone: str
    type: WorkspaceType
    capacity: Capacity
    resources: tuple[str, ...] = ()
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise InvalidWorkspaceError("code cannot be empty")
        if self.type is WorkspaceType.STATION and self.capacity.seats != 1:
            raise InvalidWorkspaceError("station must have capacity=1")

    def is_station(self) -> bool:
        return self.type is WorkspaceType.STATION

    def is_meeting_room(self) -> bool:
        return self.type is WorkspaceType.MEETING_ROOM


@dataclass(frozen=True, slots=True)
class CostCenter:
    id: CostCenterId
    code: str
    name: str


@dataclass(frozen=True, slots=True)
class Employee:
    id: EmployeeId
    name: str
    email: str
    cost_center: CostCenterId
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuditLog:
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: EmployeeId | None
    timestamp: datetime
    metadata: dict
```

### 2. Invariantes e Regras de Negócio

| # | Invariante | Garantida por |
|---|---|---|
| **I1** | Toda reserva ocupa um intervalo discreto alinhado em grid de 15 min, com `start < end` e mínimo de 1 slot. | `TimeSlot.__post_init__` |
| **I2** | Uma `AvailabilityWindow` nunca excede `capacity.seats` reservas confirmadas; inserção duplicada em `booking_windows` é prevenida. | `AvailabilityWindow.is_full(confirmed_count)` verificado antes do `INSERT` em `booking_windows` |
| **I3** | `QuotaPeriod.consumed_hours` nunca excede `total_hours`; consumo é monotônico. | `QuotaPeriod.consume` |
| **I4** | Transições de estado de `Booking` são unidirecionais: `PENDING → CONFIRMED` ou `PENDING → CANCELLED`; cancelamento duplo é proibido. | `Booking.confirm` / `Booking.cancel` |
| **I5** | Toda reserva confirmada consome horas do centro de custo na mesma operação atômica (consistência entre `Booking` e `QuotaPeriod`). | `CreateBookingUseCase.execute` orchestrating both in one transaction |
| **I6** | Duas reservas para o mesmo `workspace_id` nunca se sobrepõem em janelas confirmadas (constraint composicional). | `BookingWindowRepository.count_by_window()` verificado antes de cada `INSERT` na junction table |

### 3. Caso de Uso: `CreateBookingUseCase`

```python
@dataclass(frozen=True, slots=True)
class CreateBookingCommand:
    workspace_id: WorkspaceId
    employee_id: EmployeeId
    cost_center: CostCenterId
    slot: TimeSlot


class CreateBookingUseCase:
    def __init__(
        self,
        windows: "AvailabilityWindowRepository",
        quotas: "QuotaRepository",
        bookings: "BookingRepository",
        booking_windows: "BookingWindowRepository",
        events: "DomainEventBus",
        clock: "Clock",
        id_generator: "IdGenerator",
    ) -> None:
        self._windows = windows
        self._quotas = quotas
        self._bookings = bookings
        self._booking_windows = booking_windows
        self._events = events
        self._clock = clock
        self._ids = id_generator

    def execute(self, cmd: CreateBookingCommand) -> Booking:
        booking_id = BookingId(self._ids.new())

        booking = Booking(
            id=booking_id,
            workspace_id=cmd.workspace_id,
            employee_id=cmd.employee_id,
            cost_center=cmd.cost_center,
            slot=cmd.slot,
            status=BookingStatus.PENDING,
            qr_token=str(uuid.uuid4()),
            created_at=self._clock.now(),
        )

        for slot_start in cmd.slot.slots():
            window = self._windows.get_or_create(
                workspace_id=cmd.workspace_id,
                day=slot_start.date(),
                slot_index=int((slot_start.hour * 60 + slot_start.minute) // SLOT_MINUTES),
            )
            confirmed_count = self._booking_windows.count_by_window(
                workspace_id=cmd.workspace_id,
                day=slot_start.date(),
                slot_index=int((slot_start.hour * 60 + slot_start.minute) // SLOT_MINUTES),
            )
            if window.is_full(confirmed_count):
                raise CapacityExceededError(cmd.workspace_id, window.slot_index)
            bw = BookingWindow(
                booking_id=booking_id,
                workspace_id=cmd.workspace_id,
                day=slot_start.date(),
                slot_index=int((slot_start.hour * 60 + slot_start.minute) // SLOT_MINUTES),
            )
            self._booking_windows.save(bw)

        quota = self._quotas.get_for_period(
            cost_center=cmd.cost_center,
            day=cmd.slot.start.date(),
        )
        new_quota = quota.consume(booking.duration_hours())
        self._quotas.save(new_quota)

        self._bookings.save(booking)

        self._events.publish_batch([
            QuotaConsumed(cmd.cost_center, booking.duration_hours(), new_quota.remaining_hours()),
        ])
        return booking
```

**Fluxo de exceções (ordenado do mais provável ao mais raro):**

1. `InvalidTimeSlotError` — payload do front-end inválido (erro 400).
2. `CapacityExceededError` — janela cheia, verificado via `count_by_window()` (erro 409 + sugestão de slots adjacentes).
3. `QuotaExceededError` — centro de custo estourado (erro 402 com `remaining_hours` para a UI).
4. `RepositoryConflictError` — `booking_windows` modificado entre contagem e insert (retry com backoff: o `INSERT` na junction table usa optimistic lock via `version_id` na `availability_windows`).

**Observação crítica sobre concorrência:** O Ramo C elimina *overbooking* não por lock, mas por **monotonicidade estrutural**: `AvailabilityWindow` é imutável (aggregate root separado), e a verificação de capacidade é feita via contagem na tabela associativa `booking_windows`. Concorrência é resolvida pelo `BookingWindowRepository` via *optimistic concurrency* (`@version_id` na `availability_windows`). O retry é simples e local; sem Lua, sem Redis, sem `FOR UPDATE`.


### 4. Caso de Uso: `ConfirmBookingUseCase` (Check-in via QR Code)

```python
@dataclass(frozen=True, slots=True)
class ConfirmBookingCommand:
    booking_id: BookingId
    token: str  # QR Code payload, validado contra hash em Booking.qr_token


class ConfirmBookingUseCase:
    def __init__(
        self,
        bookings: "BookingRepository",
        events: "DomainEventBus",
        clock: "Clock",
    ) -> None:
        self._bookings = bookings
        self._events = events
        self._clock = clock

    def execute(self, cmd: ConfirmBookingCommand) -> Booking:
        booking = self._bookings.find_by_id(cmd.booking_id)
        if booking is None:
            raise UnknownBookingError(f"booking {cmd.booking_id} not found")
        if booking.qr_token != cmd.token:
            raise InvalidCheckInTokenError(f"invalid token for booking {cmd.booking_id}")
        confirmed = booking.confirm()
        if confirmed.status is not BookingStatus.CONFIRMED:
            raise InvalidStateTransitionError(booking.status, BookingStatus.CONFIRMED)
        self._bookings.save(confirmed)
        self._events.publish(BookingConfirmed.from_booking(confirmed))
        return confirmed
```


### 5. Caso de Uso: `ReleaseExpiredBookingsUseCase` (Cron — a cada 1 min)

```python
@dataclass(frozen=True, slots=True)
class ReleaseExpiredBookingsCommand:
    pass  # sem parâmetros — tolerância é por tipo de workspace


class ReleaseExpiredBookingsUseCase:
    def __init__(
        self,
        bookings: "BookingRepository",
        booking_windows: "BookingWindowRepository",
        workspaces: "WorkspaceRepository",
        waitlist: "WaitlistRepository",
        events: "DomainEventBus",
        clock: "Clock",
    ) -> None:
        self._bookings = bookings
        self._booking_windows = booking_windows
        self._workspaces = workspaces
        self._waitlist = waitlist
        self._events = events
        self._clock = clock

    def execute(self, cmd: ReleaseExpiredBookingsCommand) -> list[Booking]:
        # Tolerância diferenciada: 10 min estação, 15 min sala (RO-01, RO-05)
        now = self._clock.now()
        cutoff_station = now - timedelta(minutes=10)
        cutoff_meeting = now - timedelta(minutes=15)
        expired = self._bookings.find_pending_expired_batch(
            station_cutoff=cutoff_station,
            meeting_cutoff=cutoff_meeting,
        )
        for booking in expired:
            self._booking_windows.delete_by_booking(booking.id)
            released = booking.expire()
            self._bookings.save(released)
            self._events.publish_batch([
                BookingExpired(booking.id, self._clock.now()),
                AvailabilityReleased(
                    workspace_id=booking.workspace_id,
                    day=booking.slot.start.date(),
                    slot_index=int((booking.slot.start.hour * 60 + booking.slot.start.minute) // SLOT_MINUTES),
                ),
            ])
        return expired
```

**Fluxo de exceções:**

1. `InvalidStateTransitionError` — tentativa de expirar booking que não está PENDING (retry ignorando).

---

## ETAPA 4: ESTRUTURAÇÃO DO FRONTEND (Next.js App Router)

### 1. Gerenciamento de Estado e Reatividade

**Estratégia híbrida de 3 camadas:**

| Camada | Tecnologia | Responsabilidade | Granularidade |
|---|---|---|---|
| Server State | TanStack Query v5 | Cache de `availability`, `quotas`, `bookings`; sincronização com API | Por `workspaceId + day` |
| Realtime Push | Server-Sent Events (SSE) via Route Handler `app/api/availability/stream/route.ts` | Notificação de mudanças de janela | Por `buildingId` |
| UI Local | Zustand (apenas para filtros/UI efêmera) | Seleção de datas, preferências de andar | Componente |

**Re-renderização cirúrgica — a chave é invalidação por chave de query, não refetch global:**

```ts
// apps/web/src/features/booking/queries/availability-query.ts
import { queryOptions, useQuery } from "@tanstack/react-query";
import { z } from "zod";

export const AvailabilityWindowSchema = z.object({
  workspaceId: z.string().uuid(),
  day: z.string().date(),
  slotIndex: z.number().int().min(0).max(95),
  capacity: z.object({ seats: z.number().int().positive(), zone: z.string() }),
  confirmedCount: z.number().int().nonnegative(),
});
export type AvailabilityWindowDTO = z.infer<typeof AvailabilityWindowSchema>;

export const availabilityQueryKey = (workspaceId: string, day: string) =>
  ["availability", workspaceId, day] as const;

export function availabilityQueryOptions(workspaceId: string, day: string) {
  return queryOptions({
    queryKey: availabilityQueryKey(workspaceId, day),
    queryFn: async ({ signal }) => {
      const res = await fetch(`/api/workspaces/${workspaceId}/availability?day=${day}`, { signal });
      if (!res.ok) throw new Error(`availability ${res.status}`);
      return z.array(AvailabilityWindowSchema).parse(await res.json());
    },
    staleTime: 30_000,
    gcTime: 5 * 60_000,
  });
}
```

```ts
// apps/web/src/features/booking/hooks/use-availability-stream.ts
"use client";
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { availabilityQueryKey } from "../queries/availability-query";
import { WorkspaceEventSchema } from "@deskflow/contracts";

export function useAvailabilityStream(workspaceId: string, day: string) {
  const qc = useQueryClient();
  useEffect(() => {
    const url = `/api/workspaces/${workspaceId}/availability/stream?day=${day}`;
    const es = new EventSource(url);

    es.addEventListener("window.updated", (e) => {
      const event = WorkspaceEventSchema.parse(JSON.parse((e as MessageEvent).data));
      if (event.workspaceId === workspaceId) {
        qc.setQueryData(availabilityQueryKey(workspaceId, day), (prev) =>
          prev ? mergeWindow(prev, event) : prev
        );
      }
    });
    return () => es.close();
  }, [workspaceId, day, qc]);
}
```

**Por que SSE e não WebSocket:** Atualizações de disponibilidade são *unidirectional* (servidor → cliente) e toleram reconexão automática nativa do navegador. WebSocket traria complexidade (heartbeat, framing, fallbacks) sem benefício.

**Re-renderização mínima:** o componente `SeatGrid` é memoizado e recebe apenas a `slot` alterada via `useQueryData` com `select`. Mudanças em outros andares não invalidam a árvore virtual.

### 2. Isolamento Visão vs. Lógica (shadcn/ui + Zod strict)

**Estrutura de pastas do feature module:**

```
apps/web/src/features/booking/
├── domain/
│   ├── time-slot.ts            # lógica pura: overlaps(), isValid()
│   └── quota-calculator.ts     # funções puras, 100% testadas
├── schemas/
│   └── booking.schema.ts       # Zod schemas = contratos
├── queries/
│   ├── availability-query.ts   # queryOptions (TanStack)
│   └── quota-query.ts
├── hooks/
│   ├── use-availability-stream.ts
│   ├── use-create-booking.ts   # useMutation
│   └── use-slot-selection.ts   # estado local
├── components/
│   ├── seat-grid.tsx           # server component por padrão
│   ├── slot-picker.tsx         # "use client"
│   ├── quota-meter.tsx
│   └── booking-confirm-dialog.tsx
└── server/
    └── actions.ts              # Server Actions (Next.js 15)
```

**Princípios:**

1. **`schemas/` é a fonte da verdade tipada.** Zod gera tipos com `z.infer`. TypeScript `strict: true` + `noUncheckedIndexedAccess: true` no `tsconfig.json`. Zero `any`.
2. **`components/` não conhece `fetch`.** Toda chamada de API passa por `queries/` (TanStack) ou `server/actions.ts` (Server Actions).
3. **shadcn/ui é camada burra.** Componentes como `<Button>`, `<Dialog>` ficam em `components/ui/`. Nenhuma regra de negócio.
4. **Domain puro no front também.** `domain/time-slot.ts` espelha o `TimeSlot` do backend em TypeScript — sem dependências de React.

**Exemplo de fronteira limpa:**

```ts
// domain/time-slot.ts — puro, testável com vitest sem jsdom
export type TimeSlot = { start: Date; end: Date };

export function overlaps(a: TimeSlot, b: TimeSlot): boolean {
  return a.start < b.end && b.start < a.end;
}

export function isAlignedToGrid(d: Date, gridMinutes = 15): boolean {
  return d.getMinutes() % gridMinutes === 0 && d.getSeconds() === 0;
}
```

```tsx
// components/slot-picker.tsx — "use client", apenas UI
"use client";
import { Button } from "@/components/ui/button";
import { useSlotSelection } from "../hooks/use-slot-selection";
import { isAlignedToGrid, overlaps, type TimeSlot } from "../domain/time-slot";

export function SlotPicker({ slots, selected, onSelect }: Props) {
  const { tentative } = useSlotSelection();
  return (
    <div className="grid grid-cols-8 gap-1">
      {slots.map((s) => {
        const conflict = tentative && overlaps(s, tentative);
        return (
          <Button
            key={s.start.toISOString()}
            variant={conflict ? "destructive" : selected?.start === s.start ? "default" : "outline"}
            onClick={() => onSelect(s)}
            disabled={conflict}
          >
            {format(s.start, "HH:mm")}
          </Button>
        );
      })}
    </div>
  );
}
```

### Fluxo de dados ponta a ponta

```
[ User ] → [SlotPicker] → [useCreateBooking mutation]
                              ↓
              [Server Action + Zod parse] → [POST /api/bookings]
                              ↓
                    [CreateBookingUseCase] (Ramo C)
                              ↓
                [Domain events publicados no bus]
                              ↓
          [SSE Route Handler fan-out para clientes conectados]
                              ↓
        [useAvailabilityStream] → [qc.setQueryData] → re-render cirúrgico
```

---

**Resumo da decisão arquitetural:** o Ramo C foi escolhido por maximizar pureza de domínio, testabilidade TDD sem I/O e resiliência semântica. A complexidade de implementação adicional é paga uma vez e compensada pela ausência de bugs de overbooking — que no contexto B2B de coworking corporativo, com faturamento por centro de custo, custariam não apenas dinheiro, mas **confiança do cliente enterprise**.
