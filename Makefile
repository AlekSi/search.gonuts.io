# TODO pep8 pyflakes etc

run:
	dev_appserver.py -p 8081 --skip_sdk_update_check --use_sqlite .

run_clean:
	dev_appserver.py -p 8081 --skip_sdk_update_check --use_sqlite --clear_datastore .

deploy:
	appcfg.py --oauth2 update .
