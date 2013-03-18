SDKROOT:=/usr/local/Cellar/google-app-engine/1.7.5/share/google-app-engine

run:
	$(SDKROOT)/dev_appserver.py -p 8081 --skip_sdk_update_check --use_sqlite .

run_clean:
	$(SDKROOT)/dev_appserver.py -p 8081 --skip_sdk_update_check --use_sqlite --clear_datastore .

deploy:
	$(SDKROOT)/appcfg.py --oauth2 update .
