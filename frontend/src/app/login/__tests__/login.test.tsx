import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import LoginPage from "../page";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock useLogin hook
const mockMutateAsync = vi.fn();
let mockIsPending = false;

vi.mock("@/features/auth/hooks/use-auth", () => ({
  useLogin: () => ({
    mutateAsync: mockMutateAsync,
    isPending: mockIsPending,
  }),
}));

describe("LoginPage Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsPending = false;
    localStorage.clear();
  });

  it("renders branding, login inputs and quick demo buttons", () => {
    render(<LoginPage />);

    expect(screen.getAllByText(/DeskFlow/i).length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/E-mail Corporativo/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Senha de Acesso/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Acessar Plataforma/i })).toBeInTheDocument();
    expect(screen.getByText(/Ana Silva/i)).toBeInTheDocument();
    expect(screen.getByText(/Carlos Mendes/i)).toBeInTheDocument();
  });

  it("toggles password visibility between password and text", () => {
    render(<LoginPage />);

    const passwordInput = screen.getByLabelText(/Senha de Acesso/i);
    expect(passwordInput).toHaveAttribute("type", "password");

    const toggleButton = screen.getByRole("button", { name: /Alternar visibilidade da senha/i });
    fireEvent.click(toggleButton);

    expect(passwordInput).toHaveAttribute("type", "text");

    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute("type", "password");
  });

  it("auto-fills credentials when clicking a quick demo persona", () => {
    render(<LoginPage />);

    const anaButton = screen.getByText(/Ana Silva/i).closest("button")!;
    fireEvent.click(anaButton);

    const emailInput = screen.getByLabelText(/E-mail Corporativo/i) as HTMLInputElement;
    const passwordInput = screen.getByLabelText(/Senha de Acesso/i) as HTMLInputElement;

    expect(emailInput.value).toBe("ana.silva@deskflow.com");
    expect(passwordInput.value).toBe("Colab123456!");
  });

  it("submits the form and navigates on successful login", async () => {
    mockMutateAsync.mockResolvedValueOnce({ access_token: "token-123" });

    render(<LoginPage />);

    const emailInput = screen.getByLabelText(/E-mail Corporativo/i);
    const passwordInput = screen.getByLabelText(/Senha de Acesso/i);
    const submitButton = screen.getByRole("button", { name: /Acessar Plataforma/i });

    fireEvent.change(emailInput, { target: { value: "user@test.com" } });
    fireEvent.change(passwordInput, { target: { value: "secret123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        username: "user@test.com",
        password: "secret123",
      });
      expect(mockPush).toHaveBeenCalledWith("/");
    });
  });

  it("displays an error alert when login fails", async () => {
    mockMutateAsync.mockRejectedValueOnce(new Error("Credenciais inválidas"));

    render(<LoginPage />);

    const emailInput = screen.getByLabelText(/E-mail Corporativo/i);
    const passwordInput = screen.getByLabelText(/Senha de Acesso/i);
    const submitButton = screen.getByRole("button", { name: /Acessar Plataforma/i });

    fireEvent.change(emailInput, { target: { value: "wrong@test.com" } });
    fireEvent.change(passwordInput, { target: { value: "wrongpass" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Credenciais inválidas/i)).toBeInTheDocument();
    });
  });
});

