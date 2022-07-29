######################################
### 02: Experiment tracking module ###
######################################

db:
	docker-compose up -d

mlflow: db
	mlflow ui \
		--backend-store-uri postgresql://admin:admin@localhost:35432/db \
		--default-artifact-root ./mlruns

02-preprocess:
	pipenv run python 02-experiment-tracking/preprocess_data.py \
		--raw_data_path 02-experiment-tracking/data/raw \
		--dest_path 02-experiment-tracking/data/pre-processed
02-train:
	pipenv run python 02-experiment-tracking/train.py

register:
	pipenv run python 02-experiment-tracking/register_model.py

clean:
	mlflow gc \
		--backend-store-uri postgresql://admin:admin@localhost:35432/db

	docker-compose down --remove-orphans --volumes --timeout=5 2>/dev/null


######################################
## 03: Workflow Orchestration module #
######################################

03-flow:
	pipenv run python 03-orchestration/homework.py

orion:
	prefect orion start

deploy:
	prefect deployment create 03-orchestration/homework.py


######################################
######## 04: deployment module #######
######################################

nb2script:
	jupyter nbconvert --to script 04-deployment/starter.ipynb

04-starter:
	pipenv run python 04-deployment/starter.py 2021 2

04-docker:
	docker build -t mlops-hw4:v1 -f 04-deployment/homework.dockerfile .
	docker run -it --rm mlops-hw4:v1 2021 2


######################################
###### 06: best practises module #####
######################################

06-docker:
	docker build -t mlops-hw6:v1 -f 06-best-practices/Dockerfile .
	docker run -it --rm mlops-hw6:v1 2021 2

s3:
	docker-compose up -d s3
	aws --endpoint-url=http://localhost:4566 s3 mb s3://nyc-duration
	aws --endpoint-url=http://localhost:4566 s3 ls
