from vimmo.logger.logging_config import logger
from typing import Optional


class Query:
    def __init__(self, connection):
        self.conn = connection

    def get_panel_data(self, panel_id: Optional[int] = None, matches: bool=False):
        """Retrieve all records associated with a specific Panel_ID."""
        logger.info("Pulling all records associated with Panel_ID: %s", panel_id)


        if panel_id is None:
            logger.error("ValueError- Panel_ID must be provided")

            raise ValueError("Panel_ID must be provided.")

        cursor = self.conn.cursor()
        operator = "LIKE" if matches else "="

        # For numeric Panel_ID, LIKE is not typically used. Consider enforcing exact matches.
        if matches:
            # If 'matches' is True, you might want to convert the panel_id to a string and use LIKE
            logger.debug("Using the LIKE query for Panel_ID: %s", panel_id)
            # However, this is unusual for numeric IDs. Consider whether this is necessary.
            panel_id_query = f"%{panel_id}%"
            query = f'''
            SELECT panel.Panel_ID, panel.rcodes, panel.Version, genes_info.HGNC_ID, 
                   genes_info.Gene_Symbol, genes_info.HGNC_symbol, genes_info.GRCh38_Chr, 
                   genes_info.GRCh38_start, genes_info.GRCh38_stop, genes_info.GRCh37_Chr,
                   genes_info.GRCh37_start, genes_info.GRCh37_stop
            FROM panel
            JOIN panel_genes ON panel.Panel_ID = panel_genes.Panel_ID
            JOIN genes_info ON panel_genes.HGNC_ID = genes_info.HGNC_ID
            WHERE panel.Panel_ID LIKE ?
            '''
            result = cursor.execute(query, (panel_id_query,)).fetchall()

        else:
            # Exact match for Panel_ID
            logger.info("Exact match for Panel_ID: %s", panel_id)
            query = f'''
            SELECT panel.Panel_ID, panel.rcodes, panel.Version, genes_info.HGNC_ID, 
                   genes_info.Gene_Symbol, genes_info.HGNC_symbol, genes_info.GRCh38_Chr, 
                   genes_info.GRCh38_start, genes_info.GRCh38_stop, genes_info.GRCh37_Chr,
                   genes_info.GRCh37_start, genes_info.GRCh37_stop
            FROM panel
            JOIN panel_genes ON panel.Panel_ID = panel_genes.Panel_ID
            JOIN genes_info ON panel_genes.HGNC_ID = genes_info.HGNC_ID
            WHERE panel.Panel_ID = ?
            '''
            result = cursor.execute(query, (panel_id,)).fetchall()
        logger.info("The run was successful for Panel_ID: %s, and retrieved %d records.", panel_id, len(result))
        logger.debug(f"Panel_ID: {panel_id}, Result: {result}")


        if result:
            logger.info("Returning %d records for Panel_ID: %s.", len(result), panel_id)
            return {
                "Panel_ID": panel_id,
                "Associated Gene Records": [dict(row) for row in result]
            }
        else:
            logger.warning("No matches found for Panel_ID: %s.", panel_id)
            return {
                "Panel_ID": panel_id,
                "Message": "No matches found."
            }


    def get_panels_by_rcode(self, rcode: str, matches: bool = False):
        """Retrieve all records associated with a specific rcode."""
        logger.info("Pulling all records associated with R_code: %s.", rcode)

        if rcode is None:
            logger.error("ValueError- R_code must be provided")
            raise ValueError("R_code must be provided.")
        cursor = self.conn.cursor()
        operator = "LIKE" if matches else "="
        rcode_query = f"%{rcode}%" if matches else rcode

        logger.debug("Using operator '%s' with R_code query: %s.", operator, rcode_query)

        # Query by rcode
        query = f'''
        SELECT panel.Panel_ID, panel.rcodes, panel.Version, panel_genes.Confidence, genes_info.HGNC_ID, 
               genes_info.Gene_Symbol, genes_info.HGNC_symbol, genes_info.GRCh38_Chr, 
               genes_info.GRCh38_start, genes_info.GRCh38_stop, genes_info.GRCh37_Chr,
                genes_info.GRCh37_start, genes_info.GRCh37_stop
        FROM panel
        JOIN panel_genes ON panel.Panel_ID = panel_genes.Panel_ID
        JOIN genes_info ON panel_genes.HGNC_ID = genes_info.HGNC_ID
        WHERE panel.rcodes {operator} ?
        '''
        logger.debug("Running SQL query: %s.", query)

        result = cursor.execute(query, (rcode_query,)).fetchall()
        logger.info("Query ran successfully for R_code: %s, and retrieved %d records.", rcode, len(result))

        logger.debug(f"R_code Query: {rcode_query}, Result: {result}")
        
        if result:
            logger.info("Returning %d records for R_code: %s.", len(result), rcode)
            return {
                "Rcode": rcode,
                "Associated Gene Records": [dict(row) for row in result]
            }
        else:
            logger.warning("No matches found for R_code: %s.", rcode)
            return {
                "Rcode": rcode,
                "Message": "No matches found for this rcode."
            }

    def get_panels_from_gene_list(self, hgnc_ids: list[str], matches: bool=False) -> list[dict]:
        """
        Retrieves panels associated with multiple HGNC IDs.

        Parameters
        ----------
        hgnc_ids : list[str]
            List of HGNC IDs (e.g., ["HGNC:12345", "HGNC:67890"]).
        matches : bool
            Whether to use wildcard matching or exact matching.
            (For multiple IDs, we only perform exact matches here.)

        Returns
        -------
        list[dict]
            A list of dictionaries containing panel data for the given HGNC IDs.
        """
        logger.info("Pulling all records associated with HGNC_ID: %s.", hgnc_ids)

        if hgnc_ids is None:
            logger.error("ValueError- HGNC_ID must be provided")
            raise ValueError("HGNC_ID must be provided.")

        cursor = self.conn.cursor()
        
        
        
        if matches:
            # If matches is True, you might implement logic to do wildcard search for each ID,
            # but this can become complex. For now, we assume matches=False or handle it as exact.
            # For demonstration, we can handle matches by using LIKE for each ID combined with OR.
            # Example:
            # WHERE panel_genes.HGNC_ID LIKE ?
            # OR panel_genes.HGNC_ID LIKE ?
            # ...
            # You would need to dynamically build the query.
            
            # But let's raise a NotImplementedError if needed:
            logger.warning("Wildcard matching for multiple HGNC_IDs not implemented")
            raise NotImplementedError("Wildcard matching for multiple HGNC_IDs not implemented.")
        else:
            # Exact matching using IN clause
            logger.info("Exact match for HGNC_ID: %s", hgnc_ids)
            placeholders = ','.join('?' * len(hgnc_ids))
            query = f'''
            SELECT panel.Panel_ID, panel.rcodes, genes_info.Gene_Symbol
            FROM panel
            JOIN panel_genes ON panel.Panel_ID = panel_genes.Panel_ID
            JOIN genes_info ON panel_genes.HGNC_ID = genes_info.HGNC_ID
            WHERE panel_genes.HGNC_ID IN ({placeholders})
            '''
            logger.debug("Running SQL query: %s.", query)

            result = cursor.execute(query, tuple(hgnc_ids)).fetchall()
            logger.info("Query ran successfully for HGNC_ID: %s, and retrieved %d records.", hgnc_ids, len(result))
            logger.debug(f"HGNC_ID: {hgnc_ids}, Result: {result}")
            

            if result:
                logger.info("Returning %d records for HGNC_ID: %s.", len(result), hgnc_ids)
                return {
                    "HGNC_IDs": hgnc_ids,
                    "Panels": [dict(row) for row in result]
                }
            else:
                logger.warning("No matches found for HGNC_ID: %s.", hgnc_ids)
                return {
                    "HGNC_IDs": hgnc_ids,
                    "Message": "Could not find any match for the provided HGNC IDs."
                }
        
    def get_gene_list(self,panel_id=None,r_code=None,matches=False):
        logger.info("Pulling the gene list associated with Panel_ID: %s, R_code: %s.", panel_id, r_code)

        if panel_id:
            logger.debug("Pulling the panel data for Panel_ID: %s.", panel_id)
            panel_data = self.get_panel_data(panel_id=panel_id, matches=matches)
            if "Message" in panel_data:
                logger.warning("No panel data found for Panel_ID: %s.", panel_id)
                return panel_data
            logger.info("Successfully pulled panel data for Panel_ID: %s.", panel_id)
            gene_query={record["HGNC_ID"] for record in panel_data["Associated Gene Records"]}
        elif r_code:
            logger.debug("Pulling the panel data for R_code: %s.", r_code)
            panel_data = self.get_panels_by_rcode(rcode=r_code, matches=matches)
            if "Message" in panel_data:
                logger.warning("No panel data found for R_code: %s.", r_code)
                return panel_data
            logger.info("Successfully pulled panel data for R_code: %s.", r_code)
            gene_query={record["HGNC_ID"] for record in panel_data["Associated Gene Records"]}

        logger.debug(f"Gene list: {gene_query}")
        return gene_query
    
    def get_gene_symbol(self, ids_to_replace):
        logger.info("Pulling the gene_symbol called with IDs to replace: %s.", ids_to_replace)

        cursor = self.conn.cursor()
        placeholders = ', '.join(['?'] * len(ids_to_replace))

        logger.debug("Running SQL query with placeholders for IDs: %s.", placeholders)
        query = f'''
            SELECT HGNC_ID, HGNC_symbol
            FROM genes_info
            WHERE HGNC_ID IN ({placeholders})
            '''
        
        result = cursor.execute(query, list(ids_to_replace)).fetchall()
        logger.debug(f"id replaced: {ids_to_replace}")
        return result
    
    def local_bed(self, gene_query, genome_build):
        if genome_build=="GRCh38":
            cursor = self.conn.cursor()
            # Prepare placeholders for SQL IN clause
            placeholders = ','.join(['?'] * len(gene_query))
            query = f'''
            SELECT Chromosome, Start, End, Name, HGNC_ID, Transcript, Strand, Type
            FROM bed38
            WHERE HGNC_ID IN ({placeholders})
            '''
            local_bed_records=cursor.execute(query, list(gene_query))
            logger.info(f"Local bed searched: {gene_query}, {genome_build}")
            return local_bed_records
        elif genome_build=="GRCh37":
            cursor = self.conn.cursor()
            # Prepare placeholders for SQL IN clause
            placeholders = ','.join(['?'] * len(gene_query))
            query = f'''
            SELECT Chromosome, Start, End, Name, HGNC_ID, Transcript, Strand, Type
            FROM bed37
            WHERE HGNC_ID IN ({placeholders})
            '''
            local_bed_records = cursor.execute(query, list(gene_query))
            logger.info(f"Local bed searched: {gene_query}, {genome_build}")
            return local_bed_records
    
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
        
        patient_history = cursor.execute('''
        SELECT Version
        FROM patient_data
        WHERE Date = (
            SELECT MAX(Date) 
            FROM patient_data
            WHERE Patient_ID = ? AND Rcode = ?
        ) 
        AND Version = (
            SELECT MAX(Version)
            FROM patient_data
            WHERE Patient_ID = ? AND Rcode = ?
            AND Date = (
                SELECT MAX(Date)
                FROM patient_data
                WHERE Patient_ID = ? AND Rcode = ?
            )
        )
        AND Patient_ID = ? AND Rcode = ?         
        ''', (Patient_id, Rcode, Patient_id, Rcode, Patient_id, Rcode, Patient_id, Rcode)).fetchone()
        
        if patient_history is None:
            return None
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


        database_version = cursor.execute( f'''
        SELECT Version
        FROM panel
        WHERE rcodes = ?
        ''', (Rcode,)).fetchone()
        
        if database_version == None:
            return None
        else:
            return database_version[0]
    
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

        panel_id = cursor.execute(f'''
        SELECT Panel_ID
        FROM panel
        WHERE rcodes = ?
        ''', (Rcode,)).fetchone()
        
        if panel_id is None:
            return None
        else:
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
        
        patient_records_rows = cursor.execute(f'''
        SELECT Rcode, Version, Date
        FROM patient_data
        WHERE Patient_ID = ?
        ''', (Patient_id,)).fetchall()  # The returned query is a sqlite3 row object list[tuples()].

        patient_records = {}  # Instantiation of object for output dict.
        for i,record in enumerate(patient_records_rows):
            patient_records.update({i:{record["Date"]: [record["Rcode"], record["Version"]]}})
        return patient_records
    
    def return_all_patients(self, Rcode: str) -> dict:       
        cursor = self.conn.cursor()
        rcode_records_rows = cursor.execute(f"""
        SELECT Patient_ID, Version, Date
        FROM patient_data
        WHERE Rcode = ?
        """, (Rcode,)).fetchall() 
    
        rcode_records = {} # Instantiation of object for output dict
        for i,record in enumerate(rcode_records_rows):
            rcode_records.update({i:{record["Date"]:[record["Patient_ID"], record["Version"]]}})
        return rcode_records
    

    def current_panel_contents(self, panelID: str) -> dict:
        cursor = self.conn.cursor()
        query = f"""
        SELECT HGNC_ID, Confidence
        FROM panel_genes 
        WHERE Panel_ID = ?
"""
        current_panel_data = cursor.execute(query, (panelID,)).fetchall()
        current_data = {} # Instantiation of object for output dict{}
        
        for tuple in current_panel_data:  # Loop through the tuples (HGNC ID, Confidence)
            current_data.update({tuple["HGNC_ID"]: tuple["Confidence"]})   # Insert gene, conf pair into output dict
        return current_data



    def historic_panel_retrieval(self, panelID: str, version: float):
        """ 
        Returns panel contents for an archived panel version

        Parameters
        ----------
        PanelID: str
        The panelApp panelID for the queried R code

        version: float
        The version number of the archived panel

        Returns
        -------
        historical_data: dict{}
        The contents of the archived panel version


        Notes
        -----
        - Executes a simple SQL query to Vimmo's 'panel_genes_archive' table (see db schema in repository)
        - The dictionary returns key value pairs as follows {HGNC_ID:Confidence} 

        Example
        -----
        Input: PanelID 635, version 2.1
        Query class method: historic_panel_retrieval(635,2.1) -> {
                                                                "HGNC:1071": 3,
                                                                "HGNC:2186": 2,
                                                                "HGNC:20000": 3
                                                                }
        """
        
        cursor = self.conn.cursor()
   

        query = f"""
        SELECT HGNC_ID, Confidence
        FROM panel_genes_archive
        WHERE Panel_ID = ? AND Version = ?
"""

        historic_panel_data = cursor.execute(query, (panelID, version)).fetchall()
        historic_data = {} # Instantiation of object for output dict{}
        for tuple in historic_panel_data:  # Loop through the tuples (HGNC ID, Confidence)
                                        
            historic_data.update({tuple["HGNC_ID"]: tuple["Confidence"]})   # Insert gene, conf pair into output dict

        return historic_data

    def compare_panel_versions(self, historic_version: dict, current_version: dict) -> dict:
        # find genes added
        genes_added = {}
        for gene in current_version.keys():
            if gene in historic_version.keys():
                pass
            else:
                genes_added.update({gene:current_version[gene]})
        # find genes remove
        genes_removed = {}
        for gene in historic_version.keys():
            if gene in current_version:
                pass
            else:
                genes_removed.update({gene:historic_version[gene]})
        # find gene conf change
        conf_changes = {}
        for HGNC in current_version.keys():
            if HGNC not in historic_version.keys(): # If gene new to panel, pass
                pass
            elif HGNC in historic_version.keys() and current_version[HGNC] == historic_version[HGNC]: # If gene confidence unchanged, pass
                pass
            
            elif HGNC in historic_version.keys() and current_version[HGNC] != historic_version[HGNC]: # If gene in both versions and has changed, up
                conf_changes.update({HGNC:(historic_version[HGNC],current_version[HGNC])})
            

        return [genes_added, genes_removed, conf_changes] # Return the panel comparison information