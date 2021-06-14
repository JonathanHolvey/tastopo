import requests
import functools
from urllib.parse import urljoin


class cachedproperty(object):
    """A decorator which gets a class property once and replaces itself with the property value"""
    def __init__(self, getter):
        self.getter = getter
        functools.update_wrapper(self, getter)

    def __get__(self, obj, cls):
        if obj is None:
            return self

        value = self.getter(obj)
        setattr(obj, self.getter.__name__, value)
        return value


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
