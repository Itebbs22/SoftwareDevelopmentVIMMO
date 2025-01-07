import pytest
import requests
import time

BASE_URL = "http://127.0.0.1:5001"  # or wherever your Flask app is running

@pytest.mark.integration
def test_download_with_panel_id():
    """
    Test downloading a BED file by providing a valid Panel_ID.
    Expect a 200 status and a file attachment (text/plain).
    """
    url = f"{BASE_URL}/panels/download"
    params = {
        "Panel_ID": "123",  # must exist in your DB
        "genome_build": "GRCh38",
        "transcript_set": "all",
        "limit_transcripts": "mane_select"
    }
    response = requests.get(url, params=params)
    time.sleep(1) # sleeping so doesnt exceed rate limit
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    # Because the endpoint uses `send_file`, we expect 'text/plain' or 'application/octet-stream', etc.
    assert "text/plain" in response.headers.get("Content-Type", ""), "Response should be a text/plain for BED."
    
    # Check Content-Disposition for filename
    content_disp = response.headers.get("Content-Disposition", "")
    print("Content-Disposition:", content_disp)
    assert "attachment" in content_disp, "Expected an attachment in Content-Disposition."
    # Optionally check if the filename matches the logic in your code:
    # e.g. "filename=123_GRCh38_mane_select.bed"
    # Some servers/Flask versions might show it differently ("download_name=...").

    # If you want to inspect the actual BED content:
    bed_content = response.content.decode("utf-8")
    print("BED Content:\n", bed_content[:500])  # print first 500 chars
    assert bed_content, "Expected some BED content."

@pytest.mark.integration
def test_download_with_rcode():
    """
    Test downloading a BED file by providing a valid Rcode.
    """
    url = f"{BASE_URL}/panels/download"
    params = {
        "Rcode": "R208",  # must exist in your DB
        "genome_build": "GRCh38",
        "transcript_set": "all",
        "limit_transcripts": "mane_select"
    }
    response = requests.get(url, params=params)
    time.sleep(1) # sleeping so doesnt exceed rate limit
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    assert "text/plain" in response.headers.get("Content-Type", "")
    
    # Check the filename in Content-Disposition
    content_disp = response.headers.get("Content-Disposition", "")
    print("Content-Disposition:", content_disp)
    assert "R208" in content_disp, "Expected Rcode in the filename."

@pytest.mark.integration
def test_download_with_hgnc_id():
    """
    Provide a single HGNC_ID. The code should skip panel/rcode logic and directly parse that gene.
    """
    url = f"{BASE_URL}/panels/download"
    params = {
        "HGNC_ID": "HGNC:1100",  # must exist or this fails and highly dependant on connection
        "genome_build": "GRCh38",
        "transcript_set": "refseq",
        "limit_transcripts": "mane_select"
    }
    response = requests.get(url, params=params)
    time.sleep(1) # sleeping so doesnt exceed rate limit
    # We might get 200 if HGNC:1100 is valid, or 400/500 if no data or an error occurs.
    print("Status code:", response.status_code, "Response text:", response.text[:200])
    assert "text/plain" in response.headers.get("Content-Type", "")
    bed_content = response.content.decode("utf-8")
    assert bed_content, "BED content should not be empty."


@pytest.mark.integration
def test_download_multiple_hgnc_ids():
    """
    Provide multiple comma-separated HGNC IDs.
    """
    url = f"{BASE_URL}/panels/download"
    params = {
        "HGNC_ID": "HGNC:1100,HGNC:1200",
        "genome_build": "GRCh37",  # maybe test the older build
        "transcript_set": "ensembl",
        "limit_transcripts": "all"
    }
    response = requests.get(url, params=params)
    time.sleep(1) # sleeping so doesnt exceed rate limit
    print("Status code:", response.status_code)
    bed_content = response.content.decode("utf-8")
    print("BED content sample:\n", bed_content[:300])
    # If your code merges/joins multiple IDs, confirm the result.
    assert "application/json" in response.headers.get("Content-Type", "")
    assert bed_content, "Expected BED content for multiple HGNCs."

@pytest.mark.integration
def test_download_no_params():
    """
    If no arguments are provided, 'validate_panel_id_or_Rcode_or_hgnc' 
    raises a ValueError => should return 400 and a JSON error.
    """
    url = f"{BASE_URL}/panels/download"
    response = requests.get(url)  # no params
    time.sleep(1) # sleeping so doesnt exceed rate limit
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    error_json = response.json()
    print("Error JSON:", error_json)
    # Possibly check if "At least one of 'Panel_ID', 'Rcode', or 'HGNC_ID' must be provided." is in error_json["error"]

@pytest.mark.integration
def test_download_invalid_hgnc():
    """
    If we pass an invalid HGNC format (e.g. 'HGNC_12345'), the validator 
    should fail => 400 error with an error message.
    """
    url = f"{BASE_URL}/panels/download"
    params = {
        "HGNC_ID": "HGNC_12345",  # invalid (underscore instead of colon)
    }
    response = requests.get(url, params=params)
    time.sleep(1) # sleeping so doesnt exceed rate limit
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    error_data = response.json()
    print("Invalid HGNC format ->", error_data)
    # Possibly "Invalid format for 'HGNC_ID'..."

@pytest.mark.integration
def test_download_no_matches_panel_id():
    """
    Provide a Panel_ID that does not exist in DB -> 
    The code returns a JSON with 'Message': 'No matches found.' OR
    possibly no BED data => 400
    """
    url = f"{BASE_URL}/panels/download"
    params = {
        "Panel_ID": "99999"  # an ID you know doesn't exist
    }
    response = requests.get(url, params=params)
    time.sleep(1) # sleeping so doesnt exceed rate limit
    print("Status code:", response.status_code, response.text[:300])
    if response.status_code == 200:
        # Possibly you get JSON with "No matches found." or bed_file might be empty -> 400
        # Check if the code returns {"Panel_ID":..., "Message": "No matches found."}
        json_data = {}
        try:
            json_data = response.json()
            print("JSON:", json_data)
        except:
            # If it's actually returning a file, you won't be able to do .json() 
            pass
        # See if there's a "Message"
        if "Message" in json_data:
            assert json_data["Message"] == "No matches found.", "Expected 'No matches found.' message."
    elif response.status_code == 400:
        json_data = response.json()
        print("400 error JSON =>", json_data)
    else:
        # Possibly 500 if code raises an error
        print("Error response ->", response.text)
