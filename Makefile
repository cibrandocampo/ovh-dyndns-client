# Project-root Makefile.
#
# Holds cross-cutting orchestration targets that span multiple folders.
# Per-folder developer shortcuts (build, up, down, test, lint, format)
# stay in `dev/Makefile` — run `make -C dev <target>` for those.

.PHONY: help screenshots site-dev site-build

help:
	@echo "Available top-level targets:"
	@echo "  screenshots  Regenerate docs/dashboard-*.png from the seeded dev container"
	@echo "  site-dev     Run the Astro landing dev server (http://localhost:4321/ovh-dyndns-client/)"
	@echo "  site-build   Build the Astro landing into site/dist/"
	@echo ""
	@echo "Per-folder developer shortcuts live in dev/Makefile (build, up, test, lint, ...)."

screenshots:
	@echo "==> Bringing dev container up..."
	docker compose -f dev/docker-compose.yaml up -d
	@echo "==> Resetting and seeding fixtures..."
	docker compose -f dev/docker-compose.yaml exec --workdir /app -T ovh-dyndns-dev python /scripts/seed.py --reset
	@echo "==> Booting app (scheduler disabled to keep seed state stable)..."
	docker compose -f dev/docker-compose.yaml exec --workdir /app -d -e DISABLE_SCHEDULER=1 ovh-dyndns-dev python /app/main.py
	@scripts/wait-for-health.sh
	@echo "==> Capturing PNGs..."
	docker run --rm --network host \
		-v $(CURDIR)/e2e/screenshots.mjs:/e2e/screenshots.mjs \
		-v $(CURDIR)/docs:/screenshots \
		ovh-dyndns-e2e node /e2e/screenshots.mjs
	@echo "==> Stopping app (container stays up)..."
	-docker compose -f dev/docker-compose.yaml exec -T ovh-dyndns-dev sh -c "pkill -f 'python /app/main.py' 2>/dev/null"
	@echo "==> Done. Review docs/dashboard-*.png and commit manually."

site-dev:
	@echo "==> Starting Astro dev server on http://localhost:4321/ovh-dyndns-client/"
	cd site && npm run dev

site-build:
	@echo "==> Building Astro landing into site/dist/"
	cd site && npm run build
	@echo "==> Done. site/dist/ is ready for preview or deploy."
