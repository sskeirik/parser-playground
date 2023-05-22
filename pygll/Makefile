.PHONY: test regen-tests
test:
	python -m pytest
regen-tests:
	python -c 'import tests.test_parser as test; test.regenerate_test_files(test.PARSER_TESTS)'
