from vimmo.logger.logging_config import logger
import requests
from urllib.parse import quote
import pandas as pd
from io import BytesIO
from vimmo.db.db_query import Query
from vimmo.API import get_db
import os

class VarValAPIError(Exception):
    """Custom exception for errors related to the VarVal API."""
    pass


class VarValClient:
    def __init__(self, base_url='https://rest.variantvalidator.org/VariantValidator/tools/gene2transcripts_v2'):
        """
        Initialize the VariantValidator client.

        Parameters:
        - base_url (str): Base URL for the VariantValidator API.
        """

        self.base_url = base_url

    def _check_response(self, url):
        """
        Sends a GET request to the specified URL and validates the response.

        Parameters:
        - url (str): URL to send the GET request to.

        Returns:
        - dict: Parsed JSON response from the API.

        Raises:
        - VarValAPIError: If the request fails or the status code is not 200.
        """
        try:
            response = requests.get(url)
        except :
            logger.error(f"Failed to connect to {url}. Please check your internet connection and try again.")
            raise VarValAPIError(f"Failed to connect. Please check your internet connection and try again")
        else:
            if response.ok:
                logger.info(f"Successfully pulled data from URL: {url}")
                return response.json()
            else:
                logger.warning(f"Failed to get data from VarVal API with status code:{response.status_code}")
                raise VarValAPIError(f"Failed to get data from VarVal API with Status code:{response.status_code}. Please switch to local endpoint if you still need data.")

    def get_gene_data(self, gene_query, genome_build='GRCh38', transcript_set='all', limit_transcripts='mane_select'):
        """
        Fetches gene data from the VariantValidator API.

        Parameters:
        - gene_query (str): Gene identifier (HGNC ID, symbol, or transcript ID).
        - genome_build (str): Genome build version (e.g., 'GRCh37' or 'GRCh38').
        - transcript_set (str): Specifies the transcript set ('refseq', 'ensembl', or 'all').
        - limit_transcripts (str): Specifies transcript filtering criteria ('mane', 'select', or 'all').

        Returns:
        - dict: JSON response containing gene data.

        Raises:
        - VarValAPIError: If the API request fails or returns an error response.
        """
        # Encode URL components to ensure compatibility
        encoded_gene_query = quote(gene_query)
        encoded_transcript_set = quote(transcript_set)
        encoded_limit_transcripts = quote(limit_transcripts)
        encoded_genome_build = quote(genome_build)

        # Construct the full URL
        url = (
            f"{self.base_url}/"
            f"{encoded_gene_query}/"
            f"{encoded_limit_transcripts}/"
            f"{encoded_transcript_set}/"
            f"{encoded_genome_build}"
        )

        # Make the request and return the response
        logger.info(f"Pulling gene data from URL: {url}.")
        return self._check_response(url)
    


    def get_hgnc_ids_with_replacements(self, gene_query):
        """
        Retrieves HGNC_IDs for a given panel_id and replaces specified problematic HGNC_IDs with their HGNC_symbols.
        
        Parameters:
        - panel_id (int): The ID of the panel to query.
        - prob_gene_file (str): Path to the file containing problematic HGNC_IDs, one per line.
        - db_path (str): Path to the SQLite database file.
        
        Returns:
        - final_output (set): A set containing HGNC_IDs and HGNC_symbols with replacements made for problematic IDs.
        """
            
        # Step 2: Load prob_gene_list from the file
        db_dir=os.path.dirname(os.path.realpath(__file__))
        prob_gene_file=os.path.join(db_dir,"problem_genes.txt")
        with open(prob_gene_file, 'r') as file:
            prob_gene_list = [line.strip() for line in file if line.strip()]
        logger.info("Loaded problematic gene list successfully.")
        
        
        # Step 3: Find the HGNC_IDs that need to be replaced
        ids_to_replace = [gene for gene in gene_query if gene in prob_gene_list]
        logger.info(f"IDs to replace identified: {ids_to_replace}")
        
        # Step 4: Retrieve HGNC_symbols for the IDs to replace
        if ids_to_replace:
            # Retrieve the database connection
            db = get_db()
            # Initialize a query object with the database connection
            query = Query(db.conn)
            result = query.get_gene_symbol(ids_to_replace)
            id_to_symbol = {row[0]: row[1] for row in result}
            logger.info(f"HGNC_symbols retrieved for ID replacement: {id_to_symbol}")
            
        else:
            id_to_symbol = {}
            logger.info("No IDs to replace found.")
        
        # Step 5: Create the final set with replacements
        final_output = set()
        for hgnc_id in gene_query:
            if hgnc_id in id_to_symbol:
                final_output.add(id_to_symbol[hgnc_id])
            else:
                final_output.add(hgnc_id)
        logger.info(f"Gene query output: {final_output}")

        return "|".join(final_output)

    def custom_sort(self, row):
        """
        Generate a sorting key (a tuple) for a single DataFrame row representing a genomic location.

        This function takes into account that chromosome labels, start, and end coordinates might not 
        always be numeric. The goal is to return a tuple (chrom_number, start, end) that can be used to 
        sort the rows in a meaningful genomic order. 
        
        - Numeric autosomes (1-22) are sorted naturally (1 < 2 < 3 ... < 22).
        - The sex chromosomes X and Y are given numeric values after 22 (X=23, Y=24) so that they appear 
        after the autosomes in sorted order.
        - Any unknown, "Error", or "NoRecord" chromosomes are placed at the end by assigning them infinity.
        - For start and end coordinates, if they cannot be converted to integers, they are assigned infinity.
        - Rows with infinite values appear last in the final sorted list.
        
        Parameters
        ----------
        row : pd.Series
            A row from a pandas DataFrame. Expected columns include:
            - 'chrom': a string representing the chromosome (e.g., "chr1", "chrX", "NoRecord")
            - 'start': start coordinate of the interval (integer or string)
            - 'end': end coordinate of the interval (integer or string)
            
        Returns
        -------
        tuple of (int or float, int or float, int or float)
            A tuple (chrom_number, start, end), where:
            - chrom_number is an integer representing chromosome number or float('inf') if unknown/error.
            - start and end are integers for numeric coordinates or float('inf') if invalid.
        
        Notes
        -----
        Sorting is crucial when generating a BED file to ensure that entries appear in a logically 
        consistent genomic order. BED files typically start with chromosome 1 and ascend numerically 
        through chromosomes, followed by chromosomes X and Y. Non-standard or error conditions are 
        pushed to the end.
        """
        
        # Check for special cases of unknown or error chromosomes.
        if row['chrom'] in ["NoRecord", "Error"]:
            # Return a tuple of infinity values to push these records to the end of the sort order.
            return (float('inf'), float('inf'), float('inf'))
        
        # Extract the chromosome substring (e.g., "chr1" -> "1", "chrX" -> "X")
        # We assume all chromosome strings start with "chr" prefix.
        try:
            chrom_substring = row['chrom'][3:]
        except:
            # If something unexpected happens (e.g., 'chrom' not properly formatted), 
            # place this record at the end.
            return (float('inf'), float('inf'), float('inf'))
        
        # Convert the chromosome substring into a numeric value that can be sorted:
        # - If it's a digit, convert directly to int.
        # - If it's 'X', use 23.
        # - If it's 'Y', use 24.
        # - Otherwise, treat it as unknown and assign infinity.
        if chrom_substring.isdigit():
            chrom_number = int(chrom_substring)
        elif chrom_substring == 'X':
            chrom_number = 23
        elif chrom_substring == 'Y':
            chrom_number = 24
        else:
            # For other cases (e.g., 'M', or malformed), push to the end.
            chrom_number = float('inf')
        
        # Attempt to convert start and end to integers.
        # If they cannot be converted (e.g., "Error"), assign infinity.
        try:
            start = int(row['start'])
        except:
            start = float('inf')
        
        try:
            end = int(row['end'])
        except:
            end = float('inf')
        
        # Return the sorting key tuple.
        logger.info(f"sorted key: {chrom_number}, {start}, {end}")
        return (chrom_number, start, end)


    def parse_to_bed(self, gene_query, genome_build='GRCh38', transcript_set='all', limit_transcripts='mane_select'):
        """
        Fetches gene data from the API and converts it to BED file format.

        Parameters:
        - gene_query (str): Gene identifier for querying (HGNC ID, symbol, or transcript ID).
        - genome_build (str): Genome build version (e.g., 'GRCh37' or 'GRCh38'). Defaults: GRCh38
        - transcript_set (str): Transcript set to use (e.g., 'refseq', 'ensembl', 'all'). Defaults: all
        - limit_transcripts (str): Filter for specific transcript sets ('mane', 'select', 'mane_select'). Defaults: mane_select

        Returns:
        - BytesIO: BED file content ready to be sent as a response.

        Raises:
        - VarValAPIError: If fetching or processing gene data fails.
        """
        # Map user-friendly transcript options to API-compatible values
        limit_transcripts_map = {
            'mane_select + mane_plus_clinical': 'mane',
            'mane_select': 'mane_select',
            'canonical': 'select'
        }
        limit_transcripts = limit_transcripts_map.get(limit_transcripts, limit_transcripts)

        gene_query= self.get_hgnc_ids_with_replacements(gene_query)

        try:
            # Fetch gene data from the API
            gene_data = self.get_gene_data(
                gene_query=gene_query,
                genome_build=genome_build,
                transcript_set=transcript_set,
                limit_transcripts=limit_transcripts
            )
            logger.info(f"var val params: {gene_data}")
        except VarValAPIError as e:
            logger.debug(f"Error fetching data from VariantValidator API: {str(e)}")
            raise VarValAPIError(f"Error fetching data: {str(e)}")
        
        

        # Parse the gene data into BED format
        bed_rows = []
        for gene in gene_data:
            logger.info(f"Gene: {gene}")
            transcripts = gene.get('transcripts', [])
            # If no transcripts, create a NoRecord line
            if not transcripts or 'annotations' not in transcripts[0] or 'chromosome' not in transcripts[0]['annotations']:
                bed_rows.append({
                    'chrom': "NoRecord",
                    'start': "NoRecord",
                    'end': "NoRecord",
                    'name': f"{gene.get('requested_symbol')}_NoRecord",
                    'strand': "NoRecord"
                })
                continue

            try:
                chromosome = f"chr{gene['transcripts'][0]['annotations']['chromosome']}"
                for transcript in gene['transcripts']:
                        reference = transcript['reference']
                        genomic_spans = transcript['genomic_spans']
                        if len(genomic_spans) < 1:
                            raise ValueError("Missing data")
                        for _, spans in genomic_spans.items():
                            orientation = '+' if spans['orientation'] == 1 else '-'
                            for exon in spans['exon_structure']:
                                bed_rows.append({
                                    'chrom': chromosome,
                                    'start': exon['genomic_start'],
                                    'end': exon['genomic_end'],
                                    'name': f"{gene['current_symbol']}_exon{exon['exon_number']}_{reference}",
                                    'strand': orientation
                                })
            except Exception:
                logger.debug(f"{Exception} ocurred when parsing data from var val")
                bed_rows.append({
                    'chrom': "Error",
                    'start': "Error",
                    'end': "Error",
                    'name': f"{gene.get('current_symbol', gene_query)}_Error",
                    'strand': "Error"
                })

        # Convert rows into a DataFrame
        logger.info("Converting parsed data into DataFrame.")
        bed_df = pd.DataFrame(bed_rows)
        # Define a custom sorting function

        # Add sorting key
        logger.info("Sorting the DataFrame.")
        bed_df['sort_key'] = bed_df.apply(self.custom_sort, axis=1)

        # Sort DataFrame based on the key
        bed_df = bed_df.sort_values('sort_key').drop(columns=['sort_key'])

        # Reset index after sorting
        bed_df.reset_index(drop=True, inplace=True)

        # Write the DataFrame to a BED file (BytesIO)
        logger.info("Writing the DataFrame to BED file format.")
        output = BytesIO()
        bed_string = bed_df.to_csv(
            sep='\t',
            index=False,
            header=False,
            columns=['chrom', 'start', 'end', 'name', 'strand']
        )
        output.write(bed_string.encode('utf-8'))
        output.seek(0)
        logger.info("BED file generation completed successfully.")
        return output