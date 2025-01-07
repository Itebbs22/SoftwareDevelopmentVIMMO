from vimmo.logger.logging_config import logger
from vimmo.utils.panelapp import PanelAppClient
from vimmo.db.db_query import Query
from datetime import date

class Update:
    def __init__(self, connection, test_mode=False):
        self.conn = connection
        self.query = Query(self.conn)
        self.papp = PanelAppClient(base_url="https://panelapp.genomicsengland.co.uk/api/v1/panels")
        self.test_mode = test_mode
    
    def check_presence(self, patient_id: str, rcode: str):
        """
        Finds existing patient test in db if exists

        Parameters
        ----------
        - patient_id (required): str
          Series of integers used as the patient identifier
        - rcode (required): str
          A specific R code to search for a given patient 

        Returns
        -------
        current version (int)
        Current version of the input rcode 

        or 

        False (bool)

        Notes
        -------
        - Uses a simple SQL query to match a patient id, rcode and version to record in db
        - If not present, the patient doesn't have a record of most recent panel version
        - In absence, False returned
        - If present, version returned

        Example 
        -------
        Record present
        User input : rcode R123, patient_id 789
        check_preseence(R123,789) ->
        2.1 (int)

        Record absent
        User input : rcode R321, patient_id 654
        check_presence(321,654) ->
        False (bool) 
        """
        current_version = str(self.query.get_db_latest_version(rcode)) # Retrieve the latest panel version from our db

        cursor = self.conn.cursor()
        does_exists = cursor.execute(f"""
        SELECT Version
        FROM patient_data
        WHERE Patient_ID = ? AND Rcode = ? AND Version = ?
        """, (patient_id, rcode, current_version)).fetchone() # query patient_data table for entries matching the query rcode, patient id and current version
        
        if does_exists != None: # if a value is returned, a patient record matches the query
            return current_version # return the current version 
        else:
            return False 

    
    def add_record(self, patient_id: str, rcode: str) -> str:
        """
        Add a new patient record using an rcode or panel_id

        Parameters
        ----------
        - patient_id (required): str
          Series of integers used as the patient identifier
        - rcode (required): str
          A specific R code to search for a given patient 

        Returns
        -------
        str

        Notes
        -------
        - Uses a simple SQL query add patient record to 'patient_data' table
        - Explanatory message returned as str to endpoints.py

        Example 
        -------
        User input : rcode R123, patient_id 789
        add_record(R123,789)
        Record added to database: Patient_id: 789, Rcode: R123, version: 3.0, date: 2024-11-05
       
        """
        version = str(self.query.get_db_latest_version(rcode)) # Retrieve the latest panel version from our db
        panel_id = str(self.query.rcode_to_panelID(rcode))     # Retrieve the panel id for input Rcode
        date_today = str(date.today())                         # Create object with date of query
        cursor = self.conn.cursor()
        
        cursor.execute(f"""
        INSERT INTO patient_data 
        VALUES (?, ?, ?, ?, ?) 
        """, (patient_id, panel_id, rcode, version, date_today)) # Insert data into table
        
        # Only commit if not in test mode
        if not self.test_mode:
            self.conn.commit()
        return f'Record added to database: Patient_id: {patient_id}, Rcode: {rcode}, version: {version}, date: {date_today}'
    
    def update_panels_version(self, rcode: str, new_version: str, panel_id: str):
        """
        Update the panel table with new version

        Parameters
        ----------
       
        - rcode (required): str
          A specific R code to search for a given patient
        - new_version (required): str
          Most recent panel version
        - panel_id (requeird): str
          Panelapp panel Id corresponding to input Rcode 

        Returns
        -------
        N/a 

        Notes
        -------
        - Uses a simple SQL query to update 'panel' table with new version


        Example 
        -------
        User input : rcode R45, patient_id 789
        add_record(R45, 2.2, 3) -> 
        <3    R45     2.2> inserted into db
        """
     
        cursor = self.conn.cursor()
        operator = "="
        cursor.execute(f"""
        UPDATE panel
        SET Panel_ID {operator} ?, rcodes {operator} ?, Version {operator} ?
        WHERE Panel_ID {operator} ? AND rcodes {operator} ?
        """, (panel_id,rcode,new_version,panel_id,rcode))

        self.conn.commit()
    
    def archive_panel_contents(self, panel_id: str, archive_version: str):
        """
        Archives outdated panel contents
        
        Parameters
        ----------
       
        - panel_id (required): str
          Panelapp panel Id corresponding to input Rcode 
        - archive_version (required): str
          Outdated panel version within Vimmo db
         

        Returns
        -------
        N/a 

        Notes
        -------
        - Uses a simple SQL query to archive outdated panel contents
        - Panel data archived from 'panel_genes' -> 'archive_panel_genes'

        """
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            INSERT INTO panel_genes_archive (Panel_ID, HGNC_ID, Version, Confidence)
            SELECT pg.Panel_ID, pg.HGNC_ID, ?, pg.Confidence
            FROM panel_genes pg
            WHERE pg.Panel_ID = ?
            AND NOT EXISTS (
                SELECT 1 
                FROM panel_genes_archive pga 
                WHERE pga.Panel_ID = pg.Panel_ID 
                AND pga.HGNC_ID = pg.HGNC_ID 
                AND pga.Version = ?
            )
            ''', (archive_version, panel_id, archive_version)
        )
        self.conn.commit()

    def update_gene_contents(self, Rcode: str, panel_id: str):
        """
        Updates the panel_genes table with new panel version contents
        
        Parameters
        ----------
       
        - panel_id (required): str
          Panelapp panel Id corresponding to input Rcode 
        - Rcode (required): str
          PanelApp rare diease panel code
         

        Returns
        -------
        N/a 

        Notes
        -------
        - Uses a simple SQL query to populate db with update panel contents
        - First, retrieves most recent panel contents <get_genes_HGNC()>
        - Second, deletes all genes in 'panel_genes' with given panel _id
        - Third, populates table with new genes + conf

        """
        genes = self.papp.get_genes_HGNC(Rcode) # All HGNC:conf in panel version

        cursor = self.conn.cursor()

        cursor.execute(f"""
        DELETE FROM panel_genes
        WHERE Panel_ID = ?
        """,(panel_id,))

        for gene in genes:
        
            cursor.execute(f"""
            INSERT INTO panel_genes (Panel_ID, HGNC_ID, Confidence)
            VALUES (?, ?, ?)
            """,(panel_id, gene, genes[gene]))
        
        self.conn.commit()
        
