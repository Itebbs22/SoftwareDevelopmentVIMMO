import pytest
import requests

BASE_URL = "http://127.0.0.1:5001"  # Adjust if different

@pytest.mark.integration
def test_patient_only_id():
    """
    Provide ONLY 'Patient ID' (e.g. T123). Should return all historical tests for that patient.
    Example DB: T123 => had R208, version=2.5, date=2023-12-30
    Expected JSON:
    {
       "Patient ID": "T123",
       "patient records": {
         0: { "2023-12-30": ["R208", 2.5] }
       }
    }
    """
    url = f"{BASE_URL}/patient"
    params = {
        "Patient ID": "T123"
    }
    response = requests.get(url, params=params)
    print("Status:", response.status_code, "Response JSON:", response.json())

    assert response.status_code == 200
    data = response.json()

    assert data.get("Patient ID") == "T123"
    # Check that we have 'patient records'
    assert "patient records" in data
    # Possibly check if the date, rcode, version match the sample data


@pytest.mark.integration
def test_patient_only_rcode():
    """
    Provide ONLY 'R code' (e.g. R208). Should return all patients who have had R208.
    Example DB: T123 has R208, version=2.5
    Expected JSON:
    {
       "R code": "R208",
       "Records": {
         0: { "2023-12-30": [ "T123", 2.5 ] }
       }
    }
    """
    url = f"{BASE_URL}/patient"
    params = {
        "R code": "R208"
    }
    response = requests.get(url, params=params)
    print("Status:", response.status_code, "Response JSON:", response.json())

    assert response.status_code == 200
    data = response.json()

    assert data.get("R code") == "R208"
    # Check 'Records' key
    assert "Records" in data
    # Possibly check the structure, e.g. data["Records"][0] == { "2023-12-30": ["T123", 2.5] } in your DB case


@pytest.mark.integration
def test_patient_only_rcode():
    """
    Provide ONLY 'R code' (e.g., R208).
    Expect to get all patients who have had R208.
    
    Example response shape:
    {
      "R code": "R208",
      "Records": {
         0: {"2023-12-30": ["T123", 2.5]},
         1: {"2022-05-16": ["T456", 1.5]}
      }
    }
    """
    url = f"{BASE_URL}/patient"
    params = {
        "R code": "R208"  # change to an R code you know exists in your DB
    }
    response = requests.get(url, params=params)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print("Rcode-only response:", data)

    # Check basic structure
    assert data.get("R code") == "R208"
    assert "Records" in data
    # Optionally check the content of "Records"

@pytest.mark.integration
def test_patient_only_id():
    """
    Provide ONLY 'Patient ID' (e.g., T123).
    Expect to get all historical tests (R codes, versions, dates) for that patient.
    
    Example response shape:
    {
      "Patient ID": "T123",
      "patient records": {
         0: {"2023-12-30": ["R208", 2.5]},
         1: {"2022-05-16": ["R167", 1.5]}
      }
    }
    """
    url = f"{BASE_URL}/patient"
    params = {
        "Patient ID": "T123"  # change to a patient ID you know is in your DB
    }
    response = requests.get(url, params=params)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print("PatientID-only response:", data)

    # Check basic structure
    assert data.get("Patient ID") == "T123"
    assert "patient records" in data
    # Optionally check the contents of "patient records"


@pytest.mark.integration
def test_patient_both_no_record():
    """
    Provide BOTH 'Patient ID' and 'R code' that do NOT exist together in the DB.
    E.g. 'Patient ID' = T999, 'R code'= R208 => no record found.
    Expect something like:
    {
      "Status": "There is NO record of patient T999 recieving any R code within our records"
    }
    """
    url = f"{BASE_URL}/patient"
    params = {
        "Patient ID": "T999",  # doesn't exist
        "R code": "R208"
    }
    response = requests.get(url, params=params)
    print("Status:", response.status_code, "JSON:", response.json())

    assert response.status_code == 200  # The endpoint returns a normal JSON message
    data = response.json()

    # Possibly check if "Status" in data
    # "There is NO record of patient T999 recieving any R code within our records"
    assert "Status" in data
    assert "NO record" in data["Status"]


@pytest.mark.integration
def test_patient_both_same_version():
    """
    Provide BOTH 'Patient ID'=T123 and 'R code'=R208, 
    but the DB's current version = the patient's last version => "No version change since last T123 had R208"
    Example from DB: T123 has R208 version=2.5 (2023-12-30),
    and panel table also says R208 => version=2.5 -> no difference
    Expected JSON:
    {
      "disclaimer": "Panel comparison up to date",
      "status": "No version change since last T123 had R208",
      "Version": "2.5",
      "Panel content": {
         "HGNC:xxxx": 3,
         ...
      }
    }
    """
    url = f"{BASE_URL}/patient"
    params = {
        "Patient ID": "T123",
        "R code": "R208"
    }
    response = requests.get(url, params=params)
    data = response.json()
    print("Status:", response.status_code, "JSON:", data)

    assert response.status_code == 200
    # Check no version change scenario
    assert data.get("status", "").startswith("No version change"), "Expected a no-change status"
    # Check disclaimers, version, etc. as needed
