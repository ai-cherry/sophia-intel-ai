# Sophia Dashboard Enhancement - Quick Start Guide

## 🚀 Immediate Setup (5 minutes)

### 1. Environment Check
```bash
# Verify Slack tokens are working
python3 test_slack_tokens.py

# Check PM blending capabilities
python3 test_pm_blending.py
```

### 2. Install UI Dependencies
```bash
cd sophia-intel-app
npm install
```

### 3. Start the Services
```bash
# Terminal 1: Start backend
./start_sophia_complete.sh

# Terminal 2: Start UI
cd sophia-intel-app
npm run dev
```

### 4. Access Enhanced Dashboard
- **Basic Dashboard**: http://localhost:3000/projects
- **Sophia Chat**: http://localhost:3000/chat
- **API Status**: http://localhost:8000/api/projects/sync-status

---

## ✅ What's Been Implemented

### Backend (Ready to Use)
- ✅ `/api/projects/overview` - Unified PM data endpoint
- ✅ `/api/projects/sync-status` - Integration health check
- ✅ Slack connector with retry logic
- ✅ Asana connector with BI analytics
- ✅ Linear connector with GraphQL support
- ✅ Defensive architecture (works with partial data)

### Frontend Components (New)
- ✅ `ProjectManagementDashboard.tsx` - Full-featured PM dashboard
- ✅ Risk visualization and health scores
- ✅ Communication health monitoring
- ✅ Team performance metrics
- ✅ AI insights panel
- ✅ Auto-refresh capability

### Integration Points
- ✅ Slack tokens configured and tested
- ✅ Asana connector ready (needs PAT token)
- ⚠️  Linear needs API key in `.env`
- ⚠️  Airtable needs configuration

---

## 🔧 Configuration

### Required Environment Variables
```bash
# Already configured (tested & working)
SLACK_BOT_TOKEN=xoxb-293968207940-9492433757667-YAplHFRnTfeV6UCaY7gWLCIo
SLACK_APP_TOKEN=xapp-1-A09EH9DKDPX-9500784360276-673c418f1ec0778483b4e1676529dc040cc1917e644b34536d3565a8de21efaa
SLACK_SIGNING_SECRET=f06e529023c037b556159eef897f2cd6

# Need to add for full functionality
LINEAR_API_KEY=your-linear-api-key-here
AIRTABLE_API_KEY=your-airtable-key-here
```

### Toggle Dashboard Mode
In `/sophia-intel-app/src/app/(sophia)/projects/page.tsx`:
```typescript
// Set to true for enhanced dashboard, false for basic
const USE_ENHANCED_DASHBOARD = true;
```

---

## 📊 Dashboard Features

### Main Views
1. **Projects Tab** - All projects from Asana, Linear, Slack
2. **Communication Tab** - Slack channel health analysis
3. **Teams Tab** - Velocity and performance metrics
4. **AI Insights Tab** - Sophia's recommendations

### Key Metrics Displayed
- Risk distribution (Critical/High/Medium/Low)
- Source connectivity status
- Project completion progress
- Team velocity trends
- Communication bottlenecks
- System recommendations

---

## 🎯 Quick Wins

### See Immediate Value
1. **Risk Overview** - Instantly see critical projects
2. **Source Status** - Know which integrations are working
3. **Communication Issues** - Identify neglected Slack channels
4. **System Notes** - Get AI-powered observations

### Test the Integration
```bash
# Test API endpoint
curl http://localhost:8000/api/projects/overview

# Test Slack integration
curl http://localhost:8000/api/projects/sync-status
```

---

## 📈 Next Steps

### To Enable Full Features

1. **Add Linear API Key**
   - Get key from: https://linear.app/settings/api
   - Add to `.env`: `LINEAR_API_KEY=lin_api_...`

2. **Configure Asana**
   - Get PAT from: https://app.asana.com/0/developer-console
   - Add to `.env`: `ASANA_PAT_TOKEN=...`

3. **Enable Real-time Updates**
   ```typescript
   // In ProjectManagementDashboard.tsx
   setAutoRefresh(true); // Enables 60-second refresh
   ```

4. **Customize Risk Thresholds**
   - Modify risk calculation logic in dashboard
   - Adjust color coding for your needs

---

## 🐛 Troubleshooting

### Dashboard Not Loading?
```bash
# Check backend is running
curl http://localhost:8000/api/projects/sync-status

# Check frontend build
cd sophia-intel-app && npm run build
```

### No Data Showing?
- Verify environment variables are set
- Check integration status on dashboard
- Look at browser console for errors

### Slack Not Working?
```bash
# Test Slack tokens
python3 test_slack_tokens.py
```

---

## 📚 Documentation

- **Architecture**: `PM_BLENDING_ARCHITECTURE.md`
- **Full Proposal**: `SOPHIA_DASHBOARD_ENHANCEMENT_PROPOSAL.md`
- **Slack Setup**: `SLACK_TOKEN_UPDATE_SUMMARY.md`
- **Component Code**: `sophia-intel-app/src/components/ProjectManagementDashboard.tsx`

---

## 🎉 Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Projects page shows enhanced dashboard
- [ ] Slack integration shows "online"
- [ ] Risk overview displays project counts
- [ ] Auto-refresh toggle works
- [ ] Data updates every 60 seconds

---

**Ready to go!** Navigate to http://localhost:3000/projects to see your enhanced PM dashboard.