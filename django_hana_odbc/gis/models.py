"""
 The GeometryColumns and SpatialRefSys models for the SpatiaLite backend.
"""
from django.db import models
from django.contrib.gis.db.backends.base import SpatialRefSysMixin
from django.utils.encoding import python_2_unicode_compatible


class SpatialRefSys(models.Model, SpatialRefSysMixin):
    """
    Using a "ST_SPATIAL_REFERENCE_SYSTEMS_COPY" local schema view that copies
    data from the SYS.ST_SPATIAL_REFERENCE_SYSTEMS SYSTEM-only view.
    """
    srid = models.IntegerField(primary_key=True, db_column='SRS_ID')
    ref_sys_name = models.CharField(max_length=256, db_column='SRS_NAME')
    srs_type = models.CharField(max_length=256)
    organization = models.CharField(max_length=256)
    organization_coordsys_id = models.IntegerField()
    linear_unit_of_measure = models.CharField(max_length=256)
    angular_unit_of_measure = models.CharField(max_length=256)
    definition = models.CharField(max_length=2048)
    proj4text = models.CharField(max_length=2048, db_column='TRANSFORM_DEFINITION')

    @property
    def wkt(self):
        from django.contrib.gis.gdal import SpatialReference
        return SpatialReference(self.proj4text).wkt


    class Meta:
        # Make sure you set up your ST_SPATIAL_REFERENCE_SYSTEMS table/view
        # according to the docs.
        db_table = 'ST_SPATIAL_REFERENCE_SYSTEMS_COPY'
        managed = False
