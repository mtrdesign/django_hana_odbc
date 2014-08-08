from __future__ import absolute_import, division, print_function, unicode_literals
from django.contrib.gis.db.backends.adapter import WKTAdapter
from django_hana_odbc.operations import DatabaseOperations


class GisOperations(DatabaseOperations):
    compiler_module = 'django_hana_odbc.gis.compiler'

    # Avoid an AttributeError in GeoDjango by defining 'oracle'
    oracle = False

    select = '%s.ST_AsText()'
    from_text = 'ST_GeomFromText'

    Adapter = WKTAdapter

    def get_geom_placeholder(self, value, adapter):
        return "{}(%s, {})".format(self.from_text, adapter.srid)

    def geo_db_type(self, f):
        geom_type = f.geom_type
        if geom_type != 'POINT':
            raise NotImplementedError('Unsupported geometry type: {}'.format(geom_type))

        return 'ST_POINT({})'.format(f.srid)
