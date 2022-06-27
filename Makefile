######################################
### 02: Experiment tracking module ###
######################################

db:
	docker-compose up -d

mlflow: db
	mlflow ui \
		--backend-store-uri postgresql://admin:admin@localhost:35432/db \
		--default-artifact-root ./mlruns

preprocess:
	pipenv run python 02-experiment-tracking/preprocess_data.py \
		--raw_data_path 02-experiment-tracking/data/raw \
		--dest_path 02-experiment-tracking/data/pre-processed
train:
	pipenv run python 02-experiment-tracking/train.py
