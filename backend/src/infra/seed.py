import asyncio
import json
import uuid
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import delete, select

from infra.database import SessionLocal
from infra.models import (
    AvailabilityWindowORM,
    BookingORM,
    BookingWindowORM,
    CostCenterORM,
    EmployeeORM,
    HolidayORM,
    QuotaPeriodORM,
    WaitlistORM,
    WorkspaceORM,
)
from infra.security import hash_password


async def seed_database() -> None:
    async with SessionLocal() as session:
        print("[SEED] Iniciando seed do banco DeskFlow...")

        # 1. Centros de Custo
        existing_centers = (await session.execute(select(CostCenterORM))).scalars().all()
        centers = {cc.name: cc for cc in existing_centers}
        cost_centers_data = [
            ("Engenharia de Software", Decimal("160.00")),
            ("Recursos Humanos", Decimal("80.00")),
            ("Design & Produto", Decimal("120.00")),
            ("Financeiro", Decimal("100.00")),
        ]
        for name, quota in cost_centers_data:
            if name not in centers:
                cc = CostCenterORM(id=uuid.uuid4(), name=name, monthly_quota_hours=quota)
                session.add(cc)
                centers[name] = cc
        await session.flush()
        print(f"[OK] Centros de custo prontos: {list(centers.keys())}.")

        # 2. Períodos de Cota para o mês atual
        today = date.today()
        period_start = today.replace(day=1)
        next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
        period_end = next_month - timedelta(days=1)
        p_start_dt = datetime.combine(period_start, time.min)
        p_end_dt = datetime.combine(period_end, time.max)

        for name, cc in centers.items():
            existing_qp = await session.scalar(
                select(QuotaPeriodORM).where(
                    QuotaPeriodORM.cost_center_id == cc.id,
                    QuotaPeriodORM.period_start == p_start_dt,
                )
            )
            if not existing_qp:
                qp = QuotaPeriodORM(
                    cost_center_id=cc.id,
                    period_start=p_start_dt,
                    period_end=p_end_dt,
                    total_hours=cc.monthly_quota_hours,
                    consumed_hours=Decimal("10.00") if "Engenharia" in name else Decimal("0.00"),
                )
                session.add(qp)
        await session.flush()
        print("[OK] Cotas do mes corrente configuradas.")

        # 3. Colaboradores
        employees_data = [
            (
                "Administrador Geral",
                "admin@deskflow.com",
                "Admin123456!",
                centers["Engenharia de Software"].id,
                True,
            ),
            (
                "Maria Silva",
                "maria.silva@deskflow.com",
                "Colaborador123!",
                centers["Engenharia de Software"].id,
                True,
            ),
            (
                "Joao Santos",
                "joao.santos@deskflow.com",
                "Colaborador123!",
                centers["Recursos Humanos"].id,
                True,
            ),
            (
                "Ana Costa",
                "ana.costa@deskflow.com",
                "Colaborador123!",
                centers["Design & Produto"].id,
                False,  # Não elegível para testar validação de política presencial
            ),
            (
                "Carlos Oliveira",
                "carlos.oliveira@deskflow.com",
                "Colaborador123!",
                centers["Financeiro"].id,
                True,
            ),
        ]
        created_employees = {}
        for name, email, password, cc_id, eligible in employees_data:
            existing_emp = await session.scalar(
                select(EmployeeORM).where(EmployeeORM.email == email)
            )
            if not existing_emp:
                emp = EmployeeORM(
                    id=uuid.uuid4(),
                    name=name,
                    email=email,
                    password_hash=hash_password(password),
                    cost_center_id=cc_id,
                    is_eligible_for_booking=eligible,
                )
                session.add(emp)
                created_employees[email] = emp
            else:
                created_employees[email] = existing_emp
        await session.flush()
        print("[OK] Colaboradores criados com senhas de teste.")

        # 4. Espaços (Workspaces)
        workspaces_data = [
            # Estações (capacity = 1)
            ("A-101", "1", "open", "estacao", 1, ["monitor_duplo", "tomada", "usb_c"]),
            ("A-102", "1", "open", "estacao", 1, ["monitor", "tomada"]),
            ("A-103", "1", "focus", "estacao", 1, ["monitor", "tomada", "cadeira_ergonomica"]),
            ("A-104", "1", "focus", "estacao", 1, ["monitor", "fone_noise_cancelling"]),
            ("B-201", "2", "quiet", "estacao", 1, ["monitor_duplo", "dock_station"]),
            ("B-202", "2", "quiet", "estacao", 1, ["monitor", "tomada"]),
            ("B-203", "2", "cabine", "estacao", 1, ["isolamento_acustico", "tomada"]),
            ("B-204", "2", "cabine", "estacao", 1, ["isolamento_acustico", "monitor"]),
            # Salas de Reunião (capacity > 1)
            ("SALA-INICIAL", "1", "reuniao", "sala", 4, ["tv_4k", "whiteboard"]),
            (
                "SALA-INOVACAO",
                "1",
                "reuniao",
                "sala",
                6,
                ["videoconferencia", "tv_4k", "whiteboard"],
            ),
            (
                "SALA-DIRETORIA",
                "2",
                "executiva",
                "sala",
                10,
                ["videoconferencia_zoom", "projetor", "sistema_audio"],
            ),
        ]
        created_workspaces = {}
        for code, floor, zone, w_type, capacity, resources in workspaces_data:
            existing_ws = await session.scalar(
                select(WorkspaceORM).where(WorkspaceORM.code == code)
            )
            if not existing_ws:
                ws = WorkspaceORM(
                    id=uuid.uuid4(),
                    code=code,
                    floor=floor,
                    zone=zone,
                    type=w_type,
                    capacity=capacity,
                    resources=json.dumps(resources),
                )
                session.add(ws)
                created_workspaces[code] = ws
            else:
                created_workspaces[code] = existing_ws
        await session.flush()
        print("[OK] Espacos de trabalho (estacoes e salas) cadastrados.")

        # 5. Janelas de Disponibilidade (Availability Windows) para hoje e próximos 5 dias
        all_ws = (await session.execute(select(WorkspaceORM))).scalars().all()
        for offset in range(6):
            target_date = today + timedelta(days=offset)
            target_str = target_date.isoformat()
            for ws in all_ws:
                # Verifica se já tem o slot 0
                first_slot = await session.scalar(
                    select(AvailabilityWindowORM).where(
                        AvailabilityWindowORM.workspace_id == ws.id,
                        AvailabilityWindowORM.day == target_str,
                        AvailabilityWindowORM.slot_index == 0,
                    )
                )
                if not first_slot:
                    session.add_all(
                        AvailabilityWindowORM(
                            workspace_id=ws.id,
                            day=target_str,
                            slot_index=i,
                            seats=ws.capacity,
                            version_id=1,
                        )
                        for i in range(40)
                    )
        await session.flush()
        print("[OK] Janelas de disponibilidade de 15min geradas para os proximos 6 dias.")

        # 6. Feriado de Teste
        holiday_date = today + timedelta(days=20)
        existing_holiday = await session.scalar(
            select(HolidayORM).where(HolidayORM.day == holiday_date)
        )
        if not existing_holiday:
            session.add(HolidayORM(day=holiday_date, description="Feriado Corporativo Exemplo"))
            await session.flush()
            print("[OK] Feriado corporativo de teste registrado.")

        # 7. Reservas de Teste
        emp_maria = created_employees["maria.silva@deskflow.com"]
        ws_a101 = created_workspaces["A-101"]
        booking_start = datetime.combine(today + timedelta(days=1), time(9, 0))
        booking_end = booking_start + timedelta(hours=2)

        existing_b = await session.scalar(
            select(BookingORM).where(
                BookingORM.workspace_id == ws_a101.id,
                BookingORM.slot_start == booking_start,
            )
        )
        if not existing_b:
            b_id = uuid.uuid4()
            test_booking = BookingORM(
                id=b_id,
                workspace_id=ws_a101.id,
                employee_id=emp_maria.id,
                cost_center_id=emp_maria.cost_center_id,
                slot_start=booking_start,
                slot_end=booking_end,
                status="PENDING",
            )
            session.add(test_booking)
            await session.flush()
            # Adiciona booking windows
            day_str = booking_start.date().isoformat()
            start_idx = (9 * 60 - 8 * 60) // 15
            session.add_all(
                BookingWindowORM(
                    booking_id=b_id,
                    workspace_id=ws_a101.id,
                    day=day_str,
                    slot_index=start_idx + i,
                )
                for i in range(8)  # 2 horas = 8 slots de 15 min
            )
            print("[OK] Reserva de teste PENDING criada para A-101.")

        await session.commit()
        print("\n=== BANCO DE DADOS POPULADO COM SUCESSO! ===")
        print("\nCREDENCIAIS PARA TESTES NO SWAGGER (/api/v1/auth/login):")
        print("------------------------------------------------------------------")
        print(" ADMIN:        admin@deskflow.com       / Admin123456!")
        print(" COLABORADOR:  maria.silva@deskflow.com / Colaborador123! (Engenharia)")
        print(" COLABORADOR:  joao.santos@deskflow.com  / Colaborador123! (RH)")
        print(" NAO-ELEGIVEL: ana.costa@deskflow.com    / Colaborador123! (Design)")
        print("------------------------------------------------------------------\n")


if __name__ == "__main__":
    asyncio.run(seed_database())
