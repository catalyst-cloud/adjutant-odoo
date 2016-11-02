
from .common import BaseManager


class CloudProjectManager(BaseManager):

    def __init__(self, odooclient):
        self.client = odooclient
        self.resource_env = self.client._Project
