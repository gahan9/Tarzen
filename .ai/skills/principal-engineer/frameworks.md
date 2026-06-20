# Frameworks & Libraries Reference

Deep-dive reference for the `principal-engineer` skill. Read this file when
detailed API guidance, integration patterns, or packaging templates are needed.

---

## 1. Orchestration & Agentic Frameworks

### Graph orchestration (e.g. LangGraph >= 0.2)

**When to use**: stateful, multi-step pipelines with conditional routing,
human-in-the-loop, or checkpointing.

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(MyState)
builder.add_node("classify", classify_node)
builder.add_node("analyze", analyze_node)
builder.add_node("respond", respond_node)

builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", routing_fn, {
    "deep": "analyze",
    "simple": "respond",
})
builder.add_edge("analyze", "respond")
builder.add_edge("respond", END)

graph = builder.compile(checkpointer=checkpointer)
result = graph.invoke({"query": "..."}, config={"configurable": {"thread_id": "t1"}})
```

State reducers for accumulating fields:

```python
from typing import Annotated
from operator import add

class State(TypedDict):
    messages: Annotated[list[str], add]  # appends rather than replaces
    final: str | None
```

### Native-accelerated graph dispatch

If profiling shows graph dispatch (not node execution) is the bottleneck
(>15% of wall-clock), move scheduling to a compiled language via bindings
(e.g. PyO3/maturin for Rust). Only do this when measured — if nodes are 95%+ of
runtime (typical for LLM calls), native dispatch saves nothing (anti-ROI).

### High-throughput LLM serving

For batch inference with prefix caching and constrained decoding, use a
dedicated serving runtime (e.g. vLLM, SGLang) rather than sequential API calls.

### RAG / tool-calling

Use a model-agnostic primitive layer (prompts, parsers, runnables) for RAG and
tool-calling agents. Prefer the core/primitives package over the full framework
unless you need the integration adapters (vector stores, document loaders).

---

## 2. ML Frameworks

### PyTorch (>= 2.0)

```python
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.manual_seed(42)

model = MyModel().to(device, dtype=torch.bfloat16)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
model = torch.compile(model, mode="reduce-overhead")  # 2.0+

model.train()
for batch in dataloader:
    batch = {k: v.to(device) for k, v in batch.items()}
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        loss = model(**batch).loss
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)

model.eval()
with torch.no_grad():
    outputs = model(**inputs)
```

Distributed: `DistributedDataParallel` for throughput; `FullyShardedDataParallel`
(FSDP) or ZeRO-style sharding when the model does not fit on a single device.

| Library | Primary Use | Key Patterns |
|---------|-------------|--------------|
| NumPy | Array ops, linear algebra | `np.einsum`, `np.linalg.svd`, broadcasting |
| pandas | Tabular data, EDA | `.groupby().agg()`, `.pipe()` chains |
| scikit-learn | Classical ML, preprocessing | `Pipeline` + `ColumnTransformer`, `TfidfVectorizer` |

---

## 3. Vector Databases

| DB | Best For |
|----|----------|
| FAISS | Local/embedded, exact & approximate NN |
| Chroma | Local dev, simple API |
| Milvus | Production, billion-scale |
| Pinecone | Managed cloud, serverless |
| Weaviate | Hybrid search (vector + keyword) |

---

## 4. Parallel Programming

### Cross-vendor GPU API mapping

| NVIDIA (CUDA) | Portable (HIP) | Notes |
|---------------|----------------|-------|
| `cudaMalloc` | `hipMalloc` | 1:1 API mapping |
| `cudaMemcpy` | `hipMemcpy` | Same semantics |
| `cudaStream_t` | `hipStream_t` | Same stream model |
| `nvcc` | `hipcc` | Compiler driver |
| `cuBLAS` | `rocBLAS` | GEMM primitives |
| `cuDNN` | `MIOpen` | Conv/RNN/attention |
| `NCCL` | `RCCL` | Collective comms |
| Warp (32 threads) | Wavefront (64 threads) | Critical for occupancy calcs |

### MPI and asyncio

```python
from mpi4py import MPI

comm = MPI.COMM_WORLD
local_data = comm.scatter(data if comm.Get_rank() == 0 else None, root=0)
result = process(local_data)
all_results = comm.gather(result, root=0)
```

```python
import asyncio, aiohttp

async def fetch_all(urls: list[str], concurrency: int = 10) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as session:
        async def _fetch(url: str) -> dict:
            async with sem, session.get(url) as resp:
                resp.raise_for_status()
                return await resp.json()
        return await asyncio.gather(*[_fetch(u) for u in urls])
```

Rules: `asyncio` for I/O-bound concurrency; never block the event loop (use
`asyncio.to_thread()` for blocking libs); bound API calls with `asyncio.Semaphore`.

---

## 5. Profiling & Checkpointing

```python
from torch.profiler import profile, ProfilerActivity, tensorboard_trace_handler

with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    on_trace_ready=tensorboard_trace_handler("./log"),
    record_shapes=True, profile_memory=True, with_stack=True,
) as prof:
    for batch in dataloader:
        train_step(model, batch)
        prof.step()
```

| Tool | Use |
|------|-----|
| `torch.profiler` | Python-level + kernel timing, memory tracking |
| `py-spy` / `scalene` | CPU profiling, GIL contention |
| Vendor kernel profilers | Kernel timing, HW counters, occupancy, roofline |

---

## 6. Python Packaging & Distribution

### pyproject.toml (PEP 621 — the only acceptable format)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "your_package"
version = "0.1.0"
description = "Short project description"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Your Name", email = "you@example.com" }]
classifiers = [
    "Programming Language :: Python :: 3",
    "Framework :: AsyncIO",
    "Typing :: Typed",
]
dependencies = [
    "pydantic>=2.0",
    "aiohttp>=3.9",
]

[project.scripts]
your-package = "your_package.cli:main"

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.23", "ruff>=0.4", "mypy>=1.10", "build>=1.0"]

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "W", "F", "I", "N", "D", "UP", "ANN", "S", "B"]

[tool.ruff.pydocstyle]
convention = "google"

[tool.mypy]
strict = true
python_version = "3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Build and verify

```bash
python -m build
python -m venv /tmp/test-venv && source /tmp/test-venv/bin/activate
pip install dist/your_package-0.1.0-py3-none-any.whl
your-package --help
```

### Package structure for a typed library

```
src/
└── your_package/
    ├── __init__.py      # __version__, public API
    ├── __main__.py      # python -m your_package
    ├── py.typed         # PEP 561 marker (empty file)
    ├── cli.py           # console-script entry point
    ├── config.py        # settings loader
    └── ...
```

Non-negotiables: `py.typed` for typed packages; `src/` layout; `__version__`
matching `pyproject.toml`; deps pinned to a minimum version (`>=`).
