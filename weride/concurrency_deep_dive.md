# 高并发与语言机制 (Java & Go) 深度挖掘 - Alibaba 面试

针对阿里云 MQ 基础架构团队面试，侧重于多线程模型、内存管理、调度器实现及两种语言的差异。

---

## 1. Java 并发编程深度 (Java Multi-threading)

### 1.1 Java 内存模型 (JMM - Java Memory Model)
*   **Happen-Before 原则**: 
    1.  **程序顺序 (Sequential Consistency)**: 单线程内，前面操作可见于后面。
    2.  **Monitor (锁)**: `unlock` 可见于后续 `lock`。
    3.  **Volatile**: 写可见于读。禁止指令重排序 (Memory Barrier)。
    4.  **Start/Join**: `Thread.start()` 对线程内可见，`Thread.join()` 返回后线程内操作可见。
*   **Volatile 实现 (CPU 层面)**:
    *   **Lock prefix instruction**: 汇编 `lock addl`。
    *   锁定 Cache Line，并使其失效 (MESI 协议缓存一致性)。其他 CPU 核心必须从主存重新加载。
    *   **内存屏障 (LoadLoad/StoreStore...)**: 禁止重排。

### 1.2 锁机制 (Synchronized vs ReentrantLock)
*   **Synchronized (JVM 内置)**:
    *   **对象头 (Mark Word)**: 存储 HashCode, GC Age, 锁状态 (偏向锁 -> 轻量级锁 -> 重量级锁)。
    *   **升级过程**:
        1.  **偏向锁 (Biased)**: 单线程重复获取，无竞争，只改 ThreadID。
        2.  **轻量级锁 (Lightweight)**: 交替执行，CAS 自旋 (Spin Lock) 修改 `Lock Record` 指针。
        3.  **重量级锁 (Heavyweight)**: 竞争激烈，CAS 失败多次。膨胀为 `ObjectMonitor`，阻塞线程 (OS Mutex)，发生上下文切换。
*   **ReentrantLock (AQS - AbstractQueuedSynchronizer)**:
    *   **State**: `volatile int state` (0: 无锁, >0: 持有次数)。
    *   **CLH 队列 (Craig, Landin, and Hagersten)**: 双向链表，FIFO 等待队列。
    *   **公平锁 (Fair)**: 严格排队。**非公平锁 (Nonfair)**: 新线程先尝试插队 CAS，失败再入队 (吞吐量高，Redis/Kafka 多用非公平)。
    *   **Condition**: `await/signal` 实现多等待队列，精确唤醒。

### 1.3 线程池 (ThreadPoolExecutor)
*   **核心参数**: `corePoolSize`, `maximumPoolSize`, `keepAliveTime`, `workQueue` (Array/LinkedBlockingQueue), `handler` (拒绝策略)。
*   **执行流程**:
    1.  如果当前线程数 < core，创建新线程 (Worker)。
    2.  如果 >= core，放入 workQueue。
    3.  如果 workQueue 满，且 < max，创建非核心线程。
    4.  如果 >= max，触发拒绝策略 (Abort/Discard/CallerRuns)。
*   **Worker**: 实现了 `Runnable`，循环从 Queue `take()` 任务执行。

---

## 2. Go 语言并发与调度 (Goroutine Scheduler)

### 2.1 GMP 模型深度解析
*   **G (Goroutine)**: 用户态线程，包含 Stack (初始 2KB，最大 1GB)，PC (程序计数器)，状态 (Running/Runnable/Waiting)。
*   **M (Machine)**: OS 线程 (Kernel Thread)。真正执行代码的实体。默认 `GOMAXPROCS` (CPU 核数)。
*   **P (Processor)**: 逻辑处理器/调度上下文。拥有本地运行队列 (Local Run Queue)。
    *   *相比 GM 模型 (无 P)*: P 解决了全局锁竞争太大的问题 (Global Run Queue)。
*   **调度策略**:
    *   **Work Stealing (工作窃取)**: P 的 Local Queue 空了，随机从其他 P **偷一半** G 过来执行。保证负载均衡。
    *   **Hand Off (切换)**: 当 M 执行系统调用 (Syscall) 阻塞时，P 会带着剩下的 G 队列与 M 分离 (Release)，去寻找空闲的 M 或新建 M 继续执行。
    *   **抢占式调度 (Preemption)**: Go 1.14+ 引入基于信号的异步抢占。如果 G 运行超 10ms，发送 SIGURG 信号强制挂起，防止死循环饿死其他 G。

### 2.2 Go 内存管理与 GC (Garbage Collection)
*   **TCMalloc (Thread-Caching Malloc)**:
    *   每层缓存: **mcache** (P 本地缓存，无锁) -> **mcentral** (全局中心缓存，有锁) -> **mheap** (堆，向 OS 申请)。
    *   对象分配: 微对象 (Tiny, <16B), 小对象 (Small, <32KB), 大对象 (Large, >32KB)。小对象直接从 mcache 的 span 中分配，极快。
*   **GC 演进**:
    *   **v1.5 三色标记法**: 
        *   **白色**: 未访问。**灰色**: 已访问但子节点未访问。**黑色**: 已访问且子节点已访问。
        *   **STW (Stop The World)**: 极短。
        *   **写屏障 (Write Barrier)**: 防止黑色对象引用白色对象 (如果不加屏障，会导致白色对象被误回收)。
    *   **v1.8 混合写屏障 (Hybrid Write Barrier)**:
        *   结合了插入屏障 (Dijkstra) 和删除屏障 (Yuasa)。
        *   **核心**: 在 GC 开始时，栈上对象全部标黑 (无需扫描栈)。后续并未对栈启用屏障，只对堆启用。**消除了重扫描栈的 STW**。
    *   **Pacing (调优)**: `GOGC=100`。当堆内存增长到上次 GC 后的 2 倍时触发。

### 2.3 Channel 底层实现
*   **结构**: `hchan`。
    *   `qcount`: 元素个数。
    *   `buf`: 循环数组 (Ring Buffer)，存数据。
    *   `sendx/recvx`: 发送/接收索引。
    *   `recvq/sendq`: 等待读/写的 G 队列 (Sudog 链表)。
    *   `lock`: 互斥锁 (Mutex)。**Channel 操作是有锁的!** (不完全是无锁)。
*   **流程**:
    *   **写**: 
        1.  如果有等待读的 G (recvq)，直接把数据 copy 给 G，唤醒 G (无需入 buf)。
        2.  如果有 buf 空间，写入 buf。
        3.  如果 buf 满，当前 G 挂起 (gopark)，放入 sendq，解锁。
    *   **读**:
        1.  如果有等待写的 G (sendq)，且 buf 满: 从 buf 读头，把 sendq 头的数据 copy 到 buf 尾，唤醒写 G。
        2.  如果有 buf 数据，读 buf。
        3.  如果 buf 空，挂起 G，放入 recvq。

---

## 3. C# 语言并发与机制 (Advanced)

### 3.1 异步编程模型 (Async/Await State Machine)
*   **状态机 (State Machine)**:
    *   C# 的 `async/await` 是**编译器语法糖**。编译器会将 async 方法转换成一个实现了 `IAsyncStateMachine` 接口的 struct。
    *   **MoveNext()**: 当 `await` 的任务未完成时，当前上下文 (Context) 被捕获，状态机记录当前位置并返回。当任务完成，回调触发 `MoveNext()`，从上次的断点继续执行。
    *   **上下文切换**: 相比 Java 线程阻塞，C# 的 await **不阻塞线程**，只是暂时释放当前线程去处理其他任务 (IO Completion Port)。
*   **SynchronizationContext**:
    *   控制 await 之后的代码在哪个线程执行。UI 线程 (WinForms/WPF) 会回到 UI 线程，ASP.NET Core (默认无) 则在线程池随机线程。

### 3.2 线程池与任务并行库 (TPL - Task Parallel Library)
*   **Task vs Thread**:
    *   `Thread`: OS 内核线程 (1:1 模型)，开销大 (~1MB 栈)。
    *   `Task`: 这里的 Task 类似于轻量级对象，由 **Global Queue** 和 **Local Queue** 组成。
*   **Work Stealing (工作窃取)**:
    *   .NET CLR 线程池每个线程有自己的 Local Queue (LIFO, 优化缓存)。
    *   当本地队列空时，从全局队列或者其他线程的队列尾部 **Steal** (FIFO) 任务。这也与 Go 的 GMP 调度策略类似。

### 3.3 垃圾回收 (GC) - 分代与并发
*   **分代回收 (Generational GC)**:
    *   **Gen 0**: 新对象。频繁回收 (类似 Minor GC)。
    *   **Gen 1**: 缓冲区。
    *   **Gen 2**: 长生命周期对象 (类似 Old Gen)。
    *   **LOH (Large Object Heap)**: >85KB 对象直接分配在此，为了避免内存拷贝，默认不压缩 (仅在 Full GC 或明确配置时压缩)。
*   **模式**:
    *   **Workstation GC**: 针对客户端，响应优先。
    *   **Server GC**: 针对服务端。每个 CPU 核心一个 Heap 和 GC 线程，并行回收，吞吐量极高。
*   **Pinned Object**:
    *   为了与非托管代码 (C++) 交互，C# 支持 `fixed` 关键字固定对象地址，防止 GC 移动。

---

## 4. Java vs Go vs C# 并发模型对比 (必考)

| 特性 | Java (Thread) | Go (Goroutine) | C# (Task/Async) |
| :--- | :--- | :--- | :--- |
| **映射关系** | 1:1 (OS Thread) | M:N (Green Thread) | M:N (逻辑上的 Task 映射到 ThreadPool) |
| **核心机制** | 线程阻塞 + 上下文切换 | 协程挂起 + 用户态调度 | 状态机重入 (Callback) + IO 完成端口 |
| **内存占用** | ~1MB (主要) | ~2KB (极小) | Task 对象小, 但 underlying 仍由 OS 线程驱动 |
| **调度策略** | OS 抢占式调度 | GMP 协作/抢占式调度 | 线程池 Work Stealing |
| **GC 特性** | 分代 (G1/ZGC) | 三色标记 (非分代, 低延迟) | 分代 (Gen0/1/2) + LOH (大对象堆) |
| **优势** | 强内存模型, 稳定, 生态最强 | 极高并发, 开发快, 无锁编程 | 语法糖最优雅 (Async/Await), 泛型真泛型 |
