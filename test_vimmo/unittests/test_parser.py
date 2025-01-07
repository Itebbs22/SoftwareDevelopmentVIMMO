import unittest
from flask_restx import reqparse
from flask import Flask, request
from vimmo.utils.parser import (
    IDParser,
    PatientParser,
    PatientBedParser,
    DownloadParser,
    UpdateParser,
    LocalDownloadParser,
    PatientLocalBedParser,
    DowngradeParser
)


app = Flask(__name__)


class TestParsers(unittest.TestCase):

    def setUp(self):
        # Mock Flask app context
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()

    def tearDown(self):
        # Remove app context
        self.ctx.pop()

    def test_id_parser(self):
        with app.test_request_context('/test', method='GET', query_string={
            'Panel_ID': '12345',
            'Rcode': '',
            'HGNC_ID': '',
            'Similar_Matches': 'true',
            'Confidence': 'All'
        }):
            parser = IDParser.create_parser()
            args = parser.parse_args()
            self.assertEqual(args['Panel_ID'], '12345')
            self.assertEqual(args['Similar_Matches'], True)
            self.assertEqual(args['Confidence'], 'All')

    def test_patient_parser(self):
        with app.test_request_context('/test', method='GET', query_string={
            'Patient ID': 'P001',
            'R code': 'R123'
        }):
            parser = PatientParser.create_parser()
            args = parser.parse_args()
            self.assertEqual(args['Patient ID'], 'P001')
            self.assertEqual(args['R code'], 'R123')

    def test_patient_bed_parser(self):
        with app.test_request_context('/test', method='GET', query_string={
            'Patient ID': 'P002',
            'genome_build': 'GRCh38',
            'transcript_set': 'refseq',
            'limit_transcripts': 'mane_select'
        }):
            parser = PatientBedParser.create_parser()
            args = parser.parse_args()
            self.assertEqual(args['Patient ID'], 'P002')
            self.assertEqual(args['genome_build'], 'GRCh38')
            self.assertEqual(args['transcript_set'], 'refseq')
            self.assertEqual(args['limit_transcripts'], 'mane_select')

    def test_patient_local_bed_parser(self):
        with app.test_request_context('/test', method='GET', query_string={
            'Patient ID': 'P003',
            'genome_build': 'GRCh37',
            'transcript_set': 'Gencode',
            'limit_transcripts': 'all',
        }):
            parser = PatientLocalBedParser.create_parser()
            args = parser.parse_args()
            self.assertEqual(args['Patient ID'], 'P003')
            self.assertEqual(args['genome_build'], 'GRCh37')
            self.assertEqual(args['transcript_set'], 'Gencode')
            self.assertEqual(args['limit_transcripts'], 'all')

    def test_download_parser(self):
        with app.test_request_context('/test', method='GET', query_string={
            'Panel_ID': '12345',
            'genome_build': 'GRCh38',
            'transcript_set': 'all',
            'limit_transcripts': 'canonical',
            'Confidence': 'All'
        }):
            parser = DownloadParser.create_parser()
            args = parser.parse_args()
            self.assertEqual(args['Panel_ID'], '12345')
            self.assertEqual(args['genome_build'], 'GRCh38')
            self.assertEqual(args['transcript_set'], 'all')
            self.assertEqual(args['limit_transcripts'], 'canonical')
            self.assertEqual(args['Confidence'], 'All')

    def test_local_download_parser(self):
        with app.test_request_context('/test', method='GET', query_string={
            'Panel_ID': '12345',
            'genome_build': 'GRCh38',
            'transcript_set': 'Gencode',
            'limit_transcripts': 'all',
            'Confidence' : 'All'
        }):
            parser = LocalDownloadParser.create_parser()
            args = parser.parse_args()
            self.assertEqual(args['Panel_ID'], '12345')
            self.assertEqual(args['genome_build'], 'GRCh38')
            self.assertEqual(args['transcript_set'], 'Gencode')
            self.assertEqual(args['limit_transcripts'], 'all')
            self.assertEqual(args['Confidence'], 'All')

    def test_update_parser(self):
        with app.test_request_context('/test', method='POST', query_string={
            'Patient ID': 'P004',
            'R code': 'R124'
        }):
            parser = UpdateParser.create_parser()
            args = parser.parse_args()
            self.assertEqual(args['Patient ID'], 'P004')
            self.assertEqual(args['R code'], 'R124')

    def test_downgrade_parser(self):
        with app.test_request_context('/test', method='POST', query_string={
            'R_Code': 'R125',
            'version': '1.0.0'
        }):
            parser = DowngradeParser.create_parser()
            args = parser.parse_args()
            self.assertEqual(args['R_Code'], 'R125')
            self.assertEqual(args['version'], '1.0.0')


if __name__ == '__main__':
    unittest.main()
