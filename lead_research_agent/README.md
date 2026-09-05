# Lead Research Agent v0.1

Website-first prospect enrichment for agency outreach.

## Run

```bash
python -m lead_research_agent --input companies.csv --output prospects.csv
```

## Notes

- Does not send email.
- Does not scrape LinkedIn.
- Website extraction runs first.
- Hunter is optional and activates only when `HUNTER_API_KEY` is set.
- Snov is not used in v0.1.1.
