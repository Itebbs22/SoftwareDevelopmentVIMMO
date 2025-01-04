import pytest
import requests

BASE_URL = "http://127.0.0.1:5000"  # or wherever your Flask app is running

@pytest.mark.integration
def test_local_download_with_panel_id():
    """
    Test downloading a local BED file by providing a valid Panel_ID.
    We expect to get a text/plain file if the DB has data.
    """
    url = f"{BASE_URL}/panels/download/local"
    params = {
        "Panel_ID": "123",         # Must exist in your local DB
        "genome_build": "GRCh38",
        "transcript_set": "Gencode",  # <-- use the exact value your parser expects
        "limit_transcripts": "all"
    }
    response = requests.get(url, params=params)

    print("Status code:", response.status_code)
    print("Headers:", response.headers)
    print("Body (first 300 chars):", response.text[:300])

    if response.status_code == 200:
        # Expect a BED file
        assert "text/plain" in response.headers.get("Content-Type", ""), (
            f"Expected text/plain, got {response.headers.get('Content-Type', '')}"
        )
        bed_content = response.content.decode("utf-8")
        assert bed_content, "Expected BED content, got empty."
    else:
        # Possibly 400 if no matches or invalid input
        try:
            error_json = response.json()
            print("Error JSON:", error_json)
        except Exception:
            print("Non-JSON response:", response.text)
        pytest.fail(f"Expected 200 for a valid panel ID, got {response.status_code}.")


@pytest.mark.integration
def test_local_download_with_rcode():
    """
    Provide an Rcode. The code should retrieve the gene list from the local DB
    and generate a BED if data is found.
    """
    url = f"{BASE_URL}/panels/download/local"
    params = {
        "Rcode": "R208",          # Must exist in your local DB
        "genome_build": "GRCh38",
        "transcript_set": "Gencode",
        "limit_transcripts": "all"
    }
    response = requests.get(url, params=params)

    print("Status code:", response.status_code)
    if response.status_code == 200:
        assert "text/plain" in response.headers.get("Content-Type", "")
        bed_content = response.content.decode("utf-8")
        print("BED Content (first 200 chars):", bed_content[:200])
        assert bed_content, "Should have local BED content for Rcode=R208."
    else:
        print("Error response:", response.text)
        pytest.fail(f"Expected 200 for a valid Rcode, got {response.status_code}.")


@pytest.mark.integration
def test_local_download_with_hgnc_id():
    """
    Provide a single HGNC_ID. The code should skip panel/rcode logic and
    directly query local bed.
    """
    url = f"{BASE_URL}/panels/download/local"
    params = {
        "HGNC_ID": "HGNC:1100",   # Must exist in your bed tables
        "genome_build": "GRCh38",
        "transcript_set": "Gencode",
        "limit_transcripts": "all"
    }
    response = requests.get(url, params=params)

    print("Status code:", response.status_code)
    if response.status_code == 200:
        assert "text/plain" in response.headers.get("Content-Type", "")
        bed_content = response.content.decode("utf-8")
        print("Local BED content sample:", bed_content[:300])
        assert bed_content, "BED content should not be empty for HGNC:1100."
    else:
        print("Error response:", response.text)
        try:
            error_json = response.json()
            print("Error JSON:", error_json)
        except Exception:
            pass
        pytest.fail(f"Expected 200 if HGNC:1100 exists, got {response.status_code}.")


@pytest.mark.integration
def test_local_download_multiple_hgnc_ids():
    """
    Provide multiple comma-separated HGNC IDs, e.g. 'HGNC:11111,HGNC:22222'.
    The endpoint should query local_bed with these IDs.
    """
    url = f"{BASE_URL}/panels/download/local"
    params = {
        "HGNC_ID": "HGNC:11111,HGNC:22222",  # Adjust to real data in your DB
        "genome_build": "GRCh37",
        "transcript_set": "Gencode",
        "limit_transcripts": "all"
    }
    response = requests.get(url, params=params)

    print("Status code:", response.status_code)
    if response.status_code == 200:
        assert "text/plain" in response.headers.get("Content-Type", "")
        bed_content = response.content.decode("utf-8")
        print("Multiple-HGNC local BED content sample:", bed_content[:300])
        assert bed_content, "Expected multiple-HGNC BED content."
    else:
        print("Error response:", response.text)
        pytest.fail("Expected 200 for multiple valid HGNC IDs.")


@pytest.mark.integration
def test_local_download_no_params():
    """
    If no query params are provided, 'validate_panel_id_or_Rcode_or_hgnc' 
    should raise ValueError => 400.
    """
    url = f"{BASE_URL}/panels/download/local"
    response = requests.get(url)

    print("Status code:", response.status_code, response.text[:300])
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"


@pytest.mark.integration
def test_local_download_invalid_hgnc_format():
    """
    If the user provides an invalid HGNC format (e.g., 'HGNC_12345'), 
    'validate_hgnc_ids' should raise ValueError => 400.
    """
    url = f"{BASE_URL}/panels/download/local"
    params = {
        "HGNC_ID": "HGNC_12345",  # invalid (underscore)
        "genome_build": "GRCh38",
        "transcript_set": "Gencode",
        "limit_transcripts": "all"
    }
    response = requests.get(url, params=params)

    assert response.status_code == 400, f"Expected 400 for invalid HGNC format, got {response.status_code}"
    error_data = response.json()
    print("Invalid HGNC format =>", error_data)


@pytest.mark.integration
def test_local_download_nonexisting_panel_id():
    """
    Provide a Panel_ID that doesn't exist. 
    The code might return 400 with some JSON message 
    (e.g. "No matches found" or "No BED data" etc.).
    """
    url = f"{BASE_URL}/panels/download/local"
    params = {
        "Panel_ID": "99999",
        "genome_build": "GRCh38",
        "transcript_set": "Gencode",
        "limit_transcripts": "all"
    }
    response = requests.get(url, params=params)

    print("Status code:", response.status_code, response.text[:300])
    if response.status_code == 200:
        # Possibly it found zero records => might actually do 400 w/ "No BED data could be generated."
        bed_content = response.content.decode("utf-8")
        if not bed_content.strip():
            pytest.fail("Got 200 but the BED file is empty. Possibly expected a 400 with an error message.")
    elif response.status_code == 400:
        # Check if the endpoint returns a JSON with e.g. { "Message" : "...", ... }
        try:
            error_data = response.json()
            print("Error JSON =>", error_data)
        except Exception:
            pass
    else:
        print("Unexpected response code =>", response.status_code)
        pytest.fail("Expected 200 or 400 for a non-existing panel.")


@pytest.mark.integration
def test_local_download_no_bed_data_generated():
    """
    Scenario where the DB returns no rows for some reason.
    
    The code might return 400 with 
    {"error": "No BED data could be generated..."}
    or it might follow the same "Input payload validation failed" format 
    depending on how your code is structured.
    
    We'll adapt our assertions accordingly.
    """
    url = f"{BASE_URL}/panels/download/local"
    params = {
        "HGNC_ID": "HGNC:999999",  # assume not in bed table
        "genome_build": "GRCh38",
        "transcript_set": "Gencode",
        "limit_transcripts": "all"
    }
    response = requests.get(url, params=params)
    
    print("Status code:", response.status_code, response.text[:300])
    if response.status_code == 400:
        error_data = response.json()
        print("Error JSON =>", error_data)

        # If your endpoint code returns a top-level "error" key for no data:
        if "error" in error_data:
            assert "No BED data" in error_data["error"], "Expected 'No BED data' message."
        else:
            # If your code uses 'errors' or something else:
            if "errors" in error_data:
                print("Got a validation-style error instead of the 'No BED data' error.")
            else:
                pytest.fail("Didn't find 'error' or 'errors' in the JSON response.")
    else:
        pytest.fail(f"Expected 400 if no data is generated, got {response.status_code}.")