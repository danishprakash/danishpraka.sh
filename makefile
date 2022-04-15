ifeq ($(DRAFTS),1)
        JEKYLL_FLAGS=--drafts
endif

fetch:
	python3 scripts/reviews.py

serve:
	bundle exec jekyll serve ${JEKYLL_FLAGS}

build: fetch
	bundle exec jekyll build

setup:
	sudo apt update \
		&& apt install -y ruby-full build-essential zlib1g-dev
	gem install jekyll bundler
