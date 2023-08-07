install: clib
		pyinstaller main.py -n freyafs --noconsole --onefile

run: clib
		python main.py  ~/mount ./encrypted-files

run-limited: clib
		python main.py  ~/mount ./encrypted-files --cache-max-mem 1402360 --eviction-technique LRU

bench: clib
	python bench.py ~/mount ./test-files

clean:
		rm -rf ./build
		rm -rf ./dist
		rm -rf ./**/__pycache__

clear-encfiles:
		rm -rf ./encrypted-files
		mkdir encrypted-files

clib:
	@ cd aesmix256k && python build_aesmix.py

setup-bench-files:
		mkdir -p test-files
		mkdir -p  ~/Downloads/test-files
		base64 /dev/urandom | head -c 1024       > ~/Downloads/test-files/001K
		base64 /dev/urandom | head -c 10240      > ~/Downloads/test-files/010K
		base64 /dev/urandom | head -c 102400     > ~/Downloads/test-files/100K
		base64 /dev/urandom | head -c 1048576    > ~/Downloads/test-files/001M
		base64 /dev/urandom | head -c 10485760   > ~/Downloads/test-files/010M
		base64 /dev/urandom | head -c 104857600  > ~/Downloads/test-files/100M
		base64 /dev/urandom | head -c 1073741824 > ~/Downloads/test-files/001G
		cp ~/Downloads/test-files/001K ~/mount/
		cp ~/Downloads/test-files/010K ~/mount/
		cp ~/Downloads/test-files/100K ~/mount/
		cp ~/Downloads/test-files/001M ~/mount/
		cp ~/Downloads/test-files/010M ~/mount/
		cp ~/Downloads/test-files/100M ~/mount/
		cp ~/Downloads/test-files/001G ~/mount/
