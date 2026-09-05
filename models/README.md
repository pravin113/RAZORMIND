# RazorMind AI - Model Weights & Metadata

This directory contains trained Scikit-learn, LightGBM, and CatBoost models along with metadata.

## Qwen3-8B GGUF Model

The large language model binary (`Qwen3-8B-Q4_K_M.gguf`, ~5.0 GB) is excluded from version control via `.gitignore` to comply with GitHub file size limits.

### Downloading the Qwen3 Model
To run local LLM inference via `llama-server`:
1. Download `Qwen3-8B-Q4_K_M.gguf` from Hugging Face:
   - [Qwen/Qwen2.5-7B-Instruct-GGUF](https://huggingface.co/Qwen) or your preferred Qwen GGUF repository.
2. Place the file directly in this folder:
   `D:\RazorMind\models\Qwen3-8B-Q4_K_M.gguf`
3. Launch with `start.bat`.

## Trained Machine Learning Artifacts
- `fraud_model.joblib` / `fraud_metadata.json`: LightGBM classifier for payment fraud detection.
- `anomaly_model.joblib` / `anomaly_metadata.json`: Isolation Forest for behavioral transaction anomaly detection.
- `recovery_model.joblib` / `recovery_metadata.json`: CatBoost classifier for revenue recovery probability.
