import onnx

from onnxsharp import (
    Model,
    Node,
    LogicalSubgraphInfo,
    create_graph_from_logical_subgraph,
)


def test_subgraph_extraction():
    src = "./testdata/ort_sample_model.onnx"
    model_proto = onnx.load(src)
    m = Model.from_proto(model_proto)

    inputs_of_yield = set()

    def output_filter_func(node: Node):
        if node.type == "YieldOp":
            for i in node.input_arg_names:
                inputs_of_yield.add(i)

    print(inputs_of_yield)
    m._graph.iterate_node(output_filter_func)

    subgraph_inputs = set()

    def input_filter_func(node: Node):
        if node.type == "Gemm" and node.name == "Gemm_0":
            for i in node.input_arg_names:
                subgraph_inputs.add(i)

    print(subgraph_inputs)
    m._graph.iterate_node(input_filter_func)

    subgraph_info = LogicalSubgraphInfo(
        m._graph,
        list(inputs_of_yield),
        list(subgraph_inputs),
    )

    subgraph = create_graph_from_logical_subgraph(subgraph_info)
    new_m = Model.copy_config(m, subgraph)

    tmp_filename = "extract_subgraph.onnx"
    onnx.save(new_m.to_proto(), tmp_filename)

    model_proto2 = onnx.load(tmp_filename)
    m2 = Model.from_proto(model_proto2)


def test_clip_subgraph_from_output_arg():
    src = "./testdata/ort_sample_model.onnx"
    model_proto = onnx.load(src)
    from onnxsharp import Model, Graph, Node, clip_subgraph_around

    m = Model.from_proto(model_proto)
    new_g = clip_subgraph_around(m._graph, "onnx::Gemm_6")
    new_m = Model.copy_config(m, new_g)

    dest = f"clipped_subgraph.onnx"
    onnx.save(new_m.to_proto(), dest)
