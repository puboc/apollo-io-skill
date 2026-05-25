# Apollo.io — Natural Language Command Examples

This file maps natural language user requests to the specific script commands the agent should run.

---

## Prospecting — finding leads

**"Find VP of Sales at companies with 50–200 employees in the US"**
```bash
python3 scripts/apollo_io.py search_people \
  --title "VP of Sales" \
  --employees "51-200" \
  --location "United States"
```

**"Search for CTOs or Heads of Engineering at Series A SaaS startups"**
```bash
python3 scripts/apollo_io.py search_people \
  --title "CTO" \
  --title "Head of Engineering" \
  --title "VP Engineering" \
  --keyword "saas" \
  --employees "11-50"
```

**"Find marketing leads at fintech companies in San Francisco"**
```bash
python3 scripts/apollo_io.py search_people \
  --seniority manager \
  --seniority director \
  --seniority vp \
  --department marketing \
  --industry "fintech" \
  --location "San Francisco"
```

**"Get the next page of results"**
```bash
python3 scripts/apollo_io.py search_people --page 2 <same other flags as before>
```

**"Search with more granular filters"** — use JSON form:
```bash
python3 scripts/apollo_io.py search_people '{
  "q_organization_name": "Stripe",
  "person_titles": ["Head of Growth", "Growth Lead"],
  "person_locations": ["New York, United States"],
  "contact_email_statuses": ["verified"],
  "per_page": 5
}'
```

---

## Prospecting — finding companies

**"Find B2B SaaS companies in the US with 100–500 employees"**
```bash
python3 scripts/apollo_io.py search_organizations \
  --location "United States" \
  --employees "101-200" \
  --employees "201-500" \
  --industry "saas"
```

**"Look up Stripe"**
```bash
python3 scripts/apollo_io.py search_organizations --domain stripe.com
```

**"Find companies using HubSpot with over 200 employees"**
```bash
python3 scripts/apollo_io.py search_organizations \
  --technology "hubspot" \
  --employees "201-500" \
  --employees "501-1000"
```

---

## Enrichment

**"Get full profile for jane@acme.com"**
```bash
python3 scripts/apollo_io.py enrich_person --email jane@acme.com
```

**"Find contact info for John Smith at Stripe"**
```bash
python3 scripts/apollo_io.py enrich_person --name "John Smith" --company "Stripe"
```

**"Get more info about this company: acme.com"**
```bash
python3 scripts/apollo_io.py enrich_organization --domain acme.com
```

**"Enrich these 3 leads at once"** — pass a JSON array:
```bash
python3 scripts/apollo_io.py bulk_enrich_people '[
  {"email": "alice@acme.com"},
  {"first_name": "Bob", "last_name": "Jones", "organization_name": "Stripe"},
  {"linkedin_url": "https://linkedin.com/in/charlie"}
]'
```

---

## CRM — creating and updating records

**"Add Jane Smith as a contact"**
```bash
python3 scripts/apollo_io.py create_contact '{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@acme.com",
  "title": "VP Sales",
  "organization_name": "Acme Corp"
}'
```

**"Update Jane's title to CRO"**
```bash
python3 scripts/apollo_io.py update_contact <contact_id> '{"title": "Chief Revenue Officer"}'
```

**"Add Acme Corp as a company"**
```bash
python3 scripts/apollo_io.py create_account '{
  "name": "Acme Corp",
  "domain": "acme.com",
  "raw_address": "San Francisco, CA",
  "num_employees": 150
}'
```

**"Update Acme's phone number"**
```bash
python3 scripts/apollo_io.py update_account <account_id> '{"phone": "415-555-0100"}'
```

---

## Sequences — outreach campaigns

**"Show me all our email sequences"**
```bash
python3 scripts/apollo_io.py list_sequences
```

**"Add Jane to the Q3 Outbound sequence"**
```bash
# First, find the sequence ID:
python3 scripts/apollo_io.py list_sequences

# Then add the contact:
python3 scripts/apollo_io.py add_to_sequence <sequence_id> <contact_id>
```

**"Add Jane to the sequence using the sales@acme.com inbox"**
```bash
python3 scripts/apollo_io.py list_email_accounts
# Note the email account ID, then:
python3 scripts/apollo_io.py add_to_sequence <sequence_id> --email-account-id <email_account_id> <contact_id>
```

**"Add all three contacts to the welcome sequence"**
```bash
python3 scripts/apollo_io.py add_to_sequence <sequence_id> <contact_id_1> <contact_id_2> <contact_id_3>
```

---

## Tasks

**"Schedule a call with Jane for June 1st"**
```bash
python3 scripts/apollo_io.py create_task \
  --type call \
  --contact-id <contact_id> \
  --note "Follow up on demo" \
  --due-at 2026-06-01
```

**"Create a LinkedIn connection task for Bob"**
```bash
python3 scripts/apollo_io.py create_task \
  --type linkedin_connect \
  --contact-id <contact_id>
```

**"Show me all pending call tasks"**
```bash
python3 scripts/apollo_io.py search_tasks --type call --status pending
```

**"What tasks do I have for Jane?"**
```bash
python3 scripts/apollo_io.py search_tasks --contact-id <contact_id>
```

**"Mark that task as done"**
```bash
python3 scripts/apollo_io.py complete_task <task_id>
```

---

## Opportunities / Deals

**"Create a deal for Acme worth $15,000 at Demo Scheduled stage"**
```bash
python3 scripts/apollo_io.py create_opportunity \
  --name "Acme Corp Q3 Deal" \
  --amount 15000 \
  --account-id <account_id> \
  --contact-id <contact_id> \
  --stage "Demo Scheduled"
```

**"Update the deal to Closed Won and increase the value to $20,000"**
```bash
python3 scripts/apollo_io.py update_opportunity <opportunity_id> '{
  "amount": 20000,
  "stage_name": "Closed Won"
}'
```

**"Show all deals"**
```bash
python3 scripts/apollo_io.py list_opportunities
```

---

## Common multi-step workflows

### Full prospecting → outreach flow

```bash
# 1. Find leads
python3 scripts/apollo_io.py search_people \
  --title "Head of Marketing" \
  --employees "51-200" \
  --location "United States"

# 2. Enrich the most promising one
python3 scripts/apollo_io.py enrich_person --email <email_from_results>

# 3. Create the contact in CRM (if not already there)
python3 scripts/apollo_io.py create_contact '{"first_name":"...","email":"...",...}'

# 4. Add to outreach sequence
python3 scripts/apollo_io.py add_to_sequence <sequence_id> <contact_id>

# 5. Schedule a follow-up task
python3 scripts/apollo_io.py create_task --type call --contact-id <id> --due-at 2026-06-07
```

### Lead enrichment → deal creation

```bash
# 1. Enrich company
python3 scripts/apollo_io.py enrich_organization --domain target.com

# 2. Create account
python3 scripts/apollo_io.py create_account '{"name":"Target Co","domain":"target.com"}'

# 3. Enrich the key contact
python3 scripts/apollo_io.py enrich_person --email decision.maker@target.com

# 4. Create contact linked to account
python3 scripts/apollo_io.py create_contact '{"first_name":"...","account_id":"<account_id>",...}'

# 5. Open a deal
python3 scripts/apollo_io.py create_opportunity \
  --name "Target Co Deal" \
  --amount 25000 \
  --account-id <account_id> \
  --contact-id <contact_id> \
  --stage "Prospecting"
```
