import unittest
from flask import Flask
#from flask_restx import inputs
from vimmo.utils.parser import IDParser#, PatientParser, DownloadParser


class TestIDParser(unittest.TestCase):
    """Unit tests for IDParser."""

    def setUp(self):
        """Set up a Flask app and context for testing."""
        self.app = Flask(__name__)
        self.parser = IDParser.create_parser()


    def test_valid_panel_id(self):
        """Test parsing with a valid Panel_ID."""
        with self.app.test_request_context('/?Panel_ID=123'):
            args = self.parser.parse_args()
            self.assertEqual(args['Panel_ID'], '123')
            self.assertIsNone(args['Rcode'])
            self.assertIsNone(args['HGNC_ID'])
            self.assertFalse(args['Similar_Matches'])  # Default value is False

    def test_similar_matches_argument(self):
        """Test parsing with Similar_Matches set to true."""
        with self.app.test_request_context('/?Similar_Matches=true'):
            args = self.parser.parse_args()
            self.assertTrue(args['Similar_Matches'])

    def test_multiple_exclusive_arguments(self):
        """Test passing multiple exclusive arguments."""
        with self.app.test_request_context('/?Panel_ID=123&Rcode=R456'):
            args = self.parser.parse_args()
            self.assertEqual(args['Panel_ID'], '123')  # Both arguments are parsed
            self.assertEqual(args['Rcode'], 'R456')

    def test_default_values(self):
        """Test default behavior when no arguments are passed."""
        with self.app.test_request_context('/'):
            args = self.parser.parse_args()
            self.assertIsNone(args['Panel_ID'])
            self.assertIsNone(args['Rcode'])
            self.assertIsNone(args['HGNC_ID'])
            self.assertFalse(args['Similar_Matches'])  # Default value


# class TestPatientParser(unittest.TestCase):
#     """Unit tests for PatientParser."""
#
#     def setUp(self):
#         """Set up a Flask app and context for testing."""
#         self.app = Flask(__name__)
#         self.parser = PatientParser.create_parser()
#
#     def test_patient_id(self):
#         """Test parsing with a valid Patient ID."""
#         with self.app.test_request_context('/?Patient_ID=PAT123'):
#             args = self.parser.parse_args()
#             self.assertEqual(args['-f'], 'PAT123')
#
#     def test_rcode_argument(self):
#         """Test parsing with a valid R code."""
#         with self.app.test_request_context('/?R%20code=R456'):
#             args = self.parser.parse_args()
#             self.assertEqual(args['R code'], 'R456')
#
#
# class TestDownloadParser(unittest.TestCase):
#     """Unit tests for DownloadParser."""
#
#     def setUp(self):
#         """Set up a Flask app and context for testing."""
#         self.app = Flask(__name__)
#         self.parser = DownloadParser.create_parser()
#
#     def test_genome_build_argument(self):
#         """Test parsing with valid genome_build."""
#         with self.app.test_request_context('/?genome_build=GRCh37'):
#             args = self.parser.parse_args()
#             self.assertEqual(args['genome_build'], 'GRCh37')
#
#     def test_transcript_set_argument(self):
#         """Test parsing with valid transcript_set."""
#         with self.app.test_request_context('/?transcript_set=ensembl'):
#             args = self.parser.parse_args()
#             self.assertEqual(args['transcript_set'], 'ensembl')
#
#     def test_limit_transcripts_argument(self):
#         """Test parsing with a valid limit_transcripts value."""
#         with self.app.test_request_context('/?limit_transcripts=canonical'):
#             args = self.parser.parse_args()
#             self.assertEqual(args['limit_transcripts'], 'canonical')
#
#     def test_missing_required_arguments(self):
#         """Test parsing when required arguments are missing."""
#         with self.app.test_request_context('/?genome_build=GRCh38'):
#             with self.assertRaises(ValueError):
#                 self.parser.parse_args()
#
#     def test_invalid_choice_for_genome_build(self):
#         """Test invalid choice for genome_build."""
#         with self.app.test_request_context('/?genome_build=invalid_build'):
#             with self.assertRaises(ValueError):
#                 self.parser.parse_args()
#

if __name__ == '__main__':
    unittest.main()
