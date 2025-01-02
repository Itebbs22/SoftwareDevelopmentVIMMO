import unittest
from unittest.mock import patch
from io import BytesIO
import pandas as pd
from vimmo.utils.localbed import local_bed_formatter

class TestLocalBed(unittest.TestCase):
    """
    A test suite for the local_bed_formatter function.
    
    This class contains test cases that verify the behavior of the local_bed_formatter
    function under various scenarios, including:
    
    1. Processing a list of valid records and returning the expected BED content.
    2. Handling an empty list of records gracefully.
    3. Handling None input gracefully.
    4. Verifying that pd.DataFrame is called with the expected data.
    
    By thoroughly testing the function's behavior, we can ensure it works as intended
    and catch potential bugs early in the development process.
    """
    
    def test_local_bed_formatter_with_records(self):
        """
        Test that local_bed_formatter correctly processes a list of records 
        and returns a BytesIO object with the expected BED content.
        
        This test sets up a list of sample records, calls the local_bed_formatter
        function with those records, and verifies that:
        
        1. The function returns a BytesIO object.
        2. The content of the BytesIO object matches the expected BED format.
        
        By checking both the type and content of the returned object, we can be
        confident that the function is processing the input records correctly.
        """
        # Set up test data
        test_records = [
            {
                'Chromosome': 'chr1', 
                'Start': 100, 
                'End': 200, 
                'Name': 'Test1',
                'Strand': '+',
                'Transcript': 'NM_001',
                'Type': 'ms',
                'HGNC_ID': 'HGNC:1'
            },
            {
                'Chromosome': 'chr2',
                'Start': 300,
                'End': 400,
                'Name': 'Test2',
                'Strand': '-',
                'Transcript': 'NM_002',
                'Type': 'mpc', 
                'HGNC_ID': 'HGNC:2'
            }
        ]
        
        # Call the function with the test records
        result = local_bed_formatter(test_records)
        
        # Check that the function returned a BytesIO object
        self.assertIsInstance(result, BytesIO)
        
        # Read the BED content from the BytesIO object
        bed_content = result.getvalue().decode('utf-8')
        
        # Check that the BED content matches the expected format
        expected_bed = (
            "chr1\t100\t200\tTest1\t+\tNM_001\tms\tHGNC:1\n"
            "chr2\t300\t400\tTest2\t-\tNM_002\tmpc\tHGNC:2\n"
        )
        self.assertEqual(bed_content, expected_bed)
    
    def test_local_bed_formatter_empty_records(self):
        """
        Test that local_bed_formatter returns None when given an empty list.
        
        This test verifies that the function handles the edge case of an empty
        input list gracefully by returning None. This is important for ensuring
        the function doesn't raise exceptions or return invalid data when given
        an empty dataset.
        """
        # Call the function with an empty list
        result = local_bed_formatter([])
        
        # Check that the function returned None
        self.assertIsNone(result)
    
    def test_local_bed_formatter_none_records(self):
        """
        Test that local_bed_formatter returns None when given None.
        
        Similar to the empty list test, this test case verifies that the function
        handles the edge case of being given None as input. By returning None in
        this case, the function indicates that there are no valid records to process.
        """
        # Call the function with None
        result = local_bed_formatter(None)
        
        # Check that the function returned None
        self.assertIsNone(result)
        
    @patch('vimmo.utils.localbed.pd.DataFrame')
    def test_local_bed_formatter_dataframe_called(self, mock_dataframe):
        """
        Test that pd.DataFrame is called with the correct bed_rows data.
        
        This test verifies that the local_bed_formatter function correctly converts
        the input records into the expected format before passing them to pd.DataFrame.
        
        By using a mock object in place of pd.DataFrame, we can inspect the arguments
        it was called with and ensure they match our expectations. This helps pinpoint
        any discrepancies between the input records and the data used to create the
        DataFrame.
        """
        # Set up a test record
        test_records = [
            {
                'Chromosome': 'chr1', 
                'Start': 100, 
                'End': 200, 
                'Name': 'Test1',
                'Strand': '+',
                'Transcript': 'NM_001',
                'Type': 'ms',
                'HGNC_ID': 'HGNC:1'
            }
        ]
        # Set up the mocked DataFrame to return a string when to_csv is called otherwise df.to_csv throws an error
        # as it expects a pandas dataframe not a mock datafram object
        mock_dataframe.return_value.to_csv.return_value = "chr1\t100\t200\tTest1\t+\tNM_001\tms\tHGNC:1\n"
        # Call the function with the test record
        local_bed_formatter(test_records)
        
        # Define the expected bed_rows data
        expected_rows = [{
            'chrom': 'chr1',
            'chromStart': 100,
            'chromEnd': 200,
            'name': 'Test1', 
            'strand': '+',
            'transcript': 'NM_001',
            'type': 'ms',
            'hgnc_id': 'HGNC:1'
        }]
        
        # Check that pd.DataFrame was called once with the expected data
        mock_dataframe.assert_called_once_with(expected_rows)

if __name__ == '__main__':
    unittest.main()