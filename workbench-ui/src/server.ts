import express, { Request, Response } from 'express';
import fs from 'fs';
import path from 'path';
import YAML from 'yaml';
import { PolicyGuard } from './policyGuard';
import { commitAll, ensureBranch, ensureRepo } from './gitUtils';

const app = express();
app.use(express.json({ limit: '2mb' }));

// Server-only env load: single source from REPO_ENV_MASTER_PATH
const masterEnvPath = process.env.REPO_ENV_MASTER_PATH || '';
let WORKSPACE = '';
if (masterEnvPath) {
  try {
    const text = fs.readFileSync(masterEnvPath, 'utf8');
    text.split(/\r?\n/).forEach((line) => {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
      if (!m) return;
      let v = m[2].replace(/^['\"]|['\"]$/g, '');
      if (!(m[1] in process.env)) process.env[m[1]] = v;
    });
    WORKSPACE = path.dirname(masterEnvPath);
  } catch (e) {
    console.error('[env] failed to load .env.master at', masterEnvPath, e);
  }
}

// Minimal metrics
const metrics = {
  requests_total: 0,
  last_health: 0,
  coding_plan_total: 0,
  coding_apply_total: 0,
  coding_validate_total: 0,
};
app.use((req, _res, next) => {
  metrics.requests_total++;
  next();
});

// Utils
function bearerOk(req: Request): boolean {
  const bypass = process.env.NODE_ENV !== 'production';
  if (bypass) return true;
  const token = (req.headers['authorization'] || '').toString().replace(/^Bearer\s+/i, '');
  const expected = process.env.AUTH_BYPASS_TOKEN || '';
  return token && expected && token === expected;
}

function curatedAliases(): Record<string, string> {
  try {
    const p = path.join(process.cwd(), 'workbench-ui', 'config', 'model_aliases.json');
    const txt = fs.readFileSync(p, 'utf8');
    return JSON.parse(txt);
  } catch {
    return {};
  }
}

function topModels(): { id: string; tags?: string[]; context?: number }[] {
  try {
    const p = path.join(process.cwd(), 'workbench-ui', 'config', 'top_models.json');
    const txt = fs.readFileSync(p, 'utf8');
    return JSON.parse(txt);
  } catch {
    return [];
  }
}

async function portkeyGet(pathname: string): Promise<any> {
  const key = process.env.PORTKEY_API_KEY || '';
  if (!key) throw new Error('Missing PORTKEY_API_KEY');
  const url = `https://api.portkey.ai${pathname}`;
  const res = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${key}`,
      'Content-Type': 'application/json'
    }
  });
  if (!res.ok) {
    throw new Error(`Portkey ${pathname} failed: ${res.status}`);
  }
  return res.json();
}

async function portkeyChat(model: string, messages: any[], maxTokens = 512, temperature = 0.2): Promise<any> {
  const key = process.env.PORTKEY_API_KEY || '';
  if (!key) throw new Error('Missing PORTKEY_API_KEY');
  const provider = model.split('/', 1)[0];
  const vkEnv = `PORTKEY_VK_${provider.toUpperCase()}`;
  const vk = process.env[vkEnv] || '';
  const res = await fetch('https://api.portkey.ai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${key}`,
      'Content-Type': 'application/json',
      'x-portkey-provider': provider,
      ...(vk ? { 'x-portkey-virtual-key': vk } : {})
    },
    body: JSON.stringify({ model, messages, max_tokens: maxTokens, temperature })
  });
  if (!res.ok) throw new Error(`Portkey chat failed: ${res.status}`);
  return res.json();
}

// Routes
app.get('/health', (_req, res) => {
  metrics.last_health = Date.now();
  res.json({ ok: true, workspace: WORKSPACE || null, time: new Date().toISOString() });
});

app.get('/metrics', (_req, res) => {
  res.set('Content-Type', 'text/plain; version=0.0.4');
  const lines: string[] = [];
  lines.push(`# HELP requests_total Total HTTP requests`);
  lines.push(`# TYPE requests_total counter`);
  lines.push(`requests_total ${metrics.requests_total}`);
  lines.push(`# HELP coding_plan_total Total coding plan requests`);
  lines.push(`# TYPE coding_plan_total counter`);
  lines.push(`coding_plan_total ${metrics.coding_plan_total}`);
  lines.push(`# HELP coding_apply_total Total coding apply requests`);
  lines.push(`# TYPE coding_apply_total counter`);
  lines.push(`coding_apply_total ${metrics.coding_apply_total}`);
  lines.push(`# HELP coding_validate_total Total coding validate requests`);
  lines.push(`# TYPE coding_validate_total counter`);
  lines.push(`coding_validate_total ${metrics.coding_validate_total}`);
  res.send(lines.join('\n'));
});

app.get('/api/portkey/health', async (_req, res) => {
  try {
    const data = await portkeyGet('/v1/models');
    res.json({ ok: true, models: Array.isArray(data?.data) ? data.data.length : 0 });
  } catch (e: any) {
    res.status(502).json({ ok: false, error: String(e?.message || e) });
  }
});

app.get('/api/models', async (_req, res) => {
  const aliases = curatedAliases();
  let available: Set<string> = new Set();
  try {
    const data = await portkeyGet('/v1/models');
    const arr = Array.isArray(data?.data) ? data.data : [];
    available = new Set(arr.map((m: any) => m?.id).filter(Boolean));
  } catch {}
  const models = Object.entries(aliases).map(([alias, id]) => ({
    alias, id, available: available.has(id)
  }));
  res.json({ models });
});

app.post('/api/coding/plan', async (req, res) => {
  if (!bearerOk(req)) return res.status(401).json({ error: 'unauthorized' });
  const { task, model: modelId, alias } = req.body || {};
  if (!task) return res.status(400).json({ error: 'task required' });
  const aliases = curatedAliases();
  const model = modelId || (alias ? aliases[alias] : undefined) || aliases['grok-fast'] || Object.values(aliases)[0];
  if (!model) return res.status(400).json({ error: 'no curated models configured' });
  const system = 'You are a senior engineer. Return a concise, numbered plan with impacted files and tests.';
  const user = `Task: ${task}\nConstraints: minimal diffs; follow repo style; list files.`;
  try {
    const data = await portkeyChat(model, [{ role: 'system', content: system }, { role: 'user', content: user }], 700, 0.1);
    const content = data?.choices?.[0]?.message?.content || '';
    metrics.coding_plan_total++;
    res.json({ plan: content });
  } catch (e: any) {
    res.status(502).json({ error: String(e?.message || e) });
  }
});

type ProposedChange = { path: string; content: string };

function unifiedDiff(oldStr: string, newStr: string, filePath: string): string {
  // Minimal unified diff: no hunks, just header and full content blocks
  const oldLines = oldStr.split(/\r?\n/);
  const newLines = newStr.split(/\r?\n/);
  const header = `--- a/${filePath}\n+++ b/${filePath}\n`;
  const bodyOld = oldLines.map(l => `-"${l}"`).join('\n');
  const bodyNew = newLines.map(l => `+"${l}"`).join('\n');
  return header + bodyOld + '\n' + bodyNew + '\n';
}

app.post('/api/coding/patch', async (req, res) => {
  if (!bearerOk(req)) return res.status(401).json({ error: 'unauthorized' });
  const { apply, changes, task, branch } = req.query.apply ? { ...req.body, apply: req.query.apply } : req.body || {};
  const applyFlag = String(apply || 'false') === 'true';
  const list: ProposedChange[] = Array.isArray(changes) ? changes : [];
  if (!Array.isArray(list) || list.some(c => typeof c?.path !== 'string' || typeof c?.content !== 'string')) {
    return res.status(400).json({ error: 'changes must be an array of {path, content}' });
  }
  if (!WORKSPACE) return res.status(500).json({ error: 'workspace not resolved from REPO_ENV_MASTER_PATH' });
  // Compute diff only
  if (!applyFlag) {
    const diffs = list.map(c => {
      const abs = path.join(WORKSPACE, c.path);
      const oldTxt = fs.existsSync(abs) ? fs.readFileSync(abs, 'utf8') : '';
      const diff = unifiedDiff(oldTxt, c.content, c.path);
      return { path: c.path, diff };
    });
    return res.json({ diffs });
  }
  // Apply with policy + git
  try {
    ensureRepo(WORKSPACE);
  } catch (e: any) {
    return res.status(400).json({ error: e.message });
  }
  const guard = new PolicyGuard(WORKSPACE);
  const denied: string[] = [];
  let applied = 0;
  for (const c of list) {
    const r = guard.applyChange(c.path, c.content);
    if (!r.ok) denied.push(`${c.path}:${r.reason}`); else applied++;
  }
  // Branch + commit
  let b = '';
  try {
    b = ensureBranch(WORKSPACE, typeof branch === 'string' ? branch : undefined, typeof task === 'string' ? task : undefined);
    const msg = `[workbench] ${task || 'apply changes'}`;
    commitAll(WORKSPACE, msg);
  } catch (e: any) {
    return res.status(500).json({ error: 'git_failed:' + String(e?.message || e), applied, denied });
  }
  metrics.coding_apply_total++;
  res.json({ ok: true, branch: b, applied, denied });
});

app.post('/api/coding/validate', async (req, res) => {
  if (!bearerOk(req)) return res.status(401).json({ error: 'unauthorized' });
  const { paths } = req.body || {};
  if (!WORKSPACE) return res.status(500).json({ error: 'workspace not resolved' });
  const list: string[] = Array.isArray(paths) ? paths : [];
  const errors: string[] = [];
  for (const p of list) {
    const abs = path.join(WORKSPACE, p);
    if (!fs.existsSync(abs)) {
      errors.push(`missing:${p}`);
      continue;
    }
    if (abs.endsWith('.py')) {
      try {
        const out = require('child_process').spawnSync(process.execPath, ['-m', 'py_compile', abs], { encoding: 'utf8' });
        if (out.status !== 0) errors.push(`py_syntax:${p}:${(out.stderr || '').trim()}`);
      } catch (e: any) {
        errors.push(`py_compile_failed:${p}:${String(e?.message || e)}`);
      }
    }
  }
  // Optional ruff
  try {
    const whichRuff = require('child_process').spawnSync('ruff', ['--version'], { encoding: 'utf8' });
    if (whichRuff.status === 0) {
      const rr = require('child_process').spawnSync('ruff', ['check', ...list.filter(p => p.endsWith('.py'))], { cwd: WORKSPACE, encoding: 'utf8' });
      if (rr.status !== 0) errors.push(`ruff:${(rr.stdout + rr.stderr).trim()}`);
    }
  } catch {}
  // Optional pytest
  try {
    const whichPytest = require('child_process').spawnSync('pytest', ['--version'], { encoding: 'utf8' });
    if (whichPytest.status === 0) {
      const testSelectors = list.filter(p => /(^tests\/.+|test_.+\.py$)/.test(p)).map(p => path.basename(p, '.py'));
      const k = testSelectors.join(' or ');
      if (k) {
        const pr = require('child_process').spawnSync('pytest', ['-q', '-k', k], { cwd: WORKSPACE, encoding: 'utf8' });
        if (pr.status !== 0) errors.push(`pytest:${(pr.stdout + pr.stderr).trim()}`);
      }
    }
  } catch {}
  metrics.coding_validate_total++;
  res.json({ ok: errors.length === 0, errors });
});

// SSR-only pages (very minimal)
app.get('/', (_req, res) => {
  res.type('html').send(`<!doctype html><html><head><title>Workbench</title></head><body>
  <h1>Workbench</h1>
  <ul>
    <li><a href="/health">Health JSON</a></li>
    <li><a href="/console">Console</a></li>
    <li><a href="/coding">Coding Panel</a></li>
  </ul>
  </body></html>`);
});

app.get('/console', (_req, res) => {
  res.type('html').send(`<!doctype html><html><head><title>Console</title></head><body>
  <h2>Live Console</h2>
  <form method="post" action="/api/coding/plan" onsubmit="fetch('/api/coding/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:document.getElementById('task').value,alias:document.getElementById('alias').value})}).then(r=>r.json()).then(j=>document.getElementById('out').textContent=j.plan||JSON.stringify(j,null,2));return false;">
    <label>Alias: <input id="alias" placeholder="grok-fast"/></label>
    <br/>
    <textarea id="task" rows="6" cols="80" placeholder="Describe your task..."></textarea>
    <br/>
    <button type="submit">Plan</button>
  </form>
  <pre id="out" style="background:#f4f4f4;padding:8px"></pre>
  </body></html>`);
});

app.get('/coding', (_req, res) => {
  res.type('html').send(`<!doctype html><html><head><title>Coding</title></head><body>
  <h2>Coding Panel</h2>
  <section>
  <form id="planForm" onsubmit="window.plan();return false;">
    <label>Alias: <input id="alias" placeholder="grok-fast"/></label>
    <br/>
    <textarea id="task" rows="4" cols="80" placeholder="Describe your task..."></textarea>
    <br/>
    <button type="submit">Plan</button>
  </form>
  <pre id="plan" style="white-space:pre-wrap;background:#f4f4f4;padding:8px"></pre>
  </section>
  <section>
    <h3>Patch</h3>
    <textarea id="changes" rows="10" cols="100" placeholder='[{"path":"app/foo.py","content":"..."}]'></textarea><br/>
    <button onclick="window.diff()">Diff</button>
    <button onclick="window.apply()">Apply</button>
    <pre id="diffout" style="background:#f4f4f4;padding:8px;overflow:auto;max-height:300px"></pre>
  </section>
  <section>
    <h3>Validate</h3>
    <input id="paths" size="80" placeholder="Comma-separated paths to validate"/>
    <button onclick="window.validate()">Validate</button>
    <pre id="valout" style="background:#f4f4f4;padding:8px"></pre>
  </section>
  <script>
  window.plan = function(){
    fetch('/api/coding/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:document.getElementById('task').value,alias:document.getElementById('alias').value})}).then(r=>r.json()).then(j=>document.getElementById('plan').textContent=j.plan||JSON.stringify(j,null,2));
  };
  window.diff = function(){
    let ch; try{ ch = JSON.parse(document.getElementById('changes').value||'[]'); }catch(e){ alert('Invalid changes JSON'); return; }
    fetch('/api/coding/patch?apply=false',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({changes:ch})}).then(r=>r.json()).then(j=>document.getElementById('diffout').textContent=(j.diffs||[]).map(d=>'# '+d.path+'\\n'+d.diff).join('\\n'));
  };
  window.apply = function(){
    let ch; try{ ch = JSON.parse(document.getElementById('changes').value||'[]'); }catch(e){ alert('Invalid changes JSON'); return; }
    fetch('/api/coding/patch?apply=true',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({changes:ch,task:document.getElementById('task').value})}).then(r=>r.json()).then(j=>document.getElementById('diffout').textContent=JSON.stringify(j,null,2));
  };
  window.validate = function(){
    const p = (document.getElementById('paths').value||'').split(',').map(s=>s.trim()).filter(Boolean);
    fetch('/api/coding/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({paths:p})}).then(r=>r.json()).then(j=>document.getElementById('valout').textContent=JSON.stringify(j,null,2));
  };
  </script>
  </body></html>`);
});

const PORT = Number(process.env.PORT || 3200);
app.listen(PORT, () => {
  console.log(`[workbench] server listening on http://127.0.0.1:${PORT}`);
});
// Basic request logging with request_id; no sensitive headers
app.use((req, _res, next) => {
  (req as any).request_id = Math.random().toString(36).slice(2);
  console.log(JSON.stringify({ level: 'info', msg: 'req', request_id: (req as any).request_id, method: req.method, path: req.path }));
  next();
});
