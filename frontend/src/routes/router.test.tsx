import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { SessionProvider } from "../features/auth/session";
import { createAppRouter } from "./router";

describe("app router", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.history.pushState({}, "", "/");
  });

  it("redirects unauthenticated protected routes to sign in", async () => {
    window.history.pushState({}, "", "/dashboard");

    renderWithSession();

    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });

  it("renders the workspace picker after development sign in", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/signin");

    renderWithSession();

    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(await screen.findByRole("heading", { name: "Choose a workspace" })).toBeInTheDocument();
  });

  it("renders the dashboard shell after selecting a workspace", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/signin");

    renderWithSession();

    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(await screen.findByRole("button", { name: /northwind utilities/i }));

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Program intelligence" })).toBeInTheDocument();
  });

  it("keeps mobile navigation operable", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("gridlens.devSession", "signed-in");
    window.localStorage.setItem("gridlens.devWorkspace", "northwind");
    window.history.pushState({}, "", "/dashboard");

    renderWithSession();

    await user.click(await screen.findByRole("button", { name: "Open navigation" }));
    await user.click(screen.getByRole("link", { name: /Assistant/ }));

    expect(await screen.findByRole("heading", { name: "Assistant" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Evidence-grounded assistant" })).toBeInTheDocument();
  });
});

function renderWithSession() {
  return render(
    <SessionProvider>
      <RouterProvider router={createAppRouter()} />
    </SessionProvider>
  );
}
