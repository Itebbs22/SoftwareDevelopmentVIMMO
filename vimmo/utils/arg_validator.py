import re

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
        - `Rcode` must match the pattern 'r\d+' or 'R\d+' (e.g., 'R123').
        - `HGNC_ID` must match the pattern 'HGNC:\d+' (e.g., 'HGNC:12345').
        - `Panel_ID` must be numeric.
    """
    # Pattern for Rcode: Matches strings like 'r123' or 'R123'
    rcode_pattern = r"^[rR]\d+$"
    # Pattern for HGNC_ID: Matches strings like 'HGNC:12345'
    hgnc_pattern = r"^HGNC:\d+$"

    # Validate Panel_ID: Must be numeric
    if panel_id_value:
        try:
            int(panel_id_value)  # Convert to integer to check numeric format
        except ValueError:
            raise ValueError("Invalid input: 'Panel_ID' must be digits only (e.g., '123').")

    # Validate Rcode: Must match 'R123' or 'r123'
    if rcode_value:
        if not re.fullmatch(rcode_pattern, rcode_value):
            raise ValueError("Invalid format for 'Rcode': Must start with 'R' followed by digits only (e.g., 'R123').")

    # Validate HGNC_ID: Must match 'HGNC:12345'
    if hgnc_id_value:
        if not re.fullmatch(hgnc_pattern, hgnc_id_value):
            raise ValueError(
                "Invalid format for 'HGNC_ID': It must start with 'HGNC:' followed by digits only (e.g., 'HGNC:12345')."
            )

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
        - `Rcode` must match the pattern 'R\d+' (e.g., 'R123').
        - `HGNC_ID` must match the pattern 'HGNC:\d+' (e.g., 'HGNC:12345').
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
            raise ValueError("Invalid format for 'Panel_ID': Must be a number (e.g., '1234').")

    # Validate Rcode: Must match 'R123'
    if rcode_value:
        if not re.fullmatch(rcode_pattern, rcode_value):
            raise ValueError("Invalid format for 'Rcode': Must start with 'R' followed by digits only (e.g., 'R123').")

    # Validate HGNC_ID: Must match 'HGNC:12345'
    if hgnc_id_value:
        if not re.fullmatch(hgnc_pattern, hgnc_id_value):
            raise ValueError(
                "Invalid format for 'HGNC_ID': It must start with 'HGNC:' followed by digits only (e.g., 'HGNC:12345')."
            )

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
    panel_id_value = args.get('Panel_ID', None)
    rcode_value = args.get('Rcode', None)
    hgnc_id_value = args.get('HGNC_ID', None)

    # Ensure at least one identifier is provided
    if not any([panel_id_value, rcode_value, hgnc_id_value]):
        raise ValueError("At least one of 'Panel_ID', 'Rcode', or 'HGNC_ID' must be provided.")

    # Ensure only one identifier is provided
    if sum(bool(arg) for arg in [panel_id_value, rcode_value, hgnc_id_value]) > 1:
        raise ValueError("Provide only one of 'Panel_ID', 'Rcode', or 'HGNC_ID', not multiple.")

    # Delegate validation based on the specified space
    if panel_space:
        panel_space_validator(panel_id_value, rcode_value, hgnc_id_value)

    if bed_space:
        bed_space_validator(panel_id_value, rcode_value, hgnc_id_value)
