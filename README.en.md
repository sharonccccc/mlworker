# 🇺🇸 English Version

## Development

This repository demonstrates AI / Machine Learning workflows using the AutoGluon AutoML framework.

This project serves as an AI / Machine Learning capability development platform.  
By leveraging AutoML techniques and the AutoGluon framework, users can quickly build, train, and evaluate different types of AI models.

---

## Key Features

- Lower the barrier of building AI models through AutoML
- Provide examples for Tabular, Time Series, and Multimodal learning
- Model training and experimentation using Jupyter Notebook
- Docker environment for quick deployment and reproducibility

---

## AI Task Types

This repository demonstrates several AI / Machine Learning task types:

- Tabular Prediction
- Time Series Forecasting
- Multimodal Learning

Through these examples, users can understand how different data types are used in AI models.

Related documents:

[machine learning](./docs/machine learning)  
[autogluon.timeseries](./docs/autogluon.timeseries)  
[autogluon.tabular](./docs/autogluon.tabular)  
[autogluon.multimodal](./docs/autogluon.multimodal)

---

## Technology Stack

This project uses the following AI / Machine Learning technologies:

- AutoGluon AutoML Framework
- Python Machine Learning
- Jupyter Notebook
- Docker GPU runtime environment

### Technical Components

- AutoML Framework: AutoGluon, PyCaret
- Machine Learning Algorithms: XGBoost, LightGBM, CatBoost, Random Forest
- Data Processing: Pandas, NumPy
- Model Explainability: SHAP, Plotly
- MLOps: MLflow, Evidently AI
- Deployment: Docker, FastAPI

### Additional Capabilities

- AI model training and experimentation platform
- Worker nodes provide shared computing resources
- Integrated with computing resource scheduling systems
- Model deployment support
- Data and model drift monitoring

---

## Launch AI Environment

```bash
docker run -it --name autogluon -d --shm-size=16g --gpus all \
-p 17001:8888 \
-v $(pwd)/AG:/home/sagemaker-user/src \
--workdir /home/sagemaker-user/src \
shawoo/sagemaker bash -c "jupyter lab --allow-root --ip=0.0.0.0 --ServerApp.disable_check_xsrf=True --NotebookApp.token=YOURPASSWORD"
