import unittest
from vimmo.utils.arg_validator import (
    panel_space_validator,
    bed_space_validator,
    validate_panel_id_or_Rcode_or_hgnc,
)


class TestValidationFunctions(unittest.TestCase):

    # Testing panel_space_validator
    def test_panel_space_validator_valid_lowercase_r(self):
        # Test valid Rcode with lowercase 'r'
        panel_space_validator("123", "r123", "HGNC:45678")  # Should not raise any exceptions

    def test_panel_space_validator_valid_uppercase_R(self):
        # Test valid Rcode with uppercase 'R'
        panel_space_validator("123", "R123", "HGNC:45678")  # Should not raise any exceptions

    def test_panel_space_validator_invalid_panel_id(self):
        # Test invalid Panel_ID (non-numeric)
        with self.assertRaises(ValueError):
            panel_space_validator("abc", "r123", "HGNC:45678")

    def test_panel_space_validator_invalid_rcode(self):
        # Test invalid Rcode (not matching pattern)
        with self.assertRaises(ValueError):
            panel_space_validator("123", "invalidRcode", "HGNC:45678")

    def test_panel_space_validator_invalid_hgnc(self):
        # Test invalid HGNC_ID (missing HGNC:)
        with self.assertRaises(ValueError):
            panel_space_validator("123", "r123", "45678")

    # Testing bed_space_validator
    def test_bed_space_validator_valid(self):
        # Test valid inputs
        bed_space_validator("123", "R123", "HGNC:45678")  # Should not raise any exceptions

    def test_bed_space_validator_invalid_panel_id(self):
        # Test invalid Panel_ID (non-numeric)
        with self.assertRaises(ValueError):
            bed_space_validator("abc", "R123", "HGNC:45678")

    def test_bed_space_validator_invalid_rcode_lowercase_r(self):
        # Test invalid Rcode (lowercase 'r' is not allowed in bed space)
        with self.assertRaises(ValueError):
            bed_space_validator("123", "r123", "HGNC:45678")

    def test_bed_space_validator_invalid_rcode_format(self):
        # Test invalid Rcode (not matching pattern)
        with self.assertRaises(ValueError):
            bed_space_validator("123", "invalidRcode", "HGNC:45678")

    def test_bed_space_validator_invalid_hgnc(self):
        # Test invalid HGNC_ID (missing HGNC:)
        with self.assertRaises(ValueError):
            bed_space_validator("123", "R123", "45678")

    # Testing validate_panel_id_or_Rcode_or_hgnc
    def test_validate_single_argument(self):
        # Test valid single argument for panel space
        args = {'Panel_ID': '123'}
        validate_panel_id_or_Rcode_or_hgnc(args, panel_space=True)

    def test_validate_no_arguments(self):
        # Test with no arguments provided
        args = {}
        with self.assertRaises(ValueError):
            validate_panel_id_or_Rcode_or_hgnc(args, panel_space=True)

    def test_validate_multiple_arguments(self):
        # Test with multiple arguments provided
        args = {'Panel_ID': '123', 'Rcode': 'R123'}
        with self.assertRaises(ValueError):
            validate_panel_id_or_Rcode_or_hgnc(args, bed_space=True)

    def test_validate_invalid_panel_space(self):
        # Test invalid input for panel space
        args = {'Panel_ID': 'abc'}
        with self.assertRaises(ValueError):
            validate_panel_id_or_Rcode_or_hgnc(args, panel_space=True)

    def test_validate_invalid_bed_space(self):
        # Test invalid input for bed space
        args = {'Rcode': 'r123'}
        with self.assertRaises(ValueError):
            validate_panel_id_or_Rcode_or_hgnc(args, bed_space=True)


# Run the test suite
if __name__ == "__main__":
    unittest.main()
