def bed_processor(query, patient_id, r_code, version, args, logger):
    # Create a response object to distinguish between gene queries and messages
    response = {"type": None, "data": None}
    
    if r_code is None:
        patient_records = query.return_all_records(patient_id)
        
        if len(patient_records) >= 2:
            response["type"] = "message"
            response["data"] = {
                "MESSAGE": "Multiple records found",
                "Patient ID": patient_id,
                "patient records": patient_records,
                "Tip": "Please select a panel and version"
            }
            return response
        elif len(patient_records) == 0:
            response["type"] = "message"
            response["data"] = f"Please use the update space as no records were found for {patient_id}"
            return response
        else:
            try:
                # Get the first key (whatever R-code it might be)
                key = next(iter(patient_records))
                first_date_records = patient_records[key]
                
                # Get the first date's data for this R-code
                dated_records = next(iter(first_date_records))
                record_data = first_date_records[dated_records]
                
                r_code = record_data[0]
                version = record_data[1]
                
            except (StopIteration, KeyError, IndexError) as e:
                logger.error(f"Failed to extract record data: {e}")
                gene_query = query.get_gene_list(r_code)
                response["type"] = "Error"
                response["data"] = e
                return response
            
    elif r_code and not version:
        patient_records = query.return_all_records(patient_id)
    
        # Filter records matching the given r_code
        matching_records = []
        for _, values in patient_records.items():
            for date,details in values.items():
                if details[0] == r_code:
                    matching_records.append([date,details])

        if matching_records:
            unique_versions = {details[1][1] for details in matching_records}
            
            if len(unique_versions) > 1:
                response["type"] = "message"
                response["data"] = f"{len(matching_records)} records were found for {r_code} with multiple versions: {', '.join(map(str, sorted(unique_versions)))}. Please specify the version."
                return response
            else:
                version = next(iter(unique_versions))
        else:
            logger.info(f"no records for {args}")
            response["type"] = "message"
            response["data"] = {f"{r_code}": "No record found for this panel"}
            return response
        
    else:
        patient_records = query.return_all_records(patient_id)
        if len(patient_records) > 1:
            # Get all versions for comparison
            patient_record_version = None
            for record_num in patient_records:
                date_record = next(iter(patient_records[record_num]))
                record_data = patient_records[record_num][date_record]
                current_version = record_data[1]
                if str(current_version) == str(version):
                    patient_record_version = current_version

        else:
            key = next(iter(patient_records))
            first_date_records = patient_records[key]
            
            # Get the first date's data for this R-code
            dated_records = next(iter(first_date_records))
            record_data = first_date_records[dated_records]
            patient_record_version = record_data[1]


        if not str(version) == str(patient_record_version):
            response["type"] = "message"
            response["data"] = {f"{r_code}": f"No record found for this panel for Patient ID {patient_id}, please check version"}
            return response

        
    database_version = query.get_db_latest_version(r_code)
    if str(database_version) != str(version):
        panel_ids = query.rcode_to_panelID(Rcode=r_code)
        archived_records = query.historic_panel_retrieval(panelID=panel_ids, version=version)
        gene_query = [hgnc for hgnc, confidence in archived_records.items() if confidence == 3]

        if not gene_query:
            logger.debug(f"records not found for {panel_ids},{archived_records},{gene_query}")
            response["type"] = "message"
            response["data"] = "Sorry provided version does not have any records. Provide a valid version by checking in patient space"
            return response
            
        response["type"] = "gene_query"
        response["data"] = gene_query
        return response
    else:
        panel_ids = query.get_panels_by_rcode(rcode=r_code)
        if "Message" in panel_ids:
            logger.info(f"Missing panel IDs for {r_code}:{panel_ids}")
            response["type"] = "message"
            response["data"] = panel_ids
            return response
        else:
            gene_query = {record["HGNC_ID"] for record in panel_ids["Associated Gene Records"] if record["Confidence"] == 3}
            response["type"] = "gene_query"
            response["data"] = gene_query
            return response
