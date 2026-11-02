# campaign-attribution-audit — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason, not "it broke." If the
failure mode was technical, name the specific issue. If the failure
mode was scope or approach, name that.]

**What we tried instead:** [The next attempt, which may also have
failed and may have its own entry below]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search — e.g., "rendering, pandoc,
quarto" or "scope, scrollytelling, decoration"]

---

## Entries

[New entries get added here, most recent at the top]

### 2026-10-22 — Single event export exceeded the Pages file limit
**What we tried:** one events.csv.gz download (31 MB). **Why it failed:** Cloudflare Pages caps files at 25 MB. **Instead:** monthly split; joined rows hash to the manifest. **Status:** Resolved. **Tags:** deploy, cloudflare, export size

### 2026-10-22 — Bounds checks keyed on session_start produced false failures
**What we tried:** session continuity and R1 guards keyed on session_start. **Why it failed:** defect A3 drops session_start by design. **Instead:** keyed on all events. **Status:** Resolved. **Tags:** bound_check, A3, false failure

### 2026-11-02 — Per-deploy custom-domain job never attached the domain
**What we tried:** a CI job attaching campaignmath.lailarallc.com each deploy. **Why it failed:** the first attach registered the domain without a CNAME, so it deactivated; the job's grep never matched spaced JSON, so it never noticed. **Instead:** one manual repair (CNAME + re-validate), then removed the job. **Status:** Resolved. **Tags:** cloudflare, custom domain, CNAME, CI

### 2026-11-02 — Commit message claimed an edit that had failed
**What we tried:** committed after a string patch that did not apply (CRLF mismatch), with a message describing it (3e88d98). **Why it failed:** didn't read the diff before committing. **Instead:** fdb0773 applied it and said so; patches now normalize line endings. **Status:** Resolved. **Tags:** git, CRLF, read the diff
