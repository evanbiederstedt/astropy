# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Accuracy tests for AltAz to ICRS coordinate transformations.

We use "known good" examples computed with other coordinate libraries.

Note that we use very low precision asserts because some people run tests on 32-bit
machines and we want the tests to pass there.
TODO: check if these tests pass on 32-bit machines and implement
higher-precision checks on 64-bit machines.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from ....tests.helper import pytest, catch_warnings
from .... import units as u
from ....time import Time, TimeDelta
from ...builtin_frames import AltAz
from ... import EarthLocation
from ... import Angle, SkyCoord


def test_against_hor2eq():
    """Check that Astropy gives consistent results with an IDL hor2eq example.

    See EXAMPLE input and output here:
    http://idlastro.gsfc.nasa.gov/ftp/pro/astro/hor2eq.pro
    """
    # Observatory position for `kpno` from here:
    # http://idlastro.gsfc.nasa.gov/ftp/pro/astro/observatory.pro
    location = EarthLocation(lon=Angle('-111d36.0m'),
                             lat=Angle('31d57.8m'),
                             height=2120. * u.m)

    # obstime = Time('2041-12-26 05:00:00')
    obstime = Time(2466879.7083333, format='jd')
    # obstime += TimeDelta(-2, format='sec')

    altaz_frame = AltAz(obstime=obstime, location=location,
                        temperature=0 * u.deg_C, pressure=0.781 * u.bar)
    altaz = SkyCoord('264d55m06s 37d54m41s', frame=altaz_frame)

    radec_frame = 'icrs'

    # The following transformation throws a warning about precision problems
    # because the observation date is in the future
    with catch_warnings() as _:
        radec_actual = altaz.transform_to(radec_frame)

    radec_expected = SkyCoord('00h13m14.1s  +15d11m0.3s', frame=radec_frame)
    distance = radec_actual.separation(radec_expected).to('arcsec')
    # print(radec_expected)
    # print(radec_actual)
    # print(distance)

    # TODO: why is there a difference of 2.6 arcsec currently?
    # radec_expected = ra=3.30875 deg, dec=15.183416666666666 deg
    # radec_actual = ra=3.3094193224314625 deg, dec=15.183757021354532 deg
    # distance = 2.6285 arcsec
    assert distance < 5 * u.arcsec


def test_against_pyephem():
    """Check that Astropy gives consistent results with one PyEphem example.

    PyEphem: http://rhodesmill.org/pyephem/

    See example input and output here:
    https://gist.github.com/zonca/1672906
    https://github.com/phn/pytpm/issues/2#issuecomment-3698679
    """
    obstime = Time('2011-09-18 08:50:00')
    location = EarthLocation(lon=Angle('-109d24m53.1s'),
                             lat=Angle('33d41m46.0s'),
                             height=30000. * u.m)
    # We are using the default pressure and temperature in PyEphem
    # relative_humidity = ?
    # obswl = ?
    altaz_frame = AltAz(obstime=obstime, location=location,
                        temperature=15 * u.deg_C, pressure=1.010 * u.bar)

    altaz = SkyCoord('6.8927d -60.7665d', frame=altaz_frame)
    radec_actual = altaz.transform_to('icrs')

    radec_expected = SkyCoord('196.497518d -4.569323d', frame='icrs')  # EPHEM
    # radec_expected = SkyCoord('196.496220d -4.569390d', frame='icrs')  # HORIZON
    distance = radec_actual.separation(radec_expected).to('arcsec')
    # TODO: why is this difference so large?
    # It currently is: 31.45187984720655 arcsec
    assert distance < 1e3 * u.arcsec

    # Add assert on current Astropy result so that we notice if something changes
    radec_expected = SkyCoord('196.495372d -4.560694d', frame='icrs')
    distance = radec_actual.separation(radec_expected).to('arcsec')
    # Current value: 0.0031402822944751997 arcsec
    assert distance < 1 * u.arcsec


def test_against_jpl_horizons():
    """Check that Astropy gives consistent results with the JPL Horizons example.

    The input parameters and reference results are taken from this page:
    (from the first row of the Results table at the bottom of that page)
    http://ssd.jpl.nasa.gov/?horizons_tutorial
    """
    obstime = Time('1998-07-28 03:00')
    location = EarthLocation(lon=Angle('248.405300d'),
                             lat=Angle('31.9585d'),
                             height=2.06 * u.km)
    temperature = 15 * u.deg_C  # TODO: correct???
    pressure = 1.010 * u.bar  # TODO: correct???
    # relative_humidity = ?
    # obswl = ?
    altaz_frame = AltAz(obstime=obstime, location=location,
                        temperature=temperature, pressure=pressure)

    altaz = SkyCoord('143.2970d 2.6223d', frame=altaz_frame)
    radec_actual = altaz.transform_to('icrs')
    radec_expected = SkyCoord('19h24m55.01s -40d56m28.9s', frame='icrs')
    distance = radec_actual.separation(radec_expected).to('arcsec')
    # TODO: why is this difference so large?
    # It currently is: 557.2748864283525 arcsec
    assert distance < 1e4 * u.arcsec


@pytest.mark.xfail
def test_fk5_equinox_and_epoch_j2000_0_to_topocentric_observed():
    """
    http://phn.github.io/pytpm/conversions.html#fk5-equinox-and-epoch-j2000-0-to-topocentric-observed
    """
    # Observatory position for `kpno` from here:
    # http://idlastro.gsfc.nasa.gov/ftp/pro/astro/observatory.pro
    location = EarthLocation(lon=Angle('-111.598333d'),
                             lat=Angle('31.956389d'),
                             height=2093.093 * u.m)  # TODO: height correct?

    obstime = Time('2010-01-01 12:00:00', scale='utc')
    # relative_humidity = ?
    # obswl = ?
    altaz_frame = AltAz(obstime=obstime, location=location,
                        temperature=0 * u.deg_C, pressure=0.781 * u.bar)

    radec = SkyCoord('12h22m54.899s 15d49m20.57s', frame='fk5')

    altaz_actual = radec.transform_to(altaz_frame)

    altaz_expected = SkyCoord('264d55m06s 37d54m41s', frame='altaz')
    # altaz_expected = SkyCoord('343.586827647d 15.7683070508d', frame='altaz')
    # altaz_expected = SkyCoord('133.498195532d 22.0162383595d', frame='altaz')
    distance = altaz_actual.separation(altaz_expected)
    # print(altaz_actual)
    # print(altaz_expected)
    # print(distance)
    """TODO: Current output is completely incorrect ... xfailing this test for now.

    <SkyCoord (AltAz: obstime=2010-01-01 12:00:00.000, location=(-1994497.7199061865, -5037954.447348028, 3357437.2294832403) m, pressure=781.0 hPa, temperature=0.0 deg_C, relative_humidity=0, obswl=1.0 micron):00:00.000, location=(-1994497.7199061865, -5037954.447348028, 3357437.2294832403) m, pressure=781.0 hPa, temperature=0.0 deg_C, relative_humidity=0, obswl=1.0 micron): az=133.4869896371561 deg, alt=67.97857990957701 deg>
    <SkyCoord (AltAz: obstime=None, location=None, pressure=0.0 hPa, temperature=0.0 deg_C, relative_humidity=0, obswl=1.0 micron): az=264.91833333333335 deg, alt=37.91138888888889 deg>
    68d02m45.732s
    """

    assert distance < 1 * u.arcsec