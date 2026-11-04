import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Navbar } from "../navbar";
import * as authHook from "@/features/auth/hooks/use-auth";
import { Employee, EmployeeRole } from "@/domain/entities/employee";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

describe("Navbar Component (React Testing Library)", () => {
  it("renders brand logo and public navigation links", () => {
    vi.spyOn(authHook, "useCurrentUser").mockReturnValue({
      data: undefined,
      isLoading: false,
    } as any);
    vi.spyOn(authHook, "useLogout").mockReturnValue(vi.fn());

    render(<Navbar />);

    expect(screen.getByText("DeskFlow")).toBeInTheDocument();
    expect(screen.getByText("Espaços")).toBeInTheDocument();
    expect(screen.getByText("Minhas Reservas")).toBeInTheDocument();
    expect(screen.getByText("Fila de Espera")).toBeInTheDocument();
    expect(screen.getByText("Relatórios")).toBeInTheDocument();
    expect(screen.queryByText("Administração")).not.toBeInTheDocument();
  });

  it("renders admin link and employee badge for admin user", () => {
    const adminUser = new Employee({
      id: "admin-1",
      name: "Carlos Admin",
      email: "carlos@deskflow.com",
      role: EmployeeRole.ADMIN,
      costCenterId: "cc-1",
      costCenterName: "Engenharia de Software",
      isEligibleForBooking: true,
    });

    vi.spyOn(authHook, "useCurrentUser").mockReturnValue({
      data: adminUser,
      isLoading: false,
    } as any);
    vi.spyOn(authHook, "useLogout").mockReturnValue(vi.fn());

    render(<Navbar />);

    expect(screen.getByText("Carlos Admin")).toBeInTheDocument();
    expect(screen.getByText(/Engenharia de Software/)).toBeInTheDocument();
    expect(screen.getByText("ADMIN")).toBeInTheDocument();
    expect(screen.getByText("Administração")).toBeInTheDocument();
  });
});
