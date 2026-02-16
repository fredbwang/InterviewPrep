# 分布式基础设施深度补充 (Distributed Infra Deep Dive)

本文档补充了 Terraform 机制、共识算法 (Raft/ZAB)、Kubernetes 控制器模式以及 MQ 消费模型对比，填补此前文档的空白。

---

## 1. 分布式共识算法原理 (Consensus Algorithms)

针对“中间件选 Master 逻辑”的深度回答。

### 1.1 Raft 算法 (Etcd, Kafka KRaft, RocketMQ DLedger)
*   **核心状态**: Leader (领导者), Follower (跟随者), Candidate (候选人)。
*   **任期 (Term)**: 逻辑时钟，单调递增。每个 RequestVote/AppendEntries RPC 都带 Term。高 Term 压制低 Term。
*   **选主过程 (Leader Election)**:
    1.  Follower 超时 (Randomized Timeout) 未收到心跳，转为 Candidate，Team++，给自己投票，并发起 RequestVote。
    2.  **获胜条件**: 收到多数派 (Quorum, N/2+1) 的投票。
    3.  **投票限制**: 仅投票给 Log 至少和自己一样新 (LastLogTerm > My Or (LastLogTerm == My And LastLogIndex >= My)) 的 Candidate。**这保证了拥有最新已提交日志的节点才能当选**。
*   **日志复制 (Log Replication)**:
    1.  Leader 接收命令 -> 写入本地 Log -> 并行发 AppendEntries 给 Followers。
    2.  收到多数派 ACK -> Leader Commit -> Apply to State Machine -> 返回 Client。
    3.  Leader 下次心跳通知 Followers "已 Commit"，Followers 再 Apply。

### 1.2 ZAB 协议 (Zookeeper Atomic Broadcast)
*   **定位**: 专门为 Zookeeper 设计，支持崩溃恢复。
*   **两种模式**:
    1.  **崩溃恢复 (Recovery)**: 当 Leader 挂掉。选举新 Leader (拥有最大 ZXID 的节点)，同步数据，且**丢弃**未 Commit 的旧 Leader 的数据。
    2.  **原子广播 (Broadcast)**: 类似 2PC。Leader Propose -> Follower Ack -> Leader Commit。
*   **ZXID**: 64位 ID。高 32 位是 epoch (纪元)，低 32 位是 counter。

---

## 2. Terraform 核心机制

### 2.1 依赖图与执行流 (DAG & Execution)
*   **DAG (有向无环图)**:
    *   Terraform 不按文件顺序执行，而是解析 Resource 间的引用关系 (如 `instance_id = aws_xx.id`) 构建 DAG。
    *   **并行度**: 独立的子图可以并行创建 (默认 10 并发)。
*   **流程**:
    1.  **Refresh**: 读取 State 文件，调用 Cloud API 获取实际云端状态，更新 State (内存中)。
    2.  **Plan**: 对比 Config (期望) 与 State (实际)。计算 Delta (此阶段**不**修改云资源)。
    3.  **Apply**: 锁住 State 文件 (Locking)，按 DAG 顺序执行 API Call，最后写入新 State。

### 2.2 Reconcile Drift (漂移检测)
*   Terraform 核心价值在于**状态一致性**。如果有人手动在控制台改了 SecurityGroup，`terraform plan` 会检测到 Drift 并试图改回去 (Immutable Infrastructure 理念)。

---

## 3. Kubernetes 控制器原理 (Controller Pattern)

针对“K8s 原理”的核心回答，超越资源对象层面。

### 3.1 声明式 API (Declarative API)
*   用户只定义 **Spec** (期望状态)，Controller 负责让 **Status** (实际状态) 趋近 Spec。
*   **Edge Triggered (边缘触发) vs Level Triggered (水平触发)**: K8s 是水平触发。只关心最终状态，不丢失中间信号。

### 3.2 核心组件机制
*   **Informer & Reflector**:
    *   **List-Watch**: 也就是 Long Polling。Reflector 长连接监听 API Server 的资源变更事件 (Add/Update/Delete)。
    *   **Local Store (Delta FIFO)**: 为了减少对 API Server 的压力，Informer 会在本地维护一份缓存 (Index)。
*   **Reconcile Loop (调和循环)**:
    *   `for { item := workqueue.Get(); reconcile(item); }`
    *   **逻辑**: 
        1.  从 Informer (缓存) 拿当前对象。
        2.  比较 Spec 和实际世界 (比如调 Docker API 看容器还在不在)。
        3.  执行 CRUD 操作修复差异。

---

## 4. MQ 消费模型对比 (Push vs Pull)

针对 MQ 团队的架构设计题。

### 4.1 Push 模型 (RocketMQ 早期 / ActiveMQ)
*   **原理**: Broker 收到消息主动推给 Consumer。
*   **优点**: 实时性极高。
*   **缺点**: 
    *   **慢消费 (Slow Consumer)**: 如果 Consumer 处理慢，Broker 需要在内存维护堆积或阻塞发送，容易把 Broker 拖垮。需要复杂的**流控 (Flow Control)**。

### 4.2 Pull 模型 (Kafka)
*   **原理**: Consumer 记录自己的 Offset，主动去 Broker 拉取。
*   **优点**: 
    *   **解耦**: 速率由 Consumer 自己掌控，适合批处理 (Batch Fetch)。
    *   **Broker 简单**: Broker 是无状态的 (只管存)，不知道 Consumer 消费到哪了。
*   **缺点**: 
    *   **空轮询**: 如果没消息，Consumer 还在不停拉，浪费 CPU/网络。
    *   *优化*: **Long Polling (长轮询)**。带超时时间的 Pull。如果没消息，Broker 挂起请求 500ms，有消息立马返回。

### 4.3 RocketMQ 的方案 (Long Polling Pull)
*   RocketMQ 现在的 Consumer 本质是 **Pull** 模式 (DefaultMQPullConsumer) 或者是 **基于 Pull 的 Push** (DefaultMQPushConsumer - 实际上是 SDK 里启线程不断 Pull，给用户感觉像 Push)。
*   结合了 Pull 的没背压风险和 Long Polling 的低延迟。
