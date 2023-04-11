"""
Utilities to download shapefiles from US Census website
"""

#  Copyright (c) 2022. Harvard University
#
#  Developed by Research Software Engineering,
#  Faculty of Arts and Sciences, Research Computing (FAS RC)
#  Author: Mikhail Polykovsky
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

import os
import zipfile
from enum import Enum
from typing import Tuple
from urllib import request

from tqdm import tqdm



class CensusShapeCollection(Enum):
    genz = 'genz'
    tiger = 'tiger'


class GISDownloader:
    """
    Geographic Downloader downloads shape files for given dates
    from https://www.census.gov/
    """
    COUNTY_TEMPLATE = 'https://www2.census.gov/geo/tiger/GENZ{year}/shp/cb_{year}_us_county_500k.zip'
    ZCTA_GENZ_TEMPLATE = 'https://www2.census.gov/geo/tiger/GENZ{year}/shp/cb_{year}_us_zcta510_500k.zip'
    ZCTA_TIGER_URLs = {
        2008: 'https://www2.census.gov/geo/tiger/TIGER2008/tl_2008_us_zcta500.zip',
        2010: 'https://www2.census.gov/geo/tiger/TIGER2010/ZCTA5/2010/tl_2010_us_zcta510.zip',
        2015: 'https://www2.census.gov/geo/tiger/TIGER2015/ZCTA5/tl_2015_us_zcta510.zip'
    }

    @classmethod
    def download_shapes(cls, source: CensusShapeCollection, year: int, output_dir: str = None,
                        strict: bool = False) -> None:
        cls.download_zcta(CensusShapeCollection.genz, year, output_dir, strict)
        cls.download_zcta(CensusShapeCollection.tiger, year, output_dir, strict)
        cls.download_county(year, output_dir, strict)

    @classmethod
    def download_zcta(cls, source: CensusShapeCollection, year: int,
                      output_dir: str = None,
                      strict: bool = False) -> None:
        if source == CensusShapeCollection.genz:
            zip_url, is_exact = cls._get_genz_zcta_url(year)
        else:
            zip_url, is_exact = cls._get_tiger_zcta_url(year)

        if strict and not is_exact:
            raise ValueError(f'There is no census data for year { year }.')

        cls._download_shape(zip_url, output_dir)

    @classmethod
    def download_county(cls, year: int, output_dir: str = None, strict: bool = False) -> None:
        county_url, is_exact = cls._get_county_url(year)
        if strict and not is_exact:
            raise ValueError(f'There is no census data for year { year }.')

        cls._download_shape(county_url, output_dir)

    @classmethod
    def _download_shape(cls, url: str, output_dir: str = None) -> None:
        if output_dir is None:
            output_dir = '.'

        shape_file = url.rsplit('/', 1)[1]
        dest = os.path.join(output_dir, shape_file)

        if not os.path.exists(dest):
            https_proxy = os.environ.get('HTTPS_PROXY')
            if https_proxy:
                proxy = request.ProxyHandler({'http': https_proxy, 'https': https_proxy})
                opener = request.build_opener(proxy)
                request.install_opener(opener)

            with tqdm() as bar:
                def report(blocknum, bs, size):
                    bar.total = size
                    bar.update(bs)
                request.urlretrieve(url, dest, reporthook=report)

        with zipfile.ZipFile(dest, 'r') as zip_ref:
            zip_ref.extractall(output_dir)

    @classmethod
    def _get_county_url(cls, year: int) -> Tuple[str, bool]:
        """
            Method returns url to county shape file for nearest existing year data
        """
        if year > 2020:
            return cls._get_county_url(2020)[0], False

        if year in (2012, 2011) or year < 2010:
            return cls._get_county_url(2010)[0], False

        if year == 2010:
            return 'https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_us_050_00_500k.zip', True

        if year == 2013:
            return 'https://www2.census.gov/geo/tiger/GENZ2013/cb_2013_us_county_500k.zip', True

        if 2014 <= year <= 2020:
            return cls.COUNTY_TEMPLATE.format(year=year), True

    @classmethod
    def _get_genz_zcta_url(cls, year: int) -> Tuple[str, bool]:
        """
            Method returns url to zip shape file for nearest existing year data
        """
        if year > 2020:
            return cls._get_genz_zcta_url(2020)[0], False

        if year in (2012, 2011) or year < 2010:
            return cls._get_genz_zcta_url(2010)[0], False

        if year == 2010:
            return 'https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_us_860_00_500k.zip', True

        if year == 2013:
            return 'https://www2.census.gov/geo/tiger/GENZ2013/cb_2013_us_zcta510_500k.zip', True

        if 2014 <= year <= 2019:
            return cls.ZCTA_GENZ_TEMPLATE.format(year=year), True

        if year == 2020:
            return 'https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip', True

    @classmethod
    def _get_tiger_zcta_url(cls, year: int) -> Tuple[str, bool]:
        """
            Method returns url to zip shape file for nearest existing year data
        """

        if year in cls.ZCTA_TIGER_URLs:
            return cls.ZCTA_TIGER_URLs[year], True

        available_years = sorted(
            [key for key in cls.ZCTA_TIGER_URLs],
            reverse=True
        )
        for y in available_years:
            if y <= year:
                return cls.ZCTA_TIGER_URLs[y], False

        return cls.ZCTA_TIGER_URLs[-1], False
            

