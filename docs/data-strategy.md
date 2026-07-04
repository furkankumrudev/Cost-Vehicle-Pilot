# Data Strategy

## Goal

Cost Vehicle Pilot needs a reliable vehicle price dataset for training a price prediction model and generating market trend visuals.

## First MVP Decision

For Sprint 1, the project starts with a public used-car price dataset. This keeps the project independent from scraping risks and lets the team focus on the core product flow:

1. Data cleaning
2. Exploratory data analysis
3. Price prediction model
4. Dashboard and trend analysis

## Why Not Start With Scraping?

Live scraping from listing platforms can create technical and legal risks. Website structures can change, anti-bot systems can block access, and terms of service may restrict automated collection. For a one-month bootcamp project, relying on scraping from day one would increase delivery risk.

## Future API / Live Data Plan

The architecture will support replacing the static CSV with a scheduled data ingestion layer later.

Planned flow:

```text
External API or approved data source
  -> ingestion script
  -> raw data storage
  -> preprocessing pipeline
  -> processed dataset
  -> model training
  -> dashboard predictions
```

## Current Limitation

The current dataset is not Turkey-specific and prices are not in TRY. It is used as a model-development dataset. In the final product narrative, this will be clearly described as the first MVP data source, while the product architecture will stay ready for Turkey-focused data.
