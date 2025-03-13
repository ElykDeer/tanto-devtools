try:
  import tanto
except ModuleNotFoundError:
  import binaryninja
  from os import path
  from sys import path as python_path
  python_path.append(path.abspath(path.join(binaryninja.user_plugin_path(), '../repositories/official/plugins')))
  import tanto

from tanto.tanto_view import TantoView

from binaryninja.enums import BranchType, InstructionTextTokenType
from binaryninja import FlowGraph, FlowGraphNode, HighLevelILBlock, DisassemblyTextLine, InstructionTextToken


# Inspired by https://github.com/withzombies/bnil-graph

class InstructionGraph(tanto.slices.Slice):
  def __init__(self, parent: 'tanto.tanto_view.TantoView'):
    self.update_style = tanto.slices.UpdateStyle.ON_NAVIGATE

  def traverser(self, expr, flowgraph, nodes):
    if expr.expr_index not in nodes:
      new_node = FlowGraphNode(flowgraph)

      expr_list_index = None
      for field_name, parent_expr, _ in expr.parent.detailed_operands:
        if expr == parent_expr:
          break
        try:
          expr_list_index = parent_expr.index(expr)
          break
        except:
          pass
      else:
        field_name = None

      new_node.lines = list(expr.lines)
      if not isinstance(expr.parent, HighLevelILBlock):
        if expr_list_index is not None:
          new_node.lines = [DisassemblyTextLine([
            InstructionTextToken(InstructionTextTokenType.OperationToken, "."),
            InstructionTextToken(InstructionTextTokenType.FieldNameToken, field_name),
            InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "["),
            InstructionTextToken(InstructionTextTokenType.FieldNameToken, f"0x{expr_list_index:x}", value=expr_list_index),
            InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, "]"),
            InstructionTextToken(InstructionTextTokenType.TextToken, ": ")] + list(expr.lines)[0].tokens)] + list(expr.lines)[1:]
        else:
          new_node.lines = [DisassemblyTextLine([
            InstructionTextToken(InstructionTextTokenType.OperationToken, "."),
            InstructionTextToken(InstructionTextTokenType.FieldNameToken, field_name),
            InstructionTextToken(InstructionTextTokenType.TextToken, ": ")] + list(expr.lines)[0].tokens)] + list(expr.lines)[1:]

      new_node.lines += ["", DisassemblyTextLine([
        InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "<"),
        InstructionTextToken(InstructionTextTokenType.KeywordToken, "class"),
        InstructionTextToken(InstructionTextTokenType.TextToken, ": "),
        InstructionTextToken(InstructionTextTokenType.TypeNameToken, f"{type(expr).__name__}"),
        InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, ">")])]
      flowgraph.append(new_node)
      nodes[expr.expr_index] = new_node

      # Get the things the traverser doesn't
      blacklisted_expr_names = {'true', 'false', 'body', 'cases', 'default'}
      for expr_name, hidden_expr, _ in expr.detailed_operands:
        if expr_name in blacklisted_expr_names:
          continue
        if isinstance(hidden_expr, tanto.helpers.ILInstruction):
          continue
        elif isinstance(hidden_expr, list) and all(isinstance(hidden_sub_expr, tanto.helpers.ILInstruction) for hidden_sub_expr in hidden_expr):
          continue

        hidden_expr_node = FlowGraphNode(flowgraph)
        hidden_expr_node.lines = [
          DisassemblyTextLine([
            InstructionTextToken(InstructionTextTokenType.OperationToken, "."),
            InstructionTextToken(InstructionTextTokenType.FieldNameToken, expr_name),
            InstructionTextToken(InstructionTextTokenType.TextToken, ": "),
            InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "<"),
            InstructionTextToken(InstructionTextTokenType.KeywordToken, "class"),
            InstructionTextToken(InstructionTextTokenType.TextToken, ": "),
            InstructionTextToken(InstructionTextTokenType.TypeNameToken, f"{type(hidden_expr).__name__}"),
            InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, ">")
          ])
        ]
        flowgraph.append(hidden_expr_node)
        new_node.add_outgoing_edge(BranchType.UnconditionalBranch, hidden_expr_node)
    else:
      new_node = nodes[expr.expr_index]

    if isinstance(parent := expr.parent, tanto.helpers.ILInstruction) and parent.expr_index in nodes:
      nodes[parent.expr_index].add_outgoing_edge(BranchType.UnconditionalBranch, nodes[expr.expr_index])

  def get_flowgraph(self) -> FlowGraph:
    if (expr := tanto.helpers.get_selected_expr()) is not None:
      flowgraph = FlowGraph()
      for _ in expr.traverse(self.traverser, flowgraph, {}):
        pass  # Yield all results from the generator. It was easier to add nodes in the recursion instead of pulling out chains and processing all that here
      return flowgraph


TantoView.register_slice_type("Instruction Graph", InstructionGraph)
