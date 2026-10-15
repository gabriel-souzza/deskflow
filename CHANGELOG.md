# Changelog

Todas as mudanças notáveis neste projeto são documentadas aqui.

### Adicionado
- Implementação estrita da Invariante I6 (Lock Otimista): classe `RepositoryConflictError`, verificação atômica de versão em `AvailabilityWindowRepositoryPostgres.save(expected_version=...)` e tratamento com retorno 409 em `CreateBookingUseCase`
- Endpoints `GET /api/v1/bookings` e `GET /api/v1/bookings/{id}` permitindo ao colaborador consultar suas reservas ativas e históricas com validação de posse
- Endpoints administrativos `GET /api/v1/admin/cost-centers` e `POST /api/v1/admin/cost-centers` para gestão de centros de custo com provisionamento de cota mensal
- Endpoint administrativo `GET /api/v1/admin/accounts` para listagem de contas de colaboradores
- Inclusão dos testes de integração com PostgreSQL real (`src/tests/integration`) no pipeline do GitHub Actions (`ci.yml`)
- Checagem preventiva de conectividade via socket em `test_postgres_booking.py` para skip gracioso quando o serviço de banco não estiver acessível
- Coluna `role` persistida na tabela `employees` com migração Alembic `003_add_employee_role.py`, mapeada na entidade de domínio `Employee` e no schema `AccountCreate`
- Testes automatizados validando atribuição de papel `admin` e rejeição de rotas administrativas para papéis `employee`
- Suíte completa de testes unitários isolados (TDD puro) para todos os 14 Casos de Uso da Clean Architecture em `src/tests/application/`
- Script de inicialização e população de dados (`seed.py`) gerando centros de custo, colaboradores com hash seguro PBKDF2, espaços de trabalho, janelas de 15min e reservas de teste
- Execução de migrações Alembic `001` e `002` no PostgreSQL com resolução automática de host (Docker e PowerShell local)
- Camada de Eventos de Domínio e `EventBus`: classes tipadas de eventos (`BookingCreated`, `BookingConfirmed`, `BookingCancelled`, `BookingExpired`, `QuotaConsumed`, `QuotaAlert`, `WaitlistJoined`, `WaitlistNotified`) e interface `EventBus`
- Implementação ativa dos handlers `AuditLogHandler`, `QuotaAlertHandler` (RF15 - alertas em 80% e 95% via SSE) e `WaitlistHandler` (UC05)
- Endpoint `GET /api/v1/bookings/{id}/qr` para renderização e download direto de imagem PNG do QR Code (UC06 / RF02)
- Caso de uso `GetAvailabilityUseCase` (UC01) e endpoint autenticado `GET /api/v1/availability` com filtros por andar, zona e tipo de espaço
- Caso de uso `ExpireWaitlistUseCase` (UC05) gerenciando expiração de 5 minutos de notificações da fila de espera
- Suporte a corpo JSON em `POST /api/v1/bookings` e `POST /api/v1/bookings/{id}/checkin` com fallback para query params
- Endpoint `/metrics` no formato Prometheus e health check detalhado com banco de dados
- Testes unitários e de integração adicionais elevando a cobertura real para 89.24% sem omissões em `.coveragerc`
- Unit of Work transacional para criação/cancelamento de reservas, com repositories injetados nos casos de uso
- Teste PostgreSQL opt-in com execução Alembic e validação de reserva/cancelamento via `TEST_DATABASE_URL`
- Cadastro administrativo de contas de colaboradores com senha PBKDF2 e login persistido por email
- Endpoints de espaços, disponibilidade, cancelamento, administração, relatórios e SSE com dados persistidos no PostgreSQL
- Check-in QR assinado, controle de cota/capacidade transacional e testes de API com SQLite
- Exportação de relatórios em CSV e PDF
- Backend completo (Clean Architecture + DDD + TDD): 8 entidades, 2 VO, 6 repos ABC, 10 use cases, 4 controllers, 3 repos PostgreSQL, 4 event handlers
- DevOps: Dockerfile multistage (uv), docker-compose.yml (API + PostgreSQL 16), .env.example
- Alembic: env.py + migrations/versions/001_create_initial_schema.py (9 tabelas DER)
- SQLAlchemy 2.0 ORM: infra/models.py (workspaces, bookings, availability_windows, etc.)
- Testes: domain (TimeSlot, QuotaPeriod, Booking, Capacity), application (CreateBookingUseCase), adapter (TestClient), integration (PostgreSQL placeholder)
- README atualizado com uv, Docker Compose, arquitetura
- docs/plano-implementacao-backend.md (plano completo)

### Corrigido
- Autorização RBAC corrigida: removido hardcode de papel em `main.py`; o papel agora é lido diretamente do banco de dados (`employee.role`)
- Correção no `SqlAlchemyUnitOfWork` suportando transações ativas via `begin_nested()` e prevenindo falhas de commit no scheduler
- Script `seed.py` atualizado para ser determinístico e idempotente com UUIDs fixos canônicos
- Reservas agora exigem autenticação e só podem ser canceladas pelo titular ou por admin; JWT expira em 30 minutos por padrão
- Removidos logins e segredos padrão; Compose e migrações exigem configuração explícita de credenciais
- Gate de cobertura corrigido para medir os módulos do backend e exigir 80%
- `Booking.py`: Decimal importado, datetime.utcnow() → timezone.utc, kw_only/default corrigido, replace importado no topo
- `time_slot.py`: slots() tipo Iterator (não Tuple)
- `employee.py`: conflito de nome `is_eligible_for_booking` resolvido
- `availability_window.py`: seats_available duplicado removido
- `main.py`: criado com FastAPI + 4 routers

## [0.1.0] - 2026-10-02

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
