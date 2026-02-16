import collections
from collections import Counter

class LogsAndQueries:
    def __init__(self):
        # Counter to assign a unique ID (qid) to each query
        self.query_counter = 0
        
        # Dictionary to store seen queries
        # Key: sorted query text (to handle duplicate queries in different word orders)
        # Value: unique query ID (qid)
        self.seen_queries = {}
        
        # Dictionary to store word counts for each query
        # Key: qid, Value: Counter object with word frequencies
        self.query_word_counts = {}
        
        # Inverted index to store word-to-query ID mappings

        # Key: word, Value: set of query IDs that contain this word
        self.inverted_index = collections.defaultdict(set)
        
        # List to store output results
        self.results = []

    def process_entry(self, entry):
        """Process each log or query entry from the input list."""
        
        if entry.startswith("Q: "):  # Process a query entry
            query_text = entry[3:].strip().lower()  # Extract and normalize query text
            sorted_query_text = " ".join(sorted(query_text.split()))  # Normalize by sorting words
            word_count = Counter(query_text.split())  # Count occurrences of each word
            
            if sorted_query_text not in self.seen_queries:  # If the query is new
                self.query_counter += 1  # Increment the query counter
                self.seen_queries[sorted_query_text] = self.query_counter  # Store query ID
                self.query_word_counts[self.query_counter] = word_count  # Store word count
               
                # Update the inverted index (map words to query IDs)
                words = set(query_text.split())  # Get unique words in the query
                for word in words:
                    self.inverted_index[word].add(self.query_counter)
               
                # Store acknowledgment message
                self.results.append(f"ACK: {query_text}; ID={self.query_counter}")
            else:  # If the query has already been seen, retrieve the stored qid
                qid = self.seen_queries[sorted_query_text]
                self.results.append(f"ACK: {query_text}; ID={qid}")

        elif entry.startswith("L: "):  # Process a log entry
            log_text = entry[3:].strip().lower()  # Extract and normalize log text
            log_word_count = Counter(log_text.split())  # Count occurrences of each word in the log
            possible_qids = set()

            # Retrieve all possible query IDs that contain words from the log
            for word in log_word_count.keys():
                if word in self.inverted_index:
                    possible_qids.update(self.inverted_index[word])
            
            matched_qids = set()

            # Check if any query fully matches the log
            for qid in possible_qids:
                query_word_count = self.query_word_counts[qid]
               
                # If the query contains more words than the log, it cannot match
                if sum(query_word_count.values()) > sum(log_word_count.values()):
                    continue
               
                # Verify that the log contains all words required by the query with correct frequency
                if all(log_word_count[word] >= count for word, count in query_word_count.items()):
                    matched_qids.add(qid)

            if matched_qids:
                # If matched queries are found, store them in sorted order
                self.results.append(f"M {log_text} Q={', '.join(map(str, sorted(matched_qids)))}")
            else:
                pass  # If no match, do nothing (optional: could store "No Match Found")

    def process_logs_and_queries(self, logs_and_queries):
        """Process a list of log and query entries."""
        for entry in logs_and_queries:
            self.process_entry(entry)  # Process each entry
        return self.results  # Return the final list of results

test_input = [
    "Q: Hello world",
    "Q: data failure",
    "Q: world hello",  # Duplicate of "Hello world" (normalized)
    "L: hello world hello we have a data failure",
    "L: oh no hello system error",
]

processor = LogsAndQueries()
output = processor.process_logs_and_queries(test_input)
print(output)

test_input = [
    "Q: Hello world",
    "Q: data failure",
    "Q: world hello",
    "Q: world hello hello",
    "L: hello world hello we have a data failure",
    "L: oh no hello system error",
    "Q: system error",
    "L: oh no hello system error again",
    "L: oh no hello world system error again"
]

processor = LogsAndQueries()
output = processor.process_logs_and_queries(test_input)
print(output)

# class LogsAndQueries:
#     def __init__(self):
#         # 计数器，用于为每个查询分配唯一的 ID（qid）
#         self.query_counter = 0
        
#         # 记录已经出现的查询，key 为排序后的查询文本（去重词序），value 为 qid
#         self.seen_queries = {}
        
#         # 存储查询的单词计数（用于匹配日志）
#         self.query_word_counts = {}
        
#         # 倒排索引，key 为单词，value 为包含该单词的查询 ID 集合
#         self.inverted_index = defaultdict(set)
        
#         # 结果列表，存储每个日志或查询的输出
#         self.results = []

#     def process_entry(self, entry):
#         if entry.startswith("Q: "):  # 处理查询
#             query_text = entry[3:].strip().lower()  # 提取查询文本并转换为小写
#             sorted_query_text = " ".join(sorted(query_text.split()))  # 归一化查询文本（按字母排序）
#             word_count = Counter(query_text.split())  # 统计查询文本中的单词出现次数
            
#             if sorted_query_text not in self.seen_queries:  # 如果查询未见过
#                 self.query_counter += 1  # 递增查询计数
#                 qid = f"q{self.query_counter}"  # 生成唯一查询 ID
#                 self.seen_queries[sorted_query_text] = qid  # 存储查询 ID
#                 self.query_word_counts[qid] = word_count  # 存储查询单词计数
               
#                 # 将查询中的每个唯一单词添加到倒排索引中
#                 words = set(query_text.split())
#                 for word in words:
#                     self.inverted_index[word].add(qid)
               
#                 # 记录查询 ID
#                 self.results.append(qid)
#             else:  # 查询已出现过，直接返回之前的 qid
#                 qid = self.seen_queries[sorted_query_text]
#                 self.results.append(qid)

#         elif entry.startswith("L: "):  # 处理日志
#             log_text = entry[3:].strip().lower()  # 提取日志文本并转换为小写
#             log_word_count = Counter(log_text.split())  # 统计日志文本中的单词出现次数
#             possible_qids = set()

#             # 根据倒排索引找到所有可能匹配的查询 ID
#             for word in log_word_count.keys():
#                 if word in self.inverted_index:
#                     possible_qids.update(self.inverted_index[word])

#             matched_qids = set()

#             # 检查查询是否完全匹配日志
#             for qid in possible_qids:
#                 query_word_count = self.query_word_counts[qid]
               
#                 # 查询单词总数大于日志单词总数，不可能匹配，直接跳过
#                 if sum(query_word_count.values()) > sum(log_word_count.values()):
#                     continue
               
#                 # 检查日志是否包含查询所需的所有单词及其频率
#                 if all(log_word_count[word] >= count for word, count in query_word_count.items()):
#                     matched_qids.add(qid)

#             if matched_qids:
#                 # 如果找到匹配的查询，按 ID 排序后加入结果
#                 self.results.append(f"Log {', '.join(sorted(matched_qids))}")
#             else:
#                 # 如果没有匹配的查询，则记录 "Log"
#                 self.results.append("Log")

#     def process_logs_and_queries(self, logs_and_queries):
#         for entry in logs_and_queries:
#             self.process_entry(entry)  # 逐条处理日志和查询
#         return self.results  # 返回最终结果

# # 测试输入
# test_input = [
#     "Q: Hello world",
#     "Q: data failure",
#     "Q: world hello",
#     "Q: world hello hello",
#     "L: hello world hello we have a data failure",
#     "L: oh no hello system error",
#     "Q: system error",
#     "L: oh no hello system error again",
#     "L: oh no hello world system error again"
# ]

# # 创建处理器实例
# processor = LogsAndQueries()
# # 处理日志和查询
# output = processor.process_logs_and_queries(test_input)

# # 输出结果
# for line in output:
#     print(line)