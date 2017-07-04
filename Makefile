

clean: ## cleanup
	sudo rm -rf venv data

password: ## generates a hashPassword (salt='' password='')
	python generate-password.py $(salt) $(password)

build: ## builds the docker image
	docker build \
		--build-arg DEB_URL="` grep deb_url config.yml | awk '{ print $$NF }'`" \
		-f Dockerfile  -t azulinho/ci-platform$$BRANCH .
	docker build \
		--build-arg TEMPURL=$$TEMPURL \
		-f Dockerfile.config-vol  -t azulinho/ci-config-vol$$BRANCH .

push:
	docker push azulinho/ci-platform

pull:
	docker pull azulinho/ci-platform

config-volume:
	curl -X POST -F file=@config.yml 'http://tempurl-endpoint.service.tinc-core-vpn/api?tempurl=jenkins_config_yml_local&ttl=999'
	docker run -it --rm --net=host  \
		-v config-volume:/config \
		-e TEMPURL=$$TEMPURL \
		azulinho/ci-config-vol


deploy: ## deploys the docker image
	# kill any jenkins instances
	docker run -it --rm --net=host \
		--env JENKINS_HOME="/var/lib/jenkins" \
		--env JAVA_OPTS=" -Djava.awt.headless=true " \
		-v config-volume:/config \
		-v var-lib-jenkins:/var/lib/jenkins \
		-v var-log-jenkins:/var/log/jenkins \
		azulinho/ci-platform


tests: ## Run acceptance tests checking for exceptions in the log
	# checks for execeptions in the logs
	docker exec $$CI_PLATFORM_NAME ls /var/log/jenkins/jenkins.log
	if [ "`docker exec $$CI_PLATFORM_NAME grep 'SEVERE: Failed Loading plugin' /var/log/jenkins/jenkins.log | wc -l`" -ne "0" ]; then echo '****** FAILED *******'; exit 1; fi
	@echo "LOOKING GOOD"


PHONY: help
	help:
	@grep -E '^[a-z]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
