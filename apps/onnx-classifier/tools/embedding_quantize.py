import sys
from pathlib import Path

from onnxruntime.quantization import QuantType, quantize_dynamic

source, target = Path(sys.argv[1]), Path(sys.argv[2])
quantize_dynamic(str(source), str(target), op_types_to_quantize=["Gather"], weight_type=QuantType.QUInt8, use_external_data_format=True)
size = target.stat().st_size + (target.parent / (target.name + ".data")).stat().st_size
print(target.name, size // 1_000_000, "MB")
