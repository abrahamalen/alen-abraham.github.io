# Build alenabraham.me with my own generator (site/). Output: public/
UV_RUN := uv run --no-project --python 3.12 --with-requirements site/requirements.txt
PORT ?= 1313

.PHONY: build serve check test lint scheduled diagrams diagram clean

# FUTURE=1 make build (or serve) includes posts dated in the future, for previewing them.
build:
	$(UV_RUN) python site/build.py

serve: build
	python3 -m http.server $(PORT) -d public

check: build
	$(UV_RUN) python site/check_urls.py

# Unit tests for build.py's helpers, and config toggles (commenting out a line in site/site.yaml removes that piece).
test:
	$(UV_RUN) python -m unittest discover -s site/tests -v

lint:
	uv run --no-project --python 3.12 --with-requirements site/requirements-dev.txt ruff check site

# Posts and dailies with a future `date:`; they go live on the first deploy after it.
scheduled:
	@$(UV_RUN) python site/build.py --scheduled

# Mermaid renders (light/dark SVG + PNG), committed under each bundle's diagrams/_mermaid/.
# Needs Node; `make build` doesn't, it only checks the renders exist.
diagrams:
	cd site && npm ci --no-audit --no-fund
	$(UV_RUN) python site/build.py --diagrams

# Starter SVG for a designed diagram: make diagram POST=<slug> NAME=<name>
diagram:
	@test -n "$(POST)" -a -n "$(NAME)" || (echo "usage: make diagram POST=<slug> NAME=<name>" && exit 1)
	@$(UV_RUN) python site/build.py --new-diagram "$(POST)" "$(NAME)"

clean:
	rm -rf public
