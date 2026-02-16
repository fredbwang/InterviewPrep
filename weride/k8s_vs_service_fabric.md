# Kubernetes vs Service Fabric: 深度架构对比

本文档从分布式系统核心机制的角度，详细对比 **Kubernetes (K8s)** 与 **Azure Service Fabric (SF)** 的实现差异。

---

## 1. Service Discovery (服务发现)

### Kubernetes (K8s)
*   **基于 DNS 与 VIP (Virtual IP)**: K8s 的服务发现主要依赖 **CoreDNS** 和 **Service** 资源。
*   **机制**:
    *   每个 Service 分配一个 ClusterIP (VIP)。
    *   Pod 内的 DNS 解析 Service Name (e.g., `my-service.namsspace`) 到 ClusterIP。
    *   **Kube-Proxy** (iptables/IPVS) 将 ClusterIP 流量负载均衡到后端的 Pod IP。
*   **应用层**: 无需感知具体实例地址，对应用透明。

### Service Fabric (SF)
*   **基于 Naming Service (命名服务)**: SF 拥有一个强一致性的系统服务名叫 **Naming Service**。
*   **机制**:
    *   客户端 (Client) 或服务间通信时，必须先查询 Naming Service。
    *   解析 `fabric:/MyApp/MyService` URI，获取该服务的分区 (Partition) 和副本 (Replica) 的**物理地址 (IP:Port)**。
    *   **Smart Client**: SDK 会缓存这些地址，当连接失败时重新解析 (Re-resolve)。
*   **反向代理 (Reverse Proxy)**: SF 节点上运行的反向代理也可以处理 HTTP 请求转发，自动查询 Naming Service。

---

## 2. Configuration Sharing (配置共享)

### Kubernetes (K8s)
*   **ConfigMap & Secrets**:
    *   配置与代码分离，作为资源对象存储在 Etcd 中。
    *   **注入方式**: 环境变量 (Environment Variables) 或 挂载卷 (Volume Mounts)。
*   **动态更新**:
    *   如果挂载为 Volume，文件内容即时更新 (kubelet 定时 sync)。
    *   应用通常需要 Watch start/restart 才能生效 (或者应用内部实现 File Watcher)。

### Service Fabric (SF)
*   **Config Package (Settings.xml)**:
    *   配置是服务包 (Service Package) 的一部分，包含在 `Config` 目录中。
*   **版本控制与升级**:
    *   配置更新被视为一次**部署升级 (Upgrade)**。SF 引擎会滚动升级 (Rolling Upgrade) 服务实例。
    *   **事件通知**: 服务代码通过 `CodePackageActivationContext` 注册 `ConfigurationPackageModifiedEvent` 事件，**原生支持热更新**，无需重启进程。

---

## 3. Failure Detection (故障检测)

### Kubernetes (K8s)
*   **星型心跳机制 (Star Topology Heartbeats)**:
    *   **Node ↔ API Server**: Kubelet 每 10s (默认 `node-status-update-frequency`) 发送心跳 (NodeLease 对象)。
    *   **Controller Manager**: 如果超过 `node-monitor-grace-period` (40s) 没有收到心跳，判定节点 Unknown，随后触发 Pod 驱逐 (`pod-eviction-timeout`, 默认 5m)。
    *   *缺点*: 依赖中心化的 API Server，集群规模大时 API Server 压力巨大，且判定延迟较长 (分钟级)。
*   **应用级检测 (Probes)**:
    *   依赖 Kubelet 本地执行 Liveness/Readiness/Startup Probes。
    *   **二元状态**: 只有 Success/Failure。缺乏"疑似故障"的灰度判断。

### Service Fabric (SF)
*   **P2P 租约环机制 (Ring Topology Leases)**:
    *   **分布式检测**: 不仅依赖中心，**节点之间 (Neighbors)** 互相维持 TCP 连接并发送高频 Lease (默认 < 1s)。
    *   **Lease 行为**: 一旦相邻节点 ACK 超时，立即上报，判定非常敏锐 (毫秒级失效检测)。
*   **Arbitration (仲裁机制)**:
    *   当故障发生 (如网络分区)，SF 会进行**仲裁**来决定哪个节点应该“自杀”以保护集群一致性 (基于 Seed Nodes 多数派)。
    *   防止“脑裂” (Split-brain) 的核心手段。
*   **健康报告聚合 (Health Model)**:
    *   并非简单的 Up/Down。具有 **Ok / Warning / Error** 三级状态。
    *   支持**TTL**: 如果组件没有在规定时间内上报“我很健康”，自动转为 Error (Watchdog 模式)。

---

## 4. Leader Election (领导者选举)

### Kubernetes (K8s)
*   **Control Plane**: Etcd 集群内部使用 **Raft** 协议选举 Leader。
*   **User Application**:
    *   K8s **本身不为**应用容器提供内置的 Leader Election。
    *   **Sidecar/SDK 模式**: 应用通常使用 `client-go` 的 `Leaderelection` 库，基于 Etcd 的资源锁 (Lease/ConfigMap) 争抢锁来实现。谁抢到锁谁是 Leader。

### Service Fabric (SF)
*   **First-Class Citizen (一等公民)**: SF 专为有状态服务 (Stateful Services) 设计。
*   **自动选举**:
    *   每个 Stateful Service Partition 自动维护一个 Replica Set (副本集)。
    *   SF 系统服务 (**Failover Manager**) 负责在副本集中指定一个 **Primary** (Leader) 和多个 **ActiveSecondaries**。
    *   当 Primary 挂掉，SF 瞬间提升一个 Secondary 为 Primary。**无需应用代码干预**。

---

## 5. Consensus (共识算法)

### Kubernetes (K8s)
*   **Etcd (Raft)**: K8s 的所有集群状态 (State) 存储在 Etcd 中，依赖 Raft 保证一致性。
*   **应用层**: K8s 不管应用的共识。如果应用需要共识，需自己部署 ZooKeeper/Etcd 或是使用 StatefulSet + Headless Service 组建集群。

### Service Fabric (SF)
*   **Replicator (复制器)**:
    *   每个 Stateful Service 实例内部都有一个 Replicator 组件。
    *   使用类 Paxos/Multi-Paxos 或 PacificA 协议。
    *   **流程**: 写操作 -> Primary -> 并行发送给 Secondaries -> 收到 Quorum (多数派) 确认 -> Commit -> Apply State。
    *   **Reliable Collections**: SF 提供了 `IReliableDictionary` / `IReliableQueue`，这些数据结构的**底层自动实现了共识与复制**。开发人员像使用本地 HashMap 一样使用，但数据是分布式强一致的。

---

## 6. Disaster Recovery (容灾)

### Kubernetes (K8s)
*   **Stateless 哲学**: 推荐无状态应用。节点挂了，在其他节点重起 Pod。
*   **数据备份**: 依赖外部存储 (PVC/Cloud Disk) 的快照能力，或者工具如 **Velero** 备份 Etcd 数据和 PV 数据。
*   **多集群**: 联邦 (Federation) 或 GitOps 部署到多个集群。

### Service Fabric (SF)
*   **Backup & Restore Service**: 内置服务，定期对 Reliable State (有状态服务的数据) 进行增量/全量备份到外部存储 (Blob Storage/File Share)。
*   **Fault Analysis Service (Chaos Monkey)**:
    *   SF 内置了混沌工程服务。可以编排场景 (比如随机重启节点、网络分区、代码包重启) 来测试系统的容灾恢复能力。
*   **Geo-Distribution**: 单个 SF 集群本身就可以跨可用区 (AZ) 甚至跨 Region 部署 (虽然会有延迟挑战)，其故障域 (Fault Domain) 和更新域 (Upgrade Domain) 模型能感知物理拓扑，智能分散副本。
