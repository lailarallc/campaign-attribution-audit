<script>
	// Lailara brand frame (vendored lailara-frame.css v1.5.1). Header + main + dark footer.
	let { children } = $props();
</script>

<div class="lailara-page">
	<header class="lailara-header">
		<nav class="lailara-nav-inner">
			<a href="https://lailarallc.com" class="lailara-wordmark" target="_blank" rel="noopener">Lailara LLC</a>
			<span class="lailara-tool-name">Campaign Math</span>
		</nav>
	</header>

	<main class="lailara-main">
		{@render children()}
	</main>

	<footer class="lailara-footer">
		<div class="lailara-footer-inner">
			<p>Built by <a href="https://lailarallc.com" target="_blank" rel="noopener">Lailara LLC</a> — data hygiene and analytics consulting for specialty food brands scaling into national retail.</p>
			<p class="lailara-footer-note">
				Quellwood Provisions is an invented brand. Its quarter of data is synthetic, generated from a fixed
				seed with tracking defects planted at stated rates. Not a client. Figures are Q3 2026 web orders.
			</p>
		</div>
	</footer>
</div>
