from __future__ import absolute_import, division, print_function, unicode_literals
from django_hana_odbc.base import *
from django_hana_odbc.base import DatabaseWrapper as NonGisDatabaseWrapper
from django_hana_odbc.gis.creation import GisCreation
from django_hana_odbc.gis.introspection import GisIntrospection
from django_hana_odbc.gis.operations import GisOperations


class DatabaseWrapper(NonGisDatabaseWrapper):
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.creation = GisCreation(self)
        self.ops = GisOperations(self)
        self.introspection = GisIntrospection(self)
