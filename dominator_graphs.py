try:
  import tanto
except ModuleNotFoundError:
  import binaryninja
  from os import path
  from sys import path as python_path
  python_path.append(path.abspath(path.join(binaryninja.user_plugin_path(), '../repositories/official/plugins')))
  import tanto

from tanto.tanto_view import TantoView

from binaryninja import FlowGraph, FlowGraphNode
from binaryninja.enums import BranchType


class DominatorTreeChildrenSlice(tanto.slices.Slice):
  def __init__(self, _):
    self.update_style = tanto.slices.UpdateStyle.ON_NAVIGATE

  def get_flowgraph(self) -> FlowGraph:
    flowgraph = FlowGraph()

    current_block = tanto.helpers.get_current_il_basic_block()
    if current_block is None:
      return flowgraph

    node = FlowGraphNode(flowgraph)
    node.lines = current_block.get_disassembly_text(tanto.helpers.get_disassembly_settings())
    flowgraph.append(node)

    for child in current_block.dominator_tree_children:
      child_node = FlowGraphNode(flowgraph)
      child_node.lines = child.get_disassembly_text(tanto.helpers.get_disassembly_settings())
      flowgraph.append(child_node)
      node.add_outgoing_edge(BranchType.UnconditionalBranch, child_node)
    return flowgraph


TantoView.register_slice_type("Dominator Tree Children", DominatorTreeChildrenSlice)


class FullDominatorTreeSlice(tanto.slices.Slice):
  def __init__(self, _):
    self.update_style = tanto.slices.UpdateStyle.ON_NAVIGATE

  def get_flowgraph(self) -> FlowGraph:
    flowgraph = FlowGraph()

    if (function := tanto.helpers.get_current_il_function()) is None:
      return None

    current_block = function[0].il_basic_block
    if current_block is None:
      return flowgraph

    root_node = FlowGraphNode(flowgraph)
    root_node.lines = current_block.get_disassembly_text(tanto.helpers.get_disassembly_settings())
    flowgraph.append(root_node)

    def add_children(block, parent_node):
      for child in block.dominator_tree_children:
        child_node = FlowGraphNode(flowgraph)
        child_node.lines = child.get_disassembly_text(tanto.helpers.get_disassembly_settings())
        flowgraph.append(child_node)
        parent_node.add_outgoing_edge(BranchType.UnconditionalBranch, child_node)
        add_children(child, child_node)

    add_children(current_block, root_node)
    return flowgraph


TantoView.register_slice_type("Dominator Tree", FullDominatorTreeSlice)


class DominanceFrontierSlice(tanto.slices.Slice):
  def __init__(self, _):
    self.update_style = tanto.slices.UpdateStyle.ON_NAVIGATE

  def get_flowgraph(self) -> FlowGraph:
    flowgraph = FlowGraph()

    current_block = tanto.helpers.get_current_il_basic_block()
    if current_block is None:
      return flowgraph

    node = FlowGraphNode(flowgraph)
    node.lines = current_block.get_disassembly_text(tanto.helpers.get_disassembly_settings())
    flowgraph.append(node)

    for frontier_block in current_block.dominance_frontier:
      frontier_node = FlowGraphNode(flowgraph)
      frontier_node.lines = frontier_block.get_disassembly_text(tanto.helpers.get_disassembly_settings())
      flowgraph.append(frontier_node)
      node.add_outgoing_edge(BranchType.UnconditionalBranch, frontier_node)
    return flowgraph


TantoView.register_slice_type("Dominance Frontier", DominanceFrontierSlice)


class DominatorsSlice(tanto.slices.Slice):
  def __init__(self, _):
    self.update_style = tanto.slices.UpdateStyle.ON_NAVIGATE

  def get_flowgraph(self) -> FlowGraph:
    flowgraph = FlowGraph()

    current_block = tanto.helpers.get_current_il_basic_block()
    if current_block is None:
      return flowgraph

    node = FlowGraphNode(flowgraph)
    node.lines = current_block.get_disassembly_text(tanto.helpers.get_disassembly_settings())
    flowgraph.append(node)

    while (current_block := current_block.immediate_dominator) is not None:
      dom_node = FlowGraphNode(flowgraph)
      dom_node.lines = current_block.get_disassembly_text(tanto.helpers.get_disassembly_settings())
      flowgraph.append(dom_node)

      dom_node.add_outgoing_edge(BranchType.UnconditionalBranch, node)
      node = dom_node
    return flowgraph


TantoView.register_slice_type("Dominators", DominatorsSlice)


class PostDominatorsSlice(tanto.slices.Slice):
  def __init__(self, _):
    self.update_style = tanto.slices.UpdateStyle.ON_NAVIGATE

  def get_flowgraph(self) -> FlowGraph:
    flowgraph = FlowGraph()

    current_block = tanto.helpers.get_current_il_basic_block()
    if current_block is None:
      return flowgraph

    current_node = FlowGraphNode(flowgraph)
    current_node.lines = current_block.get_disassembly_text(tanto.helpers.get_disassembly_settings())
    flowgraph.append(current_node)

    while (current_block := current_block.immediate_post_dominator) is not None:
      new_node = FlowGraphNode(flowgraph)
      new_node.lines = current_block.get_disassembly_text(tanto.helpers.get_disassembly_settings())
      flowgraph.append(new_node)

      current_node.add_outgoing_edge(BranchType.UnconditionalBranch, new_node)
      current_node = new_node
    return flowgraph


TantoView.register_slice_type("Post Dominators", PostDominatorsSlice)
