# RazorMind Synthetic Transaction Dataset

Phase 3 generates synthetic transaction records for a Razorpay-like merchant payment platform.

The generator creates realistic but artificial correlations for:

- Payment behavior: amount, payment method, hour, day of week, retry count, failed attempts, transaction status.
- Customer and merchant history: customer transaction count, customer average amount, merchant average amount, previous successful payments, previous chargebacks, previous fraud events.
- Risk signals: amount deviation, device changes, IP changes, country changes, short-term velocity, checkout duration.
- Revenue recovery: payment failure, failure reason, subscription status, customer value, recovery attempts, recovered flag, recovery action, recovery amount.

Fraud is intentionally imbalanced. Suspicious behavior increases fraud likelihood, but no feature directly reveals `is_fraud`.

Generated files:

- `data/raw/synthetic_transactions.csv`
- `data/processed/transactions.csv`
- `data/processed/dataset_metadata.json`

This dataset is for hackathon development only and must not be treated as real Razorpay, Supabase, merchant, or customer data.

