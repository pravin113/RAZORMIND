# RazorMind AI ML Evaluation

## Dataset
- Records: 50000
- Fraud percentage: 0.91%
- Payment failure percentage: 12.04%
- Recovery rate on failed payments: 47.87%

The dataset is synthetic and generated from merchant, customer, transaction, behavioral, payment failure, and recovery variables. Suspicious signals increase fraud likelihood, but no feature directly reveals `is_fraud`.

## Feature Description
Features include transaction amount, payment method, timing, customer history, merchant averages, amount deviation, failed attempts, device/IP/country changes, velocity, previous chargebacks/fraud events, checkout duration, retries, subscription status, payment failure context, and recovery history.

## Methodology
Fraud and recovery models use stratified train/validation/test splits of 70%/15%/15%. Model selection is made on validation data, then reported on held-out test data. Imbalance is handled through model class weighting rather than naive oversampling.

## Fraud Model Comparison
### xgboost
- Precision: 0.0184
- Recall: 0.2206
- F1: 0.0340
- ROC-AUC: 0.5866
- PR-AUC: 0.0181
- False-positive rate: 0.1076
- False-negative rate: 0.7794
- False-positive cost: 40000.00
- False-negative cost: 26500.00
### lightgbm
- Precision: 0.0198
- Recall: 0.0588
- F1: 0.0296
- ROC-AUC: 0.5639
- PR-AUC: 0.0151
- False-positive rate: 0.0266
- False-negative rate: 0.9412
- False-positive cost: 9900.00
- False-negative cost: 32000.00
### catboost
- Precision: 0.0199
- Recall: 0.2794
- F1: 0.0371
- ROC-AUC: 0.6139
- PR-AUC: 0.0202
- False-positive rate: 0.1262
- False-negative rate: 0.7206
- False-positive cost: 46900.00
- False-negative cost: 24500.00

Best fraud model: `lightgbm` selected by validation total business cost and PR-AUC tie-break.
Best model held-out total cost: 41900.00

## Ensemble Comparison
- Ensemble PR-AUC: 0.0186
- Ensemble F1: 0.0462
- Ensemble total cost: 50000.00
- Ensemble improved total cost: False

## Anomaly Detection
Isolation Forest is used to identify unusual transaction behavior independently from supervised fraud classification.
- Contamination: 0.0136
- Flag rate: 0.0136
- Fraud rate among flagged transactions: 0.0529

## Recovery Model Results
Best recovery model: `catboost`.
- Precision: 0.5771
- Recall: 0.4676
- F1: 0.5166
- ROC-AUC: 0.5973
- PR-AUC: 0.5742
- Mean expected recovered value: 947.35
- Total expected recovered value: 855455.93

## Limitations
These results are measured on synthetic data, not production Razorpay data. The models demonstrate pipeline behavior and should be recalibrated with real merchant data before any production decisioning.

## Synthetic-Data Disclaimer
No real customer, merchant, Razorpay, or Supabase data was used.
