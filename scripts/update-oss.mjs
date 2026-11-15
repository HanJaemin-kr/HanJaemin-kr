// README의 <!-- OSS:START --> ~ <!-- OSS:END --> 사이를
// GitHub Search API 결과(내가 다른 사람 저장소에 올린 PR)로 다시 씁니다.
import { readFileSync, writeFileSync } from "node:fs";

const USER = process.env.GH_USER || "HanJaemin-kr";
const TOKEN = process.env.GITHUB_TOKEN;
const README = "README.md";
// 팀/개인 프로젝트 등 OSS 기여로 보지 않을 저장소 (owner/repo)
const EXCLUDE = (process.env.EXCLUDE_REPOS || "Team-MeU/MeU").split(",").map((s) => s.trim().toLowerCase());

const q = `is:pr author:${USER} -user:${USER} archived:false`;
const headers = { Accept: "application/vnd.github+json", "User-Agent": USER };
if (TOKEN) headers.Authorization = `Bearer ${TOKEN}`;

const items = [];
for (let page = 1; page <= 5; page++) {
  const url = `https://api.github.com/search/issues?q=${encodeURIComponent(q)}&sort=created&order=asc&per_page=100&page=${page}`;
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error(`GitHub API ${res.status}: ${await res.text()}`);
  const data = await res.json();
  items.push(...data.items);
  if (data.items.length < 100) break;
}

const repoOf = (pr) => pr.repository_url.replace("https://api.github.com/repos/", "");
const filtered = items.filter((pr) => !EXCLUDE.includes(repoOf(pr).toLowerCase()));
items.length = 0; items.push(...filtered);

const esc = (s) => s.replace(/\|/g, "\\|").trim();
const rows = items.map((pr) => {
  const repo = repoOf(pr);
  const badge = `https://img.shields.io/github/pulls/detail/state/${repo}/${pr.number}?label=&style=flat-square`;
  return `| [${repo}](https://github.com/${repo}) | [#${pr.number}](${pr.html_url}) ${esc(pr.title)} | <img src="${badge}" alt="status" /> |`;
});

const merged = items.filter((p) => p.pull_request?.merged_at).length;
const repos = new Set(items.map((p) => p.repository_url)).size;

const table = [
  `![PRs](https://img.shields.io/badge/PRs-${items.length}-22C55E?style=flat-square) ![Merged](https://img.shields.io/badge/Merged-${merged}-16A34A?style=flat-square) ![Repos](https://img.shields.io/badge/Repos-${repos}-065F46?style=flat-square)`,
  "",
  "| Project | Pull Request | Status |",
  "|---|---|---|",
  ...rows,
  "",
  `<sub>Last updated: ${new Date().toISOString().slice(0, 10)} (auto)</sub>`,
].join("\n");

const md = readFileSync(README, "utf8");
const re = /(<!-- OSS:START -->)[\s\S]*?(<!-- OSS:END -->)/;
if (!re.test(md)) throw new Error("OSS markers not found in README.md");
const next = md.replace(re, `$1\n${table}\n$2`);
if (next !== md) {
  writeFileSync(README, next);
  console.log(`Updated: ${items.length} PRs (${merged} merged, ${repos} repos)`);
} else console.log("No changes");
