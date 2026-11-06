import sys
from pathlib import Path

import onnx
from onnxruntime.quantization import QuantType, quantize_dynamic

source = Path(sys.argv[1])
target = Path(sys.argv[2])
variant = sys.argv[3]

graph = onnx.load(str(source)).graph
matmuls = [node.name for node in graph.node if node.op_type == "MatMul"]
attention = [name for name in matmuls if "attention" in name.lower()]
feed_forward = [name for name in matmuls if "attention" not in name.lower()]

options = {
    "per_channel": dict(per_channel=True, weight_type=QuantType.QInt8),
    "per_channel_reduce": dict(per_channel=True, reduce_range=True, weight_type=QuantType.QInt8),
    "ffn_only": dict(per_channel=True, weight_type=QuantType.QInt8, nodes_to_exclude=attention),
    "attention_only": dict(per_channel=True, weight_type=QuantType.QInt8, nodes_to_exclude=feed_forward),
}[variant]
quantize_dynamic(str(source), str(target), op_types_to_quantize=["MatMul"], **options)
print(variant, "matmuls", len(matmuls), "attention", len(attention), "ffn", len(feed_forward), target.stat().st_size // 1_000_000, "MB")
