# VRAM Optimization Summary for SpaTracker2

## Overview
This document describes the VRAM optimization techniques implemented in SpaTracker2 to reduce GPU memory usage and enable running on GPUs with limited VRAM.

**Key innovations inspired by Wan2GP and vLLM:**
- CPU-First model storage
- Sleep mode for on-demand VRAM release
- Model weight caching for faster subsequent loads

## Key Innovation: CPU-First Model Loading with Sleep Mode

**Models are stored in CPU RAM by default** and only moved to GPU during actual processing. Additionally, sleep mode allows releasing 90%+ of GPU memory on demand.

### How It Works:

```python
# 1. Model loaded to CPU RAM (not GPU!)
model = model_manager.get_vggt_model()  # Stored in CPU

# 2. Move to GPU only for inference
model = model_manager.move_to_gpu(model)

# 3. Run inference
with torch.cuda.amp.autocast(dtype=torch.bfloat16):
    result = model(input_tensor)

# 4. Immediately move back to CPU
model = model_manager.move_to_cpu(model)
torch.cuda.empty_cache()

# 5. GPU memory is now free for other tasks!

# 6. Optional: Enter sleep mode to free even more memory
model_manager.sleep(level=1)  # Free GPU, keep cache
model_manager.sleep(level=2)  # Deep sleep: free GPU + clear cache

# 7. Wake up when needed
model_manager.wake_up()
```

## Implemented Optimizations

### 1. CPU-First Model Storage ✅ (MOST IMPORTANT)
- **Status**: Implemented
- **Benefit**: Models stay in system RAM, VRAM only used during actual processing
- **How it works**:
  - All models load to CPU RAM initially
  - Moved to GPU milliseconds before inference
  - Moved back to CPU immediately after inference
  - GPU memory freed between operations

### 2. Sleep Mode (vLLM-inspired) ✅
- **Status**: Implemented
- **Benefit**: Release 90%+ GPU memory on demand
- **Levels**:
  - **Level 1**: Move all models to CPU, keep weight cache (fast resume)
  - **Level 2 (Deep Sleep)**: Move all models to CPU, clear weight cache (maximum VRAM free)
- **Use cases**:
  - Running other GPU applications between inferences
  - Multi-model workflows
  - Long idle periods

```python
# Free GPU memory, keep models cached in CPU
model_manager.sleep(level=1)

# ... do other GPU work ...

# Fast wake up (models still in CPU cache)
model_manager.wake_up()

# Deep sleep - free everything
model_manager.sleep(level=2)
```

### 3. Model Weight Caching ✅
- **Status**: Implemented
- **Benefit**: Faster subsequent model loads (no re-download)
- **How it works**:
  - First load: Download from HuggingFace to CPU RAM
  - Subsequent loads: Load from CPU cache (instant)
  - Cache persists until deep sleep (level 2)
- **Cache info**:
  ```python
  info = model_manager.get_cache_info()
  print(info)  # Shows cached models and sleep status
  ```

### 4. xFormers Memory-Efficient Attention ✅
- **Status**: Installed (v0.0.30)
- **Benefit**: Reduces memory usage in attention layers by up to 50%
- **Usage**: Automatically enabled when available
- **Additional**: Triton installed for maximum performance

### 5. Mixed Precision Inference (AMP) ✅
- **Status**: Implemented
- **Benefit**: Reduces VRAM usage by ~50% during inference
- **Implementation**: Uses `torch.cuda.amp.autocast(dtype=torch.bfloat16)`
- **Applied to**:
  - VGGT model inference
  - Tracker model inference
  - SAM inference

### 6. Automatic Memory Cleanup ✅
- **Status**: Implemented
- **Benefit**: Prevents VRAM accumulation over time
- **Methods**:
  - `torch.cuda.empty_cache()` after each inference
  - Models moved back to CPU after use
  - `gc.collect()` for garbage collection
  - Error handling includes memory cleanup

### 7. Lazy Model Loading ✅
- **Status**: Implemented
- **Benefit**: Models are only loaded when needed, not at startup
- **How it works**:
  - Models load to CPU on first request
  - No VRAM used at application startup

## ModelManager Class

The `ModelManager` class provides centralized memory management with sleep mode and caching:

```python
# Get a model (stored in CPU RAM)
vggt_model = model_manager.get_vggt_model()
tracker_model = model_manager.get_tracker_model(mode="offline")
predictor = model_manager.get_predictor()

# Move to GPU for inference
model = model_manager.move_to_gpu(model)
# ... run inference ...
# Move back to CPU
model = model_manager.move_to_cpu(model)

# Sleep mode - free GPU memory
model_manager.sleep(level=1)  # Keep cache
model_manager.sleep(level=2)  # Deep sleep - clear cache

# Wake up
model_manager.wake_up()

# Check cache status
info = model_manager.get_cache_info()
print(info)  # {'sleep_mode': False, 'cached_models': ['vggt', 'tracker_offline'], 'num_cached': 2}
```

## Memory Flow

### Before Optimizations:
```
Startup: All models loaded to GPU → High VRAM usage (8GB+)
During use: Models stay on GPU → VRAM never freed
```

### After Optimizations (CPU-First + Sleep Mode):
```
Startup: No models loaded → VRAM usage (~100MB)
Models loaded: All in CPU RAM → VRAM still ~100MB
During SAM inference: SAM → GPU → Run → CPU + empty_cache() → VRAM freed
During VGGT: VGGT → GPU → Run → CPU + empty_cache() → VRAM freed
During tracking: Tracker → GPU → Run → CPU + empty_cache() → VRAM freed
Sleep mode L1: All models in CPU cache → VRAM ~100MB (90%+ freed)
Sleep mode L2: Cache cleared → VRAM ~100MB, RAM freed too
Idle after use: All models in CPU → VRAM ~100MB
```

## Expected VRAM Reduction

| Scenario | Before | After (CPU-First) | With Sleep Mode | Reduction |
|----------|--------|-------------------|-----------------|-----------|
| Idle (startup) | ~6GB | ~100MB | ~100MB | **98%** |
| Models loaded | ~6GB | ~100MB | ~100MB | **98%** |
| During SAM inference | ~6GB | ~2GB | N/A | **67%** |
| During VGGT inference | ~8GB | ~3GB | N/A | **62%** |
| During tracking | ~10GB | ~4GB | N/A | **60%** |
| Peak usage | ~12GB | ~4GB | N/A | **67%** |
| Sleep mode L1 | ~6GB | ~100MB | **~100MB** | **98%** |
| Sleep mode L2 | ~6GB | ~100MB | **~50MB** | **99%** |

## System RAM Requirements

Since models are now stored in CPU RAM:

| Model | RAM Usage | Cached |
|-------|-----------|--------|
| VGGT4Track (Front) | ~2.5 GB | Yes |
| SpaTrackerV2-Offline | ~1.5 GB | Yes |
| SpaTrackerV2-Online | ~1.5 GB | Yes |
| SAM Predictor | ~0.5 GB | Yes |
| **Total** | **~6 GB** | **All cached** |

**Minimum system RAM recommended: 16GB**  
**Recommended system RAM: 32GB+**

## Sleep Mode Details

Inspired by vLLM's sleep mode implementation, SpaTracker2 now supports two levels of sleep:

### Level 1 Sleep (Fast Suspend)
- **What happens**:
  - All models moved to CPU
  - Model weights cached in CPU RAM
  - GPU memory freed (90%+)
- **Resume speed**: Fast (models still in cache)
- **Use case**: Short breaks, switching to other GPU tasks
- **RAM usage**: ~6GB (models cached)

### Level 2 Sleep (Deep Sleep)
- **What happens**:
  - All models moved to CPU
  - Model weight cache cleared
  - GPU memory freed (95%+)
  - System RAM freed
- **Resume speed**: Slower (models need to reload from HuggingFace)
- **Use case**: Long idle periods, maximum memory savings
- **RAM usage**: Minimal (only buffers)

## Requirements

- **PyTorch**: 2.7.0+ with CUDA 12.8
- **xFormers**: 0.0.30
- **Triton**: 3.3.1 (for xFormers optimizations)
- **CUDA-capable GPU**: Minimum 2GB VRAM (4GB+ recommended)
- **System RAM**: Minimum 8GB (16GB+ recommended)

## Performance Impact

### Trade-offs:
- **Slightly slower** (~5-10% overhead) due to CPU↔GPU transfers
- **Much lower VRAM usage** - can run on GPUs with 4GB VRAM
- **More stable** - no VRAM accumulation over time
- **Better multitasking** - GPU freed for other tasks between inferences

### When to use:
- ✅ Low VRAM GPUs (4GB-6GB)
- ✅ Processing multiple videos sequentially
- ✅ Running other GPU applications simultaneously
- ✅ Long-running sessions (no VRAM leaks)

### When you might want to disable:
- ❌ High VRAM GPUs (12GB+) with no other GPU tasks
- ❌ Maximum performance is critical
- ❌ Processing hundreds of short videos (transfer overhead adds up)

## Additional Optimizations to Consider

If you still experience VRAM issues:

1. **Reduce frame count**: Lower `MAX_FRAMES_OFFLINE` and `MAX_FRAMES_ONLINE` constants
2. **Reduce resolution**: Models automatically resize, but you can set lower max dimensions
3. **Batch size 1**: Already implemented - processes one video at a time
4. **Close other GPU applications**: Ensure no other programs are using GPU memory
5. **Use CPU for preprocessing**: Some preprocessing can be done on CPU before moving to GPU

## Troubleshooting

### Out of Memory Errors
1. Check GPU memory: `nvidia-smi` (Windows) or `watch -n 1 nvidia-smi` (Linux)
2. Verify models are in CPU: Check logs for "Loading to CPU..." messages
3. Manually clear memory: Call `model_manager.clear_gpu_memory()`
4. Reduce video resolution before processing
5. Process shorter video segments

### Slow Performance
1. Ensure xFormers is loaded: Check startup logs for "✅ xFormers enabled"
2. Verify GPU is being used: Monitor with `nvidia-smi` during inference
3. Check Triton is installed: `python -c "import triton; print(triton.__version__)"`
4. The slight slowdown from CPU↔GPU transfers is normal and expected

### High System RAM Usage
1. This is expected - models are stored in RAM intentionally
2. 6GB RAM usage for models is normal
3. Close other applications if RAM is limited
4. Consider adding more system RAM if you have <16GB

## Technical Details

### cudnn Benchmark Mode
```python
torch.backends.cudnn.benchmark = True
```
Optimizes convolution operations for better performance.

### bfloat16 Precision
Using `torch.bfloat16` instead of `float16`:
- Better numerical stability
- Same memory savings as float16
- Native support on Ampere+ GPUs (RTX 30xx+)

### Memory Transfer Optimization
```python
# Efficient CPU↔GPU transfer
model = model.to("cuda")  # Move to GPU
# ... inference ...
model = model.to("cpu")   # Move back to CPU
torch.cuda.empty_cache()  # Clear cached memory
gc.collect()              # Python garbage collection
```
