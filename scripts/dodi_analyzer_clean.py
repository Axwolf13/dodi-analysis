"""
DODI (Digital Ownership Deception Index) Analyzer, v1.1
Based on Perzanowski & Hoofnagle (2017) methodology
Weights: 25% Readability | 50% License Ratio | 25% Red Flags

v1.1 (September 2026) counts whole words and their genuine forms instead of
substrings. DODIAnalyzer(matching="substring") reproduces the v1.0 scores
published in July 2026.
"""
import textstat
import re
from collections import Counter

# Forms counted when matching="word", the default from v1.1. v1.0 counted
# substrings, which also hits unrelated words: "own" inside "download" and
# "known", "rent" inside "different" and "parent", "location" inside
# "allocation". These lists keep the genuine forms of each term and add the
# British "licence", which v1.0 never counted. scripts/matching_audit.py
# measures what the difference does to every published result.
WORD_FORMS = {
    "buy": ["buy", "buys", "buying", "buyer", "buyers"],
    "purchase": ["purchase", "purchases", "purchased", "purchasing", "purchaser", "purchasers"],
    "own": ["own", "owns", "owned", "owning", "owner", "owners", "ownership"],
    "acquire": ["acquire", "acquires", "acquired", "acquiring", "acquirer"],
    "possess": ["possess", "possesses", "possessed", "possessing", "possession", "possessions"],
    "license": ["license", "licenses", "licensed", "licensing", "licensee", "licensees",
                "licensor", "licensors", "sublicense", "sublicenses", "sublicensed",
                "sublicensing", "sublicensee", "sublicensees",
                "licence", "licences", "licenced", "licencing"],
    "subscription": ["subscription", "subscriptions"],
    "access": ["access", "accesses", "accessed", "accessing", "accessible"],
    "service": ["service", "services"],
    "grant": ["grant", "grants", "granted", "granting"],
    "rent": ["rent", "rents", "rented", "renting", "rental", "rentals"],
    "terminate": ["terminate", "terminates", "terminated", "terminating"],
    "revoke": ["revoke", "revokes", "revoked", "revoking"],
    "suspend": ["suspend", "suspends", "suspended", "suspending"],
    "forfeit": ["forfeit", "forfeits", "forfeited", "forfeiture"],
    "waiver": ["waiver", "waivers"],
    "arbitration": ["arbitration", "arbitrations"],
    "indemnify": ["indemnify"],
    "jurisdiction": ["jurisdiction", "jurisdictions", "jurisdictional"],
    "affiliates": ["affiliates"],
    "advertising": ["advertising"],
    "marketing": ["marketing"],
    "track": ["track", "tracks", "tracked", "tracking"],
    "monitor": ["monitor", "monitors", "monitored", "monitoring"],
    "location": ["location", "locations"],
    "profile": ["profile", "profiles"],
    "partners": ["partners"],
}


class DODIAnalyzer:
    def __init__(self, matching="word"):
        if matching not in ("substring", "word"):
            raise ValueError("matching must be 'substring' or 'word'")
        self.matching = matching

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

    def _count(self, text_lower, tokens, term):
        if self.matching == "substring":
            return text_lower.count(term)
        if term in WORD_FORMS:
            return sum(tokens[f] for f in WORD_FORMS[term])
        # Multi-word phrases: whole words only, so "as is" no longer fires
        # inside "has issued"
        return len(re.findall(r"\b" + re.escape(term) + r"\b", text_lower))

    def term_counts(self, text):
        """Per-term hits for (ownership, licence, red flags), counted exactly
        as analyze() counts them. Terms with no hits are left out."""
        text_lower = text.lower()
        tokens = Counter(re.findall(r"[a-z]+", text_lower)) if self.matching == "word" else None

        def counts(terms):
            found = {t: self._count(text_lower, tokens, t) for t in terms}
            return {t: n for t, n in found.items() if n}

        return counts(self.ownership_words), counts(self.license_words), counts(self.red_flags)

    def analyze(self, text):
        text_lower = text.lower()
        tokens = Counter(re.findall(r"[a-z]+", text_lower)) if self.matching == "word" else None
        
        # --- Metric 1: License/Ownership Ratio (50% Weight) ---
        ownership_count = sum(self._count(text_lower, tokens, w) for w in self.ownership_words)
        license_count = sum(self._count(text_lower, tokens, w) for w in self.license_words)
        
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
        red_flag_count = sum(self._count(text_lower, tokens, phrase) for phrase in self.red_flags)
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