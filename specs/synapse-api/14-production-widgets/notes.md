# Notes

- Checked live against butterfly 16 (story seed): output of the last 30 days (27,614,429.98) and equipment effectiveness (94.95%) equal direct reads of `ProductionSummaryByDay`; the downtime hours by cause equal `DowntimeSummaryByDay`.
- Butterfly runs one production batch a month with the same volume, so output is level month to month (the headline then says `level with the 30 days before`) and effectiveness is above the 85% target.
- The seven widgets use trailing windows because a calendar day or month to date is empty for much of the month.
- Run synapse-api next to a butterfly with the production service (butterfly 16); `PRODUCTION_BASE_URL` points at it, and the open orders come from the drivers service.
- Still mock after this phase: Exports (7) and Finance cash and collections (5).
