from unittest.mock import MagicMock, patch

from app.swarms.mcp.production_mcp_bridge import ProductionMCPBridge


class TestMCPBridge:
    @patch('aiohttp.ClientSession.post')
    async def test_code_review(self, mock_post):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'suggestions': [
                {'type': 'Performance', 'location': 'Line 15', 'description': 'Consider using a more efficient algorithm', 'fix': 'Replace for loop with array.map()'}
            ],
            'metrics': {
                'complexity': 'Medium',
                'readability': 75,
                'bug_risk': 'Low'
            }
        }
        mock_post.return_value = mock_response

        bridge = ProductionMCPBridge()
        result = await bridge.code_review("test code")
        assert result == mock_response.json.return_value

    @patch('aiohttp.ClientSession.post')
    async def test_quality_check(self, mock_post):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'quality_report': 'Test report'
        }
        mock_post.return_value = mock_response

        bridge = ProductionMCPBridge()
        result = await bridge.quality_check("http://localhost:8501")
        assert result == mock_response.json.return_value

    @patch('aiohttp.ClientSession.get')
    async def test_swarm_status(self, mock_get):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'status': 'active',
            'agents': [
                {'id': 'agent-1', 'status': 'online', 'last_active': '2025-09-02T18:26:49.231Z'}
            ]
        }
        mock_get.return_value = mock_response

        bridge = ProductionMCPBridge()
        result = await bridge.swarm_status()
        assert result == mock_response.json.return_value
