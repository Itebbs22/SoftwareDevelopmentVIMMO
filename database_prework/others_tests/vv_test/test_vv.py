import requests
from urllib.parse import quote
import pandas as pd

class VarValAPIError(Exception):
    """Custom exception for errors related to the VariantValidator API."""
    pass

def __init__(base_url='https://rest.variantvalidator.org/VariantValidator/tools/gene2transcripts_v2'):
    """
    Initialize the VariantValidator client.
    """
    return base_url

def _check_response(url):
    """
    Sends a GET request to the specified URL and validates the response.
    """
    try:
        response = requests.get(url)
    except requests.RequestException as e:
        raise VarValAPIError(f"Failed to connect. Please check your internet connection and try again: {e}")

    if not response.ok:
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type.lower():
            # Likely an HTML or non-JSON error response
            raise VarValAPIError(f"Server returned an error ({response.status_code}). Possibly an internal error.")
        else:
            # Attempt to parse JSON error
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and 'error' in error_data:
                    raise VarValAPIError(f"API returned an error: {error_data['error']}")
                else:
                    raise VarValAPIError(f"Request failed with status code {response.status_code}.")
            except ValueError:
                raise VarValAPIError(f"Request failed with status code {response.status_code}, and could not parse error details.")

    # If 200 OK, try JSON parse
    try:
        data = response.json()
        return data
    except ValueError:
        raise VarValAPIError("Failed to parse JSON response from the API.")

def get_gene_data(gene_query, genome_build='GRCh38', transcript_set='all', limit_transcripts='all'):
    """
    Fetches gene data from the VariantValidator API.
    """
    # Encode URL components
    encoded_gene_query = quote(gene_query)
    encoded_transcript_set = quote(transcript_set)
    encoded_limit_transcripts = quote(limit_transcripts)
    encoded_genome_build = quote(genome_build)

    url = (
        f"{__init__()}/"
        f"{encoded_gene_query}/"
        f"{encoded_limit_transcripts}/"
        f"{encoded_transcript_set}/"
        f"{encoded_genome_build}"
    )

    return _check_response(url)

def parse_to_bed(gene_query, genome_build='GRCh38', transcript_set='all', limit_transcripts='mane_select'):
    """
    Fetches gene data from the API and converts it to BED format.
    """
    limit_transcripts_map = {
        'mane_select + mane_plus_clinical': 'mane',
        'mane_select': 'mane_select',
        'canonical': 'select'
    }
    limit_transcripts = limit_transcripts_map.get(limit_transcripts, limit_transcripts)

    try:
        gene_data = get_gene_data(
            gene_query=gene_query,
            genome_build=genome_build,
            transcript_set=transcript_set,
            limit_transcripts=limit_transcripts
        )
    except VarValAPIError as e:
        raise VarValAPIError(f"Error fetching data for gene '{gene_query}': {str(e)}")

    # Ensure we got a list
    if not isinstance(gene_data, list):
        raise VarValAPIError(f"Unexpected response format for gene '{gene_query}': Expected a list.")

    # Check if the first element contains an error key
    if len(gene_data) > 0 and 'error' in gene_data[0]:
        error_msg = gene_data[0].get('error', 'Unknown error')
        # This indicates a 200 OK with an "error" key in the response.
        raise VarValAPIError(f"API returned an error for gene '{gene_query}': {error_msg}")

    bed_rows = []
    for gene in gene_data:
        transcripts = gene.get('transcripts', [])
        # If no transcripts, create a NoRecord line
        if not transcripts:
            bed_rows.append({
                'chrom': "NoRecord",
                'start': "NoRecord",
                'end': "NoRecord",
                'name': f"{gene.get('current_symbol', gene_query)}_NoRecord",
                'strand': "NoRecord"
            })
            continue

        if 'annotations' not in transcripts[0] or 'chromosome' not in transcripts[0]['annotations']:
            raise VarValAPIError(f"Unexpected transcript data format for gene '{gene_query}'.")

        chromosome = f"chr{transcripts[0]['annotations']['chromosome']}"

        for transcript in transcripts:
            reference = transcript.get('reference', '.')
            genomic_spans = transcript.get('genomic_spans', {})

            if not genomic_spans:
                # If no genomic_spans, skip this transcript
                continue

            for _, spans in genomic_spans.items():
                orientation = '+' if spans.get('orientation') == 1 else '-'
                exon_structure = spans.get('exon_structure', [])
                for exon in exon_structure:
                    if 'genomic_start' not in exon or 'genomic_end' not in exon or 'exon_number' not in exon:
                        continue
                    bed_rows.append({
                        'chrom': chromosome,
                        'start': exon['genomic_start'],
                        'end': exon['genomic_end'],
                        'name': f"{gene.get('current_symbol', gene_query)}_exon{exon['exon_number']}_{reference}",
                        'strand': orientation
                    })

    return bed_rows

def main():
    bed_data = []
    problem_api_errors = []
    problem_server_errors = []

    with open("genes4bed.txt", "r") as f:
        next(f)  # Skip header line
        for line in f:
            gene = line.strip()
            if not gene:
                continue
            try:
                rows = parse_to_bed(gene)
                bed_data.extend(rows)
            except VarValAPIError as e:
                # Distinguish error types
                error_message = str(e)
                if "API returned an error for gene" in error_message:
                    # API returned a 200 with an error body
                    problem_api_errors.append(gene)
                else:
                    # Other errors: server issues, JSON parsing, etc.
                    problem_server_errors.append(gene)
            except Exception:
                # Any unexpected error
                problem_server_errors.append(gene)

    # Create DataFrame and write to CSV
    df = pd.DataFrame(bed_data)
    df.to_csv("output.csv", index=False)

    # Write problem genes to separate files
    if problem_api_errors:
        with open("problem_genes_api_errors.txt", "w") as api_err_f:
            api_err_f.write("Gene\n")
            for g in problem_api_errors:
                api_err_f.write(g + "\n")

    if problem_server_errors:
        with open("problem_genes_server_errors.txt", "w") as srv_err_f:
            srv_err_f.write("Gene\n")
            for g in problem_server_errors:
                srv_err_f.write(g + "\n")

if __name__ == "__main__":
    main()