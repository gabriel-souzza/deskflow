# Guia de Testes dos Endpoints no Swagger — DeskFlow

Este documento contém todos os **parâmetros, IDs reais semeados no banco de dados PostgreSQL** e **payloads JSON prontos para copiar e colar** no Swagger UI da aplicação.

---

## 1. Acesso e Autenticação

- **URL do Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **URL da API Base**: `http://localhost:8000/api/v1`
- **Métricas Prometheus**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Como Autenticar no Swagger:
1. Abra o Swagger UI e localize o endpoint `POST /api/v1/auth/login`.
2. Execute o login com um dos usuários da tabela abaixo.
3. Copie o valor do campo `access_token` retornado.
4. Clique no botão verde **Authorize** (canto superior direito do Swagger UI).
5. Cole o token no campo de valor:
   ```text
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
6. Clique em **Authorize** e depois em **Close**. Todas as requisições autenticadas passarão a enviar o cabeçalho `Authorization`.

---

## 2. Usuários e Credenciais de Teste

| Papel | Nome | Email (`username`) | Senha | ID do Colaborador (`employee_id`) | Centro de Custo Vinculado | Elegível? |
|---|---|---|---|---|---|:---:|
| **Admin** | Administrador Geral | `admin@deskflow.com` | `Admin123456!` | `79e2f3c0-8981-4ca7-b0e4-f43a4116facf` | `d5db6013-201b-4228-af29-58a4b71e82ce` (Engenharia) | Sim |
| **Colaborador** | Maria Silva | `maria.silva@deskflow.com` | `Colaborador123!` | `7e327db5-f9d9-44bd-887b-3f2f927a16f5` | `d5db6013-201b-4228-af29-58a4b71e82ce` (Engenharia) | Sim |
| **Colaborador** | João Santos | `joao.santos@deskflow.com` | `Colaborador123!` | `cb137d3c-d9f7-4a83-a021-8ff8a91884f6` | `ecdc3ff0-ae69-446d-b264-abc647b9ef5d` (RH) | Sim |
| **Colaborador** | Carlos Oliveira | `carlos.oliveira@deskflow.com` | `Colaborador123!` | `401a2943-3c67-44d1-a5b2-7ec2df6ff49f` | `33f70fe6-ed53-49e7-ac23-cfee86564e27` (Financeiro) | Sim |
| **Colaborador** | Ana Costa | `ana.costa@deskflow.com` | `Colaborador123!` | `2982c1a5-cd3a-4945-9881-4bce087bd205` | `38161018-0b89-42e2-9603-2d4ba8655d76` (Design) | **Não** (teste de política) |

---

## 3. Centros de Custo e Cotas de Horas

| Nome do Centro de Custo | ID (`cost_center_id`) | Cota Mensal | Horas Consumidas | Saldo Atual |
|---|---|:---:|:---:|:---:|
| **Engenharia de Software** | `d5db6013-201b-4228-af29-58a4b71e82ce` | 160h | 11.00h | 149.00h |
| **Recursos Humanos** | `ecdc3ff0-ae69-446d-b264-abc647b9ef5d` | 80h | 0.00h | 80.00h |
| **Financeiro** | `33f70fe6-ed53-49e7-ac23-cfee86564e27` | 100h | 0.00h | 100.00h |
| **Design & Produto** | `38161018-0b89-42e2-9603-2d4ba8655d76` | 120h | 0.00h | 120.00h |

---

## 4. Espaços de Trabalho Cadastrados (`Workspaces`)

| Código | ID (`workspace_id`) | Andar | Zona | Tipo | Capacidade | Recursos |
|---|---|:---:|:---:|:---:|:---:|---|
| `A-101` | `d5400c11-7bbd-4a7d-9d44-f6c54990bb87` | `1` | `open` | `estacao` | 1 | Monitor 4K, Cadeira Ergonômica |
| `A-102` | `6b108a85-57c0-463e-9892-a85b808dcde3` | `1` | `open` | `estacao` | 1 | Monitor Dual |
| `A-103` | `28e131a0-9359-4c19-b8a5-2c1c0f6992a1` | `1` | `focus` | `estacao` | 1 | Fone Noise Cancelling |
| `A-104` | `76141600-b0c0-477b-9249-1b43f0969eb1` | `1` | `focus` | `estacao` | 1 | Stand Desk |
| `B-201` | `eff2b050-0e00-469a-ad73-aa981dfe6de1` | `2` | `quiet` | `estacao` | 1 | Monitor 27 |
| `B-202` | `4726432f-9ec4-42ac-83dd-3d950f4414be` | `2` | `quiet` | `estacao` | 1 | Stand Desk |
| `B-203` | `a90b00b5-5952-4d8f-a59a-63cf1db7459b` | `2` | `cabine` | `estacao` | 1 | Cabine Acústica |
| `B-204` | `480a2ec6-4e19-4a78-827a-feae0fac9df9` | `2` | `cabine` | `estacao` | 1 | Cabine Acústica |
| `SALA-INICIAL` | `66dc1d45-1a11-4281-97c4-b2d70774cb47` | `1` | `reuniao` | `sala` | 4 | TV 55, Videoconferência |
| `SALA-INOVACAO`| `89f71b5c-a59b-4a13-aafa-1b3cf5226dd3` | `1` | `reuniao` | `sala` | 6 | TV 65, Lousa Digital |
| `SALA-DIRETORIA`| `6ef72470-2011-4f32-84c8-aab0fd1370cc` | `2` | `executiva`| `sala` | 10 | Projetor, Sistema de Som |

---

## 5. Reservas e Feriados Existentes

### Reservas Semeadas:
- **Reserva 1 (Pendente no futuro)**:
  - **ID**: `849bd1b4-84e4-429d-b0a9-2c2cda39af2c`
  - **Espaço**: `A-101` (`d5400c11-7bbd-4a7d-9d44-f6c54990bb87`)
  - **Titular**: Maria Silva (`7e327db5-f9d9-44bd-887b-3f2f927a16f5`)
  - **Horário**: `2026-10-12 09:00:00` às `2026-10-12 10:00:00`
  - **Status**: `PENDING`
- **Reserva 2 (Pendente no futuro)**:
  - **ID**: `e3c1c177-e822-4ea3-a7a8-d02eda8ad137`
  - **Espaço**: `A-101` (`d5400c11-7bbd-4a7d-9d44-f6c54990bb87`)
  - **Titular**: Maria Silva (`7e327db5-f9d9-44bd-887b-3f2f927a16f5`)
  - **Horário**: `2026-10-11 09:00:00` às `2026-10-11 11:00:00`
  - **Status**: `PENDING`
- **Reserva 3 (Expirada pelo Scheduler)**:
  - **ID**: `993536dc-010e-4555-b470-d10cb5325476`
  - **Status**: `EXPIRED`

### Feriado Cadastrado:
- **Data**: `2026-10-30`
- **Descrição**: `Feriado Corporativo Exemplo`

---

## 6. Payloads e Parâmetros Prontos para Teste

### 6.1 Autenticação (`POST /api/v1/auth/login`)

#### Exemplo 1: Login de Colaborador (Maria Silva)
```json
{
  "username": "maria.silva@deskflow.com",
  "password": "Colaborador123!"
}
```

#### Exemplo 2: Login de Administrador
```json
{
  "username": "admin@deskflow.com",
  "password": "Admin123456!"
}
```

---

### 6.2 Consulta de Disponibilidade (`GET /api/v1/availability`)

- **Autenticação**: Bearer Token
- **Query Parameters**:
  - `day`: `2026-10-12` *(obrigatório)*
  - `floor`: `1` *(opcional - ex: 1 ou 2)*
  - `zone`: `open` *(opcional - ex: open, focus, quiet, cabine, reuniao)*
  - `workspace_type`: `estacao` *(opcional - `estacao` ou `sala`)*
  - `workspace_id`: `d5400c11-7bbd-4a7d-9d44-f6c54990bb87` *(opcional)*

---

### 6.3 Listar Todos os Espaços (`GET /api/v1/workspaces`)

- **Autenticação**: Nenhuma (aberto)
- **Retorno**: Lista de todos os 12 espaços com andares, zonas, capacidade e recursos.

---

### 6.4 Disponibilidade de um Espaço (`GET /api/v1/workspaces/{id}/availability`)

- **Path Parameter**:
  - `id`: `d5400c11-7bbd-4a7d-9d44-f6c54990bb87` *(Espaço A-101)*
- **Query Parameter**:
  - `day`: `2026-10-12`

---

### 6.5 Criar Reserva (`POST /api/v1/bookings`)

- **Autenticação**: Bearer Token
- **Regras do Domínio**: Horários alinhados a intervalos de 15 minutos (grid I1); colaborador elegível; cota de centro de custo suficiente.

#### Payload para Estação `A-102` (João Santos / RH):
```json
{
  "workspace_id": "6b108a85-57c0-463e-9892-a85b808dcde3",
  "employee_id": "cb137d3c-d9f7-4a83-a021-8ff8a91884f6",
  "cost_center_id": "ecdc3ff0-ae69-446d-b264-abc647b9ef5d",
  "slot_start": "2026-10-12T14:00:00",
  "slot_end": "2026-10-12T16:00:00"
}
```

#### Payload para Sala de Reunião `SALA-INICIAL` (Maria Silva / Engenharia):
```json
{
  "workspace_id": "66dc1d45-1a11-4281-97c4-b2d70774cb47",
  "employee_id": "7e327db5-f9d9-44bd-887b-3f2f927a16f5",
  "cost_center_id": "d5db6013-201b-4228-af29-58a4b71e82ce",
  "slot_start": "2026-10-13T10:00:00",
  "slot_end": "2026-10-13T11:30:00"
}
```

#### Teste de Rejeição de Política (Colaborador Não Elegível - Ana Costa):
```json
{
  "workspace_id": "eff2b050-0e00-469a-ad73-aa981dfe6de1",
  "employee_id": "2982c1a5-cd3a-4945-9881-4bce087bd205",
  "cost_center_id": "38161018-0b89-42e2-9603-2d4ba8655d76",
  "slot_start": "2026-10-12T09:00:00",
  "slot_end": "2026-10-12T10:00:00"
}
```
*(Esperado: `403 Forbidden` informando que a colaboradora não possui elegibilidade para agendamento presencial).*

---

### 6.6 Obter QR Code PNG da Reserva (`GET /api/v1/bookings/{id}/qr`)

- **Autenticação**: Bearer Token
- **Path Parameter**:
  - `id`: `849bd1b4-84e4-429d-b0a9-2c2cda39af2c` *(Reserva existente)*
- **Resposta**: Retorna a imagem em binário `image/png` contendo o token assinado HMAC/JWT. Pode ser visualizada diretamente no Swagger ou salva no disco.

---

### 6.7 Check-in da Reserva (`POST /api/v1/bookings/{id}/checkin`)

- **Autenticação**: Bearer Token
- **Path Parameter**:
  - `id`: `849bd1b4-84e4-429d-b0a9-2c2cda39af2c`
- **Request Body**:
```json
{
  "qr_token": "token_lido_do_qr_code"
}
```
*(Nota: O check-in valida a tolerância de ±10 minutos em relação ao horário de início da reserva. Se executado fora da janela, retorna `409 Conflict: Check-in is outside the allowed time window`).*

---

### 6.8 Cancelar Reserva (`DELETE /api/v1/bookings/{id}`)

- **Autenticação**: Bearer Token (Titular ou Admin)
- **Path Parameter**:
  - `id`: `e3c1c177-e822-4ea3-a7a8-d02eda8ad137`
- **Efeito**:
  - Transiciona o status de `PENDING` para `CANCELLED`.
  - Estorna automaticamente as horas consumidas de volta para o Centro de Custo (`QuotaPeriod.consume(-h)`).
  - Publica o evento `BookingCancelled` no `EventBus`, que dispara o `WaitlistHandler` para notificar o próximo da fila de espera.

---

### 6.9 Entrar na Fila de Espera (`POST /api/v1/waitlist`)

- **Autenticação**: Bearer Token
- **Request Body**:
```json
{
  "workspace_id": "d5400c11-7bbd-4a7d-9d44-f6c54990bb87",
  "slot_start": "2026-10-12T09:00:00",
  "slot_end": "2026-10-12T10:00:00"
}
```

---

### 6.10 Cadastrar Novo Colaborador (`POST /api/v1/admin/accounts`)

- **Autenticação**: Bearer Token de **Admin** (`admin@deskflow.com`)
- **Request Body**:
```json
{
  "name": "Fernanda Lima",
  "email": "fernanda.lima@deskflow.com",
  "password": "SenhaSegura123!",
  "cost_center_id": "d5db6013-201b-4228-af29-58a4b71e82ce",
  "is_eligible_for_booking": true
}
```

---

### 6.11 Listar e Gerenciar Cotas de Centros de Custo

#### Listar Cotas (`GET /api/v1/admin/quotas`):
- **Autenticação**: Bearer Token de Admin.
- **Retorno**: Todas as cotas com totais, horas gastas e centros de custo vinculados.

#### Atualizar Cota (`PUT /api/v1/admin/quotas/{id}`):
- **Path Parameter**:
  - `id`: `d5db6013-201b-4228-af29-58a4b71e82ce` *(Centro de Custo Engenharia)*
- **Request Body**:
```json
{
  "monthly_quota_hours": 200.0
}
```

---

### 6.12 Bloquear Feriado Corporativo (`POST /api/v1/admin/holidays`)

- **Autenticação**: Bearer Token de Admin
- **Request Body**:
```json
{
  "day": "2026-11-20",
  "description": "Dia da Consciência Negra"
}
```
*(Efeito: Bloqueia a criação de reservas nesse dia e limpa as janelas de disponibilidade).*

---

### 6.13 Cadastrar Novo Workspace (`POST /api/v1/admin/workspaces`)

- **Autenticação**: Bearer Token de Admin
- **Request Body**:
```json
{
  "code": "C-301",
  "floor": "3",
  "zone": "tech-lab",
  "type": "estacao",
  "capacity": 1,
  "resources": ["Monitores Triplos", "GPU Station", "Headset VR"]
}
```

---

### 6.14 Relatórios de Utilização e Exportação

#### Relatório no Dashboard (`GET /api/v1/reports/utilization`):
- **Autenticação**: Bearer Token de Admin
- **Query Parameter**:
  - `day`: `2026-10-12`

#### Exportar Relatório em CSV (`GET /api/v1/reports/export`):
- **Query Parameters**:
  - `start_date`: `2026-10-01`
  - `end_date`: `2026-10-31`
  - `format`: `csv`

#### Exportar Relatório em PDF (`GET /api/v1/reports/export`):
- **Query Parameters**:
  - `start_date`: `2026-10-01`
  - `end_date`: `2026-10-31`
  - `format`: `pdf`
- **Retorno**: Arquivo PDF formatado com tabela de reservas, andares, zonas e status gerado dinamicamente via ReportLab.

---

### 6.15 Integração de Ponto Eletrônico (`POST /api/v1/integrations/attendance/sync`)

- **Cabeçalho Requerido**: `X-Integration-Token: attendance-secret-token`
- **Request Body**:
```json
{
  "employee_id": "2982c1a5-cd3a-4945-9881-4bce087bd205",
  "days_present": ["2026-10-01", "2026-10-02", "2026-10-05"]
}
```
*(Efeito: Sincroniza dias presenciais com o registro de auditoria e calcula elegibilidade presencial).*

---

### 6.16 Monitoramento em Tempo Real (`GET /api/v1/availability/stream`)

- **Protocolo**: Server-Sent Events (SSE)
- **Eventos Emitidos em Tempo Real**:
  - `booking.created`
  - `booking.confirmed`
  - `booking.cancelled`
  - `quota.alert` (alertas automáticos em 80% e 95% de consumo de cota)
  - `heartbeat` (manutenção da conexão viva a cada 30 segundos)
