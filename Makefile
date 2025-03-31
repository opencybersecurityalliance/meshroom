release:
	git add pyproject.toml
	git commit -m "Release v$$(poetry version -s)" || true
	git push origin main
	@VERSION=$$(poetry version -s); git tag -a v$${VERSION} -m "meshroom v$${VERSION}"; git push origin v$${VERSION}; \

major:
	git checkout main
	git pull
	poetry version major
	$(MAKE) release

minor:
	git checkout main
	git pull
	poetry version minor
	$(MAKE) release

patch:
	git checkout main
	git pull
	poetry version patch
	$(MAKE) release
