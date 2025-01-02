import sqlite3
import pandas as pd

# 1. Load CSV files into pandas DataFrames
csv1 = 'latest_panel_versions.csv'  # Should have columns: [Panel_ID, rcodes, Version]
csv2 = 'genes.csv'                  # Should have columns for referencing: [Panel_ID, rcodes, HGNC ID, Confidence, etc.]
bed_file_37 = 'genes_exons37.bed'
bed_file_38 = 'genes_exons38.bed'
csv3 = 'patient_info.csv'           # Should have columns: [Patient_ID, Panel_ID, rcodes, Version, Date]
csv4 = 'archived_data.csv'          # Should have columns: [Panel_ID, rcodes, Version, Confidence]

df_panel = pd.read_csv(csv1)
df_panel_genes_raw = pd.read_csv(csv2)
df_bed38 = pd.read_csv(bed_file_38, sep='\t', header=None, names=[
    'Chromosome', 'Start', 'End', 'Name', 'HGNC_ID', 'Transcript', 'Strand', 'Type'
])
df_bed37 = pd.read_csv(bed_file_37, sep='\t', header=None, names=[
    'Chromosome', 'Start', 'End', 'Name', 'HGNC_ID', 'Transcript', 'Strand', 'Type'
])
df_patient_info = pd.read_csv(csv3)
df_archived_data = pd.read_csv(csv4)

# 2. Connect to SQLite database and enable foreign key enforcement
conn = sqlite3.connect('../../vimmo/db/panels_data.db')
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

# 3. Drop tables if you want a clean slate (optional)
# cursor.execute("DROP TABLE IF EXISTS panel;")
# cursor.execute("DROP TABLE IF EXISTS panel_genes;")
# ... etc.

# 4. Create tables with composite PK (Panel_ID, rcodes)

# Table 1: panel
cursor.execute('''
CREATE TABLE IF NOT EXISTS panel (
    Panel_ID INTEGER,
    rcodes TEXT,
    Version TEXT,
    PRIMARY KEY (Panel_ID, rcodes)
)
''')

# Table 2: panel_genes
cursor.execute('''
CREATE TABLE IF NOT EXISTS panel_genes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Panel_ID INTEGER,
    rcodes TEXT,
    HGNC_ID TEXT,
    Confidence INTEGER,
    FOREIGN KEY (Panel_ID, rcodes) REFERENCES panel (Panel_ID, rcodes)
)
''')

# Table 3: genes_info
cursor.execute('''
CREATE TABLE IF NOT EXISTS genes_info (
    HGNC_ID TEXT PRIMARY KEY,
    Gene_ID TEXT,
    HGNC_symbol TEXT,
    Gene_Symbol TEXT,
    GRCh38_Chr TEXT,
    GRCh38_start INTEGER,
    GRCh38_stop INTEGER,
    GRCh37_Chr TEXT,
    GRCh37_start INTEGER,
    GRCh37_stop INTEGER
)
''')

# Table 4: patient_data
cursor.execute('''
CREATE TABLE IF NOT EXISTS patient_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT,
    Panel_ID INTEGER,
    rcodes TEXT,
    panel_version TEXT,
    date DATE,
    FOREIGN KEY (Panel_ID, rcodes) REFERENCES panel (Panel_ID, rcodes)
)
''')

# Table 5: bed38
cursor.execute('''
CREATE TABLE IF NOT EXISTS bed38 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Chromosome TEXT,
    Start INTEGER,
    End INTEGER,
    Name TEXT,
    HGNC_ID TEXT,
    Transcript TEXT,
    Strand TEXT,
    Type TEXT,
    FOREIGN KEY (HGNC_ID) REFERENCES genes_info (HGNC_ID)
)
''')

# Table 6: bed37
cursor.execute('''
CREATE TABLE IF NOT EXISTS bed37 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Chromosome TEXT,
    Start INTEGER,
    End INTEGER,
    Name TEXT,
    HGNC_ID TEXT,
    Transcript TEXT,
    Strand TEXT,
    Type TEXT,
    FOREIGN KEY (HGNC_ID) REFERENCES genes_info (HGNC_ID)
)
''')

# Table 7: panel_genes_archive
cursor.execute('''
CREATE TABLE IF NOT EXISTS panel_genes_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Panel_ID INTEGER,
    rcodes TEXT,
    Version TEXT,
    Confidence INTEGER,
    FOREIGN KEY (Panel_ID, rcodes) REFERENCES panel (Panel_ID, rcodes)
)
''')

# 5. Populate Table 1: panel
#    Ensure df_panel has columns [Panel_ID, rcodes, Version]
df_panel.to_sql('panel', conn, if_exists='replace', index=False)

# 6. Populate Table 3: genes_info with unique gene entries
#    (unchanged, same idea you had before)
df_genes_info = df_panel_genes_raw[[
    'HGNC ID', 'Gene ID', 'HGNC symbol', 'Gene Symbol',
    'GRCh38 Chr', 'GRCh38 start', 'GRCh38 stop',
    'GRCh37 Chr', 'GRCh37 start', 'GRCh37 stop'
]].drop_duplicates()

df_genes_info.columns = [
    'HGNC_ID', 'Gene_ID', 'HGNC_symbol', 'Gene_Symbol',
    'GRCh38_Chr', 'GRCh38_start', 'GRCh38_stop',
    'GRCh37_Chr', 'GRCh37_start', 'GRCh37_stop'
]
df_genes_info.to_sql('genes_info', conn, if_exists='replace', index=False)

# 7. Populate Table 2: panel_genes
#    Make sure your CSV has columns [Panel ID, rcodes, HGNC ID, Confidence]
#    so we can rename them to match the DB columns:
df_panel_genes = df_panel_genes_raw[['Panel ID', 'HGNC ID', 'Confidence']].copy()
df_panel_genes.columns = ['Panel_ID', 'HGNC_ID', 'Confidence']
df_panel_genes.to_sql('panel_genes', conn, if_exists='replace', index=False)

# 8. Populate bed38 and bed37
df_bed38['HGNC_ID'] = df_bed38['HGNC_ID'].astype(str).str.strip()
df_bed37['HGNC_ID'] = df_bed37['HGNC_ID'].astype(str).str.strip()
df_bed38.to_sql('bed38', conn, if_exists='replace', index=False)
df_bed37.to_sql('bed37', conn, if_exists='replace', index=False)

# 9. Populate patient_data
#    Must contain columns: [Patient_ID, Panel_ID, rcodes, Version, Date]
#    We rename 'Version' -> 'panel_version'
df_patient_info.columns = ['Patient_ID', 'Panel_ID', 'Rcode', 'Version', 'Date']
df_patient_info.to_sql('patient_data', conn, if_exists='replace', index=False)

# 10. Populate panel_genes_archive
#     Must have columns: [Panel_ID, rcodes, Version, Confidence]
df_archived_data.columns = ['Panel_ID', 'HGNC_ID', 'Version', 'Confidence']
df_archived_data.to_sql('panel_genes_archive', conn, if_exists='replace', index=False)

# 11. Commit and close
conn.commit()
conn.close()
print("Database updated with composite key (Panel_ID, rcodes).")