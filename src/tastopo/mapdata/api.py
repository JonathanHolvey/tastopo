from urllib.parse import urljoin

import requests


class Client(requests.Session):
    """An HTTP client"""
    def __init__(self, url, params):
        super().__init__()
        self.base_url = url
        self.default_params = params

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.base_url, url)
        params = {**self.default_params, **kwargs.pop('params', {})}

        response = super().request(method, url, *args, params=params, **kwargs)
        response.raise_for_status()
        return response


listapi = Client(
    'https://services.thelist.tas.gov.au/arcgis/rest/services/',
    {'f': 'json'}
)

magapi = Client(
    'https://www.ngdc.noaa.gov/geomag-web/calculators/',
    {'resultFormat': 'json'}
)
