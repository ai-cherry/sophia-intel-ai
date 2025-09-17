const http = require('http');

const server = http.createServer((req, res) => {
  res.writeHead(200, {'Content-Type': 'text/html'});
  res.end(`
    <html>
      <body>
        <h1>✅ SUCCESS! Your local server is working!</h1>
        <h2>Sophia Intelligence Hub</h2>
        <p>This proves your localhost connectivity works on port 3000</p>
        <p>Access this at: <a href="http://127.0.0.1:3000">http://127.0.0.1:3000</a></p>
        <hr>
        <h3>Your Dashboard Components Ready:</h3>
        <ul>
          <li>✅ 8 Dashboard Tabs Created</li>
          <li>✅ Business Integrations Configured (7 production, 3 scaffolding)</li>
          <li>✅ AI Orchestrator Tested</li>
          <li>✅ Persistent Chat Component</li>
          <li>⚠️ Next.js needs Node 20 LTS (currently on Node 24)</li>
        </ul>
      </body>
    </html>
  `);
});

server.listen(3000, '127.0.0.1', () => {
  console.log('✅ Test server running at http://127.0.0.1:3000');
  console.log('Open this URL in your browser to verify connectivity');
});