"""Shared, dependency-free logic: GA4 default channel grouping, campaign matching, the four
attribution rules, and Kendall tau-b. Used by the generator (platform-reported column) and
the engine (attribute.py). Definitions are pinned in docs/design-gate.md section 1.5.
"""

import re

# GA4 default channel group (support.google.com/analytics/answer/9756891, read 2026-10-22).
# Google evaluates rules in its published table order; channel rules are case-insensitive.
PAID_MEDIUM = re.compile(r"^(.*cp.*|ppc|retargeting|paid.*)$")
SHOP_CAMPAIGN = re.compile(r"^(.*(([^a-df-z]|^)shop|shopping).*)$")
EMAIL = {"email", "e-mail", "e_mail", "e mail"}
# Google publishes these as downloadable site lists; only the members this universe can
# produce are listed here.
SEARCH_SITES = {"google", "bing", "duckduckgo", "yahoo", "google.com", "bing.com"}
SOCIAL_SITES = {"facebook", "instagram", "tiktok", "pinterest", "facebook.com", "m.facebook.com",
                "l.facebook.com", "instagram.com", "l.instagram.com", "tiktok.com", "pinterest.com"}
SHOPPING_SITES = {"shopping.google.com"}
VIDEO_SITES = {"youtube", "youtube.com"}


def channel_group(source, medium, campaign):
    s = (source or "").lower()
    m = (medium or "").lower()
    c = (campaign or "").lower()
    paid = bool(PAID_MEDIUM.match(m))
    if s == "(direct)" and m in ("(not set)", "(none)"):
        return "Direct"
    if "cross-network" in c:
        return "Cross-network"
    if (s in SHOPPING_SITES or SHOP_CAMPAIGN.match(c)) and paid:
        return "Paid Shopping"
    if s in SEARCH_SITES and paid:
        return "Paid Search"
    if s in SOCIAL_SITES and paid:
        return "Paid Social"
    if s in VIDEO_SITES and paid:
        return "Paid Video"
    if m in ("display", "banner", "expandable", "interstitial", "cpm"):
        return "Display"
    if paid:
        return "Paid Other"
    if s in SHOPPING_SITES or SHOP_CAMPAIGN.match(c):
        return "Organic Shopping"
    if s in SOCIAL_SITES or m in ("social", "social-network", "social-media", "sm", "social network", "social media"):
        return "Organic Social"
    if s in VIDEO_SITES or re.match(r"^(.*video.*)$", m):
        return "Organic Video"
    if s in SEARCH_SITES or m == "organic":
        return "Organic Search"
    if m in ("referral", "app", "link"):
        return "Referral"
    if s in EMAIL or m in EMAIL:
        return "Email"
    if m == "affiliate":
        return "Affiliates"
    if m == "audio":
        return "Audio"
    if s == "sms" or m == "sms":
        return "SMS"
    if m.endswith("push") or "mobile" in m or "notification" in m or s == "firebase":
        return "Mobile Push Notifications"
    return "Unassigned"


UNATTRIBUTABLE = "Unattributable"   # Unassigned / (not set) / Unmatched touches (section 1.5)
DIRECT = "Direct"


def credit_key(channel, source, campaign, campaign_names):
    """What a recorded touch can be credited to. campaign_names maps lower-cased, trimmed
    spend-table names (and Google Ads campaign IDs) to campaign_id."""
    if channel == DIRECT:
        return DIRECT
    if channel == "Unassigned" or source == "(not set)":
        return UNATTRIBUTABLE
    if campaign and campaign not in ("(not set)", "(organic)", "(referral)", "(direct)"):
        cid = campaign_names.get(campaign.strip().lower())
        return cid if cid else UNATTRIBUTABLE   # Unmatched
    return "channel:" + channel


RULES = ("last_click", "first_click", "linear", "position_based")


def split_credit(path, rule):
    """path: list of credit keys, Direct already removed, in time order. Returns {key: share}."""
    n = len(path)
    out = {}

    def add(k, w):
        out[k] = out.get(k, 0.0) + w

    if n == 0:
        add(DIRECT, 1.0)   # direct-only path (section 1.5)
        return out
    if rule == "last_click":
        add(path[-1], 1.0)
    elif rule == "first_click":
        add(path[0], 1.0)
    elif rule == "linear":
        for k in path:
            add(k, 1.0 / n)
    elif rule == "position_based":
        if n == 1:
            add(path[0], 1.0)
        elif n == 2:
            add(path[0], 0.5)
            add(path[1], 0.5)
        else:
            add(path[0], 0.4)
            add(path[-1], 0.4)
            for k in path[1:-1]:
                add(k, 0.2 / (n - 2))
    else:
        raise ValueError(rule)
    return out


def kendall_tau_b(x, y):
    """Kendall tau-b for two equal-length score lists (ties handled)."""
    n = len(x)
    conc = disc = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = (x[i] > x[j]) - (x[i] < x[j])
            dy = (y[i] > y[j]) - (y[i] < y[j])
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tx += 1
            elif dy == 0:
                ty += 1
            elif dx == dy:
                conc += 1
            else:
                disc += 1
    denom = ((conc + disc + tx) * (conc + disc + ty)) ** 0.5
    return (conc - disc) / denom if denom else 1.0
