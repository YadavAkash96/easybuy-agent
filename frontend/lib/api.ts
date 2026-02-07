const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || "Request failed");
  }
  return resp.json() as Promise<T>;
}
