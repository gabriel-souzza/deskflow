# Changelog

Todas as mudanças notáveis neste projeto são documentadas aqui.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Em Andamento
- Sprint 1 — Fundação do Domínio (TDD red→green→refactor para TimeSlot, AvailabilityWindow, QuotaPeriod, Booking)
- Sprint 2 — Motor de Agendamento (CreateBookingUseCase, ConfirmBookingUseCase, CancelBookingUseCase, ReleaseExpiredBookingsUseCase)
- Sprint 3 — Frontend Next.js + Relatórios (GenerateReportUseCase, SSE publisher)

### Documentação
- Documento de Software (Análise e Projeto) consolidado com 18 seções
- Diagrama de classes, DER, diagramas de sequência, atividades e componentes
- Mapeamento DDD com 7 aggregates, 6 invariants, 12 use cases
- Matriz de rastreabilidade §11.3 com todos os 18 UCs
- Descrições textuais de UC01, UC05, UC14, UC15, UC16, UC17, UC18
- Correção: Booking.modified_at adicionado para suportar RF12
- Correção: RF04, RF15 reescritos para refletir modelo N-N e event handlers
- Correção: UC02 reescrito sem BookingIntent (não persistido)
- Correção: typo "写入" (caracteres chineses) removido
- Correção: 12 domain events documentados com publicadores e consumidores
- Correção: Employee, Holiday, Waitlist adicionados ao código de domínio em deskflow_ideacao_arquitetura.md
- Correção: sequence diagram §7.2 e atividade §8.2 reescritos para refletir N-N (DELETE em booking_windows + QuotaPeriod.consume(-h))
- Correção: escopo-arquitetura-deskflow.md linha 57 (QuotaPeriod.without_consumption) removido — usar consume(-h)
- Correção: tolerância diferenciada (10 min estação / 15 min sala) documentada em UC15 e README
- Correção: `is_full()` com assinatura correta (confirmed_count: int) no diagrama de classes
- Correção: "BookingIntent" removido da descrição do Ramo C (obsoleto)
- Correção: "três invariantes" corrigido para "seis invariantes" no escopo
- Correção: referências a `with_booking`, `BookingIntent`, `confirmed_booking_ids: frozenset` removidas (modelo N-N via BookingWindow)
- Correção: `Booking.cancel()` agora valida regra de 2h de antecedência com `Clock`
- Correção: `InvalidCancellationError` e `RepositoryConflictError` adicionadas às exceções de domínio
- Correção: `Clock`, `IdGenerator`, `RepositoryConflictError` adicionados ao código de domínio
- Adição: `Workspace` (com `WorkspaceType` STATION/MEETING_ROOM) e `CostCenter` agregados adicionados ao código de domínio
- Adição: `InvalidWorkspaceError` adicionada às exceções de domínio
- Correção: `IntentId` e `BookingIntent` removidos (modelo antigo de duas etapas — reserva agora é uma etapa via CreateBookingUseCase)
- Correção: `CreateBookingUseCase` agora deixa Booking em PENDING (não chama `confirm()`) — check-in via QR é o que confirma, alinhado com UC06 e RO-01
- Adição: `ConfirmBookingUseCase` adicionado ao código de domínio com validação de token
- Adição: `qr_token` adicionado à entidade `Booking`
- Adição: `InvalidCheckInTokenError` adicionada às exceções de domínio
- Adição: interfaces de repository e `DomainEventBus` adicionadas como Protocols
- Adição: `BookingWindow` marcado como `@dataclass(frozen=True, slots=True)`
- Adição: `Holiday` marcado como `@dataclass(frozen=True, slots=True)`
- Adição: `Booking.expire()` adicionado para suportar UC15
- Adição: `Booking.modified_at` adicionado para suportar RF12
- Adição: `ReleaseExpiredBookingsUseCase` adicionado ao código de domínio com tolerância diferenciada (10 min estação / 15 min sala)
- Adição: `BookingRepository.find_pending_expired_batch` para tolerância por tipo de workspace
- Correção: diagrama de atividades §8 (UC02) atualizado — PENDING sem confirmação automática, passo de salvar BookingWindows adicionado
- Correção: diagrama de sequência §7 (UC02) atualizado — PENDING + qr_token, BookingConfirmed removido, BookingWindows no loop

## [0.0.1] — 2026-09-04

### Adicionado
- Proposta comercial DeskFlow (R$ 25.000 setup + R$ 8.500/mês licença)
- Diagnóstico operacional (P1–P6)
- Escopo funcional e arquitetura técnica
- Ideação arquitetural — decisão pelo Ramo C (Agregados Imutáveis com N-N via BookingWindow)
- Documento de software completo
- README.md do projeto
