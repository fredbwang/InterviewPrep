# 消息队列 (MQ) 深度挖掘与复习 - Alibaba 面试

本文件专注于 Kafka 和 RocketMQ 的底层原理、架构设计及对比，针对阿里云 MQ 团队面试要求的深度。

---

## 1. Kafka 核心原理深度解析

### 1.1 日志存储与读写优化 (高性能核心)
*   **顺序写 (Sequential Write)**: 磁盘顺序写速度 (600MB/s) 远大于随机写 (100KB/s)。Kafka 强制 Partition 追加写。
*   **零拷贝 (Zero Copy)**:
    *   **普通读**: Disk -> Kernel Buffer -> User Buffer -> Socket Buffer -> NIC Buffer (4次拷贝, 4次上下文切换)。
    *   **Kafka (sendfile)**: Disk -> Kernel Buffer --(descriptor)--> Socket Buffer -> NIC Buffer (2次拷贝, 2次切换)。Java 中对应 `FileChannel.transferTo()`。
    *   **Memory Mapped Files (mmap)**: 索引文件 (.index, .timeindex) 映射到内存，减少用户态/内核态切换。
*   **页缓存 (PageCache)**: 极度依赖 OS 的 PageCache。Broker 崩溃重启后，PageCache 依然在 OS 中 (只要机器没重启)，热启动快。

### 1.2 高可用与副本机制 (ISR & HW/LEO)
*   **AR (Assigned Replicas)**: 所有副本。
*   **ISR (In-Sync Replicas)**: 与 Leader 保持同步的副本集合。只有 ISR 中的副本才有资格被选为 Leader。
    *   *判定标准*: `replica.lag.time.max.ms` (默认 10s)。如果 Follower 超过这个时间没 fetch，被踢出 ISR。
*   **LEO (Log End Offset)**: 每个副本当前日志的下一条写入位置。
*   **HW (High Watermark)**: ISR 中所有副本的最小 LEO。HW 之前的消息才对 Consumer 可见。这保证了即使 Leader 挂掉，Consumer 读到的数据在所有 ISR 中都存在。
*   **Leader Epoch**: 解决 HW 截断导致的数据不一致问题。每当 Leader 变更，Epoch 加 1。

### 1.3 精确一次 (Exactly Once Semantics - EOS)
*   **幂等性 (Idempotence)**:
    *   范围: 单 Partition，单 Session。
    *   实现: Broker 为 Producer 分配 PID (Producer ID)，每条消息带序列号 (SeqNum)。Broker 维护 `Map<PID, SeqNum>`，重复 SeqNum 直接丢弃。
*   **事务 (Transactions)**:
    *   范围: 跨 Partition，跨 Session (重启后依然有效)。
    *   实现: 引入 **Transaction Coordinator** 组件和内部 Topic `__transaction_state`。
    *   **2PC (两阶段提交)**:
        1.  Producer 发送消息到 Topic (此时消息对 Consumer 不可见)。
        2.  Producer 发起 Commit/Abort。
        3.  Coordinator 向所有涉及的 Partition 写入 **Commit Marker** (特殊的控制消息)。
        4.  Consumer (read_committed) 读到 Marker 时，决定是分发还是丢弃之前的消息。

### 1.4 Consumer Rebalance (重平衡)
*   **触发时机**: Consumer 加入/退出、Topic 增加 Partition、订阅 Topic 变化。
*   **策略**:
    *   **Range**: 默认。按 Partition 范围分配。容易导致倾斜。
    *   **RoundRobin**: 轮询。
    *   **Sticky**: 尽量保持原有分配，减少抖动。
*   **Rebalance 过程 (Eager vs Cooperative)**:
    *   **Eager (旧版)**: "Stop The World"。所有 Consumer 停止消费，放弃所有 Partition，重新分配。
    *   **Cooperative (新版)**: 渐进式。只剥夺需要迁移的 Partition，其他 Partition 继续消费。

---

## 2. RocketMQ 深度剖析 (阿里主场必问)

### 2.1 存储架构设计的差异 (VS Kafka)
*   **Kafka 问题**: 每个 Partition 一个物理文件。当 Topic 极多 (万级) 时，顺序写变为随机写，性能崩塌。
*   **RocketMQ 优化**: 
    *   **CommitLog**: **所有 Topic** 的消息混杂在一起，顺序写入一个巨大的 CommitLog 文件。保证了**全局顺序写**。
    *   **ConsumeQueue**: 相当于索引。轻量级，只存 (Offset, Size, TagHashCode)。每个 Topic/Queue 对应一个。Consumer 读它是随机读，但利用了 PageCache 预读，影响较小。
    *   **优势**: 支持海量 Topic (因为写CommitLog永远是顺序的)，适合阿里/云厂商场景。

### 2.2 特性功能实现
*   **延时消息 (Delay Message)**:
    *   不直接投递到目标 Topic。
    *   投递到内部 Topic `SCHEDULE_TOPIC_XXXX`，根据延迟级别存入不同 Queue。
    *   Broker 内部有定时任务 (Timer) 扫描这些 Queue，到期后还原到真实 Topic。
*   **事务消息 (Transactional Message)**:
    *   实现**最终一致性** (非 2PC)。
    1.  发送 `Half Message` (对消费者不可见)。
    2.  执行本地事务。
    3.  根据本地事务结果 `Commit` 或 `Rollback`。
    4.  *回查机制*: 如果 Broker 没收到结果，会主动回调 Producer 查询事务状态。
*   **Tag 过滤**:
    *   Broker 端基于 Tag HashCode 过滤 (减少网络传输)。
    *   Consumer 端基于 Tag 字符串再次过滤 (解决 Hash 冲突)。

### 2.3 现场设计题思路：设计一个支撑双11的 MQ
*   **切入点**:
    1.  **低延迟写**: 必须 mmap/DirectIO，且必须是 Append-only。
    2.  **削峰填谷**: 存储计算分离 (现在的 Cloud Native 趋势)。Broker 只存，Compute 节点处理。
    3.  **读写分离**: Master 处理写和热读，Slave 处理冷读 (追赶读)。
    4.  **分级存储**: 热数据在 SSD，冷数据自动卸载到 S3/OSS (降低成本)。

---

## 3. 面试高频八股与对比

| 特性 | Kafka | RocketMQ |
| :--- | :--- | :--- |
| **定位** | 日志收集、流计算、超高吞吐 | 业务消息、金融级可靠性、复杂功能 |
| **存储** | Partition 粒度日志 | 单一 CommitLog + ConsumeQueue |
| **吞吐量** | 极大 (百万级) | 很高 (十万级) |
| **可靠性** | 强 (ISR) | 极强 (同步双写, Dledger) |
| **顺序消息** | Partition 有序 | Queue 有序 |
| **延迟消息** | 不支持 (需第三方) | 支持 (18个级别) |
| **语言** | Scala/Java | Java |
