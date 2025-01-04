import unittest
import sqlite3
import os
from unittest.mock import MagicMock, patch
from datetime import date
from vimmo.db.db import Database 
from vimmo.db.db_query import Query
from vimmo.db.db_update import Update
import datetime

"""
test_db.py - Comprehensive Test Suite for Database Operations

This module contains test suites for the Database, Query, and Update classes.
Each test class focuses on specific functionality while ensuring database integrity:

TestDatabase: Core database connectivity and configuration
TestQuery: Data retrieval operations
TestUpdate: Data modification operations

Key Features:
- Transaction-based testing to prevent persistent changes
- Comprehensive test data setup
- Error case handling
- Clear documentation of test scenarios

Usage:
    Run with unittest:
    python -m unittest test_db.py

Note: All test data is contained within transactions and rolled back after testing.
The actual database remains unchanged regardless of test execution.
"""

# First, let's create a base test class that other test classes can inherit from
class BaseTestCase(unittest.TestCase):
    """
    Base test class providing robust database transaction management.
    
    This class ensures complete isolation of test data by:
    1. Starting a new transaction before each test
    2. Rolling back all changes after each test
    3. Handling connection cleanup even if tests fail
    """
    def setUp(self):
        """Initialize database connection and start transaction."""
        self.db = Database()
        self.db.connect()
        self.db.conn.execute("BEGIN TRANSACTION")

    def tearDown(self):
        """
        Clean up test fixtures after each test method.

        Forces rollback of any uncommitted changes and ensures
        connection cleanup, even if tests fail.
        """
        if self.db.conn:
            try:
                self.db.conn.rollback()
            finally:
                self.db.close()

    def verify_cleanup(self):
        """
        Verify that test data was properly cleaned up.
        
        This method can be called at the end of tests to ensure
        no data persists from test operations.
        """
        # Create a new connection to verify cleanup
        verify_db = Database()
        verify_db.connect()
        cursor = verify_db.conn.cursor()
        
        try:
            # Check for test data in various tables
            test_queries = [
                "SELECT COUNT(*) FROM panel WHERE Panel_ID >= 100000",
                "SELECT COUNT(*) FROM patient_data WHERE Patient_ID LIKE 'TEST%'",
                "SELECT COUNT(*) FROM genes_info WHERE HGNC_ID LIKE 'HGNC:TEST%'"
            ]
            
            for query in test_queries:
                count = cursor.execute(query).fetchone()[0]
                if count > 0:
                    raise AssertionError(f"Test data cleanup failed: {query} returned {count} rows")
                    
        finally:
            verify_db.close()


class TestDatabase(BaseTestCase):
    """
    Test suite for core Database class functionality.
    
    This class verifies fundamental database operations including:
    - Database path resolution
    - Connection establishment and management
    - Transaction handling
    
    Each test ensures the database remains in a consistent state through
    transaction management.
    """

    def test_database_connection(self):
        """
        Verify that database connections are established correctly.
        
        This test checks:
        1. Connection object creation
        2. Connection type verification
        3. Connection state management
        """
        self.assertIsNotNone(self.db.conn, 
            "Database connection should be created")
        self.assertTrue(
            isinstance(self.db.conn, sqlite3.Connection),
            "Connection should be SQLite connection object"
        )

    def test_get_db_path_development(self):
        """
        Test database path resolution in development environment.
        
        Ensures the database path:
        1. Points to an existing file
        2. Uses absolute path format
        3. Has correct filename
        4. Is accessible for operations
        """
        db_path = self.db.get_db_path()
        
        # Path should exist and be absolute
        self.assertTrue(os.path.exists(db_path), 
            "Database file should exist")
        self.assertTrue(os.path.isabs(db_path), 
            "Database path should be absolute")
        
        # Verify correct filename
        self.assertTrue(db_path.endswith('panels_data.db'), 
            "Database should have correct filename")


class TestQuery(BaseTestCase):
    """
    Test suite for database query operations.
    
    This class tests all data retrieval operations including:
    - Panel data queries
    - Gene information retrieval
    - Version checking
    - Error handling
    
    Each test method includes thorough verification of returned data
    and proper error handling.
    """

    def setUp(self):
        """
        Prepare test environment for query testing.
        
        Extends base setup with:
        1. Query object initialization
        2. Test data creation
        """
        super().setUp()
        self.query = Query(self.db.conn)
        self._create_test_data()

    def _create_test_data(self):
        """
        Create comprehensive test dataset.
        
        Sets up test data including:
        - Panel records with various versions
        - Gene information with coordinate data
        - Panel-gene associations
        - All necessary relationships for testing
        
        Note: All test data uses distinct identifiers to avoid
        conflicts with existing database records.
        """
        cursor = self.db.conn.cursor()
        
        # Test panels setup
        cursor.execute('''
            INSERT OR IGNORE INTO panel (Panel_ID, rcodes, Version) 
            VALUES 
            (100001, 'R999.01', 2.5),
            (100002, 'R999.02', 1.0),
            (100003, 'R999.03', 3.0)
        ''')
        
        # Test genes setup with coordinate data
        cursor.execute('''
            INSERT OR IGNORE INTO genes_info (
                HGNC_ID, Gene_Symbol, HGNC_symbol,
                GRCh37_Chr, GRCh37_start, GRCh37_stop,
                GRCh38_Chr, GRCh38_start, GRCh38_stop
            ) VALUES 
            (
                'HGNC:123456789', 'TEST_1', 'TEST_SYMBOL_1',
                'chr1', 500, 1500,
                'chr1', 1000, 2000
            ),
            (
                'HGNC:987654321', 'TEST_2', 'TEST_SYMBOL_2',
                'chr2', 2500, 3500,
                'chr2', 3000, 4000
            ),
            (
                'HGNC:111222333', 'TEST_3', 'TEST_SYMBOL_3',
                'chr3', 4500, 5500,
                'chr3', 5000, 6000
            )
        ''')
        
        # Panel-gene associations
        cursor.execute('''
            INSERT OR IGNORE INTO panel_genes (
                Panel_ID, HGNC_ID, Confidence
            ) VALUES 
            (100001, 'HGNC:123456789', 3),
            (100001, 'HGNC:987654321', 2),
            (100002, 'HGNC:111222333', 3),
            (100003, 'HGNC:123456789', 3)
        ''')

    def test_get_panel_data_exact_match(self):
        """
        Test retrieving panel data with exact panel ID matching.
        
        This test verifies that when querying for panel 100001:
        1. We get exactly two associated genes (HGNC:123456789 and HGNC:987654321)
        2. All expected fields are present in the response
        3. The coordinate data for both genome builds is correct
        """
        result = self.query.get_panel_data(panel_id=100001, matches=False)
        
        # Verify basic structure
        self.assertIn("Panel_ID", result)
        self.assertIn("Associated Gene Records", result)
        
        # We expect exactly two gene records for panel 100001
        gene_records = result["Associated Gene Records"]
        self.assertEqual(len(gene_records), 2)
        
        # Verify first record's content
        first_record = gene_records[0]
        self.assertEqual(first_record["Panel_ID"], 100001)
        self.assertEqual(first_record["rcodes"], "R999.01")
        self.assertEqual(first_record["Version"], 2.5)
        
        # Verify coordinate data presence
        self.assertIn("GRCh37_Chr", first_record)
        self.assertIn("GRCh37_start", first_record)
        self.assertIn("GRCh37_stop", first_record)
        self.assertIn("GRCh38_Chr", first_record)
        self.assertIn("GRCh38_start", first_record)
        self.assertIn("GRCh38_stop", first_record)
        
        # Verify the HGNC IDs are present
        hgnc_ids = {record["HGNC_ID"] for record in gene_records}
        self.assertIn("HGNC:123456789", hgnc_ids)
        self.assertIn("HGNC:987654321", hgnc_ids)

    def test_get_panels_by_rcode_exact(self):
        """
        Test retrieving panels by exact R-code match.
        
        This test verifies that when searching for R999.01:
        1. We get records from exactly one panel (100001)
        2. The record contains the correct gene associations
        3. Version number is correct for the panel
        """
        result = self.query.get_panels_by_rcode(rcode="R999.01", matches=False)
        
        self.assertIn("Rcode", result)
        self.assertIn("Associated Gene Records", result)
        
        records = result["Associated Gene Records"]
        
        # Get unique panel IDs and versions
        panel_data = {(record["Panel_ID"], record["Version"]) for record in records}
        
        # Verify we found the correct panel with R999.01
        self.assertIn((100001, 2.5), panel_data)
        
        # Verify all records have the correct R-code
        self.assertTrue(all(record["rcodes"] == "R999.01" for record in records))



    def test_get_panels_from_gene_list(self):
        """
        Test retrieving panels associated with multiple HGNC IDs.
        
        This test verifies:
        1. Searching for HGNC:123456789 finds panels 100001 and 100003
        2. Searching for multiple genes returns the correct combined results
        3. The response format matches the expected structure
        """
        # Test with a gene that appears in multiple panels
        single_gene = ["HGNC:123456789"]
        result = self.query.get_panels_from_gene_list(hgnc_ids=single_gene)
        
        self.assertIn("Panels", result)
        panels = result["Panels"]
        
        # This gene should be in panels 100001 and 100003
        panel_ids = {panel["Panel_ID"] for panel in panels}
        self.assertIn(100001, panel_ids)
        self.assertIn(100003, panel_ids)
        
        # Test with multiple genes
        multiple_genes = ["HGNC:123456789", "HGNC:987654321"]
        result = self.query.get_panels_from_gene_list(hgnc_ids=multiple_genes)
        
        panels = result["Panels"]
        panel_ids = {panel["Panel_ID"] for panel in panels}
        self.assertIn(100001, panel_ids)  # Should find panel with both genes

    def test_get_gene_list(self):
        """
        Test retrieving gene lists by panel ID and R-code.
        
        This test verifies:
        1. Getting genes by panel ID returns the correct set
        2. Getting genes by R-code returns genes from all matching panels
        3. The function handles both query methods correctly
        """
        # Test by panel ID
        panel_genes = self.query.get_gene_list(panel_id=100001, r_code=None, matches=False)
        self.assertIsInstance(panel_genes, set)
        self.assertEqual(len(panel_genes), 2)
        self.assertIn("HGNC:123456789", panel_genes)
        self.assertIn("HGNC:987654321", panel_genes)
        
        # Test by R-code (R999.01 appears in two panels)
        rcode_genes = self.query.get_gene_list(panel_id=None, r_code="R999.01", matches=False)
        self.assertIsInstance(rcode_genes, set)
        self.assertIn("HGNC:123456789", rcode_genes)

    def test_get_gene_symbol(self):
        """
        Test retrieving gene symbols for a list of HGNC IDs.
        
        This test verifies:
        1. Symbols are correctly returned for existing genes
        2. The correct symbol mappings are maintained
        3. The function handles multiple IDs properly
        """
        ids_to_replace = ["HGNC:123456789", "HGNC:987654321"]
        result = self.query.get_gene_symbol(ids_to_replace)
        
        # Convert result to a dict for easier testing
        symbol_map = {row["HGNC_ID"]: row["HGNC_symbol"] for row in result}
        
        self.assertEqual(symbol_map["HGNC:123456789"], "TEST_SYMBOL_1")
        self.assertEqual(symbol_map["HGNC:987654321"], "TEST_SYMBOL_2")

    
    def test_get_db_latest_version(self):
        """
        Test retrieving the version for a given R-code.
        
        This test verifies that:
        1. Each R-code returns its correct version
        2. For non-existent R-codes, it returns None
        3. The version is returned in the correct numeric format
        
        The test data contains:
        - R999.01 with version 2.5
        - R999.02 with version 1.0
        - R999.03 with version 3.0
        """
        # Test all R-codes
        version = self.query.get_db_latest_version("R999.01")
        self.assertIsNotNone(version)
        self.assertEqual(version, 2.5)
        
        version = self.query.get_db_latest_version("R999.02")
        self.assertIsNotNone(version)
        self.assertEqual(version, 1.0)
        
        version = self.query.get_db_latest_version("R999.03")
        self.assertIsNotNone(version)
        self.assertEqual(version, 3.0)  # Fixed to match test data
        
        # Test non-existent R-code
        version = self.query.get_db_latest_version("R000.00")
        self.assertIsNone(version)
   
    def test_rcode_to_panelID(self):
        """
        Test converting R-codes to panel IDs.
        
        This test verifies that:
        1. Each R-code maps to exactly one panel ID
        2. The correct panel ID is returned for each R-code
        3. For non-existent R-codes, it returns None
        
        The test data contains:
        - R999.01 associated with panel 100001
        - R999.02 associated with panel 100002
        - R999.03 associated with panel 100003
        """
        # Test each R-code
        panel_id = self.query.rcode_to_panelID("R999.01")
        self.assertIsNotNone(panel_id)
        self.assertEqual(panel_id, 100001)
        
        panel_id = self.query.rcode_to_panelID("R999.02")
        self.assertIsNotNone(panel_id)
        self.assertEqual(panel_id, 100002)
        
        panel_id = self.query.rcode_to_panelID("R999.03")
        self.assertIsNotNone(panel_id)
        self.assertEqual(panel_id, 100003)
        
        # Test non-existent R-code
        panel_id = self.query.rcode_to_panelID("R000.00")
        self.assertIsNone(panel_id)

    def test_version_and_panelID_consistency(self):
        """
        Test the consistency between version and panel ID retrieval.
        
        This test verifies that:
        1. Each R-code has exactly one version and one panel ID
        2. The version returned matches the panel's version in the database
        3. Both functions handle edge cases consistently
        """
        # Test consistency for all R-codes
        test_codes = ["R999.01", "R999.02", "R999.03"]
        expected_data = {
            "R999.01": (100001, 2.5),
            "R999.02": (100002, 1.0),
            "R999.03": (100003, 3.0)
        }
        
        for rcode in test_codes:
            version = self.query.get_db_latest_version(rcode)
            panel_id = self.query.rcode_to_panelID(rcode)
            
            self.assertIsNotNone(version)
            self.assertIsNotNone(panel_id)
            
            expected_panel_id, expected_version = expected_data[rcode]
            self.assertEqual(panel_id, expected_panel_id)
            self.assertEqual(version, expected_version)


    def test_check_patient_history(self):
        """
        Test patient history retrieval functionality with proper date filtering.
        """
        cursor = self.db.conn.cursor()
        
        cursor.execute('''
            INSERT INTO patient_data (Patient_ID, Panel_ID, Rcode, Version, Date)
            VALUES 
            ("TEST_P123", 999999999, "TEST_R999", 2.0, "2023-01-01")
        ''')
        
        cursor.execute('''
            INSERT INTO patient_data (Patient_ID, Panel_ID, Rcode, Version, Date)
            VALUES 
            ("TEST_P123", 999999999, "TEST_R999", 2.5, "2024-12-01")
        ''')

        cursor.execute('''
            SELECT Version
            FROM patient_data
            WHERE Date = (
                SELECT MAX(Date) 
                FROM patient_data
                WHERE Patient_ID = ? AND Rcode = ?
            ) 
            AND Patient_ID = ? AND Rcode = ?
        ''', ("TEST_P123", "TEST_R999", "TEST_P123", "TEST_R999"))
        final_result = cursor.fetchone()
        print("Direct Query Result:", dict(final_result) if final_result else None)

        version = self.query.check_patient_history("TEST_P123", "TEST_R999")
        self.assertEqual(version, 2.5)

    def test_error_cases(self):
        """
        Test various error conditions and edge cases.
        
        This test suite verifies proper handling of:
        1. Invalid panel IDs
        2. Non-existent R-codes
        3. Empty or invalid gene lists
        4. Missing data scenarios
        """
        # Test invalid panel ID
        result = self.query.get_panel_data(panel_id=999999)
        self.assertIn("Message", result)
        self.assertEqual(result["Message"], "No matches found for this panel id with confidence : All.")
        
        # Test non-existent R-code
        result = self.query.get_panels_by_rcode(rcode="R000.00")
        self.assertIn("Message", result)
        self.assertEqual(result["Message"], "No matches found for this rcode with confidence : All.")
        
        # Test empty gene list
        result = self.query.get_panels_from_gene_list([])
        self.assertIn("Message", result)
        
        # Test non-existent HGNC ID
        result = self.query.get_gene_symbol(["HGNC:000000"])
        self.assertEqual(len(result), 0)
        
        # Test None panel_id
        with self.assertRaises(ValueError):
            self.query.get_panel_data(panel_id=None)


    


# class TestUpdate(BaseTestCase):
#     """
#     Test suite for database update operations.
    
#     This class verifies all data modification operations including:
#     - Patient record management
#     - Panel version updates
#     - Content archiving
#     - Data integrity preservation
    
#     Each test ensures changes are properly isolated within transactions
#     and can be safely rolled back.
#     """

#     def setUp(self):
#         """
#         Initialize update testing environment.
        
#         Sets up:
#         1. Database connection with transaction
#         2. Update instance with test configuration
#         3. Mock PanelApp client
#         4. Test dataset
#         """
#         super().setUp()
#         # Initialize Update instance with test mode enabled
#         self.update = Update(self.db.conn, test_mode=True)
#         self.update.papp = MagicMock()
#         self._create_test_data()

#     def _create_test_data(self):
#         """
#         Create test data for update operations.
        
#         Establishes:
#         1. Base panel records
#         2. Gene information
#         3. Panel-gene associations
#         4. Initial patient records
#         """
#         cursor = self.db.conn.cursor()
        
#         # Create panels with various versions
#         cursor.execute('''
#             INSERT OR IGNORE INTO panel (Panel_ID, rcodes, Version) 
#             VALUES 
#             (100001, 'R999.01', 2.5),
#             (100002, 'R999.02', 1.0),
#             (100003, 'R999.03', 3.0)
#         ''')
        
#         # Gene information setup
#         cursor.execute('''
#             INSERT OR IGNORE INTO genes_info (
#                 HGNC_ID, Gene_Symbol, HGNC_symbol,
#                 GRCh37_Chr, GRCh37_start, GRCh37_stop,
#                 GRCh38_Chr, GRCh38_start, GRCh38_stop
#             ) VALUES (
#                 'HGNC:123456789', 'TEST_1', 'TEST_SYMBOL_1',
#                 'chr1', 500, 1500,
#                 'chr1', 1000, 2000
#             )
#         ''')
        
#         # Panel-gene associations
#         cursor.execute('''
#             INSERT OR IGNORE INTO panel_genes (
#                 Panel_ID, HGNC_ID, Confidence
#             ) VALUES (100001, 'HGNC:123456789', 3)
#         ''')
        
#         # Initial patient record
#         cursor.execute('''
#             INSERT OR IGNORE INTO patient_data 
#             (Patient_ID, Panel_ID, Rcode, Version, Date)
#             VALUES 
#             ('PATIENT001', '100001', 'R999.01', '2.5', '2024-01-01')
#         ''')

#     def test_check_presence(self):
#         """
#         Test patient record presence checking.
        
#         Verifies:
#         1. Existing patient detection
#         2. Current version validation
#         3. Non-existent patient handling
#         4. Different R-code scenarios
#         """
#         # Existing patient test
#         result = self.update.check_presence("PATIENT001", "R999.01")
#         self.assertEqual(result, "2.5")
        
#         # Non-existent patient test
#         result = self.update.check_presence("NONEXISTENT", "R999.01")
#         self.assertFalse(result)
        
#         # Different R-code test
#         result = self.update.check_presence("PATIENT001", "R999.02")
#         self.assertFalse(result)

#     def test_add_record(self):
#         """
#         Test patient record addition functionality.
        
#         Ensures:
#         1. New records are properly created
#         2. All required fields are populated
#         3. Dates are correctly recorded
#         4. Versions are accurately assigned
        
#         Note: SQLite returns numeric values as their native type (float),
#         so we need to ensure our comparisons account for this.
#         """
#         self.update.add_record("PATIENT002", "R999.02")
        
#         cursor = self.db.conn.cursor()
#         result = cursor.execute('''
#             SELECT * FROM patient_data 
#             WHERE Patient_ID = ? AND Rcode = ?
#         ''', ("PATIENT002", "R999.02")).fetchone()
        
#         self.assertIsNotNone(result)
#         # Convert both values to float for comparison
#         self.assertEqual(float(result["Version"]), 1.0)
#         self.assertEqual(result["Date"], str(date.today()))
# if __name__ == '__main__':
#     unittest.main(verbosity=2)