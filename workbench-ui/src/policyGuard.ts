import fs from 'fs';
import path from 'path';
import YAML from 'yaml';

export class PolicyGuard {
  private workspace: string;
  private policies: any;

  constructor(workspace: string) {
    this.workspace = workspace;
    this.policies = this.loadPolicies();
  }

  private loadPolicies(): any {
    try {
      const policyPath = path.join(this.workspace, 'POLICIES', 'access.yml');
      if (fs.existsSync(policyPath)) {
        const content = fs.readFileSync(policyPath, 'utf8');
        return YAML.parse(content);
      }
    } catch (e) {
      console.error('[PolicyGuard] Failed to load policies:', e);
    }
    return { deny_patterns: ['\\.env', '/\\.ssh/', '/infra/'] };
  }

  applyChange(filePath: string, content: string): { ok: boolean; reason?: string } {
    // Check deny patterns
    const denyPatterns = this.policies?.deny_patterns || ['\\.env', '/\\.ssh/', '/infra/'];
    for (const pattern of denyPatterns) {
      const regex = new RegExp(pattern);
      if (regex.test(filePath)) {
        return { ok: false, reason: `denied:${pattern}` };
      }
    }

    // Write file with backup
    try {
      const absPath = path.join(this.workspace, filePath);
      const dir = path.dirname(absPath);
      
      // Create directory if needed
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      // Create backup if file exists
      if (fs.existsSync(absPath)) {
        fs.copyFileSync(absPath, `${absPath}.bak`);
      }

      // Write new content
      fs.writeFileSync(absPath, content, 'utf8');
      return { ok: true };
    } catch (e: any) {
      return { ok: false, reason: `write_failed:${e.message}` };
    }
  }
}
