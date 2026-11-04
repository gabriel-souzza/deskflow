import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AuthGuard } from "../components/auth-guard";
import * as authHook from "../hooks/use-auth";

const mockReplace = vi.fn();
let currentPathname = "/";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
    push: vi.fn(),
  }),
  usePathname: () => currentPathname,
}));

describe("AuthGuard Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    currentPathname = "/";
  });

  it("redirects unauthenticated users to /login when on a protected page", () => {
    currentPathname = "/";
    vi.spyOn(authHook, "useCurrentUser").mockReturnValue({
      data: null,
      isLoading: false,
    } as any);

    render(
      <AuthGuard>
        <div>Conteúdo Protegido</div>
      </AuthGuard>
    );

    expect(mockReplace).toHaveBeenCalledWith("/login");
  });

  it("renders protected content when user is authenticated", () => {
    currentPathname = "/";
    vi.spyOn(authHook, "useCurrentUser").mockReturnValue({
      data: { id: "123", name: "Maria" } as any,
      isLoading: false,
    } as any);

    render(
      <AuthGuard>
        <div>Conteúdo Protegido</div>
      </AuthGuard>
    );

    expect(screen.getByText("Conteúdo Protegido")).toBeInTheDocument();
    expect(mockReplace).not.toHaveBeenCalled();
  });

  it("redirects authenticated user away from /login to /", () => {
    currentPathname = "/login";
    vi.spyOn(authHook, "useCurrentUser").mockReturnValue({
      data: { id: "123", name: "Maria" } as any,
      isLoading: false,
    } as any);

    render(
      <AuthGuard>
        <div>Tela de Login</div>
      </AuthGuard>
    );

    expect(mockReplace).toHaveBeenCalledWith("/");
  });

  it("renders login form when unauthenticated user visits /login", () => {
    currentPathname = "/login";
    vi.spyOn(authHook, "useCurrentUser").mockReturnValue({
      data: null,
      isLoading: false,
    } as any);

    render(
      <AuthGuard>
        <div>Tela de Login</div>
      </AuthGuard>
    );

    expect(screen.getByText("Tela de Login")).toBeInTheDocument();
    expect(mockReplace).not.toHaveBeenCalled();
  });
});

