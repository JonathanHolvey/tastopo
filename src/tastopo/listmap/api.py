import requests
from urllib.parse import urljoin


class ListAPI(requests.Session):
    """A client for the ListMap ArcGIS API"""
    BASE_URL = 'https://services.thelist.tas.gov.au/arcgis/rest/services/'
    DEFAULT_PARAMS = {
        'f': 'json',
    }

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.BASE_URL, url)
        params = {**self.DEFAULT_PARAMS, **kwargs.pop('params', {})}

        response = super().request(method, url, *args, params=params, **kwargs)
        response.raise_for_status()
        return response


# Single instance of API class to allow connection reuse
listapi = ListAPI()
