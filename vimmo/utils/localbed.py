from vimmo.logger.logging_config import logger
import pandas as pd
from io import BytesIO


def local_bed_formatter(db_records):
    logger.debug(f"Local bed records: {db_records}")
    if db_records:
        bed_rows = []
        for row in db_records:
            bed_rows.append({
                'chrom': row['Chromosome'],
                'chromStart': row['Start'],
                'chromEnd': row['End'],
                'name': row['Name'],
                'strand': row['Strand'],
                'transcript': row['Transcript'],
                'type': row['Type'],
                'hgnc_id': row['HGNC_ID']
            })


        if bed_rows:
            # Convert rows into a DataFrame
            bed_df = pd.DataFrame(bed_rows)
            logger.info(f"Created Dataframe with {len(bed_rows)} rows.")

            # Write the DataFrame to a BED file (BytesIO)
            output = BytesIO()
            bed_string = bed_df.to_csv(
                sep='\t',
                index=False,
                header=False,
                columns=['chrom', 'chromStart', 'chromEnd', 'name', 'strand', 'transcript', 'type', 'hgnc_id']
            )
            output.write(bed_string.encode('utf-8'))
            output.seek(0)
            logger.info("DataFrame successfully written to the bedfile")
            return output
        else:
            # No matching records
            logger.warning("No matching records found to write to BED file")
            return None
    else:
        # No records to process
        logger.warning("No database records found")
        return None