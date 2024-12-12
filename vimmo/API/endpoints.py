from flask import send_file
from flask_restx import Resource
from vimmo.API import api,get_db
from vimmo.utils.panelapp import  PanelAppClient
from vimmo.utils.variantvalidator import VarValClient, VarValAPIError
from vimmo.utils.parser import IDParser, PatientParser, DownloadParser, UpdateParser, LocalDownloadParser

from vimmo.utils.arg_validator import validate_panel_id_or_Rcode_or_hgnc
from vimmo.db.db import Query
from vimmo.utils.localbed import local_bed_formatter




panel_app_client = PanelAppClient()

# Create a namespace for panel-related endpoints
panels_space = api.namespace('panels', description='Return panel data provided by the user')

# Create a parser for handling request arguments
id_parser = IDParser.create_parser()

# Define the Panel Search endpoint
@panels_space.route('/')
class PanelSearch(Resource):
    # Document the API using the argument parser
    @api.doc(parser=id_parser)
    def get(self):
        # Parse arguments from the request
        args = id_parser.parse_args()

        # Normalize the Rcode to uppercase if it exists
        if args.get("Rcode"):
            args["Rcode"] = args["Rcode"].upper()  # Convert lowercase 'r' to uppercase 'R'

        # Apply custom validation for the parsed arguments
        try:
            validate_panel_id_or_Rcode_or_hgnc(args,panel_space=True)  # Ensure only one valid parameter is provided
        except ValueError as e:
            # Return an error response if validation fails
            return {"error": str(e)}, 400

        # Retrieve the database connection
        db = get_db()
        # Initialize a query object with the database connection
        query = Query(db.conn)

        # Handle requests based on the provided argument
        if args.get("Panel_ID"):
            # Fetch panel data by Panel_ID with optional similar matches
            panel_data = query.get_panel_data(panel_id=args.get("Panel_ID"), matches=args.get("Similar_Matches"))
            return panel_data

        elif args.get("Rcode"):
            # Fetch panel data by Rcode with optional similar matches
            panel_data = query.get_panels_by_rcode(rcode=args.get("Rcode"), matches=args.get("Similar_Matches"))
            return panel_data

        elif args.get("HGNC_ID"):
            # Fetch panels associated with a specific HGNC_ID with optional similar matches
            panels_returned = query.get_panels_from_gene(hgnc_id=args.get("HGNC_ID"), matches=args.get("Similar_Matches"))
            return panels_returned
            # If no valid parameter is provided, return an error response

        return {"error": "No valid Panel_ID, Rcode, or HGNC_ID provided."}, 400






download_parser=DownloadParser.create_parser()
@panels_space.route('/download')
class PanelDownload(Resource):
    @api.doc(parser=download_parser)
    def get(self):
        """
        Endpoint to download panel data as a BED file.

        Query Parameters:
        - HGNC_ID (str): Gene identifier for querying (e.g., HGNC ID or symbol).
        - genome_build (str): Genome build version (default: 'GRCh38').
        - transcript_set (str): Transcript set to use (e.g., 'refseq', 'ensembl', 'all'; default: 'all').
        - limit_transcripts (str): Specifies transcript filtering ('mane', 'select', 'all'; default: 'all').

        Returns:
        - FileResponse: A downloadable BED file containing gene data.
        """
        # Parse user-provided arguments from the request
        args = download_parser.parse_args()

        # # Apply custom validation
        try:
            validate_panel_id_or_Rcode_or_hgnc(args, bed_space=True)
        except ValueError as e:
            return {"error": str(e)}, 400

        panel_id=args.get("Panel_ID",None)
        r_code=args.get("Rcode",None)
        matches=args.get("Similar_Matches",None)
        HGNC_ID=args.get("HGNC_ID",None)


        # Retrieve the database connection
        db = get_db()
        # Initialize a query object with the database connection
        query = Query(db.conn)

        if panel_id:
            panel_data = query.get_panel_data(panel_id=args.get("Panel_ID"), matches=args.get("Similar_Matches"))
            if "Message" in panel_data:
                return panel_data
            gene_query={record["HGNC_ID"] for record in panel_data["Associated Gene Records"]}
            gene_query="|".join(gene_query)
        elif r_code:
            panel_data = query.get_panels_by_rcode(rcode=args.get("Rcode"), matches=args.get("Similar_Matches"))
            if "Message" in panel_data:
                return panel_data
            gene_query={record["HGNC_ID"] for record in panel_data["Associated Gene Records"]}
            gene_query="|".join(gene_query)
        query = Query(db.conn)
        
        if not HGNC_ID:
            gene_query=query.get_gene_list(panel_id,r_code,matches)
            # Check if gene_query is a set of HGNC IDs
            if isinstance(gene_query, dict) and "Message" in gene_query:
                return gene_query, 400
        else:
            gene_query=HGNC_ID
            

        genome_build = args.get('genome_build', 'GRCh38')
        transcript_set = args.get('transcript_set', 'all')
        limit_transcripts = args.get('limit_transcripts', 'mane_select')
        

        # Initialize the VariantValidator client
        var_val_client = VarValClient()

        try:
            # Generate the BED file content
            bed_file = var_val_client.parse_to_bed(
                gene_query=gene_query,
                genome_build=genome_build,
                transcript_set=transcript_set,
                limit_transcripts=limit_transcripts
            )
        except VarValAPIError as e:
            # Return an error response if processing fails
            return {"error": str(e)}, 500


        # Generate a meaningful filename for the download
        if panel_id:
            filename = f"{panel_id}_{genome_build}_{limit_transcripts}.bed"
        elif r_code:
            filename = f"{r_code}_{genome_build}_{limit_transcripts}.bed"
        else:
            filename = f"Genes_{genome_build}_{limit_transcripts}.bed"

        # Return the BED file as a downloadable response
        return send_file(
            bed_file,
            mimetype='text/plain',
            as_attachment=True,
            download_name=filename
        )

        
        db.close()
        
         # Return the BED file as a downloadable response
        if bed_file:
            # Return the BED file using send_file
            return send_file(
                bed_file,
                mimetype='text/plain',
                as_attachment=True,
                download_name=filename
            )
        else:
            return {"error": "No BED data could be generated from the provided gene query."}, 400


       






local_download_parser=LocalDownloadParser.create_parser()
@panels_space.route('/download/local')
class LocalPanelDownload(Resource):
    @api.doc(parser=local_download_parser)
    def get(self):
        """
        Endpoint to download panel data as a BED file.

        Query Parameters:
        - HGNC_ID (str): Gene identifier for querying (e.g., HGNC ID or symbol).
        - genome_build (str): Genome build version (default: 'GRCh38').
        - transcript_set (str): Transcript set to use (e.g., 'refseq', 'ensembl', 'all'; default: 'all').
        - limit_transcripts (str): Specifies transcript filtering ('mane', 'select', 'all'; default: 'all').

        Returns:
        - FileResponse: A downloadable BED file containing gene data.
        """
        # Parse user-provided arguments from the request
        args = local_download_parser.parse_args()


        # # Apply custom validation
        try:
            validate_panel_id_or_Rcode_or_hgnc(args, bed_space=True)
        except ValueError as e:
            return {"error": str(e)}, 400

        panel_id=args.get("Panel_ID",None)
        r_code=args.get("Rcode",None)
        matches=args.get("Similar_Matches",None)
        HGNC_ID=args.get("HGNC_ID",None)


        # Retrieve the database connection
        db = get_db()
        # Initialize a query object with the database connection
        query = Query(db.conn)
        if not HGNC_ID:
            gene_query=query.get_gene_list(panel_id,r_code,matches)
            # Check if gene_query is a set of HGNC IDs
            if isinstance(gene_query, dict) and "Message" in gene_query:
                return gene_query, 400
        else:
            gene_query=HGNC_ID
        
        genome_build = args.get('genome_build', 'GRCh38')
        local_bed_records=query.local_bed(gene_query,genome_build)
        bed_file=local_bed_formatter(local_bed_records)



        # Generate a meaningful filename for the download
        if panel_id:
            filename = f"{panel_id}_{genome_build}_Gencode.bed"
        elif r_code:
            filename = f"{r_code}_{genome_build}_Gencode.bed"
        else:
            filename = f"Genes_{genome_build}_Gencode.bed"

        db.close()

        if bed_file:
            return send_file(
                bed_file,
                mimetype='text/plain',
                as_attachment=True,
                download_name=filename
            )
        else:
            return {"error": "No BED data could be generated from the provided gene query."}, 400



    


patient_space = api.namespace('patient', description='Return a patient panel provided by the user')
patient_parser = PatientParser.create_parser()
@patient_space.route("/patient")
class PatientClass(Resource):
    @api.doc(parser=patient_parser)
    def get(self):
                # Collect Arguements
        args = patient_parser.parse_args()
        # Fetch the database and connect
        db = get_db()
        
        query = Query(db.conn)
        #Return all records for a patient
        if args["R code"] == None: # No Rcode input = show all Tests/version for a given patient ID workflow

            patient_records = query.return_all_records(args["Patient ID"])
   
            return {"Patient ID": args["Patient ID"], "patient records":patient_records}
        #Panel comparison if possible
        else:
            # Version comparison workflow
            # Check database version is up to date
            panel_id = query.rcode_to_panelID(args["R code"]) # Convert the rcode into the panel id
              
            lastest_online_version = panel_app_client.get_latest_online_version(panel_id) # Retrive the latest online panel version

            if lastest_online_version == None: # If online version can't be accessed/return no data
                # complete comparison using database not updated with disclaimer
                disclaimer = 'The latest version of panel app was unable to be contacted, results are on valid from (lastupdate date)'
            
            elif query.get_db_latest_version(args["R code"]) != lastest_online_version: # If our local version NOT same as panel app latest, then update database and continue
            # Update db prior to comparison
            
                return f'update the db! goes here!' 

            else: 
                disclaimer = 'Panel comparison up to date'# If our db is up-to-date, continue with panel comparison, without updating or a disclaimer in response
            
            patient_history = query.check_patient_history(args["Patient ID"], args["R code"]) # Returns version of most recent panel used on patient for a given Rcode
            database_version = query.get_db_latest_version(args["R code"])
            # Is the patient in the table
            if patient_history == None: # Checks if the response is empty ie - the patient_id isn't in the table
                return f"There is no record of patient {args["Patient ID"]} recieving {args["R code"]} within our records" # Return explanatory message
            # Is the last patient version different to the current version?
            elif patient_history == database_version: # The database version is the same as the historic version return the gene contents 

                current_panel_data = query.current_panel_contents(panel_id)
                return {"disclaimer": disclaimer,"status": f"No version change since last {args["Patient ID"]} had {args['R code']}", "Version":f"{database_version}","Panel content":{current_panel_data}}
                 
            else: #  If patient_ID in table with outdated version, find the difference between their most recent historical panel version & the current panel version contents
                # Comparison function
                historic_panel_data = query.historic_panel_retrieval(panel_id,patient_history)
                current_panel_data = query.current_panel_contents(panel_id)
                version_comparison = query.compare_panel_versions(historic_panel_data,current_panel_data)

                return {"disclaimer": disclaimer,"status": f"Version changed since last {args["Patient ID"]} had {args['R code']}", "Version":f"{database_version}", "Genes added": version_comparison[0], "Genes removed": version_comparison[1], "Confidence changes (old ver -> new ver)": version_comparison[2]}
        
            
update_space = api.namespace('UpdatePatientRecords', description='Update the Vimmo database with a patients test history')
update_parser = UpdateParser.create_parser()
@update_space.route("/update")
class UpdateClass(Resource):
    @api.doc(parser=update_parser)
    def get(self):
        args = update_parser.parse_args()
        
        ### Update functionality here ###
        return f"{args}"
        

    
