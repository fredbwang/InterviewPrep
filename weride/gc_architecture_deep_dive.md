# 垃圾回收 (GC) 核心算法与架构深度解析

本文档整理了常见的 GC 算法类型、分代设计思想以及主流语言 (Java, Go, C#, Python) 的具体实现差异。

---

## 1. 基础 GC 算法主要类型

### 1.1 引用计数 (Reference Counting)
*   **原理**: 每个对象维护一个引用计数器。引用+1时计数器++, 引用失效时计数器--。归零时立即回收。
*   **优点**:
    *   **即时性**: 内存回收是实时的，没有 STW (Stop-The-World) 突刺。
    *   **简单**: 容易实现。
*   **缺点**:
    *   **循环引用**: A -> B, B -> A，导致内存泄漏 (需要引入 WeakRef 或循环检测器)。
    *   **开销**: 每次赋值都要原子操作更新计数 (Atomic Inc/Dec)，多线程下性能损耗大。
*   **代表**: Python, PHP, Swift (ARC)。

### 1.2 标记-清除 (Mark-Sweep)
*   **原理**:
    1.  **Mark**: 从 Root (栈、全局变量) 出发，遍历所有可达对象并打标记。
    2.  **Sweep**: 遍历整个堆，回收未标记对象的内存。
*   **优点**: 解决了循环引用问题。
*   **缺点**:
    *   **内存碎片 (Fragmentation)**: 回收后的内存是不连续的，分配大对象时可能因为没足够连续空间而再次触发 GC。
*   **代表**: Go (三色标记+并发清除), Lua。

### 1.3 标记-压缩 (Mark-Compact) / 标记-整理
*   **原理**:
    1.  **Mark**: 标记过程同上。
    2.  **Compact**: 将所有存活对象向内存一端移动 (Copy)，然后清理掉边界以外的内存。
*   **优点**: 消除内存碎片，分配内存只需移动指针 (Bump Pointer)，极快。
*   **缺点**:
    *   **移动对象**: 需要更新所有引用该对象的指针地址，成本高，通常需要 STW。
*   **代表**: Java (Old Gen), C# (Gen 2)。

### 1.4 复制算法 (Copying)
*   **原理**: 将内存分为两块 (From/To Space)。
    1.  只在 From 空间分配。
    2.  GC 时，将 From 中存活对象全部复制到 To 空间。
    3.  交换 From/To 指针。
*   **优点**: 无碎片，分配快。
*   **缺点**:
    *   **空间浪费**: 内存利用率只有 50% (实际上 Java Survivor 区优化了比例，8:1:1)。
*   **代表**: Java (Young Gen / Survivor), C# (Gen 0/1)。

### 1.5 三色标记法 (Tri-color Marking)
*   **背景**: 为了实现**并发标记 (Concurrent Marking)**，即在 GC 标记期间用户线程 (Mutator) 不停顿。
*   **三个集合**:
    *   **白色 (White)**: 未被访问的对象。GC 结束时如果还是白色，则回收。
    *   **灰色 (Grey)**: 自身已被访问，但其子节点 (引用的对象) 尚未被扫描。作为工作队列。
    *   **黑色 (Black)**: 自身及子节点均已被扫描。安全存活。
*   **流程**:
    1.  初始状态所有对象为白色。
    2.  扫描 Root Set，将直接可达对象标记为灰色。
    3.  从灰色集合取出对象，将其引用的白色对象标为灰色，自身标为黑色。
    4.  重复步骤 3，直到灰色集合为空。
    5.  剩余白色对象即为垃圾。
*   **读写屏障 (Barriers)**:
    *   并发执行时，用户线程可能会破坏图关系 (例如把白色对象挂在黑色对象下，导致白色对象被漏标被误删)。
    *   需要引入 **Dijkstra 插入屏障** (强三色不变性) 或 **Yuasa 删除屏障** (弱三色不变性) 来修正。

---

## 2. 分代垃圾回收 (Generational GC)

*   **核心假设 (Weak Generational Hypothesis)**:
    1.  大多数对象都是朝生夕死的 (很快变得不可达)。
    2.  老年代对象持有新生代对象引用的情况非常少。

### 2.1 架构设计
*   **Young Gen (新生代)**:
    *   对象分配极快，回收频率高。
    *   通常使用 **Copying** 算法 (因为存活率低，复制成本低)。
*   **Old Gen (老年代)**:
    *   存活时间长的对象晋升 (Promotion) 到此。
    *   通常使用 **Mark-Compact** 算法 (因为存活率高，复制成本太高，且不想浪费空间)。
*   **Card Table (卡表) / Remembered Set**:
    *   为了解决“老年代引用新生代”的问题，不需要扫描整个老年代。
    *   只需记录老年代哪一块内存 (Page/Card) 引用了新生代，Minor GC 时只扫描 Card Table 标记为 Dirty 的区域。

---

## 3. 主流语言 GC 架构对比

### 3.1 Java (HotSpot VM)
*   **进化史**:
    *   **Serial**: 单线程，STW 长。
    *   **CMS (Concurrent Mark Sweep)**: 老年代并发标记清除，降低 STW，但有碎片。
    *   **G1 (Garbage First)**:
        *   将堆划分成通过 Region。逻辑分代，物理不分代。
        *   **Mixed GC**: 既回收 Young Region，也回收收益最高的 Old Region。
    *   **ZGC (Z Garbage Collector)**:
        *   **着色指针 (Colored Pointers)**: 指针本身包含元数据。
        *   **读屏障 (Load Barriers)**: 访问对象时检测指针颜色，如果指针指向旧地址，自动修正 (Remap)。
        *   **目标**: 停顿时间 < 10ms (甚至 < 1ms)，支持 TB 级堆。

### 3.2 Go (Golang)
*   **策略**: **非分代 (Non-generational)**，并发的三色标记清除 (Concurrent Tri-color Mark-Sweep)。
*   **为什么不分代?**:
    *   Go 编译器通过 **逃逸分析 (Escape Analysis)** 将大量临时对象分配在**栈 (Stack)** 上，函数返回即释放，无需 GC 介入。
    *   堆上的对象相对较少，分代的收益（Write Barrier 维护开销）不如 Java 明显。
*   **优化**: 极度重视低延迟 (Low Latency)，愿意牺牲吞吐量换取 STW 极短。

### 3.3 C# (.NET CLR)
*   **策略**: **纯粹的分代 GC (Generational)**。
*   **Gen 0/1**: 使用 Copying (实际上是逻辑上的 View，不一定物理移动，由于 C# 支持 Pinning，比较复杂)。几乎无锁。
*   **Gen 2**: 使用 Mark-Compact。会触发较长时间 STW。
*   **LOH (Large Object Heap)**: 
    *   大于 85,000 字节的对象。
    *   使用 Mark-Sweep (为了避免移动大块内存的巨大开销)。
    *   从 .NET Core 3.0 开始支持 LOH 压缩 (Compact)。

### 3.4 Python (CPython)
*   **主策略**: **引用计数 (Reference Counting)**。
*   **辅助策略**: **分代循环垃圾回收器 (Generational Cyclic GC)**。
    *   维护 3 是链表 (Generation 0, 1, 2)。
    *   当 `allocation_count - deallocation_count > threshold` 时，触发标记-清除算入，专门检测并断开循环引用。

---

## 4. STW (Stop-The-World) 解决与优化方案

### 4.1 并发标记 (Concurrent Marking)
*   **原理**: 将最耗时的“标记”阶段这并发运行 (与用户线程 Mutator 一般跑)。
*   **难点**: 用户线程修改对象图，导致标记错误 (多标或漏标)。
*   **解法**: 引入**三色标记法** + **写屏障 (Write Barrier)**。
*   **代表**: CMS, G1, Go GC, ZGC。

### 4.2 增量式 GC (Incremental GC)
*   **原理**: 将整个 GC 过程切分成许多微小的时间片 (Slice)。每次分配内存时稍微做一点 GC 工作，然后暂停，交还 CPU 给用户。
*   **优点**: 将长 STW 打散成肉眼不可见的微型停顿。
*   **代表**: Lua 5.1+, Python (部分), Node.js (V8 Scavenger)。

### 4.3 读/写屏障 (Barriers) - 必考细节
*   目的是在并发/增量过程中维持数据一致性。
*   **写屏障 (Write Barrier) - SATB vs IU**:
    *   **SATB (Snapshot At The Beginning - G1)**: 当引用关系 `A.field = B` 被删除时，记录下旧引用 B。保证 GC 开始时的“快照”里活的对象都被扫到。**关注结束引用**。
    *   **Incremental Update (CMS)**: 当引用关系 `A.field = B` 插入时，将 A 重新标灰 (即使它原本均黑)。**关注新增引用**。
    *   **Hybrid Write Barrier (Go)**: 结合两者优点，最大化减少需要重扫的栈空间。
*   **读屏障 (Load Barrier - ZGC)**:
    *   当用户线程从堆里 *读取* 引用时，检查该指针是否指向了已移动/回收的对象。如果是，立马进行**重定位 (Remap)** 修正指针。这也是 ZGC 能并发移动对象的关键。

### 4.4 语言与应用层优化
*   **逃逸分析 (Escape Analysis)**:
    *   编译器优化。如果对象只在函数内部使用，直接分配在 **Stack** 上。
    *   **效果**: 栈对象随函数返回自动销毁，完全不给 GC 增加压力 (Go 做的最好)。
*   **对象池 (Object Pooling)**:
    *   复用对象，减少 `new` 和 GC 频率。
    *   例如 Go `sync.Pool`, Java `ThreadLocal`, Netty `Recycler`.
*   **堆外内存 (Off-Heap Memory)**:
    *   Java `DirectByteBuffer`。使用 `Unsafe.allocateMemory` 分配。
    *   完全绕过 GC，需要手动 `free`。适用于网络缓冲区。

---

## 5. 其他高级优化方向 (Advanced Optimizations)

### 5.1 指针压缩 (Compressed Oops)
*   **场景**: 在 64 位系统上，指针占用 8 字节，相比 32 位系统 (4 字节) 内存占用膨胀，且降低了 CPU 缓存命中率。
*   **原理**: 
    *   如果堆内存 < 32GB，JVM 可以使用 4 字节的相对偏移量 (Offset) 来表示指针。
    *   `Address = Base + (Offset << 3)`。因为 Java 对象按 8 字节对齐，后 3 位永远是 0，所以可以左移 3 位。即便 Offset 只有 32 位，也能寻址 $2^{32} * 8 = 32GB$ 空间。
*   **收益**: 节省内存，提高带宽利用率。

### 5.2 字符串去重 String Deduplication
*   **场景**: 内存中往往存在大量内容相同的 String 对象 (如 HTTP Header, JSON Key)。
*   **G1 实现**: 
    *   在 GC 期间，检查 String 的 `char[]` 数组内容。如果发现重复，让多个 String 对象指向同一个 `char[]` 数组。
    *   *注意*: 这不同于 String 常量池 (`intern()`)。这是在 Runtime 自动发生的。

### 5.3 线程局部分配缓存 (TLAB - Thread Local Allocation Buffer)
*   **问题**: 多线程并发分配堆内存时，需要竞争锁 (Bump Pointer 也是临界资源)。
*   **优化**:
    *   每个线程在 Eden 区预先申请一小块**专属**内存 (TLAB)。
    *   分配对象时，直接在自己的 TLAB 里分配，**完全无锁**，速度堪比 C 语言栈分配。
    *   只有 TLAB 满了需要扩容时，才需要加锁申请新的 TLAB。

### 5.4 区域化与内存布局优化 (Region & Layout)
*   **Region-based (G1/Shenandoah)**: 将堆切碎。不再坚持连续的 One Big Heap。允许灵活回收性价比最高的 Region。
*   **NUMA-Aware (G1/ZGC)**: 感知非统一内存访问架构。倾向于将对象分配在当前 CPU 核心绑定的本地内存条上，减少跨 Socket 访问延迟。
