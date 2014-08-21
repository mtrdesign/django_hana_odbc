from __future__ import absolute_import, division, print_function, unicode_literals
from decimal import Decimal
from django.contrib.gis.db.backends.adapter import WKTAdapter
from django_hana_odbc.operations import DatabaseOperations
from django.contrib.gis.db.backends.util import SpatialFunction
from django.contrib.gis.measure import Distance
from django.utils import six


class GisFunction(SpatialFunction):
    "For SpatiaLite function calls."
    def __init__(self, function, **kwargs):
        super(GisFunction, self).__init__(function, **kwargs)


class GisFunctionParam(GisFunction):
    "For SpatiaLite functions that take another parameter."
    sql_template = '%(function)s(%(geo_col)s, %(geometry)s, %%s)'


class ST_Distance(GisFunction):
    "For SpatiaLite distance operations."
    dist_func = 'ST_Distance'
    sql_template = '%(geo_col)s.%(function)s(%(geometry)s) %(operator)s %%s'

    def __init__(self, operator):
        super(ST_Distance, self).__init__(self.dist_func,
                                          operator=operator)


# Valid distance types and substitutions
dtypes = (Decimal, Distance, float) + six.integer_types


def get_dist_ops(operator):
    return (ST_Distance(operator),)


class GisOperations(DatabaseOperations):
    compiler_module = 'django_hana_odbc.gis.compiler'

    # Avoid an AttributeError in GeoDjango by defining 'oracle'
    oracle = False

    select = '%s.ST_AsText()'
    from_text = 'ST_GeomFromText'

    Adapter = WKTAdapter

    geometry_functions = {
    }

    distance_functions = {
        'distance_gt': (get_dist_ops('>'), dtypes),
        'distance_gte': (get_dist_ops('>='), dtypes),
        'distance_lt': (get_dist_ops('<'), dtypes),
        'distance_lte': (get_dist_ops('<='), dtypes),
    }
    geometry_functions.update(distance_functions)

    def __init__(self, connection):
        super(GisOperations, self).__init__(connection)

        gis_terms = ['isnull']
        gis_terms += list(self.geometry_functions)
        self.gis_terms = dict([(term, None) for term in gis_terms])

    def get_geom_placeholder(self, value, adapter):
        if value and adapter:
            return "{}(%s, {})".format(self.from_text, adapter.srid)
        else:
            return '%s'

    def geo_db_type(self, f):
        geom_type = f.geom_type
        if geom_type != 'POINT':
            raise NotImplementedError('Unsupported geometry type: {}'.format(geom_type))

        return 'ST_POINT({})'.format(f.srid)

    def spatial_ref_sys(self):
        from django_hana_odbc.gis.models import SpatialRefSys
        return SpatialRefSys


    def get_distance(self, f, value, lookup_type):
        """
        (A concoction of the SpatiaLite and PostGIS adapter code.)

        Assuming ST_Distance will return the distance in meters.
        """
        if not value:
            return []

        value = value[0]
        geodetic = f.geodetic(self.connection)

        if isinstance(value, Distance):
            if geodetic:
                dist_param = value.m
            else:
                dist_param = getattr(value, Distance.unit_attname(f.units_name(self.connection)))
        else:
            dist_param = value
        return [dist_param]

    def spatial_lookup_sql(self, lvalue, lookup_type, value, field, qn):
        """
        (shamelessly stolen from the SpatiaLite adapter code)

        Returns the HANA-specific SQL for the given lookup value
        [a tuple of (alias, column, db_type)], lookup type, lookup
        value, the model field, and the quoting function.
        """
        alias, col, db_type = lvalue

        # Getting the quoted field as `geo_col`.
        geo_col = '%s.%s' % (qn(alias), qn(col))

        if lookup_type in self.geometry_functions:
            # See if a SpatiaLite geometry function matches the lookup type.
            tmp = self.geometry_functions[lookup_type]

            # Lookup types that are tuples take tuple arguments, e.g., 'relate' and
            # distance lookups.
            if isinstance(tmp, tuple):
                # First element of tuple is the SpatiaLiteOperation instance, and the
                # second element is either the type or a tuple of acceptable types
                # that may passed in as further parameters for the lookup type.
                op, arg_type = tmp

                # Ensuring that a tuple _value_ was passed in from the user
                if not isinstance(value, (tuple, list)):
                    raise ValueError('Tuple required for `%s` lookup type.' % lookup_type)

                # Geometry is first element of lookup tuple.
                geom = value[0]

                # Number of valid tuple parameters depends on the lookup type.
                if len(value) != 2:
                    raise ValueError('Incorrect number of parameters given for `%s` lookup type.' % lookup_type)

                # Ensuring the argument type matches what we expect.
                if not isinstance(value[1], arg_type):
                    raise ValueError('Argument type should be %s, got %s instead.' % (arg_type, type(value[1])))

                # For lookup type `relate`, the op instance is not yet created (has
                # to be instantiated here to check the pattern parameter).
                if lookup_type == 'relate':
                    op = op(value[1])
                elif lookup_type in self.distance_functions:
                    op = op[0]
            else:
                op = tmp
                geom = value
            # Calling the `as_sql` function on the operation instance.
            return op.as_sql(geo_col, self.get_geom_placeholder(field, geom))
        elif lookup_type == 'isnull':
            # Handling 'isnull' lookup type
            return "%s IS %sNULL" % (geo_col, (not value and 'NOT ' or ''))

        raise TypeError("Got invalid lookup_type: %s" % repr(lookup_type))
