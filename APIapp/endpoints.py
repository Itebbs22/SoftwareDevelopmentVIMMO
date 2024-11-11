
from flask_restx import Resource, reqparse
from APIapp import api,get_db
#from database_prework.each_paneld import hgnc_id
from utils.panelapp import  PanelAppClient
from db.db import PanelQuery
import requests

panel_app_client = PanelAppClient()
# Create a RequestParser object to identify specific content-type requests in HTTP URLs
# The requestparser allows us to specify arguements passed via a URL, in this case, ....?content-type=application/json
parser = reqparse.RequestParser()
parser.add_argument('ID',
                    type=str,
                    help='Type in Panel-ID or R code')
parser2 = reqparse.RequestParser()
parser2.add_argument('HGNC_ID', type=str, help='Type in HGNC code')

panels_space = api.namespace('panels', description='Return panel data provided by the user')
@panels_space.route("/panels")
class NameClass(Resource):
    @api.doc(parser=parser)
    def get(self):
        # Parse arguments
        args = parser.parse_args()
        ID = args.get('ID')
        db = get_db()
        query = PanelQuery(db.conn)  # Pass the database connection to PanelQuery
        
        # Determine if input is a Panel_ID (numeric string) or an rcode (contains "R")
        if "R" in ID:
            # Treat as rcode
            panel_data = query.get_panel_data(rcode=ID)
        else:
            # Treat as Panel_ID (since it's purely numeric)
            panel_data = query.get_panel_data(panel_id=ID)
        
        # Return result as JSON
        return {
            "Panel ID or R-code": ID,
            "Associated Gene Records": panel_data
        }

genes_space = api.namespace('genes', description='Return panels containing gene')
@genes_space.route("/genes")
class NameClass(Resource):
    @api.doc(parser=parser2)
    def get(self):
        args = parser2.parse_args()
        hgnc_id = args.get('HGNC_ID')
        db = get_db()
        query = PanelQuery(db.conn)
        panels_returned = query.get_panels_from_gene(hgnc_id=hgnc_id)
        return {
            "HGNC ID": hgnc_id,
            "Panels": panels_returned
        }


    


# VIMMO_space = api.namespace('VIMMO', description='Return a name provided by the user')
# @VIMMO_space.route("/<string:rcode>")
# class NameClass(Resource):
#     @api.doc(parser=parser)
#     def get(self, rcode):
#                 # Collect Arguements
#         args = parser.parse_args()

#         gene_list = panel_app_client.get_genes(rcode)
#         return {
#             f"Paitned ID: {args['Patient-ID ']} List of genes in {rcode}" : gene_list
#         }