release:
	git add pyproject.toml
	git commit -m "Release v$$(poetry version -s)" || true
	git push origin master
	@VERSION=$$(poetry version -s); git tag -a v$${VERSION} -m "meshroom v$${VERSION}"; git push origin v$${VERSION}; \

major:
	git checkout master
	git pull
	poetry version major
	$(MAKE) release

minor:
	git checkout master
	git pull
	poetry version minor
	$(MAKE) release

patch:
	git checkout master
	git pull
	poetry version patch
	$(MAKE) release
