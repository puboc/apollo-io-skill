# Apollo.io API Reference

Base URL: `https://api.apollo.io/api/v1`  
Auth header: `x-api-key: <APOLLO_API_KEY>`  
Full docs: https://docs.apollo.io/docs/api-overview

---

## People / Contacts

### POST `/mixed_people/search`
Search for people. Returns paginated results.

**Key request fields:**

| Field | Type | Description |
|-------|------|-------------|
| `q_person_name` | string | Person name (full or partial) |
| `q_organization_name` | string | Company name |
| `q_keywords` | string | Keyword search |
| `person_titles` | string[] | Job titles |
| `person_locations` | string[] | Person location (city, state, country) |
| `person_seniorities` | string[] | `owner` `founder` `c_suite` `partner` `vp` `head` `director` `manager` `senior` `entry` `intern` |
| `contact_function_changed_to` | string[] | Department: `sales` `marketing` `engineering` `finance` `operations` `hr` `legal` `it` `design` `product` |
| `contact_email_statuses` | string[] | `verified` `unverified` `likely_to_engage` `unavailable` |
| `num_employees_ranges` | string[] | Company headcount ranges: `"1-10"` `"11-50"` `"51-200"` `"201-500"` `"501-1000"` `"1001-5000"` `"5001-10000"` `"10001+"` |
| `organization_ids` | string[] | Filter by specific Apollo org IDs |
| `page` | int | Page number (default 1) |
| `per_page` | int | Results per page (max 100, default 10 to conserve credits) |

**Response:** `{ people: [...], pagination: { total_entries, total_pages, page, per_page } }`

### POST `/people/match`
Enrich a person — find full profile from partial data. **Costs credits.**

**Key request fields:**

| Field | Type | Description |
|-------|------|-------------|
| `email` | string | Best identifier — use when available |
| `first_name` | string | |
| `last_name` | string | |
| `organization_name` | string | Company name |
| `domain` | string | Company domain |
| `linkedin_url` | string | LinkedIn profile URL |
| `reveal_personal_emails` | bool | Return personal email if found (costs extra credit) |
| `reveal_phone_number` | bool | Return phone if found (costs extra credit) |

**Response:** `{ person: { id, name, email, phone_numbers, linkedin_url, title, organization: {...} } }`

### POST `/people/bulk_match`
Enrich up to 10 people in one call. **Costs credits per match.**

**Request:** `{ details: [{ email, first_name, last_name, organization_name, domain, linkedin_url }, ...] }`

### GET `/contacts/:id`
Get a single contact by Apollo ID.

### POST `/contacts`
Create a contact. **Request:** `{ contact: { first_name, last_name, email, title, organization_name, phone_numbers: [{ raw_number, type }], linkedin_url, website_url, label_names } }`

### PUT `/contacts/:id`
Update a contact. Same body shape as POST.

### GET `/contacts`
List contacts. **Params:** `page`, `per_page`

---

## Organizations / Accounts

### POST `/mixed_companies/search`
Search for companies.

**Key request fields:**

| Field | Type | Description |
|-------|------|-------------|
| `q_organization_name` | string | Company name |
| `organization_domains` | string[] | Exact domains |
| `organization_locations` | string[] | HQ location |
| `num_employees_ranges` | string[] | Headcount ranges (same values as people search) |
| `q_organization_keyword_tags` | string[] | Industry keywords (e.g. `"saas"` `"fintech"` `"healthcare"`) |
| `currently_using_any_of_technology_uids` | string[] | Technology slugs (e.g. `"hubspot"` `"salesforce"` `"stripe"`) |
| `revenue_ranges` | string[] | Annual revenue ranges: `"0-1000000"` `"1000000-10000000"` etc. |
| `page` | int | |
| `per_page` | int | |

### POST `/organizations/enrich`
Enrich a company by domain or name. **Request:** `{ domain, name }`  
**Response:** `{ organization: { name, website_url, linkedin_url, num_employees, annual_revenue, primary_domain, technologies: [...] } }`

### GET `/accounts/:id`
Get an account by Apollo ID.

### POST `/accounts`
Create an account. **Request:** `{ account: { name, domain, phone, raw_address, website_url, num_employees, annual_revenue } }`

### PUT `/accounts/:id`
Update an account. Same body shape as POST.

---

## Sequences

### GET `/emailer_campaigns`
List all sequences. **Params:** `page`, `per_page`  
**Response:** `{ emailer_campaigns: [{ id, name, active, num_steps, created_at }] }`

### GET `/emailer_campaigns/:id`
Get a single sequence with all steps.

### POST `/emailer_campaigns/:id/add_contact_ids`
Add contacts to a sequence.  
**Request:** `{ contact_ids: ["id1","id2"], send_email_from_email_account_id: "optional_id" }`  
**Response:** `{ contacts: [{ id, emailer_campaign_id, status }] }`

---

## Tasks

### POST `/tasks`
Create a task. **Request:** `{ task: { type, contact_id, note, due_at } }`

**Valid types:** `call` `email` `action_item` `linkedin_message` `linkedin_connect`

### POST `/tasks/search`
Search tasks. **Request:** `{ types: [], status, contact_ids: [], page, per_page }`

**Valid statuses:** `pending` `complete` `deleted` `scheduled`

### PUT `/tasks/:id`
Update a task. To complete: `{ task: { status: "complete" } }`

---

## Opportunities

### GET `/opportunities/search`
List opportunities. **Params:** `page`, `per_page`

### POST `/opportunities`
Create an opportunity. **Request:** `{ opportunity: { name, amount, account_id, contact_ids, stage_name, close_date } }`

### PUT `/opportunities/:id`
Update an opportunity. **Request:** `{ opportunity: { amount, stage_name, close_date, ... } }`

---

## Email Accounts

### GET `/email_accounts`
List connected email inboxes. Returns `{ email_accounts: [{ id, email, active }] }`  
Use the `id` in sequence enrollment to specify which inbox sends the emails.

---

## Labels

### GET `/labels`
List all custom labels/lists. Returns `{ labels: [{ id, name }] }`

---

## Credit costs

| Operation | Credits |
|-----------|---------|
| `search_people` / `search_organizations` | 0 (browsing) |
| `enrich_person` (email match) | 1 export credit |
| `enrich_person` (+ reveal personal email) | 1 export + 1 email credit |
| `bulk_enrich_people` | 1 per person |
| `enrich_organization` | 1 export credit |

Keep `per_page` at 10 (default) for searches to avoid browsing through too many unneeded results.  
Only call `enrich_person` when you actually need the full profile.

---

## Error codes

| HTTP | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request — check the payload fields |
| 401 | Invalid or missing `x-api-key` |
| 403 | Plan does not include this feature |
| 422 | Validation error — check required fields |
| 429 | Rate limited — slow down requests |
| 500 | Apollo server error — retry after a delay |
