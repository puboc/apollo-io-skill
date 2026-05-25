---
name: apollo-io
description: Apollo.io lead intelligence — search, enrich, and engage prospects; manage contacts, accounts, sequences, tasks, and deals.
---

# Apollo.io Lead Intelligence

Use this skill when the user wants to prospect, research, or run outreach using Apollo.io.

## What this skill handles

- Search for people (leads) by name, title, company, location, seniority, or keywords
- Search for companies (accounts) by name, domain, industry, size, or location
- Enrich a person record — get full profile, email, phone, LinkedIn from a name/company/email
- Enrich an organization record — get full company profile from a domain or name
- Create and update contacts and accounts in the Apollo CRM
- List and paginate through the contact and account database
- List email sequences and add contacts to them
- Create tasks (call, email, LinkedIn, action item) on contacts
- Search and filter tasks by type, status, or contact
- Create and list opportunities/deals linked to accounts and contacts
- List connected email accounts for sending context
- List labels and custom lists

## Runtime config

Read `.env` in this skill directory for:

- `APOLLO_API_KEY` — required; master API key for all operations

## Execution rules

- Always source `.env` first; never proceed if `APOLLO_API_KEY` is empty.
- When searching people or companies, never send an empty payload — it wastes API credits and returns irrelevant results. Always include at least one filter criterion.
- Default `per_page` to 10 for searches unless the user explicitly asks for more.
- Apollo enrichment costs credits. Prefer `enrich_person` with an email when available; fall back to name+company only when no email is known.
- IDs (contact_id, account_id, sequence_id, etc.) must come from API responses — never invent them.
- When the user asks to "add someone to a sequence", first verify the contact exists with `get_contact` or `search_people`, then call `add_to_sequence`.
- Task types must be exactly one of: `call`, `email`, `action_item`, `linkedin_message`, `linkedin_connect`.
- When bulk-enriching, batch using the JSON array form rather than calling enrich_person in a loop.
- Print the full JSON response so the user can see IDs and fields for follow-up operations.
- If a request is ambiguous (e.g. "find marketing leads"), ask for at least one more qualifier (location, company size, title keyword) before searching.

## Commands via script

```bash
# ── People / Contacts ──────────────────────────────────────────────────────────
python3 scripts/apollo_io.py search_people --name "Jane Smith"
python3 scripts/apollo_io.py search_people --company "Acme Corp" --title "VP of Sales" --location "New York"
python3 scripts/apollo_io.py search_people --seniority manager --seniority director --department sales --employees "11-50" --page 2
python3 scripts/apollo_io.py search_people '{"q_organization_name":"Stripe","person_titles":["CTO","Head of Engineering"],"per_page":5}'

python3 scripts/apollo_io.py get_contact <contact_id>

python3 scripts/apollo_io.py enrich_person --email jane@acme.com
python3 scripts/apollo_io.py enrich_person --name "Jane Smith" --company "Acme Corp"
python3 scripts/apollo_io.py enrich_person --linkedin-url "https://linkedin.com/in/janesmith"
python3 scripts/apollo_io.py enrich_person '{"email":"jane@acme.com","reveal_personal_emails":true}'

python3 scripts/apollo_io.py bulk_enrich_people '[{"first_name":"Jane","last_name":"Smith","organization_name":"Acme"},{"email":"bob@stripe.com"}]'

python3 scripts/apollo_io.py create_contact '{"first_name":"Jane","last_name":"Smith","email":"jane@acme.com","title":"VP Sales","organization_name":"Acme Corp"}'
python3 scripts/apollo_io.py update_contact <contact_id> '{"title":"Chief Revenue Officer","email":"jane.smith@acme.com"}'
python3 scripts/apollo_io.py list_contacts --page 1 --per-page 25

# ── Organizations / Accounts ───────────────────────────────────────────────────
python3 scripts/apollo_io.py search_organizations --name "Stripe"
python3 scripts/apollo_io.py search_organizations --domain "stripe.com"
python3 scripts/apollo_io.py search_organizations --location "San Francisco" --employees "51-200" --industry "fintech"
python3 scripts/apollo_io.py search_organizations '{"organization_locations":["United States"],"num_employees_ranges":["201-500","501-1000"],"q_organization_keyword_tags":["saas","b2b"]}'

python3 scripts/apollo_io.py get_account <account_id>

python3 scripts/apollo_io.py enrich_organization --domain stripe.com
python3 scripts/apollo_io.py enrich_organization --name "Stripe"
python3 scripts/apollo_io.py enrich_organization '{"domain":"stripe.com"}'

python3 scripts/apollo_io.py create_account '{"name":"Acme Corp","domain":"acme.com","phone":"415-555-0100","raw_address":"San Francisco, CA"}'
python3 scripts/apollo_io.py update_account <account_id> '{"phone":"415-555-9999","annual_revenue":5000000}'

# ── Sequences ─────────────────────────────────────────────────────────────────
python3 scripts/apollo_io.py list_sequences
python3 scripts/apollo_io.py list_sequences --page 2 --per-page 50
python3 scripts/apollo_io.py get_sequence <sequence_id>

python3 scripts/apollo_io.py add_to_sequence <sequence_id> <contact_id>
python3 scripts/apollo_io.py add_to_sequence <sequence_id> <contact_id_1> <contact_id_2> <contact_id_3>
python3 scripts/apollo_io.py add_to_sequence <sequence_id> --email-account-id <email_account_id> <contact_id>

# ── Tasks ─────────────────────────────────────────────────────────────────────
python3 scripts/apollo_io.py create_task --type call --contact-id <id> --note "Follow up on demo" --due-at 2026-06-01
python3 scripts/apollo_io.py create_task --type email --contact-id <id> --note "Send proposal"
python3 scripts/apollo_io.py create_task --type linkedin_message --contact-id <id>
python3 scripts/apollo_io.py create_task '{"type":"action_item","contact_id":"<id>","note":"Review their website","due_at":"2026-06-01"}'

python3 scripts/apollo_io.py search_tasks --status pending
python3 scripts/apollo_io.py search_tasks --type call --status pending
python3 scripts/apollo_io.py search_tasks --contact-id <id>

python3 scripts/apollo_io.py complete_task <task_id>

# ── Opportunities / Deals ─────────────────────────────────────────────────────
python3 scripts/apollo_io.py list_opportunities
python3 scripts/apollo_io.py create_opportunity --name "Acme Corp Q3 Deal" --amount 15000 --account-id <id> --contact-id <id> --stage "Demo Scheduled"
python3 scripts/apollo_io.py create_opportunity '{"name":"Big Deal","amount":50000,"account_id":"<id>","contact_ids":["<id1>","<id2>"],"stage_name":"Proposal Sent"}'
python3 scripts/apollo_io.py update_opportunity <opportunity_id> '{"amount":60000,"stage_name":"Closed Won"}'

# ── Utility ───────────────────────────────────────────────────────────────────
python3 scripts/apollo_io.py list_email_accounts
python3 scripts/apollo_io.py list_labels
```

## References

- `references/COMMANDS.md` — natural language examples and how they map to commands
- `references/API.md` — Apollo.io endpoint reference with field descriptions and valid values
