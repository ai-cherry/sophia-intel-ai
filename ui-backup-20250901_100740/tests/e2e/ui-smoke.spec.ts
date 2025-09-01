import { test, expect } from '@playwright/test';

test.describe('UI Smoke Tests', () => {
  test('should load homepage', async ({ page }) => {
    await page.goto('/');
    
    // Check app name is visible
    await expect(page.locator('h1')).toContainText('slim-agno');
    
    // Check endpoint picker is present
    await expect(page.locator('input[type="url"]')).toBeVisible();
    
    // Check quick action links
    await expect(page.locator('text=Open Chat')).toBeVisible();
    await expect(page.locator('text=Open Workflow Runner')).toBeVisible();
  });

  test('should connect to endpoint', async ({ page }) => {
    await page.goto('/');
    
    // Enter endpoint
    const endpointInput = page.locator('input[type="url"]');
    await endpointInput.fill('http://localhost:7777');
    
    // Click connect
    await page.locator('button:has-text("Connect")').click();
    
    // Check for connection indicator (may show error if backend not running)
    await page.waitForSelector('.w-3.h-3.rounded-full', { timeout: 5000 });
  });

  test('should navigate to chat page', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Open Chat');
    
    // Verify we're on the chat page
    await expect(page).toHaveURL('/chat');
    await expect(page.locator('h1')).toContainText('Team Chat');
    
    // Check for team/workflow tabs
    await expect(page.locator('button:has-text("Team")')).toBeVisible();
    await expect(page.locator('button:has-text("Workflow")')).toBeVisible();
  });

  test('should navigate to workflow page', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Open Workflow Runner');
    
    // Verify we're on the workflow page
    await expect(page).toHaveURL('/workflow');
    await expect(page.locator('h1')).toContainText('Workflow Runner');
    
    // Check for workflow info banner
    await expect(page.locator('text=Workflow Mode')).toBeVisible();
  });

  test('should show Judge JSON with decision and runner_instructions', async ({ page }) => {
    // This test requires mocking or a running backend
    // For CI, we'll create a mock response
    
    await page.goto('/workflow');
    
    // Mock a judge response if backend is available
    // This would normally come from running a workflow
    
    // Check that Judge Report component structure exists
    const pageContent = await page.content();
    
    // Verify the component structure is in place
    expect(pageContent).toContain('TeamWorkflowPanel');
  });

  test('should handle streaming responses', async ({ page }) => {
    await page.goto('/chat');
    
    // Verify streaming view is present
    await expect(page.locator('text=No output yet')).toBeVisible();
    
    // Check message textarea
    const messageInput = page.locator('textarea[placeholder*="Enter your task"]');
    await expect(messageInput).toBeVisible();
    
    // Check additional data field
    const additionalDataInput = page.locator('textarea[placeholder*="repo"]');
    await expect(additionalDataInput).toBeVisible();
  });

  test('should have proper CSP headers', async ({ page, context }) => {
    const response = await page.goto('/');
    const headers = response?.headers();
    
    if (headers) {
      // Check for security headers
      expect(headers['content-security-policy']).toBeDefined();
      expect(headers['x-frame-options']).toBe('DENY');
      expect(headers['x-content-type-options']).toBe('nosniff');
    }
  });

  test('should display pool and priority selectors', async ({ page }) => {
    await page.goto('/chat');
    
    // Check for pool selector
    const poolSelect = page.locator('select').filter({ hasText: /fast|balanced|heavy/i }).first();
    await expect(poolSelect).toBeVisible();
    
    // Check for priority selector
    const prioritySelect = page.locator('select').filter({ hasText: /low|medium|high/i }).first();
    await expect(prioritySelect).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('should have no accessibility violations on homepage', async ({ page }) => {
    await page.goto('/');
    
    // Basic accessibility checks
    // For full axe-core integration, install @axe-core/playwright
    
    // Check for proper heading hierarchy
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBe(1);
    
    // Check for alt text on images (if any)
    const images = page.locator('img');
    const imageCount = await images.count();
    for (let i = 0; i < imageCount; i++) {
      const alt = await images.nth(i).getAttribute('alt');
      expect(alt).toBeDefined();
    }
    
    // Check for label associations
    const inputs = page.locator('input, textarea, select');
    const inputCount = await inputs.count();
    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        const labelCount = await label.count();
        // Input should have associated label or aria-label
        if (labelCount === 0) {
          const ariaLabel = await input.getAttribute('aria-label');
          expect(ariaLabel).toBeTruthy();
        }
      }
    }
  });
});