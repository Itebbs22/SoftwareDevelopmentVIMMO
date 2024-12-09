import re


def panel_space_validator(panel_id_value, rcode_value, hgnc_id_value):
    """
    Validates Panel_ID, Rcode, and HGNC_ID specifically for the panel space.
    - `Rcode`: Starts with lowercase 'r' followed by digits.
    - `HGNC_ID`: Starts with 'HGNC:' followed by digits.
    - `Panel_ID`: Must be numeric.
    """
    # Pattern for Rcode: Matches strings starting with 'r' followed by digits (e.g., r123)
    rcode_pattern = r"^r\d+$"
    # Pattern for HGNC_ID: Matches strings starting with 'HGNC:' followed by digits (e.g., HGNC:12345)
    hgnc_pattern = r"^HGNC:\d+$"

    # Validate Panel_ID: Ensure it is numeric
    if panel_id_value:
        try:
            int(panel_id_value)  # Convert to integer to check numeric format
        except ValueError:
            # Raise an error if conversion fails
            raise ValueError("Invalid input: 'Panel_ID' must be digits only (e.g., '123').")

    # Validate Rcode: Matches lowercase 'r' followed by digits
    if rcode_value:
        if not re.fullmatch(rcode_pattern, rcode_value):  # Match pattern
            raise ValueError("Invalid format for 'Rcode': Must start with 'R' followed by digits only (e.g., 'R123').")

    # Validate HGNC_ID: Matches 'HGNC:' followed by digits
    if hgnc_id_value:
        if not re.fullmatch(hgnc_pattern, hgnc_id_value):  # Match pattern
            raise ValueError(
                "Invalid format for 'HGNC_ID': It must start with 'HGNC:' followed by digits only (e.g., 'HGNC:12345')."
            )


def bed_space_validator(panel_id_value, rcode_value, hgnc_id_value):
    """
    Validates Panel_ID, Rcode, and HGNC_ID specifically for the bed space.
    - `Rcode`: Starts with uppercase 'R' followed by digits.
    - `HGNC_ID`: Starts with 'HGNC:' followed by digits.
    - `Panel_ID`: Must be numeric.
    """
    # Pattern for Rcode: Matches strings starting with 'R' followed by digits (e.g., R123)
    rcode_pattern = r"^R\d+$"
    # Pattern for Panel_ID: Matches numeric strings (e.g., 1234)
    panel_pattern = r"^\d+$"
    # Pattern for HGNC_ID: Matches 'HGNC:' followed by digits (e.g., HGNC:12345)
    hgnc_pattern = r"^HGNC:\d+$"

    # Validate Panel_ID: Ensure it is numeric
    if panel_id_value:
        if not re.fullmatch(panel_pattern, str(panel_id_value)):  # Match pattern
            raise ValueError("Invalid format for 'Panel_ID': Must be a number (e.g., '1234').")

    # Validate Rcode: Matches uppercase 'R' followed by digits
    if rcode_value:
        if not re.fullmatch(rcode_pattern, rcode_value):  # Match pattern
            raise ValueError("Invalid format for 'Rcode': Must start with 'R' followed by digits only (e.g., 'R123').")

    # Validate HGNC_ID: Matches 'HGNC:' followed by digits
    if hgnc_id_value:
        if not re.fullmatch(hgnc_pattern, hgnc_id_value):  # Match pattern
            raise ValueError(
                "Invalid format for 'HGNC_ID': It must start with 'HGNC:' followed by digits only (e.g., 'HGNC:12345')."
            )


def validate_panel_id_or_Rcode_or_hgnc(args, panel_space=False, bed_space=False):
    """
    High-level validation function for Panel_ID, Rcode, and HGNC_ID.
    - Ensures only one identifier is provided.
    - Delegates validation to panel_space_validator or bed_space_validator.
    Args:
        args (dict): Input arguments containing `Panel_ID`, `Rcode`, and `HGNC_ID`.
        panel_space (bool): If True, validates using `panel_space_validator`.
        bed_space (bool): If True, validates using `bed_space_validator`.
    """
    # Extract input values from the dictionary
    panel_id_value = args.get('Panel_ID', None)  # Panel_ID
    rcode_value = args.get('Rcode', None)  # Rcode
    hgnc_id_value = args.get('HGNC_ID', None)  # HGNC_ID

    # Ensure at least one of the identifiers is provided
    if not any([panel_id_value, rcode_value, hgnc_id_value]):
        raise ValueError("At least one of 'Panel_ID', 'Rcode', or 'HGNC_ID' must be provided.")

    # Ensure only one of the identifiers is provided
    if sum(bool(arg) for arg in [panel_id_value, rcode_value, hgnc_id_value]) > 1:
        raise ValueError("Provide only one of 'Panel_ID', 'Rcode', or 'HGNC_ID', not multiple.")

    # Delegate validation based on the specified space
    if panel_space:
        panel_space_validator(panel_id_value, rcode_value, hgnc_id_value)

    if bed_space:
        bed_space_validator(panel_id_value, rcode_value, hgnc_id_value)
