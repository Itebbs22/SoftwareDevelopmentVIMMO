from db import Database
import random
from scheduled_update import main

'''
This script adds in, removes and changes the confidence of some genes in panels 3 and 9, then calls the main function
from test_weekly_update.py to contact the PanelApp API and update the database, including changing latest version
numbers, latest genes and confidences (in panel_genes) and archiving any previous versions (in panel_genes_archive)

'''


def update_tester(cursor):

    '''
    Function adds in, deletes and changes the confidence of genes in the panel_genes table, so the weekly update
    and archive script can be tested
    '''

    cursor.execute(
        '''
        delete from panel_genes where Panel_ID = 3 and HGNC_ID = 'HGNC:2186'
        '''
    )

    cursor.execute(
        '''
        insert into panel_genes (Panel_ID, HGNC_ID, Confidence) VALUES (3, 'HGNC:44444444', 1)
        '''
    )

    cursor.execute(
        '''
        Update panel_genes set Confidence = 2 where Panel_ID = 3 and HGNC_ID = 'HGNC:2200'
        '''
    )

    cursor.execute(
        '''
        delete from panel_genes where Panel_ID = 9 and HGNC_ID = 'HGNC:3424'
        '''
    )

    cursor.execute(
        '''
        insert into panel_genes (Panel_ID, HGNC_ID, Confidence) VALUES (9, 'HGNC:44444444', 1)
        '''
    )

    cursor.execute(
        '''
        Update panel_genes set Confidence = 2 where Panel_ID = 9 and HGNC_ID = 'HGNC:5211'
        '''
    )

    random_version = round(random.uniform(0.1, 1.0), 3)
    cursor.execute(
        '''
        update panel set Version = ? where Panel_ID = 3
        ''',
        (random_version,)
    )

    cursor.execute(
        '''
        update panel set Version = ? where Panel_ID = 9
        ''',
        (random_version,)
    )

    db.conn.commit()
    db.conn.close()

if __name__ == '__main__':
    db = Database()
    db.connect()
    cursor = db.conn.cursor()
    update_tester(cursor)
    main()