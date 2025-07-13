from zeep import Client
from typing import Dict, Union
from .consts import WEB_API_URL

client = Client(WEB_API_URL)


def api_get_config(sn: str) -> Union[Dict[str, str], None]:
    response = client.service.SendRequest("QUERY", sn, "CONFIG")
    if response["Msg"] == "OK":
        result = {}
        for line in response["Configs"]["Config"]:
            result[line["Parameter"]] = line["Value"]
        return result
    else:
        return None
