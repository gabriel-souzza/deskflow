# ESCOPO FUNCIONAL E ARQUITETURA TÉCNICA — DeskFlow
---

## 1. Escopo Funcional Dividido por Módulos

### 1.1 Gestão de Espaços
- **Cadastro de Estaçōes**: código único, andar, zona (ex: aberto, cabine), capacidade (1 assento), recursos (monitor, tomada).
- **Cadastro de Salas de Reunião**: código, capacidade, recursos (projetor, videoconferência), zona.
- **Definição de Zonas / Bounded Contexts**: agrupamento lógico por departamento ou andar para aplicação de cotas.
- **Calendário de Disponibilidade**: geração de slots de 15 min (08:00–18:00) por dia útil; bloqueio de feriados e ponto facultativo.
- **API de Consulta**: listagem de estações/salas livres por intervalo, com opções de filtro por zona/resources.

### 1.2 Motor de Agendamento (Core)
- **Reserva de Estação/Sala**: criação de intent (pending) → validação de conflitos (TimeSlot.overlaps) → confirmação após check-in.
- **Check‑in via QR Code**: geração de token temporário (validade 10 min); leitura via app móvel confirma presença e move intent de *pending* para *confirmed*.
- **Liberação Automática**: se não houver check‑in dentro da tolerância, a reserva é cancelada e a vaga volta ao pool (fila de espera é notificada).
- **Fila de Espera (Waitlist)**: ordem FIFO por timestamp de criação da intent; notificação push (SSE ou WebSocket) quando vaga surge.
- **Cancelamento com Antecedência de 2h**: permite reutilização imediata da estação; após esse prazo, a vaga é considerada “no‑show tardia” e não gera fila automática.
- **Cotas por Setor (Centro de Custo)**: cada departamento possui limite de horas‑estação/mês; a reserva consome quota; tentativa de ultrapassar lança exceção de domínio.
- **Integração de Ponto**: validação de que o colaborador está em dia presencial permitido (conforme política 3 dias) antes de permitir reserva para aquele dia.

### 1.3 Relatórios e Compliance
- **Dashboard de Utilização**: por dia, andar, zona, departamento; métricas de ocupação média, pico, ociosidade, taxa de no‑show.
- **Relatório de Custo por Centro de Custo**: consumo de horas‑estação × custo por estação (R$ 1.200) → rateio automático.
- **Auditoria de Alterações**: log de quem criou, modificou ou cancelou reserva; timestamp e motivo.
- **Exportação**: CSV/PDF para fins de prestação de contas e ajuste de política híbrida.
- **Alertas de Limite de Cota**: notificação via e‑mail ou Slack quando departamento atinge 80%/95% do limite mensal.

---

## 2. Arquitetura da Solução

| Camada | Backend (FastAPI) | Frontend (Next.js) |
|---|---|---|
| **Presentation Layer** | - Rotas REST (`/api/v1/bookings`, `/api/v1/spaces`) <br>- Dependency Injection de use cases <br>- Tratamento de exceções de domínio → HTTP 4xx/422 | - Pages (`app/(bookings)/page.tsx`, `app/(admin)/...`) <br>- Componentes shadcn/ui (Button, Dialog, Table, Toast) <br>- Hooks custom (`useCreateBooking`, `useAvailability`) |
| **Application Layer** | - Casos de uso: `CreateBookingUseCase`, `ConfirmBookingUseCase`, `CancelBookingUseCase`, `ReleaseExpiredBookingsUseCase`, `NotifyWaitlistUseCase` (consumo de quota é interno, dentro de `CreateBookingUseCase` e `CancelBookingUseCase`, não é um use case próprio) <br>- Orquestram repositórios e publicam eventos de domínio | - TanStack Query (`useQuery`, `useMutation`) para carregar e mutar dados <br>- Server‑Sent Events (`useEffect` + `EventSource`) para receber atualizações de disponibilidade em tempo real <br>- Zustand (opcional) para estado UI local (filtros, modal abertos) |
| **Domain Layer** | - Entidades/Value Objects: `Booking`, `TimeSlot`, `Capacity`, `AvailabilityWindow` (aggregate root com `version_id` otimista), `QuotaPeriod`, `Workspace`, `Employee`, `Waitlist`, `Holiday`, `AuditLog` (arquivo puro `dataclasses` frozen) <br>- Regras de negócio: `TimeSlot.overlaps()`, `AvailabilityWindow.is_full()`, `QuotaPeriod.consume()` <br>- Tabela associativa `BookingWindow` materializa a relação N-N entre Booking e AvailabilityWindow <br>- Exceções de domínio (`CapacityExceededError`, `QuotaExceededError`, `InvalidTimeSlotError`) | - Tipos TypeScript gerados a partir de Zod schemas (mesmas regras de validação) <br>- Funções puras (`isAlignedToGrid`, `overlaps`) reutilizadas em validação de formulário <br>- Nenhuma lógica de negócio que dependa de React ou Next.js |
| **Infrastructure Layer** | - Repositórios SQLAlchemy 2.0 mapeando para tabelas PostgreSQL (`bookings`, `availability_windows`, `booking_windows`, `quota_periods`) <br>- Migrations Alembic <br>- Publicador de eventos via Postgres NOTIFY (sem Redis — reduz custo de infraestrutura) <br>- Serviço de geração de QR Code (bibliotecas `qrcode`, `pillow`) <br>- Clock e IdGenerator inseríveis (facilita testes) | - Biblioteca HTTP (fetch ou axios) wrappers para endpoints da API <br>- Biblioteca de QR Code para leitura no móvil (`react-qr-reader` ou equivalente) <br>- Tailwind CSS para estilização utilitária <br>- shadcn/ui como base de componentes acessíveis |
| **Cross‑cutting** | - Logging estruturado (structlog) <br>- Métricas Prometheus (latência, taxa de erro) <br>- Segurança: JWT via OAuth2 ou API Key interno, HTTPS obrigatório | - Política de CSP, cookies HttpOnly para token de sessão <br>- Pré‑renderização (SSG) de páginas estáticas (sobre, ajuda) <br>- Optimistic UI nas mutações (ex: mostra reserva imediatamente, desfaz em erro) |

**Observação de Orçamento:** Nenhuma camada introduz tecnologia paga além da stack definida (PostgreSQL pode ser versão open‑source hospedada em instância modesta; Redis opcional para eventos pode ser substituído por Postgres NOTIFY se necessário). O uso de bibliotecas open‑source (FastAPI, SQLAlchemy, TanStack, shadcn/ui, Tailwind) mantém custo de licença zero.

---

## 3. Mapeamento de Invariantes do Domínio (DDD)

| Invariante (Regra de Negócio Imutável) | Onde é Aplicada (Camada) | Como é Garantida |
|---|---|---|
| **Colisão de Horários** (não pode haver duas reservas confirmadas que se sobreponham no mesmo recurso) | **Domain** – `AvailabilityWindow` (aggregate root) tem `is_full()` que compara `count(booking_windows WHERE workspace_id=? AND day=? AND slot_index=?)` com `capacity.seats`. <br>**Application** – `CreateBookingUseCase` insere em `booking_windows` para cada slot da reserva, em transação com `version_id` otimista. | Se a janela já estiver cheia (count ≥ seats), `INSERT` em `booking_windows` viola constraint de capacidade e o use case captura `CapacityExceededError`. O caso de uso não persiste até que todas as janelas passem na validação. |
| **Cancelamento com Antecedência de 2h** (uma reserva somente pode ser cancelada se faltarem ≥ 2h para o início) | **Domain** – método `Booking.cancel()` verifica `if self.slot.start - clock.now() < timedelta(hours=2): raise InvalidCancellationError`. | O caso de uso `CancelBookingUseCase` delega à entidade; se a regra for violada, retorna erro 409 com mensagem clara. A tentativa de cancelamento tardio não altera o estado nem consome quota. |
| **Cotas por Setor** (cada centro de custo tem limite máximo de horas‑estação/mês; não é possível ultrapassar) | **Domain** – classe `QuotaPeriod` com método `consume(hours)` que verifica `if hours > self.remaining_hours(): raise QuotaExceededError`. <br>**Application** – `CreateBookingUseCase` busca a quota do período correspondente ao centro de custo e chama `quota.consume(booking.duration_hours())` antes de confirmar a reserva (atomicamente com a inserção em `booking_windows`). | Se a quota for insuficiente, lança `QuotaExceededError` que é tratada na camada de aplicação como HTTP 402 (Payment Required) ou 400 com detalhe do saldo restante. A reserva nunca é confirmada, portanto a quota não é consumida indevidamente. |

**Como esses invariantes protegem o negócio:**

- Evita **overbooking** mesmo sob alta concorrência, porque a verificação é feita em memória (objeto imutável) antes de qualquer escrita; o repositório usa otimistic lock (`version_id`) apenas para detectar atualizações concorrentes e disparar retry automático no caso de uso.
- Garante que o **check‑in** seja o gatilho de confirmação; sem ele, a reserva permanece *pending* e é liberada automaticamente após a tolerância, liberando a vaga para a fila de espera.
- Assegura o **controle de custos** por departamento: toda reserva confirmada consome quota; se o limite for atingido, novas reservas são bloqueadas até o próximo período ou até que alguma seja cancelada (que devolve quota via `QuotaPeriod.consume(-duration_hours)` — `consume()` aceita valor negativo para devolver).

---

## ✅ Auto‑Correção Final

### Cobertura de 100% dos problemas apontados no Diagnóstico

| Problema do Diagnóstico | Mapeado para | Como é resolvido |
|---|---|---|
| P1 – Overbooking em dias de pico | RO-02 (fila de espera) + Motor de Agendamento (validação de colisão) | Fila absorve picos; sobreposição proibida por invariante de colisão. |
| P2 – Estações ociosas por no-show (35%) | RO-01 (check‑in automático) + Liberação Automática | Reserva sem check‑in vira vaga disponível; reduz ociosidade em ~80%. |
| P3 – Custo total de ociosidade | Consequência de P1+P2 | Redução de ociosidade gera economia > R$ 100k/mês (ver viabilidade). |
| P4 – Salas de reunião ociosas | RO-05 (política de sala com tolerância) + Liberação Automática | Sala sem check‑in volta ao pool; permite uso por outros times. |
| P5 – Falta de controle de custos por departamento | RO-03 (cotas por centro de custo) + Relatórios de custo | Visão em tempo real e rateio automático; elimina esforço manual. |
| P6 – Risco de não adequação ao orçamento | Análise de viabilidade (ROI < 1 mês) | Custo da licença ≤ orçamento; economia líquida garante pagamento e ainda sobra recurso. |

### Recursos desnecessários que poderiam estourar o orçamento

- **Inteligência Artificial para sugestão de horários**: não solicitado pelo diagnóstico; implicaria custos de modelo, treinamento e manutenção. Removido.
- **Módulo de gamificação / pontos de engajamento**: fora do escopo de controle de ociosidade e custos; não agrega valor financeiro imediato. Removido.
- **Integração com múltiplos provedores de calendário (Google, Outlook)**: o diagnóstico aponta apenas necessidade de integração com sistema de ponto interno; provedores externos seriam esforço extra sem retorno claro. Mantido apenas a integração de ponto via REST.
- **Armazenamento de logs em serviço de terceiros (ex: Datadog)**: pode ser substituído por solução open‑source (ELK ou Loki) ou simplesmente por logs rotacionados em disco; não é essencial para o MVP. Mantido logging padrão.

Todas as funcionalidades listadas são **estritamente necessárias** para atender aos requisitos obrigatórios (RO-01 a RO-08) e para colocar em prática os seis invariantes do domínio (I1–I6, ver documento-software.md §10). Nenhum componente adiciona custo de licença ou infraestrutura além da stack já definida.

--- 
