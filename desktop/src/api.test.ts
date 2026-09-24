/**
 * Smoke/logic tests for the typed HTTP client (src/api.ts).
 *
 * api.ts has no Tauri dependency at all — it is a pure fetch client — so
 * these tests cover the non-Tauri/fallback path with a stubbed global fetch.
 * No `@tauri-apps/api` mock is needed here (and none is registered).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, RadClient } from "./api";

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Service Unavailable",
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

describe("RadClient — non-Tauri HTTP fallback path", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("strips a trailing slash from the base URL", () => {
    const c = new RadClient("http://127.0.0.1:7331/", "tok");
    expect(c.base).toBe("http://127.0.0.1:7331");
    expect(c.token).toBe("tok");
  });

  it("health() issues an authenticated GET and parses the body", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ ok: true, version: "0.1.0" }));

    const c = new RadClient("http://127.0.0.1:7331", "secret-token");
    const res = await c.health();

    expect(res).toEqual({ ok: true, version: "0.1.0" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://127.0.0.1:7331/v1/health");
    expect(init?.method).toBe("GET");
    expect(init?.headers).toMatchObject({ Authorization: "Bearer secret-token" });
    expect(init?.body).toBeUndefined();
  });

  it("chat() POSTs a JSON body", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ reply: "pong", via: "http" }));

    const c = new RadClient("http://127.0.0.1:7331", "t");
    const res = await c.chat("ping");

    expect(res.reply).toBe("pong");
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://127.0.0.1:7331/v1/chat");
    expect(init?.method).toBe("POST");
    expect(init?.headers).toMatchObject({ "Content-Type": "application/json" });
    expect(init?.body).toBe(JSON.stringify({ text: "ping" }));
  });

  it("throws ApiError with the HTTP status on non-OK responses", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ error: "nope" }, 503));

    const c = new RadClient("http://127.0.0.1:7331", "t");
    await expect(c.status()).rejects.toBeInstanceOf(ApiError);
    await expect(c.status()).rejects.toMatchObject({ status: 503, message: "nope" });
  });
});
