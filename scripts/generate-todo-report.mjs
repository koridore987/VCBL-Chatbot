#!/usr/bin/env node
/**
 * Scans the repository for TODO-style annotations and generates docs/TODO.md.
 */
import { promises as fs } from 'fs';
import path from 'path';

const repoRoot = process.cwd();
const outputPath = path.join(repoRoot, 'docs', 'TODO.md');

const IGNORED_DIRS = new Set([
  '.git',
  '.hg',
  '.svn',
  'node_modules',
  '.mypy_cache',
  '.pytest_cache',
  '.venv',
  'venv',
  'dist',
  'build',
  '.next',
  '.nuxt',
  '.turbo',
]);

const ALLOWED_EXTENSIONS = new Set([
  '.js',
  '.jsx',
  '.ts',
  '.tsx',
  '.mjs',
  '.cjs',
  '.py',
  '.rb',
  '.java',
  '.kt',
  '.swift',
  '.go',
  '.rs',
  '.cs',
  '.php',
  '.sh',
  '.ps1',
  '.cfg',
  '.conf',
  '.json',
  '.yaml',
  '.yml',
  '.md',
  '.txt',
  '.html',
  '.css',
  '.scss',
  '.less',
]);

const TODO_REGEX =
  /TODO(?:\(([^)]+)\)|\[([^\]]+)\])?\s*:?\s*(.*?)(?:\s*(?:https?:\/\/\S+))?$/i;

const COMMENT_TODO_REGEX =
  /(?:^\s*TODO\b)|(?:\/\/\s*TODO\b)|(?:#\s*TODO\b)|(?:\/\*\s*TODO\b)|(?:\*\s*TODO\b)|(?:<!--\s*TODO\b)|(?:--\s*TODO\b)|(?:;\s*TODO\b)|(?:%\s*TODO\b)/i;

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    if (IGNORED_DIRS.has(entry.name) || entry.name.startsWith('.idea')) continue;

    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      files.push(...(await walk(fullPath)));
      continue;
    }

    if (!shouldInspect(entry.name)) continue;
    files.push(fullPath);
  }

  return files;
}

function shouldInspect(filename) {
  const ext = path.extname(filename).toLowerCase();
  if (!ext) return false;
  return ALLOWED_EXTENSIONS.has(ext);
}

async function collectTodos(files) {
  const todos = [];

  for (const file of files) {
    let content;
    try {
      content = await fs.readFile(file, 'utf8');
    } catch (error) {
      // Skip unreadable files (likely binary or permission issues).
      continue;
    }

    const lines = content.split(/\r?\n/);
    if (!lines.some((line) => line.includes('TODO'))) continue;

    lines.forEach((line, index) => {
      if (!line.includes('TODO')) return;
      if (!COMMENT_TODO_REGEX.test(line)) return;

      const match = line.match(TODO_REGEX);
      if (!match) return;
      const [, ownerParen, ownerBracket, rawDetail] = match;
      const owner = [ownerParen, ownerBracket].find(Boolean) || null;
      const detail = (rawDetail || '').trim() || '(no details provided)';

      todos.push({
        file,
        line: index + 1,
        owner,
        detail,
        snippet: line.trim(),
        scope: resolveScope(file),
      });
    });
  }

  return todos.sort(
    (a, b) =>
      a.scope.localeCompare(b.scope) ||
      a.file.localeCompare(b.file) ||
      a.line - b.line,
  );
}

function resolveScope(fullPath) {
  const relative = path.relative(repoRoot, fullPath).replace(/\\/g, '/');
  const [firstSegment] = relative.split('/');
  if (!firstSegment) return 'root';
  return firstSegment.includes('.') ? 'root' : firstSegment;
}

function buildMarkdown(todos) {
  const lines = [];
  lines.push('# TODO Dashboard');
  lines.push('');
  lines.push(`_Last updated: ${new Date().toISOString()}_`);
  lines.push('');

  if (todos.length === 0) {
    lines.push('Everything looks clear! No TODO markers found in the codebase.');
    lines.push('');
    return lines.join('\n');
  }

  const scopeMap = new Map();
  todos.forEach((todo) => {
    if (!scopeMap.has(todo.scope)) {
      scopeMap.set(todo.scope, {
        count: 0,
        owners: new Set(),
        items: [],
      });
    }
    const entry = scopeMap.get(todo.scope);
    entry.count += 1;
    if (todo.owner) entry.owners.add(todo.owner);
    entry.items.push(todo);
  });

  lines.push('## Overview');
  lines.push('');
  lines.push('| Scope | TODOs | Owners |');
  lines.push('| --- | ---: | --- |');

  const overviewRows = [...scopeMap.entries()].sort(
    (a, b) => b[1].count - a[1].count || a[0].localeCompare(b[0]),
  );

  overviewRows.forEach(([scope, data]) => {
    const owners = [...data.owners].sort();
    const ownersCell = owners.length ? owners.join(', ') : '—';
    lines.push(`| ${scope} | ${data.count} | ${ownersCell} |`);
  });

  lines.push('');
  lines.push('## Detailed List');
  lines.push('');

  overviewRows.forEach(([scope, data]) => {
    lines.push(`### ${scope}`);
    lines.push('');
    data.items.forEach((todo) => {
      const relativePath = path
        .relative(repoRoot, todo.file)
        .replace(/\\/g, '/');
      const ownerNote = todo.owner ? ` _(owner: ${todo.owner})_` : '';
      lines.push(
        `- [ ] \`${relativePath}:${todo.line}\` — ${todo.detail}${ownerNote}`,
      );
      lines.push(`  > ${todo.snippet}`);
    });
    lines.push('');
  });

  return lines.join('\n');
}

async function ensureDocsDir() {
  const docsDir = path.join(repoRoot, 'docs');
  await fs.mkdir(docsDir, { recursive: true });
}

async function main() {
  console.time('todo-report');
  const files = await walk(repoRoot);
  const todos = await collectTodos(files);
  const markdown = buildMarkdown(todos);
  await ensureDocsDir();
  await fs.writeFile(outputPath, `${markdown}\n`, 'utf8');
  console.timeEnd('todo-report');
  console.log(
    `Generated TODO report with ${todos.length} item(s) → ${path.relative(
      repoRoot,
      outputPath,
    )}`,
  );
}

main().catch((error) => {
  console.error('Failed to generate TODO report:', error);
  process.exitCode = 1;
});
