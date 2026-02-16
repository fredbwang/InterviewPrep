class TreeNode:
    def __init__(self, score):
     """
     初始化一个多叉树节点。

     :param score: 该节点的分值
     """
     self.score = score # 节点的值
     self.children = [] # 存储子节点的列表

def max_root_to_leaf_sum(root):
    """
    计算从根节点到叶子节点的最大路径和。

    :param root: TreeNode, 树的根节点
    :return: int, 最大路径和
    """
    if not root: # 空节点直接返回 0
     return 0

    if not root.children: # 如果是叶子节点，直接返回当前节点的值
     return root.score

    # 递归计算所有子节点的最大路径和，并取最大值
    max_child_sum = max(max_root_to_leaf_sum(child) for child in root.children)

    # 返回当前节点的值加上其子树的最大路径和
    return root.score + max_child_sum