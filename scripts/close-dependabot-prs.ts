export { };

const access_token = process.env.GH_APP_ACCESS_TOKEN;
if (!access_token) {
  throw new Error("GH_APP_ACCESS_TOKEN is not set");
}

const OWNER = "microsoft";
const REPO = "graphrag";
const DEPENDABOT_LOGIN = "dependabot[bot]";

const headers = {
  Authorization: `Bearer ${access_token}`,
  Accept: "application/vnd.github+json",
  "X-GitHub-Api-Version": "2026-03-10",
};

type PullRequest = {
  number: number;
  title: string;
  user: { login: string } | null;
};

const dependabotPrs: PullRequest[] = [];
for (let page = 1; ; page++) {
  const res = await fetch(
    `https://api.github.com/repos/${OWNER}/${REPO}/pulls?state=open&per_page=100&page=${page}`,
    { headers },
  );

  if (!res.ok) {
    throw new Error(
      `Failed to list pull requests. ${res.status} - ${res.statusText}`,
    );
  }

  const pulls = (await res.json()) as PullRequest[];
  if (pulls.length === 0) {
    break;
  }

  dependabotPrs.push(
    ...pulls.filter((pr) => pr.user?.login === DEPENDABOT_LOGIN),
  );
}

if (dependabotPrs.length === 0) {
  console.log("No open dependabot pull requests found.");
} else {
  for (const pr of dependabotPrs) {
    const res = await fetch(
      `https://api.github.com/repos/${OWNER}/${REPO}/pulls/${pr.number}`,
      {
        method: "PATCH",
        headers,
        body: JSON.stringify({ state: "closed" }),
      },
    );

    if (!res.ok) {
      throw new Error(
        `Failed to close PR #${pr.number}. ${res.status} - ${res.statusText}`,
      );
    }

    console.log(`Closed PR #${pr.number}: ${pr.title}`);
  }

  console.log(`Closed ${dependabotPrs.length} dependabot pull request(s).`);
}
