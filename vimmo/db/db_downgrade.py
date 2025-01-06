
from vimmo.logger.logging_config import logger
from vimmo.db.db_query import Query
from vimmo.db.db_update import Update
from vimmo.utils.panelapp import PanelAppClient

class Downgrade:
    def __init__(self,connection):
        self.conn = connection
        self.query = Query(self.conn)
        self.update=Update(self.conn)
        self.papp = PanelAppClient(base_url="https://panelapp.genomicsengland.co.uk/api/v1/panels")


    def _get_current_genes(self, panel_id: str) -> dict:
        """Get current genes and their confidence levels for a panel"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT HGNC_ID, Confidence
            FROM panel_genes
            WHERE Panel_ID = ?
        """, (panel_id,))
        return {row["HGNC_ID"]: row["Confidence"] for row in cursor.fetchall()}
    
    def change_panels_version(self, rcode: str, new_version: float, panel_id: str):
        """Update the panel table with the downgraded version"""
        cursor = self.conn.cursor()
        logger.info(f"Updating panel version: {new_version}, {panel_id}, {rcode}")
        cursor.execute("""
            UPDATE panel 
            SET Version = ?
            WHERE Panel_ID = ? AND rcodes = ?
        """, (new_version, panel_id, rcode))
        
        if cursor.rowcount == 0:
            logger.error(f"No matching record found for Panel_ID: {panel_id} and R_code: {rcode}.")
            raise ValueError(f"No matching record found for Panel_ID: {panel_id} and rcode: {rcode}")
        

    def _extract_genes_from_records(self, panel_records: dict) -> list:
        """
        Extract gene information from panel records
        Returns list of tuples: [(HGNC_ID, Confidence), ...]
        """
        genes_data = []
        for gene in panel_records.get("genes", []):
            # Extract HGNC ID and confidence level
            if "gene_data" in gene and "hgnc_id" in gene["gene_data"]:
                hgnc_id = gene["gene_data"]["hgnc_id"]
                # Convert confidence_level to int, default to 0 if not present
                confidence = int(gene.get("confidence_level", 0))
                genes_data.append((hgnc_id, confidence))
        return genes_data


        
    def change_gene_contents(self, panel_id: str, new_genes: list) -> dict:
        """
        Update panel_genes table with downgraded version contents
        
        Parameters:
        -----------
        panel_id: str
            The Panel_ID to update
        new_genes: list
            List of tuples containing (HGNC_ID, Confidence) pairs
        
        Returns:
        --------
        dict
            Summary of changes made to the gene contents
        """
        cursor = self.conn.cursor()
        
        # Get current genes for comparison
        current_genes = self._get_current_genes(panel_id)
        
        try:
            # Create dictionary of new genes
            new_gene_dict = {hgnc_id: conf for hgnc_id, conf in new_genes}
            
            # Track changes
            added_genes = [hgnc_id for hgnc_id in new_gene_dict if hgnc_id not in current_genes]
            removed_genes = [hgnc_id for hgnc_id in current_genes if hgnc_id not in new_gene_dict]
            confidence_changes = [
                {
                    "hgnc_id": hgnc_id,
                    "old_confidence": current_genes[hgnc_id],
                    "new_confidence": new_gene_dict[hgnc_id]
                }
                for hgnc_id in current_genes
                if hgnc_id in new_gene_dict and current_genes[hgnc_id] != new_gene_dict[hgnc_id]
            ]
            
            # Check if there are any changes
            if not added_genes and not removed_genes and not confidence_changes:
                return {"message": "No changes detected between versions"}
            
            # If there are changes, proceed with update
            logger.info(f"Db deleting records {panel_id}")
            cursor.execute("""
                DELETE FROM panel_genes 
                WHERE Panel_ID = ?
            """, (panel_id,))
            
            # Insert new records
            for hgnc_id, confidence in new_genes:
                logger.info(f"Db is updating {panel_id}, {hgnc_id}, {confidence}")
                cursor.execute("""
                    INSERT INTO panel_genes (Panel_ID, HGNC_ID, Confidence)
                    VALUES (?, ?, ?)
                """, (panel_id, hgnc_id, confidence))
            
            # Return detailed changes
            return {
                "added": added_genes,
                "removed": removed_genes,
                "confidence_changed": confidence_changes
            }
                
        except Exception as e:
            logger.warning(f"Failed to update gene contents: {str(e)}")
            raise Exception(f"Failed to update gene contents: {str(e)}")

    
    
    def process_downgrade(self, rcode: str, panel_id: str, version: float, panel_records: dict) -> dict:
        """
        Process the downgrade operation for a panel
        """
        cursor = self.conn.cursor()
        
        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            logger.info("Db is using transaction to downgrade")
            
            # Get current version before changes
            current_version = self.query.get_db_latest_version(rcode)
            
            
            # Update panel version
            logger.info(f"Downgrading {rcode} to {version}")
            self.change_panels_version(rcode, version, panel_id)
            
            # Extract and process genes from panel_records
            new_genes = self._extract_genes_from_records(panel_records)
            
            # Update gene contents
            changes = self.change_gene_contents(panel_id, new_genes)
            
            # Commit transaction
            self.conn.commit()
            
            return {
                "panel_id": panel_id,
                "rcode": rcode,
                "previous_version": current_version,
                "new_version": version,
                "changes": changes
            }
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.warning(f"Failed to process downgrade: {str(e)}")
            raise Exception(f"Failed to process downgrade: {str(e)}")
