import unittest
from unittest.mock import patch
from flask import Flask
from vimmo.API import api
from vimmo.utils.panelapp import PanelAppClient
from vimmo.utils.variantvalidator import VarValClient
from vimmo.db.db import Query

# Assuming you've set up Flask app in `app.py`
from your_flask_app import app


class TestEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()  # Create a test client for your app
        self.app = app

    # Test PanelSearch endpoint with valid parameters
    @patch.object(Query, 'get_panel_data', return_value={"panel_id": "P123", "genes": ["GENE1", "GENE2"]})
    def test_panel_search_valid(self):
        response = self.client.get('/panels/', query_string={'Panel_ID': 'P123'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('panel_id', response.json)
        self.assertEqual(response.json['panel_id'], 'P123')

    # Test PanelSearch endpoint with invalid parameters
    def test_panel_search_invalid(self):
        response = self.client.get('/panels/', query_string={'Invalid_Param': 'Value'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    # Test PanelDownload endpoint with valid parameters
    @patch.object(VarValClient, 'parse_to_bed', return_value="test_bed_data")
    @patch.object(Query, 'get_panel_data', return_value={"panel_id": "P123", "genes": ["GENE1", "GENE2"]})
    def test_panel_download_valid(self):
        response = self.client.get('/panels/download', query_string={'Panel_ID': 'P123'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/plain')
        self.assertIn('Content-Disposition', response.headers)

    # Test PanelDownload endpoint with invalid parameters
    def test_panel_download_invalid(self):
        response = self.client.get('/panels/download', query_string={'Invalid_Param': 'Value'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    # Test LocalPanelDownload endpoint with valid parameters
    @patch.object(Query, 'local_bed', return_value=["local_bed_data"])
    @patch('vimmo.utils.localbed.local_bed_formatter', return_value="local_bed_file_content")
    def test_local_panel_download_valid(self):
        response = self.client.get('/panels/download/local', query_string={'Panel_ID': 'P123'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/plain')
        self.assertIn('Content-Disposition', response.headers)

    # Test LocalPanelDownload endpoint with invalid parameters
    def test_local_panel_download_invalid(self):
        response = self.client.get('/panels/download/local', query_string={'Invalid_Param': 'Value'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    # Test Patient search with valid patient ID
    @patch.object(Query, 'return_all_records', return_value=[{'test': 'record'}])
    def test_patient_search_valid(self):
        response = self.client.get('/patient/patient', query_string={'Patient ID': 'P456'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Patient ID', response.json)
        self.assertEqual(response.json['Patient ID'], 'P456')

    # Test Patient search with missing patient ID
    def test_patient_search_invalid(self):
        response = self.client.get('/patient/patient', query_string={'Invalid_Param': 'Value'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)


if __name__ == '__main__':
    unittest.main()
