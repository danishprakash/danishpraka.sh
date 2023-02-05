.PHONY: build
build:
	rm -rf kizai
	git clone https://github.com/danishprakash/kizai
	cd kizai && go build -o kizai && cd ..
	./kizai/kizai build
