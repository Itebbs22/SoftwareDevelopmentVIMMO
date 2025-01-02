import requests
import logging
import os
from database_prework.createdb.get_version import extract_rcodes

from db import Database

def fetch_latest_versions(api_url):
    """
    Fetches the latest panel versions from a paginated API.

    Args:
        api_url (str): The initial URL of the API (page 1) to fetch panel versions.

    Returns:
        latest_versions: A dictionary where the keys are panel IDs and the values are their latest versions.
    """
    latest_versions = []

    while api_url:
        try:
            # Send GET request to the API
            response = requests.get(api_url)
            response.raise_for_status()  # Raise an error for HTTP issues
            data = response.json()  # Parse JSON response
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from API: {e}")
            break

        # Process results in the current page
        results = data.get("results", [])
        for item in results:
            try:
                panel_id = item.get("id")
                version = float(item.get("version"))  # Convert version to a float for comparison with current version
                r_code = item.get("relevant_disorders", [])
                r_code = ", ".join(extract_rcodes(r_code))
                latest_versions.append([panel_id, r_code, version])
            except ValueError as e:
                logging.warning(f"Skipping invalid version for panel {item.get('id')}: {e}")

        # Move to the next page if available
        api_url = data.get("next")

    logging.info(f"Fetched {len(latest_versions)} panels from PanelApp API.")
    return latest_versions

def fetch_latest_version_genes(id, latest_version):
    latest_genes = []

    genes_url = f"https://panelapp.genomicsengland.co.uk/api/v1/panels/{id}/?format=json&version={latest_version}"

    try:
        # Send GET request to the API
        response = requests.get(genes_url)
        response.raise_for_status()  # Raise an error for HTTP issues
        data = response.json()  # Parse JSON response
        panel_genes = data.get("genes")
        for gene in panel_genes:
            hgnc_id = gene['gene_data']['hgnc_id']
            confidence = gene['confidence_level']
            latest_genes.append([id, hgnc_id, confidence])

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching latest genes from API: {e}")


    return latest_genes


def update_or_insert_panel_versions(cursor, latest_versions):
    """
    Updates or inserts panel versions in the database, archives genes in the current version and adds the latest genes to
    panel_genes.

    Args:
        cursor: SQLite database cursor for executing queries.
        latest_versions (list): A list of lists, where each sublist contains [panel_id, r_code, version].

    Returns:
        bool: True if any updates or inserts were made, False otherwise.
    """
    updates = False

    for panel_info in latest_versions:
        panel_id, r_code, latest_version = panel_info  # Unpack the sublist

        # Check if the panel already exists in the database
        cursor.execute('SELECT Panel_ID, Version FROM panel WHERE Panel_ID = ?', (panel_id,))
        existing_row = cursor.fetchone()

        if existing_row:
            existing_id, existing_version = existing_row
            # Update version and archive old version genes if it differs
            if existing_version != latest_version:
                latest_genes = fetch_latest_version_genes(panel_id, latest_version)

                # Archive existing genes of the old version
                cursor.execute(
                    '''
                    INSERT INTO panel_genes_archive (Panel_ID, HGNC_ID, Version, Confidence)
                    SELECT Panel_ID, HGNC_ID, ?, Confidence
                    FROM panel_genes
                    WHERE Panel_ID = ?
                    ''',
                    (existing_version, panel_id)
                )

                # Update the panel version
                cursor.execute(
                    'UPDATE panel SET Version = ? WHERE Panel_ID = ?',
                    (latest_version, panel_id)
                )
                logging.info(f"Updated panel {panel_id} from version {existing_version} to version {latest_version}.")
                updates = True

                # Delete the old genes and insert new ones
                cursor.execute('DELETE FROM panel_genes WHERE Panel_ID = ?', (panel_id,))
                cursor.executemany(
                    '''INSERT INTO panel_genes (Panel_ID, HGNC_ID, Confidence) VALUES (?, ?, ?)''',
                    latest_genes
                )

                # Fetch gene changes and log them
                added_genes, removed_genes, confidence_changes = fetch_gene_changes(cursor, panel_id, existing_version)
                logging.info(
                    f"{panel_id} --> {added_genes} added, {removed_genes} removed. Confidence changes: {confidence_changes}")
        else:
            latest_genes = fetch_latest_version_genes(panel_id, latest_version)
            # Insert new panel if it doesn't exist
            cursor.execute(
                'INSERT INTO panel (Panel_ID, rcodes, Version) VALUES (?, ?, ?)',
                (panel_id, r_code, latest_version)
            )
            cursor.executemany(
                '''INSERT INTO panel_genes (Panel_ID, HGNC_ID, Confidence) VALUES (?, ?, ?)''',
                latest_genes
            )
            logging.info(f"Inserted panel {panel_id} with version {latest_version}.")
            updates = True

    if not updates:
        logging.info("0 updates made.")
    return updates

def fetch_gene_changes(cursor, panel_id, old_version):
    # Fetch genes from the old version
    cursor.execute(
        '''
        SELECT HGNC_ID, Confidence
        FROM panel_genes_archive
        WHERE Panel_ID = ? AND Version = ?
        ''',
        (panel_id, old_version)
    )
    old_version_genes = {row['HGNC_ID']: row['Confidence'] for row in cursor.fetchall()}  # Map of HGNC_ID to Confidence

    # Fetch genes from the new version
    cursor.execute(
        '''
        SELECT HGNC_ID, Confidence
        FROM panel_genes
        WHERE Panel_ID = ? 
        ''',
        (panel_id,)
    )
    new_version_genes = {row['HGNC_ID']: row['Confidence'] for row in cursor.fetchall()}  # Map of HGNC_ID to Confidence

    # Identify added genes (present in new but not in old)
    added_genes = [
        (hgnc_id, confidence) for hgnc_id, confidence in new_version_genes.items()
        if hgnc_id not in old_version_genes
    ]

    # Identify removed genes (present in old but not in new)
    removed_genes = [
        (hgnc_id, confidence) for hgnc_id, confidence in old_version_genes.items()
        if hgnc_id not in new_version_genes
    ]

    # Identify confidence changes (same HGNC_ID but different Confidence)
    confidence_changed = [
        (hgnc_id, old_version_genes[hgnc_id], new_version_genes[hgnc_id])
        for hgnc_id in old_version_genes
        if hgnc_id in new_version_genes and old_version_genes[hgnc_id] != new_version_genes[hgnc_id]
    ]

    return added_genes, removed_genes, confidence_changed



def main():
    """
    Main function to coordinate fetching panel versions and updating the database.
    """

    # Determine the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the log file path
    log_file = os.path.join(script_dir, 'logs', 'cron_panel_updates.log')

    # Ensure the logs directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Configure logging to log to both file and console
    logging.basicConfig(
        filename=log_file, # commented out for now as the cron job will redirect stdout to
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add console handler for logging

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    logging.info("Starting the panel update process.")

    # URL for the latest signed off panel versions API endpoint
    api_url = "https://panelapp.genomicsengland.co.uk/api/v1/panels/signedoff/?display=latest&page=1"

    # Initialize and connect to the database
    db = Database()
    db.connect()

    # Fetch latest versions from the API
    latest_versions = fetch_latest_versions(api_url)

    # Get a cursor for database operations
    cursor = db.conn.cursor()

    # Update or insert panel versions
    updates_made = update_or_insert_panel_versions(cursor, latest_versions)


    # Commit changes and close the database connection
    db.conn.commit()
    db.close()

    logging.info("Completed the panel update process.\n")


if __name__ == "__main__":

    main()