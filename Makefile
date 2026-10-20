# Build alenabraham.me with my own generator (site/). Output: public/
UV_RUN := uv run --no-project --python 3.12 --with-requirements site/requirements.txt
PORT ?= 1313

.PHONY: build serve check test clean

build:
	$(UV_RUN) python site/build.py

serve: build
	python3 -m http.server $(PORT) -d public

check: build
	$(UV_RUN) python site/check_urls.py

# Unit tests for build.py's helpers, and config toggles (commenting out a line in site/site.yaml removes that piece).
test:
	$(UV_RUN) python -m unittest discover -s site/tests -v

clean:
	rm -rf public
