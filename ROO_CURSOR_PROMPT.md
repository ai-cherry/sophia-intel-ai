# 🎨 Roo/Cursor Task: Frontend Review Interface  
## AI-Powered Code Review System - Frontend Development

**🎯 Your Mission:** Build the user interface and visualization system for our AI-powered code review system. You're working in coordination with Cline/VS Code (building the backend) and Claude (monitoring integration).

---

## 📋 **Your Specific Tasks:**

### **1. Review Dashboard**
**File:** `agent-ui/src/components/code-review/ReviewDashboard.tsx`

Create a dashboard with:
```typescript
interface ReviewDashboard {
  pendingReviews: Review[]
  completedReviews: Review[] 
  metrics: {
    totalReviews: number
    averageScore: number
    trendsData: ChartData[]
  }
  realTimeUpdates: boolean
}
```

**Features:**
- Overview cards showing review statistics
- Progress indicators for active reviews
- Real-time status updates via WebSocket
- Quick actions (submit new review, view details)

### **2. Code Submission Interface**
**File:** `agent-ui/src/components/code-review/CodeSubmission.tsx`

Build submission form with:
- Code editor component (Monaco Editor or similar)
- Language selection dropdown
- Review options configuration
- File upload capability
- Preview before submission
- Validation and error handling

### **3. Results Visualization**
**File:** `agent-ui/src/components/code-review/ResultsView.tsx`

Create interactive results display:
- Syntax-highlighted code with inline annotations
- Metrics dashboard (complexity, quality scores)
- Issue severity indicators (error, warning, info)
- Expandable suggestions and recommendations
- Before/after code comparisons

### **4. Real-time Updates Hook**
**File:** `agent-ui/src/hooks/useReviewUpdates.ts`

Implement WebSocket integration:
```typescript
export const useReviewUpdates = (reviewId: string) => {
  // WebSocket connection to backend
  // Real-time progress updates
  // Status change notifications
  // Error handling and reconnection
  // Return: { status, progress, results, error }
}
```

### **5. Review History Component**
**File:** `agent-ui/src/components/code-review/ReviewHistory.tsx`

Build history browser with:
- Paginated list of past reviews
- Search and filtering capabilities
- Sort by date, score, language
- Trend analysis charts
- Export functionality (JSON, CSV)

---

## 🔗 **MCP Integration Commands:**

### **Update Progress:**
```
@sophia-mcp store "Frontend Dashboard: Created review overview components"
@sophia-mcp store "Code Submission: Added Monaco editor integration" 
@sophia-mcp store "Real-time Updates: WebSocket connection established"
```

### **Stay Coordinated:**
```
@sophia-mcp search "api endpoints"        # Get backend API details from Cline
@sophia-mcp search "data structures"      # Check what data backend provides
@sophia-mcp context                       # Get full project understanding
```

### **Share Frontend Requirements:**
```
@sophia-mcp store "Frontend needs: Real-time WebSocket endpoint for review progress"
@sophia-mcp store "UI requires: GET /api/review/metrics for dashboard stats"
```

---

## ✅ **Success Criteria:**

1. **Responsive UI Working:**
   - Dashboard loads and displays sample data
   - Code submission form accepts input
   - Results view renders mock analysis results

2. **API Integration:**
   - Frontend successfully calls backend endpoints
   - Error handling for API failures
   - Loading states during async operations

3. **Real-time Features:**
   - WebSocket connection established
   - Live updates when review status changes
   - Notifications for completed reviews

4. **MCP Communication:**
   - Progress updates visible to other tools
   - Frontend requirements shared with backend team
   - UI mockups and requirements documented

---

## 🚀 **Getting Started:**

1. **Check Project Context:**
   ```
   @sophia-mcp context
   @sophia-mcp search "code review project"
   ```

2. **Set Up Component Structure:**
   ```bash
   mkdir -p agent-ui/src/components/code-review
   mkdir -p agent-ui/src/hooks
   mkdir -p agent-ui/src/types
   ```

3. **Start with Dashboard:**
   Begin with `ReviewDashboard.tsx` - create basic layout and structure

4. **Update Progress:**
   Use `@sophia-mcp store` to share your progress as you work

5. **Coordinate with Backend:**
   Monitor MCP for API contracts and data structures from Cline

---

## 💡 **UI/UX Guidelines:**

### **Design System:**
- Follow existing `agent-ui` patterns and styling
- Use Tailwind CSS for consistent design
- Implement dark/light theme support
- Ensure mobile responsiveness

### **User Experience:**
- Clear loading states and progress indicators
- Intuitive navigation between different views
- Helpful error messages and validation
- Keyboard shortcuts for power users

### **Data Visualization:**
- Use Chart.js or Recharts for metrics
- Color-coded severity levels (red=error, yellow=warning)
- Interactive tooltips and hover states
- Accessible design for screen readers

---

## 📊 **Component Architecture:**

```typescript
// Type definitions you'll need
interface Review {
  id: string
  code: string
  language: string
  status: 'pending' | 'analyzing' | 'completed' | 'error'
  results?: AnalysisResults
  createdAt: string
  completedAt?: string
}

interface AnalysisResults {
  score: number
  issues: Issue[]
  metrics: CodeMetrics
  suggestions: Suggestion[]
}

interface Issue {
  type: 'error' | 'warning' | 'info'
  message: string
  line: number
  severity: number
  fix?: string
}
```

---

## 🤖 **MCP-Enhanced Development:**

Remember: You're not just building a React app - you're participating in **revolutionary cross-tool AI collaboration!**

- Your progress is automatically shared with Cline and Claude
- UI requirements are coordinated with backend development
- Integration issues are resolved in real-time through MCP
- The entire team maintains shared understanding of user experience

**Design Coordination:**
- Share UI mockups through `@sophia-mcp store "UI Design: [description]"`
- Communicate data requirements to backend team
- Coordinate WebSocket event structures with Cline
- Keep Claude informed of any integration challenges

---

## 🚀 **Ready to Build Amazing UI?**

Your frontend will be the face of our AI-powered code review system! Focus on:

1. **Intuitive User Experience** - Make code review feel effortless
2. **Real-time Responsiveness** - Users see progress as it happens  
3. **Rich Visualizations** - Turn analysis data into actionable insights
4. **Seamless Integration** - Work perfectly with Cline's backend

**Need help or coordination?** Claude is monitoring through MCP and will provide guidance. Cline is building APIs based on your requirements. Just keep updating your progress and stay connected!

**Let's create the most advanced code review interface ever built!** 🎨✨

---

**Pro Tip:** Check the existing `agent-ui` components for patterns and reusable elements. Our UI already has great foundations - build on them for consistency!