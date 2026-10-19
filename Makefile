# Build alenabraham.me with my own generator (site/). Output: public/
UV_RUN := uv run --no-project --python 3.12 --with-requirements site/requirements.txt
PORT ?= 1313

.PHONY: build serve check clean

build:
	$(UV_RUN) python site/build.py

serve: build
	python3 -m http.server $(PORT) -d public

check: build
	$(UV_RUN) python site/check_urls.py

clean:
	rm -rf public
