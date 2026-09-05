# Decision Journal

> Why we made the choices we made. Updated throughout the project.

---

## 2026-08-05 — Project Inception

### Target Audience: Small Agencies (not freelancers)
Alternatives considered: Freelancers, startups, small law firms.
Reason: Agencies have recurring revenue, regular contract flow, and are willing to pay €20–50/month. Freelancers rarely convert to paid users.
Expected effect: Higher subscription conversion rate when monetization starts.

### Three Decision Categories (not 0–100 scale)
Alternatives considered: Sign Score 0–100, five categories, traffic light.
Reason: Without statistical calibration, users will question "why 82 and not 76?" Three categories are intuitive and sufficient for v0.1.
Expected effect: Higher trust, lower cognitive load.

### "Issue" instead of "Risk" in UI
Alternatives considered: Risk, Problem, Concern, Finding.
Reason: "Issue" is more familiar to agency owners than "Risk" (which is an insurance/legal term).
Expected effect: Friendlier interface, lower language barrier.

### No "AI" on the landing page
Alternatives considered: AI-powered, Artificial Intelligence, no mention.
Reason: The user cares about the result, not the technology. "AI" is noise in 2026, not a differentiator.
Expected effect: Higher trust, less skepticism.

### Service Agreement only for v0.1
Alternatives considered: NDA, Employment Contract, all contract types.
Reason: Focus on one type increases analysis quality and speeds up development.
Expected effect: Better solution for one problem vs. mediocre for several.

### Repeat usage as primary success metric
Alternatives considered: Signups, total uploads, NPS.
Reason: Signups don't prove value. Repeat usage is an objective signal that the service solved a real problem.
Expected effect: Early product/market fit signal without illusions.

### Decision Catalogue before code (Day -1)
Reason: Business rules should live independently from code. Makes the engine explainable and maintainable.
Expected effect: Easier to onboard, audit, and extend to new document types.

### docs/ as Obsidian-compatible Vault
Reason: Documentation becomes a knowledge base, not just a formality. Graph view shows connections between decisions, architecture, and roadmap.
Expected effect: Faster context recovery when revisiting the project. Reusable for future products.