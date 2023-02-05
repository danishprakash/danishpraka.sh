.PHONY: build

.PHONY: kizai
kizai:
	rm -rf kizai
	git clone https://github.com/danishprakash/kizai
	cd kizai && go build -o kizai && cd ..


.PHONY: build
build: kizai
	./kizai/kizai build


.PHONY: serve
serve: kizai
	./kizai/kizai serve
