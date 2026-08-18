export { };

const access_token = process.env.GH_APP_ACCESS_TOKEN;
if (!access_token) {
  throw new Error("GH_APP_ACCESS_TOKEN is not set");
}

const OWNER = "microsoft";
const REPO = "graphrag";

const body = {
  title: "Update Dependencies Sweep",
  body: "Update dependencies to the latest versions. This is an automated sweep to ensure that all dependencies are up-to-date.",
  labels: ["dependencies"],
  assignees: ["copilot-swe-agent[bot]"],
  agent_assignment: {
    target_repo: `${OWNER}/${REPO}`,
    base_branch: "main",
    custom_instructions:
      "Use the update-deps skill to update all dependencies to their latest versions.",
    model: "claude-opus-4.8",
  },
};

const res = await fetch(
  `https://api.github.com/repos/${OWNER}/${REPO}/issues`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${access_token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2026-03-10",
    },
    body: JSON.stringify(body),
  },
);

if (!res.ok) {
  throw new Error(`Failed to open issue. ${res.status} - ${res.statusText}`);
}

const data = await res.json();

console.log(JSON.stringify(data, null, 2));
