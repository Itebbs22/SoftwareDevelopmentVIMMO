from flask_restx import reqparse, inputs

class IDParser:
    """Parser for handling panel ID, Rcode, and HGNC ID arguments."""
    
    @staticmethod
    def create_parser():
        """Create and return a request parser for ID-related arguments."""
        parser = reqparse.RequestParser()
        
        # Argument for Panel_ID
        parser.add_argument(
            'Panel_ID',
            type=str,
            help="Provide Panel_ID. Leave blank if using 'Rcode' or 'HGNC_ID'.",
            required=False
        )
        
        # Argument for Rcode
        parser.add_argument(
            'Rcode',
            type=str,
            help="Provide Rcode. Leave blank if using 'Panel_ID' or 'HGNC_ID'.",
            required=False
        )
        
        # Argument for HGNC_ID
        parser.add_argument(
            'HGNC_ID',
            type=str,
            help="Provide HGNC ID. Leave blank if using 'Rcode' or 'Panel_ID'.",
            required=False
        )
        
        # Argument for Similar_Matches (boolean)
        parser.add_argument(
            'Similar_Matches',
            type=inputs.boolean,
            help="Select true to get similarly matched IDs. Use 'true' or 'false' (case-insensitive).",
            required=False,
            default=False
        )
        
        return parser


class PatientParser:
    """Parser for handling patient-related arguments."""
    
    @staticmethod  
    def upper_rcode(rcode):  # Convert all input Rcodes to upper case
        if isinstance(rcode, str):
            return rcode.upper()
        raise ValueError("Input must be a string.") # Raise error if non str value input
    
    @staticmethod
    def create_parser():
        """Create and return a request parser for patient-related arguments."""
        parser = reqparse.RequestParser()
        
        # Argument for Patient ID
        parser.add_argument(
            'Patient ID',
            type=str,
            help='Type in Patient ID',
            required=False
        )
        
        # Argument for R code
        parser.add_argument(
            'R code',
            type=PatientParser.upper_rcode,
            help='Type in R code',
            required=False
        )
        return parser
    


class PatientBedParser:
    """Parser for handling patient-related arguments."""
    
    @staticmethod
    def create_parser():
        """Create and return a request parser for patient-related arguments."""
        parser = reqparse.RequestParser()
        
        # Argument for Patient ID
        parser.add_argument(
            'Patient ID',
            type=str,
            help='Type in Patient ID',
            required=True
        )
        
        # Argument for R code
        parser.add_argument(
            'R code',
            type=str,
            help='Type in R code',
            required=False
        )

        parser.add_argument(
            'version',
            type=str,
            help='Type in Version',
            required=False
        )
        
        parser.add_argument(
            'genome_build',
            type=str,
            choices=['GRCh37', 'GRCh38'],
            help="Specify the genome build (GRCh37 or GRCh38).",
            required=True,
            default='GRCh38'
        )
        parser.add_argument(
            'transcript_set',
            type=str,
            choices=['refseq', 'ensembl', 'all'],
            help="Specify the transcript set (refseq, ensembl, or all).",
            required=True,
            default='all'
        )
        parser.add_argument(
            'limit_transcripts',
            type=str,
            choices=['mane_select + mane_plus_clinical', 'mane_select', 'canonical'],
            help=(
                "Limit transcripts to specific categories: "
                "'mane_select + mane_plus_clinical' for MANE Select and Mane Plus Clinical, "
                "'mane_select' for MANE Select only, "
                "'canonical' for canonical transcripts."
            ),
            required=True,
            default='mane_select'
        )

        parser.add_argument(
            'Padding',
            type=int,
            help='Please provide a value to pad the bed records by +/- N bp',
            required=False
        )

        return parser
    


class PatientLocalBedParser:
    """Parser for handling patient-related arguments."""
    
    @staticmethod
    def create_parser():
        """Create and return a request parser for patient-related arguments."""
        parser = reqparse.RequestParser()
        
        # Argument for Patient ID
        parser.add_argument(
            'Patient ID',
            type=str,
            help='Type in Patient ID',
            required=True
        )
        
        # Argument for R code
        parser.add_argument(
            'R code',
            type=str,
            help='Type in R code',
            required=False
        )

        parser.add_argument(
            'version',
            type=str,
            help='Type in Version',
            required=False
        )
        
        parser.add_argument(
            'genome_build',
            type=str,
            choices=['GRCh37', 'GRCh38'],
            help="Specify the genome build (GRCh37 or GRCh38).",
            required=True,
            default='GRCh38'
        )
        parser.add_argument(
            'transcript_set',
            type=str,
            choices=['Gencode'],
            help="Only Gencode records can be downloaded from local endpoint.",
            required=True,
            default='Gencode'
        )
        parser.add_argument(
            'limit_transcripts',
            type=str,
            choices=['all'],
            help=(
                "Local endpoint outputs all the records for all available records."
                "Available records are given in priority as follows: "
                "Only Mane_Select is returned for a matching exon if available"
                "Mane_Plus_Clinical is returned if there are no matching exons returned"
                "Canonical records are returned if no Mane_Select and Mane_Plus_Canonical are found"
                "these are indicated in the type encoded as : ms: Mane_Select, mpc: Mane_Plus_Clinical, can: Canonical"
            ),
            required=True,
            default='all'
        )


        return parser
    



class DownloadParser:
    """Parser for handling download-related arguments."""

    @staticmethod
    def create_parser():
        parser = reqparse.RequestParser()

        id_parser = IDParser.create_parser()
        for arg in id_parser.args:
            parser.add_argument(**arg.__dict__)

        # Add additional arguments specific to the download functionality
        parser.add_argument(
            'genome_build',
            type=str,
            choices=['GRCh37', 'GRCh38'],
            help="Specify the genome build (GRCh37 or GRCh38).",
            required=True,
            default='GRCh38'
        )
        parser.add_argument(
            'transcript_set',
            type=str,
            choices=['refseq', 'ensembl', 'all'],
            help="Specify the transcript set (refseq, ensembl, or all).",
            required=True,
            default='all'
        )
        parser.add_argument(
            'limit_transcripts',
            type=str,
            choices=['mane_select + mane_plus_clinical', 'mane_select', 'canonical'],
            help=(
                "Limit transcripts to specific categories: "
                "'mane_select + mane_plus_clinical' for MANE Select and Mane Plus Clinical, "
                "'mane_select' for MANE Select only, "
                "'canonical' for canonical transcripts."
            ),
            required=True,
            default='mane_select'
        )
        parser.add_argument(
            'Confidence',
            choices=['Green', 'Amber', 'Red', 'All'],
            help="Specify the gene confidence to restrict gene relevence.",
            required=True,
            default='All'
        )


        return parser




class LocalDownloadParser:
    """Parser for handling download-related arguments."""

    @staticmethod
    def create_parser():
        parser = reqparse.RequestParser()

        id_parser = IDParser.create_parser()
        for arg in id_parser.args:
            parser.add_argument(**arg.__dict__)

        # Add additional arguments specific to the download functionality
        parser.add_argument(
            'genome_build',
            type=str,
            choices=['GRCh37', 'GRCh38'],
            help="Specify the genome build (GRCh37 or GRCh38).",
            required=True,
            default='GRCh38'
        )
        parser.add_argument(
            'transcript_set',
            type=str,
            choices=['Gencode'],
            help="Only Gencode records can be downloaded from local endpoint.",
            required=True,
            default='Gencode'
        )
        parser.add_argument(
            'limit_transcripts',
            type=str,
            choices=['all'],
            help=(
                "Local endpoint outputs all the records for all available records."
                "Available records are given in priority as follows: "
                "Only Mane_Select is returned for a matching exon if available"
                "Mane_Plus_Clinical is returned if there are no matching exons returned"
                "Canonical records are returned if no Mane_Select and Mane_Plus_Canonical are found"
                "these are indicated in the type encoded as : ms: Mane_Select, mpc: Mane_Plus_Clinical, can: Canonical"
            ),
            required=True,
            default='all'
        )
        parser.add_argument(
            'Confidence',
            choices=['Green', 'Amber', 'Red', 'All'],
            help="Specify the gene confidence to restrict gene relevence.",
            required=True,
            default='All'
        )


        return parser


class UpdateParser:
    """Parser for updating the patient database."""
    
    @staticmethod  
    def upper_rcode(rcode):  # Convert all input Rcodes to upper case
        if isinstance(rcode, str):
            return rcode.upper()
        raise ValueError("Input must be a string.") # Raise error if non str value input
    
    @staticmethod
    def create_parser():
        parser = reqparse.RequestParser()
        
        parser.add_argument(
            'Patient ID',
            type=str,
            help='Type in Patient ID (Required)',
            required = True
        )
        parser.add_argument(
            'R code',
            type=str,
            help='Type in R code (Required)',
            required = True
        )

        return parser



class DowngradeParser:
    """Parser for downgrading the database for a given panel."""
    @staticmethod
    def create_parser():
        parser = reqparse.RequestParser()
        
        parser.add_argument(
            'R_Code',
            type=str,
            help='Type in R Code',
            required = True
        )
        parser.add_argument(
            'version',
            type=str,
            help='type in a previous version',
            required = True
        )

        return parser
