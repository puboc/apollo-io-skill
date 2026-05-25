#!/usr/bin/env python3
"""
Apollo.io skill — agent-callable script for lead intelligence and outreach automation.

Usage:  python3 scripts/apollo_io.py <command> [args]
Run with no args to list all commands.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://api.apollo.io/api/v1"

ENV_CANDIDATES = [
    Path(__file__).resolve().parent.parent / ".env",
    Path.cwd() / ".env",
]


# ── Environment ────────────────────────────────────────────────────────────────

def load_env():
    for path in ENV_CANDIDATES:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def api_key():
    load_env()
    key = os.environ.get("APOLLO_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "APOLLO_API_KEY not set — source the skill .env or export the variable"
        )
    return key


# ── HTTP ───────────────────────────────────────────────────────────────────────

def apollo_request(method, path, payload=None, params=None):
    url = f"{API_BASE}{path}"
    if params:
        url = url + "?" + urllib.parse.urlencode(
            {k: v for k, v in params.items() if v is not None}, doseq=True
        )
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "x-api-key": api_key(),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        # Apollo.io sits behind Cloudflare which blocks Python's default user-agent.
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"Apollo API error HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Network error: {exc.reason}")


def out(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ── Argument helpers ──────────────────────────────────────────────────────────

def parse_flags(args, schema):
    """
    Minimal flag parser.

    schema is a dict: { "--flag": ("dest_key", converter) }
    Returns (result_dict, remaining_positionals).
    """
    result = {}
    positionals = []
    i = 0
    while i < len(args):
        matched = False
        for flag, (key, conv) in schema.items():
            if args[i] == flag and i + 1 < len(args):
                val = args[i + 1]
                if key in result and isinstance(result[key], list):
                    result[key].append(conv(val))
                elif key in result:
                    result[key] = [result[key], conv(val)]
                else:
                    result[key] = conv(val)
                i += 2
                matched = True
                break
        if not matched:
            positionals.append(args[i])
            i += 1
    return result, positionals


def json_or_flags(args, flag_schema):
    """If first arg is a JSON object use it directly, otherwise parse flags."""
    if args and args[0].lstrip().startswith("{"):
        return json.loads(args[0])
    flags, _ = parse_flags(args, flag_schema)
    return flags


# ── People / Contacts ─────────────────────────────────────────────────────────

def cmd_search_people(args):
    """Search for people by name, title, company, location, seniority, or keyword.

    Flags: --name --company --title --location --seniority --department
           --employees (e.g. "1-10" "11-50" "51-200") --email-status
           --keyword --page --per-page
    Or pass a raw JSON filter object as the first argument.

    Examples:
      search_people --company "Stripe" --title "Head of Engineering"
      search_people --seniority manager --seniority director --department sales
      search_people '{"q_organization_name":"Acme","person_titles":["CEO"]}'
    """
    if args and args[0].lstrip().startswith("{"):
        payload = json.loads(args[0])
    else:
        payload = {}
        i = 0
        while i < len(args):
            a = args[i]
            if a == "--name" and i + 1 < len(args):
                payload["q_person_name"] = args[i + 1]; i += 2
            elif a == "--company" and i + 1 < len(args):
                payload["q_organization_name"] = args[i + 1]; i += 2
            elif a == "--title" and i + 1 < len(args):
                payload.setdefault("person_titles", []).append(args[i + 1]); i += 2
            elif a == "--location" and i + 1 < len(args):
                payload.setdefault("person_locations", []).append(args[i + 1]); i += 2
            elif a == "--seniority" and i + 1 < len(args):
                payload.setdefault("person_seniorities", []).append(args[i + 1]); i += 2
            elif a == "--department" and i + 1 < len(args):
                payload.setdefault("contact_function_changed_to", []).append(args[i + 1]); i += 2
            elif a == "--employees" and i + 1 < len(args):
                payload.setdefault("num_employees_ranges", []).append(args[i + 1]); i += 2
            elif a == "--email-status" and i + 1 < len(args):
                # verified, unverified, likely_to_engage, unavailable
                payload.setdefault("contact_email_statuses", []).append(args[i + 1]); i += 2
            elif a == "--keyword" and i + 1 < len(args):
                payload["q_keywords"] = args[i + 1]; i += 2
            elif a == "--page" and i + 1 < len(args):
                payload["page"] = int(args[i + 1]); i += 2
            elif a == "--per-page" and i + 1 < len(args):
                payload["per_page"] = int(args[i + 1]); i += 2
            else:
                i += 1

    payload.setdefault("page", 1)
    payload.setdefault("per_page", 10)
    out(apollo_request("POST", "/mixed_people/search", payload))


def cmd_get_contact(args):
    """Get a contact/person by their Apollo contact ID.

    Usage: get_contact <contact_id>
    """
    if not args:
        raise SystemExit("Usage: get_contact <contact_id>")
    out(apollo_request("GET", f"/contacts/{args[0]}"))


def cmd_enrich_person(args):
    """Enrich a person record — returns full profile, email, phone, LinkedIn.

    Flags: --email --name (full name) --first-name --last-name
           --company --domain --linkedin-url
    Or pass a raw JSON object.
    Note: enrichment costs Apollo credits.

    Examples:
      enrich_person --email jane@acme.com
      enrich_person --name "Jane Smith" --company "Acme Corp"
      enrich_person --linkedin-url "https://linkedin.com/in/janesmith"
    """
    if args and args[0].lstrip().startswith("{"):
        payload = json.loads(args[0])
    else:
        payload = {}
        i = 0
        while i < len(args):
            a = args[i]
            if a == "--email" and i + 1 < len(args):
                payload["email"] = args[i + 1]; i += 2
            elif a == "--name" and i + 1 < len(args):
                parts = args[i + 1].split(" ", 1)
                payload["first_name"] = parts[0]
                if len(parts) > 1:
                    payload["last_name"] = parts[1]
                i += 2
            elif a == "--first-name" and i + 1 < len(args):
                payload["first_name"] = args[i + 1]; i += 2
            elif a == "--last-name" and i + 1 < len(args):
                payload["last_name"] = args[i + 1]; i += 2
            elif a == "--company" and i + 1 < len(args):
                payload["organization_name"] = args[i + 1]; i += 2
            elif a == "--domain" and i + 1 < len(args):
                payload["domain"] = args[i + 1]; i += 2
            elif a == "--linkedin-url" and i + 1 < len(args):
                payload["linkedin_url"] = args[i + 1]; i += 2
            else:
                i += 1
    payload.setdefault("reveal_personal_emails", True)
    out(apollo_request("POST", "/people/match", payload))


def cmd_bulk_enrich_people(args):
    """Enrich multiple people in one call.

    Accepts a JSON array of person objects (email, first_name, last_name,
    organization_name, domain, linkedin_url) as the first argument.

    Usage: bulk_enrich_people '[{"email":"a@x.com"},{"first_name":"Bob","organization_name":"Acme"}]'
    Note: each enrichment costs Apollo credits.
    """
    if not args:
        raise SystemExit(
            "Usage: bulk_enrich_people '[{\"email\":\"a@x.com\"},{...}]'"
        )
    details = json.loads(args[0])
    if not isinstance(details, list):
        details = [details]
    payload = {"details": details, "reveal_personal_emails": True}
    out(apollo_request("POST", "/people/bulk_match", payload))


def cmd_create_contact(args):
    """Create a new contact in Apollo CRM.

    Accepts a JSON object with any of:
      first_name, last_name, email, title, organization_name,
      phone_numbers, linkedin_url, website_url, label_names

    Usage: create_contact '{"first_name":"Jane","last_name":"Smith","email":"jane@acme.com","title":"VP Sales","organization_name":"Acme Corp"}'
    """
    if not args:
        raise SystemExit('Usage: create_contact \'{"first_name":"...","email":"..."}\'')
    contact = json.loads(args[0])
    out(apollo_request("POST", "/contacts", {"contact": contact}))


def cmd_update_contact(args):
    """Update fields on an existing contact.

    Usage: update_contact <contact_id> '{"title":"CRO","email":"new@acme.com"}'
    """
    if len(args) < 2:
        raise SystemExit("Usage: update_contact <contact_id> '{\"field\":\"value\"}'")
    contact_id, payload_raw = args[0], args[1]
    out(apollo_request("PUT", f"/contacts/{contact_id}", {"contact": json.loads(payload_raw)}))


def cmd_list_contacts(args):
    """List contacts with optional pagination.

    Flags: --page --per-page
    """
    flags, _ = parse_flags(args, {
        "--page":     ("page",     int),
        "--per-page": ("per_page", int),
    })
    params = {"page": flags.get("page", 1), "per_page": flags.get("per_page", 25)}
    out(apollo_request("GET", "/contacts", params=params))


# ── Organizations / Accounts ───────────────────────────────────────────────────

def cmd_search_organizations(args):
    """Search for companies by name, domain, industry, size, or location.

    Flags: --name --domain --location --employees (e.g. "51-200")
           --industry --technology --keyword --page --per-page
    Or pass a raw JSON filter object.

    Examples:
      search_organizations --domain stripe.com
      search_organizations --location "San Francisco" --employees "11-50"
      search_organizations '{"num_employees_ranges":["201-500"],"organization_locations":["United States"]}'
    """
    if args and args[0].lstrip().startswith("{"):
        payload = json.loads(args[0])
    else:
        payload = {}
        i = 0
        while i < len(args):
            a = args[i]
            if a == "--name" and i + 1 < len(args):
                payload["q_organization_name"] = args[i + 1]; i += 2
            elif a == "--domain" and i + 1 < len(args):
                payload.setdefault("organization_domains", []).append(args[i + 1]); i += 2
            elif a == "--location" and i + 1 < len(args):
                payload.setdefault("organization_locations", []).append(args[i + 1]); i += 2
            elif a == "--employees" and i + 1 < len(args):
                payload.setdefault("num_employees_ranges", []).append(args[i + 1]); i += 2
            elif a == "--industry" and i + 1 < len(args):
                payload.setdefault("q_organization_keyword_tags", []).append(args[i + 1]); i += 2
            elif a == "--technology" and i + 1 < len(args):
                payload.setdefault("currently_using_any_of_technology_uids", []).append(args[i + 1]); i += 2
            elif a == "--keyword" and i + 1 < len(args):
                payload["q_keywords"] = args[i + 1]; i += 2
            elif a == "--page" and i + 1 < len(args):
                payload["page"] = int(args[i + 1]); i += 2
            elif a == "--per-page" and i + 1 < len(args):
                payload["per_page"] = int(args[i + 1]); i += 2
            else:
                i += 1

    payload.setdefault("page", 1)
    payload.setdefault("per_page", 10)
    out(apollo_request("POST", "/mixed_companies/search", payload))


def cmd_get_account(args):
    """Get an account/organization by its Apollo account ID.

    Usage: get_account <account_id>
    """
    if not args:
        raise SystemExit("Usage: get_account <account_id>")
    out(apollo_request("GET", f"/accounts/{args[0]}"))


def cmd_enrich_organization(args):
    """Enrich an organization record — returns headcount, revenue, tech stack, etc.

    Flags: --domain --name
    Or pass a raw JSON object.

    Examples:
      enrich_organization --domain stripe.com
      enrich_organization --name "Stripe"
    """
    if args and args[0].lstrip().startswith("{"):
        payload = json.loads(args[0])
    else:
        flags, _ = parse_flags(args, {
            "--domain": ("domain", str),
            "--name":   ("name",   str),
        })
        payload = flags
    if not payload:
        raise SystemExit("Provide at least --domain or --name")
    out(apollo_request("POST", "/organizations/enrich", payload))


def cmd_create_account(args):
    """Create a new account/company in Apollo CRM.

    Accepts a JSON object with any of:
      name, domain, phone, raw_address, website_url, blog_url,
      linkedin_url, twitter_url, annual_revenue, num_employees

    Usage: create_account '{"name":"Acme Corp","domain":"acme.com"}'
    """
    if not args:
        raise SystemExit('Usage: create_account \'{"name":"Acme Corp","domain":"acme.com"}\'')
    account = json.loads(args[0])
    out(apollo_request("POST", "/accounts", {"account": account}))


def cmd_update_account(args):
    """Update fields on an existing account.

    Usage: update_account <account_id> '{"phone":"555-9999","annual_revenue":5000000}'
    """
    if len(args) < 2:
        raise SystemExit("Usage: update_account <account_id> '{\"field\":\"value\"}'")
    account_id, payload_raw = args[0], args[1]
    out(apollo_request("PUT", f"/accounts/{account_id}", {"account": json.loads(payload_raw)}))


# ── Sequences ─────────────────────────────────────────────────────────────────

def cmd_list_sequences(args):
    """List all email sequences/campaigns.

    Flags: --page --per-page
    """
    flags, _ = parse_flags(args, {
        "--page":     ("page",     int),
        "--per-page": ("per_page", int),
    })
    params = {"page": flags.get("page", 1), "per_page": flags.get("per_page", 25)}
    out(apollo_request("GET", "/emailer_campaigns", params=params))


def cmd_get_sequence(args):
    """Get details for a single sequence by ID.

    Usage: get_sequence <sequence_id>
    """
    if not args:
        raise SystemExit("Usage: get_sequence <sequence_id>")
    out(apollo_request("GET", f"/emailer_campaigns/{args[0]}"))


def cmd_add_to_sequence(args):
    """Add one or more contacts to a sequence.

    Usage:
      add_to_sequence <sequence_id> <contact_id> [<contact_id> ...]
      add_to_sequence <sequence_id> --email-account-id <id> <contact_id> ...

    The --email-account-id flag sets which connected inbox sends the emails.
    Get available email account IDs via list_email_accounts.
    """
    if len(args) < 2:
        raise SystemExit(
            "Usage: add_to_sequence <sequence_id> [--email-account-id <id>] <contact_id> ..."
        )
    seq_id = args[0]
    remaining = args[1:]
    email_account_id = None
    contact_ids = []
    i = 0
    while i < len(remaining):
        if remaining[i] == "--email-account-id" and i + 1 < len(remaining):
            email_account_id = remaining[i + 1]; i += 2
        else:
            contact_ids.append(remaining[i]); i += 1
    if not contact_ids:
        raise SystemExit("At least one contact_id is required")
    payload = {"contact_ids": contact_ids}
    if email_account_id:
        payload["send_email_from_email_account_id"] = email_account_id
    out(apollo_request("POST", f"/emailer_campaigns/{seq_id}/add_contact_ids", payload))


# ── Tasks ─────────────────────────────────────────────────────────────────────

def cmd_create_task(args):
    """Create a task on a contact.

    Flags: --type TYPE --contact-id ID [--note TEXT] [--due-at YYYY-MM-DD]
    Valid types: call  email  action_item  linkedin_message  linkedin_connect
    Or pass a raw JSON object.

    Examples:
      create_task --type call --contact-id <id> --note "Follow up on demo" --due-at 2026-06-01
      create_task '{"type":"email","contact_id":"<id>","note":"Send proposal","due_at":"2026-06-01"}'
    """
    if args and args[0].lstrip().startswith("{"):
        payload = json.loads(args[0])
    else:
        flags, _ = parse_flags(args, {
            "--type":       ("type",       str),
            "--contact-id": ("contact_id", str),
            "--note":       ("note",       str),
            "--due-at":     ("due_at",     str),
        })
        payload = {k: v for k, v in flags.items() if v is not None}
    if "type" not in payload:
        raise SystemExit("--type is required (call|email|action_item|linkedin_message|linkedin_connect)")
    if "contact_id" not in payload:
        raise SystemExit("--contact-id is required")
    out(apollo_request("POST", "/tasks", {"task": payload}))


def cmd_search_tasks(args):
    """Search and filter tasks.

    Flags: --type TYPE  --status STATUS  --contact-id ID  --page  --per-page
    Status values: pending  complete  deleted  scheduled
    Type values:   call  email  action_item  linkedin_message  linkedin_connect
    """
    payload = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--type" and i + 1 < len(args):
            payload.setdefault("types", []).append(args[i + 1]); i += 2
        elif a == "--status" and i + 1 < len(args):
            payload["status"] = args[i + 1]; i += 2
        elif a == "--contact-id" and i + 1 < len(args):
            payload.setdefault("contact_ids", []).append(args[i + 1]); i += 2
        elif a == "--page" and i + 1 < len(args):
            payload["page"] = int(args[i + 1]); i += 2
        elif a == "--per-page" and i + 1 < len(args):
            payload["per_page"] = int(args[i + 1]); i += 2
        else:
            i += 1
    payload.setdefault("page", 1)
    payload.setdefault("per_page", 25)
    out(apollo_request("POST", "/tasks/search", payload))


def cmd_complete_task(args):
    """Mark a task as complete.

    Usage: complete_task <task_id>
    """
    if not args:
        raise SystemExit("Usage: complete_task <task_id>")
    out(apollo_request("PUT", f"/tasks/{args[0]}", {"task": {"status": "complete"}}))


# ── Opportunities / Deals ─────────────────────────────────────────────────────

def cmd_list_opportunities(args):
    """List deals/opportunities.

    Flags: --page --per-page
    """
    flags, _ = parse_flags(args, {
        "--page":     ("page",     int),
        "--per-page": ("per_page", int),
    })
    params = {"page": flags.get("page", 1), "per_page": flags.get("per_page", 25)}
    out(apollo_request("GET", "/opportunities/search", params=params))


def cmd_create_opportunity(args):
    """Create a new deal/opportunity.

    Flags: --name --amount --account-id --contact-id (repeatable) --stage
    Or pass a raw JSON object.

    Examples:
      create_opportunity --name "Acme Q3 Deal" --amount 15000 --account-id <id> --stage "Demo Scheduled"
      create_opportunity '{"name":"Big Deal","amount":50000,"account_id":"<id>","contact_ids":["<id>"],"stage_name":"Proposal Sent"}'
    """
    if args and args[0].lstrip().startswith("{"):
        payload = json.loads(args[0])
    else:
        payload = {}
        i = 0
        while i < len(args):
            a = args[i]
            if a == "--name" and i + 1 < len(args):
                payload["name"] = args[i + 1]; i += 2
            elif a == "--amount" and i + 1 < len(args):
                payload["amount"] = float(args[i + 1]); i += 2
            elif a == "--account-id" and i + 1 < len(args):
                payload["account_id"] = args[i + 1]; i += 2
            elif a == "--contact-id" and i + 1 < len(args):
                payload.setdefault("contact_ids", []).append(args[i + 1]); i += 2
            elif a == "--stage" and i + 1 < len(args):
                payload["stage_name"] = args[i + 1]; i += 2
            else:
                i += 1
    out(apollo_request("POST", "/opportunities", {"opportunity": payload}))


def cmd_update_opportunity(args):
    """Update fields on an existing opportunity.

    Usage: update_opportunity <opportunity_id> '{"amount":60000,"stage_name":"Closed Won"}'
    """
    if len(args) < 2:
        raise SystemExit("Usage: update_opportunity <opportunity_id> '{\"field\":\"value\"}'")
    opp_id, payload_raw = args[0], args[1]
    out(apollo_request(
        "PUT", f"/opportunities/{opp_id}", {"opportunity": json.loads(payload_raw)}
    ))


# ── Utility ───────────────────────────────────────────────────────────────────

def cmd_list_email_accounts(args):
    """List all connected email accounts (inboxes) for sending context.

    Use the returned IDs in add_to_sequence --email-account-id.
    """
    out(apollo_request("GET", "/email_accounts"))


def cmd_list_labels(args):
    """List all labels/custom lists defined in the account."""
    out(apollo_request("GET", "/labels"))


# ── Command registry ──────────────────────────────────────────────────────────

COMMANDS = {
    # People / Contacts
    "search_people":        cmd_search_people,
    "get_contact":          cmd_get_contact,
    "enrich_person":        cmd_enrich_person,
    "bulk_enrich_people":   cmd_bulk_enrich_people,
    "create_contact":       cmd_create_contact,
    "update_contact":       cmd_update_contact,
    "list_contacts":        cmd_list_contacts,
    # Organizations / Accounts
    "search_organizations": cmd_search_organizations,
    "get_account":          cmd_get_account,
    "enrich_organization":  cmd_enrich_organization,
    "create_account":       cmd_create_account,
    "update_account":       cmd_update_account,
    # Sequences
    "list_sequences":       cmd_list_sequences,
    "get_sequence":         cmd_get_sequence,
    "add_to_sequence":      cmd_add_to_sequence,
    # Tasks
    "create_task":          cmd_create_task,
    "search_tasks":         cmd_search_tasks,
    "complete_task":        cmd_complete_task,
    # Opportunities
    "list_opportunities":   cmd_list_opportunities,
    "create_opportunity":   cmd_create_opportunity,
    "update_opportunity":   cmd_update_opportunity,
    # Utility
    "list_email_accounts":  cmd_list_email_accounts,
    "list_labels":          cmd_list_labels,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print("Apollo.io skill — usage: python3 scripts/apollo_io.py <command> [args]\n")
        groups = [
            ("People / Contacts", [
                "search_people", "get_contact", "enrich_person",
                "bulk_enrich_people", "create_contact", "update_contact", "list_contacts",
            ]),
            ("Organizations / Accounts", [
                "search_organizations", "get_account", "enrich_organization",
                "create_account", "update_account",
            ]),
            ("Sequences", ["list_sequences", "get_sequence", "add_to_sequence"]),
            ("Tasks", ["create_task", "search_tasks", "complete_task"]),
            ("Opportunities", ["list_opportunities", "create_opportunity", "update_opportunity"]),
            ("Utility", ["list_email_accounts", "list_labels"]),
        ]
        for group_name, cmds in groups:
            print(f"{group_name}:")
            for name in cmds:
                fn = COMMANDS[name]
                doc_first = (fn.__doc__ or "").strip().splitlines()[0]
                print(f"  {name:<28}  {doc_first}")
            print()
        print("Run 'python3 scripts/apollo_io.py <command> --help' to see full command docs.")
        sys.exit(0)

    cmd_name = sys.argv[1]
    if cmd_name not in COMMANDS:
        raise SystemExit(
            f"Unknown command: {cmd_name!r}. Run without args to list all commands."
        )

    cmd_args = sys.argv[2:]
    if cmd_args and cmd_args[0] in ("-h", "--help"):
        fn = COMMANDS[cmd_name]
        print(f"{cmd_name}:\n{fn.__doc__ or '(no description)'}")
        sys.exit(0)

    COMMANDS[cmd_name](cmd_args)


if __name__ == "__main__":
    main()
