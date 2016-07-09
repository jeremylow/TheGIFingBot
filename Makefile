help:
	@echo "  info 	     show information on current sys config"
	@echo "  clean       remove unwanted stuff"
	@echo "  work        run server & gulp"
	@echo "  migrate     make migrations and migrate all apps"
	@echo "  shell       starts a django ipython shell"


local: export GBKEYS = test_keys
local:
	python gifing_bot.py


prod: export GBKEYS = prod_keys
prod:
	python gifing_bot.py

shell:
	cd ostrich; python manage.py shell -i ipython

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
