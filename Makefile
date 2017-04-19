help:
	@echo "  info 	     show information on current sys config"
	@echo "  clean       remove unwanted stuff"
	@echo "  local       run gifing bot using non-production settings"
	@echo "  prod        run gifing bot using production settings"


local: export GBKEYS = test_keys
local:
	python gifing_bot.py


prod: export GBKEYS = prod_keys
prod:
	python gifing_bot.py

info:
	python --version
	pyenv --version
	pip --version

clean:
	rm -fr build
	rm -fr dist
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -name '*~' ! -name '*.un~' -exec rm -f {} \;

test:
	pytest
