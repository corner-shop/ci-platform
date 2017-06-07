
ifndef CI_PLATFORM_NAME
$(error CI_PLATFORM_NAME is not set)
endif

ifndef CI_CONFIG_VOL
$(error CI_CONFIG_VOL is not set)
endif

ifndef CI_DATA_VOL
$(error CI_DATA_VOL is not set)
endif


clean: ## cleanup
	sudo rm -rf venv data

password: ## generates a hashPassword (salt='' password='')
	python generate-password.py $(salt) $(password)

build: ## builds the docker image
	docker build \
		--build-arg DEB_URL="` grep deb_url config.yml | awk '{ print $$NF }'`" \
		-f Dockerfile  -t azulinho/ci-platform .

push:
	docker push azulinho/ci-platform

pull:
	docker pull azulinho/ci-platform


data-volume:
	docker create -v /var/lib/jenkins --name $$CI_DATA_VOL busybox /bin/true || true

config-volume:
	# re-create any jenkins config-volume if they happen to exist
	docker rm $$CI_CONFIG_VOL || echo
	docker create -v /config --name $$CI_CONFIG_VOL busybox /bin/true
	tar -c . | docker run -i --volumes-from $$CI_CONFIG_VOL azulinho/ci-platform bash -c "mkdir /build && tar -C /build -xvf - && cd /build && pip install -r requirements.txt && python -u render.py  && /bin/tar -C /build/target -cvzf /config/config.tar.gz . && rm -rf target"


deploy: ## deploys the docker image
	# kill any jenkins instances
	docker kill $$CI_PLATFORM_NAME  || echo
	docker rm $$CI_PLATFORM_NAME || echo
	docker run --rm --net=host --volumes-from $$CI_CONFIG_VOL --volumes-from $$CI_DATA_VOL --name $$CI_PLATFORM_NAME --env JENKINS_HOME="/var/lib/jenkins" --env JAVA_OPTS=" -Djava.awt.headless=true " azulinho/ci-platform


logs: ## Show jenkins logs
	docker exec $$CI_PLATFORM_NAME tail -f /var/log/jenkins/jenkins.log

tests: ## Run acceptance tests checking for exceptions in the log
	# checks for execeptions in the logs, and for the existence 'build' file
	# in a jenkins job workspace which is configured automatically at startup.
	docker exec $$CI_PLATFORM_NAME ls /var/log/jenkins/jenkins.log
	if [ "`docker exec $$CI_PLATFORM_NAME grep exception /var/log/jenkins/jenkins.log  | grep -v WEB-INF | grep -v '\/job\/' | wc -l`" -ne "0" ]; then echo '****** FAILED ********'; exit 1; fi
	if [ "`docker exec $$CI_PLATFORM_NAME grep 'SEVERE: Failed Loading plugin' /var/log/jenkins/jenkins.log | wc -l`" -ne "0" ]; then echo '****** FAILED *******'; exit 1; fi
	docker exec $$CI_PLATFORM_NAME ls /var/lib/jenkins/jobs/seed_job/workspace/target
	@echo "LOOKING GOOD"

deploy-marathon:
	# simplifly deployment as a marathon app.
	# set variables:
	# TEMPURL : full URL to the config.xml on the tempurl service
	# CI_PLATFORM_NAME : name to use for this particular docker instance
	# CI_CONFIG_VOL : name of the volume holding the config.tar.gz
	# CI_DATA_VOL :  name of the data volume for this CI instance
	make data-volume
	( wget $$TEMPURL -O config.yml && make config-volume && rm config.yml) || echo
	make deploy

PHONY: help
	help:
	@grep -E '^[a-z]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
