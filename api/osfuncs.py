import requests

def parse_opensea_resp(openSeaResp):
    title = "🚫Not Found"
    address = "🚫Not Found"
    floor = 0
    imageUrl = "https://i.seadn.io/gcs/files/b9210a9b845b331a654ec9a05a48d785.png?auto=format&w=500"
    try:
        if openSeaResp["collection"]["primary_asset_contracts"][0]["name"]:
            title = openSeaResp["collection"]["primary_asset_contracts"][0]["name"]
        if openSeaResp["collection"]["primary_asset_contracts"][0]["address"]:
            address = openSeaResp["collection"]["primary_asset_contracts"][0]["address"]
        if openSeaResp["collection"]["stats"]["floor_price"]:
            floor = openSeaResp["collection"]["stats"]["floor_price"]
        if openSeaResp["collection"]["primary_asset_contracts"][0]["image_url"]:
            imageUrl = openSeaResp["collection"]["primary_asset_contracts"][0]["image_url"]

        return [title, address, floor, imageUrl]
    except Exception as e:
        # print(e)
        try:
            if openSeaResp["collection"]["name"]:
                title = openSeaResp["collection"]["name"]
            if openSeaResp["collection"]["address"]:
                address = openSeaResp["collection"]["address"]
            if openSeaResp["collection"]["stats"]["floor_price"]:
                floor = openSeaResp["collection"]["stats"]["floor_price"]
            if openSeaResp["collection"]["image_url"]:
                imageUrl = openSeaResp["collection"]["image_url"]
            return [title, address, floor, imageUrl]
        except Exception as e:
            raise Exception('Wrong URL')
            return None

def opensea_collection_api(slug):
    request_session = requests.session()
    request_session.keep_alive = False
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    openSeaResp = requests.get(
        'https://api.opensea.io/api/v1/collection/'+slug, headers=headers)

    openSeaResp = openSeaResp.json()
    
    # if it has success key it's wrong
    if 'success' in openSeaResp.keys():
        return {'success': False}

    try:
        return parse_opensea_resp(openSeaResp)
    except:
        return None
    

