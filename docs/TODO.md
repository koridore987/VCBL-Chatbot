# TODO Dashboard

_Last updated: 2025-10-16T01:08:51.569Z_

## Overview

| Scope | TODOs | Owners |
| --- | ---: | --- |
| scripts | 12 | ?:\(([^ |

## Detailed List

### scripts

- [ ] `scripts/generate-todo-report.mjs:3` — -style annotations and generates docs/TODO.md.
  > * Scans the repository for TODO-style annotations and generates docs/TODO.md.
- [ ] `scripts/generate-todo-report.mjs:9` — .md');
  > const outputPath = path.join(repoRoot, 'docs', 'TODO.md');
- [ ] `scripts/generate-todo-report.mjs:58` — _REGEX =
  > const TODO_REGEX =
- [ ] `scripts/generate-todo-report.mjs:59` — ]+)\)|\[([^\]]+)\])?\s*:?\s*(.*?)(?:\s*(?:https?:\/\/\S+))?$/i; _(owner: ?:\(([^)_
  > /TODO(?:\(([^)]+)\)|\[([^\]]+)\])?\s*:?\s*(.*?)(?:\s*(?:https?:\/\/\S+))?$/i;
- [ ] `scripts/generate-todo-report.mjs:101` — '))) continue;
  > if (!lines.some((line) => line.includes('TODO'))) continue;
- [ ] `scripts/generate-todo-report.mjs:104` — ')) return;
  > if (!line.includes('TODO')) return;
- [ ] `scripts/generate-todo-report.mjs:106` — _REGEX);
  > const match = line.match(TODO_REGEX);
- [ ] `scripts/generate-todo-report.mjs:140` — Dashboard');
  > lines.push('# TODO Dashboard');
- [ ] `scripts/generate-todo-report.mjs:146` — markers found in the codebase.');
  > lines.push('Everything looks clear! No TODO markers found in the codebase.');
- [ ] `scripts/generate-todo-report.mjs:168` — s | Owners |');
  > lines.push('| Scope | TODOs | Owners |');
- [ ] `scripts/generate-todo-report.mjs:218` — report with ${todos.length} item(s) → ${path.relative(
  > `Generated TODO report with ${todos.length} item(s) → ${path.relative(
- [ ] `scripts/generate-todo-report.mjs:226` — report:', error);
  > console.error('Failed to generate TODO report:', error);

