"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
var express_1 = require("express");
var http_1 = require("http");
var path_1 = require("path");
var url_1 = require("url");
var child_process_1 = require("child_process");
var __dirname = path_1.default.dirname((0, url_1.fileURLToPath)(import.meta.url));
var app = (0, express_1.default)();
var PORT = 8000;
// Middleware
app.use(express_1.default.json());
app.use(express_1.default.urlencoded({ extended: true }));
// Health check endpoint
app.get('/health', function (req, res) {
    res.json({ status: 'healthy', service: 'MCP Server' });
});
// Code review endpoint
app.post('/mcp/code-review', function (req, res) { return __awaiter(void 0, void 0, void 0, function () {
    var code, suggestions, metrics;
    return __generator(this, function (_a) {
        try {
            code = req.body.code;
            if (!code) {
                return [2 /*return*/, res.status(400).json({ error: 'Code is required' })];
            }
            suggestions = [
                {
                    type: "Performance",
                    location: "Line 15",
                    description: "Consider using a more efficient algorithm for this loop",
                    fix: "Replace for loop with array.map()"
                },
                {
                    type: "Security",
                    location: "Line 22",
                    description: "Potential SQL injection vulnerability",
                    fix: "Use parameterized queries"
                }
            ];
            metrics = {
                complexity: "Medium",
                readability: 75,
                bug_risk: "Low"
            };
            res.json({ suggestions: suggestions, metrics: metrics });
        }
        catch (error) {
            res.status(500).json({ error: 'Internal server error' });
        }
        return [2 /*return*/];
    });
}); });
// Quality check endpoint
app.post('/mcp/quality-check', function (req, res) { return __awaiter(void 0, void 0, void 0, function () {
    var _a, url, validUrl, axe, output_1, errorOutput_1;
    return __generator(this, function (_b) {
        try {
            _a = req.body.url, url = _a === void 0 ? 'http://localhost:8501' : _a;
            validUrl = new URL(url);
            if (!['http:', 'https:'].includes(validUrl.protocol)) {
                return [2 /*return*/, res.status(400).json({ error: 'Invalid URL protocol' })];
            }
            if (!['localhost', '127.0.0.1'].includes(validUrl.hostname)) {
                return [2 /*return*/, res.status(403).json({ error: 'Only local URLs allowed' })];
            }
            axe = (0, child_process_1.spawn)('npx', ['axe-cli', validUrl.href], {
                shell: false, // Critical: Disable shell to prevent injection
                timeout: 30000
            });
            output_1 = '';
            errorOutput_1 = '';
            axe.stdout.on('data', function (data) {
                output_1 += data.toString();
            });
            axe.stderr.on('data', function (data) {
                errorOutput_1 += data.toString();
            });
            axe.on('close', function (code) {
                if (code === 0) {
                    res.json({ quality_report: output_1 });
                }
                else {
                    res.status(500).json({ error: 'Quality check failed', details: errorOutput_1 });
                }
            });
            axe.on('error', function (error) {
                res.status(500).json({ error: 'Failed to spawn quality check', details: error.message });
            });
        }
        catch (error) {
            res.status(500).json({ error: 'Invalid request', details: error.message });
        }
        return [2 /*return*/];
    });
}); });
// Swarm status endpoint
app.get('/mcp/swarm-status', function (req, res) {
    // Mock swarm data for demonstration
    var swarmData = {
        status: 'active',
        agents: [
            { id: 'agent-1', status: 'online', last_active: new Date().toISOString() },
            { id: 'agent-2', status: 'online', last_active: new Date().toISOString() },
            { id: 'agent-3', status: 'offline', last_active: new Date(Date.now() - 300000).toISOString() }
        ],
        total_agents: 3,
        active_agents: 2
    };
    res.json(swarmData);
});
// Swarm configuration endpoint
app.post('/mcp/swarm-config', function (req, res) {
    try {
        var _a = req.body, num_agents = _a.num_agents, agent_type = _a.agent_type, max_concurrency = _a.max_concurrency;
        // Input validation
        if (!num_agents || typeof num_agents !== 'number' || num_agents < 1 || num_agents > 100) {
            return res.status(400).json({ error: 'Invalid num_agents: must be between 1 and 100' });
        }
        var validAgentTypes = ['CPU', 'GPU', 'Hybrid'];
        if (!agent_type || !validAgentTypes.includes(agent_type)) {
            return res.status(400).json({ error: 'Invalid agent_type: must be CPU, GPU, or Hybrid' });
        }
        if (!max_concurrency || typeof max_concurrency !== 'number' || max_concurrency < 1 || max_concurrency > 50) {
            return res.status(400).json({ error: 'Invalid max_concurrency: must be between 1 and 50' });
        }
        // Process configuration (e.g., update swarm settings)
        console.log("Swarm configuration updated: ".concat(num_agents, " agents, ").concat(agent_type, ", ").concat(max_concurrency));
        res.json({ status: 'success', message: 'Configuration updated' });
    }
    catch (error) {
        res.status(500).json({ error: 'Invalid configuration data' });
    }
});
// Start server
var server = (0, http_1.createServer)(app);
server.listen(PORT, function () {
    console.log("MCP Server running on http://localhost:".concat(PORT));
});
// Graceful shutdown
process.on('SIGINT', function () {
    server.close(function () {
        console.log('MCP Server closed');
        process.exit(0);
    });
});
