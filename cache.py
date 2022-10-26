from io import BufferedReader  # used for types
import sys
import os
import time
import threading
from typing import NoReturn


class Node:
    """Definition of a Node for a Double Ended Queue"""

    def __init__(self, req: bytes, res: bytes, ttl: int) -> None:
        self.request: bytes = req
        self.response: bytes = res
        self.ttl: int = ttl
        self.last_access: float = time.time()
        self.next: Node | None = None
        self.prev: Node | None = None


class Deque:
    """Definition of a Double Ended Queue"""

    def __init__(self) -> None:
        self.head: Node | None = None
        self.tail: Node | None = None
        self.size: int = 0

    def add(self, *args) -> Node | None:
        """Add a new node to the front of the queue and return it"""

        temp: Node = Node(*args)
        temp.next = self.head
        if self.head:
            self.head.prev = temp
        self.head = temp

        if self.size == 0:
            self.tail = self.head

        self.size += 1

        return temp

    def to_front(self, node: Node) -> None:
        """Move a node to the front of the queue"""

        if not node or self.size == 0:
            return

        back, front = node.prev, node.next

        # If there is only one node in the queue or if the node is already the head, dont do anything
        if (not back and not front) or (not back and front):
            return

        node.prev, node.next = None, None

        if back and not front:  # If the node is the tail, move to the front AND set the new tail
            back.next = None
            self.tail = back
        else:
            front.prev = back
            back.next = front

        # Move the node to the front
        node.next = self.head

        # And set the new head
        self.head = node

    def pop(self) -> Node | None:
        """Remove the last node from the queue and return it"""

        # If the Deque is empty, there is nothing to pop, so return None
        if self.size == 0:
            return None

        # Reduce size by 1
        self.size -= 1

        # If there is only one node in the queue, set the head and tail to None and return the it
        if self.size == 1:
            node = self.head
            node.next, node.prev = None, None
            self.head, self.tail = None, None
            return node

        # If there are more than one node in the queue, set the tail to the second to last node and return the last node
        deleted = self.tail
        self.tail = deleted.prev
        deleted.prev, self.tail.next = None, None

        return deleted


class Cache:
    """Definition of Cache"""

    def __init__(self, cache_size: int, ttl: int, delimiter: str, path_to_persistence: str, sleep: int) -> None:
        # Config variables
        self.PATH_TO_PERSISTENCE: str = path_to_persistence
        self.MAX_SIZE: int = cache_size
        self.DELIMITER: str = delimiter
        self.TTL: int = ttl
        self.lock: threading.Lock = threading.Lock()

        # Cache variables
        self.CURRENT_SIZE: int = 0
        self.in_deq: dict[bytes, Node | None] = {}
        self.deq: Deque = Deque()

        # Time
        self.SLEEP = sleep

        self.read_cache()

    def parse_descriptor(self, line: bytes) -> dict[str, int]:
        items: list[bytes] = line.split(b', ')
        descriptor: dict[str, int] = {}
        for item in items:
            key, val = item.split(b': ')
            descriptor[key.decode('utf-8')] = int(val)
        return descriptor

    def read_segment(self, file: BufferedReader, descriptor: dict[str, int], key: str, other: bytes) -> tuple[bytes, bytes]:
        request: bytes = b''
        buffer: bytes = b''
        while descriptor[key] > 0:
            line: bytes = other + file.readline()
            other = b''
            length: int = min(len(line), descriptor[key])
            descriptor[key] -= length
            request += line[:length]
            buffer += line[length:]
        return request, buffer

    def read_cache(self) -> None:

        if not os.path.exists(self.PATH_TO_PERSISTENCE):
            print('Cache file not found')
            print('Procceeding to start with empty cache')
            return

        print('Cache file found, loading...')

        # Load cache from persistence
        with open(self.PATH_TO_PERSISTENCE, 'rb') as file:

            buffer = b''
            while True:
                line = buffer + file.readline()
                descriptor = self.parse_descriptor(line)

                request, buffer_request = self.read_segment(
                    file, descriptor, 'request', b'')
                response, buffer_response = self.read_segment(
                    file, descriptor, 'response', buffer_request)
                ttl, _ = self.read_segment(
                    file, descriptor, 'ttl', buffer_response)
                # TTL = int(float(TTL))
                node: Node | None = self.deq.add(
                    [request, response, int(float(ttl))])
                self.in_deq[request] = node
                break

    def add(self, request: bytes, response: bytes) -> Node | None:
        with self.lock:
            # Check if cache is full and delete oldest nodes while it is
            while self.CURRENT_SIZE + sys.getsizeof(response) > self.MAX_SIZE:
                old_node: Node = self.deq.pop()
                del self.in_deq[old_node.request]
                self.CURRENT_SIZE -= sys.getsizeof(old_node.response)

            # Add request to cache
            node = self.deq.add([request, response, self.TTL])
            self.CURRENT_SIZE += sys.getsizeof(response)
            self.in_deq[request] = node

    def get(self, request: bytes) -> bytes:
        with self.lock:
            # Check if request is in cache
            # print(request, self.in_deq)
            if request in self.in_deq:
                node = self.in_deq[request]  # Get node from cache
                node.ttl = self.TTL  # Reset TTL
                node.last_access = time.time()  # Update last access time
                self.deq.to_front(node)  # Move node to front of cache
                return node.response

            # Request not in cache, return None
            return b''

    def check_time(self) -> NoReturn:
        while True:
            self.update_time()
            self.save_cache()
            time.sleep(self.SLEEP)

    def update_time(self) -> None:
        with self.lock:
            curr: Node = self.deq.tail

            # Iterate through cache
            while curr != None:
                node = curr

                # Get current time
                now = time.time()

                # Check if TTL is 0 or less since last access
                node.ttl -= now - node.last_access

                # Update last access time
                node.last_access = now

                # If TTL is 0 or less, remove node from cache
                if node.ttl <= 0:
                    self.deq.pop()
                    self.CURRENT_SIZE -= sys.getsizeof(node)
                    del self.in_deq[node.request]

                # Move to next node
                curr = curr.prev

    def save_cache(self) -> None:
        with self.lock:
            curr: Node | None = self.deq.head
            with open(self.PATH_TO_PERSISTENCE, 'wb') as file:
                # Iterate through cache
                while curr != None:
                    node = curr

                    buffer = bytes()
                    request = node.request
                    response = node.response
                    ttl = bytes(node.ttl)
                    descriptor: bytes = b'request: ' + bytes(len(request))
                    descriptor += b', response: ' + bytes(len(response))
                    descriptor += b', ttl: ' + bytes(len(ttl)) + b'\n'

                    buffer += descriptor + request + response + ttl

                    file.write(buffer)
                    curr = curr.next
