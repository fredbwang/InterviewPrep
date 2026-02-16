def length_of_longest_unique_substring(s: str) -> int:
    # 使用一个集合 (set) 来存储当前滑动窗口内的唯一字符
    seen = set()
   
    # 滑动窗口的左指针
    left = 0 
   
    # 记录最长无重复子串的长度
    max_length = 0 

    # 使用右指针遍历字符串
    for right in range(len(s)):
     # 如果当前字符已经在集合中，说明出现重复字符，需要移动左指针
     while s[right] in seen:
         seen.remove(s[left]) # 移除滑动窗口左侧的字符
         left += 1 # 右移左指针，缩小窗口
     
     # 将当前字符添加到集合中
     seen.add(s[right])

     # 更新最大长度
     max_length = max(max_length, right - left + 1)
   
    # 返回最长无重复子串的长度
    return max_length