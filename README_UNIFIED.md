> Deprecated: content consolidated. Use the canonical entry points below.

Use these single sources of truth:

- START_HERE.md — authoritative onboarding and daily flow
- README.md — high-level overview and quickstart

Environment policy (enforced):

- Single source of truth: <repo>/.env.master (chmod 600)
- Manage with: `./bin/keys edit`
- Start services with: `./sophia start`

3. **Required configurations**:
```env
# Minimum required
OPENAI_API_KEY=sk-your-key
# or
ANTHROPIC_API_KEY=sk-ant-your-key

# For Slack integration
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token
SLACK_SIGNING_SECRET=your-secret

# For Asana integration
ASANA_ENABLED=true
ASANA_PAT_TOKEN=your-pat-token

# For Linear integration
LINEAR_ENABLED=true
LINEAR_API_KEY=lin_api_your-key
```

---

## 📊 Features

### Project Management Dashboard
- **Unified view** of projects from all sources
- **Risk heat map** visualization
- **Communication health** monitoring
- **Team performance** metrics
- **AI-powered insights**

### Context-Aware Chat
- **Available on every page**
- **Page context detection**
- **Smart prompt suggestions**
- **Session persistence**
- **Real-time streaming**

### Integration Capabilities
- **Slack**: Channel health, message analysis
- **Asana**: Project tracking, task management
- **Linear**: Development velocity, sprint metrics
- **Defensive design**: Works with partial data

---

## 🧪 Testing

### Run Complete Test Suite
```bash
python3 test_sophia_unified.py
```

### Test Categories
1. **Configuration Tests** - Secure env, no exposed secrets
2. **Server Health Tests** - Availability, endpoints
3. **API Tests** - All endpoints functional
4. **Integration Tests** - Slack, Asana, Linear
5. **Security Tests** - CORS, no data leaks
6. **Performance Tests** - Response times

### View Test Results
```bash
cat test_results.json | python3 -m json.tool
```

---

## 📁 File Structure

```
sophia-intel-ai/
├── backend/main.py               # Main API entrypoint
├── config/
│   └── unified_manager.py        # Unified config management
├── app/
│   ├── integrations/
│   │   ├── slack_unified.py      # Slack with unified config
│   │   ├── asana_client.py       # Asana integration
│   │   └── linear_client.py      # Linear integration
│   └── orchestrators/
│       └── sophia/                # Sophia orchestrator
├── sophia-intel-app/
│   └── src/components/
│       ├── ProjectManagementDashboard.tsx
│       └── SophiaContextChat.tsx
├── start_sophia_unified.sh       # Unified start script
├── stop_sophia_unified.sh        # Stop script
├── test_sophia_unified.py        # Test suite
└── .env.example                   # Environment template
```

---

## 🚦 Health Monitoring

### Check System Health
```bash
curl http://localhost:8000/api/health | python3 -m json.tool
```

### Check Integration Status
```bash
curl http://localhost:8000/api/integrations/status | python3 -m json.tool
```

### View Logs
```bash
tail -f logs/sophia-server.log
tail -f logs/mcp-*.log
```

---

## 🐛 Troubleshooting

### Server Won't Start
1. Check if port 8000 is in use: `lsof -i :8000`
2. Check logs: `cat logs/sophia-server.log`
3. Verify config: `python3 -c "from config.unified_manager import get_config_manager; print(get_config_manager().validate_config())"`

### Integrations Not Working
1. Check config: `<repo>/.env.master`
2. Test specific integration: `curl -X POST http://localhost:8000/api/integrations/slack/test`
3. Check tokens are valid

### Chat Not Appearing
1. Ensure server is running: `curl http://localhost:8000/api/health`
2. Check browser console for errors
3. Verify WebSocket connection

---

## 🔄 Migration from Old System

### For Existing Users
1. **Backup old config**: `cp .env .env.backup`
2. **Create secure config**: `cp .env.template .env.master && chmod 600 .env.master`
3. **Copy your tokens** from backup to secure config
4. **Remove old .env files** with secrets
5. **Use new start script**: `./start_sophia_unified.sh`

### Deprecated Files
- `sophia_server_standalone.py` → Use `backend/main.py`
- `run_sophia_real.py` → Use `backend/main.py`
- `start_sophia_complete.sh` → Use `start_sophia_unified.sh`
- Individual config files → Use `unified_manager.py`

---

## 📈 Performance Metrics

### Expected Performance
- **Server startup**: < 5 seconds
- **Health check**: < 500ms
- **API responses**: < 1 second
- **Chat response**: < 2 seconds
- **Dashboard load**: < 2 seconds

### Resource Usage
- **Memory**: ~200MB base
- **CPU**: < 5% idle
- **Disk**: ~50MB logs/day
- **Network**: Minimal

---

## 🔒 Security Best Practices

1. **Never commit secrets** to repository
2. **Use secure config** at `<repo>/.env.master`
3. **Rotate tokens** regularly
4. **Monitor access logs**
5. **Use HTTPS** in production
6. **Enable CORS** only for trusted origins

---

## 📚 Additional Documentation

- **Overhaul Plan**: `SOPHIA_COMPLETE_OVERHAUL_PLAN.md`
- **PM Architecture**: `PM_BLENDING_ARCHITECTURE.md`
- **Chat Documentation**: `SOPHIA_CONTEXT_CHAT_DOCUMENTATION.md`
- **Dashboard Proposal**: `SOPHIA_DASHBOARD_ENHANCEMENT_PROPOSAL.md`

---

## 🤝 Support

### Getting Help
1. Check logs in `logs/` directory
2. Run test suite: `python3 test_sophia_unified.py`
3. Review documentation above
4. Check configuration with validation

### Reporting Issues
Include:
- Error messages from logs
- Test suite results
- Configuration validation output
- Steps to reproduce

---

**Last Updated**: 2025-09-10
**Version**: 1.0.0
**Status**: ✅ Production Ready
