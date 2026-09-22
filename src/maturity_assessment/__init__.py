"""Maturity Assessment Layer package.

Architectural boundary, parallel to src/compliance/ (Compliance Decision
Layer) and separate from src/scoring/ (Evidence Coverage aggregation).

This layer answers exactly one question per MQ: "what is the highest
maturity level (0-5) supported by the evidence assessed so far, walking
data/maturity_models/DC_MQ_*.json cumulatively?" It never reads
coverage_percentage/compliance_percentage, never produces a Compliance
verdict, and never aggregates across MQ.1/2/3 into a single domain score
(that aggregation rule is not documented in any SDAIA/NDMO source available
to this project — see maturity_level_walker.py module docstring).
"""
