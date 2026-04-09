import Link from "next/link";
import type { Route } from "next";
import { apiGet } from "../../../lib/api";
import { Reveal } from "../../../components/Reveal";

type AgentSpec = {
  id: string;
  name: string;
  category: string;
  tags: string[];
  summary: string;
  description: string;
  inputs: Array<{ key: string; label: string; type: string; required: boolean }>;
  outputs: string[];
  helps_with: string[];
};

export default async function AgentDetails({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const spec = await apiGet<AgentSpec>(`/agents/${id}`);

  return (
    <div className="grid" style={{ gap: 14 }}>
      <Reveal>
        <section className="hero-strip hero-premium">
          <p className="kicker">{spec.category}</p>
          <h1>{spec.name}</h1>
          <p>{spec.description}</p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {spec.helps_with.map((h) => (
              <span className="badge" key={h}>{h}</span>
            ))}
            {spec.tags.map((t) => (
              <span className="badge" key={t}>#{t}</span>
            ))}
          </div>
        </section>
      </Reveal>

      <Reveal>
        <section className="card workspace-form">
          <h3>Required Inputs</h3>
          <table className="table">
            <thead><tr><th>Field</th><th>Type</th><th>Required</th></tr></thead>
            <tbody>
              {spec.inputs.map((f) => (
                <tr key={f.key}><td>{f.label}</td><td>{f.type}</td><td>{f.required ? "Yes" : "No"}</td></tr>
              ))}
            </tbody>
          </table>
        </section>
      </Reveal>

      <Reveal>
        <section className="card workspace-analysis">
          <h3>Expected Outputs</h3>
          <ul>
            {spec.outputs.map((o) => (
              <li key={o}>{o}</li>
            ))}
          </ul>
        </section>
      </Reveal>

      <Reveal>
        <Link className="btn btn-subtle" href={`/run/${spec.id}` as Route}>Open Agent Console</Link>
      </Reveal>
    </div>
  );
}
