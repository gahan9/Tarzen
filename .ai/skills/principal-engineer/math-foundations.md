# Mathematical Foundations Reference

Applied mathematics reference for the `principal-engineer` skill. Read this file
when proofs, derivations, numerical methods, or optimization theory are needed.

---

## 1. Linear Algebra for ML

| Operation | Notation | ML Use Case | Complexity |
|-----------|----------|-------------|------------|
| Matrix multiply | C = AB | Forward pass, attention | O(n*m*k) |
| SVD | A = UΣVᵀ | Dimensionality reduction, LoRA | O(min(mn², m²n)) |
| Eigendecomposition | Av = λv | PCA, spectral clustering, Hessian analysis | O(n³) |
| QR factorization | A = QR | Least squares, orthogonalization | O(mn²) |
| Cholesky | A = LLᵀ | Gaussian processes, covariance inversion | O(n³/3) |

### Einstein summation (universal tool for tensor contractions)

```python
import numpy as np

# Batch matmul: (B, M, K) x (B, K, N) -> (B, M, N)
C = np.einsum("bmk,bkn->bmn", A, B)

# Attention scores: (B, H, S, D) x (B, H, S, D) -> (B, H, S, S)
scores = np.einsum("bhsd,bhtd->bhst", Q, K) / np.sqrt(d_k)
```

### Low-rank adaptation (LoRA)

```
W_new = W_frozen + BA
  W_frozen ∈ R^{d×k}   (frozen)
  B ∈ R^{d×r}, A ∈ R^{r×k}   (trainable, r << min(d,k))
```

Parameter savings: from d*k to r*(d+k). For d=k=4096, r=16: ~99.2% reduction.

---

## 2. Calculus & Optimization

### Adam / AdamW (default for transformers)

```
m_t = β1·m_{t-1} + (1-β1)·g_t
v_t = β2·v_{t-1} + (1-β2)·g_t²
m̂_t = m_t / (1-β1^t);  v̂_t = v_t / (1-β2^t)
Adam:   θ_t = θ_{t-1} - lr·m̂_t / (√v̂_t + ε)
AdamW:  θ_t = θ_{t-1} - lr·(m̂_t / (√v̂_t + ε) + λ·θ_{t-1})
```

AdamW decouples weight decay from the adaptive learning rate.

### Practical defaults (transformer fine-tuning)

```python
lr = 2e-5
warmup_ratio = 0.06
weight_decay = 0.01
beta1, beta2, eps = 0.9, 0.999, 1e-8
max_grad_norm = 1.0
```

### Numerical stability

```python
def stable_softmax(logits):
    max_logit = logits.max(dim=-1, keepdim=True).values
    exp_logits = (logits - max_logit).exp()
    return exp_logits / exp_logits.sum(dim=-1, keepdim=True)
```

---

## 3. Probability, Statistics & Information Theory

| Quantity | Formula | ML Application |
|----------|---------|----------------|
| Entropy | H(X) = -Σ p(x) log p(x) | Prediction uncertainty |
| Cross-entropy | H(p,q) = -Σ p(x) log q(x) | Classification loss |
| KL divergence | D_KL(p‖q) = Σ p(x) log(p(x)/q(x)) | VAE regularization, distillation |
| Mutual information | I(X;Y) = H(X) - H(X\|Y) | Feature selection |

### Scaled dot-product attention

```
Attention(Q, K, V) = softmax(QKᵀ / √d_k) V
Scaling by 1/√d_k prevents softmax saturation for large d_k.
```

---

## 4. Convergence Diagnostics

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Loss = NaN after a few steps | Gradient explosion | Reduce lr, clip gradients, check data |
| Loss plateaus early | Vanishing gradients / saddle | Residual connections, LayerNorm, lr warmup |
| Train loss drops, val rises | Overfitting | Dropout, weight decay, early stopping, more data |
| Loss oscillates | lr too high | Reduce lr, scheduler with warmup |

### Weight initialization

| Method | Formula | When |
|--------|---------|------|
| Xavier (Glorot) | U(-√(6/(n_in+n_out)), √(6/(n_in+n_out))) | sigmoid/tanh |
| Kaiming (He) | N(0, √(2/n_in)) | ReLU/GELU |
| Normal (0.02) | N(0, 0.02) | Transformer (GPT-style) |

### Batch-size scaling (linear scaling rule)

When multiplying batch size by k, multiply lr by k (up to a limit); use warmup
to stabilize. Breaks down above batch ~8K — use LARS/LAMB for very large batches.

---

## 5. Regularization

| Method | Math | Effect |
|--------|------|--------|
| L1 (Lasso) | λ Σ\|w_i\| | Sparsity |
| L2 (Ridge / Weight Decay) | λ Σ w_i² | Shrinkage |
| Dropout | Randomly zero p of activations | Implicit ensemble |
| Label smoothing | (1-ε)·one_hot + ε/K | Prevents overconfidence |
| Spectral normalization | W / σ(W) | Lipschitz constraint |
