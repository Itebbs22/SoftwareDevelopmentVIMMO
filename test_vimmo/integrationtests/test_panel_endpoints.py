# test_vimmo/integrationtests/test_panel_endpoints.py

import pytest
import requests

# Adjust this to match the actual URL where your Flask app runs.
# If running locally:
BASE_URL = "http://127.0.0.1:5000"
# Or if using Docker, it might be "http://localhost:5000" or something else.

@pytest.mark.integration
def test_panel_search_with_panel_id():
    """
    Test /panels endpoint by passing a valid 'Panel_ID'.
    Expect a 200 and valid panel data in JSON.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "123",  # Example ID
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    
    json_data = response.json()
    # Here, you'd assert on the structure or content of `json_data`.
    # For instance, if your DB has known data for Panel_ID=123:
    # assert json_data["panel_name"] == "Some Panel"  (example)
    print("Response JSON for Panel_ID=123 -->", json_data)


@pytest.mark.integration
def test_panel_search_with_rcode():
    """
    Test /panels endpoint by passing a valid 'Rcode'.
    Expect a 200 and valid panel data in JSON.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Rcode": "R123",  # Must match the pattern [Rr]digits
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    
    json_data = response.json()
    # Check structure:
    # assert isinstance(json_data, list) or dict, etc.
    print("Response JSON for Rcode=R123 -->", json_data)


@pytest.mark.integration
def test_panel_search_with_hgnc_id():
    """
    Test /panels endpoint by passing a valid 'HGNC_ID'.
    Must start with 'HGNC:' followed by digits, e.g. 'HGNC:12345'
    Since your code also handles multiple HGNC IDs (comma-separated), we can test that too.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "HGNC_ID": "HGNC:12345"  # example
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    
    json_data = response.json()
    print("Response JSON for HGNC_ID=HGNC:12345 -->", json_data)


@pytest.mark.integration
def test_panel_search_with_multiple_params_should_fail():
    """
    The validator enforces ONLY one of Panel_ID, Rcode, or HGNC_ID to be provided.
    Passing multiple should result in a 400 error and an error message.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "123",
        "Rcode": "R456",
    }
    response = requests.get(url, params=params)
    
    # The validate_panel_id_or_Rcode_or_hgnc function raises a ValueError if multiple are present,
    # so we expect a 400.
    assert response.status_code == 400, f"Expected 400 but got {response.status_code}"
    
    error_data = response.json()
    print("Response JSON for multiple params -->", error_data)
    # Example check: 
    # assert "Provide only one" in error_data["error"]


@pytest.mark.integration
def test_panel_search_with_no_params_should_fail():
    """
    If we pass no parameters, the endpoint should raise a ValueError stating
    at least one of Panel_ID, Rcode, or HGNC_ID must be provided.
    """
    url = f"{BASE_URL}/panels"
    response = requests.get(url)  # no params at all
    
    assert response.status_code == 400, f"Expected 400 but got {response.status_code}"
    error_data = response.json()
    print("Response JSON for no params -->", error_data)


@pytest.mark.integration
def test_panel_search_with_similar_matches():
    """
    Test how the endpoint behaves when 'Similar_Matches=true' is passed.
    Your code indicates it might look for similarly matched IDs in the DB.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "123",
        "Similar_Matches": "true"
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    
    json_data = response.json()
    print("Response JSON for Panel_ID=123 with Similar_Matches=true -->", json_data)
    # Potentially assert that the result includes similarly matched panel IDs, etc.


@pytest.mark.integration
def test_panel_search_non_existing_panel_id():
    """
    If Panel_ID doesn't exist in the DB, the endpoint should return a 200 with a 'No matches found.' message.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "9999999"  # Use an ID you know doesn't exist in your DB
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    json_data = response.json()
    print("Non-existing Panel_ID JSON:", json_data)
    
    # For your Query.get_panel_data(), if no matches are found, you return:
    #   {"Panel_ID": panel_id, "Message": "No matches found."}
    # Adjust if your code differs.
    assert "Message" in json_data, "Expected a 'Message' key with 'No matches found.'"
    assert json_data["Message"] == "No matches found.", "Should return 'No matches found.' for missing panel."


@pytest.mark.integration
def test_panel_search_with_similar_matches_for_panel_id():
    """
    If 'Similar_Matches=true' is passed with a Panel_ID,
    Query.get_panel_data() uses a LIKE query for the ID. 
    That might return any panels that partially match '123'.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "123",      # Adjust this to a partial ID that might appear in your DB (e.g., "12")
        "Similar_Matches": "true"
    }
    response = requests.get(url, params=params)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    json_data = response.json()
    print("Similar matches for panel_id=123 ->", json_data)

    # If your DB has panel_id 123 or 1234 or 4123, it might appear in the result. 
    # Make an assertion about the data structure:
    if "Associated Gene Records" in json_data:
        assert isinstance(json_data["Associated Gene Records"], list), "Expected a list of records"
    else:
        # Possibly returns {"Panel_ID": "123", "Message": "No matches found."}
        assert "Message" in json_data



@pytest.mark.integration
def test_panel_search_non_existing_rcode():
    """
    If Rcode doesn't exist, the endpoint should return a 200 but with a 
    'Message': 'No matches found for this rcode.' 
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Rcode": "R999999"
    }
    response = requests.get(url, params=params)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    json_data = response.json()
    print("Non-existing Rcode JSON:", json_data)
    
    # Query.get_panels_by_rcode() returns:
    #   {"Rcode": rcode, "Message": "No matches found for this rcode."} if none found
    assert json_data.get("Message") == "No matches found for this rcode.", "Did not get the expected error message."


@pytest.mark.integration
def test_panel_search_with_similar_matches_for_rcode():
    """
    If 'Similar_Matches=true' is passed with Rcode,
    we expect get_panels_by_rcode to use an operator LIKE for rcode.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Rcode": "R12",        # If you have an Rcode that partially matches 'R12'
        "Similar_Matches": "true"
    }
    response = requests.get(url, params=params)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    json_data = response.json()
    print("Similar matches for Rcode=R12 ->", json_data)
    
    # If the DB found partial matches (e.g., R123, R125, etc.), you'd see them.
    # If not found, might see {"Rcode": "R12", "Message": "No matches found for this rcode."}
    # Validate the structure as needed.
    if "Associated Gene Records" in json_data:
        assert isinstance(json_data["Associated Gene Records"], list), "Should be a list of gene records."


@pytest.mark.integration
def test_panel_search_with_multiple_hgnc_ids():
    """
    Passing multiple HGNC IDs, e.g., 'HGNC:12345,HGNC:67890'.
    Your parser (hgnc_to_list) splits these into a list, 
    then Query.get_panels_from_gene_list() does an IN(...) query.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "HGNC_ID": "HGNC:12345,HGNC:67890"  # Adjust to real IDs in your DB
    }
    response = requests.get(url, params=params)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    json_data = response.json()
    print("Multiple HGNC IDs JSON:", json_data)
    
    # The DB logic returns something like:
    #  {
    #     "HGNC_IDs": ["HGNC:12345","HGNC:67890"],
    #     "Panels": [...]
    #  }
    # or {"HGNC_IDs":[...], "Message":"Could not find any match..."} if not found
    if "Panels" in json_data:
        assert isinstance(json_data["Panels"], list), "Expected a list of panel data."
    else:
        assert "Message" in json_data, "Should have 'Message' if no matches found."


@pytest.mark.integration
def test_panel_search_with_hgnc_matches_not_implemented():
    """
    If user passes 'Similar_Matches=true' AND uses HGNC_ID, the code
    should raise NotImplementedError, which hopefully you handle gracefully
    or return 400/500.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "HGNC_ID": "HGNC:12345",
        "Similar_Matches": "true"
    }
    response = requests.get(url, params=params)
    
    # If your code doesn't catch NotImplementedError, you'll get a 500
    # (internal server error). You might want to handle it and return 501 or 400.
    print("Wildcard HGNC_ID test ->", response.status_code, response.text)
    assert response.status_code != 200, "Expected an error code if NotImplementedError is raised."
    
    # Alternatively, if you decide to handle the NotImplementedError gracefully,
    # you might do something like: return {"error": "Wildcard matching not implemented"}, 501
    # Adjust your test expectations accordingly.


@pytest.mark.integration
def test_panel_search_invalid_hgnc_format():
    """
    If user passes an invalid HGNC format (e.g., 'HGNC12345' or 'hgnc:999'),
    your validate_hgnc_ids should raise a ValueError => returns 400.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "HGNC_ID": "HGNC_99999"  # underscores, not a colon
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    error_data = response.json()
    print("Invalid HGNC format error response:", error_data)
    
    # Possibly check if the error message says "Invalid format for 'HGNC_ID'..."
    # assert "Invalid format" in error_data["error"]
@pytest.mark.integration
def test_panel_search_with_panel_rcode_hgnc():
    """
    Provide Panel_ID, Rcode, and HGNC_ID together => 400 error.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "123",
        "Rcode": "R208",
        "HGNC_ID": "HGNC:12345"
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    error_json = response.json()
    print("Panel + Rcode + HGNC => error JSON:", error_json)
    # Possibly assert "Provide only one" in error_json["error"] or similar.


@pytest.mark.integration
def test_panel_search_with_numeric_like():
    """
    If your code wants to allow partial matching on numeric Panel_ID,
    e.g. passing "12" matches "123", "412", etc.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "12",
        "Similar_Matches": "true"
    }
    response = requests.get(url, params=params)

    # Could be 200 with partial matches or "No matches found."
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    json_data = response.json()
    print("Numeric partial match response:", json_data)





@pytest.mark.integration
def test_panel_search_non_existing_panel_id():
    """
    If Panel_ID doesn't exist in the DB, the endpoint should return a 200 with a 'No matches found.' message.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "9999999"  # Use an ID you know doesn't exist in your DB
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    json_data = response.json()
    print("Non-existing Panel_ID JSON:", json_data)
    
    # For your Query.get_panel_data(), if no matches are found, you return:
    #   {"Panel_ID": panel_id, "Message": "No matches found."}
    # Adjust if your code differs.
    assert "Message" in json_data, "Expected a 'Message' key with 'No matches found.'"
    assert json_data["Message"] == "No matches found.", "Should return 'No matches found.' for missing panel."



@pytest.mark.integration
def test_panel_search_with_similar_matches_for_panel_id():
    """
    If 'Similar_Matches=true' is passed with a Panel_ID,
    Query.get_panel_data() uses a LIKE query for the ID. 
    That might return any panels that partially match '123'.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "123",      # Adjust this to a partial ID that might appear in your DB (e.g., "12")
        "Similar_Matches": "true"
    }
    response = requests.get(url, params=params)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    json_data = response.json()
    print("Similar matches for panel_id=123 ->", json_data)

    # If your DB has panel_id 123 or 1234 or 4123, it might appear in the result. 
    # Make an assertion about the data structure:
    if "Associated Gene Records" in json_data:
        assert isinstance(json_data["Associated Gene Records"], list), "Expected a list of records"
    else:
        # Possibly returns {"Panel_ID": "123", "Message": "No matches found."}
        assert "Message" in json_data

@pytest.mark.integration
def test_panel_search_non_existing_rcode():
    """
    If Rcode doesn't exist, the endpoint should return a 200 but with a 
    'Message': 'No matches found for this rcode.' 
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Rcode": "R999999"
    }
    response = requests.get(url, params=params)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    json_data = response.json()
    print("Non-existing Rcode JSON:", json_data)
    
    # Query.get_panels_by_rcode() returns:
    #   {"Rcode": rcode, "Message": "No matches found for this rcode."} if none found
    assert json_data.get("Message") == "No matches found for this rcode.", "Did not get the expected error message."

@pytest.mark.integration
def test_panel_search_with_similar_matches_for_rcode():
    """
    If 'Similar_Matches=true' is passed with Rcode,
    we expect get_panels_by_rcode to use an operator LIKE for rcode.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Rcode": "R12",        # If you have an Rcode that partially matches 'R12'
        "Similar_Matches": "true"
    }
    response = requests.get(url, params=params)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    json_data = response.json()
    print("Similar matches for Rcode=R12 ->", json_data)
    
    # If the DB found partial matches (e.g., R123, R125, etc.), you'd see them.
    # If not found, might see {"Rcode": "R12", "Message": "No matches found for this rcode."}
    # Validate the structure as needed.
    if "Associated Gene Records" in json_data:
        assert isinstance(json_data["Associated Gene Records"], list), "Should be a list of gene records."

@pytest.mark.integration
def test_panel_search_with_multiple_hgnc_ids():
    """
    Passing multiple HGNC IDs, e.g., 'HGNC:12345,HGNC:67890'.
    Your parser (hgnc_to_list) splits these into a list, 
    then Query.get_panels_from_gene_list() does an IN(...) query.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "HGNC_ID": "HGNC:12345,HGNC:67890"  # Adjust to real IDs in your DB
    }
    response = requests.get(url, params=params)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    json_data = response.json()
    print("Multiple HGNC IDs JSON:", json_data)
    
    # The DB logic returns something like:
    #  {
    #     "HGNC_IDs": ["HGNC:12345","HGNC:67890"],
    #     "Panels": [...]
    #  }
    # or {"HGNC_IDs":[...], "Message":"Could not find any match..."} if not found
    if "Panels" in json_data:
        assert isinstance(json_data["Panels"], list), "Expected a list of panel data."
    else:
        assert "Message" in json_data, "Should have 'Message' if no matches found."

@pytest.mark.integration
def test_panel_search_with_hgnc_matches_not_implemented():
    """
    If user passes 'Similar_Matches=true' AND uses HGNC_ID, the code
    should raise NotImplementedError, which hopefully you handle gracefully
    or return 400/500.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "HGNC_ID": "HGNC:12345",
        "Similar_Matches": "true"
    }
    response = requests.get(url, params=params)
    
    # If your code doesn't catch NotImplementedError, you'll get a 500
    # (internal server error). You might want to handle it and return 501 or 400.
    print("Wildcard HGNC_ID test ->", response.status_code, response.text)
    assert response.status_code != 200, "Expected an error code if NotImplementedError is raised."
    
    # Alternatively, if you decide to handle the NotImplementedError gracefully,
    # you might do something like: return {"error": "Wildcard matching not implemented"}, 501
    # Adjust your test expectations accordingly.

@pytest.mark.integration
def test_panel_search_invalid_hgnc_format():
    """
    If user passes an invalid HGNC format (e.g., 'HGNC12345' or 'hgnc:999'),
    your validate_hgnc_ids should raise a ValueError => returns 400.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "HGNC_ID": "HGNC_99999"  # underscores, not a colon
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    error_data = response.json()
    print("Invalid HGNC format error response:", error_data)
    

@pytest.mark.integration
def test_panel_search_with_panel_rcode_hgnc():
    """
    Provide Panel_ID, Rcode, and HGNC_ID together => 400 error.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "123",
        "Rcode": "R208",
        "HGNC_ID": "HGNC:12345"
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    error_json = response.json()
    print("Panel + Rcode + HGNC => error JSON:", error_json)
    # Possibly assert "Provide only one" in error_json["error"] or similar.

@pytest.mark.integration
def test_panel_search_with_numeric_like():
    """
    If your code wants to allow partial matching on numeric Panel_ID,
    e.g. passing "12" matches "123", "412", etc.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "12",
        "Similar_Matches": "true"
    }
    response = requests.get(url, params=params)

    # Could be 200 with partial matches or "No matches found."
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    json_data = response.json()
    print("Numeric partial match response:", json_data)
#(If you think partial matching for numeric IDs doesn’t make sense, you might remove or alter this test.)

@pytest.mark.integration
def test_panel_search_basic_existing_data():
    """
    Simple test that uses a known valid Panel_ID (or Rcode) which definitely 
    exists in your DB. We expect a 200 with non-empty results.
    """
    url = f"{BASE_URL}/panels"
    params = {
        "Panel_ID": "123"  # MUST be a real panel_id in your local DB
    }
    response = requests.get(url, params=params)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    json_data = response.json()
    print("Smoke test for Panel_ID=123 ->", json_data)
    
    # If your DB definitely has records for Panel_ID=123, 
    # ensure we get "Associated Gene Records" and it's non-empty:
    assert "Associated Gene Records" in json_data, "Expected 'Associated Gene Records' key in the response."
    assert len(json_data["Associated Gene Records"]) > 0, "Expected at least one record."