import unittest
from vimmo.utils.arg_validator import (
    panel_space_validator,
    bed_space_validator,
    validate_panel_id_or_Rcode_or_hgnc,
    validate_hgnc_ids
)

class TestValidationFunctions(unittest.TestCase):

    #Panel Space Validator Tests
    def test_panel_space_validator_valid_lowercase_r(self):
        panel_space_validator("123", "r123", ["HGNC:45678"])  # Should not raise exceptions

    def test_panel_space_validator_valid_uppercase_R(self):
        panel_space_validator("123", "R123", ["HGNC:45678"])  # Should not raise exceptions

    def test_panel_space_validator_invalid_panel_id(self):
        with self.assertRaises(ValueError) as err:
            panel_space_validator("abc", "r123", ["HGNC:45678"])
        self.assertIn("'Panel_ID' must be digits only", str(err.exception))

    def test_panel_space_validator_invalid_rcode(self):
        with self.assertRaises(ValueError) as err:
            panel_space_validator("123", "invalidRcode", ["HGNC:45678"])
        self.assertIn("Invalid format for 'Rcode'", str(err.exception))

    def test_panel_space_validator_invalid_hgnc(self):
        with self.assertRaises(ValueError) as err:
            panel_space_validator("123", "r123", ["45678"])
        self.assertIn("Invalid format for 'HGNC_ID'", str(err.exception))

    def test_panel_space_validator_multiple_hgnc_valid(self):
        panel_space_validator("123", "R123", ["HGNC:12345","HGNC:67890"])  # Should not raise exceptions

    def test_panel_space_validator_multiple_hgnc_invalid(self):
        with self.assertRaises(ValueError) as err:
            panel_space_validator("123", "R123", ["HGNC:12345","Invalid"])
        self.assertIn("Invalid format for 'HGNC_ID'", str(err.exception))

    # Bed Space Validator Tests
    def test_bed_space_validator_valid(self):
        bed_space_validator("123", "R123", ["HGNC:45678"])  # Should not raise exceptions

    def test_bed_space_validator_invalid_panel_id(self):
        with self.assertRaises(ValueError) as err:
            bed_space_validator("abc", "R123", ["HGNC:45678"])
        self.assertIn("Invalid format for 'Panel_ID'", str(err.exception))

    def test_bed_space_validator_invalid_rcode_lowercase_r(self):
        with self.assertRaises(ValueError) as err:
            bed_space_validator("123", "r123", ["HGNC:45678"])
        self.assertIn("Invalid format for 'Rcode'", str(err.exception))

    def test_bed_space_validator_invalid_rcode_format(self):
        with self.assertRaises(ValueError) as err:
            bed_space_validator("123", "invalidRcode", ["HGNC:45678"])
        self.assertIn("Invalid format for 'Rcode'", str(err.exception))

    def test_bed_space_validator_invalid_hgnc(self):
        with self.assertRaises(ValueError) as err:
            bed_space_validator("123", "R123", ["45678"])
        self.assertIn("Invalid format for 'HGNC_ID'", str(err.exception))

    def test_bed_space_validator_multiple_hgnc_valid(self):
        bed_space_validator("123", "R123", ["HGNC:12345"])

    def test_bed_space_validator_multiple_hgnc_invalid(self):
        with self.assertRaises(ValueError) as err:
            bed_space_validator("123", "R123", ["HGNC:12345,Invalid"])
        self.assertIn("Invalid format for 'HGNC_ID'", str(err.exception))

    # HGNC ID Validation Tests
    def test_validate_hgnc_ids_single_valid(self):
        validate_hgnc_ids(["HGNC:12345"])  # Should not raise exceptions

    def test_validate_hgnc_ids_multiple_valid(self):
        validate_hgnc_ids(["HGNC:12345", "HGNC:67890"])  # Should not raise exceptions

    def test_validate_hgnc_ids_invalid(self):
        with self.assertRaises(ValueError) as err:
            validate_hgnc_ids(["HGNC:12345", "Invalid"])
        self.assertIn("Invalid format for 'HGNC_ID'", str(err.exception))

    # Generic Argument Validation Tests
    def test_validate_single_argument(self):
        args = {'Panel_ID': '123'}
        validate_panel_id_or_Rcode_or_hgnc(args, panel_space=True)  # Should not raise exceptions

    def test_validate_no_arguments(self):
        args = {}
        with self.assertRaises(ValueError) as err:
            validate_panel_id_or_Rcode_or_hgnc(args, panel_space=True)
        self.assertIn("At least one of 'Panel_ID', 'Rcode', or 'HGNC_ID' must be provided", str(err.exception))

    def test_validate_multiple_arguments(self):
        args = {'Panel_ID': '123', 'Rcode': 'R123'}
        with self.assertRaises(ValueError) as err:
            validate_panel_id_or_Rcode_or_hgnc(args, bed_space=True)
        self.assertIn("Provide only one of 'Panel_ID', 'Rcode', or 'HGNC_ID'", str(err.exception))

    def test_validate_invalid_panel_space(self):
        args = {'Panel_ID': 'abc'}
        with self.assertRaises(ValueError) as err:
            validate_panel_id_or_Rcode_or_hgnc(args, panel_space=True)
        self.assertIn("'Panel_ID' must be digits only", str(err.exception))

    def test_validate_invalid_bed_space(self):
        args = {'Rcode': 'r123'}
        with self.assertRaises(ValueError) as err:
            validate_panel_id_or_Rcode_or_hgnc(args, bed_space=True)
        self.assertIn("Invalid format for 'Rcode'", str(err.exception))

if __name__ == "__main__":
    unittest.main()
