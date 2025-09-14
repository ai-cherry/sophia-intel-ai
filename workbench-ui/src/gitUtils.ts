import { execSync } from 'child_process';
import path from 'path';

export function ensureRepo(workspace: string): void {
  try {
    execSync('git rev-parse --git-dir', { cwd: workspace, encoding: 'utf8' });
  } catch {
    throw new Error('Not a git repository');
  }
}

export function ensureBranch(workspace: string, branchName?: string, task?: string): string {
  let branch = branchName;
  
  if (!branch) {
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const slug = (task || 'changes').toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 30);
    branch = `feat/auto/${date}-${slug}`;
  }

  try {
    // Check if branch exists
    execSync(`git rev-parse --verify ${branch}`, { cwd: workspace, encoding: 'utf8' });
    // Branch exists, switch to it
    execSync(`git checkout ${branch}`, { cwd: workspace, encoding: 'utf8' });
  } catch {
    // Branch doesn't exist, create it
    execSync(`git checkout -b ${branch}`, { cwd: workspace, encoding: 'utf8' });
  }

  return branch;
}

export function commitAll(workspace: string, message: string): void {
  try {
    // Add all changes
    execSync('git add -A', { cwd: workspace, encoding: 'utf8' });
    
    // Check if there are changes to commit
    const status = execSync('git status --porcelain', { cwd: workspace, encoding: 'utf8' });
    if (status.trim()) {
      // Commit changes
      execSync(`git commit -m "${message}"`, { cwd: workspace, encoding: 'utf8' });
    }
  } catch (e: any) {
    throw new Error(`Git commit failed: ${e.message}`);
  }
}
