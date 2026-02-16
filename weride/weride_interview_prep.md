# WeRide 面试复习材料 (针对面经整理)

根据 WeRide 最近的面经，面试风格偏向于：
1.  **简历深挖 (Deep Dive)**: 尤其是 Domain Knowledge (CV, Perception, Sensor Fusion) 和 PhD 研究内容。
2.  **Coding**: 偏向于表达式解析、计算器、DFS/BFS、图论 (Union Find) 和位运算。
3.  **八股**: OS、分布式、数据库细节。
4.  **Math/Logic**: 卡尔曼滤波 (Kalman Filter) 出现频率极高。

---

## 1. 核心算法题 (Coding)

### 1.1 表达式展开 (Expression Expansion) - 高频计算器变种
**问题**: 将带有括号、加法、乘法的表达式展开。
*   **Case 1 (Simple)**: `(a+b)*(c+d)` -> `ac+ad+bc+bd`. (无嵌套，无外部 + 号)
*   **Case 2 (Hard)**: `a+b*c*(d+e+f)+k` -> `a+bcd+bce+bcf+k`. (混合运算)

**思路**:
这道题本质上是 **多项式乘法 (Polynomial Multiplication)**。
可以看作是一个层级结构：
1.  **Term (项)**: 比如 `a`, `b`, `c`。
2.  **Factor (因子)**: 由 Term 组成的乘积，比如 `b*c`。
3.  **Expression (表达式)**: 由 Factor 组成的和，比如 `a + b*c`。

**数据结构**:
用 `List<List<String>>` 来表示一个中间结果。
例如 `(a+b)` 表示为 `[[a], [b]]` (两项，每项包含一个因子)。
`(c+d)` 表示为 `[[c], [d]]`。
`(a+b)*(c+d)` 就是两个 List 的笛卡尔积 (Cartesian Product) -> `[[a,c], [a,d], [b,c], [b,d]]` -> `ac+ad+bc+bd`。

对于 Case 2 `a+b*c*(d+e+f)`:
1.  解析 `a` -> `[[a]]`
2.  遇到 `+`，保存当前 currentRes 到 finalRes。
3.  解析 `b` -> `[[b]]`
4.  遇到 `*`，解析 `c` -> `[[c]]`，与前一个结果做笛卡尔积 -> `[[b,c]]`。
5.  遇到 `*`，解析 `(d+e+f)` -> 递归处理括号 -> `[[d], [e], [f]]`。
6.  与 `[[b,c]]` 做笛卡尔积 -> `[[b,c,d], [b,c,e], [b,c,f]]`。
7.  最后把所有结果加起来。

### 1.2 用户邮箱分组 (User Grouping by Email)
**问题**: 给定 user 和 emails，如果两个 user 有相同的 email，则视为同一个 user group。
**LeetCode 对应**: [721. Accounts Merge](https://leetcode.com/problems/accounts-merge/)
**解法 (Union Find)**:
1.  遍历每个 User 的每个 Email。
2.  维护一个 Map: `Email -> UserID`。
3.  如果 Email 已经存在 Map 中，说明当前 User 与 Map 中记录的 UserID 是同一个人 -> `union(currentUser, recordedUser)`。
4.  如果没有，记录 `Map[email] = currentUser`。
5.  最后遍历 Map，根据 Find(user) 的 Root ID 将 Emails 聚合。

### 1.3 链表交换节点 (Swap Nodes in Pairs / Reverse Nodes in k-Group)
**问题**: 交换链表节点引用 (Switch Reference, not Value)。
**LeetCode 对应**: [24. Swap Nodes in Pairs](https://leetcode.com/problems/swap-nodes-in-pairs/) 或 [25. Reverse Nodes in k-Group](https://leetcode.com/problems/reverse-nodes-in-k-group/)。
**注意**: 面试官特别强调了 **Switch Reference**。
**代码 template**:
```java
// Dummy node is key
ListNode dummy = new ListNode(0);
dummy.next = head;
ListNode prev = dummy;
while (prev.next != null && prev.next.next != null) {
    ListNode first = prev.next;
    ListNode second = prev.next.next;
    // Swap
    first.next = second.next;
    second.next = first;
    prev.next = second;
    // Move
    prev = first;
}
return dummy.next;
```

---

## 2. 领域知识 (Domain Knowledge & Math)

### 2.1 卡尔曼滤波 (Kalman Filter) - 必考
*   **用途**: 在存在噪声 (Noise) 的数据中估计动态系统的状态。常用于**自动驾驶 (定位/感知/融合)**。
*   **核心步骤**:
    1.  **预测 (Predict)**: 根据上一时刻的状态和运动方程，猜测当前时刻的状态 (先验估计)。
        *   $ \hat{x}_k^- = A \hat{x}_{k-1} + B u_k $ (状态预测)
        *   $ P_k^- = A P_{k-1} A^T + Q $ (协方差预测，误差变大)
    2.  **更新 (Update)**: 拿着测量值 (传感器数据)，修正刚才的猜测 (后验估计)。
        *   $ K_k = P_k^- H^T (H P_k^- H^T + R)^{-1} $ (计算卡尔曼增益 Kalman Gain)
        *   $ \hat{x}_k = \hat{x}_k^- + K_k (z_k - H \hat{x}_k^-) $ (修正状态: 预测 + 增益*(测量 - 预测))
        *   $ P_k = (I - K_k H) P_k^- $ (更新误差协方差，误差变小)
*   **直观理解**: 加权平均。如果你相信模型 (Q小)，K就小；如果你相信传感器 (R小)，K就大。

### 2.2 传感器融合 (Sensor Fusion)
*   **多模态**: Lidar (激光雷达 - 测距准，无纹理), Camera (相机 - 纹理丰富，测距差), Radar (雷达 - 测速准，分辨率低)。
*   **融合层次**:
    *   **Data Level (Early Fusion)**: 原始数据融合 (e.g. RGB + Point Cloud 投影)。
    *   **Feature Level**: 提取特征后融合。
    *   **Object Level (Late Fusion)**: 各自检测出物体 (Bounding Box)，再通过 IoU 或 Kalman Filter 进行匹配和轨迹平滑。WeRide 可能更多问这个。

---

## 3. 面试风格贴士 (Tips)
*   **Domain Knowledge**: 既然有人被问了 C++ 和 CV，如果你简历里有写 (特别是 PhD)，一定要准备好这部分。即便岗位是 General SDE，WeRide 的 Infra 也是服务于 Autonomous Driving 的。
*   **C++ vs Python**: 面试官可能会问 C++ 指针/引用问题，因为自动驾驶底层栈大量用 C++ (ROS/Cyber RT)。
*   **Aggressive Style**: 有个别面试官风格比较直接 (Challenge/打断)。**不要慌**，这是 Stress Test。保持冷静，解释清楚你的 Trade-off。
*   **System Design**: “开放 sys design 题目”。可能涉及:
    *   **海量 Log 收集与处理**: 自动驾驶车每天产生 TB 级数据。
    *   **任务调度系统**: 车端任务 vs 云端仿真任务。
