"""
Predefined business profiles for impact modeling.
Each industry maps to a list of tier dicts with operational metrics.
The user selects an industry, then picks the tier closest to their business.

IMPORTANT: The system never asks for actual revenue. These are illustrative
baselines that Gemini uses for relative impact calculations.

MVP FOCUS: For the initial product, only the "Transport & Logistics" industry
is actively used, with BodaBoda Rider as the primary tier. All other industries
are retained in the taxonomy for future scalability but are not yet populated
with tiers.
"""

import logging

logger = logging.getLogger(__name__)

# Active target sector for single-industry focus
ACTIVE_INDUSTRY = "Transport & Logistics"

# Canonical industry taxonomy — used by both the LLM auto-tagger and the UI.

# The LLM prompt instructs Gemini to pick ONLY from this list (W7).
# MVP: Only "Transport & Logistics" has active tier profiles.
INDUSTRIES = [
    "Transport & Logistics",
    "Digital & Content Creation",
    "Agriculture & Farming",
    "Retail & Market Trading",
    "Hospitality & Food Service",
    "Manufacturing & Artisan",
    "Finance & Mobile Money",
    "Construction & Real Estate",
]

HUSTLE_PROFILES = {
    "Transport & Logistics": [
        {
            "tier": "Tier 1 — BodaBoda Rider (Motorcycle)",
            "description": "Motorcycle taxi/delivery rider, self-owned bike",
            "metrics": {
                "vehicle_value_kes": 150000,
                "est_monthly_revenue_kes": 30000,
                "est_monthly_overhead_kes": 12000,
                "insurance_annual_kes": 5000,
                "num_employees": 0,
                "expense_categories": [
                    "Fuel",
                    "Motorcycle maintenance/repairs",
                    "Insurance (third-party)",
                    "Phone/data for ride apps",
                    "NTSA compliance fees"
                ],
                "registered_business": False,
            },
            # Compliance profile for regulatory bill analysis.
            # Captures the typical baseline regulatory status of a bodaboda rider.
            # Used by the Compliance Advisor Agent to determine which requirements
            # are already met vs. which need action.
            "compliance_baseline": {
                "has_operating_permit": False,    # Most riders don't have county permits yet
                "has_valid_insurance": True,      # Third-party insurance is common
                "has_safety_training": False,     # New requirement under 2025 regulations
                "has_reflective_vest": False,     # New safety requirement
                "has_helmet_passenger": False,    # Passenger helmet often missing
                "has_ntsa_inspection": True,      # Most have basic NTSA compliance
                "operating_zone": "unrestricted", # Will change under county regulations
            }
        },
        {
            "tier": "Tier 2 — Uber/Bolt Driver (Car)",
            "description": "Full-time ride-hailing driver, financed or owned vehicle",
            "metrics": {
                "vehicle_value_kes": 1200000,
                "est_monthly_revenue_kes": 80000,
                "est_monthly_overhead_kes": 45000,
                "insurance_annual_kes": 35000,
                "num_employees": 0,
                "expense_categories": [
                    "Fuel",
                    "Car loan/financing repayment",
                    "Comprehensive insurance",
                    "Vehicle servicing & repairs",
                    "Phone/data for ride apps",
                    "NTSA inspection & compliance",
                    "Car wash & detailing"
                ],
                "registered_business": False,
            },
            "compliance_baseline": {
                "has_operating_permit": False,
                "has_valid_insurance": True,
                "has_safety_training": False,
                "has_reflective_vest": False,
                "has_helmet_passenger": False,
                "has_ntsa_inspection": True,
                "operating_zone": "unrestricted",
            }
        },
        {
            "tier": "Tier 3 — Small Fleet Owner (2-5 vehicles)",
            "description": "Operates 2-5 vehicles with employed drivers (boda or car)",
            "metrics": {
                "vehicle_value_kes": 4000000,
                "est_monthly_revenue_kes": 250000,
                "est_monthly_overhead_kes": 160000,
                "insurance_annual_kes": 120000,
                "num_employees": 4,
                "expense_categories": [
                    "Driver salaries/commissions",
                    "Fleet fuel costs",
                    "Fleet insurance (comprehensive)",
                    "Vehicle loan repayments",
                    "Maintenance & repairs",
                    "NTSA compliance (multiple vehicles)",
                    "KRA tax obligations (income tax, VAT)",
                    "Tracking/fleet management software"
                ],
                "registered_business": True,
            },
            "compliance_baseline": {
                "has_operating_permit": True,
                "has_valid_insurance": True,
                "has_safety_training": False,
                "has_reflective_vest": False,
                "has_helmet_passenger": False,
                "has_ntsa_inspection": True,
                "operating_zone": "unrestricted",
            }
        }
    ],
}


def get_hustle_profile(industry: str, tier: str) -> dict:
    """
    Look up a predefined hustle profile by industry and tier string.
    Supports exact and partial tier string matching.
    Falls back to default profile if industry or tier is not found.
    """
    profiles_for_ind = HUSTLE_PROFILES.get(industry)
    if not profiles_for_ind:
        # Fall back to Transport & Logistics default if industry not in HUSTLE_PROFILES
        profiles_for_ind = HUSTLE_PROFILES.get("Transport & Logistics", [])

    if not profiles_for_ind:
        return {}

    tier_clean = tier.strip().lower()
    for p in profiles_for_ind:
        p_tier_clean = p["tier"].strip().lower()
        if p_tier_clean == tier_clean or tier_clean in p_tier_clean or p_tier_clean in tier_clean:
            return p

    # If no match found, return first profile in industry
    logger.warning(
        f"No matching tier profile found for tier '{tier}' in industry '{industry}'; "
        f"falling back to default profile '{profiles_for_ind[0]['tier']}'."
    )
    return profiles_for_ind[0]

