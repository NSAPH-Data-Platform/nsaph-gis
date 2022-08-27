"""
This module contains Enums used by configuration for
processing of GIS information
"""

from enum import Enum


class RasterizationStrategy(Enum):
    """
    Rasterization Strategy, see details at
    https://pythonhosted.org/rasterstats/manual.html#rasterization-strategy
    """

    default = 'default'
    """
    The default strategy is to include all pixels along the line render path
    (for lines), or cells where the center point is within the polygon
    (for polygons).
    """

    all_touched = 'all_touched'
    """
    Alternate, all_touched strategy, rasterizes the geometry
    by including all pixels that it touches.
    """

    combined = 'combined'
    """
    Calculate statistics using both default and all_touched strategy and
    combine results, e.g. using arithmetic means
    """

    downscale = 'downscale'
    """
    A combination of "default" rasterization strategy with 
    affine transformation with downscaling factor = 5
    
    See get_affine_transform `../../../gridmet/doc/gridmet_tools.html#gridmet.gridmet_tools.get_affine_transform`
    """


class Geography(Enum):
    """Type of geography"""
    zip = 'zip'
    county = 'county'
    custom = 'custom'
