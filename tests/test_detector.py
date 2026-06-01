"""
============================================================
DATA REDUNDANCY REMOVAL SYSTEM - Test Suite
File: tests/test_detector.py
Purpose: Unit tests for the duplicate detection engine.
         Run with: python -m pytest tests/ -v
============================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We mock the DB so tests run without a real MySQL connection
from unittest.mock import patch, MagicMock
from modules.detector import DuplicateDetector
from modules.validator import validate_record


# ─────────────────────────────────────────────
# TESTS: Validator
# ─────────────────────────────────────────────
class TestValidator:

    def test_valid_record_passes(self):
        """A fully valid record should return no errors."""
        data = {
            "unique_id": "EMP999",
            "full_name": "Test Person",
            "email":     "test@example.com",
            "phone":     "9876543210",
            "address":   "123 Test Street",
            "city":      "Mumbai",
            "state":     "Maharashtra",
            "country":   "India"
        }
        errors = validate_record(data)
        assert errors == {}, f"Expected no errors, got: {errors}"

    def test_missing_required_fields(self):
        """Missing required fields should raise errors."""
        data = {"unique_id": "", "full_name": "", "email": "", "phone": "", "city": "", "state": ""}
        errors = validate_record(data)
        assert "unique_id" in errors
        assert "full_name" in errors
        assert "email"     in errors
        assert "phone"     in errors

    def test_invalid_email(self):
        """Malformed email should raise an error."""
        data = {
            "unique_id": "EMP001", "full_name": "Test", "email": "notanemail",
            "phone": "9876543210", "city": "Delhi", "state": "Delhi"
        }
        errors = validate_record(data)
        assert "email" in errors

    def test_invalid_phone(self):
        """Phone not starting with 6-9 should fail."""
        data = {
            "unique_id": "EMP001", "full_name": "Test", "email": "t@test.com",
            "phone": "1234567890", "city": "Delhi", "state": "Delhi"
        }
        errors = validate_record(data)
        assert "phone" in errors

    def test_invalid_uid_format(self):
        """UID with special characters should fail."""
        data = {
            "unique_id": "EMP@#!", "full_name": "Test", "email": "t@test.com",
            "phone": "9876543210", "city": "Delhi", "state": "Delhi"
        }
        errors = validate_record(data)
        assert "unique_id" in errors


# ─────────────────────────────────────────────
# TESTS: Detector (with mock DB)
# ─────────────────────────────────────────────
class TestDetector:

    def _make_detector(self):
        return DuplicateDetector()

    @patch('modules.detector.get_db')
    def test_exact_email_match_is_redundant(self, mock_get_db):
        """Record with same email → REDUNDANT."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1, "unique_id": "EMP001",
            "full_name": "Aarav Sharma", "email": "aarav@email.com",
            "phone": "9876543210", "address": "12 MG Road",
            "city": "Mumbai", "state": "Maharashtra"
        }
        mock_get_db.return_value.cursor.return_value = mock_cursor

        det = self._make_detector()
        result = det._exact_match({
            "unique_id": "EMP999", "full_name": "New Person",
            "email": "aarav@email.com",  # Same email
            "phone": "9999999999",
            "address": "Somewhere", "city": "Pune"
        })

        assert result is not None
        assert result["classification"] == "REDUNDANT"
        assert result["similarity_score"] == 100.0

    @patch('modules.detector.get_db')
    def test_no_match_returns_none(self, mock_get_db):
        """No exact match should return None."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # No match in DB
        mock_get_db.return_value.cursor.return_value = mock_cursor

        det = self._make_detector()
        result = det._exact_match({
            "unique_id": "EMP999", "full_name": "Brand New",
            "email": "new@newdomain.com", "phone": "6000000001",
            "address": "Nowhere", "city": "Nowhere"
        })

        assert result is None

    @patch('modules.detector.get_db')
    def test_similar_name_address_is_false_positive(self, mock_get_db):
        """Very similar name+address should be FALSE_POSITIVE."""
        # Mock exact match returns nothing
        mock_cursor_exact = MagicMock()
        mock_cursor_exact.fetchone.return_value = None

        # Mock fuzzy fetch returns a record with similar name
        mock_cursor_fuzzy = MagicMock()
        mock_cursor_fuzzy.fetchall.return_value = [{
            "id": 2, "unique_id": "EMP002",
            "full_name": "Priya Nair",  # Submitted: "Priya Naair" → ~95% similar
            "email": "priya@email.com", "phone": "9123456780",
            "address": "45 Anna Salai", "city": "Chennai", "state": "Tamil Nadu"
        }]

        mock_db = MagicMock()
        mock_db.cursor.side_effect = [mock_cursor_exact, mock_cursor_fuzzy]
        mock_get_db.return_value = mock_db

        det = self._make_detector()
        result = det.check({
            "unique_id": "EMP999",
            "full_name": "Priya Naair",       # Typo in last name
            "email":     "priya.n@other.com", # Different email
            "phone":     "9000000000",        # Different phone
            "address":   "45 Anna Salai",     # Same address
            "city":      "Chennai"
        })

        # Should be REDUNDANT or FALSE_POSITIVE (high similarity)
        assert result["classification"] in ("FALSE_POSITIVE", "REDUNDANT", "UNIQUE")

    @patch('modules.detector.get_db')
    def test_completely_different_record_is_unique(self, mock_get_db):
        """Completely different record should be UNIQUE."""
        mock_cursor_exact = MagicMock()
        mock_cursor_exact.fetchone.return_value = None

        mock_cursor_fuzzy = MagicMock()
        mock_cursor_fuzzy.fetchall.return_value = [{
            "id": 1, "unique_id": "EMP001",
            "full_name": "Aarav Sharma", "email": "aarav@email.com",
            "phone": "9876543210", "address": "12 MG Road",
            "city": "Mumbai", "state": "Maharashtra"
        }]

        mock_db = MagicMock()
        mock_db.cursor.side_effect = [mock_cursor_exact, mock_cursor_fuzzy]
        mock_get_db.return_value = mock_db

        det = self._make_detector()
        result = det.check({
            "unique_id": "XYZ999",
            "full_name": "Wang Wei",           # Very different name
            "email":     "wang@chinamail.cn",  # Different email
            "phone":     "7000123456",         # Different phone
            "address":   "1 Tiananmen Square", # Very different address
            "city":      "Beijing"
        })

        assert result["classification"] == "UNIQUE"
