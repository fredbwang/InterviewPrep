# 阿里巴巴 Cloud MQ 团队面试备忘录 (Alibaba Interview Prep)

针对阿里云 MQ 团队的面试准备，涵盖核心 MQ 原理、分布式系统、存储、云原生及高并发语言特性。

---

## 1. 消息队列 (Message Queue) - 核心考点

### Kafka 原理与架构
*   **基本架构**: Producer -> Broker (Topic -> Partition -> Replica) -> Consumer Group.
*   **Partition 理论**: 
    *   **并行度**: Partition 是 Kafka 并行读写的基本单位。
    *   **顺序性**: 只能保证 Partition 内有序，无法保证 Topic 全局有序。
*   **消息不丢失机制 (Durability)**:
    *   **Producer**: `acks=all` (sr -1)，确保所有 ISR (In-Sync Replicas) 都写入成功。
    *   **Broker**: `min.insync.replicas > 1`，`unclean.leader.election.enable=false` (禁止非 ISR 副本竞选 Leader)。
    *   **Consumer**: 关闭自动提交 (`enable.auto.commit=false`)，处理完业务逻辑后再手动 commit offset。
*   **Exactly Once (精确一次)**:
    *   **幂等性 Producer**: `enable.idempotence=true`。Broker 分配 PID (Producer ID) 和 Sequence Number，自动去重。
    *   **事务 (Transactional API)**: 跨 Partition 的原子写入。配合 `isolation.level=read_committed`。
*   **Kafka 选择 Master (Leader Election)**:
    *   **Partition Leader**: 由 Controller 负责选举，通常选择 ISR 列表中的第一个副本。
    *   **Controller Leader**: 利用 Zookeeper (或 KRaft 中的 Raft 协议) 竞选。

### RocketMQ 设计与对比 (现场设计题)
*   **架构特点**: NameServer (无状态，轻量级) vs ZK。Broker 主从架构。
*   **存储设计**: 
    *   **CommitLog**: 消息主体顺序写入，极致写性能。
    *   **ConsumeQueue**: 逻辑队列，存储消息在 CommitLog 的 offset，用于消费者消费。
    *   **IndexFile**: 支持按 Key 查询消息。
*   **现场设计一个 RocketMQ**:
    *   *关注点*: 存储模型 (顺序写/随机读优化)、高可用 (主从同步/Dledger Raft)、低延迟 (零拷贝 mmap/sendfile)。

---

## 2. 分布式系统与 SLA

### SLA (Service Level Agreement)
*   **定义**: 服务等级协议，通常用“几个 9”衡量可用性。
*   **五个 9 (99.999%)**:
    *   **计算**: 一年停机时间不超过 `365 * 24 * 60 * 5.26 分钟` (大约 5 分钟)。
    *   **如何做到**:
        1.  **冗余 (Redundancy)**: 多机房、多区域部署 (异地多活)。
        2.  **故障转移 (Failover)**: 自动化的监控与切换系统。
        3.  **发布策略**: 灰度发布 (Canary)、蓝绿部署，避免全量故障。
        4.  **柔性可用**: 限流 (Rate Limiting)、熔断 (Circuit Breaking)、降级 (Degradation)。

### 中间件选 Master (Leader Election) 逻辑
*   **Zookeeper (ZAB 协议)**: 类似 2PC，强一致性，用于 Kafka (旧版), HBase, Hadoop。
*   **Etcd/Consul (Raft 协议)**: 强一致性，Leader-Follower 模型，用于 Kubernetes。
*   **Redis Sentinel/Cluster (Gossip/Raft-like)**: 哨兵模式下由 Sentinel 投票选新 Master。
*   **RocketMQ (DLedger)**: 基于 Raft 的 commit log 复制。

---

## 3. 存储: Redis & MySQL

### Redis
*   **持久化 (Persistence)**:
    *   **RDB (Snapshot)**: 二进制快照，恢复快，但可能丢数据。`fork()` 子进程进行写时复制 (COW)。
    *   **AOF (Append Only File)**: 记录写命令，数据全，但文件大恢复慢。AOF Rewrite 压缩。
    *   **混合持久化**: RDB + 增量 AOF。
*   **事务 (Transaction)**:
    *   `MULTI`, `EXEC`, `DISCARD`, `WATCH`。即使通过 `MULTI` 也是弱事务 (不支持回滚)。
    *   **Lua 脚本**: 保证操作原子性 (Atomicity)，是目前实现 Redis 复杂事务的首选。
*   **大可以 (Big Key) 优化**:
    *   **问题**: 阻塞网络 IO，阻塞主线程 (Redis 单线程)。
    *   **解决**: 
        *   拆分 Big Key。
        *   `UNLINK` (异步删除) 代替 `DEL`。
        *   压缩数据。
        *   定期扫描 (`--bigkeys`).

### MySQL
*   **事务原理 (ACID)**:
    *   **A (原子性)**: Undo Log (回滚日志)。
    *   **C (一致性)**: 通过其他三个特性保证。
    *   **I (隔离性)**: MVCC (多版本并发控制) + 锁 (Next-Key Lock)。
    *   **D (持久性)**: Redo Log (重做日志) + WAL (Write-Ahead Logging)。
*   **MVCC 原理**: 
    *   **ReadView**: 事务开始时生成的快照 (主要包含活跃事务 ID 列表)。
    *   **版本链**: 每一行数据通过 undo log 指针串联历史版本。
    *   通过对比 Transaction ID 判断可见性 (RC 级别每次 select 生成 ReadView，RR 级别第一次 select 生成)。

---

## 4. 云原生 (Cloud Native)

### Kubernetes (K8s) 原理
*   **StatefulSet vs Deployment (无状态 Service)**:
    *   **无状态 (Deployment)**: Pod 是互换的，IP 变动不影响，随意扩缩容。
    *   **有状态 (StatefulSet)**: 
        *   **唯一标识**: Pod 有固定的有序名称 (web-0, web-1)。
        *   **存储绑定**: 每个 Pod 对应固定的 PVC/PV，重启后自动挂载原有数据。
        *   **有序部署/删除**: 按顺序启动和停止。
*   **Service**: 流量负载均衡 (ClusterIP, NodePort, LoadBalancer)。

### Terraform
*   **机制**: **Infrastructure as Code (IaC)**。
*   **State (状态文件)**: 记录资源当前状态，用于 `plan` 和 `apply` 时计算差异 (Diff)。通常存储在 S3/OSS 等远端并加锁 (Locking) 防止并发冲突。
*   **HCL**: 声明式语言，描述“不仅要是”。

---

## 5. 高并发与语言特性 (Java & Go)

### 场景题: N 个线程完成 -> M 个线程开始
**如果是 Java:**
1.  **CountDownLatch**: 初始化 `new CountDownLatch(N)`。N 个线程通过 `countDown()`。M 个线程在 `await()` 阻塞等待，计数归零后同时唤醒。
2.  **CyclicBarrier**: 屏障，适用于 N 个线程互相等待到达同一点。
3.  **CompletableFuture**: `CompletableFuture.allOf(future1, ... futureN).create(...)`，异步编排的神器。

**如果是 Go:**
1.  **Sync.WaitGroup**: `wg.Add(N)` -> `wg.Done()` -> `wg.Wait()`。
2.  **Channels**: 通过关闭 channel 广播信号，或者缓冲 channel 传递完成信号。

### Java 线程通信
*   **共享内存**: `volatile` (保证可见性), `synchronized/Lock` (保证互斥)。
*   **等待/通知**: `Object.wait()/notify()`, `Condition.await()/signal()`.
*   **并发工具**: BlockingQueue, CountDownLatch, Semaphore.

### Go 语言特性 (Goroutine & GC)
*   **Goroutine 原理 (GMP 模型)**:
    *   **G (Goroutine)**: 协程，轻量级，初始栈 ~2KB。
    *   **M (Machine)**: 内核级线程 (OS Thread)。
    *   **P (Processor)**: 逻辑处理器，维护本地运行队列 (Local Run Queue)。
    *   **调度机制**: Work Stealing (工作窃取, P 从其他 P 偷任务), Hand Off (P 在 M 阻塞时转移到新 M)。
*   **解决高并发上下文切换**:
    *   **用户态切换**: Goroutine 切换不涉及内核态陷入 (Trap)，只保存少量寄存器 (PC, SP, DX)，成本极低 (纳秒级)。
    *   相比 Java 线程 (MB 级栈，内核调度)，Go 可以轻松支撑百万并发。
*   **GC (垃圾回收) 更新与原理**:
    *   **v1.3**: Mark STW (Stop The World) Sweep. 效率低。
    *   **v1.5**: **三色标记法 (Tri-color Marking)** + 并发标记。虽然减少了 STW，但需要 Write Barrier (写屏障) 保证一致性。
    *   **v1.8**: **混合写屏障 (Hybrid Write Barrier)**。结合了插入屏障和删除屏障的优点，极大地缩短了 STW 时间 (通常 < 1ms)。
