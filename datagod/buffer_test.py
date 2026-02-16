import unittest
import threading

class BufferWrite:
    def __init__(self, size=1024):
        self.max_size = size
        self.buffer = ""
        self.disk = []  # Simulating disk storage for verification
        self.lock = threading.RLock()

    def write(self, data: str) -> None:
        """Writes data to the buffer."""
        with self.lock:
            idx = 0
            while idx < len(data):
                # Calculate space left in buffer
                space_left = self.max_size - len(self.buffer)
                
                # Take chunk that fits
                chunk = data[idx : idx + space_left]
                self.buffer += chunk
                idx += len(chunk)
                
                # If buffer is full, flush
                if len(self.buffer) == self.max_size:
                    self.flush()

    def flush(self) -> None:
        """Forces the buffer to flush its contents to the disk."""
        with self.lock:
            if self.buffer:
                self.disk.append(self.buffer)
                self.buffer = ""
                print("Flushed to disk")
            else:
                # No data to flush
                pass

class TestBufferWrite(unittest.TestCase):
    def setUp(self):
        self.buffer_writer = BufferWrite()
    def test_concurrent_writes(self):
        """Test concurrent writes from multiple threads to ensure thread safety."""
        num_threads = 10
        writes_per_thread = 100
        data_write = "x" * 10  # 10 bytes per write

        def worker():
            for _ in range(writes_per_thread):
                self.buffer_writer.write(data_write)

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Flush any remaining data
        self.buffer_writer.flush()

        # Check total data written
        total_disk_data = "".join(self.buffer_writer.disk)
        total_expected_len = num_threads * writes_per_thread * len(data_write)
        
        self.assertEqual(len(total_disk_data), total_expected_len)

    def test_auto_flush_exact_1024(self):
        """write('a' * 1024) should automatically flush() immediately."""
        self.buffer_writer.write('a' * 1024)
        self.assertEqual(len(self.buffer_writer.disk), 1)
        self.assertEqual(self.buffer_writer.disk[0], 'a' * 1024)
        self.assertEqual(self.buffer_writer.buffer, "")

    def test_auto_flush_incremental(self):
        """write('a' * 1000) then write('b' * 24) should trigger an automatic flush()."""
        self.buffer_writer.write('a' * 1000)
        self.assertEqual(len(self.buffer_writer.disk), 0)
        self.assertEqual(self.buffer_writer.buffer, 'a' * 1000)
        
        self.buffer_writer.write('b' * 24)
        self.assertEqual(len(self.buffer_writer.disk), 1)
        self.assertEqual(self.buffer_writer.disk[0], 'a' * 1000 + 'b' * 24)
        self.assertEqual(self.buffer_writer.buffer, "")

    def test_manual_flush(self):
        """write('a' * 900) then flush() should manually trigger a flush."""
        self.buffer_writer.write('a' * 900)
        self.assertEqual(len(self.buffer_writer.disk), 0)
        
        self.buffer_writer.flush()
        self.assertEqual(len(self.buffer_writer.disk), 1)
        self.assertEqual(self.buffer_writer.disk[0], 'a' * 900)
        self.assertEqual(self.buffer_writer.buffer, "")

    def test_multiple_writes_until_flush(self):
        """Multiple write('a' * 512) calls until flush() is needed."""
        self.buffer_writer.write('a' * 512)
        self.assertEqual(len(self.buffer_writer.disk), 0)
        
        self.buffer_writer.write('a' * 512) # buffer full -> flush
        self.assertEqual(len(self.buffer_writer.disk), 1)
        self.assertEqual(self.buffer_writer.disk[0], 'a' * 1024)
        self.assertEqual(self.buffer_writer.buffer, "")

    def test_two_1024_writes_with_flush(self):
        """write('a' * 1024) twice with a flush() in between."""
        self.buffer_writer.write('a' * 1024)
        self.assertEqual(len(self.buffer_writer.disk), 1)
        
        self.buffer_writer.flush()
        # buffer was empty, so no change to disk
        self.assertEqual(len(self.buffer_writer.disk), 1)
        
        self.buffer_writer.write('a' * 1024)
        self.assertEqual(len(self.buffer_writer.disk), 2)
        self.assertEqual(self.buffer_writer.disk[1], 'a' * 1024)

    

if __name__ == '__main__':
    unittest.main()
