SDKROOT:=/usr/local/Cellar/google-app-engine/1.8.3/share/google-app-engine

run:
	$(SDKROOT)/dev_appserver.py --admin_port 8001 --port 8081 --skip_sdk_update_check=yes .

run_clean:
	$(SDKROOT)/dev_appserver.py --admin_port 8001 --port 8081 --skip_sdk_update_check=yes --clear_datastore=yes .

deploy:
	$(SDKROOT)/appcfg.py --oauth2 update .
