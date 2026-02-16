# Java 并发与算法面试必备 (Concurrency & Algorithmic Interview)

## 1. Java 并发编程概述 (Java Concurrency)

### 核心概念
*   **线程安全 (Thread Safety)**: 当多个线程访问一个类时，如果不用考虑这些线程在运行时环境下的调度和交替执行，并且不需要额外的同步，这个类都能表现出正确的行为，那么这个类就是线程安全的。
*   **JMM (Java Memory Model)**: 
    *   **可见性 (Visibility)**: 一个线程修改了共享变量，其他线程能立即看到 (`volatile`).
    *   **原子性 (Atomicity)**: 一个操作不可被中断 (`synchronized`, `Lock`, `AtomicInteger`).
    *   **有序性 (Ordering)**: 禁止指令重排序 (`volatile`, `Happen-Before`).
*   **锁机制**: 
    *   `synchronized`: 内置锁，自动释放，不可中断。
    *   `ReentrantLock`: 显式锁，灵活 (tryLock, lockInterruptibly)，需手动释放。
    *   `ReadWriteLock`: 读写分离，提升读多写少场景的性能。

---

## 2. 多线程 i++ 问题与解决方案

### 问题: 非原子操作 (Non-Atomic Operation)
`i++` 实际上包含三个步骤: `Read i` -> `Modify (i+1)` -> `Write i`。多线程并发执行时，可能发生从主存读到旧值的情况，导致多次 `++` 只加了 1 次 (丢失更新)。

#### 错误示例 (线程不安全)
```java
public class UnsafeCounter {
    private int count = 0;

    public void increment() {
        count++; // 非原子操作，存在竞态条件
    }

    public int getCount() {
        return count;
    }
}
```

### 解决方案 (Thread-Safe Solutions)

#### 方案 A: 使用 AtomicInteger (推荐 - CAS 乐观锁)
利用 CPU 提供的 CAS (Compare-And-Swap) 指令，无锁实现，性能高。

```java
import java.util.concurrent.atomic.AtomicInteger;

public class SafeCounterAtomic {
    private AtomicInteger count = new AtomicInteger(0);

    public void increment() {
        count.incrementAndGet(); // 原子操作
    }

    public int getCount() {
        return count.get();
    }
}
```

#### 方案 B: 使用 synchronized (互斥锁)
确保同一时刻只有一个线程能执行 `increment`。

```java
public class SafeCounterSync {
    private int count = 0;

    public synchronized void increment() {
        count++;
    }

    public synchronized int getCount() {
        return count;
    }
}
```

#### 方案 C: 使用 LongAdder (高并发推荐)
在极高并发下 (`AtomicInteger` CAS 失败率高时)，`LongAdder` 通过分散热点 (Cell 数组) 减少竞争，吞吐量更高。

```java
import java.util.concurrent.atomic.LongAdder;

public class SafeCounterAdder {
    private LongAdder count = new LongAdder();

    public void increment() {
        count.increment();
    }

    public long getCount() { // sum() 操作可能较慢，但 increment 极快
        return count.sum();
    }
}
```

---

## 3. 算法部分 (Algorithms)

### 3.1 矩阵乘法 (Matrix Multiplication)
两个矩阵 A ($m \times n$) 和 B ($n \times p$) 相乘，结果 C 是 ($m \times p$)。
公式: $C_{ij} = \sum_{k=1}^{n} A_{ik} \times B_{kj}$

```java
public class MatrixMult {
    public static int[][] multiply(int[][] A, int[][] B) {
        int m = A.length;
        int n = A[0].length;
        int p = B[0].length;
        int[][] C = new int[m][p];

        for (int i = 0; i < m; i++) {
            for (int j = 0; j < p; j++) {
                for (int k = 0; k < n; k++) {
                    C[i][j] += A[i][k] * B[k][j];
                }
            }
        }
        return C;
    }
}
```

### 3.2 快速幂 (Fast Exponentiation)
计算 $x^n$，时间复杂度由 $O(n)$ 降为 $O(\log n)$。
原理: $x^{10} = (x^5)^2$。二进制拆分: $10 = (1010)_2 \Rightarrow x^{10} = x^8 \cdot x^2$。

```java
public class FastPow {
    public static long power(long base, long exp) {
        long res = 1;
        while (exp > 0) {
            if ((exp & 1) == 1) { // 如果末位是1
                res *= base;
            }
            base *= base; // 底数翻倍: x^1 -> x^2 -> x^4 -> x^8
            exp >>= 1;    // 指数右移
        }
        return res;
    }
}
```

### 3.3 斐波那契数列 (矩阵快速幂解法)
斐波那契数列: $F(n) = F(n-1) + F(n-2)$。
这就相当于矩阵递推:
$$
\begin{bmatrix} F(n+1) \\ F(n) \end{bmatrix} = \begin{bmatrix} 1 & 1 \\ 1 & 0 \end{bmatrix} \times \begin{bmatrix} F(n) \\ F(n-1) \end{bmatrix}
$$
推导 N 次可得:
$$
\begin{bmatrix} F(n+1) \\ F(n) \end{bmatrix} = \begin{bmatrix} 1 & 1 \\ 1 & 0 \end{bmatrix}^n \times \begin{bmatrix} F(1) \\ F(0) \end{bmatrix}
$$
时间复杂度: $O(\log n)$。

```java
public class FibonacciMatrix {
    // 2x2 矩阵乘法
    private static long[][] multiply(long[][] A, long[][] B) {
        long[][] C = new long[2][2];
        for (int i = 0; i < 2; i++) {
            for (int j = 0; j < 2; j++) {
                for (int k = 0; k < 2; k++) {
                    C[i][j] += A[i][k] * B[k][j];
                }
            }
        }
        return C;
    }

    // 矩阵快速幂
    private static long[][] matrixPow(long[][] A, int n) {
        long[][] res = {{1, 0}, {0, 1}}; // 单位矩阵 I
        while (n > 0) {
            if ((n & 1) == 1) res = multiply(res, A);
            A = multiply(A, A);
            n >>= 1;
        }
        return res;
    }

    public static long fib(int n) {
        if (n <= 0) return 0;
        if (n == 1) return 1;

        long[][] base = {{1, 1}, {1, 0}};
        // 计算 base^(n-1)
        long[][] res = matrixPow(base, n - 1);
        
        // F(n) = res[0][0]*F(1) + res[0][1]*F(0)
        // F(1)=1, F(0)=0  =>  F(n) = res[0][0]
        return res[0][0];
    }
    
    public static void main(String[] args) {
        System.out.println(fib(10)); // 55
    }
}
```
