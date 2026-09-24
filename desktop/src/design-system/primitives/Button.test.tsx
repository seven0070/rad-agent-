// @vitest-environment jsdom
/**
 * Render + interaction test for the design-system Button primitive.
 * (Chosen over pages/ChatView — small, context-free, no useRad dependency.)
 * Needs a real document; vitest.min.config.ts otherwise runs on node.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Button } from "./Button";

describe("Button primitive", () => {
  it("renders its children with the variant class", () => {
    render(<Button variant="danger">Delete</Button>);
    const btn = screen.getByRole("button", { name: "Delete" }) as HTMLButtonElement;
    expect(btn.className).toContain("btn");
    expect(btn.className).toContain("btn-danger");
    expect(btn.disabled).toBe(false);
  });

  it("fires onClick via user-event", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(
      <Button variant="secondary" onClick={onClick}>
        Run
      </Button>,
    );
    await user.click(screen.getByRole("button", { name: "Run" }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("disables itself while loading", () => {
    render(<Button loading>Save</Button>);
    const btn = screen.getByRole("button", { name: "Save" }) as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });
});
