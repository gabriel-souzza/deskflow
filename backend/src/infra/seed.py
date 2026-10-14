import asyncio
import json
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select

from infra.database import SessionLocal
from infra.models import (
    AvailabilityWindowORM,
    BookingORM,
    BookingWindowORM,
    CostCenterORM,
    EmployeeORM,
    HolidayORM,
    QuotaPeriodORM,
    WorkspaceORM,
)
from infra.security import hash_password


async def seed_database() -> None:
    async with SessionLocal() as session:
        print("[SEED] Iniciando seed do banco DeskFlow...")

        # 1. Centros de Custo (IDs canônicos fixos)
        cost_centers_data = [
            (
                uuid.UUID("d5db6013-201b-4228-af29-58a4b71e82ce"),
                "Engenharia de Software",
                Decimal("160.00"),
            ),
            (
                uuid.UUID("ecdc3ff0-ae69-446d-b264-abc647b9ef5d"),
                "Recursos Humanos",
                Decimal("80.00"),
            ),
            (
                uuid.UUID("38161018-0b89-42e2-9603-2d4ba8655d76"),
                "Design & Produto",
                Decimal("120.00"),
            ),
            (
                uuid.UUID("33f70fe6-ed53-49e7-ac23-cfee86564e27"),
                "Financeiro",
                Decimal("100.00"),
            ),
        ]
        centers = {}
        for cc_id, name, quota in cost_centers_data:
            existing_cc = await session.scalar(
                select(CostCenterORM).where(
                    (CostCenterORM.id == cc_id) | (CostCenterORM.name == name)
                )
            )
            if not existing_cc:
                cc = CostCenterORM(id=cc_id, name=name, monthly_quota_hours=quota)
                session.add(cc)
                centers[name] = cc
            else:
                centers[name] = existing_cc
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

        # 3. Colaboradores (IDs canônicos fixos com role no banco)
        employees_data = [
            (
                uuid.UUID("79e2f3c0-8981-4ca7-b0e4-f43a4116facf"),
                "Administrador Geral",
                "admin@deskflow.com",
                "Admin123456!",
                centers["Engenharia de Software"].id,
                "admin",
                True,
            ),
            (
                uuid.UUID("7e327db5-f9d9-44bd-887b-3f2f927a16f5"),
                "Maria Silva",
                "maria.silva@deskflow.com",
                "Colaborador123!",
                centers["Engenharia de Software"].id,
                "employee",
                True,
            ),
            (
                uuid.UUID("cb137d3c-d9f7-4a83-a021-8ff8a91884f6"),
                "Joao Santos",
                "joao.santos@deskflow.com",
                "Colaborador123!",
                centers["Recursos Humanos"].id,
                "employee",
                True,
            ),
            (
                uuid.UUID("2982c1a5-cd3a-4945-9881-4bce087bd205"),
                "Ana Costa",
                "ana.costa@deskflow.com",
                "Colaborador123!",
                centers["Design & Produto"].id,
                "employee",
                False,  # Não elegível para testar validação de política presencial
            ),
            (
                uuid.UUID("401a2943-3c67-44d1-a5b2-7ec2df6ff49f"),
                "Carlos Oliveira",
                "carlos.oliveira@deskflow.com",
                "Colaborador123!",
                centers["Financeiro"].id,
                "employee",
                True,
            ),
        ]
        created_employees = {}
        for emp_id, name, email, password, cc_id, emp_role, eligible in employees_data:
            existing_emp = await session.scalar(
                select(EmployeeORM).where(
                    (EmployeeORM.id == emp_id) | (EmployeeORM.email == email)
                )
            )
            if not existing_emp:
                emp = EmployeeORM(
                    id=emp_id,
                    name=name,
                    email=email,
                    password_hash=hash_password(password),
                    cost_center_id=cc_id,
                    role=emp_role,
                    is_eligible_for_booking=eligible,
                )
                session.add(emp)
                created_employees[email] = emp
            else:
                existing_emp.role = emp_role
                created_employees[email] = existing_emp
        await session.flush()
        print("[OK] Colaboradores criados com senhas de teste.")

        # 4. Espaços (Workspaces - IDs canônicos fixos)
        workspaces_data = [
            # Estações (capacity = 1)
            (
                uuid.UUID("d5400c11-7bbd-4a7d-9d44-f6c54990bb87"),
                "A-101",
                "1",
                "open",
                "estacao",
                1,
                ["monitor_duplo", "tomada", "usb_c"],
            ),
            (
                uuid.UUID("6b108a85-57c0-463e-9892-a85b808dcde3"),
                "A-102",
                "1",
                "open",
                "estacao",
                1,
                ["monitor", "tomada"],
            ),
            (
                uuid.UUID("28e131a0-9359-4c19-b8a5-2c1c0f6992a1"),
                "A-103",
                "1",
                "focus",
                "estacao",
                1,
                ["monitor", "tomada", "cadeira_ergonomica"],
            ),
            (
                uuid.UUID("76141600-b0c0-477b-9249-1b43f0969eb1"),
                "A-104",
                "1",
                "focus",
                "estacao",
                1,
                ["monitor", "fone_noise_cancelling"],
            ),
            (
                uuid.UUID("eff2b050-0e00-469a-ad73-aa981dfe6de1"),
                "B-201",
                "2",
                "quiet",
                "estacao",
                1,
                ["monitor_duplo", "dock_station"],
            ),
            (
                uuid.UUID("4726432f-9ec4-42ac-83dd-3d950f4414be"),
                "B-202",
                "2",
                "quiet",
                "estacao",
                1,
                ["monitor", "tomada"],
            ),
            (
                uuid.UUID("a90b00b5-5952-4d8f-a59a-63cf1db7459b"),
                "B-203",
                "2",
                "cabine",
                "estacao",
                1,
                ["isolamento_acustico", "tomada"],
            ),
            (
                uuid.UUID("480a2ec6-4e19-4a78-827a-feae0fac9df9"),
                "B-204",
                "2",
                "cabine",
                "estacao",
                1,
                ["isolamento_acustico", "monitor"],
            ),
            # Salas de Reunião (capacity > 1)
            (
                uuid.UUID("66dc1d45-1a11-4281-97c4-b2d70774cb47"),
                "SALA-INICIAL",
                "1",
                "reuniao",
                "sala",
                4,
                ["tv_4k", "whiteboard"],
            ),
            (
                uuid.UUID("89f71b5c-a59b-4a13-aafa-1b3cf5226dd3"),
                "SALA-INOVACAO",
                "1",
                "reuniao",
                "sala",
                6,
                ["videoconferencia", "tv_4k", "whiteboard"],
            ),
            (
                uuid.UUID("6ef72470-2011-4f32-84c8-aab0fd1370cc"),
                "SALA-DIRETORIA",
                "2",
                "executiva",
                "sala",
                10,
                ["videoconferencia_zoom", "projetor", "sistema_audio"],
            ),
        ]
        created_workspaces = {}
        for ws_id, code, floor, zone, w_type, capacity, resources in workspaces_data:
            existing_ws = await session.scalar(
                select(WorkspaceORM).where(
                    (WorkspaceORM.id == ws_id) | (WorkspaceORM.code == code)
                )
            )
            if not existing_ws:
                ws = WorkspaceORM(
                    id=ws_id,
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

        # 7. Reservas de Teste (ID canônico fixo)
        fixed_booking_id = uuid.UUID("849bd1b4-84e4-429d-b0a9-2c2cda39af2c")
        emp_maria = created_employees["maria.silva@deskflow.com"]
        ws_a101 = created_workspaces["A-101"]
        booking_start = datetime.combine(today + timedelta(days=1), time(9, 0))
        booking_end = booking_start + timedelta(hours=2)

        existing_b = await session.scalar(
            select(BookingORM).where(BookingORM.id == fixed_booking_id)
        )
        if not existing_b:
            test_booking = BookingORM(
                id=fixed_booking_id,
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
                    booking_id=fixed_booking_id,
                    workspace_id=ws_a101.id,
                    day=day_str,
                    slot_index=start_idx + i,
                )
                for i in range(8)  # 2 horas = 8 slots de 15 min
            )
            print("[OK] Reserva de teste canônica PENDING criada para A-101.")

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
