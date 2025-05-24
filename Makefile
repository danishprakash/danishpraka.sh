.PHONY: build

.PHONY: kizai
kizai: check-kizai
	cd kizai && go build -o kizai && cd ..

check-kizai:
	@if [ ! -d "kizai" ]; then \
		rm -rf kizai; \
		git clone https://github.com/danishprakash/kizai; \
	fi
.PHONY: build
build: kizai
	./kizai/kizai build


.PHONY: serve
serve: kizai
	./kizai/kizai serve
