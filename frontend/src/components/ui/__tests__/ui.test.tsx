import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Badge } from "../badge";
import { Button } from "../button";

describe("UI Components (Vitest + React Testing Library)", () => {
  it("renders Button and handles click events", async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Reservar Estação</Button>);

    const button = screen.getByRole("button", { name: /reservar estação/i });
    expect(button).toBeInTheDocument();

    await userEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("renders disabled Button and does not trigger click", async () => {
    const handleClick = vi.fn();
    render(
      <Button disabled onClick={handleClick}>
        Indisponível
      </Button>
    );

    const button = screen.getByRole("button", { name: /indisponível/i });
    expect(button).toBeDisabled();

    await userEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it("renders Badge with correct variant styling", () => {
    const { rerender } = render(<Badge variant="success">CONFIRMED</Badge>);
    expect(screen.getByText("CONFIRMED")).toHaveClass("bg-emerald-600");

    rerender(<Badge variant="destructive">CANCELLED</Badge>);
    expect(screen.getByText("CANCELLED")).toHaveClass("bg-red-600");

    rerender(<Badge variant="warning">PENDING</Badge>);
    expect(screen.getByText("PENDING")).toHaveClass("bg-amber-500");
  });
});

