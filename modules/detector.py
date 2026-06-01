"""
============================================================
DATA REDUNDANCY REMOVAL SYSTEM - Duplicate Detection Engine
File: modules/detector.py
Purpose: Core intelligence of the system.
         Detects EXACT duplicates and SIMILAR (false positive) records
         using both database lookups and fuzzy string matching (RapidFuzz).
============================================================

HOW CLASSIFICATION WORKS:
─────────────────────────
  REDUNDANT     → Exact match on email, phone, OR unique_id
  FALSE_POSITIVE→ No exact match, but name+address similarity > threshold
  UNIQUE        → No match at all — safe to insert

THRESHOLDS (configurable in config.py):
  DUPLICATE_THRESHOLD    = 95%  → Above this = REDUNDANT
  FALSE_POSITIVE_THRESHOLD = 75% → Between 75-94% = FALSE_POSITIVE
"""

from rapidfuzz import fuzz
from modules.db import get_db
from config import DUPLICATE_THRESHOLD, FALSE_POSITIVE_THRESHOLD


class DuplicateDetector:
    """
    Encapsulates all duplicate detection logic.
    
    Attributes:
        dup_threshold (float): Min score to classify as REDUNDANT (exact dup)
        fp_threshold  (float): Min score to classify as FALSE_POSITIVE
    """

    def __init__(self):
        self.dup_threshold = DUPLICATE_THRESHOLD
        self.fp_threshold  = FALSE_POSITIVE_THRESHOLD


    # ─────────────────────────────────────────────────────────
    # PUBLIC METHOD: check()
    # ─────────────────────────────────────────────────────────
    def check(self, data: dict) -> dict:
        """
        Main entry point. Takes a submitted record and returns
        its classification with a full explanation.
        
        Steps:
          1. Exact field match (email / phone / unique_id)
          2. Fuzzy similarity match (name + address)
          3. If neither → UNIQUE
        
        Args:
            data (dict): Submitted record fields

        Returns:
            dict: {
                "classification": "UNIQUE" | "REDUNDANT" | "FALSE_POSITIVE",
                "reason": "Human-readable explanation",
                "similarity_score": float (0–100),
                "matched_id": int or None,
                "matched_record": dict or None
            }
        """

        # ── Step 1: Exact Match ──────────────────────────────
        exact_result = self._exact_match(data)
        if exact_result:
            return exact_result

        # ── Step 2: Fuzzy / Similarity Match ────────────────
        fuzzy_result = self._fuzzy_match(data)
        if fuzzy_result:
            return fuzzy_result

        # ── Step 3: Fully Unique ─────────────────────────────
        return {
            "classification":  "UNIQUE",
            "reason":          "No matching record found. This is a new unique entry.",
            "similarity_score": 0.0,
            "matched_id":      None,
            "matched_record":  None
        }


    # ─────────────────────────────────────────────────────────
    # PRIVATE: _exact_match()
    # Checks email, phone, unique_id against database
    # ─────────────────────────────────────────────────────────
    def _exact_match(self, data: dict) -> dict | None:
        """
        Queries the database for an exact match on:
          - email address
          - phone number
          - unique_id

        If any of these match → the submission is a REDUNDANT duplicate.
        
        Args:
            data (dict): Submitted record

        Returns:
            dict: Classification result if match found, else None
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)

        sql = """
            SELECT id, unique_id, full_name, email, phone, address, city, state
            FROM records
            WHERE LOWER(email)     = LOWER(%s)
               OR phone            = %s
               OR UPPER(unique_id) = UPPER(%s)
            LIMIT 1
        """
        cursor.execute(sql, (data["email"], data["phone"], data["unique_id"]))
        match = cursor.fetchone()
        cursor.close()

        if match:
            # Determine which field caused the match
            reasons = []
            if match["email"].lower() == data["email"].lower():
                reasons.append(f"Email '{data['email']}' already exists")
            if match["phone"] == data["phone"]:
                reasons.append(f"Phone '{data['phone']}' already exists")
            if match["unique_id"].upper() == data["unique_id"].upper():
                reasons.append(f"Unique ID '{data['unique_id']}' already exists")

            return {
                "classification":  "REDUNDANT",
                "reason":          "Exact duplicate detected — " + " | ".join(reasons),
                "similarity_score": 100.0,
                "matched_id":      match["id"],
                "matched_record":  match
            }
        return None


    # ─────────────────────────────────────────────────────────
    # PRIVATE: _fuzzy_match()
    # Uses RapidFuzz to compare name + address similarity
    # ─────────────────────────────────────────────────────────
    def _fuzzy_match(self, data: dict) -> dict | None:
        """
        Fetches all records from the database and computes
        fuzzy similarity for name and address using RapidFuzz.
        
        RapidFuzz Algorithms Used:
        ─────────────────────────
        fuzz.token_sort_ratio → Good for name comparison
            "John Smith" vs "Smith John" → 100%
            Handles word order differences
        
        fuzz.partial_ratio → Good for address comparison
            "12 MG Road, Mumbai" vs "MG Road Mumbai" → High score
            Handles partial matches within strings
        
        Combined Score = 60% name + 40% address
        
        Args:
            data (dict): Submitted record

        Returns:
            dict: Classification result if >= fp_threshold, else None
        """
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, unique_id, full_name, email, phone, address, city, state
            FROM records
        """)
        all_records = cursor.fetchall()
        cursor.close()

        best_match    = None
        best_score    = 0.0
        best_name_sc  = 0.0
        best_addr_sc  = 0.0

        submitted_name = data.get("full_name", "").lower().strip()
        submitted_addr = (data.get("address", "") + " " + data.get("city", "")).lower().strip()

        for record in all_records:
            # ── Name similarity ───────────────────────────
            db_name = (record.get("full_name") or "").lower().strip()
            name_score = fuzz.token_sort_ratio(submitted_name, db_name)

            # ── Address similarity ────────────────────────
            db_addr = ((record.get("address") or "") + " " + (record.get("city") or "")).lower().strip()
            addr_score = fuzz.partial_ratio(submitted_addr, db_addr) if submitted_addr and db_addr else 0

            # ── Combined weighted score ───────────────────
            # Name is more important (60%) than address (40%)
            combined = (name_score * 0.60) + (addr_score * 0.40)

            if combined > best_score:
                best_score   = combined
                best_match   = record
                best_name_sc = name_score
                best_addr_sc = addr_score

        # ── Classify by threshold ────────────────────────
        if best_score >= self.dup_threshold and best_match:
            return {
                "classification":  "REDUNDANT",
                "reason":          (f"Near-identical record found. "
                                    f"Name similarity: {best_name_sc:.1f}%, "
                                    f"Address similarity: {best_addr_sc:.1f}%"),
                "similarity_score": round(best_score, 2),
                "matched_id":      best_match["id"],
                "matched_record":  best_match
            }

        if best_score >= self.fp_threshold and best_match:
            return {
                "classification":  "FALSE_POSITIVE",
                "reason":          (f"Similar but not identical record found. "
                                    f"Name similarity: {best_name_sc:.1f}%, "
                                    f"Address similarity: {best_addr_sc:.1f}%. "
                                    f"May be the same person with different details."),
                "similarity_score": round(best_score, 2),
                "matched_id":      best_match["id"],
                "matched_record":  best_match
            }

        return None


    # ─────────────────────────────────────────────────────────
    # PUBLIC: batch_check()
    # Checks a list of records from a Pandas DataFrame
    # ─────────────────────────────────────────────────────────
    def batch_check(self, df) -> list:
        """
        Processes a Pandas DataFrame of records and classifies each row.
        Useful for bulk CSV imports.
        
        Args:
            df (pd.DataFrame): DataFrame with columns matching record fields

        Returns:
            list: List of result dicts, one per row
        """
        results = []
        for _, row in df.iterrows():
            data = row.to_dict()
            result = self.check(data)
            result["row"] = data
            results.append(result)
        return results
