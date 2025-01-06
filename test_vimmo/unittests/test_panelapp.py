import requests
import unittest
from unittest.mock import patch
from vimmo.utils.panelapp import PanelAppClient, PanelAppAPIError


class TestPanelAppClient(unittest.TestCase):

    # Test for the _check_response method (using a mock response)
    @patch('requests.get')
    def test_check_response_success(self, mock_get):
        # Mock the response to return a valid JSON with status code 200
        mock_response = {'results': []}  # Sample mock data
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        client = PanelAppClient()
        result = client._check_response('https://panelapp.genomicsengland.co.uk/api/v1/panels')
        self.assertEqual(result, mock_response)

    @patch('requests.get')
    def test_check_response_http_error(self, mock_get):
        # Simulate an HTTP error (e.g., 404 Not Found)
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")

        client = PanelAppClient()
        with self.assertRaises(PanelAppAPIError):
            client._check_response('https://panelapp.genomicsengland.co.uk/api/v1/panels')

    @patch('requests.get')
    def test_check_response_request_exception(self, mock_get):
        # Simulate a network error (RequestException)
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        client = PanelAppClient()
        with self.assertRaises(PanelAppAPIError):
            client._check_response('https://panelapp.genomicsengland.co.uk/api/v1/panels')

    # Test for get_genes_HUGO method
    @patch('requests.get')
    def test_get_genes_hugo(self, mock_get):
        # Mock the API response for get_genes_HUGO
        mock_response = {
            "results": [
                {"gene_data": {"gene_symbol": "BRCA1"}},
                {"gene_data": {"gene_symbol": "TP53"}},
                {"gene_data": {"gene_symbol": "EGFR"}}
            ]
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        client = PanelAppClient()
        result = client.get_genes_HUGO('R123')
        self.assertEqual(result, ['BRCA1', 'TP53', 'EGFR'])

    # Test for get_genes_HGNC method
    @patch('requests.get')
    def test_get_genes_hgnc(self, mock_get):
        # Mock the API response for get_genes_HGNC
        mock_response = {
            "results": [
                {"gene_data": {"hgnc_id": "HGNC:1234"}, "confidence_level": "3"},
                {"gene_data": {"hgnc_id": "HGNC:5678"}, "confidence_level": "1"},
                {"gene_data": {"hgnc_id": "HGNC:91011"}, "confidence_level": "2"}
            ]
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        client = PanelAppClient()
        result = client.get_genes_HGNC('R123')
        expected_result = {
            "HGNC:1234": "3",
            "HGNC:5678": "1",
            "HGNC:91011": "2"
        }
        self.assertEqual(result, expected_result)

    # Test for get_latest_online_version method
    @patch('requests.get')
    def test_get_latest_online_version(self, mock_get):
        # Mock the API response for get_latest_online_version
        mock_response = {
            "results": [{"version": "2.5"}]
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        client = PanelAppClient()
        result = client.get_latest_online_version('635')
        self.assertEqual(result, 2.5)

    @patch('requests.get')
    def test_get_latest_online_version_error(self, mock_get):
        # Simulate a missing or invalid version response
        mock_response = {"results": []}
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        client = PanelAppClient()
        with self.assertRaises(KeyError):
            client.get_latest_online_version('635')



    # Test for dowgrade_records method
    @patch('requests.get')
    def test_dowgrade_records(self, mock_get):
        # Mock the API response for dowgrade_records
        mock_response = {
            "results": [{"panel_id": "635", "version": "2.5"}]
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        client = PanelAppClient()
        result = client.dowgrade_records('635', '2.5')
        self.assertEqual(result, mock_response)

    @patch('requests.get')
    def test_dowgrade_records_error(self, mock_get):
        # Simulate an HTTP error (e.g., 404 Not Found)
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")

        client = PanelAppClient()
        with self.assertRaises(Exception):
            client.dowgrade_records('635', '2.5')


if __name__ == '__main__':
    unittest.main()