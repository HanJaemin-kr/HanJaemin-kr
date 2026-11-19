import { readFileSync, writeFileSync } from 'node:fs';

const user = process.env.GH_USER || 'HanJaemin-kr';
if (!/^[a-z0-9-]+$/i.test(user)) throw new Error('Invalid GH_USER');
const excluded = ['Team-MeU', 'FocuStudy', 'uiai-lab', 'Ulsan-Industrial-AI-Lab'];
const query = ['is:public', 'is:pr', 'author:' + user, '-user:' + user,
  ...excluded.map(name => '-org:' + name), 'archived:false'].join(' ');
const searchLink = 'https://github.com/search?type=pullrequests&s=created&o=desc&q=' + encodeURIComponent(query);
const reposLink = 'https://github.com/' + user + '?tab=repositories&type=source&sort=created';
const headers = { Accept: 'application/vnd.github+json', 'User-Agent': 'profile-readme-updater' };
if (process.env.GITHUB_TOKEN) headers.Authorization = 'Bearer ' + process.env.GITHUB_TOKEN;

async function get(endpoint) {
  const res = await fetch('https://api.github.com' + endpoint, { headers, signal: AbortSignal.timeout(20_000) });
  if (!res.ok) throw new Error('GitHub API returned HTTP ' + res.status);
  return res.json();
}

// Escape Markdown syntax and HTML, including table separators in PR titles.
const text = value => String(value || '').replace(/\s+/g, ' ').trim()
  .replace(/[&<>\\|`*_[\]~!]/g, c => '&#' + c.codePointAt(0) + ';')
  .replace(/@(?=[a-z0-9-])/gi, '&#64;');
const validName = /^[a-z0-9_.-]+\/[a-z0-9_.-]+$/i;
const prMap = new Map();
for (let page = 1; page <= 10; page++) {
  const data = await get('/search/issues?q=' + encodeURIComponent(query) + '&sort=created&order=desc&per_page=100&page=' + page);
  if (data.incomplete_results !== false || !Array.isArray(data.items) || data.total_count > 1000) {
    throw new Error('Incomplete PR search; README left unchanged');
  }
  for (const pr of data.items) {
    const name = pr.repository_url?.replace(/^https:\/\/api\.github\.com\/repos\//, '');
    if (!validName.test(name || '') || !Number.isSafeInteger(pr.number) || !pr.pull_request) {
      throw new Error('Unexpected PR payload; README left unchanged');
    }
    const owner = name.split('/')[0].toLowerCase();
    if ([user, ...excluded].some(n => n.toLowerCase() === owner)) continue;
    const state = pr.pull_request.merged_at ? 'Merged' : pr.state === 'open' ? (pr.draft ? 'Draft' : 'Open') : null;
    if (!state) continue;
    prMap.set(name.toLowerCase() + '#' + pr.number, { name, number: pr.number, state, title: pr.title });
  }
  if (data.items.length < 100) break;
}
const prs = [...prMap.values()];
const repoList = [];
for (let page = 1; repoList.length < 6; page++) {
  const data = await get('/users/' + user + '/repos?type=owner&sort=created&direction=desc&per_page=100&page=' + page);
  if (!Array.isArray(data)) throw new Error('Unexpected repository list; README left unchanged');
  for (const repo of data) {
    if (repo.private !== false || repo.fork !== false || repo.archived !== false) continue;
    if (!validName.test(repo.full_name || '') || repo.owner?.login?.toLowerCase() !== user.toLowerCase()) continue;
    if (repo.name.toLowerCase() === user.toLowerCase()) continue;
    repoList.push(repo);
    if (repoList.length === 6) break;
  }
  if (data.length < 100) break;
}

const merged = prs.filter(pr => pr.state === 'Merged').length;
const countRepos = new Set(prs.map(pr => pr.name.toLowerCase())).size;
const badge = (label, count, color) => '![' + label + '](https://img.shields.io/badge/' + label + '-' + count + '-' + color + '?style=flat-square)';
const oss = [badge('PRs', prs.length, '22C55E') + ' ' + badge('Merged', merged, '16A34A') + ' ' + badge('Repos', countRepos, '065F46'), '',
  ...(prs.length ? ['| Project | Pull Request | Status |', '|---|---|---|', ...prs.map(pr => {
    const url = 'https://github.com/' + pr.name;
    return '| [' + pr.name + '](' + url + ') | [#' + pr.number + '](' + url + '/pull/' + pr.number + ') ' + text(pr.title) + ' | ' + pr.state + ' |';
  })] : ['아직 표시할 공개 오픈소스 PR이 없습니다.']), '', '[GitHub에서 최신 공개 PR 보기](' + searchLink + ')'];
const projects = ['개인 계정에서 공개한 원본 저장소를 생성일 순으로 표시합니다. 포크와 아카이브는 제외합니다.', '',
  ...(repoList.length ? ['| Project | Description |', '|---|---|', ...repoList.map(repo => '| [' + repo.name + '](https://github.com/' + repo.full_name + ') | ' + (text(repo.description) || text(repo.language) || '없음') + ' |')]
    : ['아직 표시할 공개 프로젝트가 없습니다.']), '', '[GitHub에서 최신 공개 저장소 보기](' + reposLink + ')'];

function replaceBlock(md, label, lines) {
  const start = '<!-- ' + label + ':START -->';
  const end = '<!-- ' + label + ':END -->';
  const left = md.indexOf(start);
  const right = md.indexOf(end);
  if (left < 0 || right < left || md.indexOf(start, left + start.length) >= 0 || md.indexOf(end, right + end.length) >= 0) {
    throw new Error('Expected exactly one ordered pair of ' + label + ' markers');
  }
  return md.slice(0, left + start.length) + '\n' + lines.join('\n') + '\n' + md.slice(right);
}
const md = readFileSync('README.md', 'utf8');
const next = replaceBlock(replaceBlock(md, 'OSS', oss), 'PUBLIC-REPOS', projects);
if (next !== md) writeFileSync('README.md', next);
console.log((next === md ? 'Unchanged: ' : 'Updated: ') + prs.length + ' PRs (' + merged + ' merged), ' + repoList.length + ' public projects');
