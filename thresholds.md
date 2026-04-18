# Quality Gate v1 Threshold Guide

This document explains how `src/core/quality_gate.py` rejects low-quality inputs before expensive model inference.

## Why Gate Before Inference
- Save GPU/CPU time on unusable images.
- Avoid meaningless model outputs from bad inputs.
- Return explainable rejection reasons to users.

## Checks and Reason Codes

| Check | Metric | Default Threshold | Reason Code | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| Resolution | `width`, `height` | `width < 150` or `height < 150` | `low_resolution` | Image is too small for stable detection. |
| Blur | Variance of Laplacian | `< 80.0` | `too_blurry` | Edge details are too weak. |
| Too dark | Mean grayscale brightness | `< 30.0` | `too_dark` | Underexposed image. |
| Too bright | Mean grayscale brightness | `> 240.0` | `too_bright` | Overexposed image. |
| Heavy compression | Blockiness ratio (`boundary_diff / non_boundary_diff`) | `> 1.8` | `too_compressed` | Strong 8x8 JPEG artifacts detected. |

## Explainable Output (What to Show in Report)

The gate returns these fields:
- `reasons`: machine-friendly codes.
- `reason_details`: each reason with measured value + threshold.
- `metrics`: raw measured scores.
- `applied_thresholds`: actual thresholds used in this run.

Example:

```json
{
  "is_valid": false,
  "reasons": ["too_blurry", "too_dark"],
  "reason_details": [
    {
      "code": "too_blurry",
      "message": "Image is too blurry for reliable inference.",
      "value": 45.12,
      "threshold": {"min_blur_score": 80.0}
    },
    {
      "code": "too_dark",
      "message": "Image is too dark.",
      "value": 25.40,
      "threshold": {"min_brightness": 30.0}
    }
  ],
  "metrics": {
    "resolution": [800, 600],
    "blur_score": 45.12,
    "brightness": 25.40,
    "block_boundary_diff_mean": 7.81,
    "block_non_boundary_diff_mean": 3.34,
    "blockiness_ratio": 2.34
  },
  "applied_thresholds": {
    "min_width": 150,
    "min_height": 150,
    "min_blur_score": 80.0,
    "min_brightness": 30.0,
    "max_brightness": 240.0,
    "max_blockiness_ratio": 1.8,
    "enable_compression_check": true
  }
}
```

## Suggested Tuning Procedure

1. Prepare a calibration set (at least 30 to 50 images):
- Normal images that should pass.
- Borderline images (slightly blur/dark/compressed).
- Clearly bad images.

2. Run gate and record metrics.

3. Tune in this order:
- `min_width`, `min_height`
- `min_blur_score`
- `min_brightness`, `max_brightness`
- `max_blockiness_ratio`

4. Target behavior:
- False reject rate on normal images should be low.
- Clearly bad images should be consistently rejected.

## Config Example

Add this section in `config.yaml` to override defaults:

```yaml
quality_gate:
  min_width: 150
  min_height: 150
  min_blur_score: 80.0
  min_brightness: 30.0
  max_brightness: 240.0
  max_blockiness_ratio: 1.8
  enable_compression_check: true
```
