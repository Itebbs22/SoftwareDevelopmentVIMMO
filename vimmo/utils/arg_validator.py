from vimmo.logger.logging_config import logger


import re


def validate_hgnc_ids(hgnc_id_value):
    """
    Validates one or multiple HGNC_IDs provided as a comma-separated string.

    Parameters
    ----------
    hgnc_ids_str : str
        A string containing one or more HGNC IDs, e.g. "HGNC:12345" or "HGNC:12345,HGNC:67890".

    Returns
    -------
    list of str
        A list of valid HGNC IDs.

    Raises
    ------
    ValueError
        If any HGNC_ID does not match the required format.
    """
    # Pattern for HGNC_ID: Matches strings like 'HGNC:12345'
    hgnc_pattern = r"^HGNC:\d+$"


    # Validate each HGNC ID against the pattern
    for hgnc_id in hgnc_id_value:
        # print(hgnc_id)
        if not re.fullmatch(hgnc_pattern, hgnc_id):
            logger.error(f"Invalid format for 'HGNC_ID': '{hgnc_id}' must start with 'HGNC:' followed by digits only.")
            raise ValueError(
                f"Invalid format for 'HGNC_ID': '{hgnc_id}' must start with 'HGNC:' followed by digits only (e.g., 'HGNC:12345')."
            )
        else:
            logger.info(f"Validated HGNC_ID: {hgnc_id}")
            continue


def panel_space_validator(panel_id_value, rcode_value, hgnc_id_value):
    """
    Validates identifiers specifically for the panel space.

    Args:
        panel_id_value (str): Value of the Panel_ID (should be numeric).
        rcode_value (str): Value of the Rcode (should start with 'r' or 'R' followed by digits).
        hgnc_id_value (str): Value of the HGNC_ID (should start with 'HGNC:' followed by digits).

    Raises:
        ValueError: If any provided value does not match the expected format.

    Notes:
        - `Rcode` must match the pattern 'r\\d+' or 'R\\d+' (e.g., 'R123').
        - `HGNC_ID` must match the pattern 'HGNC:d+' (e.g., 'HGNC:12345').
        - `Panel_ID` must be numeric.
    """
    # Pattern for Rcode: Matches strings like 'r123' or 'R123'
    rcode_pattern = r"^[rR]\d+$"

    # Validate Panel_ID: Must be numeric
    if panel_id_value:
        try:
            int(panel_id_value)  # Convert to integer to check numeric format
            logger.info(f"Valid Panel_ID: {panel_id_value}")
        except ValueError:
            logger.error("Invalid input: 'Panel_ID' must be digits only.")
            raise ValueError("Invalid input: 'Panel_ID' must be digits only (e.g., '123').")

    # Validate Rcode: Must match 'R123' or 'r123'
    if rcode_value:
        if not re.fullmatch(rcode_pattern, rcode_value):
            logger.error("Invalid format for 'Rcode': Must start with 'R' followed by digits only")
            raise ValueError("Invalid format for 'Rcode': Must start with 'R' followed by digits only (e.g., 'R123').")

    # Validate HGNC_ID: Must match 'HGNC:12345'
    if hgnc_id_value:
        logger.info("Validating HGNC_ID")
        # We'll validate all HGNC IDs at once
        # If this fails, it will raise ValueError
        validate_hgnc_ids(hgnc_id_value)
        logger.info(f"Validation for HGNC_ID: {hgnc_id_value} successful")

def bed_space_validator(panel_id_value, rcode_value, hgnc_id_value):
    """
        Validates identifiers specifically for the bed space.

        Args:
            panel_id_value (str): Value of the Panel_ID (should be numeric).
            rcode_value (str): Value of the Rcode (should start with 'R' followed by digits).
            hgnc_id_value (str): Value of the HGNC_ID (should start with 'HGNC:' followed by digits).

        Raises:
            ValueError: If any provided value does not match the expected format.

        Notes:
            - `Rcode` must match the pattern 'R\\d+' (e.g., 'R123').
            - `HGNC_ID` must match the pattern 'HGNC:\\d+' (e.g., 'HGNC:12345').
            - `Panel_ID` must be numeric.
    """
    # Pattern for Rcode: Matches strings like 'R123'
    rcode_pattern = r"^R\d+$"
    # Pattern for Panel_ID: Matches numeric strings (e.g., '1234')
    panel_pattern = r"^\d+$"
    # Pattern for HGNC_ID: Matches strings like 'HGNC:12345'
    hgnc_pattern = r"^HGNC:\d+$"

    # Validate Panel_ID: Must be numeric
    if panel_id_value:
        if not re.fullmatch(panel_pattern, str(panel_id_value)):
            logger.error("Invalid format for 'Panel_ID': Must be a number.")
            raise ValueError("Invalid format for 'Panel_ID': Must be a number (e.g., '1234').")

    # Validate Rcode: Must match 'R123'
    if rcode_value:
        if not re.fullmatch(rcode_pattern, rcode_value):
            logger.error("Invalid format for 'Rcode': Must start with 'R' followed by digits only")
            raise ValueError("Invalid format for 'Rcode': Must start with 'R' followed by digits only (e.g., 'R123').")

    # Validate HGNC_ID: Must match 'HGNC:12345'
    if hgnc_id_value:
        validate_hgnc_ids(hgnc_id_value)


def validate_panel_id_or_Rcode_or_hgnc(args, panel_space=False, bed_space=False):
    """
    High-level validation function for identifiers.

    Ensures only one identifier (Panel_ID, Rcode, or HGNC_ID) is provided and validates it based on context.

    Args:
        args (dict): Dictionary containing `Panel_ID`, `Rcode`, and `HGNC_ID`.
        panel_space (bool): If True, validate using `panel_space_validator`.
        bed_space (bool): If True, validate using `bed_space_validator`.

    Raises:
        ValueError: If validation fails due to multiple identifiers or invalid formats.

    Notes:
        - At least one identifier must be provided.
        - Only one identifier should be provided at a time.
        - Delegates validation to the appropriate validator based on context (`panel_space` or `bed_space`).
    """
    # Extract values from input arguments
    logger.info(f"validator recieved: {args},{panel_space},{bed_space}")
    panel_id_value = args.get('Panel_ID', None)
    rcode_value = args.get('Rcode', None)
    hgnc_id_value = args.get('HGNC_ID', None)

    # Ensure at least one identifier is provided
    if not any([panel_id_value, rcode_value, hgnc_id_value]):
        logger.error("At least one of 'Panel_ID', 'Rcode', or 'HGNC_ID' must be provided.")
        raise ValueError("At least one of 'Panel_ID', 'Rcode', or 'HGNC_ID' must be provided.")

    # Ensure only one identifier is provided
    if sum(bool(arg) for arg in [panel_id_value, rcode_value, hgnc_id_value]) > 1:
        logger.error("Provide only one of 'Panel_ID', 'Rcode', or 'HGNC_ID', not multiple.")
        raise ValueError("Provide only one of 'Panel_ID', 'Rcode', or 'HGNC_ID', not multiple.")

    # Delegate validation based on the specified space
    if panel_space:
        logger.info("Validation for panel space")
        panel_space_validator(panel_id_value, rcode_value, hgnc_id_value)

    if bed_space:
        logger.info("Validation for bed space")
        bed_space_validator(panel_id_value, rcode_value, hgnc_id_value)


def hgnc_to_list(args):
            # Check if HGNC_ID is provided
        hgnc_id_value = args.get("HGNC_ID",None)
        if hgnc_id_value:
            if "," in hgnc_id_value:
                try:
                    # Split the HGNC_ID string into a list by commas
                    hgnc_id_list = [h.strip() for h in hgnc_id_value.split(',') if h.strip()]
                    # You can set HGNC_ID to None or remove it to avoid confusion
                    args["HGNC_ID"] = hgnc_id_list

                except Exception as e:

                    
                    logger.debug(f"'error' : 'Failed to process HGNC_ID list: {str(e)}'")
                    # If something unexpected happens, return a descriptive error message
                    return {"error": f"Failed to process HGNC_ID list: {str(e)}"}, 400
            else:
                args["HGNC_ID"] = [hgnc_id_value,]

        return args


def patient_update_validator(args):
    """ Validates patient update inputs (Patient_ID and Rcode).

    Args:
        args (dict): Dictionary containing `Patient_ID` and `Rcode`.
        
    Raises:
        ValueError: If validation fails due to simultaneous absent identifiers or invalid formats.

    Notes:
        - At least one identifier must be provided.
        - Rcode should: 1) start with 'r' or 'R' 2) The proceeding values should be either 2 or 3 digits
        - Patient ID has to contain only digits of any length >= 1.
        """
    # Extract values from input arguments
    patient_id_value = args.get('Patient ID', None)  
    rcode_value = args.get('R code', None) 

     # Pattern for Patient_ID: Matches numeric strings (e.g., '1234')
    patient_pattern = r"^\d+$"
     # Pattern for Rcode: Matches strings like 'R123'
    rcode_pattern = r"^[R]\d+$"
    
     # Validate Panel_ID
    if patient_id_value:
        if not re.fullmatch(patient_pattern, str(patient_id_value)):
            raise ValueError("Invalid format for 'Patient_ID': Must be a number (e.g., '1234').")

    # Validate Rcode
    if rcode_value:
        if not re.fullmatch(rcode_pattern, rcode_value):
            raise ValueError("Invalid format for 'Rcode': Must start with 'R' followed by digits only (e.g., 'R123').")
    

    # Ensure at least one identifier is provided
    if not any([patient_id_value, rcode_value]):
        raise ValueError(f"At least one of 'Panel_ID' or 'Rcode' must be provided. {patient_id_value}")
    
    # Ensure R code exists from panel APP
    # Instantiate query 
    # Query function to check if rcode is in db
    # raise error is not found 
