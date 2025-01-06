from vimmo.logger.logging_config import logger
import sys

try:
    from flask import send_file
    from flask_restx import Resource
    from vimmo.API import api,get_db
<<<<<<< HEAD
    from vimmo.API.endpoint_process_func import bed_processor

=======
    from vimmo.utils.endpoint_process_func import bed_processor
>>>>>>> dev
    from vimmo.db.db_query import Query
    from vimmo.db.db_update import Update
    from vimmo.db.db_downgrade import Downgrade
    from vimmo.utils.panelapp import  PanelAppClient
    from vimmo.utils.variantvalidator import VarValClient, VarValAPIError
    from vimmo.utils.localbed import local_bed_formatter
    from vimmo.utils.arg_validator import validate_panel_id_or_Rcode_or_hgnc, hgnc_to_list, patient_update_validator
    from vimmo.utils.parser import (
        IDParser, 
        PatientParser,
        PatientBedParser,
        DownloadParser, 
        UpdateParser, 
        LocalDownloadParser,
        PatientLocalBedParser,
        DowngradeParser
    )
    
    logger.info("Import Success")
except Exception as err:
    logger.critical(f"Importing Modules failed, please check {err}")
    sys.exit(1)










# Create a namespace for panel-related endpoints
panels_space = api.namespace('panels', description='Return panel data provided by the user')

# Create a parser for handling request arguments
id_parser = IDParser.create_parser()

# Define the Panel Search endpoint
@panels_space.route('')
class PanelSearch(Resource):
    # Document the API using the argument parser
    @api.doc(parser=id_parser)
    def get(self):
        # Parse arguments from the request
        args = id_parser.parse_args()

        if args.get("HGNC_ID"):
            args=hgnc_to_list(args=args)



        # Normalize the Rcode to uppercase if it exists
        if args.get("Rcode"):
            args["Rcode"] = args["Rcode"].upper()  # Convert lowercase 'r' to uppercase 'R'


        # Apply custom validation for the parsed arguments
        try:
            validate_panel_id_or_Rcode_or_hgnc(args,panel_space=True)  # Ensure only one valid parameter is provided
        except ValueError as e:
            logger.debug(f"Validation for argumemts failed for Panel_id: {args.get("Panel_ID")}, rcode: {args.get("Rcode")}, HGNC_ID: {args.get("HGNC_ID")} with {e}")
            # Return an error response if validation fails
            return {"error": str(e)}, 400

        # Retrieve the database connection
        db = get_db()
        # Initialize a query object with the database connection
        query = Query(db.conn)
        logger.info("DB connection made from panel endpoint")
        

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
            # Fetch panels associated with a specific HGNC_ID with optional similar matches or a using a list
            panels_returned = query.get_panels_from_gene_list(hgnc_ids=args.get("HGNC_ID"), matches=args.get("Similar_Matches"))
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

        if args.get("HGNC_ID", None):
            args=hgnc_to_list(args=args)

        # # Apply custom validation
        try:
            validate_panel_id_or_Rcode_or_hgnc(args, bed_space=True)
        except ValueError as e:
            logger.error(f"error: {str(e)}")
            return {"error": str(e)}, 400

        panel_id=args.get("Panel_ID",None)
        r_code=args.get("Rcode",None)
        matches=args.get("Similar_Matches",None)
        HGNC_ID=args.get("HGNC_ID",None)


        # Retrieve the database connection
        db = get_db()
        # Initialize a query object with the database connection
        query = Query(db.conn)
        logger.info("DB connection made from download endpoint")
        
        if not args["HGNC_ID"]:
            if panel_id:
                panel_data = query.get_panel_data(panel_id=args.get("Panel_ID"), matches=args.get("Similar_Matches"))
                if "Message" in panel_data:
                    logger.info(f"Panel_data: {panel_data}")
                    return panel_data
                gene_query={record["HGNC_ID"] for record in panel_data["Associated Gene Records"]}
            elif r_code:
                panel_data = query.get_panels_by_rcode(rcode=args.get("Rcode"), matches=args.get("Similar_Matches"))
                if "Message" in panel_data:
                    logger.info(f"Panel_data: {panel_data}")
                    return panel_data
                gene_query={record["HGNC_ID"] for record in panel_data["Associated Gene Records"]}

            gene_query=query.get_gene_list(panel_id,r_code,matches)
            # Check if gene_query is a set of HGNC IDs
            if isinstance(gene_query, dict) and "Message" in gene_query:
                return gene_query, 400
        else:
            gene_query=args["HGNC_ID"]
        

            
            
        genome_build = args.get('genome_build', 'GRCh38')
        transcript_set = args.get('transcript_set', 'all')
        limit_transcripts = args.get('limit_transcripts', 'mane_select')
        

        # Initialize the VariantValidator client
        var_val_client = VarValClient()

        try:
            # Generate the BED file content
            logger.info(f"var_val_client.parse_to_bed(gene_query={gene_query},genome_build={genome_build},transcript_set={transcript_set},limit_transcripts={limit_transcripts})")
            bed_file = var_val_client.parse_to_bed(
                gene_query=gene_query,
                genome_build=genome_build,
                transcript_set=transcript_set,
                limit_transcripts=limit_transcripts
            )
        except VarValAPIError as e:
            # Return an error response if processing fails
            logger.error(f"error: {str(e)}")
            return {"error": str(e)}, 500


        # Generate a meaningful filename for the download
        if panel_id:
            filename = f"{panel_id}_{genome_build}_{limit_transcripts}.bed"
        elif r_code:
            filename = f"{r_code}_{genome_build}_{limit_transcripts}.bed"
        else:
            filename = f"Genes_{genome_build}_{limit_transcripts}.bed"

        
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
            logger.info("error, No BED data could be generated from the provided gene query.")
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

        if args.get("HGNC_ID", None):
            args=hgnc_to_list(args=args)

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
        logger.info("DB connection made from local bed endpoint")

        if not HGNC_ID:
            gene_query=query.get_gene_list(panel_id,r_code,matches)
            # Check if gene_query is a set of HGNC IDs
            if isinstance(gene_query, dict) and "Message" in gene_query:
                return gene_query, 400
        else:
            gene_query=HGNC_ID
        
        genome_build = args.get('genome_build', 'GRCh38')
        local_bed_records=query.local_bed(gene_query,genome_build)
        logger.debug(f"query.local_bed({gene_query},{genome_build})")
        bed_file=local_bed_formatter(local_bed_records)
        logger.debug(f"local_bed_formatter({local_bed_records})")
        



        # Generate a meaningful filename for the download
        if panel_id:
            filename = f"{panel_id}_{genome_build}_Gencode.bed"
        elif r_code:
            filename = f"{r_code}_{genome_build}_Gencode.bed"
        else:
            filename = f"Genes_{genome_build}_Gencode.bed"

        if bed_file:
            return send_file(
                bed_file,
                mimetype='text/plain',
                as_attachment=True,
                download_name=filename
            )
        else:
            logger.debug("Bed was not generated please enable Debug if needed")

            return {"error": "No BED data could be generated from the provided gene query."}, 400






patient_space = api.namespace('patient', description='Return a patient panel provided by the user')
patient_parser = PatientParser.create_parser()
@patient_space.route("")
class PatientResource(Resource):
    @api.doc(parser=patient_parser)
    def get(self):
        """
        Endpoint to handle GET requests to the patient namespace.
         
        Parameters
        ----------
        - patient_id : str
          Numerical identifier for a patient
        - rcode: str 
          Panel app code for a rare disease gene panel

        Notes
        -----
        - For detailed explanation - see documentation and flow chart ('Feature 2 decision tree')
        - If ONLY an rcode is given, all patient records with that rcode are returned
        - If ONLY a patient_id is given, all test records are returned for that patient
        - if BOTH rcode & patient_id are given & the panel version has changed since patient X's last test
          , a panel comparison will be returned 
        Example
        -----
        Please see user manual for example usage
         """
        args = patient_parser.parse_args()  # Collect Arguements
        try:
            patient_update_validator(args)  # Validate Rcode & patient ID
            logger.info("Patient space recieved valid input")
        except ValueError as e:
            # Return an error response if validation fails
            logger.error(f"Value Error raised by input args {str(e)}")
            return {"error": str(e)}, 400
         
        db = get_db()  # Fetch the database and connect
        logger.info("DB connection made from patient endpoint")

        query = Query(db.conn)
        update = Update(db.conn)
        
        # Return all records for a patient
        if args["R code"] is None:
        # No Rcode input: Show all tests/versions for a given patient ID.
            patient_records = query.return_all_records(args["Patient ID"])          
            logger.info(f"No input Rcode - Returning all records for patient {args["Patient ID"]}")
            return {"Patient ID": args["Patient ID"],
                    "patient records": patient_records}
        
        # Return all patients for an R code
        elif args["Patient ID"] is None:
            # No Patient input: Return all patients who have had a given R code.
            patients_list = query.return_all_patients(args["R code"])           
            logger.info(f"No input Patient ID - Returning all records for Rcode {args['R code']}")
            return {"R code": args["R code"],
                    "Records": patients_list}
            
        else:
            logger.info(f"Both Patient ID: {args["Patient ID"]} & Rcode: {args["R code"]} provided")
            # Version comparison workflow
            # Check database version is up to date.
            panel_id = query.rcode_to_panelID(args["R code"])  # Convert R code to panel ID.
            database_version = query.get_db_latest_version(args["R code"])
            try:
                panel_app_client = PanelAppClient()
                latest_online_version = panel_app_client.get_latest_online_version(panel_id)
                logger.debug(f"Latest online version retreived: {latest_online_version}")
            except:
                # If any error occurs, set latest_online_version to None and create the disclaimer
                logger.info("Database not updated during query")
                latest_online_version = None
                disclaimer = (
                    "The latest version of PanelApp was unable to be contacted. "
                    "Results are valid as of the last update date."
                )
            else:
                if database_version != latest_online_version:
                    logger.info("Differerence between Vimmo db and latest online panel version")
                    try: # If our local version NOT same as panel app latest, then update database and continue
                    #  Update the database to match the latest online version.
                        update.update_panels_version(args["R code"], latest_online_version, panel_id)
                        logger.info("panel version updated successfully")

                        update.archive_panel_contents(panel_id, database_version)
                        logger.info(f"{args["R code"]} v{database_version} archived successfully")

                        update.update_gene_contents(args["R code"],panel_id)
                        logger.info(f"{args['Patient ID']} v{latest_online_version} inserted successfully")
                        disclaimer = 'Panel comparison up to date'
                        logger.info(f"UPDATE database - {args['R code']}  {database_version} --> {latest_online_version}")
                        database_version = query.get_db_latest_version(args["R code"])  # get newly updated database version
                    except:
                        logger.warning("Database could not be updated")
                        disclaimer=f'Database update failed - using most recent db version ({database_version}) for panel comparison ' 
                else: 
                # Database is up-to-date; no updates/disclaimers needed.
                    disclaimer = 'Panel comparison up to date'
            
            
            # At this point the database should be current and  necessary disclaimers inplace
           
            patient_history = query.check_patient_history(args["Patient ID"], args["R code"])  # Returns most recent panel version from db           
            # Check if the patient is in the table
            if patient_history is None:  # Check if patient isn't in db with record of input R code
                patient_records = query.return_all_records(args["Patient ID"])
                if patient_records:  # if any record of patient exists - print records
                    logger.info(f"No record of patient {args['Patient ID']} having {args["R code"]}")
                    return {"Status": f"There is NO record of patient {args['Patient ID']} recieving {args['R code']} within our records", "Patient records": patient_records} # Re
                else: # If no record esists
                    logger.info(f"No records of patient {args['Patient ID']}")
                    return {"Status":f"There is NO record of patient {args['Patient ID']} recieving any R code within our records"} # Return explanatory message
            
            # Check if the last patient version is different to the current version
            elif patient_history == database_version: # The database version is the same as the historic version return the gene contents 
                logger.info(f"No change in panel version detected for patient: {args["Patient ID"]} rcode: {args['R code']}")
                logger.debug(f"patient history : {patient_history}, database version: {database_version}")
                current_panel_data = query.current_panel_contents(panel_id)                                 # Retreieve current panel contents
                return {"disclaimer": disclaimer,"status": f"No version change since patient: {args["Patient ID"]} last had {args['R code']}", 
                        "Version":f"{database_version}", "current_panel": current_panel_data ,"Tip": f"For more information on {args["R code"]} v{database_version}, please use the panels space."}

                 
            else: #  If patient_ID in archive table with outdated version, find the difference between most recent archived panel version & the current panel version contents
                # Comparison function
                historic_panel_data = query.historic_panel_retrieval(panel_id,patient_history)              # Retrieve archived version contents
                current_panel_data = query.current_panel_contents(panel_id)                                 # Retreieve current panel contents
                version_comparison = query.compare_panel_versions(historic_panel_data,current_panel_data)   # Compare 
                logger.info("Panel comparison successfully returned")
                return {"disclaimer": disclaimer,"status": f"Version changed since last {args["Patient ID"]} had {args['R code']}", 
                        "Version":f"{database_version}", 
                        "Genes added": version_comparison[0], 
                        "Genes removed": version_comparison[1], 
                        "Confidence changes (old ver -> new ver)": version_comparison[2]}
            



patient_bed = PatientBedParser.create_parser()
@patient_space.route("/bed")
class PatientBed(Resource):
    @api.doc(parser=patient_bed)
    def get(self):
        args = patient_bed.parse_args()
        patient_id=args.get("Patient ID",None)
        r_code=args.get("R code",None)
        version=args.get("version",None)
        genome_build = args.get('genome_build', 'GRCh38')
        transcript_set = args.get('transcript_set', 'all')
        limit_transcripts = args.get('limit_transcripts', 'mane_select')
        # Fetch the database and connect
        db = get_db()
        logger.info("DBconnection made from patient bed endpoint")
    
        query = Query(db.conn)  
        processed_info=bed_processor(query,patient_id,r_code,version,args,logger)
        if processed_info["type"] == "gene_query":
            # Perform additional processing on response["data"]
            gene_query = processed_info["data"]
        else:
            # Return message directly to API
            return processed_info["data"]

        

        # Initialize the VariantValidator client
        var_val_client = VarValClient()

        try:
            # Generate the BED file content
            logger.info(f"var_val_client.parse_to_bed(gene_query={gene_query},genome_build={genome_build},transcript_set={transcript_set},limit_transcripts={limit_transcripts})")
        
            bed_file = var_val_client.parse_to_bed(
                gene_query=gene_query,
                genome_build=genome_build,
                transcript_set=transcript_set,
                limit_transcripts=limit_transcripts
            )
        except VarValAPIError as e:
            logger.error(f"Varval returned an error {str(e)}")
            # Return an error response if processing fails
            return {"error": str(e)}, 500


        # Generate a meaningful filename for the download
        filename = f"{patient_id}_{r_code}_{genome_build}_{limit_transcripts}.bed"


        
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
            logger.debug("Bed was not generated please enable Debug")
            return {"error": "No BED data could be generated from the provided gene query.",
                    "Tip": "Please use local bed endpoint to download records"}, 400



patient_local_bed = PatientLocalBedParser.create_parser()
@patient_space.route("/local_bed")
class PatientLocalBed(Resource):
    @api.doc(parser=patient_local_bed)
    def get(self):
        args = patient_local_bed.parse_args()
        patient_id=args.get("Patient ID",None)
        r_code=args.get("R code",None)
        version=args.get("version",None)
        genome_build = args.get('genome_build', 'GRCh38')
        # Fetch the database and connect
        db = get_db()
        logger.info("DB connection made from patient local bed endpoint")
        
        query = Query(db.conn) 
        processed_info=bed_processor(query,patient_id,r_code,version,args,logger)
        if processed_info["type"] == "gene_query":
            # Perform additional processing on response["data"]
            gene_query = processed_info["data"]
        else:
            # Return message directly to API
            return processed_info["data"]
    
        local_bed_records=query.local_bed(gene_query,genome_build)
        bed_file=local_bed_formatter(local_bed_records)

        filename = f"{patient_id}_{r_code}_{genome_build}_Gencode.bed"

        db.close()

        if bed_file:
            return send_file(
                bed_file,
                mimetype='text/plain',
                as_attachment=True,
                download_name=filename
            )
        else:
            logger.debug(f"Failed local BED for patient {patient_id}. DB returned: {local_bed_records}")
            return {"error": "No BED data could be generated from the provided gene query."}, 400


                
    
update_space = api.namespace('UpdatePatientRecords', description='Update the Vimmo database with a patients test history')
update_parser = UpdateParser.create_parser()
@update_space.route("")
class UpdateClass(Resource):
    @api.doc(parser=update_parser)
    
    def get(self):
        """
        Endpoint to handle GET requests to the update namespace.
         
        Parameters
        ----------
        - patient_id : str 
          Numerical identifier for a patient
        - rcode: str 
          Panel app code for a rare disease gene panel

        Notes
        -----
        - For detailed explanation - see documentation and flow chart ('Feature 2 decision tree')
        - If ONLY an rcode is given, all patient records with that rcode are returned
        - If ONLY a patient_id is given, all test records are returned for that patient
        - if BOTH rcode & patient_id are given & the panel version has changed since patient X's last test
          , a panel comparison will be returned 
        Example
        -----
        User input rcode: R208
        get(R208) -> {
        "R code": "R208",
        "Records": {
            "2023-12-30": [
            123,
            2.1
            ],
        }
        """
        args = update_parser.parse_args()
        try: 
            patient_update_validator(args)
            logger.info(f"Valid arguments given to update space: Patient ID = {args["Patient ID"]}, Rcode = {args['R code']}")
        except ValueError as e:
            logger.error(f"Value error raised by arg parser: {e}")
            return {"error": str(e)}, 400

        db = get_db()
        logger.info("DB connection made from patient update endpoint")

        update = Update(db.conn) # Instantiate an Update class object
        query = Query(db.conn)   # Instantiate an Query  class object
        panel_app_client = PanelAppClient()
        # Check the database is up to date before updating the db with the now current current verison
        panel_id = query.rcode_to_panelID(args["R code"])  # Convert the rcode into the panel id
        database_version = query.get_db_latest_version(args["R code"])
        latest_online_version = panel_app_client.get_latest_online_version(panel_id)
 
        
        if database_version != latest_online_version:
                # Update version and panel contents (panel and panel_contents tables)
            
            try:
                logger.info(f"Attempting to update database: Rcode: {args["R code"]} {database_version} --> {latest_online_version}")
                # Update the panel version in 'panels' table
                update.update_panels_version(args["R code"], latest_online_version, panel_id)
                logger.info("panel version updated successfully")
                # Archive the old panel verison to 'archive_panel_genes'
                update.archive_panel_contents(panel_id, database_version)
                logger.info(f"{args["R code"]} v{database_version} archived successfully")         
                # Update the version in the 'panel_genes' table
                update.update_gene_contents(args["R code"],panel_id)
                logger.info(f"{args['Patient ID']} v{latest_online_version} inserted successfully")
                logger.info(f"UPDATE database success - {args['R code']}  {database_version} --> {latest_online_version}")
                database_version = query.get_db_latest_version(args["R code"])  # Retrieve newly updated db panel version

            except KeyError: 
                logger.error("Database could not be updated")
                return "The database could not be updated at this point"
            
        else:
            pass
        
        is_present = update.check_presence(args["Patient ID"], args["R code"])  # Check presence pre-existing record with patient ID, R code and Version
        if is_present is False:
            updated_record = update.add_record(args["Patient ID"], args["R code"])  # If propsed patient record isn't in db, add record
            logger.info(f"Patient record added: {args['Patient ID']} {args["R code"]} v{database_version}")
            return updated_record
        else:
            logger.warning(f"Entry not made in db, patient: {args['Patient ID']} already present in db with current version")
            return {"Status": f"Patient {args["Patient ID"]} already has a record of {args["R code"]} version {is_present}"}

               









  
downgrade_space = api.namespace('DowngradeRecords', description='Downgrade the Vimmo database with a panel and version from panel app')
downgrade_parser = DowngradeParser.create_parser()
@downgrade_space.route("")
class DowngradeClass(Resource):
    @api.doc(parser=downgrade_parser)
    
    def get(self):
        args = downgrade_parser.parse_args()
        rcode=args.get("R_Code")
        version=args.get("version")

        db = get_db()
        downgrade = Downgrade(db.conn) # Instantiate an Update class object
        query = Query(db.conn)   # Instantiate an Query  class object
        panel_app_client = PanelAppClient()

        database_version = query.get_db_latest_version(rcode)
        if str(database_version) == version:
            return {
                    "message": "Requested version matches current database version",
                    "current_version": database_version
                }, 200
        else:
            panel_id=query.rcode_to_panelID(rcode)
            if not panel_id:
                return {"error": "Panel ID could not be identified for {rcode}"}

                        # Get records from PanelApp
            try:
                panel_records = panel_app_client.dowgrade_records(panel_id=panel_id, version=version)
                if not panel_records:
                    return {"error": f"No records found for panel {panel_id} version {version}"}

                                # Process and downgrade records
                result = downgrade.process_downgrade(
                    rcode=rcode,
                    panel_id=panel_id,
                    version=version,
                    panel_records=panel_records
                )

            except:
                pass

        return result

        
       