"""
This module processes layers of data containing geographic coordinates
and observed values for a certain parameter (band)
and returns records containing
an identifier for a geographic shape and the value of the band
aggregated over the shape.
"""

#  Copyright (c) 2021. Harvard University
#
#  Developed by Research Software Engineering,
#  Faculty of Arts and Sciences, Research Computing (FAS RC)
#  Author: Michael A Bouzinier
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

import rasterio
from rasterstats import zonal_stats
from tqdm import tqdm

from .constants import RasterizationStrategy, Geography

NO_DATA = -999  # I do not know what it is, but not setting it causes a warning


@dataclass
class Record:
    mean: Optional[float]
    prop: str


class StatsCounter:
    @classmethod
    def process(
        cls,
        strategy: RasterizationStrategy,
        shapefile: str,
        affine: rasterio.Affine,
        layer: Iterable,
        geography: Geography
    ) -> Iterable[Record]:
        non_all_touched_strategies = [
            RasterizationStrategy.default,
            RasterizationStrategy.combined,
            RasterizationStrategy.downscale,
        ]
        all_touched_strategies = [
            RasterizationStrategy.all_touched,
            RasterizationStrategy.combined,
        ]
        """
        Given a layer, i.e. a slice of a dataframe, and a shapefile 
        returns an iterable of records, containing aggregated values
        of the observations over the shapes in the shapefile. 
        
        :param strategy: Rasterization strategy to be used
        :param shapefile: A path to shapefile to be used
        :param affine: An optional affine transformation to be applied to
            the coordinates
        :param layer: A slice of dataframe, containing coordinates and values
        :param geography: WHat type of geography is to be used: zip codes
            or counties
        :return: An iterable of records, containing an identifier
            of a certain shape with the aggregated value of teh observation
            for this shape
        """

        stats = []
        if strategy in non_all_touched_strategies:
            stats.append(
                zonal_stats(
                    shapefile,
                    layer,
                    stats="mean",
                    affine=affine,
                    geojson_out=True,
                    all_touched=False,
                    nodata=NO_DATA,
                )
            )
        if strategy in all_touched_strategies:
            stats.append(
                zonal_stats(
                    shapefile,
                    layer,
                    stats="mean",
                    affine=affine,
                    geojson_out=True,
                    all_touched=True,
                    nodata=NO_DATA,
                )
            )

        if not len(stats[0]):
            return

        row = stats[0][0]
        if geography == Geography.zip:
            key = cls._determine_zip_key(row)
        elif geography == Geography.county:
            key = cls._determine_county_key(row)
        else:
            raise ValueError("Unsupported geography: " + str(geography))

        for i in tqdm(range(len(stats[0])), total=len(stats[0])):
            if len(stats) == 2:
                # Combined strategy
                mean, prop = cls._combine(key, stats[0][i], stats[1][i])

            else:
                mean = stats[0][i]['properties']['mean']
                props = [stats[0][i]['properties'][subkey] for subkey in key]
                prop = "".join(props)

            yield Record(mean=mean, prop=prop)

    @classmethod
    def _determine_zip_key(cls, row) -> Tuple:
        candidates = ("ZIP", "ZCTA5", "ZCTA5CE10", "ZCTA5CE20")
        return cls._determine_key(row, candidates),

    @classmethod
    def _determine_county_key(cls, row) -> Tuple:
        candidates = ["COUNTY", "COUNTYFP"]
        c = cls._determine_key(row, candidates)
        s = cls._determine_key(row, ["STATE", "STATEFP"])
        return s, c

    @staticmethod
    def _determine_key(row, candidates) -> str:
        for candidate in candidates:
            if candidate in row['properties']:
                return candidate
        raise ValueError(f"Unknown shape format, no expected fields '{ candidates }'")

    @staticmethod
    def _combine(key, r1, r2) -> Record:
        prop1 = "".join([r1['properties'][subkey] for subkey in key])
        prop2 = "".join([r2['properties'][subkey] for subkey in key])
        assert prop1 == prop2

        m1 = r1['properties']['mean']
        m2 = r2['properties']['mean']
        if m1 and m2:
            mean = (m1 + m2) / 2
        elif m2:
            mean = m2
        elif m1:
            raise AssertionError("m1 && !m2")
        else:
            mean = None
        return Record(mean=mean, prop=prop1)
