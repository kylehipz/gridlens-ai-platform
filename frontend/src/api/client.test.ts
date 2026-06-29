import { describe, expect, it, vi } from "vitest";
import { ApiError, createApiClient } from "./client";

describe("api client", () => {
  it("sends tenant and auth headers with JSON requests", async () => {
    const fetchImpl = vi.fn<typeof fetch>(async () => Response.json({ ok: true }));
    const client = createApiClient({
      baseUrl: "http://gridlens.test",
      fetchImpl,
      getAccessToken: () => "dev-token",
      getWorkspaceId: () => "northwind"
    });

    await client.post("/datasets", { name: "Bills" });

    const [, init] = fetchImpl.mock.calls[0];
    const headers = init?.headers as Headers;
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://gridlens.test/datasets",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ name: "Bills" }) })
    );
    expect(headers.get("Authorization")).toBe("Bearer dev-token");
    expect(headers.get("X-GridLens-Workspace")).toBe("northwind");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("normalizes JSON API errors", async () => {
    const fetchImpl = vi.fn<typeof fetch>(async () =>
      Response.json({ message: "Tenant access denied", code: "tenant_denied" }, { status: 403 })
    );
    const client = createApiClient({ fetchImpl });

    await expect(client.get("/audit")).rejects.toMatchObject({
      name: "ApiError",
      status: 403,
      code: "tenant_denied",
      message: "Tenant access denied"
    } satisfies Partial<ApiError>);
  });
});
