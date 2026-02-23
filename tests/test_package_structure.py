"""
Tests for package structure after refactoring root-level scripts
into nemt_parser.parsers and nemt_parser.geocoding subpackages.
"""

import importlib
import pytest


# === Subpackage import tests ===


class TestParsersPackage:
    """Verify nemt_parser.parsers exposes the correct public API."""

    def test_import_parse_excel_with_smart_llm(self):
        from nemt_parser.parsers import parse_excel_with_smart_llm
        assert callable(parse_excel_with_smart_llm)

    def test_import_parse_messy_excel(self):
        from nemt_parser.parsers import parse_messy_excel
        assert callable(parse_messy_excel)

    def test_import_enhance_with_claude(self):
        from nemt_parser.parsers import enhance_with_claude
        assert callable(enhance_with_claude)

    def test_direct_module_import_smart_llm(self):
        from nemt_parser.parsers.smart_llm import parse_excel_with_smart_llm
        assert callable(parse_excel_with_smart_llm)

    def test_direct_module_import_messy_clinic(self):
        from nemt_parser.parsers.messy_clinic import parse_messy_excel
        assert callable(parse_messy_excel)

    def test_direct_module_import_llm_enhance(self):
        from nemt_parser.parsers.llm_enhance import enhance_with_claude
        assert callable(enhance_with_claude)

    def test_parsers_all_exports(self):
        import nemt_parser.parsers as pkg
        assert "parse_excel_with_smart_llm" in pkg.__all__
        assert "parse_messy_excel" in pkg.__all__
        assert "enhance_with_claude" in pkg.__all__

    def test_determine_service_type_accessible_from_smart_llm(self):
        from nemt_parser.parsers.smart_llm import determine_service_type
        assert callable(determine_service_type)

    def test_determine_service_type_accessible_from_messy_clinic(self):
        from nemt_parser.parsers.messy_clinic import determine_service_type
        assert callable(determine_service_type)


class TestGeocodingPackage:
    """Verify nemt_parser.geocoding exposes the correct public API."""

    def test_import_geocode_trips_google(self):
        from nemt_parser.geocoding import geocode_trips_google
        assert callable(geocode_trips_google)

    def test_import_geocode_trips_free(self):
        from nemt_parser.geocoding import geocode_trips_free
        assert callable(geocode_trips_free)

    def test_direct_module_import_google(self):
        from nemt_parser.geocoding.google import geocode_trips_google
        assert callable(geocode_trips_google)

    def test_direct_module_import_free(self):
        from nemt_parser.geocoding.free import geocode_trips_free
        assert callable(geocode_trips_free)

    def test_geocoding_all_exports(self):
        import nemt_parser.geocoding as pkg
        assert "geocode_trips_google" in pkg.__all__
        assert "geocode_trips_free" in pkg.__all__


# === Root-level cleanup verification ===


class TestRootCleanup:
    """Verify old root-level modules are gone."""

    def test_no_root_parse_smart_llm(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("parse_smart_llm")

    def test_no_root_parse_messy_clinic(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("parse_messy_clinic")

    def test_no_root_parse_with_llm(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("parse_with_llm")

    def test_no_root_geocode_with_google(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("geocode_with_google")

    def test_no_root_geocode_free(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("geocode_free")

    def test_no_root_add_geocoding(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("add_geocoding")

    def test_no_empty_llm_package(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("nemt_parser.llm")

    def test_no_empty_utils_package(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("nemt_parser.utils")


# === api_server import test ===


class TestApiServerImports:
    """Verify api_server can load with the new import paths."""

    def test_api_server_imports_parsers(self):
        """The same imports api_server.py uses should resolve."""
        from nemt_parser.parsers import (
            parse_messy_excel,
            enhance_with_claude,
            parse_excel_with_smart_llm,
        )
        assert all(callable(f) for f in [
            parse_messy_excel, enhance_with_claude, parse_excel_with_smart_llm
        ])

    def test_api_server_imports_geocoding(self):
        """The same imports api_server.py uses should resolve."""
        from nemt_parser.geocoding import geocode_trips_google, geocode_trips_free
        assert all(callable(f) for f in [geocode_trips_google, geocode_trips_free])


# === Cross-module dependency test ===


class TestInternalDependencies:
    """Verify internal imports between submodules work."""

    def test_llm_enhance_can_import_messy_clinic(self):
        """llm_enhance.py has a relative import from messy_clinic."""
        mod = importlib.import_module("nemt_parser.parsers.llm_enhance")
        assert hasattr(mod, "enhance_with_claude")
        assert hasattr(mod, "parse_with_llm_enhancement")
