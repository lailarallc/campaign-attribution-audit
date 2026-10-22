"""Generate the Quellwood Provisions universe: one quarter (Q3 2026) of GA4-export-shaped
events plus a campaign spend table, with tracking defects seeded at the pinned rates.

Architecture (docs/design-gate.md section 1): true journeys first, tracking layer second,
every defect application logged. Seed-locked and byte-stable; no wall-clock values.

Inputs:  data/parameters.json (scripts/roll_parameters.py)
Outputs (committed):   data/spend.csv, data/manifest.json
Outputs (gitignored, hashed in the manifest; regenerate with this script):
         data/export/events.csv.gz   flattened GA4 BigQuery-style event export (what an analyst gets)
         data/truth/sessions.csv.gz  true sessions (never read by the engine)
         data/truth/seed_log.csv.gz  every planted defect (never read by the engine's attribution)
"""

import csv
import gzip
import hashlib
import io
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cmlib

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
P = json.loads((DATA / "parameters.json").read_text(encoding="utf-8"))
D = {k: v["value"] for k, v in P["draws"].items()}
ROSTER = P["roster"]

SEED = int(hashlib.sha256(b"quellwood-provisions/2026-q3/universe/v1").hexdigest(), 16) % (2**32)

# ---- Pinned by the design gate (docs/design-gate.md) ----
Q_START = datetime(2026, 7, 1, tzinfo=timezone.utc)
Q_DAYS = 92                                      # Q3 2026; one fixed quarter (gate 2)
TARGET_REVENUE = 500_000                         # gate 2 (A)
PLATFORM_SPLIT = {"Google": 0.45, "Meta": 0.40, "Other paid": 0.15}   # gate 3 (A)
RATE = {                                          # gate 5 (A-tags, owner-accepted 2026-10-16)
    "A1": 0.06, "A2a": 0.12, "A2b": 0.02, "A3": 0.01, "A4a": 0.03, "A4b": 0.005,
    "A5": 0.04, "A6_paid": 0.03, "A6_other": 0.01, "A7": 0.02, "A9": 0.20,
}
SAFARI_SHARE = 0.3042                             # A8: StatCounter US all-platform, Sep 2026
ITP_DAYS = 7                                      # A8 mechanism
SITE = "https://quellwoodprovisions.com"

# ---- Structural constants (no published figure; shapes follow DIR anchors) ----
# In-quarter session share by sub-channel.
SESSION_SHARE = {
    "direct": 0.18, "organic_search": 0.24, "brand_search": 0.05, "nonbrand_search": 0.10,
    "shopping": 0.05, "meta_prospecting": 0.12, "meta_retargeting": 0.05, "tiktok": 0.04,
    "organic_social": 0.06, "email": 0.07, "referral": 0.025, "affiliate": 0.015,
}
# Per-session CVR: ThoughtMetric Q3 2025 levels (CITE, vendor) x cvr_scale; within-platform
# multipliers keep each platform's aggregate at its benchmark (brand converts above non-brand,
# retargeting above prospecting).
TM = {"email": 8.43, "google": 3.95, "meta": 3.87, "tiktok": 3.07, "organic_search": 2.02, "organic_social": 1.42}
S = D["cvr_scale"]
CVR = {
    "email": TM["email"] * S,
    "brand_search": TM["google"] * S * 1.8, "nonbrand_search": TM["google"] * S * 0.7, "shopping": TM["google"] * S * 1.0,
    "meta_prospecting": TM["meta"] * S * 0.6, "meta_retargeting": TM["meta"] * S * 2.0,
    "tiktok": TM["tiktok"] * S, "organic_search": TM["organic_search"] * S, "organic_social": TM["organic_social"] * S,
    "direct": D["cvr_direct_pct"], "referral": D["cvr_referral_pct"], "affiliate": D["cvr_referral_pct"],
}
CVR = {k: v / 100 for k, v in CVR.items()}
# Multi-session journeys: first touch skews to discovery, middle touches to return channels
# (DIR: Racklify, Adtriba). The last touch follows share x CVR so per-channel CVR holds.
FIRST = {"meta_prospecting": 22, "nonbrand_search": 16, "organic_search": 18, "tiktok": 6, "organic_social": 7,
         "referral": 4, "affiliate": 3, "shopping": 6, "direct": 8, "email": 5, "brand_search": 5}
MIDDLE = {"direct": 24, "brand_search": 16, "email": 16, "meta_retargeting": 12, "organic_search": 12,
          "meta_prospecting": 5, "shopping": 5, "nonbrand_search": 4, "organic_social": 3, "referral": 2, "affiliate": 1}
PAID_SUBS = {"brand_search", "nonbrand_search", "shopping", "meta_prospecting", "meta_retargeting", "tiktok", "affiliate"}
EMAIL_WEIGHTS = {"E01": 0.5, "E02": 0.3, "E03": 0.2}
DEVICES = [("mobile", 0.62), ("desktop", 0.34), ("tablet", 0.04)]
BROWSERS = [("Safari", SAFARI_SHARE), ("Chrome", 0.5382), ("Samsung Internet", 0.07), ("Edge", 0.05), ("Firefox", 0.0376)]
HOUR_W = [2, 1, 1, 1, 1, 2, 3, 5, 6, 6, 6, 6, 7, 7, 6, 6, 6, 7, 8, 9, 10, 9, 7, 4]
DOW_W = [1.02, 1.00, 0.98, 0.99, 0.96, 0.95, 1.10]   # Mon..Sun
ORGANIC_SOURCES = [("google", 0.86), ("bing", 0.09), ("duckduckgo", 0.05)]
SOCIAL_REFERRERS = [("l.instagram.com", 0.45), ("m.facebook.com", 0.25), ("pinterest.com", 0.20), ("tiktok.com", 0.10)]
REFERRERS = [("giftguide-weekly.net", 0.30), ("pantryshelfreview.com", 0.25), ("hotsaucenotes.blog", 0.25),
             ("smallbatchfinds.org", 0.20)]
CATALOG = [  # invented products (item_id, name, price)
    ("QW-CC-01", "Smoked Chili Crisp", 14.00), ("QW-CC-02", "Garlic Chili Crisp", 14.00),
    ("QW-CC-03", "Chili Crisp Trio", 38.00), ("QW-SB-01", "Campfire Spice Blend", 11.00),
    ("QW-SB-02", "Citrus Pepper Blend", 11.00), ("QW-SB-03", "Spice Library (6)", 58.00),
    ("QW-PR-01", "Sour Cherry Preserves", 13.00), ("QW-PR-02", "Fig & Black Pepper Jam", 13.00),
    ("QW-HN-01", "Hot Honey", 16.00), ("QW-HN-02", "Smoked Honey", 16.00),
    ("QW-GB-01", "Pantry Starter Box", 64.00), ("QW-GB-02", "Heat Seeker Gift Box", 78.00),
    ("QW-GB-03", "The Quellwood Hamper", 128.00), ("QW-SC-01", "Green Hot Sauce", 12.00),
    ("QW-SC-02", "Fermented Red Sauce", 12.00),
]
CATALOG_W = [9, 7, 5, 6, 5, 3, 4, 4, 6, 4, 3, 3, 1.5, 5, 5]


def wpick(rng, items):
    """items: list of (value, weight) or dict value->weight."""
    if isinstance(items, dict):
        items = list(items.items())
    tot = sum(w for _, w in items)
    r = rng.random() * tot
    for v, w in items:
        r -= w
        if r <= 0:
            return v
    return items[-1][0]


def day_weights():
    w = []
    for d in range(Q_DAYS):
        day = Q_START + timedelta(days=d)
        trend = 1.0 + 0.10 * d / Q_DAYS                # mild growth through the quarter
        w.append(DOW_W[day.weekday()] * trend)
    return w


DAY_W = day_weights()


def rand_time_in_quarter(rng):
    d = wpick(rng, list(zip(range(Q_DAYS), DAY_W)))
    h = wpick(rng, list(zip(range(24), HOUR_W)))
    return Q_START + timedelta(days=d, hours=h, seconds=rng.randint(0, 3599))


def campaign_for(rng, sub):
    if sub == "email":
        return wpick(rng, EMAIL_WEIGHTS)
    if sub not in PAID_SUBS:
        return None
    camps = [(c["campaign_id"], c["platform_share"]) for c in ROSTER if c["sub_channel"] == sub]
    return wpick(rng, camps)


def main():
    rng = random.Random(SEED)
    by_id = {c["campaign_id"]: c for c in ROSTER}

    # ---------------- 1. True journeys ----------------
    mean_price = sum(p * w for (_, _, p), w in zip(CATALOG, CATALOG_W)) / sum(CATALOG_W)
    lam = max(0.0, D["aov_target_usd"] / mean_price - 1.0)
    site_cvr = sum(SESSION_SHARE[c] * CVR[c] for c in SESSION_SHARE)
    n_orders = round(TARGET_REVENUE / D["aov_target_usd"])
    total_sessions = round(n_orders / site_cvr)
    last_w = {c: SESSION_SHARE[c] * CVR[c] for c in SESSION_SHARE}

    users = []      # dict(uid, browser, device)
    sessions = []   # true sessions: dict(sid, uid, ts, sub, cid, converts)
    orders = []     # dict(oid, uid, sid, ts, value_cents, items)

    def new_user():
        u = {"uid": len(users), "browser": wpick(rng, BROWSERS), "device": wpick(rng, DEVICES)}
        if u["browser"] == "Safari" and rng.random() < 0.8:
            u["device"] = "mobile"
        users.append(u)
        return u["uid"]

    def add_session(uid, ts, sub, converts=False):
        s = {"sid": len(sessions), "uid": uid, "ts": ts, "sub": sub, "cid": campaign_for(rng, sub),
             "converts": converts, "bot": False}
        sessions.append(s)
        return s

    for _ in range(n_orders):
        uid = new_user()
        t_purchase = rand_time_in_quarter(rng)
        if rng.random() < D["single_session_share"]:
            subs = [wpick(rng, last_w)]
        else:
            extra = 1 + min(10, int(rng.expovariate(1.0 / (D["extra_sessions_mean"] - 0.5))))
            subs = [wpick(rng, FIRST)] + [wpick(rng, MIDDLE) for _ in range(extra - 1)] + [wpick(rng, last_w)]
        times = [t_purchase]
        for _ in range(len(subs) - 1):
            gap = min(30.0, rng.expovariate(1.0 / D["gap_days_mean"]))
            times.append(times[-1] - timedelta(days=gap, seconds=rng.randint(600, 7200)))
        times.reverse()
        for i, (sub, ts) in enumerate(zip(subs, times)):
            s = add_session(uid, ts - (timedelta(minutes=rng.randint(4, 25)) if i == len(subs) - 1 else timedelta(0)),
                            sub, converts=(i == len(subs) - 1))
        k = 1 + (min(7, _poisson(rng, lam)) if lam > 0 else 0)
        items = [wpick(rng, list(zip(CATALOG, CATALOG_W))) for _ in range(k)]
        value = sum(round(p * 100) for _, _, p in items)
        orders.append({"oid": len(orders), "uid": uid, "sid": s["sid"], "ts": t_purchase, "value_cents": value,
                       "items": [i for i, _, _ in items]})

    # Non-converting traffic fills each sub-channel to its in-quarter session count.
    in_q = lambda ts: Q_START <= ts < Q_START + timedelta(days=Q_DAYS)
    have = {c: 0 for c in SESSION_SHARE}
    for s in sessions:
        if in_q(s["ts"]):
            have[s["sub"]] += 1
    for sub in SESSION_SHARE:
        need = round(total_sessions * SESSION_SHARE[sub]) - have[sub]
        while need > 0:
            uid = new_user()
            n = min(need, wpick(rng, [(1, 80), (2, 15), (3, 5)]))
            t = rand_time_in_quarter(rng)
            for j in range(n):
                add_session(uid, t, sub)
                t = t + timedelta(days=rng.uniform(0.5, 12))
                if not in_q(t):
                    t = rand_time_in_quarter(rng)
            need -= n

    # Bots (A6): extra non-human sessions. Paid: 3% of paid-click sessions; other: 1% of other.
    seed_log = []
    brng = random.Random(SEED + 6)
    paid_q = [s for s in sessions if s["sub"] in PAID_SUBS and in_q(s["ts"])]
    other_q = [s for s in sessions if s["sub"] not in PAID_SUBS and in_q(s["ts"])]
    n_bot_paid = round(len(paid_q) * RATE["A6_paid"] / (1 - RATE["A6_paid"]))
    n_bot_other = round(len(other_q) * RATE["A6_other"] / (1 - RATE["A6_other"]))
    paid_w = [(s["sub"], 1) for s in paid_q]
    for i in range(n_bot_paid + n_bot_other):
        paid = i < n_bot_paid
        sub = wpick(brng, paid_w) if paid else wpick(brng, [("direct", 70), ("referral", 30)])
        u = {"uid": len(users), "browser": "Chrome", "device": "desktop"}
        users.append(u)
        t = Q_START + timedelta(seconds=brng.randint(0, Q_DAYS * 86400 - 1))
        s = {"sid": len(sessions), "uid": u["uid"], "ts": t, "sub": sub,
             "cid": campaign_for(brng, sub), "converts": False, "bot": True}
        sessions.append(s)
        seed_log.append(("A6", s["sid"], "", "paid" if paid else "other"))

    # ---------------- 2. Tracking layer ----------------
    trng = {k: random.Random(SEED + 100 + i) for i, k in enumerate(["A1", "A2", "A3", "A5", "A7", "A4", "id", "ev"])}
    sessions.sort(key=lambda s: (s["ts"], s["sid"]))
    user_sessions = {}
    for s in sessions:
        user_sessions.setdefault(s["uid"], []).append(s)

    # A8: Safari users get a new client_id when a session comes >7 days after the previous one.
    client_of = {}
    cid_counter = [0]
    idr = trng["id"]

    def new_client(ts):
        cid_counter[0] += 1
        return f"{idr.randint(100000000, 2147483647)}.{int(ts.timestamp())}"

    for uid, ss in user_sessions.items():
        cur = new_client(ss[0]["ts"])
        prev = None
        for s in ss:
            if prev and users[uid]["browser"] == "Safari" and (s["ts"] - prev["ts"]).total_seconds() > ITP_DAYS * 86400:
                cur = new_client(s["ts"])
                seed_log.append(("A8", s["sid"], "", "client_id reset"))
            client_of[s["sid"]] = cur
            prev = s

    rec = {}   # sid -> recorded (source, medium, campaign, gclid, landing_query)
    for s in sessions:
        rec[s["sid"]] = clean_recording(trng["ev"], s, by_id)

    humans = [s for s in sessions if not s["bot"]]
    tagged = [s for s in humans if s["sub"] in ("meta_prospecting", "meta_retargeting", "tiktok", "email", "affiliate")]
    for s in humans:   # A1: untagged paid-social and email clicks fall to (direct)/(none)
        if s["sub"] in ("meta_prospecting", "meta_retargeting", "tiktok", "email") and trng["A1"].random() < RATE["A1"]:
            rec[s["sid"]] = ("(direct)", "(none)", "(not set)", "", "")
            seed_log.append(("A1", s["sid"], "", "utm stripped"))
    r2 = trng["A2"]
    for s in tagged:   # A2a / A2b on sessions that still carry UTMs
        src, med, camp, gclid, _ = rec[s["sid"]]
        if src == "(direct)":
            continue
        x = r2.random()
        if x < RATE["A2a"]:
            if r2.random() < D["a2a_case_share"]:
                camp2 = case_variant(r2, camp)
                src2 = src.capitalize() if r2.random() < 0.5 else src
                rec[s["sid"]] = (src2, med, camp2, gclid, utm_q(src2, med, camp2))
                seed_log.append(("A2a", s["sid"], "case", camp2))
            else:
                camp2 = spelling_variant(r2, camp)
                rec[s["sid"]] = (src, med, camp2, gclid, utm_q(src, med, camp2))
                seed_log.append(("A2a", s["sid"], "spelling", camp2))
        elif x < RATE["A2a"] + RATE["A2b"]:
            if s["sub"] == "email":
                src2, med2 = "quellwood_news", "newsletter"
            elif s["sub"] == "affiliate":
                src2, med2 = "partner_network", "partner"
            else:
                src2, med2 = "meta" if s["sub"] != "tiktok" else "tt", "social_ad"
            rec[s["sid"]] = (src2, med2, camp, gclid, utm_q(src2, med2, camp))
            seed_log.append(("A2b", s["sid"], "", f"{src2}/{med2}"))
    for s in humans:   # A7: gclid lost on a redirect; Google referrer survives -> google/organic
        if s["sub"] in ("brand_search", "nonbrand_search", "shopping") and trng["A7"].random() < RATE["A7"]:
            rec[s["sid"]] = ("google", "organic", "(organic)", "", "")
            seed_log.append(("A7", s["sid"], "", "gclid stripped"))
    no_session_start = set()
    for s in humans:   # A3: session_start missing -> source/medium (not set)
        if trng["A3"].random() < RATE["A3"]:
            no_session_start.add(s["sid"])
            seed_log.append(("A3", s["sid"], "", "no session_start"))

    # Purchases: transaction ids in time order; A4a duplicates, A4b missing ids, A5 gateway.
    orders.sort(key=lambda o: (o["ts"], o["oid"]))
    r4, r5 = trng["A4"], trng["A5"]
    for n, o in enumerate(orders):
        o["txn"] = f"QW{104000 + n}"
        o["dup"] = o["noid"] = o["gateway"] = False
        x = r4.random()
        if x < RATE["A4a"]:
            o["dup"] = True
            seed_log.append(("A4a", o["sid"], o["txn"], "purchase sent twice"))
        elif x < RATE["A4a"] + RATE["A4b"]:
            o["noid"] = True
            seed_log.append(("A4b", o["sid"], o["txn"], "transaction_id missing"))
        if r5.random() < RATE["A5"]:
            o["gateway"] = True
            seed_log.append(("A5", o["sid"], o["txn"], "paypal.com referral at checkout return"))

    # ---------------- 3. Write the event export ----------------
    order_of_sid = {o["sid"]: o for o in orders}
    session_number = {}
    seen_client = set()
    ev = trng["ev"]
    rows = []
    for s in sessions:
        if not in_q(s["ts"]):
            continue   # export window = the quarter; earlier journey touches are not in the file
        u = users[s["uid"]]
        client = client_of[s["sid"]]
        session_number[client] = session_number.get(client, 0) + 1
        sess_id = int(s["ts"].timestamp())
        src, med, camp, gclid, q = rec[s["sid"]]
        base = {"user_pseudo_id": client, "ga_session_id": sess_id, "ga_session_number": session_number[client],
                "device_category": u["device"], "browser": u["browser"]}
        t = s["ts"]
        landing = landing_page(ev, s["sub"])
        if s["sid"] not in no_session_start:
            rows.append(event(t, "session_start", base, src, med, camp, gclid, SITE + landing + q))
        if client not in seen_client:
            seen_client.add(client)
            rows.append(event(t, "first_visit", base, src, med, camp, gclid, SITE + landing + q))
        rows.append(event(t, "page_view", base, page_location=SITE + landing + q,
                          engagement=0 if s["bot"] else ev.randint(3000, 60000)))
        if s["bot"]:
            continue
        o = order_of_sid.get(s["sid"])
        pages = 1 + min(8, int(ev.expovariate(0.9)))
        for _ in range(pages - 1):
            t = t + timedelta(seconds=ev.randint(10, 120))
            rows.append(event(t, "page_view", base, page_location=SITE + ev.choice(BROWSE_PAGES),
                              engagement=ev.randint(3000, 90000)))
        funnel = 4 if o else (3 if ev.random() < 0.025 else 2 if ev.random() < 0.05 else 1 if ev.random() < 0.22 else 0)
        names = ["view_item", "add_to_cart", "begin_checkout"]
        for i in range(min(funnel, 3)):
            t = t + timedelta(seconds=ev.randint(15, 180))
            rows.append(event(t, names[i], base, page_location=SITE + ["/products/item", "/cart", "/checkout"][i]))
        if o:
            pbase, psrc = base, None
            if o["gateway"]:   # A5: returns from PayPal in a new referral session
                t = t + timedelta(seconds=ev.randint(60, 300))
                session_number[client] += 1
                pbase = dict(base, ga_session_id=int(t.timestamp()), ga_session_number=session_number[client])
                rows.append(event(t, "session_start", pbase, "paypal.com", "referral", "(referral)", "",
                                  SITE + "/checkout/thank-you"))
                rows.append(event(t, "page_view", pbase, page_location=SITE + "/checkout/thank-you",
                                  engagement=ev.randint(2000, 15000)))
            t = t + timedelta(seconds=ev.randint(20, 120))
            o["ts_recorded"] = t
            p = event(t, "purchase", pbase, page_location=SITE + "/checkout/thank-you")
            p.update({"transaction_id": "" if o["noid"] else o["txn"], "value": f"{o['value_cents'] / 100:.2f}",
                      "currency": "USD", "items": "|".join(o["items"])})
            rows.append(p)
            if o["dup"]:   # A4a: thank-you page reload re-sends the purchase
                p2 = dict(p, event_timestamp=p["event_timestamp"] + ev.randint(5, 90) * 1_000_000)
                rows.append(p2)
    rows.sort(key=lambda r: (r["event_timestamp"], r["user_pseudo_id"], EVENT_ORDER[r["event_name"]]))

    # ---------------- 4. Spend table (platform view) ----------------
    paid_true_linear = true_linear_paid_revenue(sessions, orders, user_sessions)
    total_spend = sum(paid_true_linear.values()) / D["blended_roas"]
    clicks = {}
    for s in sessions:
        if in_q(s["ts"]) and s["cid"]:
            clicks[s["cid"]] = clicks.get(s["cid"], 0) + 1
    recorded_lc = recorded_last_click(rows)   # for A9: platform reports +20% over GA4 last-click
    spend_rows = []
    for c in ROSTER:
        cid = c["campaign_id"]
        if c["platform"] == "Email":
            spend = 0.0
        else:
            spend = total_spend * PLATFORM_SPLIT[c["platform"]] * c["platform_share"]
        k = clicks.get(cid, 0)
        conv, rev = recorded_lc.get(cid, (0, 0.0))
        is_paid = c["platform"] != "Email"
        spend_rows.append({
            "campaign_id": cid, "campaign_name": c["campaign_name"], "platform": c["platform"],
            "spend": f"{spend:.2f}",
            "impressions": round(k / (D["ctr_pct"] / 100)) if is_paid else "",
            "clicks": k,
            "platform_conversions": round(conv * (1 + RATE["A9"])) if is_paid else conv,
            "platform_conversion_value": f"{rev * (1 + RATE['A9']) if is_paid else rev:.2f}",
        })
    for c in ROSTER:
        if c["platform"] != "Email":
            seed_log.append(("A9", -1, c["campaign_id"], "platform-reported = GA4 last-click x 1.20"))

    # ---------------- 5. Write outputs ----------------
    (DATA / "export").mkdir(parents=True, exist_ok=True)
    (DATA / "truth").mkdir(parents=True, exist_ok=True)
    cols = ["event_date", "event_timestamp", "event_name", "user_pseudo_id", "ga_session_id", "ga_session_number",
            "source", "medium", "campaign", "gclid", "page_location", "engagement_time_msec", "transaction_id",
            "value", "currency", "items", "device_category", "browser"]
    write_gz(DATA / "export" / "events.csv.gz", cols, rows)
    tcols = ["sid", "uid", "ts", "sub", "campaign_id", "converts", "bot", "browser", "client_id", "in_quarter",
             "recorded_source", "recorded_medium", "recorded_campaign"]
    trows = []
    for s in sorted(sessions, key=lambda s: s["sid"]):
        src, med, camp, _, _ = rec[s["sid"]]
        trows.append({"sid": s["sid"], "uid": s["uid"], "ts": s["ts"].strftime("%Y-%m-%dT%H:%M:%SZ"), "sub": s["sub"],
                      "campaign_id": s["cid"] or "", "converts": int(s["converts"]), "bot": int(s["bot"]),
                      "browser": users[s["uid"]]["browser"], "client_id": client_of[s["sid"]],
                      "in_quarter": int(in_q(s["ts"])), "recorded_source": src, "recorded_medium": med,
                      "recorded_campaign": camp})
    write_gz(DATA / "truth" / "sessions.csv.gz", tcols, trows)
    ocols = ["txn", "sid", "uid", "value_cents", "dup", "noid", "gateway"]
    write_gz(DATA / "truth" / "orders.csv.gz", ocols,
             [{k: (int(o[k]) if isinstance(o[k], bool) else o[k]) for k in ocols} for o in orders])
    write_gz(DATA / "truth" / "seed_log.csv.gz", ["class", "sid", "ref", "detail"],
             [dict(zip(["class", "sid", "ref", "detail"], r)) for r in seed_log])
    with open(DATA / "spend.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(spend_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(spend_rows)

    manifest = {"seed": SEED, "quarter": "2026-Q3", "orders": len(orders), "events": len(rows),
                "sessions_in_quarter": sum(1 for s in sessions if in_q(s["ts"])),
                "files": {}}
    for p in ["export/events.csv.gz", "truth/sessions.csv.gz", "truth/orders.csv.gz", "truth/seed_log.csv.gz",
              "spend.csv", "parameters.json"]:
        manifest["files"][p] = hashlib.sha256((DATA / p).read_bytes()).hexdigest()
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "files"}, indent=1))


# ---------------- helpers ----------------
EVENT_ORDER = {"session_start": 0, "first_visit": 1, "page_view": 2, "view_item": 3, "add_to_cart": 4,
               "begin_checkout": 5, "purchase": 6}
BROWSE_PAGES = ["/collections/chili-crisp", "/collections/gift-boxes", "/collections/spice-blends",
                "/collections/preserves", "/products/smoked-chili-crisp", "/products/heat-seeker-gift-box",
                "/products/spice-library", "/pages/our-kitchen", "/collections/all", "/products/hot-honey"]
LANDING = {"brand_search": "/", "nonbrand_search": "/collections/chili-crisp", "shopping": "/products/smoked-chili-crisp",
           "meta_prospecting": "/collections/gift-boxes", "meta_retargeting": "/cart", "tiktok": "/products/smoked-chili-crisp",
           "email": "/collections/new", "affiliate": "/products/heat-seeker-gift-box", "referral": "/products/spice-library",
           "organic_social": "/collections/chili-crisp", "organic_search": "/", "direct": "/"}


def landing_page(rng, sub):
    return LANDING[sub] if rng.random() < 0.6 else rng.choice(BROWSE_PAGES)


def _poisson(rng, lam):
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def utm_q(src, med, camp):
    return f"?utm_source={src}&utm_medium={med}&utm_campaign={camp}"


def clean_recording(rng, s, by_id):
    sub, cid = s["sub"], s["cid"]
    camp = by_id[cid]["campaign_name"] if cid else None
    if sub in ("brand_search", "nonbrand_search", "shopping"):
        g = f"Cj0KCQjw{rng.getrandbits(64):016x}"
        return ("google", "cpc", camp, g, f"?gclid={g}")
    if sub in ("meta_prospecting", "meta_retargeting"):
        src = "facebook" if rng.random() < 0.62 else "instagram"
        return (src, "paid_social", camp, "", utm_q(src, "paid_social", camp))
    if sub == "tiktok":
        return ("tiktok", "paid_social", camp, "", utm_q("tiktok", "paid_social", camp))
    if sub == "affiliate":
        return ("partner_network", "affiliate", camp, "", utm_q("partner_network", "affiliate", camp))
    if sub == "email":
        return ("quellwood_news", "email", camp, "", utm_q("quellwood_news", "email", camp))
    if sub == "organic_search":
        return (wpick(rng, ORGANIC_SOURCES), "organic", "(organic)", "", "")
    if sub == "organic_social":
        return (wpick(rng, SOCIAL_REFERRERS), "referral", "(referral)", "", "")
    if sub == "referral":
        return (wpick(rng, REFERRERS), "referral", "(referral)", "", "")
    return ("(direct)", "(none)", "(not set)", "", "")


def case_variant(rng, camp):
    parts = camp.split("_")
    return "_".join(p.upper() if p in ("qw",) else (p.capitalize() if rng.random() < 0.5 else p) for p in parts) \
        if rng.random() < 0.7 else camp.upper()


def spelling_variant(rng, camp):
    options = [camp.replace("_", "-"), camp.replace("chili", "chilli"), camp.replace("qw_", "qw "),
               camp.rstrip("s"), camp.replace("-", "")]
    options = [o for o in options if o != camp] or [camp + "_v2"]
    return rng.choice(options)


def event(t, name, base, src=None, med=None, camp=None, gclid=None, page_location="", engagement=""):
    r = {"event_date": t.strftime("%Y%m%d"), "event_timestamp": int(t.timestamp()) * 1_000_000,
         "event_name": name, **base,
         "source": src or "", "medium": med or "", "campaign": camp or "", "gclid": gclid or "",
         "page_location": page_location, "engagement_time_msec": engagement,
         "transaction_id": "", "value": "", "currency": "", "items": ""}
    return r


def write_gz(path, cols, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    with open(path, "wb") as f:
        with gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0, compresslevel=6) as gz:
            gz.write(buf.getvalue().encode("utf-8"))


def true_linear_paid_revenue(sessions, orders, user_sessions):
    """True-layer linear credit to paid campaigns (sets total spend via blended ROAS)."""
    out = {}
    for o in orders:
        path = [s for s in user_sessions[o["uid"]] if s["ts"] <= o["ts"] and s["sub"] != "direct"]
        if not path:
            continue
        for s in path:
            if s["cid"] and s["sub"] in PAID_SUBS:
                out[s["cid"]] = out.get(s["cid"], 0.0) + o["value_cents"] / 100 / len(path)
    return out


def recorded_last_click(rows):
    """GA4 last-non-direct-click conversions and revenue per campaign, from the recorded rows
    (the number a platform-vs-GA4 comparison starts from). Uses the engine's own logic."""
    import attribute
    res = attribute.attribute_rows(rows, {c["campaign_name"].lower(): c["campaign_id"] for c in ROSTER})
    return res["last_click_by_campaign"]


if __name__ == "__main__":
    main()
