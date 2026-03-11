# 🇯🇵 日本語版

## Development

このリポジトリは、AutoGluon AutoML フレームワークを使用した  
AI / Machine Learning ワークフローの実装例を示しています。

本プロジェクトは AI / Machine Learning の能力育成および実践プラットフォームです。  
AutoML 技術と AutoGluon フレームワークを活用し、ユーザーがさまざまな AI モデルを迅速に構築・学習・評価できるように設計されています。

---

## 主な特徴

- AutoML により AI モデル構築のハードルを低減
- Tabular、Time Series、Multimodal 学習のサンプルを提供
- Jupyter Notebook を用いたモデル学習と実験
- Docker 環境による簡単なデプロイと再現性

---

## AI タスクの種類

本プロジェクトでは、以下の AI / Machine Learning タスクの例を提供しています。

- Tabular Prediction
- Time Series Forecasting
- Multimodal Learning

これらの例を通して、異なるデータ形式が AI モデルにどのように活用されるかを理解できます。

関連ドキュメント：

[machine learning](./docs/machine learning)  
[autogluon.timeseries](./docs/autogluon.timeseries)  
[autogluon.tabular](./docs/autogluon.tabular)  
[autogluon.multimodal](./docs/autogluon.multimodal)

---
## Dataset

本プロジェクトでは、AutoML ワークフローとさまざまな AI タスクの応用を示すために、複数の公開 Machine Learning データセットを使用しています。

使用されるデータセットの例：
- AutoGluon 公式サンプルデータセット（GitHub）
- M4 時系列予測データセット（M4 Forecasting Competition）
- その他の一般的なオープンソース Machine Learning データセット

---

## 使用技術

本プロジェクトで使用している AI / Machine Learning 技術：

- AutoGluon AutoML Framework
- Python Machine Learning
- Jupyter Notebook
- Docker GPU 実行環境

### 技術構成

- AutoML フレームワーク：AutoGluon、PyCaret
- 機械学習アルゴリズム：XGBoost、LightGBM、CatBoost、Random Forest
- データ処理：Pandas、NumPy
- モデル解釈：SHAP、Plotly
- MLOps：MLflow、Evidently AI
- デプロイ：Docker、FastAPI

### 補足機能

- AI モデルの学習および検証プラットフォーム
- Worker ノードによる計算リソース共有
- 計算リソーススケジューリングシステムとの統合
- モデルデプロイ対応
- データおよびモデルドリフト監視

---

## AI 環境の起動

```bash
docker run -it --name autogluon -d --shm-size=16g --gpus all \
-p 17001:8888 \
-v $(pwd)/AG:/home/sagemaker-user/src \
--workdir /home/sagemaker-user/src \
shawoo/sagemaker bash -c "jupyter lab --allow-root --ip=0.0.0.0 --ServerApp.disable_check_xsrf=True --NotebookApp.token=YOURPASSWORD"
