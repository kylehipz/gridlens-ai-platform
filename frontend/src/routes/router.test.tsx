import { render, screen } from "@testing-library/react";
import { RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRouter } from "./router";

describe("app router", () => {
  it("redirects unknown entry points to sign in", async () => {
    window.history.pushState({}, "", "/dashboard");

    render(<RouterProvider router={createAppRouter()} />);

    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });
});
