import { useEffect, useState } from "react";
import AgentPanel from "./AgentPanel";
import { checkHealth, fetchAgents, fetchModels, fetchServices, type Agent } from "./api";
import "./App.css";

export default function App() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>("backlog");
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [services, setServices] = useState<Record<string, string>>({});
  const [models, setModels] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function init() {
      try {
        const [agentList, serviceList, modelList, isHealthy] = await Promise.all([
          fetchAgents(),
          fetchServices(),
          fetchModels(),
          checkHealth(),
        ]);
        setAgents(agentList);
        setServices(serviceList);
        setModels(modelList);
        setHealthy(isHealthy);
        if (agentList.length > 0) setSelectedAgent(agentList[0].id);
      } catch {
        setHealthy(false);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  const currentAgent = agents.find((a) => a.id === selectedAgent);

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <div className="logo">AI</div>
          <div>
            <h1>Enterprise AI Platform</h1>
            <p className="subtitle">Vertex AI · Cloud Run · BigQuery</p>
          </div>
        </div>
        <div className={`status-badge ${healthy ? "healthy" : "unhealthy"}`}>
          <span className="status-dot" />
          {healthy === null ? "Checking..." : healthy ? "Gateway Online" : "Gateway Offline"}
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <section className="sidebar-section">
            <h3>Agents</h3>
            <nav className="agent-nav">
              {agents.map((agent) => (
                <button
                  key={agent.id}
                  className={`agent-nav-item ${selectedAgent === agent.id ? "active" : ""}`}
                  onClick={() => setSelectedAgent(agent.id)}
                >
                  <span className="agent-icon">{agent.id[0].toUpperCase()}</span>
                  <div>
                    <div className="agent-name">{agent.name}</div>
                    <div className="agent-desc">{agent.description.slice(0, 50)}...</div>
                  </div>
                </button>
              ))}
            </nav>
          </section>

          <section className="sidebar-section">
            <h3>Cloud Run Services</h3>
            <ul className="mcp-list">
              {Object.entries(services).map(([name, url]) => (
                <li key={name}>
                  <span className="mcp-name">{name}</span>
                  <span className="mcp-cmd">{url.replace("http://localhost:", ":")}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="sidebar-section">
            <h3>Vertex AI Models</h3>
            <ul className="mcp-list">
              {(models as { name: string; status: string }[]).map((m) => (
                <li key={m.name}>
                  <span className="mcp-name">{m.name}</span>
                  <span className="mcp-cmd">{m.status}</span>
                </li>
              ))}
            </ul>
          </section>
        </aside>

        <main className="main">
          {loading ? (
            <div className="loading">Loading platform...</div>
          ) : currentAgent ? (
            <AgentPanel agent={currentAgent} />
          ) : (
            <div className="loading">Start ai-gateway and agent-service to begin.</div>
          )}
        </main>
      </div>
    </div>
  );
}
