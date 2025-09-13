"""
Test Coverage Reporting Dashboard
Comprehensive test coverage tracking and visualization system
"""
import asyncio
import json
import logging
import os
import sqlite3
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
# Web framework and visualization libraries
try:
    from flask import Flask, jsonify, render_template, request, send_from_directory
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
try:
    import plotly
    import plotly.express as px
    import plotly.graph_objs as go
    from plotly.utils import PlotlyJSONEncoder
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False
@dataclass
class CoverageMetrics:
    """Test coverage metrics"""
    timestamp: datetime
    test_suite: str  # unit, integration, e2e, performance, security
    component: str  # unified_mcp, , bi_server, mem0, base_mcp
    lines_covered: int
    lines_total: int
    branches_covered: int
    branches_total: int
    functions_covered: int
    functions_total: int
    files_analyzed: int
    coverage_percentage: float
    missing_lines: List[str]
    @property
    def branch_coverage_percentage(self) -> float:
        if self.branches_total == 0:
            return 100.0
        return (self.branches_covered / self.branches_total) * 100
    @property
    def function_coverage_percentage(self) -> float:
        if self.functions_total == 0:
            return 100.0
        return (self.functions_covered / self.functions_total) * 100
@dataclass
class CoverageTrend:
    """Coverage trend data over time"""
    component: str
    test_suite: str
    timestamps: List[datetime]
    coverage_percentages: List[float]
    target_coverage: float = 95.0
@dataclass
class CoverageReport:
    """Comprehensive coverage report"""
    generated_at: datetime
    overall_coverage: float
    components: Dict[str, CoverageMetrics]
    trends: List[CoverageTrend]
    recommendations: List[str]
    alerts: List[Dict[str, Any]]
class CoverageDatabase:
    """SQLite database for storing coverage metrics"""
    def __init__(self, db_path: str = "coverage_metrics.db"):
        self.db_path = db_path
        self.init_database()
    def init_database(self):
        """Initialize coverage metrics database"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coverage_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    test_suite TEXT NOT NULL,
                    component TEXT NOT NULL,
                    lines_covered INTEGER NOT NULL,
                    lines_total INTEGER NOT NULL,
                    branches_covered INTEGER NOT NULL,
                    branches_total INTEGER NOT NULL,
                    functions_covered INTEGER NOT NULL,
                    functions_total INTEGER NOT NULL,
                    files_analyzed INTEGER NOT NULL,
                    coverage_percentage REAL NOT NULL,
                    missing_lines TEXT,
                    git_commit TEXT,
                    build_number TEXT
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coverage_targets (
                    component TEXT PRIMARY KEY,
                    target_coverage REAL NOT NULL,
                    minimum_coverage REAL NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            # Insert default targets if they don't exist
            targets = [
                ("unified_mcp", 95.0, 85.0),
                ("", 95.0, 85.0),
                ("bi_server", 90.0, 80.0),
                ("mem0", 95.0, 85.0),
                ("base_mcp", 95.0, 85.0),
                ("overall", 93.0, 83.0),
            ]
            for component, target, minimum in targets:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO coverage_targets 
                    (component, target_coverage, minimum_coverage, updated_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (component, target, minimum, datetime.now().isoformat()),
                )
            conn.commit()
        finally:
            conn.close()
    def store_coverage(
        self, metrics: CoverageMetrics, git_commit: str = None, build_number: str = None
    ):
        """Store coverage metrics"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO coverage_metrics 
                (timestamp, test_suite, component, lines_covered, lines_total,
                 branches_covered, branches_total, functions_covered, functions_total,
                 files_analyzed, coverage_percentage, missing_lines, git_commit, build_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metrics.timestamp.isoformat(),
                    metrics.test_suite,
                    metrics.component,
                    metrics.lines_covered,
                    metrics.lines_total,
                    metrics.branches_covered,
                    metrics.branches_total,
                    metrics.functions_covered,
                    metrics.functions_total,
                    metrics.files_analyzed,
                    metrics.coverage_percentage,
                    json.dumps(metrics.missing_lines),
                    git_commit,
                    build_number,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    def get_latest_coverage(
        self, component: str = None, test_suite: str = None
    ) -> List[CoverageMetrics]:
        """Get latest coverage metrics"""
        conn = sqlite3.connect(self.db_path)
        try:
            query = """
                SELECT timestamp, test_suite, component, lines_covered, lines_total,
                       branches_covered, branches_total, functions_covered, functions_total,
                       files_analyzed, coverage_percentage, missing_lines
                FROM coverage_metrics
                WHERE 1=1
            """
            params = []
            if component:
                query += " AND component = ?"
                params.append(component)
            if test_suite:
                query += " AND test_suite = ?"
                params.append(test_suite)
            query += " ORDER BY timestamp DESC LIMIT 50"
            cursor = conn.execute(query, params)
            results = []
            for row in cursor.fetchall():
                results.append(
                    CoverageMetrics(
                        timestamp=datetime.fromisoformat(row[0]),
                        test_suite=row[1],
                        component=row[2],
                        lines_covered=row[3],
                        lines_total=row[4],
                        branches_covered=row[5],
                        branches_total=row[6],
                        functions_covered=row[7],
                        functions_total=row[8],
                        files_analyzed=row[9],
                        coverage_percentage=row[10],
                        missing_lines=json.loads(row[11]) if row[11] else [],
                    )
                )
            return results
        finally:
            conn.close()
    def get_coverage_trends(self, days: int = 30) -> List[CoverageTrend]:
        """Get coverage trends over time"""
        conn = sqlite3.connect(self.db_path)
        try:
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor = conn.execute(
                """
                SELECT component, test_suite, timestamp, coverage_percentage
                FROM coverage_metrics
                WHERE timestamp >= ?
                ORDER BY component, test_suite, timestamp
            """,
                (since_date,),
            )
            # Group by component and test suite
            trends_data = {}
            for row in cursor.fetchall():
                key = (row[0], row[1])  # (component, test_suite)
                if key not in trends_data:
                    trends_data[key] = {"timestamps": [], "coverages": []}
                trends_data[key]["timestamps"].append(datetime.fromisoformat(row[2]))
                trends_data[key]["coverages"].append(row[3])
            trends = []
            for (component, test_suite), data in trends_data.items():
                trends.append(
                    CoverageTrend(
                        component=component,
                        test_suite=test_suite,
                        timestamps=data["timestamps"],
                        coverage_percentages=data["coverages"],
                    )
                )
            return trends
        finally:
            conn.close()
    def get_coverage_targets(self) -> Dict[str, Tuple[float, float]]:
        """Get coverage targets for components"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT component, target_coverage, minimum_coverage
                FROM coverage_targets
            """
            )
            targets = {}
            for row in cursor.fetchall():
                targets[row[0]] = (row[1], row[2])  # (target, minimum)
            return targets
        finally:
            conn.close()
class CoverageCollector:
    """Collects coverage data from various test suites"""
    def __init__(self, db: CoverageDatabase):
        self.db = db
        self.logger = self._setup_logger()
    def _setup_logger(self) -> logging.Logger:
        """Set up logging"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    async def collect_all_coverage(self) -> CoverageReport:
        """Collect coverage from all test suites"""
        self.logger.info("Starting comprehensive coverage collection...")
        # Test suites to run
        test_suites = [
            (
                "unit",
                "tests/unit/",
                [
                    "test_unified_mcp_server.py",
                    "test__swarm_orchestrator.py",
                    "test_business_intelligence_server.py",
                    "test_mem0_memory_server.py",
                    "test_base_mcp_server_library.py",
                ],
            ),
            ("integration", "tests/integration/", ["test_mcp_servers_integration.py"]),
            ("e2e", "tests/e2e/", ["test_complete_user_workflows.py"]),
            ("performance", "tests/performance/", ["test_performance_regression.py"]),
            ("security", "tests/security/", ["test_security_vulnerabilities.py"]),
        ]
        all_metrics = []
        for suite_name, suite_path, test_files in test_suites:
            self.logger.info(f"Collecting coverage for {suite_name} tests...")
            suite_metrics = await self.collect_suite_coverage(
                suite_name, suite_path, test_files
            )
            all_metrics.extend(suite_metrics)
        # Generate comprehensive report
        report = await self.generate_report(all_metrics)
        self.logger.info("Coverage collection completed")
        return report
    async def collect_suite_coverage(
        self, suite_name: str, suite_path: str, test_files: List[str]
    ) -> List[CoverageMetrics]:
        """Collect coverage for a specific test suite"""
        metrics = []
        if not os.path.exists(suite_path):
            self.logger.warning(f"Test suite path does not exist: {suite_path}")
            return metrics
        for test_file in test_files:
            test_path = os.path.join(suite_path, test_file)
            if os.path.exists(test_path):
                try:
                    # Run coverage analysis
                    coverage_data = await self._run_coverage_analysis(
                        suite_name, test_path
                    )
                    if coverage_data:
                        # Determine component from test file name
                        component = self._extract_component_name(test_file)
                        metric = CoverageMetrics(
                            timestamp=datetime.now(),
                            test_suite=suite_name,
                            component=component,
                            **coverage_data,
                        )
                        metrics.append(metric)
                        self.db.store_coverage(
                            metric, self._get_git_commit(), self._get_build_number()
                        )
                        self.logger.info(
                            f"Collected coverage for {component}/{suite_name}: {metric.coverage_percentage:.1f}%"
                        )
                except Exception as e:
                    self.logger.error(f"Error collecting coverage for {test_file}: {e}")
            else:
                self.logger.warning(f"Test file not found: {test_path}")
        return metrics
    async def _run_coverage_analysis(
        self, suite_name: str, test_path: str
    ) -> Optional[Dict[str, Any]]:
        """Run coverage analysis for a specific test file"""
        try:
            # Create coverage configuration
            coverage_config = """
[run]
source = .
omit = 
    */tests/*
    */venv/*
    */env/*
    */__pycache__/*
    */migrations/*
    setup.py
    conftest.py
[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
"""
            # Write coverage config
            with open(".coveragerc", "w") as f:
                f.write(coverage_config)
            # Run tests with coverage
            cmd = [
                sys.executable,
                "-m",
                "coverage",
                "run",
                "--rcfile=.coveragerc",
                f"--source={self._get_source_dirs()}",
                "-m",
                "pytest",
                test_path,
                "-v",
                "--tb=short",
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                self.logger.warning(f"Test execution failed: {stderr.decode()}")
                # Continue with coverage analysis even if some tests fail
            # Generate coverage report
            report_process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "coverage",
                "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            report_stdout, report_stderr = await report_process.communicate()
            if report_process.returncode == 0:
                # Load coverage data
                with open("coverage.json") as f:
                    coverage_data = json.load(f)
                return self._parse_coverage_data(coverage_data)
            else:
                self.logger.error(
                    f"Coverage report generation failed: {report_stderr.decode()}"
                )
                return None
        except Exception as e:
            self.logger.error(f"Coverage analysis failed: {e}")
            return None
        finally:
            # Clean up
            for file in [".coveragerc", "coverage.json", ".coverage"]:
                if os.path.exists(file):
                    os.remove(file)
    def _parse_coverage_data(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse coverage.py JSON output"""
        totals = coverage_data.get("totals", {})
        return {
            "lines_covered": totals.get("covered_lines", 0),
            "lines_total": totals.get("num_statements", 0),
            "branches_covered": totals.get("covered_branches", 0),
            "branches_total": totals.get("num_branches", 0),
            "functions_covered": 0,  # Not directly available in coverage.py
            "functions_total": 0,
            "files_analyzed": len(coverage_data.get("files", {})),
            "coverage_percentage": totals.get("percent_covered", 0.0),
            "missing_lines": self._extract_missing_lines(coverage_data),
        }
    def _extract_missing_lines(self, coverage_data: Dict[str, Any]) -> List[str]:
        """Extract missing lines from coverage data"""
        missing_lines = []
        for filename, file_data in coverage_data.get("files", {}).items():
            if "missing_lines" in file_data and file_data["missing_lines"]:
                for line_num in file_data["missing_lines"]:
                    missing_lines.append(f"{filename}:{line_num}")
        return missing_lines
    def _extract_component_name(self, test_filename: str) -> str:
        """Extract component name from test filename"""
        if "unified_mcp" in test_filename:
            return "unified_mcp"
        elif "" in test_filename:
            return ""
        elif "business_intelligence" in test_filename:
            return "bi_server"
        elif "mem0" in test_filename:
            return "mem0"
        elif "base_mcp" in test_filename:
            return "base_mcp"
        else:
            return "unknown"
    def _get_source_dirs(self) -> str:
        """Get source directories for coverage analysis"""
        return ",".join(["backend", "asip", "agents", "mcp_servers"])
    def _get_git_commit(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "unknown"
    def _get_build_number(self) -> str:
        """Get build number from environment"""
        return os.environ.get("GITHUB_RUN_NUMBER", "local")
    async def generate_report(self, metrics: List[CoverageMetrics]) -> CoverageReport:
        """Generate comprehensive coverage report"""
        components = {}
        overall_lines_covered = 0
        overall_lines_total = 0
        # Group metrics by component
        for metric in metrics:
            if metric.component not in components:
                components[metric.component] = []
            components[metric.component].append(metric)
            overall_lines_covered += metric.lines_covered
            overall_lines_total += metric.lines_total
        # Calculate overall coverage
        overall_coverage = (
            (overall_lines_covered / overall_lines_total * 100)
            if overall_lines_total > 0
            else 0
        )
        # Get trends
        trends = self.db.get_coverage_trends(30)
        # Generate recommendations and alerts
        targets = self.db.get_coverage_targets()
        recommendations = []
        alerts = []
        for component, component_metrics in components.items():
            avg_coverage = sum(m.coverage_percentage for m in component_metrics) / len(
                component_metrics
            )
            target_coverage, min_coverage = targets.get(component, (95.0, 85.0))
            if avg_coverage < min_coverage:
                alerts.append(
                    {
                        "type": "critical",
                        "component": component,
                        "message": f"{component} coverage {avg_coverage:.1f}% below minimum threshold {min_coverage:.1f}%",
                    }
                )
            elif avg_coverage < target_coverage:
                alerts.append(
                    {
                        "type": "warning",
                        "component": component,
                        "message": f"{component} coverage {avg_coverage:.1f}% below target {target_coverage:.1f}%",
                    }
                )
            # Find files with low coverage
            for metric in component_metrics:
                if metric.missing_lines:
                    recommendations.append(
                        f"Add tests for {component} - {len(metric.missing_lines)} uncovered lines"
                    )
        return CoverageReport(
            generated_at=datetime.now(),
            overall_coverage=overall_coverage,
            components={
                comp: metrics[0] for comp, metrics in components.items()
            },  # Latest metric per component
            trends=trends,
            recommendations=recommendations[:10],  # Top 10 recommendations
            alerts=alerts,
        )
class CoverageDashboard:
    """Web dashboard for coverage visualization"""
    def __init__(self, db: CoverageDatabase):
        self.db = db
        self.app = Flask(__name__) if FLASK_AVAILABLE else None
        self.socketio = SocketIO(self.app) if FLASK_AVAILABLE else None
        if self.app:
            self._setup_routes()
    def _setup_routes(self):
        """Set up Flask routes"""
        @self.app.route("/")
        def index():
            return render_template("coverage_dashboard.html")
        @self.app.route("/api/coverage/latest")
        def latest_coverage():
            metrics = self.db.get_latest_coverage()
            return jsonify([asdict(m) for m in metrics])
        @self.app.route("/api/coverage/component/<component>")
        def component_coverage(component):
            metrics = self.db.get_latest_coverage(component=component)
            return jsonify([asdict(m) for m in metrics])
        @self.app.route("/api/coverage/trends")
        def coverage_trends():
            days = request.args.get("days", 30, type=int)
            trends = self.db.get_coverage_trends(days)
            return jsonify([asdict(t) for t in trends])
        @self.app.route("/api/coverage/report")
        def coverage_report():
            # Get latest coverage data
            collector = CoverageCollector(self.db)
            # This would be done asynchronously in a real scenario
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            report = loop.run_until_complete(
                collector.generate_report(self.db.get_latest_coverage())
            )
            return jsonify(asdict(report))
        @self.app.route("/api/coverage/charts/overview")
        def coverage_overview_chart():
            if not PLOTLY_AVAILABLE:
                return jsonify({"error": "Plotly not available"})
            metrics = self.db.get_latest_coverage()
            # Group by component
            components = {}
            for metric in metrics:
                if metric.component not in components:
                    components[metric.component] = []
                components[metric.component].append(metric.coverage_percentage)
            # Calculate average coverage per component
            component_names = []
            coverage_values = []
            for component, coverages in components.items():
                component_names.append(component)
                coverage_values.append(sum(coverages) / len(coverages))
            # Create bar chart
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=component_names,
                        y=coverage_values,
                        marker_color=[
                            "red" if c < 80 else "orange" if c < 90 else "green"
                            for c in coverage_values
                        ],
                    )
                ]
            )
            fig.update_layout(
                title="Test Coverage by Component",
                xaxis_title="Component",
                yaxis_title="Coverage Percentage",
                yaxis=dict(range=[0, 100]),
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        @self.app.route("/api/coverage/charts/trends")
        def coverage_trends_chart():
            if not PLOTLY_AVAILABLE:
                return jsonify({"error": "Plotly not available"})
            trends = self.db.get_coverage_trends(30)
            fig = go.Figure()
            for trend in trends:
                fig.add_trace(
                    go.Scatter(
                        x=trend.timestamps,
                        y=trend.coverage_percentages,
                        name=f"{trend.component} ({trend.test_suite})",
                        mode="lines+markers",
                    )
                )
            fig.update_layout(
                title="Coverage Trends (Last 30 Days)",
                xaxis_title="Date",
                yaxis_title="Coverage Percentage",
                yaxis=dict(range=[0, 100]),
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        @self.socketio.on("request_realtime_coverage")
        def handle_realtime_request():
            # Emit real-time coverage updates
            self.emit_coverage_update()
    def emit_coverage_update(self):
        """Emit real-time coverage update via WebSocket"""
        if self.socketio:
            latest_metrics = self.db.get_latest_coverage()
            self.socketio.emit(
                "coverage_update",
                {
                    "timestamp": datetime.now().isoformat(),
                    "metrics": [
                        asdict(m) for m in latest_metrics[:5]
                    ],  # Latest 5 metrics
                },
            )
    def create_dashboard_template(self):
        """Create HTML template for the dashboard"""
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        os.makedirs(template_dir, exist_ok=True)
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Coverage Dashboard - Sophia AI</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .coverage-card { margin-bottom: 20px; }
        .coverage-high { border-left: 5px solid #28a745; }
        .coverage-medium { border-left: 5px solid #ffc107; }
        .coverage-low { border-left: 5px solid #dc3545; }
        .chart-container { height: 400px; margin-bottom: 30px; }
        .real-time-indicator { 
            display: inline-block;
            width: 10px;
            height: 10px;
            background-color: #28a745;
            border-radius: 50%;
            animation: blink 2s infinite;
        }
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-12">
                <h1 class="mb-4">
                    Test Coverage Dashboard 
                    <small class="text-muted">
                        <span class="real-time-indicator"></span> Live Updates
                    </small>
                </h1>
            </div>
        </div>
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>Coverage Overview by Component</h5>
                    </div>
                    <div class="card-body">
                        <div id="overview-chart" class="chart-container"></div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card coverage-card">
                    <div class="card-header">
                        <h6>Overall Coverage</h6>
                    </div>
                    <div class="card-body">
                        <h2 id="overall-coverage" class="text-center">--%</h2>
                        <div class="progress">
                            <div id="overall-progress" class="progress-bar" role="progressbar"></div>
                        </div>
                    </div>
                </div>
                <div class="card coverage-card">
                    <div class="card-header">
                        <h6>Coverage Alerts</h6>
                    </div>
                    <div class="card-body">
                        <div id="alerts-container">
                            <p class="text-muted">Loading alerts...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Coverage Trends</h5>
                    </div>
                    <div class="card-body">
                        <div id="trends-chart" class="chart-container"></div>
                    </div>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Component Details</h5>
                    </div>
                    <div class="card-body">
                        <div id="components-table" class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Component</th>
                                        <th>Test Suite</th>
                                        <th>Coverage</th>
                                        <th>Lines</th>
                                        <th>Branches</th>
                                        <th>Last Updated</th>
                                    </tr>
                                </thead>
                                <tbody id="components-tbody">
                                    <tr><td colspan="6" class="text-center">Loading...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        // Initialize Socket.IO for real-time updates
        const socket = io();
        // Load initial data
        loadDashboard();
        // Set up real-time updates
        socket.on('coverage_update', function(data) {
            updateRealTimeData(data);
        });
        function loadDashboard() {
            loadOverviewChart();
            loadTrendsChart();
            loadComponentsTable();
            loadCoverageReport();
        }
        function loadOverviewChart() {
            fetch('/api/coverage/charts/overview')
                .then(response => response.json())
                .then(data => {
                    Plotly.newPlot('overview-chart', data.data, data.layout);
                });
        }
        function loadTrendsChart() {
            fetch('/api/coverage/charts/trends')
                .then(response => response.json())
                .then(data => {
                    Plotly.newPlot('trends-chart', data.data, data.layout);
                });
        }
        function loadComponentsTable() {
            fetch('/api/coverage/latest')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('components-tbody');
                    tbody.innerHTML = '';
                    data.forEach(metric => {
                        const row = tbody.insertRow();
                        const coverageClass = metric.coverage_percentage >= 90 ? 'text-success' :
                                            metric.coverage_percentage >= 80 ? 'text-warning' : 'text-danger';
                        row.innerHTML = `
                            <td>${metric.component}</td>
                            <td>${metric.test_suite}</td>
                            <td class="${coverageClass}">${metric.coverage_percentage.toFixed(1)}%</td>
                            <td>${metric.lines_covered}/${metric.lines_total}</td>
                            <td>${metric.branches_covered}/${metric.branches_total}</td>
                            <td>${new Date(metric.timestamp).toLocaleString()}</td>
                        `;
                    });
                });
        }
        function loadCoverageReport() {
            fetch('/api/coverage/report')
                .then(response => response.json())
                .then(data => {
                    // Update overall coverage
                    document.getElementById('overall-coverage').textContent = 
                        data.overall_coverage.toFixed(1) + '%';
                    const progressBar = document.getElementById('overall-progress');
                    progressBar.style.width = data.overall_coverage + '%';
                    progressBar.className = `progress-bar ${
                        data.overall_coverage >= 90 ? 'bg-success' :
                        data.overall_coverage >= 80 ? 'bg-warning' : 'bg-danger'
                    }`;
                    // Update alerts
                    const alertsContainer = document.getElementById('alerts-container');
                    alertsContainer.innerHTML = '';
                    if (data.alerts.length === 0) {
                        alertsContainer.innerHTML = '<p class="text-success">No coverage alerts</p>';
                    } else {
                        data.alerts.forEach(alert => {
                            const alertDiv = document.createElement('div');
                            alertDiv.className = `alert alert-${
                                alert.type === 'critical' ? 'danger' : 'warning'
                            } alert-sm`;
                            alertDiv.textContent = alert.message;
                            alertsContainer.appendChild(alertDiv);
                        });
                    }
                });
        }
        function updateRealTimeData(data) {
            // Update components table with real-time data
            loadComponentsTable();
            // Show notification of update
            showNotification('Coverage data updated', 'info');
        }
        function showNotification(message, type) {
            // Simple notification system
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.body.appendChild(notification);
            // Auto-remove after 3 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 3000);
        }
        // Request real-time updates
        socket.emit('request_realtime_coverage');
        // Refresh data every 5 minutes
        setInterval(loadDashboard, 5 * 60 * 1000);
    </script>
</body>
</html>
        """
        template_path = os.path.join(template_dir, "coverage_dashboard.html")
        with open(template_path, "w") as f:
            f.write(html_template)
        return template_path
    def run(self, host="${BIND_IP}", port=5000, debug=False):
        """Run the dashboard server"""
        if not self.app:
            print("Flask not available. Cannot run dashboard.")
            return
        # Create template
        self.create_dashboard_template()
        print(f"🚀 Starting Test Coverage Dashboard on http://{host}:{port}")
        print("📊 Dashboard features:")
        print("   - Real-time coverage updates")
        print("   - Interactive charts and graphs")
        print("   - Component-wise coverage breakdown")
        print("   - Historical trends analysis")
        print("   - Coverage alerts and recommendations")
        if self.socketio:
            self.socketio.run(self.app, host=host, port=port, debug=debug)
        else:
            self.app.run(host=host, port=port, debug=debug)
async def main():
    """Main function for CLI usage"""
    import argparse
    parser = argparse.ArgumentParser(description="Test Coverage Dashboard")
    parser.add_argument("--collect", action="store_true", help="Collect coverage data")
    parser.add_argument("--dashboard", action="store_true", help="Run web dashboard")
    parser.add_argument("--port", type=int, default=5000, help="Dashboard port")
    parser.add_argument("--host", type=str, default="${BIND_IP}", help="Dashboard host")
    parser.add_argument(
        "--db", type=str, default="coverage_metrics.db", help="Database path"
    )
    args = parser.parse_args()
    # Initialize database
    db = CoverageDatabase(args.db)
    if args.collect:
        # Collect coverage data
        collector = CoverageCollector(db)
        report = await collector.collect_all_coverage()
        print("📊 Coverage Collection Complete!")
        print(f"   Overall Coverage: {report.overall_coverage:.1f}%")
        print(f"   Components Analyzed: {len(report.components)}")
        print(f"   Alerts: {len(report.alerts)}")
        if report.alerts:
            print("\n⚠️  Coverage Alerts:")
            for alert in report.alerts:
                print(f"   - {alert['type'].upper()}: {alert['message']}")
    if args.dashboard:
        # Run dashboard
        dashboard = CoverageDashboard(db)
        dashboard.run(host=args.host, port=args.port)
    if not args.collect and not args.dashboard:
        print(
            "Use --collect to gather coverage data or --dashboard to run web interface"
        )
if __name__ == "__main__":
    asyncio.run(main())
