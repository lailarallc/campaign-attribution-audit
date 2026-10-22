"""Generate the Quellwood Provisions universe: one quarter (Q3 2026) of GA4-export-shaped
events plus a daily campaign spend table, with tracking defects seeded at the pinned rates.

Architecture (docs/design-gate.md section 1): true journeys first, tracking layer second,
every defect application logged. Seed-locked and byte-stable; no wall-clock values.
v1.1 answers the realism review (docs/realism-review.md F2-F10, F13) in structure only:
no section 5 rate and no pinned A row changed. New structural randomness uses separate streams.

Inputs:  data/parameters.json (scripts/roll_parameters.py)
Outputs (committed):   data/spend.csv (daily, per campaign), data/manifest.json
Outputs (gitignored, content-hashed in the manifest; regenerate with this script):
         data/export/events.csv.gz   flattened GA4 BigQuery-style event export (what an analyst gets)
         data/truth/sessions.csv.gz  true sessions (never read by the engine's attribution)
         data/truth/orders.csv.gz    true orders
         data/truth/seed_log.csv.gz  every planted defect
"""

import base64
import csv
import gzip
import hashlib
import io
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
P = json.loads((DATA / "parameters.json").read_text(encoding="utf-8"))
D = {k: v["value"] for k, v in P["draws"].items()}
V = {k: v["value"] for k, v in P["v1_1"]["draws"].items()}
VC = P["v1_1"]["campaign"]
ROSTER = P["roster"]
BY_ID = {c["campaign_id"]: c for c in ROSTER}


def seed_of(s):
    return int(hashlib.sha256(s.encode()).hexdigest(), 16) % (2**32)


SEED = seed_of("quellwood-provisions/2026-q3/universe/v1")
SEED11 = seed_of("quellwood-provisions/2026-q3/universe/v1.1")

# ---- Pinned by the design gate (docs/design-gate.md) ----
TZ_OFFSET = timedelta(hours=-4)                   # property time zone America/New_York (EDT all quarter)
Q_START = datetime(2026, 7, 1, 4, 0, tzinfo=timezone.utc)   # 2026-07-01 00:00 local
Q_DAYS = 92                                       # Q3 2026; one fixed quarter (gate 2)
TARGET_REVENUE = 500_000                          # gate 2 (A)
PLATFORM_SPLIT = {"Google": 0.45, "Meta": 0.40, "Other paid": 0.15}   # gate 3 (A)
RATE = {                                          # gate 5 (A-tags, owner-accepted 2026-10-16)
    "A1": 0.06, "A2a": 0.12, "A2b": 0.02, "A3": 0.01, "A4a": 0.03, "A4b": 0.005,
    "A5": 0.04, "A6_paid": 0.03, "A6_other": 0.01, "A7": 0.02, "A9": 0.20,
}
ITP_DAYS = 7                                      # A8 mechanism
SITE = "https://quellwoodprovisions.com"

# ---- Structural constants (no published figure; shapes follow DIR anchors) ----
# Session share: paid platforms as totals (traffic inside a platform follows pinned spend / CPC,
# F13); non-paid channels by sub-channel.
PLATFORM_SESSION_SHARE = {"Google": 0.20, "Meta": 0.17, "Other paid": 0.055}
NONPAID_SHARE = {"direct": 0.18, "organic_search": 0.24, "organic_social": 0.06, "email": 0.07, "referral": 0.025}
EMAIL_SPLIT = {"E01": 0.5, "E02": 0.3, "E03": 0.2}
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
FIRST = {"meta_prospecting": 22, "nonbrand_search": 16, "organic_search": 18, "tiktok": 6, "organic_social": 7,
         "referral": 4, "affiliate": 3, "shopping": 6, "direct": 8, "email": 5, "brand_search": 5}
MIDDLE = {"direct": 24, "brand_search": 16, "email": 16, "meta_retargeting": 12, "organic_search": 12,
          "meta_prospecting": 5, "shopping": 5, "nonbrand_search": 4, "organic_social": 3, "referral": 2, "affiliate": 1}
PAID_SUBS = {"brand_search", "nonbrand_search", "shopping", "meta_prospecting", "meta_retargeting", "tiktok", "affiliate"}
TAGGED_SUBS = {"meta_prospecting", "meta_retargeting", "tiktok", "email", "affiliate"}
GOOGLE_SUBS = {"brand_search", "nonbrand_search", "shopping"}
# F2: who has history. Probability the user existed before the quarter, by their first in-quarter
# session's sub-channel; retention channels require history.
EXISTING_P = {"email": 0.97, "meta_retargeting": 1.0, "brand_search": 0.55, "direct": 0.45,
              "organic_search": 0.20, "shopping": 0.15}
REQUIRES_HISTORY = {"meta_retargeting"}
REQUIRES_HISTORY_CAMPAIGN = {"E02", "E03", "M04", "M05"}
# F7: pages per session differ by channel (extra pages beyond the landing page, mean).
EXTRA_PAGES = {"email": 2.2, "brand_search": 2.0, "organic_search": 1.6, "direct": 1.8, "meta_prospecting": 0.8,
               "tiktok": 0.6, "meta_retargeting": 1.6, "nonbrand_search": 1.2, "shopping": 1.0, "referral": 1.4,
               "organic_social": 0.9, "affiliate": 1.2}
# F8: device first, then browser conditional on device. Overall Safari ~30.5% (A8 pin 30.42%).
DEVICES = [("mobile", 0.62), ("desktop", 0.34), ("tablet", 0.04)]
BROWSER_BY_DEVICE = {
    "mobile": [("Safari", 0.38), ("Chrome", 0.50), ("Samsung Internet", 0.12)],
    "desktop": [("Chrome", 0.62), ("Safari", 0.14), ("Edge", 0.15), ("Firefox", 0.09)],
    "tablet": [("Safari", 0.55), ("Chrome", 0.45)],
}
OS_OF = {("mobile", "Safari"): [("iOS", 1)], ("mobile", "Chrome"): [("Android", 0.82), ("iOS", 0.18)],
         ("mobile", "Samsung Internet"): [("Android", 1)],
         ("desktop", "Chrome"): [("Windows", 0.68), ("Macintosh", 0.27), ("Linux", 0.05)],
         ("desktop", "Safari"): [("Macintosh", 1)], ("desktop", "Edge"): [("Windows", 1)],
         ("desktop", "Firefox"): [("Windows", 0.6), ("Macintosh", 0.3), ("Linux", 0.1)],
         ("tablet", "Safari"): [("iOS", 1)], ("tablet", "Chrome"): [("Android", 1)]}
STATES = [("California", 12), ("Texas", 9), ("New York", 8), ("Florida", 7), ("Illinois", 4.5), ("Pennsylvania", 4.5),
          ("Ohio", 3.5), ("Georgia", 3.5), ("North Carolina", 3.3), ("Michigan", 3), ("New Jersey", 3), ("Virginia", 2.8),
          ("Washington", 2.7), ("Massachusetts", 2.5), ("Arizona", 2.3), ("Tennessee", 2.1), ("Colorado", 2),
          ("Minnesota", 1.8), ("Maryland", 1.8), ("Oregon", 1.4), ("Wisconsin", 1.7), ("Missouri", 1.8),
          ("Indiana", 2), ("South Carolina", 1.6), ("Connecticut", 1.1), ("Utah", 1.0), ("Louisiana", 1.3)]
TAX = {"California": 0.0825, "Texas": 0.0625, "New York": 0.08, "Florida": 0.06, "Illinois": 0.0625,
       "Pennsylvania": 0.06, "Washington": 0.065, "New Jersey": 0.06625}
CA_PROVINCES = [("Ontario", 5), ("British Columbia", 3), ("Quebec", 2)]
# F6: local-time hour weights (evening peak for food e-commerce); email clicks peak after a morning send.
HOUR_W = [2, 1, 1, 1, 1, 1, 2, 3, 5, 6, 6, 6, 7, 7, 6, 6, 6, 7, 8, 10, 11, 10, 7, 4]
HOUR_W_EMAIL = [1, 1, 1, 1, 1, 1, 3, 6, 12, 11, 9, 7, 7, 6, 5, 5, 5, 5, 5, 6, 6, 5, 3, 2]
DOW_W = [1.02, 1.00, 0.98, 0.99, 0.96, 0.95, 1.10]   # Mon..Sun
PROMO_DAYS = {65, 66, 67, 68}                    # Sep 4-7 local (Labor Day weekend sale)
FLIGHTS = {"M01": ("launch", 47), "T01": ("pause", 33, 46), "G03": ("boost", 62, 1.7)}   # day indexes
NEWSLETTER_DAYS = sorted({d for d in range(Q_DAYS) if (Q_START + timedelta(days=d, hours=4)).weekday() == 3} | {65})
ORGANIC_SOURCES = [("google", 0.86), ("bing", 0.09), ("duckduckgo", 0.05)]
SEARCH_REF = {"google": "https://www.google.com/", "bing": "https://www.bing.com/", "duckduckgo": "https://duckduckgo.com/"}
SOCIAL_REFERRERS = [("l.instagram.com", 0.45), ("m.facebook.com", 0.25), ("pinterest.com", 0.20), ("tiktok.com", 0.10)]
REFERRERS = [("giftguide-weekly.net", 0.30), ("pantryshelfreview.com", 0.25), ("hotsaucenotes.blog", 0.25),
             ("smallbatchfinds.org", 0.20)]
AFF_PUBLISHERS = ["thepantrydispatch.com", "giftlistlab.net", "spicyreviewroundup.com", "kitchencartnotes.com",
                  "dealsforcooks.net", "foodgiftfinder.com", "heatseekerjournal.blog", "weeknightpantry.net",
                  "snackscoutdaily.com", "condimentclub.blog"]
CATALOG = [  # invented products (item_id, slug, price)
    ("QW-CC-01", "smoked-chili-crisp", 14.00), ("QW-CC-02", "garlic-chili-crisp", 14.00),
    ("QW-CC-03", "chili-crisp-trio", 38.00), ("QW-SB-01", "campfire-spice-blend", 11.95),
    ("QW-SB-02", "citrus-pepper-blend", 11.95), ("QW-SB-03", "spice-library", 58.00),
    ("QW-PR-01", "sour-cherry-preserves", 12.95), ("QW-PR-02", "fig-black-pepper-jam", 12.95),
    ("QW-HN-01", "hot-honey", 15.50), ("QW-HN-02", "smoked-honey", 15.50),
    ("QW-GB-01", "pantry-starter-box", 64.00), ("QW-GB-02", "heat-seeker-gift-box", 78.00),
    ("QW-GB-03", "quellwood-hamper", 128.00), ("QW-SC-01", "green-hot-sauce", 11.50),
    ("QW-SC-02", "fermented-red-sauce", 11.50),
]
CATALOG_W = [9, 7, 5, 6, 5, 3, 4, 4, 6, 4, 3, 3, 1.5, 5, 5]
PRODUCT_PAGES = ["/products/" + c[1] for c in CATALOG]
COLLECTIONS = ["/collections/chili-crisp", "/collections/gift-boxes", "/collections/spice-blends",
               "/collections/preserves", "/collections/all", "/pages/our-kitchen", "/collections/hot-honey"]
LANDING = {   # F10: per campaign (falls back to sub-channel)
    "G01": "/", "G02": "/collections/chili-crisp", "G03": "/collections/gift-boxes", "G04": "/collections/spice-blends",
    "G05": "/products/smoked-chili-crisp", "M01": "/collections/gift-boxes", "M02": "/products/smoked-chili-crisp",
    "M03": "/collections/all", "M04": "/collections/chili-crisp", "M05": "/cart", "T01": "/products/smoked-chili-crisp",
    "A01": "/products/heat-seeker-gift-box", "E01": "/collections/new", "E02": "/cart", "E03": "/pages/our-kitchen",
    "referral": "/products/spice-library", "organic_social": "/collections/chili-crisp", "organic_search": "/",
    "direct": "/",
}
LINKS_PER_CAMPAIGN = {"meta_prospecting": 14, "meta_retargeting": 8, "tiktok": 8, "affiliate": 10,
                      "brand_search": 4, "nonbrand_search": 6, "shopping": 5, "E02": 4, "E03": 4}


def wpick(rng, items):
    if isinstance(items, dict):
        items = list(items.items())
    tot = sum(w for _, w in items)
    r = rng.random() * tot
    for v, w in items:
        r -= w
        if r <= 0:
            return v
    return items[-1][0]


def day_weight(d, key):
    day = Q_START + timedelta(days=d, hours=4)
    w = DOW_W[day.weekday()] * (1.0 + 0.08 * d / Q_DAYS) * (1.45 if d in PROMO_DAYS else 1.0)
    f = FLIGHTS.get(key)
    if f:
        if f[0] == "launch" and d < f[1]:
            return 0.0
        if f[0] == "pause" and f[1] <= d <= f[2]:
            return 0.0
        if f[0] == "boost" and d >= f[1]:
            w *= f[2]
    return w


_DAYW = {}


def draw_time(rng, key):
    """Session start time for a campaign id or sub-channel key, in UTC, from local-time weights."""
    if key == "E01":   # newsletter: send day plus decay (F6)
        send = rng.choice(NEWSLETTER_DAYS)
        d = min(Q_DAYS - 1, send + wpick(rng, [(0, 68), (1, 22), (2, 7), (3, 3)]))
        h = wpick(rng, list(zip(range(24), HOUR_W_EMAIL)))
    else:
        if key not in _DAYW:
            _DAYW[key] = [(d, day_weight(d, key)) for d in range(Q_DAYS)]
        d = wpick(rng, _DAYW[key])
        h = wpick(rng, list(zip(range(24), HOUR_W_EMAIL if key in ("E02", "E03") else HOUR_W)))
    return Q_START + timedelta(days=d, hours=h, seconds=rng.randint(0, 3599), microseconds=rng.randint(0, 999_999))


def live(cid, ts):
    d = int((ts - Q_START).total_seconds() // 86400)
    return d < 0 or d >= Q_DAYS or day_weight(d, cid) > 0


def main():
    rng = random.Random(SEED)
    r11 = random.Random(SEED11)                    # all v1.1 structure draws
    rlink = random.Random(SEED11 + 1)

    # ---- traffic inside each paid platform follows pinned spend / CPC (F13) ----
    camp_w = {}   # campaign -> share of all sessions
    for plat, ps in PLATFORM_SESSION_SHARE.items():
        cs = [c for c in ROSTER if c["platform"] == plat]
        raw = {c["campaign_id"]: c["platform_share"] / VC[c["campaign_id"]]["cpc_usd"] for c in cs}
        tot = sum(raw.values())
        for cid, v in raw.items():
            camp_w[cid] = ps * v / tot
    for cid, sh in EMAIL_SPLIT.items():
        camp_w[cid] = NONPAID_SHARE["email"] * sh
    sub_share = dict(NONPAID_SHARE)
    for cid, w in camp_w.items():
        sub = BY_ID[cid]["sub_channel"]
        if sub != "email":
            sub_share[sub] = sub_share.get(sub, 0) + w
    sub_camps = {}
    for cid, w in camp_w.items():
        sub_camps.setdefault(BY_ID[cid]["sub_channel"], []).append((cid, w))
    # Hold each benchmark group's traffic-weighted CVR at its ThoughtMetric level, whatever the
    # spend/CPC traffic mix turns out to be (the multipliers' stated intent).
    for group in (("brand_search", "nonbrand_search"), ("meta_prospecting", "meta_retargeting")):
        mean = sum(sub_share[g] * CVR[g] for g in group) / sum(sub_share[g] for g in group)
        target = (TM["google"] if group[0] == "brand_search" else TM["meta"]) * S / 100
        for g in group:
            CVR[g] *= target / mean

    def campaign_for(rg, sub, ts=None):
        if sub not in sub_camps:
            return None
        opts = [(c, w) for c, w in sub_camps[sub] if ts is None or live(c, ts)]
        return wpick(rg, opts) if opts else None

    # ---- links: ads, ad groups, email sends / flow steps (F4) ----
    links = {}   # cid -> list[(link_id, weight)]
    for c in ROSTER:
        cid, sub = c["campaign_id"], c["sub_channel"]
        if cid == "E01":
            links[cid] = [(f"E01-send-{d:02d}", 1.0) for d in NEWSLETTER_DAYS]
            continue
        n = LINKS_PER_CAMPAIGN.get(cid, LINKS_PER_CAMPAIGN.get(sub, 4))
        ws = [1.0 / (k + 1) ** 1.1 for k in range(n)]
        rlink.shuffle(ws)
        links[cid] = [(f"{cid}-L{k + 1:02d}", w) for k, w in enumerate(ws)]

    def link_for(rg, cid, ts):
        if cid == "E01":
            d = int((ts - Q_START).total_seconds() // 86400)
            sends = [x for x in NEWSLETTER_DAYS if x <= d]
            return f"E01-send-{(sends[-1] if sends else NEWSLETTER_DAYS[0]):02d}"
        return wpick(rg, links[cid])

    mean_price = sum(p * w for (_, _, p), w in zip(CATALOG, CATALOG_W)) / sum(CATALOG_W)
    site_cvr = sum(sub_share[c] * CVR[c] for c in sub_share)
    n_orders = round(TARGET_REVENUE / D["aov_target_usd"])
    n_repeat = round(n_orders * V["repeat_order_share"])
    n_first = n_orders - n_repeat
    total_sessions = round(n_orders / site_cvr)
    last_w = {c: sub_share[c] * CVR[c] for c in sub_share}

    users, sessions, orders = [], [], []

    def new_user(rg):
        dev = wpick(rg, DEVICES)
        br = wpick(rg, BROWSER_BY_DEVICE[dev])
        country = "United States" if rg.random() < 0.985 else "Canada"
        region = wpick(rg, STATES) if country == "United States" else wpick(rg, CA_PROVINCES)
        u = {"uid": len(users), "device": dev, "browser": br, "os": wpick(rg, OS_OF[(dev, br)]),
             "country": country, "region": region, "prior": 0, "first_seen": None, "bot": False}
        users.append(u)
        return u["uid"]

    def add_session(uid, ts, sub, converts=False, cid=None):
        if cid is None:
            cid = campaign_for(rng, sub, ts)
        if sub in PAID_SUBS and cid is None:   # campaign paused/not launched: the click never happened
            sub, cid = ("organic_social" if sub == "tiktok" else "organic_search"), None
        s = {"sid": len(sessions), "uid": uid, "ts": ts, "sub": sub, "cid": cid,
             "link": link_for(r11, cid, ts) if cid else "", "converts": converts, "bot": False, "kind": ""}
        sessions.append(s)
        return s

    def make_order(uid, s, t_purchase):
        k = 1 + _poisson(rng, max(0.0, D["aov_target_usd"] / mean_price - 1.0))
        picks = [wpick(rng, list(zip(CATALOG, CATALOG_W))) for _ in range(min(8, k))]
        lines = {}
        for item in picks:
            lines[item] = lines.get(item, 0) + 1
        o = {"oid": len(orders), "uid": uid, "sid": s["sid"], "ts": t_purchase,
             "lines": sorted(lines.items(), key=lambda x: x[0][0])}
        o["value_cents"] = sum(round(i[2] * 100) * q for i, q in o["lines"])
        orders.append(o)
        return o

    # ---------------- 1. True journeys ----------------
    for _ in range(n_first):
        uid = new_user(r11)
        last_sub = wpick(rng, last_w)
        last_cid = campaign_for(rng, last_sub)
        t_purchase = draw_time(rng, last_cid or last_sub)
        if rng.random() < D["single_session_share"]:
            subs = [last_sub]
        else:
            extra = 1 + min(10, int(rng.expovariate(1.0 / (D["extra_sessions_mean"] - 0.5))))
            subs = [wpick(rng, FIRST)] + [wpick(rng, MIDDLE) for _ in range(extra - 1)] + [last_sub]
        times = [t_purchase]
        for _ in range(len(subs) - 1):   # F3: gaps floored well past the 30-minute session timeout
            gap = min(30.0, max(0.04, rng.expovariate(1.0 / D["gap_days_mean"])))
            times.append(times[-1] - timedelta(days=gap, seconds=rng.randint(600, 7200)))
        times.reverse()
        for i, (sub, ts) in enumerate(zip(subs, times)):
            last = i == len(subs) - 1
            s = add_session(uid, ts - (timedelta(minutes=rng.randint(4, 25)) if last else timedelta(0)), sub,
                            converts=last, cid=last_cid if last else None)
        make_order(uid, s, t_purchase)

    # Repeat orders and post-purchase browsing (F2), separate stream.
    buyers = list(orders)
    rr = random.Random(SEED11 + 2)
    eligible = [o for o in buyers if (o["ts"] - Q_START).days <= 75]
    for o in rr.sample(eligible, n_repeat):
        t = o["ts"] + timedelta(days=rr.uniform(8, 40), seconds=rr.randint(0, 86399))
        if t >= Q_START + timedelta(days=Q_DAYS):
            t = o["ts"] + timedelta(days=rr.uniform(2, 6))
        sub = wpick(rr, [("email", 45), ("direct", 25), ("brand_search", 18), ("organic_search", 12)])
        cid = wpick(rr, [("E01", 70), ("E02", 30)]) if sub == "email" else campaign_for(rr, sub, t)
        s = add_session(o["uid"], t - timedelta(minutes=rr.randint(4, 20)), sub, converts=True, cid=cid)
        make_order(o["uid"], s, t)
    for o in buyers:
        if rr.random() < V["post_purchase_share"]:
            t = o["ts"]
            for _ in range(rr.choice([1, 1, 2])):
                t = t + timedelta(days=rr.uniform(1, 25), seconds=rr.randint(0, 86399))
                sub = wpick(rr, [("direct", 40), ("email", 40), ("organic_search", 20)])
                cid = wpick(rr, [("E01", 80), ("E02", 20)]) if sub == "email" else None
                add_session(o["uid"], t, sub, cid=cid)

    # Non-converting traffic fills each sub-channel (and each campaign) to its in-quarter count.
    q_end = Q_START + timedelta(days=Q_DAYS)
    in_q = lambda ts: Q_START <= ts < q_end
    have = {c: 0 for c in sub_share}
    camp_have = {c: 0 for c in camp_w}
    for s in sessions:
        if in_q(s["ts"]):
            have[s["sub"]] += 1
            if s["cid"]:
                camp_have[s["cid"]] += 1
    for sub in sub_share:
        need = round(total_sessions * sub_share[sub]) - have[sub]
        while need > 0:
            uid = new_user(r11)
            n = min(need, wpick(rng, [(1, 80), (2, 15), (3, 5)]))
            cid = None
            if sub in sub_camps:
                gaps = [(c, max(0.0, total_sessions * w - camp_have[c])) for c, w in sub_camps[sub]]
                cid = wpick(rng, gaps) if sum(g for _, g in gaps) > 0 else campaign_for(rng, sub)
            t = draw_time(rng, cid or sub)
            for _ in range(n):
                s = add_session(uid, t, sub, cid=cid if (cid and live(cid, t)) else None)
                if s["cid"]:
                    camp_have[s["cid"]] += 1
                t = t + timedelta(days=rng.uniform(0.5, 12))
                if not in_q(t):
                    t = draw_time(rng, cid or sub)
            need -= n

    # Space each user's sessions: a session must start well after the previous one ends (F3).
    order_by_sid = {o["sid"]: o for o in orders}
    by_user = {}
    for s in sessions:
        by_user.setdefault(s["uid"], []).append(s)
    for ss in by_user.values():
        ss.sort(key=lambda s: (s["ts"], s["sid"]))
        for prev, s in zip(ss, ss[1:]):
            if (s["ts"] - prev["ts"]).total_seconds() < 3600:
                shift = (prev["ts"] + timedelta(hours=1, minutes=rng.randint(5, 240))) - s["ts"]
                s["ts"] += shift
                if s["sid"] in order_by_sid:
                    order_by_sid[s["sid"]]["ts"] += shift

    # ---- history (F2): who existed before the quarter ----
    rh = random.Random(SEED11 + 3)
    user_sessions = {}
    for s in sorted(sessions, key=lambda s: (s["ts"], s["sid"])):
        user_sessions.setdefault(s["uid"], []).append(s)
    for uid, ss in user_sessions.items():
        first = ss[0]
        must = first["sub"] in REQUIRES_HISTORY or first["cid"] in REQUIRES_HISTORY_CAMPAIGN
        if must or rh.random() < EXISTING_P.get(first["sub"], 0.08):
            u = users[uid]
            u["prior"] = rh.randint(1, 3) if first["cid"] == "E03" else 1 + min(40, int(rh.expovariate(1 / 5)))
            back = rh.uniform(1, 25) if first["cid"] in ("E03", "M04", "M05", "E02") else rh.uniform(14, 700)
            u["first_seen"] = first["ts"] - timedelta(days=back)

    # ---- bots (A6), three profiles (F9) ----
    seed_log = []
    brng = random.Random(SEED + 6)
    rb = random.Random(SEED11 + 4)
    paid_q = [s for s in sessions if s["sub"] in PAID_SUBS and in_q(s["ts"])]
    other_q = [s for s in sessions if s["sub"] not in PAID_SUBS and in_q(s["ts"])]
    n_bot_paid = round(len(paid_q) * RATE["A6_paid"] / (1 - RATE["A6_paid"]))
    n_bot_other = round(len(other_q) * RATE["A6_other"] / (1 - RATE["A6_other"]))
    # Retargeting serves only audience members; a brand-new bot client cannot be in one.
    paid_w = [(s["cid"], 1) for s in paid_q if BY_ID[s["cid"]]["sub_channel"] != "meta_retargeting"]
    for i in range(n_bot_paid + n_bot_other):
        paid = i < n_bot_paid
        profile = wpick(rb, [("click_fraud", 55), ("single_hit", 35), ("crawler", 10)]) if paid else \
            wpick(rb, [("single_hit", 60), ("crawler", 40)])
        dev = "mobile" if profile == "click_fraud" and rb.random() < 0.7 else "desktop"
        br = wpick(rb, [("Chrome", 80), ("Safari", 12), ("Edge", 8)]) if dev == "desktop" else \
            wpick(rb, [("Chrome", 75), ("Safari", 25)])
        u = {"uid": len(users), "device": dev, "browser": br, "os": wpick(rb, OS_OF[(dev, br)]),
             "country": "United States",
             "region": wpick(rb, [("Virginia", 40), ("Oregon", 25), ("California", 20), ("Ohio", 15)]),
             "prior": 0, "first_seen": None, "bot": True}
        users.append(u)
        if paid:
            cid = wpick(brng, paid_w)
            sub = BY_ID[cid]["sub_channel"]
            t = draw_time(rb, cid)
        else:
            sub, cid = wpick(brng, [("direct", 70), ("referral", 30)]), None
            t = Q_START + timedelta(seconds=brng.randint(0, Q_DAYS * 86400 - 1), microseconds=rb.randint(0, 999_999))
        s = {"sid": len(sessions), "uid": u["uid"], "ts": t, "sub": sub, "cid": cid,
             "link": link_for(rb, cid, t) if cid else "", "converts": False, "bot": True, "kind": profile}
        sessions.append(s)
        seed_log.append(("A6", s["sid"], profile, "paid" if paid else "other"))

    # ---------------- 2. Tracking layer ----------------
    sessions.sort(key=lambda s: (s["ts"], s["sid"]))
    user_sessions = {}
    for s in sessions:
        user_sessions.setdefault(s["uid"], []).append(s)
    idr = random.Random(SEED + 100 + 6)

    client_of, client_first = {}, {}
    for uid, ss in user_sessions.items():
        u = users[uid]
        t0 = u["first_seen"] or ss[0]["ts"]
        cur = f"{idr.randint(100000000, 2147483647)}.{int(t0.timestamp())}"
        client_first[cur] = u["prior"]
        prev = None
        for s in ss:
            if prev and u["browser"] == "Safari" and not u["bot"] and \
                    (s["ts"] - prev["ts"]).total_seconds() > ITP_DAYS * 86400:
                cur = f"{idr.randint(100000000, 2147483647)}.{int(s['ts'].timestamp())}"
                client_first[cur] = 0
                seed_log.append(("A8", s["sid"], "", "client_id reset"))
            client_of[s["sid"]] = cur
            prev = s

    rec = {s["sid"]: clean_recording(r11, s) for s in sessions}

    # Link-level defects (F4): whole links are mis-built; one fixed bad string per link.
    rd = random.Random(SEED11 + 5)
    link_n = {}
    for s in sessions:
        if s["link"] and not s["bot"]:
            link_n[s["link"]] = link_n.get(s["link"], 0) + 1
    link_cid = {s["link"]: s["cid"] for s in sessions if s["link"]}
    humans = [s for s in sessions if not s["bot"]]
    a1_subs = ("meta_prospecting", "meta_retargeting", "tiktok", "email")
    base_a1 = sum(1 for s in humans if s["sub"] in a1_subs)
    base_tag = sum(1 for s in humans if s["sub"] in TAGGED_SUBS)
    base_goog = sum(1 for s in humans if s["sub"] in GOOGLE_SUBS)
    taken = set()

    def pick_links(pool, target):
        pool = sorted(pool)
        rd.shuffle(pool)
        got, cum = [], 0
        for l in pool:
            n = link_n.get(l, 0)
            if l in taken or n == 0:
                continue
            if cum + n <= target + n / 2:
                got.append(l)
                taken.add(l)
                cum += n
            if cum >= target:
                break
        return got

    a1_pool = [l for l, c in link_cid.items() if BY_ID[c]["sub_channel"] in a1_subs]
    tag_pool = [l for l, c in link_cid.items() if BY_ID[c]["sub_channel"] in TAGGED_SUBS]
    goog_pool = [l for l, c in link_cid.items() if BY_ID[c]["sub_channel"] in GOOGLE_SUBS]
    bad = {}
    for l in pick_links(a1_pool, RATE["A1"] * base_a1):
        bad[l] = ("A1", None)
    for l in pick_links(tag_pool, RATE["A2a"] * base_tag):
        camp = BY_ID[link_cid[l]]["campaign_name"]
        if rd.random() < D["a2a_case_share"]:
            bad[l] = ("A2a", ("case", case_variant(rd, camp), rd.random() < 0.5))
        else:
            bad[l] = ("A2a", ("spelling", spelling_variant(rd, camp), False))
    for l in pick_links(tag_pool, RATE["A2b"] * base_tag):
        bad[l] = ("A2b", None)
    for l in pick_links(goog_pool, RATE["A7"] * base_goog):
        bad[l] = ("A7", None)

    for s in sessions:
        b = bad.get(s["link"])
        if not b:
            continue
        cls, info = b
        src, med, camp, gclid, q = rec[s["sid"]]
        if cls == "A1":
            rec[s["sid"]] = ("(direct)", "(none)", "(not set)", "", "")
        elif cls == "A2a":
            kind, camp2, cap = info
            src2 = src.capitalize() if cap else src
            rec[s["sid"]] = (src2, med, camp2, gclid, utm_q(src2, med, camp2))
        elif cls == "A2b":
            if s["sub"] == "email":
                src2, med2 = "quellwood_news", "newsletter"
            elif s["sub"] == "affiliate":
                src2, med2 = "partner_network", "partner"
            else:
                src2, med2 = ("meta" if s["sub"] != "tiktok" else "tt"), "social_ad"
            rec[s["sid"]] = (src2, med2, camp, gclid, utm_q(src2, med2, camp))
        elif cls == "A7":   # redirect strips gclid; Google referrer survives -> google/organic
            rec[s["sid"]] = ("google", "organic", "(organic)", "", "")
        if not s["bot"]:
            seed_log.append((cls, s["sid"], s["link"], info[0] if info else ""))

    no_session_start = set()
    r3 = random.Random(SEED + 100 + 2)
    for s in humans:   # A3: tag-order race, per session
        if r3.random() < RATE["A3"]:
            no_session_start.add(s["sid"])
            seed_log.append(("A3", s["sid"], "", "no session_start"))

    orders.sort(key=lambda o: (o["ts"], o["oid"]))
    r4, r5 = random.Random(SEED + 100 + 5), random.Random(SEED + 100 + 3)
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
            seed_log.append(("A5", o["sid"], o["txn"], "paypal.com return after >30 min idle"))

    # ---------------- 3. Event export ----------------
    order_of_sid = {o["sid"]: o for o in orders}
    session_number = {}
    seen_client = set()
    ev = random.Random(SEED11 + 6)
    rows = []

    def push(t, name, base, page, ref="", src=None, med=None, camp=None, gclid=None, eng="", **extra):
        r = {"event_date": (t + TZ_OFFSET).strftime("%Y%m%d"),
             "event_timestamp": int(t.timestamp()) * 1_000_000 + t.microsecond,
             "event_name": name, **base, "page_location": page, "page_referrer": ref,
             "source": src or "", "medium": med or "", "campaign": camp or "", "gclid": gclid or "",
             "engagement_time_msec": eng}
        r.update(extra)
        rows.append(r)
        return r

    for s in sessions:
        u = users[s["uid"]]
        client = client_of[s["sid"]]
        if client not in session_number:
            session_number[client] = client_first.get(client, 0)
        session_number[client] += 1   # pre-quarter sessions count too, as they do in GA4
        if not in_q(s["ts"]):
            seen_client.add(client)
            continue   # export window = the quarter
        base = {"user_pseudo_id": client, "ga_session_id": int(s["ts"].timestamp()),
                "ga_session_number": session_number[client], "platform": "WEB",
                "device_category": u["device"], "operating_system": u["os"], "browser": u["browser"],
                "geo_country": u["country"], "geo_region": u["region"]}
        src, med, camp, gclid, q = rec[s["sid"]]
        landing = LANDING.get(s["cid"]) or LANDING.get(s["sub"], "/")
        if ev.random() < 0.35:
            landing = ev.choice(COLLECTIONS)
        ext_ref = external_referrer(ev, s, src)
        t = s["ts"]
        if s["sid"] not in no_session_start:
            push(t, "session_start", base, SITE + landing + q, ext_ref, src, med, camp, gclid)
        if client not in seen_client:
            seen_client.add(client)
            if session_number[client] == 1:
                push(t, "first_visit", base, SITE + landing + q, ext_ref, src, med, camp, gclid)
        o = order_of_sid.get(s["sid"])
        if s["bot"]:
            n = {"single_hit": 1, "click_fraud": ev.choice([1, 1, 2]), "crawler": ev.randint(3, 8)}[s["kind"]]
            prev_page = ext_ref
            for i in range(n):
                path = landing + q if i == 0 else ev.choice(COLLECTIONS + PRODUCT_PAGES)
                eng = "" if s["kind"] != "click_fraud" else ev.randint(150, 1500)
                push(t, "page_view", base, SITE + path, prev_page, eng=eng)
                prev_page = SITE + path
                t = t + timedelta(seconds=ev.uniform(0.4, 3.0))
            continue
        extra_n = min(9, int(ev.expovariate(1.0 / max(0.2, EXTRA_PAGES[s["sub"]]))))
        path_list = [landing + q] + [ev.choice(COLLECTIONS + PRODUCT_PAGES) for _ in range(extra_n)]
        funnel = 4 if o else (3 if ev.random() < 0.025 else 2 if ev.random() < 0.05 else 1 if ev.random() < 0.22 else 0)
        item = o["lines"][0][0] if o else wpick(ev, list(zip(CATALOG, CATALOG_W)))
        if funnel >= 1:
            path_list.append("/products/" + item[1])
        if funnel >= 2:
            path_list.append("/cart")
        if funnel >= 3:
            path_list.append("/checkouts/" + base64.b32encode(ev.getrandbits(80).to_bytes(10, "big")).decode().lower())
        prev_page, events = ext_ref, []
        for i, path in enumerate(path_list):
            dwell = ev.uniform(8, 140) if i < len(path_list) - 1 else ev.lognormvariate(2.2, 0.9)
            events.append((t, path, prev_page, dwell))
            prev_page = SITE + path
            t = t + timedelta(seconds=dwell)
        single = len(events) == 1
        for i, (tt, path, ref, dwell) in enumerate(events):
            eng = "" if (single and ev.random() < 0.3) else int(dwell * 1000 * ev.uniform(0.35, 0.95))
            push(tt, "page_view", base, SITE + path, ref, eng=eng)
            if funnel >= 1 and i == 1 + extra_n:   # the funnel's product page
                push(tt + timedelta(milliseconds=ev.randint(300, 2500)), "view_item", base, SITE + path, ref,
                     value=f"{item[2]:.2f}", currency="USD", items=f"{item[0]}:1:{item[2]:.2f}")
            if path == "/cart" and i > 0:
                push(tt - timedelta(milliseconds=ev.randint(800, 4000)), "add_to_cart", base,
                     SITE + events[i - 1][1], events[i - 1][2], value=f"{item[2]:.2f}", currency="USD",
                     items=f"{item[0]}:1:{item[2]:.2f}")
            if path.startswith("/checkouts/"):
                push(tt + timedelta(milliseconds=ev.randint(200, 900)), "begin_checkout", base, SITE + path, ref,
                     currency="USD")
        if o:
            pbase, pref = base, SITE + path_list[-1]
            if o["gateway"]:   # A5 / F3: PayPal return after >30 min idle starts a referral session
                t = t + timedelta(minutes=ev.uniform(31, 120))
                session_number[client] += 1
                pbase = dict(base, ga_session_id=int(t.timestamp()), ga_session_number=session_number[client])
                push(t, "session_start", pbase, SITE + "/checkout/thank-you", "https://www.paypal.com/",
                     "paypal.com", "referral", "(referral)", "")
                pref = "https://www.paypal.com/"
            t = t + timedelta(seconds=ev.uniform(2, 20))
            push(t, "page_view", pbase, SITE + "/checkout/thank-you", pref, eng=ev.randint(2000, 15000))
            sub_c = o["value_cents"] / 100
            ship = 0.0 if sub_c >= 60 else 6.95
            tax = round(sub_c * TAX.get(u["region"], 0.06), 2) if u["country"] == "United States" else 0.0
            items = "|".join(f"{i[0]}:{qn}:{i[2]:.2f}" for i, qn in o["lines"])
            t = t + timedelta(milliseconds=ev.randint(300, 2500))
            p = push(t, "purchase", pbase, SITE + "/checkout/thank-you", pref,
                     transaction_id="" if o["noid"] else o["txn"], value=f"{sub_c:.2f}", currency="USD",
                     shipping=f"{ship:.2f}", tax=f"{tax:.2f}", items=items)
            if o["dup"]:   # A4a: thank-you reload re-sends the purchase
                rows.append(dict(p, event_timestamp=p["event_timestamp"] + ev.randint(5_000_000, 90_000_000)))
    rows.sort(key=lambda r: (r["event_timestamp"], r["user_pseudo_id"], EVENT_ORDER[r["event_name"]]))

    # ---------------- 4. Daily spend table (F5) ----------------
    import attribute
    names = {c["campaign_name"].lower(): c["campaign_id"] for c in ROSTER}
    res = attribute.attribute_rows(rows, names)
    lc_day = {}
    for p, path, _ in res["paths"]:
        k = path[-1] if path else None
        if k in BY_ID:
            d = datetime.fromtimestamp(p["ts"] / 1e6, timezone.utc) + TZ_OFFSET
            key = (k, d.strftime("%Y-%m-%d"))
            n_, v_ = lc_day.get(key, (0, 0.0))
            lc_day[key] = (n_ + 1, v_ + p["value"])
    paid_true_linear = true_linear_paid_revenue(orders, user_sessions)
    total_spend = sum(paid_true_linear.values()) / D["blended_roas"]
    clicks_day = {}
    for s in sessions:
        if in_q(s["ts"]) and s["cid"]:
            key = (s["cid"], (s["ts"] + TZ_OFFSET).strftime("%Y-%m-%d"))
            clicks_day[key] = clicks_day.get(key, 0) + 1
    # A9 per-campaign multiplier; conversion-weighted mean held at exactly 1 + RATE["A9"].
    paid_ids = [c["campaign_id"] for c in ROSTER if c["platform"] != "Email"]
    conv_c = {cid: sum(n_ for (k, _), (n_, _) in lc_day.items() if k == cid) for cid in paid_ids}
    raw_m = {cid: math.exp(V["a9_log_sd"] * VC[cid]["a9_z"]) for cid in paid_ids}
    scale = (1 + RATE["A9"]) * sum(conv_c.values()) / sum(raw_m[c] * conv_c[c] for c in paid_ids)
    mult = {cid: raw_m[cid] * scale for cid in paid_ids}
    rs = random.Random(SEED11 + 7)
    days = [(Q_START + TZ_OFFSET + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(Q_DAYS)]
    spend_rows = []
    for c in ROSTER:
        cid = c["campaign_id"]
        is_paid = c["platform"] != "Email"
        camp_spend = total_spend * PLATFORM_SPLIT[c["platform"]] * c["platform_share"] if is_paid else 0.0
        daily_clicks = [clicks_day.get((cid, d), 0) for d in days]
        if cid == "A01":   # affiliate: commission on platform-reported sales, not per click
            weights = [lc_day.get((cid, d), (0, 0.0))[1] for d in days]
        else:
            weights = [k * rs.uniform(0.9, 1.1) for k in daily_clicks]
        wsum = sum(weights)
        cents = [round(camp_spend * 100 * w / wsum) if wsum else 0 for w in weights]
        if is_paid and wsum:
            cents[max(range(Q_DAYS), key=lambda i: weights[i])] += round(camp_spend * 100) - sum(cents)
        conv_cum_exact, conv_cum_round = 0.0, 0
        for i, d in enumerate(days):
            k = daily_clicks[i]
            n_, v_ = lc_day.get((cid, d), (0, 0.0))
            if k == 0 and cents[i] == 0 and n_ == 0:
                continue
            if is_paid:
                conv_cum_exact += n_ * mult[cid]
                pc = round(conv_cum_exact) - conv_cum_round   # carry rounding so totals stay exact
                conv_cum_round += pc
                pv = v_ * mult[cid]
                ctr = VC[cid]["ctr_pct"]
                imps = round(k / (ctr / 100) * rs.uniform(0.85, 1.15)) if ctr and k else ""
            else:
                pc, pv, imps = n_, v_, ""
            billing = {"Google": "cpc", "Meta": "cpm", "Email": "owned"}.get(c["platform"]) or \
                ("commission" if cid == "A01" else "cpm")
            spend_rows.append({
                "date": d, "campaign_id": cid, "campaign_name": c["campaign_name"], "platform": c["platform"],
                "billing": billing, "spend": f"{cents[i] / 100:.2f}", "impressions": imps, "clicks": k,
                "platform_conversions": pc, "platform_conversion_value": f"{pv:.2f}",
            })
    seed_log.extend(("A9", -1, cid, f"platform multiplier {mult[cid]:.4f}") for cid in paid_ids)

    # ---------------- 5. Write outputs ----------------
    (DATA / "export").mkdir(parents=True, exist_ok=True)
    (DATA / "truth").mkdir(parents=True, exist_ok=True)
    cols = ["event_date", "event_timestamp", "event_name", "user_pseudo_id", "ga_session_id", "ga_session_number",
            "platform", "source", "medium", "campaign", "gclid", "page_location", "page_referrer",
            "engagement_time_msec", "transaction_id", "value", "currency", "shipping", "tax", "items",
            "device_category", "operating_system", "browser", "geo_country", "geo_region"]
    write_gz(DATA / "export" / "events.csv.gz", cols, rows)
    trows = []
    for s in sorted(sessions, key=lambda s: s["sid"]):
        src, med, camp, _, _ = rec[s["sid"]]
        u = users[s["uid"]]
        trows.append({"sid": s["sid"], "uid": s["uid"], "ts": s["ts"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                      "sub": s["sub"], "campaign_id": s["cid"] or "", "link": s["link"],
                      "converts": int(s["converts"]), "bot": int(s["bot"]), "bot_profile": s["kind"],
                      "device": u["device"], "browser": u["browser"], "existing": int(u["prior"] > 0),
                      "client_id": client_of[s["sid"]], "in_quarter": int(in_q(s["ts"])),
                      "recorded_source": src, "recorded_medium": med, "recorded_campaign": camp})
    write_gz(DATA / "truth" / "sessions.csv.gz", list(trows[0].keys()), trows)
    ocols = ["txn", "sid", "uid", "ts", "value_cents", "dup", "noid", "gateway"]
    write_gz(DATA / "truth" / "orders.csv.gz", ocols,
             [{"txn": o["txn"], "sid": o["sid"], "uid": o["uid"], "ts": o["ts"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
               "value_cents": o["value_cents"], "dup": int(o["dup"]), "noid": int(o["noid"]),
               "gateway": int(o["gateway"])} for o in orders])
    write_gz(DATA / "truth" / "seed_log.csv.gz", ["class", "sid", "ref", "detail"],
             [dict(zip(["class", "sid", "ref", "detail"], r)) for r in seed_log])
    with open(DATA / "spend.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(spend_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(spend_rows)

    manifest = {"seed": SEED, "seed_v1_1": SEED11, "quarter": "2026-Q3", "orders": len(orders), "events": len(rows),
                "sessions_in_quarter": sum(1 for s in sessions if in_q(s["ts"])), "files": {}}
    for p in ["export/events.csv.gz", "truth/sessions.csv.gz", "truth/orders.csv.gz", "truth/seed_log.csv.gz",
              "spend.csv", "parameters.json"]:
        raw = (DATA / p).read_bytes()
        if p.endswith(".gz"):   # hash content, not deflate bytes: zlib builds may compress differently
            raw = gzip.decompress(raw)
        manifest["files"][p] = hashlib.sha256(raw).hexdigest()
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "files"}, indent=1))


# ---------------- helpers ----------------
EVENT_ORDER = {"session_start": 0, "first_visit": 1, "page_view": 2, "view_item": 3, "add_to_cart": 4,
               "begin_checkout": 5, "purchase": 6}


def _poisson(rng, lam):
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def utm_q(src, med, camp):
    return f"?utm_source={src}&utm_medium={med}&utm_campaign={camp}"


def gclid_of(rng):   # realistic shape: ~90 chars of base64url (F7)
    body = base64.urlsafe_b64encode(rng.getrandbits(504).to_bytes(63, "big")).decode().rstrip("=")
    return "Cj0KCQjw" + body[:80] + "_BwE"


def clean_recording(rng, s):
    sub, cid = s["sub"], s["cid"]
    camp = BY_ID[cid]["campaign_name"] if cid else None
    if sub in GOOGLE_SUBS:
        g = gclid_of(rng)
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


def external_referrer(rng, s, src):
    sub = s["sub"]
    if sub in GOOGLE_SUBS:
        return "https://www.google.com/"
    if sub == "organic_search":
        return SEARCH_REF.get(src, "https://www.google.com/")
    if sub in ("meta_prospecting", "meta_retargeting"):
        return rng.choice(["https://m.facebook.com/", "https://l.instagram.com/", "https://l.facebook.com/"])
    if sub == "tiktok":
        return "https://www.tiktok.com/"
    if sub in ("organic_social", "referral"):
        return f"https://{src}/" if "." in src else ""
    if sub == "affiliate":
        k = int(s["link"].split("-L")[-1]) - 1 if s["link"] else 0
        return f"https://{AFF_PUBLISHERS[k % len(AFF_PUBLISHERS)]}/"
    return ""   # direct and email (mail clients strip the referrer)


def case_variant(rng, camp):
    parts = camp.split("_")
    if rng.random() < 0.3:
        return camp.upper()
    return "_".join(p.upper() if p == "qw" else (p.capitalize() if rng.random() < 0.5 else p) for p in parts)


def spelling_variant(rng, camp):
    options = [camp.replace("_", "-"), camp.replace("chili", "chilli"), camp.replace("qw_", "qw "),
               camp.rstrip("s"), camp.replace("-", "")]
    options = [o for o in options if o != camp] or [camp + "_v2"]
    return rng.choice(options)


def write_gz(path, cols, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    with open(path, "wb") as f:
        with gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0, compresslevel=6) as gz:
            gz.write(buf.getvalue().encode("utf-8"))


def true_linear_paid_revenue(orders, user_sessions):
    """True-layer linear credit to paid campaigns (sets total spend via blended ROAS)."""
    out = {}
    for o in orders:
        path = [s for s in user_sessions[o["uid"]] if s["ts"] <= o["ts"] and s["sub"] != "direct"
                and (o["ts"] - s["ts"]).days < 90]
        for s in path:
            if s["cid"] and s["sub"] in PAID_SUBS:
                out[s["cid"]] = out.get(s["cid"], 0.0) + o["value_cents"] / 100 / len(path)
    return out


if __name__ == "__main__":
    main()
