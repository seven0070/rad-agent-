// exportCode.ts — Pure pipeline export (CrewAI Python / YAML / JSON) for the Studio header menu.
// Extracted verbatim from ChatView.handleExportCode (behavior unchanged).

import type { ObjectiveRow, TaskRow } from "../../api";

export type ExportFormat = "python" | "yaml" | "json";

export function exportCode(
  format: ExportFormat,
  objective: ObjectiveRow,
  tasks: TaskRow[],
  verification: unknown,
  modelName: string,
): void {
  let content = "";
  let filename = "";
  let mimeType = "text/plain";

  if (format === "python") {
    filename = `crew_${objective.id.slice(0, 8)}.py`;
    content = `# RAD Studio v2 — Autonomous Multi-Agent Pipeline
# Objective: ${objective.goal}
from rad import Crew, Agent, Task, VerificationGate

crew = Crew(
    name="rad-autonomous-crew",
    goal=${JSON.stringify(objective.goal)},
    model="${modelName}",
    invariants=["filesystem_existence", "schema_validation", "hash_proof"],
)

${tasks
  .map(
    (t, i) => `task_${i + 1} = Task(
    id=${JSON.stringify(t.id)},
    description=${JSON.stringify(t.title || t.text || `Task ${i + 1}`)},
    status=${JSON.stringify(t.status)},
    depends_on=${JSON.stringify(t.depends_on || [])},
)`
  )
  .join("\n\n")}

verification = VerificationGate(
    level=5,
    ground_truth=True,
    strict_checkpoints=True,
)

if __name__ == "__main__":
    crew.kickoff()
`;
  } else if (format === "yaml") {
    filename = `tasks_${objective.id.slice(0, 8)}.yaml`;
    content = `# RAD Studio v2 Task Pipeline Definitions
objective:
  id: "${objective.id}"
  goal: "${objective.goal.replace(/"/g, '\\"')}"
  status: "${objective.status}"
  plan_version: ${objective.plan_version || 1}

tasks:
${tasks
  .map(
    (t, i) => `  - id: "${t.id}"
    title: "${(t.title || t.text || `Task ${i + 1}`).replace(/"/g, '\\"')}"
    status: "${t.status}"
    attempts: ${t.attempts || 1}
    depends_on: ${JSON.stringify(t.depends_on || [])}`
  )
  .join("\n")}

verification:
  level: 5
  status: "${objective.status === "completed" ? "VERIFIED" : "PENDING"}"
`;
  } else {
    filename = `dag_${objective.id.slice(0, 8)}.json`;
    mimeType = "application/json";
    content = JSON.stringify(
      {
        objective,
        tasks,
        verification,
        model: modelName,
        exported_at: new Date().toISOString(),
      },
      null,
      2
    );
  }

  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
