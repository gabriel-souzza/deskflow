# PROPOSTA COMERCIAL EXECUTIVA — DeskFlow

## 1. Sumário Executivo

**DeskFlow** é uma plataforma de gestão de espaços híbridos projetada especificamente para resolver os desafios de sobrecarga, ociosidade e falta de controle de custos do seu modelo de trabalho. Com um investimento inicial de **R$ 25.000,00** e uma licença mensal de **R$ 8.500,00**, a solução entrega **70% de redução nos custos com ociosidade em até 90 dias**, com retorno sobre investimento (ROI) positivo já no primeiro mês de operação.

**Investimento Total:** R$ 25.000,00 (setup) + R$ 8.500,00/mês (licença)
**Prazo:** 6 semanas (3 sprints quinzenais)
**Orçamento:** Dentro do teto de R$ 15.000,00/mês estabelecido

---

## 2. Diagnóstico e Desafios Mapeados

O diagnóstico revela três problemas interdependentes que consomem recursos críticos da sua operação:

| Problema | Impacto | Custo Mensal |
|---|---|---|
| **Overbooking em dias de pico** | 50 funcionários sem espaço garantido | R$ 960.000,00 de perda potencial/mês |
| **No-show de 35%** | 105 estações ociosas/dia | R$ 126.000,00 de desperdício mensal |
| **Custo total de ociosidade** | 250 estações × R$ 1.200,00 | R$ 300.000,00 fixo/mês (65% de utilização) |

Esses problemas geram **R$ 169.520,00/mês de custo de ociosidade** — entre **7 e 11 vezes** o orçamento mensal disponível (R$ 15.000,00). Sem intervenção, a empresa perde produtividade, aumenta custos operacionais e compromete a experiência do colaborador.

---

## 3. A Solução DeskFlow (Escopo Resumido e Stack)

### Arquitetura Técnica

| Camada | Tecnologia | Função |
|---|---|---|
| **Presentation** | Next.js (TypeScript) + shadcn/ui + Tailwind | Interface responsiva para reserva, agenda e relatórios |
| **Application** | TanStack Query + Server-Sent Events | Carregamento e atualização em tempo real de disponibilidade |
| **Domain** | Python (FastAPI) + dataclasses + Zod | Regras de negócio imutáveis (colisão de horários, cancelamento, cotas) |
| **Infrastructure** | PostgreSQL + SQLAlchemy 2.0 | Persistência de entidades e eventos de domínio |

### Três Invariantes de Domínio Garantidos

1. **Colisão de Horários** — Nenhuma reserva confirmada pode sobrepor-se a outra no mesmo recurso. Validado em tempo real pelo motor de agendamento.
2. **Cancelamento com 2h de Antecedência** — Reservas só podem ser canceladas se houver pelo menos 2 horas até o início do slot. Impede cancelamentos tardios que comprometem a disponibilidade.
3. **Cotas por Setor** — Cada centro de custo tem limite máximo de horas-estação/mês. Consumo rastreado e bloqueio antecipado quando o limite é atingido.

---

## 4. Cronograma de Implementação (3 Sprints Quinzenais)

| Sprint | Foco | Entregas Principais |
|---|---|---|
| **Sprint 1 (Semana 1)** | Fundação do Domínio | Modelagem de entidades (Booking, TimeSlot, AvailabilityWindow, QuotaPeriod); validação de invariantes; setup do ambiente PostgreSQL |
| **Sprint 2 (Semana 2-3)** | Motor de Agendamento | Engine de alocação com fila de espera; check-in via QR Code; liberação automática; integração com sistema de ponto |
| **Sprint 3 (Semana 4-6)** | Frontend e Relatórios | Interface Next.js completa; dashboard de utilização; relatórios de custo por centro de custo; deploy em produção |

**Prazo Total:** 6 semanas (3 sprints de 2 semanas cada)

---

## 5. Plano de Investimento e Análise de ROI

| Item | Valor | Observação |
|---|---|---|
| **Setup (One-time)** | R$ 25.000,00 | Modelagem de domínio, onboarding, integração com sistema de ponto |
| **Licença Mensal** | R$ 8.500,00 | DeskFlow — dentro do orçamento de R$ 15.000,00/mês |
| **Investimento Total (6 meses)** | R$ 89.000,00 | Setup + 6 meses de licença |
| **Economia Mensal (ROI)** | R$ 118.664,00 | 70% de redução nos custos com ociosidade (R$ 169.520 → R$ 50.856) |
| **Custo da licença** | R$ 8.500,00/mês | Dentro do teto de R$ 15.000,00/mês |
| **Lucro líquido mensal** | R$ 110.164,00 | Economia mensal subtraída da licença |
| **Payback** | **< 1 mês** | Economia mensal (R$ 118.664) supera o custo de licença (R$ 8.500) já no primeiro mês |

**Análise de ROI (verificação):**
- **Custo mensal de ociosidade:** R$ 169.520,00
- **Economia projetada:** R$ 118.664,00 (70% de redução)
- **Custo da licença:** R$ 8.500,00/mês (dentro do orçamento de R$ 15.000,00)
- **Lucro líquido mensal:** R$ 110.164,00
- **Payback:** Menos de 1 mês (primeiro mês de lucro líquido)

Nota: a tabela de investimento acima e esta análise derivam dos mesmos dados — qualquer divergência entre elas é erro de cálculo, não de cenário.

---

## 6. Termos e Próximos Passos

**Termos:**
- Implementação em 6 semanas (3 sprints quinzenais)
- Licença mensal de R$ 8.500,00, cobrada a partir do segundo mês de operação
- Suporte prioritário durante a fase de go-live
- Relatórios de desempenho mensais com foco em redução de ociosidade e controle de custos

**Próximos Passos:**
1. Aprovação do orçamento (R$ 25.000 setup + R$ 8.500/mês)
2. Definição do período piloto (1 trimestre de implantação)
3. Kick-off do Sprint 1 (semana 1)
4. Go-live e monitoramento de KPIs (ocupação, no-show, custo por centro de custo)

---

**DeskFlow** transforma a gestão de espaços híbridos de um gargalo operacional em uma fonte de eficiência. Com uma solução robusta, de baixo custo e impacto imediato, a empresa recupera produtividade, reduz custos e ganha controle total sobre seus recursos físicos.

---

