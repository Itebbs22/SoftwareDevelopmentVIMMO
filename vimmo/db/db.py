
import sqlite3
from sqlite3 import Connection
from typing import Optional, List, Tuple, Dict, Any
import importlib.resources
import os


class Database:
    def __init__(self, db_path: str = 'db/panels_data.db'):
        self.db_path = db_path
        self.conn: Optional[Connection] = None

    def get_db_path(self) -> str:
        """
        Get the database path, handling both development and installed scenarios.
        """
        try:
            # First try to get the database from the installed package
            with importlib.resources.path('vimmo.db', 'panels_data.db') as db_path:
                return str(db_path)
        except Exception:
            # If that fails, try the development path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dev_db_path = os.path.join(current_dir, self.db_path)
            
            if os.path.exists(dev_db_path):
                return dev_db_path
            else:
                raise FileNotFoundError("database file could not be located")
            


    def connect(self):
        """Establish a connection to the SQLite database."""
        if not self.conn:
            db_path = self.get_db_path()
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
    
    def _initialize_tables(self):
        """Create necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Create panel table (assuming it’s done elsewhere, but included here if needed)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS panel (
            Panel_ID INTEGER PRIMARY KEY,
            rcodes TEXT,
            Version TEXT
        )
        ''')
        
        # Create genes_info table (assuming it’s done elsewhere, but included here if needed)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS genes_info (
            HGNC_ID TEXT PRIMARY KEY,
            Gene_ID TEXT,
            HGNC_symbol TEXT,
            Gene_Symbol TEXT,
            GRCh38_Chr TEXT,
            GRCh38_start INTEGER,
            GRCh38_stop INTEGER,
            GRCh37_Chr TEXT,
            GRCh37_start INTEGER,
            GRCh37_stop INTEGER
        )
        ''')
        
        # Create patient_data table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            panel_id INTEGER,
            rcode TEXT,
            version INT,
            date DATE,
            FOREIGN KEY (panel_id) REFERENCES panel (Panel_ID)
        )
        ''')

        self.conn.commit()

        
    def get_patient_data(self, patient_id: str) -> List[Tuple]:
        """Retrieve patient data by patient_id."""
        cursor = self.conn.cursor()
        query = '''
        SELECT patient_data.patient_id, patient_data.panel_id, patient_data.rcode, patient_data.panel_version,
               panel.rcodes, panel.Version
        FROM patient_data
        JOIN panel ON patient_data.panel_id = panel.Panel_ID
        WHERE patient_data.patient_id = ?
        '''
        result = cursor.execute(query, (patient_id,)).fetchall()
        return [dict(row) for row in result]  # Convert rows to dictionaries for easy JSON conversion
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
        
class Query:
    def __init__(self, connection):
        self.conn = connection

    def get_panel_data(self, panel_id: Optional[int] = None, matches: bool=False):
        """Retrieve all records associated with a specific Panel_ID."""
        if panel_id is None:
            raise ValueError("Panel_ID must be provided.")

        cursor = self.conn.cursor()
        operator = "LIKE" if matches else "="

        # For numeric Panel_ID, LIKE is not typically used. Consider enforcing exact matches.
        if matches:
            # If 'matches' is True, you might want to convert the panel_id to a string and use LIKE
            # However, this is unusual for numeric IDs. Consider whether this is necessary.
            panel_id_query = f"%{panel_id}%"
            query = f'''
            SELECT panel.Panel_ID, panel.rcodes, panel.Version, genes_info.HGNC_ID, 
                   genes_info.Gene_Symbol, genes_info.HGNC_symbol, genes_info.GRCh38_Chr, 
                   genes_info.GRCh38_start, genes_info.GRCh38_stop
            FROM panel
            JOIN panel_genes ON panel.Panel_ID = panel_genes.Panel_ID
            JOIN genes_info ON panel_genes.HGNC_ID = genes_info.HGNC_ID
            WHERE panel.Panel_ID LIKE ?
            '''
            result = cursor.execute(query, (panel_id_query,)).fetchall()
        else:
            # Exact match for Panel_ID
            query = f'''
            SELECT panel.Panel_ID, panel.rcodes, panel.Version, genes_info.HGNC_ID, 
                   genes_info.Gene_Symbol, genes_info.HGNC_symbol, genes_info.GRCh38_Chr, 
                   genes_info.GRCh38_start, genes_info.GRCh38_stop
            FROM panel
            JOIN panel_genes ON panel.Panel_ID = panel_genes.Panel_ID
            JOIN genes_info ON panel_genes.HGNC_ID = genes_info.HGNC_ID
            WHERE panel.Panel_ID = ?
            '''
            result = cursor.execute(query, (panel_id,)).fetchall()

        if result:
            return {
                "Panel_ID": panel_id,
                "Associated Gene Records": [dict(row) for row in result]
            }
        else:
            return {
                "Panel_ID": panel_id,
                "Message": "No matches found."
            }

    def get_panels_by_rcode(self, rcode: str, matches: bool = False):
        """Retrieve all records associated with a specific rcode."""
        cursor = self.conn.cursor()
        operator = "LIKE" if matches else "="
        rcode_query = f"%{rcode}%" if matches else rcode

        # Query by rcode
        query = f'''
        SELECT panel.Panel_ID, panel.rcodes, panel.Version, genes_info.HGNC_ID, 
               genes_info.Gene_Symbol, genes_info.HGNC_symbol, genes_info.GRCh38_Chr, 
               genes_info.GRCh38_start, genes_info.GRCh38_stop
        FROM panel
        JOIN panel_genes ON panel.Panel_ID = panel_genes.Panel_ID
        JOIN genes_info ON panel_genes.HGNC_ID = genes_info.HGNC_ID
        WHERE panel.rcodes {operator} ?
        '''
        result = cursor.execute(query, (rcode_query,)).fetchall()

        if result:
            return {
                "Rcode": rcode,
                "Associated Gene Records": [dict(row) for row in result]
            }
        else:
            return {
                "Rcode": rcode,
                "Message": "No matches found for this rcode."
            }

    def get_panels_from_gene(self, hgnc_id: str, matches: bool=False) -> list[dict]:
        cursor = self.conn.cursor()
        operator = "LIKE" if matches else "="
        query = f'''
        SELECT panel.Panel_ID, panel.rcodes, genes_info.Gene_Symbol
        FROM panel
        JOIN panel_genes ON panel.Panel_ID = panel_genes.Panel_ID
        JOIN genes_info ON panel_genes.HGNC_ID = genes_info.HGNC_ID
        WHERE panel_genes.HGNC_ID {operator} ?
        '''

        result = cursor.execute(query, (hgnc_id,)).fetchall()
        if result:
            return {
                "HGNC ID": hgnc_id,
                "Panels": [dict(row) for row in result]
            }
        else:
            return {
                "HGNC ID": hgnc_id,
                "Message": "Could not find any match for the HGNC ID."
            }
    
    def check_patient_history(self, Patient_id: str, Rcode) -> str:
            """
            Retrieves the latest test version for a given patient and R code within the Vimmo database. 
            
            Parameters
            ----------
            Patient_id: str (required)
            The patient id, linked to the test history for a given patient

            Rcode: str (required)
            A specific R code to search for a given patient
            

            Returns
            -------
            patient_history: float
            The most recent version of a R code that a given patient has had
            
            Notes
            -----
            - Excutes a simple SQL query
            - Queries the patient_data table
            - For the entire test history of a patient, see return_all_records()

            Example
            -----
            User UI input: Patient ID = 123, Rcode R208

            Query class method: check_patient_history(123, R208) -> 2.5 

            Here, '2.5' is the most recent version of R208 conducted on patient 123
            """
            
            cursor = self.conn.cursor()
            operator = "="
            query = f'''
            SELECT Version
            FROM patient_data
            WHERE DATE {operator} (SELECT MAX(DATE) FROM patient_data WHERE Rcode {operator} ? AND Patient_ID {operator} ?)         
    '''
            patient_history = cursor.execute(query, (Rcode, Patient_id)).fetchone()
            return patient_history[0]

    def get_db_latest_version(self, Rcode: str) -> str:
        """
        Returns the most uptodate panel verision stored within the Vimmo database for an input R code

        Parameters
        ----------
        Rcode : str
        The R code to search for in the Vimmo's database

        Returns
        -------
        panel_id: str
        The corresponding version for the corresponding R code panels_data.db - 'panel' table (see schema in repo)

        Notes
        -----
        - Excutes a simple SQL query that that selections the

        Example
        -----
        User UI input: R208
        Query class method: rcode_to_panelID(R208) -> 635 
        
        Here 635 is the R208 panel ID, as of (26/11/24)
        """
        cursor = self.conn.cursor()
        operator = "="
        query = f'''
        SELECT panel.Version
        FROM panel
        WHERE panel.rcodes {operator} ?
        '''
        database_version = cursor.execute(query, (Rcode,)).fetchone()
        return str(database_version[0])
    
    def rcode_to_panelID(self, Rcode: str) -> str:
        """
        Returns the panelapp panel ID for an input panelapp Rcode

        Parameters
        ----------
        Rcode : str
        The R code to search for in the Vimmo's database

        Returns
        -------
        panel_id[0]: str
        The corresponding panel ID for the input R code


        Notes
        -----
        - Executes a simple SQL query to Vimmo's 'panel' table (see db schema in repository root)
        - panel_id[0] indexed to access the sql lite 'row' object type

        Example
        -----
        User UI input: R208
        Query class method: rcode_to_panelID(R208) -> 635 
        
        Here 635 is the R208 panel ID, as of (26/11/24)
        """

        cursor = self.conn.cursor()
        operator = "="
        query = f'''
        SELECT Panel_ID
        FROM panel
        WHERE panel.rcodes {operator} ?
        '''
        panel_id = cursor.execute(query, (Rcode,)).fetchone()
        return panel_id[0] 
    
    def return_all_records(self, Patient_id: str) -> str:
        """
        Returns all historical tests stored for a given patient

        Parameters
        ----------
        Rcode : str
        The R code to search for in the Vimmo's database

        Returns
        -------
        patient_records: list[list[]]
        The list of Rcodes, versions and dates that a patient has had


        Notes
        -----
        - Executes a simple SQL query to Vimmo's 'patient_data' table (see db schema in repository root)
        - Returns a list of lists. Each nested list represents a row in the 

        Example
        -----
        User UI input: R208
        Query class method: return_all_records(R208) -> [[R208, 2.5, 2000-1-5],[R132, 1, 2024-1-2]] 
        
        """
        cursor = self.conn.cursor()
        operator = "="
        query = f'''
        SELECT Rcode, Version, Date
        FROM patient_data
        WHERE patient_data.Patient_ID {operator} ?
'''
     
        patient_records_rows = cursor.execute(query, (Patient_id,)).fetchall() # The returned query is a sqlite3 row object list[tuples()]

        patient_records = [] # Instantiation of object for output list[list[]]
        for tuple in patient_records_rows:  # Loop through the tuples returned by sql query
            entry = []                      # Each list contains the values from the patient_data table row returned
            entry.append(tuple["Rcode"])    # Append the values correspondings to the column 'Rcode'
            entry.append(tuple["Version"])  # 'Version'
            entry.append(tuple["Date"])     # 'Date'
            patient_records.append(entry)   # Add the rows values to the output list


        return patient_records
        
    def current_panel_contents(self, panelID: str) -> list[list]:
        cursor = self.conn.cursor()
        operator = "="

        query = f"""
        SELECT HGNC_ID, Version, Confidence
        FROM panel_genes 
        WHERE panel_genes.Panel_ID {operator} ?
"""
        current_panel_data = cursor.execute(query, (panelID)).fetchall()
        return current_panel_data
        

    def historic_panel_contents(self, panelID: str, version):
        cursor = self.conn.cursor()
        operator = "="

        query = f"""
        SELECT Rcode, Version, Date
        FROM historic_data
        WHERE patient_data.Patient_ID {operator} ?
"""

        historic_panel_data = cursor.execute(query, (panelID, version)).fetchall()
        return historic_panel_data
        ...


class Update:
    def __init__(self,connection):
        self.conn = connection
    
    def add_record(self, patient_id: str, rcode: str, date, version: Optional[str]):
        """Add a new patient record using either a panel_id or an rcode."""
        cursor = self.conn.cursor()
        # 1. Check if the record already exists
        # YES - return 'record already exists'
        # NO - Update db
        operator = "="
        does_exists = cursor.execute(f"""
        SELECT Rcode, Date, Patient_ID
        FROM Patient_data
        WHERE Rcode {operator} ? AND Date {operator} ? AND Patient_ID {operator} ?
        """, (rcode, date, patient_id)).fetchone()

        if does_exists != None: # Check if the record is already in the table 
            return f"Patient record (Patient id: {patient_id}, Rcode {rcode}, Date {date})"
        elif version: # If version has been input
            ...
            # 1. fetch panel id from db (rcode_to_id())
            # 2. add record to the panel (sql INSERT INTO query)
        else: # If no version has been provided
            ...
            # fetch panel ID, current panel version (must check up-to-date)
            # add record to the patient_history table
            

            
            self.conn.commit()