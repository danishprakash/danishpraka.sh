ifeq ($(DRAFTS),1)
        JEKYLL_FLAGS=--drafts
endif

fetch:
	python3 scripts/reviews.py

serve:
	bundle exec jekyll serve ${JEKYLL_FLAGS}

build: fetch
	bundle exec jekyll build
