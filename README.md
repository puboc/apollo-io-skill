# apollo-io-skill

Apollo.io lead intelligence skill for OpenClaw and Hermes agents.

Provides search, enrichment, CRM management, sequence enrollment, task tracking, and deal management — all via a single Python script with no external dependencies.

## Quick start

```bash
export APOLLO_API_KEY=your_key_here
python3 scripts/apollo_io.py search_people --company "Stripe" --title "Head of Engineering"
```

Or create a `.env` file in this directory:

```
APOLLO_API_KEY=your_key_here
```

Then run any command:

```bash
python3 scripts/apollo_io.py                          # list all commands
python3 scripts/apollo_io.py search_people --help     # docs for one command
```

## Requirements

- Python 3.7+ (stdlib only — no pip install needed)
- An Apollo.io account with a valid API key ([get one here](https://developer.apollo.io/keys#/keys))

## Structure

```
apollo-io-skill/
├── SKILL.md               Agent instructions and execution rules
├── scripts/
│   └── apollo_io.py       Main script — all commands
├── references/
│   ├── COMMANDS.md        Natural language → command examples
│   └── API.md             Apollo.io endpoint reference
└── README.md
```

## Commands

| Group | Commands |
|-------|----------|
| People / Contacts | `search_people` `get_contact` `enrich_person` `bulk_enrich_people` `create_contact` `update_contact` `list_contacts` |
| Organizations | `search_organizations` `get_account` `enrich_organization` `create_account` `update_account` |
| Sequences | `list_sequences` `get_sequence` `add_to_sequence` |
| Tasks | `create_task` `search_tasks` `complete_task` |
| Opportunities | `list_opportunities` `create_opportunity` `update_opportunity` |
| Utility | `list_email_accounts` `list_labels` |

## Installation (via bot infrastructure)

This repo is installed automatically by the Apollo.io skill adapter in `feature_common`. The installer:

1. Clones this repo to `/opt/apollo_io_skill`
2. Copies it into the agent's skills directory
3. Writes `APOLLO_API_KEY` to `.env`

No manual setup is needed when provisioning via the shop website.

## Notes on API credits

- Search operations (search_people, search_organizations) are free
- Enrichment (enrich_person, enrich_organization) costs Apollo export credits
- Revealing personal emails or phone numbers costs additional credits
- Use `bulk_enrich_people` instead of looping enrich_person to batch requests
