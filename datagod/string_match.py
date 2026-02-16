def is_match(word: str, abbr: str) -> bool:
    word_ptr, abbr_ptr = 0, 0  # 指针分别指向 word 和 abbr 的当前位置

    while abbr_ptr < len(abbr):  # 遍历 abbr
        if abbr[abbr_ptr].isdigit():  # 如果当前字符是数字
            num = int(abbr[abbr_ptr])  # 直接转换为整数（因题目限制为单个数字）
            abbr_ptr += 1  # 移动 abbr 指针
            word_ptr += num  # 在 word 中跳过 num 个字符
        else:  # 如果当前字符是字母
            if word_ptr >= len(word) or word[word_ptr] != abbr[abbr_ptr]:  
                # 1. 若 word 遍历完但 abbr 仍有剩余字符，匹配失败
                # 2. 若当前字符不匹配，匹配失败
                return False
            word_ptr += 1  # 移动 word 指针
            abbr_ptr += 1  # 移动 abbr 指针

    return word_ptr == len(word)  # 只有当 word 也完全遍历完时才算匹配成功