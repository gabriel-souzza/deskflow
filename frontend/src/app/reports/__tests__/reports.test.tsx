import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ReportsPage from "../page";
import { Employee, EmployeeRole } from "@/domain/entities/employee";

const mockUseCurrentUser = vi.fn();
const mockUseUtilizationReport = vi.fn();

vi.mock("@/features/auth/hooks/use-auth", () => ({
  useCurrentUser: () => mockUseCurrentUser(),
}));

vi.mock("@/features/reports/hooks/use-reports", () => ({
  useUtilizationReport: (...args: unknown[]) => mockUseUtilizationReport(...args),
  downloadReport: vi.fn(),
}));

describe("ReportsPage Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders restricted access view when user is not an administrator", () => {
    mockUseCurrentUser.mockReturnValue({
      data: new Employee({
        id: "emp-1",
        name: "Ana Silva",
        email: "ana@deskflow.com",
        role: EmployeeRole.EMPLOYEE,
        isEligibleForBooking: true,
      }),
      isLoading: false,
    });
    mockUseUtilizationReport.mockReturnValue({
      data: undefined,
      isLoading: false,
    });

    render(<ReportsPage />);

    expect(screen.getByText(/Acesso Restrito ao Administrador/i)).toBeInTheDocument();
  });

  it("renders report dashboard safely without throwing when report is undefined or null", () => {
    mockUseCurrentUser.mockReturnValue({
      data: new Employee({
        id: "adm-1",
        name: "Carlos Mendes",
        email: "carlos.admin@deskflow.com",
        role: EmployeeRole.ADMIN,
        isEligibleForBooking: true,
      }),
      isLoading: false,
    });
    mockUseUtilizationReport.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    render(<ReportsPage />);

    expect(screen.getByText(/Dashboard de Utilização e Rateio/i)).toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByText(/0 reservas confirmadas/i)).toBeInTheDocument();
  });

  it("renders correctly with nested summary data", () => {
    mockUseCurrentUser.mockReturnValue({
      data: new Employee({
        id: "adm-1",
        name: "Carlos Mendes",
        email: "carlos.admin@deskflow.com",
        role: EmployeeRole.ADMIN,
        isEligibleForBooking: true,
      }),
      isLoading: false,
    });
    mockUseUtilizationReport.mockReturnValue({
      data: {
        summary: {
          utilization_rate: 0.75,
          no_show_rate: 0.05,
          bookings_confirmed: 12,
          bookings_expired: 1,
          total_stations: 20,
          total_meeting_rooms: 4,
        },
        by_floor: {
          "1": { occupied_slot_seats: 16 },
        },
        by_zone: {},
        cost_center_hours: {
          "cc-1234567890": 8.5,
        },
      },
      isLoading: false,
      error: null,
    });

    render(<ReportsPage />);

    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText(/12 reservas confirmadas/i)).toBeInTheDocument();
    expect(screen.getByText("5.0%")).toBeInTheDocument();
    expect(screen.getByText("20")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("4h")).toBeInTheDocument();
    expect(screen.getByText("8.5h")).toBeInTheDocument();
  });
});
