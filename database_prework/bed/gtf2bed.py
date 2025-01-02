import gzip
import pandas as pd
import re

# Input files
hgnc_file = "genes4bed.txt"
annotation_file = "gencode.v37lift37.basic.annotation.gtf.gz"  # Gzipped GTF file
output_bed_file = "genes_exons37.bed"
unmatched_hgnc_file = "unmatched_37_hgnc_ids.txt"

# Load HGNC IDs into a set
with open(hgnc_file, "r") as f:
    hgnc_ids = set(line.strip() for line in f if line.strip())

# Parse GTF file to extract relevant information for HGNC IDs
priority_transcripts = {}
exon_data = {}

with gzip.open(annotation_file, "rt") as f:  # Open gzipped GTF file
    for line in f:
        if line.startswith("#"):  # Skip headers
            continue
        cols = line.strip().split("\t")
        if cols[2] != "exon":  # Only process exons
            continue
        chrom = cols[0]
        start = int(cols[3]) - 1  # Convert to 0-based start
        end = int(cols[4])
        strand = cols[6]
        info = cols[8]

        # Extract relevant tags and fields
        hgnc_id = None
        gene_name = None
        transcript_id = None
        exon_number = None
        is_mane_select = "tag \"MANE_Select\"" in info
        is_mane_plus_clinical = "tag \"MANE_Plus_Clinical\"" in info
        is_canonical = "tag \"Ensembl_canonical\"" in info

        for field in info.split(";"):
            field = field.strip()
            if field.startswith("hgnc_id"):
                hgnc_id = field.split('"')[1]
            elif field.startswith("gene_name"):
                gene_name = field.split('"')[1]
            elif field.startswith("transcript_id"):
                transcript_id = field.split('"')[1]
            elif field.startswith("exon_number"):
                exon_number = field.split()[1]

        # Skip if HGNC ID is not in the gene list
        if hgnc_id not in hgnc_ids:
            continue

        # Initialize storage for this HGNC ID if needed
        if hgnc_id not in exon_data:
            exon_data[hgnc_id] = {}

        # Assign priority to the transcript
        tag_priority = (
            1 if is_mane_select else
            2 if is_mane_plus_clinical else
            3 if is_canonical else
            4  # This value will be excluded
        )

        # Exclude records that are not ms, mpc, or can
        if tag_priority > 3:
            continue

        # Only store the exon if it's the highest-priority transcript for this exon_number
        if exon_number not in exon_data[hgnc_id] or tag_priority < exon_data[hgnc_id][exon_number]["priority"]:
            exon_data[hgnc_id][exon_number] = {
                "chrom": chrom,
                "start": start,
                "end": end,
                "strand": strand,
                "gene_name": gene_name,
                "exon_number": exon_number,
                "transcript_id": transcript_id,
                "priority": tag_priority,
                "source": (
                    "ms" if is_mane_select else
                    "mpc" if is_mane_plus_clinical else
                    "can"
                ),
            }

# Compile filtered exons into a list
filtered_exon_data = []
matched_hgnc_ids = set()

for hgnc_id, exons in exon_data.items():
    matched_hgnc_ids.add(hgnc_id)
    for exon_info in exons.values():
        filtered_exon_data.append((
            exon_info["chrom"],
            exon_info["start"],
            exon_info["end"],
            f"{exon_info['gene_name']}_exon{exon_info['exon_number']}",
            hgnc_id,
            exon_info["transcript_id"],
            exon_info["strand"],
            exon_info["source"]
        ))

# Add unmatched HGNC IDs as `UNK` records
unmatched_hgnc_ids = hgnc_ids - matched_hgnc_ids
unk_records = []
for hgnc_id in unmatched_hgnc_ids:
    unk_records.append((
        "UNK",    # Chromosome
        "NA",     # Start
        "NA",     # End
        "NA",     # Name
        hgnc_id,  # HGNC ID
        "NA",     # Transcript ID
        "NA",     # Strand
        "NA"      # Source
    ))

# Save unmatched HGNC IDs to a file for debugging
with open(unmatched_hgnc_file, "w") as f:
    for hgnc_id in sorted(unmatched_hgnc_ids):
        f.write(hgnc_id + "\n")
print(f"Unmatched HGNC IDs written to {unmatched_hgnc_file}")

# Convert to DataFrame
df = pd.DataFrame(filtered_exon_data, columns=["chrom", "start", "end", "name", "hgnc_id", "transcript_id", "strand", "source"])

# Add `UNK` records to the DataFrame
unk_df = pd.DataFrame(unk_records, columns=df.columns)
df = pd.concat([df, unk_df], ignore_index=True)

# Remove duplicates (if any remain after filtering)
df = df.drop_duplicates(subset=["chrom", "start", "end", "name", "hgnc_id", "transcript_id", "strand", "source"])

# Sort by chromosome order and position, placing `UNK` at the end
def chromosome_sort_key(chrom):
    match = re.match(r'chr(\d+|[XYMT]+)', chrom)
    if match:
        value = match.group(1)
        return (int(value) if value.isdigit() else float('inf'), value)
    return (float('inf'), chrom)  # Place unknown chromosomes at the end

df["chromosome_sort_key"] = df["chrom"].apply(lambda x: chromosome_sort_key(x) if x != "UNK" else (float('inf'), "UNK"))
df = df.sort_values(by=["chromosome_sort_key", "start"]).drop(columns=["chromosome_sort_key"])

# Reorder columns to match desired output
df = df[["chrom", "start", "end", "name", "hgnc_id", "transcript_id", "strand", "source"]]

# Save to BED format
df.to_csv(output_bed_file, sep="\t", header=False, index=False)

print(f"Filtered BED file written to {output_bed_file}")