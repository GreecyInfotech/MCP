const API_BASE = import.meta.env.VITE_API_URL || "/api";

export interface Agent {
  id: string;
  name: string;
  description: string;
}

export interface AgentResponse {
  agent: string;
  answer: string;
  actions_taken: string[];
  metadata: Record<string, unknown>;
}

export async function fetchAgents(): Promise<Agent[]> {
  const res = await fetch(`${API_BASE}/agents`);
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}

export async function runAgent(agentId: string, query: string): Promise<AgentResponse> {
  const res = await fetch(`${API_BASE}/agents/${agentId}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Agent request failed");
  }
  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchServices(): Promise<Record<string, string>> {
  const res = await fetch(`${API_BASE}/services`);
  if (!res.ok) throw new Error("Failed to fetch services");
  return res.json();
}

export async function fetchModels(): Promise<unknown[]> {
  const res = await fetch(`${API_BASE}/models`);
  if (!res.ok) return [];
  return res.json();
}
