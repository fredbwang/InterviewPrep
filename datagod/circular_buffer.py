class MyCircularQueue:
    def __init__(self, k: int):
        """初始化固定大小的循环队列"""
        self.queue = [0] * k  # 初始化数组
        self.capacity = k     # 队列容量
        self.size = 0         # 当前队列元素个数
        self.head = 0         # 头指针（指向当前头部元素）
        self.tail = 0         # 尾指针（指向下一个插入位置）

    def enQueue(self, value: int) -> bool:
        """向队列尾部插入元素"""
        if self.isFull():
            return False
        self.queue[self.tail] = value
        self.tail = (self.tail + 1) % self.capacity  # 处理循环
        self.size += 1
        return True

    def deQueue(self) -> bool:
        """从队列头部移除元素"""
        if self.isEmpty():
            return False
        self.queue[self.head] = 0  # **修正点**: 逻辑上清空该位置（可选）
        self.head = (self.head + 1) % self.capacity  # 头指针前进
        self.size -= 1
        return True

    def Front(self) -> int:
        """获取队列头部元素"""
        if self.isEmpty():
            return -1
        return self.queue[self.head]

    def Rear(self) -> int:
        """获取队列尾部元素"""
        if self.isEmpty():
            return -1
        return self.queue[(self.tail - 1 + self.capacity) % self.capacity]  # **修正点**: 防止 `tail == 0` 时 `-1` 计算错误

    def isEmpty(self) -> bool:
        """检查队列是否为空"""
        return self.size == 0

    def isFull(self) -> bool:
        """检查队列是否已满"""
        return self.size == self.capacity

    def size(self) -> int:
        """获取当前队列中的元素数量"""
        return self.size

    def __str__(self):
        """打印队列状态"""
        return f"Queue: {self.queue}, Head: {self.head}, Tail: {self.tail}, Size: {self.size}"


# 测试代码
queue = MyCircularQueue(5)
print(queue.enQueue(1))  # True
print(queue.enQueue(2))  # True
print(queue.enQueue(3))  # True
print(queue.enQueue(4))  # True
print(queue.enQueue(5))  # True
print(queue.enQueue(6))  # False (队列已满)

print(queue.Front())  # 1
print(queue.Rear())   # 5
print(queue.deQueue())  # True
print(queue.enQueue(6))  # True (循环插入)
print(queue.Rear())   # 6
print(queue)  # 查看队列内部状态