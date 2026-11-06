import sys
from pathlib import Path

import onnx
from onnxruntime.quantization import QuantType, quantize_dynamic
from onnxruntime.quantization.matmul_nbits_quantizer import DefaultWeightOnlyQuantConfig, MatMulNBitsQuantizer

source, target, bits = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
model = onnx.load(str(source))
config = DefaultWeightOnlyQuantConfig(block_size=32, is_symmetric=True, bits=bits)
quantizer = MatMulNBitsQuantizer(model, bits=bits, algo_config=config)
quantizer.process()
quantizer.model.save_model_to_file(str(target), True)
print(target.name, target.stat().st_size // 1_000_000, "MB")
