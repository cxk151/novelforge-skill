# Project schema

## Layout

```text
project/
├── canon.yaml
├── constraints.md
├── change-log.yaml
├── story-bible/{characters,world,factions,powers,items}.yaml
├── planning/{master-outline.md,volumes,arcs,events,options}
├── continuity/{timeline,open-threads,state}.yaml
├── summaries/
├── manuscript/
└── exports/
```

Use statuses `active`, `confirmed`, `draft`, `option`, `superseded`, or `abandoned`. Plans are not confirmed merely because they exist.

Each changeable canon record should retain value, status, source, effective chapter, and update time when provenance matters. Use stable IDs for characters, items, powers, events, and threads; display names may change.

A chapter summary records chapter number/title, time, locations, participants, events, new facts, knowledge changes, item/state changes, relationship changes, threads opened/resolved, and next hook. Keep summaries factual.

A change record includes date, source, scope, old value, new value, status, whether manuscript scanning is required, and resolution.
