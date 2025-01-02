"""
test_variant_validator.py - Test Suite for VariantValidator Client

This module contains tests for the VariantValidator client functionality while
handling Python's module loading complexities. The key challenge addressed here
is managing circular imports in a Flask application with multiple interdependent
modules.

Module Loading Process:
When Python imports modules, it follows a specific sequence:
1. Start loading the requested module
2. Process its imports from top to bottom
3. If an imported module tries to import something that's still loading,
   Python encounters a circular import error

The Problem:
In our application, we have the following import chain:
- variantvalidator.py needs get_db from vimmo.API
- vimmo.API/__init__.py imports endpoints.py
- endpoints.py imports VarValClient from variantvalidator.py

This creates a circular dependency that fails when testing because:
- Tests try to import VarValClient directly
- This triggers the import chain before the Flask app is initialized
- The partial imports cause Python to raise ImportError

The Solution:
We solve this by following the same initialization order as our main application:
1. First, we mock the database connection
2. Then we import the Flask app, which sets up the proper environment
3. Only after that do we import VarValClient

This mirrors how our production application loads modules and prevents
circular import issues while maintaining proper test isolation.
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock, call
from io import BytesIO
import pandas as pd
# Use patch to mock the imports
with patch('vimmo.API.app'):  # Ensures Flask/DB init order
    from vimmo.utils.variantvalidator import VarValClient, VarValAPIError



class TestVarValClient(unittest.TestCase):
    """
    Test suite for the VariantValidator API client.
    
    This class tests the functionality of the VarValClient including:
    - API communication
    - Data parsing and transformation
    - Error handling
    - BED file generation
    
    Each test method focuses on a specific aspect of the client's functionality
    while mocking external dependencies to ensure reliable testing.
    """

    def setUp(self):
        """
        Initialize test environment before each test.
        Creates a client instance and sets up common test data.
        """
        self.client = VarValClient()

    @patch('requests.get')
    def test_check_response_success(self, mock_get):
        """
        Test successful API response handling.
        Verifies that valid API responses are properly processed and returned.
        """
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {"test": "data"}
        
        result = self.client._check_response("test_url")
        self.assertEqual(result, {"test": "data"})

    @patch('requests.get', side_effect=Exception("Connection failed"))
    def test_check_response_connection_error(self, mock_get):
        """
        Test handling of connection failures.
        Ensures appropriate error handling when network connection fails.
        """
        with self.assertRaises(VarValAPIError) as context:
            self.client._check_response("test_url")
        self.assertIn("Failed to connect", str(context.exception))

    @patch('requests.get')
    def test_check_response_non_200(self, mock_get):
        """
        Test handling of non-200 status codes.
        Ensures that a VarValAPIError is raised if the response is not OK.
        """
        mock_get.return_value.ok = False
        mock_get.return_value.status_code = 404
        
        with self.assertRaises(VarValAPIError) as context:
            self.client._check_response("test_url")
        self.assertIn("Failed to get data from VarVal API with Status code:404", str(context.exception))

    def test_custom_sort(self):
        """
        Test the custom sorting function for BED file entries.
        
        Verifies correct sorting of:
        - Chromosome numbers
        - X and Y chromosomes
        - Error cases
        - Start/end coordinates
        """
        test_data = pd.DataFrame([
            {'chrom': 'chr1', 'start': '1000', 'end': '2000'},
            {'chrom': 'chrX', 'start': '500', 'end': '1500'},
            {'chrom': 'chr2', 'start': '750', 'end': '1750'},
            {'chrom': 'NoRecord', 'start': 'Error', 'end': 'Error'}
        ])

        # Test individual sorting keys
        self.assertEqual(
            self.client.custom_sort(test_data.iloc[0]),
            (1, 1000, 2000)
        )
        self.assertEqual(
            self.client.custom_sort(test_data.iloc[1]),
            (23, 500, 1500)  # 'X' chromosome -> 23
        )
        self.assertEqual(
            self.client.custom_sort(test_data.iloc[2]),
            (2, 750, 1750)
        )
        self.assertEqual(
            self.client.custom_sort(test_data.iloc[3]),
            (float('inf'), float('inf'), float('inf'))
        )

    def test_custom_sort_edge_cases(self):
        """
        Tests the custom_sort function's handling of non-standard chromosome names and coordinates.
        
        This comprehensive test verifies proper sorting behavior for:
        - Standard chromosomes (1-22, X, Y)
        - Mitochondrial DNA (MT)
        - Unplaced contigs (Un)
        - Empty or malformed chromosome names
        - Various coordinate formats
        
        The sorting function should maintain a consistent ordering while properly
        handling edge cases and invalid inputs.
        """
        test_data = pd.DataFrame([
            {'chrom': 'chr1', 'start': '1000', 'end': '2000'},
            {'chrom': 'chrMT', 'start': '500', 'end': '1500'},  # Mitochondrial
            {'chrom': 'chr23', 'start': '750', 'end': '1750'},  # Invalid chromosome number
            {'chrom': 'chrUn', 'start': '100', 'end': '200'},   # Unplaced contig
            {'chrom': 'chr', 'start': '300', 'end': '400'},     # Missing chromosome number
            {'chrom': '', 'start': '1', 'end': ''}             # Empty chromosome and end
        ])

        # Test sorting of non-standard chromosomes
        self.assertEqual(
            self.client.custom_sort(test_data.iloc[1]),  # chrMT
            (float('inf'), 500, 1500)
        )
        self.assertEqual(
            self.client.custom_sort(test_data.iloc[4]),  # chr
            (float('inf'), 300, 400)
        )
        self.assertEqual(
            self.client.custom_sort(test_data.iloc[5]),  # empty
            (float('inf'), float('1'), float('inf'))
        )

    @patch('requests.get')
    def test_get_gene_data_success(self, mock_get):
        """
        Test successful retrieval of gene data via get_gene_data.
        Mocks requests.get to return a successful response.
        """
        mock_response_data = [{"mock": "gene_data"}]
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_response_data
        
        # 1) Call with BRCA1
        self.client.get_gene_data(
            gene_query="BRCA1",
            genome_build="GRCh38",
            transcript_set="all",
            limit_transcripts="mane_select"
        )

        # 2) Call with HGNC:1100
        self.client.get_gene_data(
            gene_query="HGNC:1100",
            genome_build="GRCh38",
            transcript_set="all",
            limit_transcripts="mane_select"
        )

        # The two expected function calls
        expected_url_brca = (
            "https://rest.variantvalidator.org/VariantValidator/tools/"
            "gene2transcripts_v2/BRCA1/mane_select/all/GRCh38"
        )
        expected_url_hgnc = (
            "https://rest.variantvalidator.org/VariantValidator/tools/"
            "gene2transcripts_v2/HGNC%3A1100/mane_select/all/GRCh38"
        )

        # Check only the function calls, ignoring the call().json() part
        expected_calls = [
            unittest.mock.call(expected_url_brca),
            unittest.mock.call(expected_url_hgnc),
        ]
        self.assertEqual(mock_get.call_args_list, expected_calls)

    @patch('requests.get')
    def test_get_gene_data_non_200(self, mock_get):
        """
        Test get_gene_data raises VarValAPIError when the API returns non-200.
        """
        mock_get.return_value.ok = False
        mock_get.return_value.status_code = 500

        with self.assertRaises(VarValAPIError) as context:
            self.client.get_gene_data("BRCA2")
        self.assertIn("Failed to get data from VarVal API with Status code:500", str(context.exception))

    @patch('builtins.open', new_callable=mock_open, read_data="HGNC:12345678\nHGNC:999\n")
    @patch('vimmo.utils.variantvalidator.Query')
    @patch('vimmo.utils.variantvalidator.get_db')
    def test_get_hgnc_ids_with_replacements(self, mock_get_db, mock_query_cls, mock_file):
        """
        Test that get_hgnc_ids_with_replacements correctly replaces 
        problematic HGNC IDs with their symbols if found in the DB.
        """
        # Mock the DB connection
        mock_db_instance = MagicMock()
        mock_db_instance.conn = "fake_connection"
        mock_get_db.return_value = mock_db_instance

        # Mock the query object to return pairs of (hgnc_id, hgnc_symbol)
        mock_query_instance = MagicMock()
        mock_query_instance.get_gene_symbol.return_value = [("HGNC:12345678", "TEST_symbol")]
        mock_query_cls.return_value = mock_query_instance
        
        # Call the method
        gene_query = ["HGNC:12345678", "HGNC:456"]
        result = self.client.get_hgnc_ids_with_replacements(gene_query)

        # "HGNC:123" should be replaced by "BRCA1_symbol"
        # "HGNC:456" remains as is
        self.assertIn("TEST_symbol", result)
        self.assertIn("HGNC:456", result)

        # Ensure the DB was called only for the problematic genes
        mock_query_instance.get_gene_symbol.assert_called_once_with(["HGNC:12345678"])

    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('vimmo.utils.variantvalidator.Query')
    @patch('vimmo.utils.variantvalidator.get_db')
    @patch('requests.get')
    def test_parse_to_bed_success(self, mock_get, mock_get_db, mock_query_cls, mock_file):
        """
        Test parse_to_bed outputs valid BED content from the API data.
        """
        # Mock DB/Query for get_hgnc_ids_with_replacements
        mock_db_instance = MagicMock()
        mock_db_instance.conn = "fake_connection"
        mock_get_db.return_value = mock_db_instance

        mock_query_instance = MagicMock()
        mock_query_instance.get_gene_symbol.return_value = []
        mock_query_cls.return_value = mock_query_instance

        # (2) Mock VariantValidator JSON with two transcripts, each having two exons
        mock_json = [
            {
                "current_symbol": "BRCA1",
                "transcripts": [
                    {
                        # Orientation -1 => strand will be '-'
                        # Reference => "NM_007294.4"
                        "reference": "NM_007294.4",
                        "annotations": {
                            "chromosome": "17",
                        },
                        "genomic_spans": {
                            "NC_000017.11": {
                                "orientation": -1,
                                "exon_structure": [
                                    {
                                        "exon_number": 1,
                                        "genomic_start": 43125271,
                                        "genomic_end": 43125364
                                    },
                                    {
                                        "exon_number": 2,
                                        "genomic_start": 43124017,
                                        "genomic_end": 43124115
                                    }
                                ]
                            }
                        }
                    },
                    {
                        # Orientation -1 => strand will be '-'
                        # Reference => "ENST00000357654.9"
                        "reference": "ENST00000357654.9",
                        "annotations": {
                            "chromosome": "17",
                        },
                        "genomic_spans": {
                            "NC_000017.11": {
                                "orientation": -1,
                                "exon_structure": [
                                    {
                                        "exon_number": 1,
                                        "genomic_start": 43125271,
                                        "genomic_end": 43125364
                                    },
                                    {
                                        "exon_number": 2,
                                        "genomic_start": 43124017,
                                        "genomic_end": 43124115
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        ]

        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_json

        # (3) Call parse_to_bed
        bed_io = self.client.parse_to_bed(
            gene_query=["HGNC:1100"],  # or "BRCA1"
            genome_build="GRCh38",
            transcript_set="all",
            limit_transcripts="mane_select"  # or "mane_select", etc.
        )
        self.assertIsInstance(bed_io, BytesIO)

        # (4) Read and split the resulting BED lines
        bed_data = bed_io.read().decode('utf-8').strip().split('\n')
        self.assertEqual(len(bed_data), 4, "Should produce 4 lines (2 exons × 2 transcripts).")

        # (5) Because code sorts by chrom/start/end, we expect the lines in ascending order.
        # In ascending numerical order, exon2 (start=43124017) < exon1 (start=43125271).
        # So each transcript’s exon2 line appears before its exon1 line.
        # Also, the two transcripts have the same coordinates, since we are using a mocked dict to compare order is maintained.
        # A likely final order is:
        #   - Transcript1 Exon2
        #   - Transcript2 Exon2
        #   - Transcript1 Exon1
        #   - Transcript2 Exon1

        # Construct the *expected* lines. Since orientation=-1 => strand='-'
        # reference is appended in the 4th column after exon number (ex: _NM_007294.4)
        expected_bed_lines = [
            "chr17\t43124017\t43124115\tBRCA1_exon2_NM_007294.4\t-",
            "chr17\t43124017\t43124115\tBRCA1_exon2_ENST00000357654.9\t-",
            "chr17\t43125271\t43125364\tBRCA1_exon1_NM_007294.4\t-",
            "chr17\t43125271\t43125364\tBRCA1_exon1_ENST00000357654.9\t-"
        ]

        # (6) Check that your actual lines match exactly.
        self.assertListEqual(bed_data, expected_bed_lines)



    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('vimmo.utils.variantvalidator.Query')
    @patch('vimmo.utils.variantvalidator.get_db')
    @patch('requests.get')
    def test_parse_to_bed_missing_transcripts(self, mock_get, mock_get_db, mock_query_cls, mock_file):
        """
        Tests handling of API responses where the transcripts array is empty or missing.
        
        This test verifies that the client correctly handles cases where gene data is
        returned but no transcript information is available. Such cases might occur for:
        - Pseudogenes
        - Recently discovered genes
        - Genes not yet annotated in the selected genome build
        
        The expected behavior is to generate a "NoRecord" entry in the BED file with
        appropriate placeholder values.
        
        Test Steps:
        1. Mock database and query setup
        2. Simulate API response with empty transcripts
        3. Call parse_to_bed
        4. Verify correct formatting of "NoRecord" entry
        
        Args:
            mock_get: Mocked requests.get function
            mock_get_db: Mocked database connection
            mock_query_cls: Mocked Query class
            mock_file: Mocked file operations
        """
        mock_db_instance = MagicMock()
        mock_db_instance.conn = "fake_connection"
        mock_get_db.return_value = mock_db_instance

        mock_query_instance = MagicMock()
        mock_query_instance.get_gene_symbol.return_value = []
        mock_query_cls.return_value = mock_query_instance

        # Mock API response with missing transcripts
        mock_json = [{
            "current_symbol": "BRCA1",
            "requested_symbol": "BRCA1",
            "transcripts": []  # Empty transcripts array
        }]

        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_json

        bed_io = self.client.parse_to_bed(
            gene_query=["BRCA1"],
            genome_build="GRCh38"
        )

        bed_data = bed_io.read().decode('utf-8').strip().split('\n')
        expected_line = "NoRecord\tNoRecord\tNoRecord\tBRCA1_NoRecord\tNoRecord"
        self.assertEqual(bed_data[0], expected_line)



    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('vimmo.utils.variantvalidator.Query')
    @patch('vimmo.utils.variantvalidator.get_db')
    @patch('requests.get')
    def test_parse_to_bed_api_error_response(self, mock_get, mock_get_db, mock_query_cls, mock_file):
        """
        Tests handling of API error responses where the server returns an error message
        instead of gene data.
        
        This test verifies the client's behavior when receiving an error response like:
        [
            {
                "error": "Unable to retrieve data from the VVTA, please contact admin",
                "requested_symbol": "TRAC"
            }
        ]
        
        The client should:
        1. Recognize the error response structure
        2. Handle it gracefully without crashing
        3. Generate appropriate "Error" entries in the BED file
        4. Preserve the gene symbol information for debugging
        
        Test Steps:
        1. Set up mock infrastructure
        2. Simulate API error response
        3. Process through parse_to_bed
        4. Verify error handling in output
        
        Args:
            mock_get: Mocked requests.get function
            mock_get_db: Mocked database connection
            mock_query_cls: Mocked Query class
            mock_file: Mocked file operations
        """
        # Set up database and query mocks
        mock_db_instance = MagicMock()
        mock_get_db.return_value = mock_db_instance

        mock_query_instance = MagicMock()
        mock_query_instance.get_gene_symbol.return_value = []
        mock_query_cls.return_value = mock_query_instance

        # Mock API error response
        mock_json = [{
            "error": "Unable to retrieve data from the VVTA, please contact admin",
            "requested_symbol": "TRAC"
        }]

        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_json

        # Process the error response
        bed_io = self.client.parse_to_bed(
            gene_query=["TRAC"],
            genome_build="GRCh38"
        )

        # Read and verify the output
        bed_data = bed_io.read().decode('utf-8').strip().split('\n')
        
        # The BED file should contain one line with Error markers
        self.assertEqual(len(bed_data), 1)
        
        # Split the BED line into its components
        bed_fields = bed_data[0].split('\t')
        
        # Verify the format of the error entry
        self.assertEqual(bed_fields[0], "NoRecord")  # chromosome
        self.assertEqual(bed_fields[1], "NoRecord")  # start
        self.assertEqual(bed_fields[2], "NoRecord")  # end
        self.assertEqual(bed_fields[3], "TRAC_NoRecord")  # name includes original symbol
        self.assertEqual(bed_fields[4], "NoRecord")  # strand



    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('vimmo.utils.variantvalidator.Query')
    @patch('vimmo.utils.variantvalidator.get_db')
    @patch('requests.get')
    def test_parse_to_bed_missing_genomic_spans(self, mock_get, mock_get_db, mock_query_cls, mock_file):
        """
        Tests behavior when API response contains transcripts without genomic span information.
        
        This test verifies proper handling of cases where transcript data exists but
        genomic coordinates are missing. This scenario might occur due to:
        - Incomplete genome annotations
        - Data synchronization issues
        - API response truncation
        
        Expected behavior is to generate an error entry in the BED file while
        maintaining the ability to process other valid entries.
        
        Test Steps:
        1. Configure mock objects for database and API
        2. Create test response with missing genomic spans
        3. Process through parse_to_bed
        4. Verify error handling and output format
        
        Args:
            mock_get: Mocked requests.get function
            mock_get_db: Mocked database connection
            mock_query_cls: Mocked Query class
            mock_file: Mocked file operations
        """
        mock_db_instance = MagicMock()
        mock_get_db.return_value = mock_db_instance

        mock_query_instance = MagicMock()
        mock_query_cls.return_value = mock_query_instance

        # Mock API response with missing genomic spans
        mock_json = [{
            "current_symbol": "TEST",
            "transcripts": [{
                "annotations": {
                    "chromosome": "1"
                },
                "reference": "NM_TEST",
                "genomic_spans": {}  # Empty genomic spans
            }]
        }]

        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_json

        bed_io = self.client.parse_to_bed(
            gene_query=["TEST"],
            genome_build="GRCh38"
        )

        bed_data = bed_io.read().decode('utf-8').strip().split('\n')
        self.assertTrue("Error" in bed_data[0])



if __name__ == '__main__':
    unittest.main()