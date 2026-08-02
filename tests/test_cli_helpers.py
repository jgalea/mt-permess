"""Unit tests (no network)."""

import argparse

import pytest

from mt_permess.cli import PLACES, _norm_lonlat, resolve_latlon
from mt_permess.client import PermessError


def test_places_has_valletta():
    lon, lat = PLACES["valletta"]
    assert 14.4 < lon < 14.6
    assert 35.8 < lat < 36.0


def test_resolve_place():
    args = argparse.Namespace(place="sliema", latlon=None, lat=None, lon=None)
    lat, lon = resolve_latlon(args)
    assert lat > 35.8
    assert lon > 14.4


def test_resolve_latlon_string():
    args = argparse.Namespace(place=None, latlon="35.90,14.51", lat=None, lon=None)
    lat, lon = resolve_latlon(args)
    assert lat == pytest.approx(35.90)
    assert lon == pytest.approx(14.51)


def test_resolve_lat_lon_flags():
    args = argparse.Namespace(place=None, latlon=None, lat=35.9, lon=14.5)
    lat, lon = resolve_latlon(args)
    assert lat == 35.9
    assert lon == 14.5


def test_resolve_missing():
    args = argparse.Namespace(place=None, latlon=None, lat=None, lon=None)
    with pytest.raises(PermessError):
        resolve_latlon(args)


def test_norm_lonlat_swaps_if_needed():
    # user passes lat,lon for Malta
    assert _norm_lonlat("35.90,14.51") == "14.51, 35.9"
    # already lon,lat
    assert _norm_lonlat("14.51,35.90") == "14.51, 35.9"
    assert _norm_lonlat("14.5, 35.9") == "14.5, 35.9"
