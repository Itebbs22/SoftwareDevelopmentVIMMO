from vimmo.logger.logging_config import logger
import requests

class PanelAppAPIError(Exception):
    """Custom exception for errors related to the PanelApp API."""
    pass


class PanelAppClient:
    def __init__(self, base_url='https://panelapp.genomicsengland.co.uk/api/v1/panels'):
        self.base_url = base_url

    def _check_response(self, url):
        '''
        Checks the HTTP response status code.
        Raises PanelAppAPIError if status code is not 200.
        '''
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            return response.json()
        except requests.ConnectionError as e:
            logger.warning(f"Connection error while accessing PanelApp API: {str(e)}")
            raise PanelAppAPIError(f"Failed to connect to PanelApp API: {str(e)}")
            
        except requests.Timeout as e:
            logger.warning(f"Timeout while accessing PanelApp API: {str(e)}")
            raise PanelAppAPIError(f"Request to PanelApp API timed out: {str(e)}")
            
        except requests.HTTPError as e:
            status_code = response.status_code
            logger.warning(f"HTTP {status_code} error from PanelApp API: {str(e)}")
            raise PanelAppAPIError(f"PanelApp API returned HTTP {status_code}: {str(e)}")
            
        except ValueError as e:
            logger.warning(f"Invalid JSON response from PanelApp API: {str(e)}")
            raise PanelAppAPIError(f"Failed to parse JSON response from PanelApp API: {str(e)}")
            
        except Exception as e:
            logger.warning(f"Unexpected error while accessing PanelApp API: {str(e)}")
            raise PanelAppAPIError(f"Unexpected error occurred: {str(e)}")


    def get_genes_HUGO(self, rcode):
        '''
        Query PanelApp API based on RCode --> return list of genes (HUGO gene symbols) with a specified confidence level.
        '''
        url = f'{self.base_url}/{rcode}/genes/'
        json_data = self._check_response(url)
        gene_symbols = [entry["gene_data"]["gene_symbol"] for entry in json_data.get("results", [])]
        return gene_symbols
    
    def get_genes_HGNC(self, rcode):
        """
        Query PanelApp API base on Rcode --> return list of genes (HGNC id) with a specified confidence level.
        """
        url = f'{self.base_url}/{rcode}/genes/'
        json_data = self._check_response(url)
        
        hgnc_confidence_dict = {
        entry["gene_data"]["hgnc_id"]: entry["confidence_level"]
         for entry in json_data.get("results", [])
        }
        return hgnc_confidence_dict

    def get_latest_online_version(self, panel_id: str) -> str: 
        """
        Returns the most recent signedoff panel version from the panelapp api

        Parameters
        ----------
        panel_id : str
        The panel to search for in the panelapp database

        Returns
        -------
        version: str
        The latest  version for the most recent GMS signedoff panelapp panel

        Notes
        -----
        - This function substitues the input panel id into the signedoff URL
        - Using the response module, sends and recieves a GET HTTP request and response
        - It extracts the .json response format
        - Indexs the results nested dictionary, and extracts the 'version'

        Example
        -----
        User UI input: R208
        Query class method: rcode_to_panelID(R208) -> 635 # converts rcode to panel_id (see db.py)
        get_latest_online_version(635) -> 2.5
        
        Here 2.5 is the version of R208, as of (26/11/24)
        """
        
        url = f'{self.base_url}/signedoff/?panel_id={panel_id}&display=latest' # Set the URL 
        json_data = self._check_response(url) # Send get request to URL, if 200 return json format of the response
        
        try:
        # Safely extract the version
            version_value = json_data["results"][0]["version"] # Extract the version number from the json response
            version = float(version_value)

        except:
            return KeyError({"Error":"Invalid or missing rcode. Please check the R code at 'https://panelapp.genomicsengland.co.uk/panels/'"})

        else:
            return version

    def get_latest_online_version(self, panel_id: str) -> str:
        """
        Returns the most recent signedoff panel version from the panelapp api

        Parameters
        ----------
        panel_id : str
        The panel to search for in the panelapp database

        Returns
        -------
        version: str
        The latest  version for the most recent GMS signedoff panelapp panel

        Notes
        -----
        - This function substitutes the input panel id into the signedoff URL
        - Using the response module, sends and receives a GET HTTP request and response
        - It extracts the .json response format
        - Indexes the results nested dictionary, and extracts the 'version'

        Example
        -----
        User UI input: R208
        Query class method: rcode_to_panelID(R208) -> 635 # converts rcode to panel_id (see db.py)
        get_latest_online_version(635) -> 2.5
        """
        logger.info(f"Starting get_latest_online_version for panel_id: {panel_id}")

        url = f'{self.base_url}/signedoff/?panel_id={panel_id}&display=latest'  # Set the URL
        logger.info(f"Constructed URL Panel app API: {url}")
        json_data = self._check_response(url)  # Send get request to URL, if 200 return json format of the response
        logger.info(f"Successfully retrieved JSON data for panel_id: {panel_id}")

        try:
            # Check if 'results' is empty
            if not json_data.get("results"):
                raise KeyError(f"Error: No results found for panel_id: {panel_id}")

            # Extract the version from the first result
            version_value = json_data["results"][0]["version"]
            version = float(version_value)
            logger.info(f"Extracted version: {version} for panel_id: {panel_id}")
            return version

        except KeyError as e:
            logger.warning(f"Invalid or missing version key in response for panel_id: {panel_id}")
            raise e

        except IndexError as e:
            # Handle the case where 'results' is an empty list
            logger.warning(f"No results found for panel_id: {panel_id}")
            raise KeyError(f"Error: No results found for panel_id: {panel_id}")

        except Exception as e:
            logger.warning(f"Unexpected error: {str(e)}")
            raise Exception(f"Unexpected error occurred: {str(e)}")


    def dowgrade_records(self, panel_id: str, version:str ) -> str: 
        """
        Returns the most recent signedoff panel version from the panelapp api

        Parameters
        ----------
        panel_id : str
        The panel to search for in the panelapp database

        Returns
        -------
        version: str
        The latest  version for the most recent GMS signedoff panelapp panel

        Notes
        -----
        - This function substitues the input panel id into the signedoff URL
        - Using the response module, sends and recieves a GET HTTP request and response
        - It extracts the .json response format
        - Indexs the results nested dictionary, and extracts the 'version'

        Example
        -----
        User UI input: R208
        Query class method: rcode_to_panelID(R208) -> 635 # converts rcode to panel_id (see db.py)
        get_latest_online_version(635) -> 2.5
        
        Here 2.5 is the version of R208, as of (26/11/24)
        """
        try:
            url = f'{self.base_url}/{panel_id}/?version={version}' # Set the URL
            logger.info(f"requesting data from endpoint: {url}")
            json_data = self._check_response(url) # Send get request to URL, if 200 return json format of the response
            logger.info(f"Successfully fetched data for panel_id: {panel_id}, version: {version}")
            return json_data
        except Exception as err:
            logger.error(f"Failed to fetch data for panel_id: {panel_id}, version: {version}. {err}" )
            raise Exception
