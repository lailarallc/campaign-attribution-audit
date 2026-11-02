<script>
	// Copy is verbatim from docs/verdict-branches.md (pre-registered 2026-10-22); every {slot}
	// comes from src/lib/site.json, built from data/results.json by scripts/build_site_data.py.
	import site from '$lib/site.json';

	const RULES = ['last_click', 'first_click', 'linear', 'position_based'];
	const RULE_COLOR = { last_click: '#1f2e7a', first_click: '#8e9ad0', linear: '#0c6552', position_based: '#6dcdb5' };
	const RULE_TEXT = { last_click: '#ffffff', first_click: '#0a0f29', linear: '#ffffff', position_based: '#063d32' };

	const usd = (v) => '$' + Math.round(v).toLocaleString('en-US');
	const usdK = (v) => (v >= 1000 ? '$' + (v / 1000).toFixed(1) + 'K' : usd(v));
	const pct = (v, d = 0) => (v * 100).toFixed(d) + '%';
	const x2 = (v) => v.toFixed(2) + '×';

	const paid = site.campaigns;
	const X = site.X;
	const lastTop = site.tops.last_click[0];
	const dissent = RULES.filter((r) => r !== 'last_click' && site.tops[r][0] !== lastTop);
	const agree = RULES.filter((r) => r !== 'last_click' && site.tops[r][0] === lastTop);

	// ---- bump chart geometry (rank by rule) ----
	const B = { w: 860, rowH: 30, top: 44, left: 230, right: 230 };
	const bumpH = B.top + paid.length * B.rowH + 10;
	const colX = (i) => B.left + (i * (B.w - B.left - B.right)) / (RULES.length - 1);
	const rowY = (rank) => B.top + (rank - 0.5) * B.rowH;
	const isMover = (c) => c.rank_hi - c.rank_lo >= 2;

	// ---- ROAS range chart geometry ----
	const maxRoas = Math.ceil(Math.max(...paid.map((c) => c.roas_hi)));
	const Rg = { w: 860, rowH: 34, top: 36, left: 250, right: 30 };
	const roasH = Rg.top + paid.length * Rg.rowH + 30;
	const rx = (v) => Rg.left + (v / maxRoas) * (Rg.w - Rg.left - Rg.right);
	// A zero low end ranks widest, as in attribute.py's ratio().
	const spread = (c) => (c.roas_lo ? c.roas_hi / c.roas_lo : Infinity);
	const byRoas = [...paid].sort((a, b) => spread(b) - spread(a));
	const ticks = Array.from({ length: maxRoas + 1 }, (_, i) => i);

	const totalUntraced = paid.reduce((a, c) => a + c.untraced, 0);

	function fireCta() {
		// Query-free event, same rule as the pageview in app.html.
		const gc = window.goatcounter;
		if (gc && typeof gc.count === 'function') {
			gc.count({ path: 'cta_click', title: 'CTA click', event: true });
		}
	}
</script>

<svelte:head>
	<title>Campaign Math — Lailara LLC</title>
</svelte:head>

<div class="lailara-container">
	<!-- ============ VERDICT ============ -->
	<section class="verdict ll-column" aria-labelledby="verdict-h">
		<p class="eyebrow">Campaign Math · Quellwood Provisions · {site.quarter_label}</p>
		<h1 id="verdict-h" class="lead">
			<span class="ll-headline-number">{usd(site.lead.U)}</span>
			<span class="lead-rest">of this quarter's {usd(site.lead.S)} in paid spend bought clicks that Quellwood's analytics can't tie back to the campaign that paid for them.</span>
		</h1>

		{#if site.branch !== 'BANK'}
			<p class="second">And which campaign worked best depends on a rule nobody chose.</p>
		{/if}

		{#if site.branch === 'B1'}
			<p class="body">
				Last-click names <code>{lastTop}</code>.{#each dissent as r} {site.rule_labels[r]} names <code>{site.tops[r][0]}</code>.{/each}
				Each answer is arithmetic on the same quarter of data, and each can be checked by hand. None of them is wrong.
				The report you get depends on which one somebody picked.
				{#if agree.length}{agree.map((r) => site.rule_labels[r]).join(' and ')} {agree.length > 1 ? 'agree' : 'agrees'} with last-click.{/if}
			</p>
		{:else if site.branch === 'B2'}
			<p class="body">
				Every rule names <code>{X}</code> the top campaign. That result is real. Below it, the order is a choice:
				{site.n} of {site.m} paid campaigns move two or more places depending on the rule, and
				<code>{site.Z.name}</code>'s return on spend runs from {x2(site.Z.lo)} to {x2(site.Z.hi)}.
			</p>
			<p class="body">
				Why the top holds: {pct(site.p1)} of revenue comes from customers with one recorded visit, where every rule gives
				the same answer by arithmetic, and among paid campaigns, <code>{X}</code> takes the largest share of those one-visit
				sales ({pct(site.share)}).
			</p>
		{:else}
			<p class="body">
				On this data the four rules mostly agree. Here is why: {pct(site.p1)} of revenue comes from customers with one
				recorded visit, where every rule must give the same answer. Another {pct(site.p2)} comes from two-visit journeys,
				where position-based and linear are identical by construction. Only {pct(site.p3)} of revenue comes from longer
				journeys, the only place the rules can disagree, and tracking breaks shorten some of those: {pct(site.u)} of
				multi-visit journeys were split by a seeded cookie or session break. The rule barely matters this quarter.
				Tracking decides the numbers instead.
			</p>
		{/if}

		<div class="always">
			<p>
				<strong>Every-rule winners:</strong>
				{#if site.every_rule.length}
					{#each site.every_rule as w, i}<code>{w}</code>{i < site.every_rule.length - 2 ? ', ' : i === site.every_rule.length - 2 ? ' and ' : ''}{/each}
					rank in the top {site.k} under all four rules. Fund them without argument.
				{:else}
					No campaign ranks in the top {site.k} under all four rules.
				{/if}
			</p>
			<p>
				<strong>Unattributable:</strong> {pct(site.s, 1)} of conversions, {usd(site.d)} in revenue, reach no campaign and
				no traceable source: Direct, Unassigned, (not set) or an unmatched campaign name. {pct(site.t)} of those got there through a tracking defect, seeded at the published or stated rate
				listed below.
			</p>
			<p>
				<strong>GA4:</strong> Since November 2023, GA4 offers no first-click, linear or position-based model. Its default
				is data-driven attribution, which cannot be reproduced outside Google. These four rules can be, and they bracket it.
				<a href="https://support.google.com/analytics/answer/10596866" target="_blank" rel="noopener">Google's note</a>
			</p>
			<p>
				<strong>Measurable floor:</strong> For a brand that sells mostly through retailers, this is the slice of marketing
				where the math can be checked. Most ad money also moves shelf sales that web analytics never sees.
			</p>
		</div>

		<nav class="subnav" aria-label="Sections">
			<a href="#campaigns">The campaigns</a>
			<a href="#hygiene">The hygiene audit</a>
			<a href="#method">Method and data</a>
		</nav>
	</section>

	<!-- Rank by rule (bump chart) -->
	<section class="chart-section" aria-labelledby="bump-h">
		<h2 id="bump-h" class="ll-section-title">Rank of each paid campaign under each rule</h2>
		<p class="sub">Ranked by attributed revenue. Highlighted lines move two or more places between rules.</p>
		<div class="scroll">
			<svg viewBox="0 0 {B.w} {bumpH}" role="img" aria-label="Rank of {site.m} paid campaigns under four attribution rules.{site.branch === 'B1' ? '' : ` ${X} ranks first under all four;`} {site.n} campaigns move two or more places.">
				{#each RULES as r, i}
					<text x={colX(i)} y="20" class="axis" text-anchor="middle">{site.rule_labels[r]}</text>
				{/each}
				{#each paid as c}
					{@const pts = RULES.map((r, i) => [colX(i), rowY(c.ranks[r])])}
					<polyline points={pts.map((p) => p.join(',')).join(' ')} fill="none"
						stroke={isMover(c) ? '#1f2e7a' : '#b3b3b3'} stroke-width={isMover(c) ? 2.5 : 1.5} />
					{#each pts as p, i}
						<circle cx={p[0]} cy={p[1]} r="11" fill={isMover(c) ? '#1f2e7a' : '#f2f2f2'} stroke={isMover(c) ? '#1f2e7a' : '#b3b3b3'} />
						<text x={p[0]} y={p[1] + 4} text-anchor="middle" class="pt" fill={isMover(c) ? '#ffffff' : '#333333'}>{c.ranks[RULES[i]]}</text>
					{/each}
					<text x={B.left - 18} y={rowY(c.ranks.last_click) + 4} text-anchor="end" class="lbl" class:mover={isMover(c)}>{c.name}</text>
					<text x={B.w - B.right + 18} y={rowY(c.ranks.position_based) + 4} class="lbl" class:mover={isMover(c)}>{c.name}</text>
				{/each}
			</svg>
		</div>
		<p class="footnote">
			Source: synthetic GA4 export, {site.quarter_label}; {site.conversions.toLocaleString('en-US')} purchases after
			deduplication on transaction ID. Paths use last-non-direct-click conventions, 90-day lookback inside the export window.
		</p>
	</section>

	<!-- ============ CAMPAIGNS ============ -->
	<section id="campaigns" class="chart-section" aria-labelledby="camp-h">
		<h2 id="camp-h" class="ll-section-title">The campaigns: return on spend is a range, not a number</h2>
		<p class="sub ll-measure">
			Each row is one paid campaign's return on ad spend under the four rules. The dot colors mark the rule; the labels
			mark the low and high ends.
		</p>
		<div class="legend">
			{#each RULES as r}<span><i style="background:{RULE_COLOR[r]}"></i>{site.rule_labels[r]}</span>{/each}
		</div>
		<div class="scroll">
			<svg viewBox="0 0 {Rg.w} {roasH}" role="img" aria-label="Return on ad spend range across four rules for each paid campaign.">
				{#each ticks as t}
					<line x1={rx(t)} x2={rx(t)} y1={Rg.top - 10} y2={roasH - 26} class="grid" />
					<text x={rx(t)} y={roasH - 8} text-anchor="middle" class="axis">{t}×</text>
				{/each}
				{#each byRoas as c, i}
					{@const y = Rg.top + i * Rg.rowH + Rg.rowH / 2}
					<text x={Rg.left - 14} y={y + 4} text-anchor="end" class="lbl">{c.name}</text>
					<line x1={rx(c.roas_lo)} x2={rx(c.roas_hi)} y1={y} y2={y} stroke="#b3b3b3" stroke-width="4" />
					{#each RULES as r}
						<circle cx={rx(c.roas[r])} cy={y} r="6" fill={RULE_COLOR[r]} stroke="#f5f3ee" stroke-width="1" />
					{/each}
					<text x={rx(c.roas_lo) - 10} y={y + 4} text-anchor="end" class="val">{x2(c.roas_lo)}</text>
					<text x={rx(c.roas_hi) + 10} y={y + 4} class="val">{x2(c.roas_hi)}</text>
				{/each}
			</svg>
		</div>
		<p class="footnote">Return on ad spend = revenue attributed under the rule ÷ the campaign's spend in the spend table. Sorted by the width of the range.</p>

		<div class="scroll table-wrap">
			<table>
				<thead>
					<tr>
						<th>Campaign</th><th>Platform</th><th class="num">Spend</th>
						{#each RULES as r}<th class="num">{site.rule_labels[r]}</th>{/each}
						<th class="num">Rank range</th><th>Reading</th>
					</tr>
				</thead>
				<tbody>
					{#each paid as c}
						<tr>
							<td><code>{c.name}</code></td><td>{c.platform}</td><td class="num">{usd(c.spend)}</td>
							{#each RULES as r}<td class="num">{usd(c.revenue[r])}</td>{/each}
							<td class="num">{c.rank_lo === c.rank_hi ? c.rank_lo : `${c.rank_lo}–${c.rank_hi}`}</td>
							<td>{c.every_rule_top3 ? 'Top 3 under every rule' : c.rule_dependent ? 'Depends on the rule' : 'Stable'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="footnote">
			Attributed revenue by rule. "Depends on the rule": rank moves two or more places, or return on spend varies by 1.5× or
			more. Email campaigns carry no media spend and are not ranked:
			{#each site.email as e, i}<code>{e.name}</code> {usdK(e.revenue.last_click)} (last-click){i < site.email.length - 1 ? '; ' : '.'}{/each}
			Revenue credited to no campaign, last-click:
			{#each site.buckets as b, i}{b.label} {usdK(b.revenue.last_click)}{i < site.buckets.length - 1 ? '; ' : '.'}{/each}
			These last-click buckets and the unattributable line at the top measure different things. The top line
			({usd(site.d)}) counts purchases that no rule can credit to any campaign: {usd(site.d_direct_only)} with only
			Direct visits, and {usd(site.d_unattr_touch)} whose every tracked visit is Unassigned, (not set) or unmatched.
			The last-click "Unassigned, (not set), unmatched" bucket ({usd(site.lc_unattr)}) also holds
			{usd(site.lc_unattr - site.d_unattr_touch)} of purchases whose last visit was untraceable but an earlier visit
			had a traceable source (a campaign, or an organic or referral channel), which the other three rules credit.
		</p>
	</section>

	<!-- ============ HYGIENE ============ -->
	<section id="hygiene" class="chart-section" aria-labelledby="hyg-h">
		<h2 id="hyg-h" class="ll-section-title">The hygiene audit: can the data answer the question?</h2>
		<p class="sub ll-measure">
			Nine classes of tracking defect, each planted in this quarter at a published or stated rate. The four that touch the
			most revenue are below. "Documented case" says whether a published account exists of this defect changing a budget
			decision.
		</p>
		<div class="cards">
			{#each site.hygiene_top as h}
				<article class="card">
					<p class="card-eyebrow">Class {h.taxonomy}</p>
					<h3>{h.label}</h3>
					<p class="ll-benchmark-value">{usd(h.revenue_affected)}</p>
					<p class="card-sub">{h.class === 'A9' ? 'more revenue in platform reports than in GA4' : h.class === 'A4a' ? 'of revenue double-counted in the raw export' : 'of revenue on journeys it touched'}</p>
					<dl>
						<dt>Seeded at</dt><dd>{h.seeded_at}</dd>
						<dt>Results in</dt><dd>{h.instances.toLocaleString('en-US')} instance{h.instances === 1 ? '' : 's'}{#if h.instances_path_neutral}; {h.instances_path_neutral.toLocaleString('en-US')} of them fall before the quarter and change no recorded path{/if}</dd>
						<dt>Documented case</dt><dd>{h.documented_case}</dd>
					</dl>
				</article>
			{/each}
		</div>

		<details class="rest">
			<summary>Other defects found ({site.hygiene_rest.length})</summary>
			<div class="scroll table-wrap">
				<table>
					<thead><tr><th>Class</th><th>Defect</th><th>Seeded at</th><th class="num">Instances</th><th class="num">Revenue touched</th><th class="num">Spend on it</th><th>Documented case</th></tr></thead>
					<tbody>
						{#each site.hygiene_rest as h}
							<tr>
								<td>{h.taxonomy}</td><td>{h.label}</td><td>{h.seeded_at}</td>
								<td class="num">{h.instances.toLocaleString('en-US')}</td>
								<td class="num">{usd(h.revenue_affected)}</td>
								<td class="num">{h.spend_affected ? usd(h.spend_affected) : '—'}</td>
								<td>{h.documented_case}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			<p class="footnote">
				Bot traffic touches no revenue: bots don't buy. Its cost is the spend on non-human paid clicks. It is the only class
				with a published decision case: Uber cut about two-thirds of a ~$150M rider-ad budget and installs did not move
				(<a href="https://www.dailymaverick.co.za/article/2021-01-18-the-digital-advertising-rip-off/" target="_blank" rel="noopener">Daily Maverick, 2021</a>).
			</p>
		</details>

		<h3 class="table-title">Where the untraced spend sits</h3>
		<div class="scroll table-wrap">
			<table>
				<thead><tr><th>Campaign</th><th class="num">Platform clicks</th><th class="num">GA4 sessions matched</th><th class="num">Gap</th><th class="num">Untraced spend</th></tr></thead>
				<tbody>
					{#each [...paid].sort((a, b) => b.untraced - a.untraced) as c}
						<tr>
							<td><code>{c.name}</code></td><td class="num">{c.clicks.toLocaleString('en-US')}</td>
							<td class="num">{c.matched.toLocaleString('en-US')}</td>
							<td class="num">{Math.max(0, c.clicks - c.matched).toLocaleString('en-US')}</td>
							<td class="num">{usd(c.untraced)}</td>
						</tr>
					{/each}
					<tr class="total"><td>Total</td><td></td><td></td><td></td><td class="num">{usd(totalUntraced)}</td></tr>
				</tbody>
			</table>
		</div>
		<p class="footnote">
			Untraced spend = spend × (platform clicks − GA4 sessions carrying the campaign's name) ÷ platform clicks. Bot clicks
			are counted on both sides, so they don't shrink the gap. Untraced spend here counts only the seeded tracking
			defects: this synthetic quarter has no other click loss (consent refusals, ad blockers, visitors who leave before
			the tag fires), so a real account's gap would be larger.
			{#each site.hygiene_footnote as h}Class {h.taxonomy}, {h.label.toLowerCase()} ({h.seeded_at}): case differences are matched back to their campaign; spelling variants are not, and land in the unattributable count. No published decision case.{/each}
		</p>
	</section>

	<!-- ============ METHOD ============ -->
	<section id="method" class="method ll-column" aria-labelledby="method-h">
		<h2 id="method-h" class="ll-section-title">Method and data</h2>
		<p>
			<strong>Synthetic data:</strong> Quellwood Provisions is an invented brand. Its quarter of data is generated from a
			fixed seed, with tracking defects planted at the rates listed above. The method is real.
		</p>
		<p>
			<strong>The four rules.</strong> Each purchase's path is the buyer's recorded sessions in the 90 days before it,
			Direct visits removed (GA4's last-non-direct-click convention, applied to all four rules alike). Last-click gives
			the last touch 100%. First-click gives the first touch 100%. Linear splits evenly. Position-based gives 40% to the
			first and last touches and splits 20% across the middle; with two touches it is 50/50. A path with only Direct visits
			goes to Direct. Purchases are deduplicated on transaction ID, as GA4 does.
		</p>
		<p>
			<strong>Rates.</strong> Each defect rate is either published (cited) or a stated assumption bounded by published
			figures. None was chosen to make the result dramatic, and none was adjusted after the result was seen. The verdict
			copy and the rule for choosing it were committed before the data was generated. After generation, review found
			copy clauses that were false against the data and one measure defined differently from its wording; each was
			corrected, and each correction is dated and logged in <code>docs/verdict-branches.md</code>.
		</p>
		<p>
			<strong>Check it by hand.</strong>
			GA4 event export, one gzip CSV per month: <a href="/data/events_2026-07.csv.gz" download>July</a>,
			<a href="/data/events_2026-08.csv.gz" download>August</a>, <a href="/data/events_2026-09.csv.gz" download>September</a>
			({site.events.toLocaleString('en-US')} events; joined, their rows hash to SHA-256
			<code class="hash">{site.manifest_sha_events.slice(0, 16)}…</code>), and the daily
			<a href="/data/spend.csv" download>spend table</a>. Every attribution number on this page comes from those files. The hygiene audit counts the
			defects the generator planted; it reads the <a href="/data/truth_seed_log.csv.gz" download>seed log</a>,
			<a href="/data/truth_sessions.csv.gz" download>true sessions</a> and
			<a href="/data/truth_orders.csv.gz" download>true orders</a>, published here too.
		</p>
		<p class="cta-row">
			<a class="cta" href="https://lailarallc.com/campaign-analytics" onclick={fireCta}>Run this on your own GA4 export and spend sheet</a>
		</p>
	</section>
</div>

<style>
	.verdict { padding-top: 8px; }
	.eyebrow {
		font-family: var(--ll-sans); font-size: 13px; letter-spacing: 0.06em; text-transform: uppercase;
		color: var(--ll-red-42); margin: 0 0 12px; border-bottom: 1px solid var(--ll-red-42); padding-bottom: 8px;
	}
	.lead { margin: 0 0 16px; font-weight: 400; }
	.lead .ll-headline-number { display: block; color: var(--ll-london-5); }
	.lead-rest {
		display: block; font-family: var(--ll-serif); font-size: 26px; line-height: 1.3; font-weight: 700;
		color: var(--ll-london-5); margin-top: 8px;
	}
	.second { font-family: var(--ll-serif); font-size: 22px; line-height: 1.3; font-weight: 700; color: var(--ll-london-20); margin: 0 0 20px; }
	.body { font-size: 17px; line-height: 1.6; color: var(--ll-london-20); margin: 0 0 14px; }
	.always { border-top: 1px solid var(--ll-london-85); margin-top: 24px; padding-top: 16px; }
	.always p { font-size: 15px; line-height: 1.6; color: var(--ll-london-20); margin: 0 0 10px; padding-left: 12px; border-left: 3px solid var(--ll-london-85); }
	code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.88em; color: var(--ll-london-5); overflow-wrap: anywhere; }
	.subnav { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 24px; font-size: 15px; }
	.subnav a, .footnote a, .always a, .method a:not(.cta) { color: var(--ll-london-20); }
	.subnav a:hover { color: var(--ll-chicago-20); }

	.chart-section { border-top: 1px solid var(--ll-london-85); margin-top: var(--ll-section-gap); padding-top: 32px; }
	.sub { font-size: 14px; color: var(--ll-london-35); margin: 4px 0 16px; }
	.scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
	.scroll svg { min-width: 760px; width: 100%; height: auto; display: block; }
	svg .axis { font-family: var(--ll-sans); font-size: 12px; fill: var(--ll-london-35); }
	svg .lbl { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; fill: var(--ll-london-35); }
	svg .lbl.mover { fill: var(--ll-london-5); font-weight: 600; }
	svg .pt { font-family: var(--ll-sans); font-size: 12px; font-weight: 600; }
	svg .val { font-family: var(--ll-sans); font-size: 12px; fill: var(--ll-london-20); }
	svg .grid { stroke: var(--ll-london-85); stroke-width: 1; }
	.footnote { font-size: 12px; font-style: italic; color: var(--ll-london-35); line-height: 1.5; max-width: var(--ll-body-max-width-wide); margin: 10px 0 0; }
	.legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; color: var(--ll-london-35); margin-bottom: 8px; }
	.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; }

	.table-wrap { margin-top: 24px; }
	table { border-collapse: collapse; width: 100%; font-size: 14px; min-width: 640px; }
	th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--ll-london-85); white-space: nowrap; }
	th { font-weight: 600; color: var(--ll-london-20); border-bottom: 1px solid var(--ll-london-40); }
	td { color: var(--ll-london-20); }
	.num { text-align: right; font-variant-numeric: tabular-nums; }
	tr.total td { font-weight: 600; border-top: 1px solid var(--ll-london-40); }
	.table-title { font-family: var(--ll-serif); font-size: 18px; font-weight: 700; margin: 36px 0 0; color: var(--ll-london-5); }

	.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
	.card { border: 1px solid var(--ll-london-85); border-radius: var(--ll-radius); padding: 16px; background: var(--ll-canvas); }
	.card-eyebrow { font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ll-red-42); margin: 0 0 4px; }
	.card h3 { font-family: var(--ll-serif); font-size: 18px; font-weight: 700; margin: 0 0 8px; color: var(--ll-london-5); }
	.card .ll-benchmark-value { margin: 0; }
	.card-sub { font-size: 14px; color: var(--ll-london-35); margin: 2px 0 12px; }
	.card dl { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; font-size: 13px; margin: 0; }
	.card dt { color: var(--ll-london-35); }
	.card dd { margin: 0; color: var(--ll-london-20); }
	.rest { margin-top: 20px; }
	.rest summary { cursor: pointer; font-weight: 600; color: var(--ll-london-20); padding: 8px 0; min-height: var(--ll-touch-target); display: flex; align-items: center; }
	.rest summary:focus-visible, .cta:focus-visible, a:focus-visible { outline: 2px solid var(--ll-london-5); outline-offset: 2px; }

	.method { border-top: 1px solid var(--ll-london-85); margin-top: var(--ll-section-gap); padding-top: 32px; }
	.method p { font-size: 16px; line-height: 1.6; color: var(--ll-london-20); }
	.hash { font-size: 0.8em; }
	.cta-row { margin-top: 24px; }
	.cta {
		display: inline-flex; align-items: center; min-height: var(--ll-touch-target); padding: 0 18px;
		background: var(--ll-chicago-20); color: #ffffff; border-radius: var(--ll-radius); font-weight: 600;
		font-size: 15px; text-decoration: none;
	}
	.cta:hover { background: var(--ll-chicago-10); }

	@media (max-width: 640px) {
		.lead-rest { font-size: 20px; }
		.second { font-size: 18px; }
		.body { font-size: 15px; }
	}
</style>
