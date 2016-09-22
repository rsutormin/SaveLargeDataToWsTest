# -*- coding: utf-8 -*-
import unittest
import os
import json
import time
import requests
import subprocess

from os import environ
try:
    from ConfigParser import ConfigParser  # py2
except:
    from configparser import ConfigParser  # py3

from pprint import pprint

from biokbase.workspace.client import Workspace as workspaceService
from SaveLargeDataToWsTest.SaveLargeDataToWsTestImpl import SaveLargeDataToWsTest
from SaveLargeDataToWsTest.SaveLargeDataToWsTestServer import MethodContext


class SaveLargeDataToWsTestTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        user_id = requests.post(
            'https://kbase.us/services/authorization/Sessions/Login',
            data='token={}&fields=user_id'.format(token)).json()['user_id']
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'SaveLargeDataToWsTest',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('SaveLargeDataToWsTest'):
            cls.cfg[nameval[0]] = nameval[1]
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = workspaceService(cls.wsURL, token=token)
        cls.serviceImpl = SaveLargeDataToWsTest(cls.cfg)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        if hasattr(self.__class__, 'wsName'):
            return self.__class__.wsName
        suffix = int(time.time() * 1000)
        wsName = "test_SaveLargeDataToWsTest_" + str(suffix)
        ret = self.getWsClient().create_workspace({'workspace': wsName})
        self.__class__.wsName = wsName
        return wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    # NOTE: According to Python unittest naming rules test method names should start from 'test'.
    def test_large_save(self):
        data_dir = "/kb/module/test/data"
        input_file = os.path.join(data_dir, "arab.json.gz")
        subprocess.Popen(["gunzip", input_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()
        input_file = os.path.join(data_dir, "arab.json")
        genome = None
        print("Loading genome object from file into memory...")
        with open(input_file) as f:
            genome = json.load(f)
        print("Loaded!")
        print("Saving it to Workspace...")
        genome_object_name = "genome.1"
        self.getWsClient().save_objects({'workspace': self.getWsName(), 'objects':
                [{ "type":"KBaseGenomes.Genome", "data": genome, "name": genome_object_name}]})
        print("Saved!")
