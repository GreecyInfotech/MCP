import { useState } from "react";
import { runAgent, type Agent, type AgentResponse } from "./api";
import "./AgentPanel.css";

interface Props {
  agent: Agent;
}

export default function AgentPanel({ agent }: Props) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await runAgent(agent.id, query);
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const suggestions: Record<string, string[]> = {
    backlog: [
      "Show me all open stories in the current sprint",
      "What's our average sprint velocity?",
      "Create a story for user authentication improvements",
    ],
    support: [
      "A customer can't reset their password. Help me triage.",
      "Search the knowledge base for SSO configuration issues",
      "Draft a response for a dashboard loading issue",
    ],
    incident: [
      "Query errors in the last hour with severity >= 3",
      "Create a P1 incident for API latency spike",
      "What's the blast radius of a database connection pool exhaustion?",
    ],
    reporting: [
      "Generate an executive summary report",
      "Show incident trends for the last 30 days",
      "What's our support SLA compliance this week?",
    ],
    code: [
      "Review open PRs in our main repository",
      "Search for authentication middleware implementations",
      "Find documentation about our API design patterns",
    ],
  };

  return (
    <div className="agent-panel">
      <div className="agent-header">
        <h2>{agent.name}</h2>
        <p>{agent.description}</p>
      </div>

      <div className="suggestions">
        {suggestions[agent.id]?.map((s) => (
          <button key={s} className="suggestion-chip" onClick={() => setQuery(s)}>
            {s}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="query-form">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={`Ask the ${agent.name}...`}
          rows={3}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? "Running..." : "Run Agent"}
        </button>
      </form>

      {error && <div className="error-box">{error}</div>}

      {response && (
        <div className="response-box">
          <h3>Response</h3>
          <div className="answer">{response.answer}</div>
          {response.actions_taken.length > 0 && (
            <details>
              <summary>Actions taken ({response.actions_taken.length})</summary>
              <ul>
                {response.actions_taken.map((action, i) => (
                  <li key={i}><code>{action}</code></li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
