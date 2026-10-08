# Offline Client-Side Prediction

The goal is to enable full client-side offline prediction using WebAssembly (WASM) and ONNX.

## Current Status
We have deferred the full WASM/ONNX compilation of the LightGBM booster because doing so requires a native C++ toolchain (e.g., Emscripten, CMake) which is currently unfeasible to set up automatically in this Windows environment without manual user intervention.

## Implementation Stub
To implement this in the future:
1. Export the LightGBM model to ONNX using `onnxmltools`:
   ```python
   import onnxmltools
   from onnxmltools.convert import convert_lightgbm
   from skl2onnx.common.data_types import FloatTensorType
   import lightgbm as lgb
   
   booster = lgb.Booster(model_file="artifacts/model/model.txt")
   initial_type = [("float_input", FloatTensorType([None, NUM_FEATURES]))]
   onnx_model = convert_lightgbm(booster, initial_types=initial_type)
   
   with open("artifacts/model/model.onnx", "wb") as f:
       f.write(onnx_model.SerializeToString())
   ```
2. In the React frontend, include `onnxruntime-web` to load `model.onnx`.
3. Replicate the `FeaturePipeline` logic in JavaScript/TypeScript (e.g., applying the `TargetEncoder` mappings and distance calculations).
4. Run predictions synchronously in the browser offline.
