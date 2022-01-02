fetch:
	python3 scripts/reviews.py

serve:
	bundle exec jekyll server

build: fetch
	bundle exec jekyll build
