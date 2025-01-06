import re
import csv
import json
import requests
import sys

# Initialize the list to store all data
all_data = []

# Fetch new data and append to the list
api_url = "https://panelapp.genomicsengland.co.uk/api/v1/panels/signedoff/?display=latest&page=1"

while api_url:
    try:
        # Send GET request to the API
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for HTTP issues
        data = response.json()       # Parse JSON response
        all_data.append(data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        sys.exit(1)

    # Move to the next page if available
    api_url = data.get("next")

# Write the updated data back to the file
with open("all_panel.json", "w") as json_file:
    json.dump(all_data, json_file)

def extract_rcodes(disorders_list):
    """
    Returns all items from disorders_list that match the pattern:
      R + digits, optionally with . and more digits (e.g. R45, R128, R21.5).
    """
    rcodes = []
    pattern = r'^R\d+(\.\d+)?$'  # e.g. R45 or R45.2
    for disorder in disorders_list:
        if re.match(pattern, disorder):
            rcodes.append(disorder)
    return rcodes

def main():
    # Load the data from the JSON file (which can have multiple 'pages')
    with open("all_panel.json", "r", encoding="utf-8") as json_file:
        all_data = json.load(json_file)
    
    # We'll store rows in a list of dictionaries
    rows = []
    
    # all_data could be an array of pages or a single page. 
    # It's an array where each element has "results".
    for page_data in all_data:
        for item in page_data.get('results', []):
            panel_id = item.get('id')
            version = item.get('version')
            disorders_list = item.get('relevant_disorders', [])
            
            # Extract any R-codes
            rcodes = extract_rcodes(disorders_list)
            
            # If no R-codes were found, create one row with a blank R_Code
            if not rcodes:
                rows.append({
                    "Panel_ID": panel_id,
                    "rcodes": "",
                    "Version": version
                })
            else:
                # For each valid R-code, create its own row
                for rcode in rcodes:
                    rows.append({
                        "Panel_ID": panel_id,
                        "rcodes": rcode,
                        "Version": version
                    })
    
    # Write out to CSV
    with open("latest_panel_versions.csv", "w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ["Panel_ID", "rcodes", "Version"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print("CSV file 'latest_panel_versions.csv' has been created.")

main()

items = []
with open('latest_panel_versions.csv', 'r', encoding='utf-8') as pf:
    next(pf)  # Skip header
    for line in pf:
        cleaned_line = line.strip().split(",")
        items.append(cleaned_line)

# This set keeps track of (panel_id, version) pairs we've already processed
processed = set()

with open('genes.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = [
        'Panel ID', 'Gene ID', 'HGNC symbol', 'HGNC ID', 'Gene Symbol',
        'GRCh38 Chr', 'GRCh38 start', 'GRCh38 stop',
        'GRCh37 Chr', 'GRCh37 start', 'GRCh37 stop', 'Confidence'
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in items:
        panel_id = row[0].strip()
        version = row[2].strip()  # row = [Panel_ID, R_Code, Version]

        # Skip if we've already processed this (panel_id, version)
        if (panel_id, version) in processed:
            continue
        processed.add((panel_id, version))

        # Now fetch the data for this panel & version
        url = f'https://panelapp.genomicsengland.co.uk/api/v1/panels/{panel_id}/?format=json&version={version}'
        response = requests.get(url)
        json_data = response.json()

        # Extract the panel ID from the JSON (optional, might be same as panel_id)
        panel_id_json = json_data.get('id', '')

        # Iterate over each gene in the JSON data
        for gene_entry in json_data.get('genes', []):
            gene_data = gene_entry.get('gene_data', None)
            if gene_data:
                # Extract HGNC ID and symbols
                hgnc_id = gene_data.get('hgnc_id', '')
                hgnc_symbol = gene_data.get('hgnc_symbol', '')
                gene_symbol = gene_data.get('gene_symbol', '')

                # Extract Ensembl gene data for GRCh38 and GRCh37
                ensembl_genes = gene_data.get('ensembl_genes', {})
                grch38_data = ensembl_genes.get('GRch38', {})
                grch37_data = ensembl_genes.get('GRch37', {})

                # Function to extract the latest version data
                def get_latest_version_data(version_data):
                    if version_data:
                        return version_data[max(version_data.keys())]
                    return {}

                grch38_info = get_latest_version_data(grch38_data)
                grch37_info = get_latest_version_data(grch37_data)

                # Function to parse chromosome location
                def parse_location(location):
                    if location:
                        chr_part, positions = location.split(':')
                        start_pos, end_pos = positions.split('-')
                        return chr_part, start_pos, end_pos
                    return '', '', ''

                # Extract GRCh38 location details
                grch38_chr, grch38_start, grch38_stop = parse_location(grch38_info.get('location', ''))
                # Extract GRCh37 location details
                grch37_chr, grch37_start, grch37_stop = parse_location(grch37_info.get('location', ''))

                # Use Ensembl ID as the Gene ID
                gene_id = grch38_info.get('ensembl_id') or grch37_info.get('ensembl_id', '')

                # Confidence
                confidence = gene_entry.get('confidence_level', '')

                writer.writerow({
                    'Panel ID': panel_id_json,
                    'Gene ID': gene_id,
                    'HGNC symbol': hgnc_symbol,
                    'HGNC ID': hgnc_id,
                    'Gene Symbol': gene_symbol,
                    'GRCh38 Chr': grch38_chr,
                    'GRCh38 start': grch38_start,
                    'GRCh38 stop': grch38_stop,
                    'GRCh37 Chr': grch37_chr,
                    'GRCh37 start': grch37_start,
                    'GRCh37 stop': grch37_stop,
                    'Confidence': confidence
                })

print("CSV file 'genes.csv' has been created.")