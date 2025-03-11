import tanto
from tanto import helpers
from tanto.tanto_view import TantoView

from binaryninja import FlowGraph


class HierarchyGraph(tanto.slices.Slice):
  def __init__(self, parent: 'tanto.tanto_view.TantoView'):
    self.update_style = tanto.slices.UpdateStyle.ON_NAVIGATE

  def get_flowgraph(self) -> FlowGraph:
    if (expr := helpers.get_selected_expr()) is not None:
      return expr.add_subgraph(FlowGraph(), {})


TantoView.register_slice_type("Hierarchy Graph", HierarchyGraph)
