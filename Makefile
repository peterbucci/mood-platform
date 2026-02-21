.PHONY: verify verify-env check

verify:
	@python scripts/verify.py

verify-env:
	@python scripts/verify.py --skip-style --skip-api --skip-db

check:
	@pre-commit run --all-files
