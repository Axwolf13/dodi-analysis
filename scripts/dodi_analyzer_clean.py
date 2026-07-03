"""
DODI (Digital Ownership Deception Index) Analyzer - FINAL VERSION
Based on Perzanowski & Hoofnagle (2017) methodology
Weights: 25% Readability | 50% License Ratio | 25% Red Flags
"""
import textstat
import re

class DODIAnalyzer:
    def __init__(self):
        # 1. Ownership Terminology (Positive)
        self.ownership_words = ["buy", "purchase", "own", "acquire", "possess"]
        
        # 2. License Terminology (Negative)
        self.license_words = ["license", "subscription", "access", "service", "grant", "rent"]
        
        # 3. Red Flags (Aggressive Clauses - Expanded List)
        self.red_flags = [
            # Ownership/Termination
            "without notice", "sole discretion", "terminate", "revoke", 
            "suspend", "non-transferable", "forfeit", "at any time",
            
            # Legal Rights (The "Sony/Microsoft" Killers)
            "class action", "waiver", "arbitration", "jury trial", 
            "indemnify", "hold harmless", "limitation of liability", 
            "as is", "no warranty", "jurisdiction",
            
            # Privacy/Data (The "Facebook" Killers)
            "third party", "third parties", "affiliates", "advertising", 
            "marketing", "track", "monitor", "location", "profile", 
            "partners", "share your", "sell your", "opt-out", "opt out"
        ]

    def analyze(self, text):
        text_lower = text.lower()
        
        # --- Metric 1: License/Ownership Ratio (50% Weight) ---
        ownership_count = sum(text_lower.count(w) for w in self.ownership_words)
        license_count = sum(text_lower.count(w) for w in self.license_words)
        
        if ownership_count == 0:
            ratio = license_count  # Infinite ratio penalty
            ratio_score = 100
        else:
            ratio = license_count / ownership_count
            # Cap ratio score at 100 (if ratio > 10, it's max deception)
            ratio_score = min((ratio / 10) * 100, 100)

        # --- Metric 2: Readability (25% Weight) ---
        try:
            grade_level = textstat.flesch_kincaid_grade(text)
        except:
            grade_level = 12 # Fallback
            
        # Linear penalty: Grade 8 = 0pts, Grade 16 = 100pts
        if grade_level <= 8:
            readability_penalty = 0
        elif grade_level >= 16:
            readability_penalty = 100
        else:
            readability_penalty = ((grade_level - 8) / 8) * 100

        # --- Metric 3: Red Flags (25% Weight) ---
        red_flag_count = sum(text_lower.count(phrase) for phrase in self.red_flags)
        # Cap at 50 flags for max score
        red_flag_score = min((red_flag_count / 50) * 100, 100)

        # --- Final Weighted Score (25/50/25) ---
        dodi_score = (readability_penalty * 0.25) + (ratio_score * 0.50) + (red_flag_score * 0.25)

        return {
            "dodi_score": round(dodi_score, 1),
            "ownership_count": ownership_count,
            "license_count": license_count,
            "ratio": round(ratio, 2),
            "grade_level": round(grade_level, 1),
            "red_flags": red_flag_count
        }