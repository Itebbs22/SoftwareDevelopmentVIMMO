import requests

ID_list = []

for number in range(1,9):
    url=f"https://panelapp.genomicsengland.co.uk/api/v1/panels/signedoff/?display=all&format=json&page=2"
    url = f"https://panelapp.genomicsengland.co.uk/api/v1/panels/?page={number}"
    data = requests.get(url)
    json_data = data.json()
    for entry in json_data.get("results", []):

        
         for item in entry["relevant_disorders"]:
             if item[0]=="R" and item[-1] in ["1","2","3","4","5","6","7","8","9","0"]:
                 ID_list.append([entry['id'],item])
print(len(ID_list))                