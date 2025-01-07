import requests
from urllib.parse import quote
import csv
import time

class VarValAPIError(Exception):
    """Custom exception for errors related to the VariantValidator API."""
    pass

def __init__(base_url='https://rest.variantvalidator.org/VariantValidator/tools/gene2transcripts_v2'):
    return base_url

def _check_response(url):
    try:
        response = requests.get(url)
    except requests.RequestException as e:
        raise VarValAPIError(f"Failed to connect. Please check your internet connection and try again: {e}")

    if not response.ok:
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
    try:
        data = response.json()
        return data
    except ValueError:
        raise VarValAPIError("Failed to parse JSON response from the API.")

def get_gene_data(gene_query, genome_build='GRCh38', transcript_set='all', limit_transcripts='all'):
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

    if not isinstance(gene_data, list):
        raise VarValAPIError(f"Unexpected response format for gene '{gene_query}': Expected a list.")

    if len(gene_data) > 0 and 'error' in gene_data[0]:
        error_msg = gene_data[0].get('error', 'Unknown error')
        raise VarValAPIError(f"API returned an error for gene '{gene_query}': {error_msg}")

    bed_rows = []
    for gene in gene_data:
        transcripts = gene.get('transcripts', [])
        # If no transcripts, create a NoRecord line
        if not transcripts or 'annotations' not in transcripts[0] or 'chromosome' not in transcripts[0]['annotations']:
            bed_rows.append({
                'chrom': "NoRecord",
                'start': "NoRecord",
                'end': "NoRecord",
                'name': f"{gene.get('current_symbol', gene_query)}_NoRecord",
                'strand': "NoRecord"
            })
            continue


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
    problem_api_errors = []
    problem_server_errors = []

    # Open the output CSV in append mode and write header once
    with open("output.csv", "w", newline='') as outfile:
        fieldnames = ['chrom', 'start', 'end', 'name', 'strand']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

    with open("genes4bed.txt", "r") as f, \
         open("output.csv", "a", newline='') as outfile:

        writer = csv.DictWriter(outfile, fieldnames=['chrom', 'start', 'end', 'name', 'strand'])
        
        next(f)  # Skip the header line in the input file
        for line in f:
            gene = line.strip()
            if not gene:
                continue
            # Wait 1 second before making the next request to avoid rate limits
            time.sleep(1)
            try:
                rows = parse_to_bed(gene)
                # Write each row as we get it
                for r in rows:
                    writer.writerow(r)
            except VarValAPIError as e:
                print(f"\033[91mX\033[0m Problem with gene: {gene}")
                error_message = str(e)
                if "API returned an error for gene" in error_message:
                    problem_api_errors.append(gene)
                else:
                    problem_server_errors.append(gene)
            except Exception:
                print(f"\033[91mX\033[0m Unexpected error with gene: {gene}")
                problem_server_errors.append(gene)

    # Write problem genes files
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