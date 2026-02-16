# 存储深度挖掘与复习 (Redis/MySQL) - Alibaba 面试

针对阿里云 MQ 存储团队面试，侧重于底层实现、性能优化以及一致性保证。

---

## 1. Redis 深度挖掘

### 1.1 数据结构底层 (SDS & ZipList -> QuickList -> ListPack) (重要更新)
*   **SDS (Simple Dynamic String)**:
    *   结构: `len`, `alloc`, `flags`, `buf`。不仅仅是 char*。
    *   优势: O(1) 取长度，二进制安全 (buf中间可有\0)，自动扩容预分配 (减少 `realloc` 次数)。
*   **ZipList (压缩列表 - 已逐步淘汰)**:
    *   连续内存块，存储 entry。每个元素包含 encoding, prevlen。
    *   **连锁更新 (Cascade Update)**: 插入导致 prevlen 变大，进而影响所有后续 entry 的 prevlen，极其耗时。
*   **ListPack (紧凑列表 - Redis 7.0+)**:
    *   解决连锁更新。每个 entry 只有当前长度 `element-tot-len`，不依赖前一个。
*   **Hash/Set/ZSet 转换**:
    *   数据少时用 ListPack/ZipList (省内存，利用 CPU 缓存)。
    *   数据多时转为 Dict (HT) 或 SkipList。

### 1.2 跳表 (SkipList) - ZSet 实现
*   **核心**: 也就是带多级索引的链表。
*   **插入过程**: 生成随机层数 (概率 1/4, 1/2)，如果层数 > 当前最大层，更新 head。
*   **对比红黑树 (RBT)**:
    *   RBT 插入/删除需要旋转/变色，并发支持差 (锁整个树)。
    *   SkipList 只改局部指针，容易无锁化 (CAS)。且范围查询效率极高 (ZRANGE)。
*   *面试陷阱*: 为何不用 B+ 树？因为 Redis 是内存型，没有磁盘 IO 瓶颈，SkipList 更简单且同样 O(logN)。

### 1.3 Redis Cluster (分布式)
*   **Slot (槽位)**: 16384 个。`CRC16(key) % 16384`。
*   **Gossip 协议**: 节点间交换状态 (PING, PONG, MEET, FAIL)。最终一致。
*   **ASK 重定向**: 
    1.  Client 请求 Key。
    2.  Server 发现 Slot 正在做 **Resharding (迁移)**。
    3.  Server 返回 ASK (临时重定向)。Client 再请求目标节点。
    4.  **MOVED**: 永久重定向 (Slot 已经完全迁移过去了)。

### 1.4 缓存异常 (Cache Patterns)
*   **穿透 (Penetration)**: 查询不存在的数据。直接打 DB。
    *   解法: BloomFilter, 空对象缓存 (TTL 短)。
*   **击穿 (Breakdown)**: 热点 Key 过期，并发量巨大，瞬间打 DB。
    *   解法: Mutex 锁 (Only one thread fetches DB), 逻辑过期 (Soft TTL)。
*   **雪崩 (Avalanche)**: 大批 Key 同时过期 / Redis 宕机。
    *   解法: 过期时间加随机值 (Jitter), Hystrix 熔断降级.

### 1.5 线程模型与 IO 多路复用 (为何单线程还快?)
*   **IO 多路复用 (IO Multiplexing)**:
    *   **核心**: 单个线程监视多个文件描述符 (FD) 的可读/可写状态。一旦这就绪，就通知程序进行读写操作。
    *   **实现**: `select`, `poll`, `epoll` (Linux), `kqueue` (BSD)。Redis 封装了 `ae.c` 库，根据 OS 自动选择最优方案 (首选 `epoll`)。
    *   **Epoll 优势**:
        *   **无 FD 上限**: 不受 1024 限制 (select)。
        *   **无轮询**: 只返回就绪的 FD 链表，不用全量遍历 (poll/select)。
        *   **内存拷贝少**: 内核与用户空间共享内存 (mmap)。
*   **Reactor 模式**:
    *   **文件事件 (File Event)**: 对应 Socket 读写。
    *   **时间事件 (Time Event)**: 对应周期性任务 (serverCron)。
*   **为何单线程快?**:
    *   1. 纯内存操作 (Bottleneck is Memory/Network, not CPU)。
    *   2. 非阻塞 IO (Non-blocking IO)。
    *   3. 避免了多线程上下文切换 (Context Switch) 和竞争条件 (Race Condition)。
*   **Redis 6.0 多线程**:
    *   **仅用于网络 IO (读写 Socket)**: 解包/封包是 CPU 密集型。
    *   **命令执行** 依然是单线程 (原子性保证)。

---

## 2. MySQL (InnoDB) 深度挖掘

### 2.1 索引与存储结构 (B+ Tree)
*   **B+ 树优势**:
    *   **扇出高 (Fan-out)**: 一页 16KB，如果主键 bigint (8B) + 指针 (6B)，一页能存 ~1170 个。3层树高可存 1170^3 ≈ 16亿行。**IO 次数少**。
    *   **范围查询**: 叶子节点是双向链表，顺着走即可，极大优化 HDD 磁头移动。
*   **聚簇索引 (Clustered Index)**: 数据本身存在主键索引的叶子上。
*   **二级索引 (Secondary Index)**: 叶子存的是主键 ID。需要 **回表 (Look Up)**。
    *   **覆盖索引 (Covering Index)**: Select 的字段全在二级索引里，**无需回表**。

### 2.2 事务隔离深度解析 (RR & Phantom Read)
*   **MVCC (Multi-Version Concurrency Control)**:
    *   **Hidden Columns**: `DB_TRX_ID` (事务ID), `DB_ROLL_PTR` (回滚指针), `DB_ROW_ID`。
    *   **ReadView (一致性视图)**: `m_ids` (活跃事务列表), `min_trx_id`, `max_trx_id`。
    *   **可见性规则**: 小于 min 可见，大于 max 不可见，在 m_ids 里不可见 (活跃未提交)，不在 m_ids 里可见 (已提交)。
*   **幻读 (Phantom Read) 彻底解决了吗？**:
    *   **快照读 (Snapshot Read)**: 普通 Select。靠 MVCC 解决。
    *   **当前读 (Current Read)**: Select ... For Update。靠 **Next-Key Lock** (Gap Lock + Record Lock) 解决。锁住间隙，禁止插入。
    *   *特例*: 原本不存在的记录，如果要 Update 它，会变成当前读，可能产生幻读。

### 2.3 Buffer Pool 与 Double Write
*   **Buffer Pool**: 内存缓冲池，减少磁盘 IO。数据按页管理 (LRU 链表: 冷热分离)。
*   **Change Buffer (写缓冲)**: 针对**二级索引**的插入/修改。如果页不在内存，先记在缓存，后续 merge。避免随机读磁盘加载页。
*   **Double Write Buffer (双写缓冲) - 极其重要**:
    *   **Partial Page Write (页断裂)**: OS 页 4KB，MySQL 页 16KB。如果写了一半断电，页损坏。Redo Log 基于物理页，如果页坏了，Redo 无法恢复。
    *   **流程**: Dirty Page -> memcpy 到 DWB 内存 -> 顺序写 DWB 磁盘 (2MB) -> fsync -> 离散写数据文件 (.ibd)。
    *   *恢复*: 启动时检查 DWB，如果发现页断裂，用 DWB 里的完好副本覆盖，再重放 Redo Log。

---

## 3. 分布式共识与锁 (Advanced)

### 3.1 Redis 分布式锁 -> Redlock
*   **setnx (set if not exists)**: `SET key uuid NX PX 30000`。
*   **续期 (Watch Dog)**: Redisson 实现。独立线程每隔 10s 检查，如果持有锁还未完成，重置过期时间。
*   **Redlock (红锁)**:
    *   为了解决 Redis 单点/主从异步导致的锁丢失问题。
    *   向 N (通常 5) 个独立的 Master 节点顺序申请锁。
    *   如果 >= N/2+1 个节点成功，且耗时 < 总时间，才算加锁成功。
    *   *争议*: 依赖时钟同步 (Clock Drift)。如果发生 GC Pause 或时钟跳变，依然不安全。Martin Kleppmann 曾撰文批判。

### 3.2 MySQL 分布式锁 (排他锁)
*   `GET_LOCK(str, timeout)`: 简单，session 级别。
*   **For Update**: `Select * from lock_table where id=1 for update`。强依赖 DB 性能，并发极低。仅适用于小规模任务调度。
