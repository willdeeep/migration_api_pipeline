"""Migration-oriented ingestion pipeline.

Extracts university chapter records from the Ducks Unlimited ArcGIS Feature
Service, filters to CA/OR/WA, validates and transforms them, and loads them
into BigQuery (the migration target).
"""

__version__ = "0.1.0"
