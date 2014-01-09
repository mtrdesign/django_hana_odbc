import os
import sys

from django.core.exceptions import ImproperlyConfigured
from django.db.backends import BaseDatabaseClient

class DatabaseClient(BaseDatabaseClient):
    executable_name = 'isql'

    def runshell(self):
        settings = self.connection.settings_dict

        if not (settings.has_key('DSN') and settings.has_key('USER') and settings.has_key('PASSWORD')):
            raise ImproperlyConfigured('ODBC shell supports only connections via DSN')

        args = [self.executable_name, settings['DSN'], settings['USER'], settings['PASSWORD']]
        os.execvp(self.executable_name, args)
