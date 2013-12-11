VERSION=0.0.1
RELEASE=2013-12-11

.PHONY: naemon-core naemon-livestatus thruk

all: naemon-core naemon-livestatus thruk

thruk:
	cd thruk && make

naemon-core:
	cd naemon-core && make

naemon-livestatus:
	cd naemon-livestatus/src && ln -fs ../../naemon-core/naemon .
	cd naemon-livestatus && make

update: update-naemon-core update-naemon-livestatus update-thruk
	if [ `git status 2>/dev/null | grep -c "Changed but not updated"` -eq 1 ]; then \
		git commit -av -m 'automatic update';\
	else \
		echo "no updates"; \
		exit 1; \
	fi

update-naemon-core: submoduleinit
	cd naemon-core && git pull

update-naemon-livestatus: submoduleinit
	cd naemon-livestatus && git pull

update-thruk: submoduleinit
	cd thruk && make update

submoduleinit:
	git submodule init

clean:
	-cd naemon-core && make clean
	-cd naemon-livestatus && make clean
	-cd thruk && make clean
	rm -rf naemon-${VERSION} naemon-${VERSION}.tar.gz

install:
	cd naemon-core && make install install-sample-config install-rc
	cd naemon-livestatus && make install
	cd thruk && make install

dist:
	rm -rf naemon-${VERSION} naemon-${VERSION}.tar.gz
	mkdir naemon-${VERSION}
	git archive --format=tar HEAD | tar x -C "naemon-${VERSION}"
	cd naemon-core       && git archive --format=tar HEAD | tar x -C    "../naemon-${VERSION}/naemon-core/"
	cd naemon-livestatus && git archive --format=tar HEAD | tar x -C    "../naemon-${VERSION}/naemon-livestatus/"
	cd thruk/gui         && git archive --format=tar HEAD | tar x -C "../../naemon-${VERSION}/thruk/gui/"
	cd thruk/libs        && git archive --format=tar HEAD | tar x -C "../../naemon-${VERSION}/thruk/libs/"
	cd naemon-${VERSION}/naemon-core && autoreconf -i -v
	cd naemon-${VERSION}/naemon-livestatus && autoreconf -i -v
	cp -p thruk/gui/Makefile naemon-${VERSION}/thruk/gui
	cd naemon-${VERSION}/thruk/gui && ./script/thruk_patch_makefile.pl
	cd naemon-${VERSION}/thruk/gui && make staticfiles
	tar cf "naemon-${VERSION}.tar" \
		--exclude=thruk.spec \
		--exclude=naemon-core/naemon.spec \
		--exclude=.gitmodules \
		--exclude=.gitignore \
		"naemon-${VERSION}"
	gzip -9 "naemon-${VERSION}.tar"
	rm -rf "naemon-${VERSION}"

naemon-${VERSION}.tar.gz: dist

rpm: naemon-${VERSION}.tar.gz
	rpmbuild -tb naemon-${VERSION}.tar.gz

deb:
	debuild -i -us -uc -b