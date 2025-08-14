"""
Tests for the natural language interface to the Swarm system
"""

import unittest
from unittest.mock import patch, MagicMock

from swarm.nl_interface import process_natural_language


class TestNaturalLanguageInterface(unittest.TestCase):
    """Test cases for the Swarm natural language interface"""

    @patch("swarm.nl_interface.run")
    def test_process_natural_language(self, mock_run):
        """Test that the interface properly processes a natural language query"""
        # Setup mock return value
        mock_results = {
            "architect": "Architecture design completed",
            "builder": "Implementation completed",
            "tester": "Tests passed",
            "operator": "Deployment successful"
        }
        mock_run.return_value = mock_results

        # Call the function
        query = "Create a new API endpoint for user authentication"
        results = process_natural_language(query)

        # Verify the swarm was called with the query
        mock_run.assert_called_once_with(query)

        # Verify the results match what was returned by the swarm
        self.assertEqual(results, mock_results)
        self.assertEqual(len(results), 4)
        self.assertIn("architect", results)
        self.assertIn("builder", results)
        self.assertIn("tester", results)
        self.assertIn("operator", results)


if __name__ == "__main__":
    unittest.main()
