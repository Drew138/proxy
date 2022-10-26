import sys
import os
import time
import threading

# Definition of a Node for a Double Ended Queue


class Node:
    def __init__(self, req: str, res: str, TTL: int):
        self.res: str = res
        self.req: str = req
        self.TTL: int = TTL
        self.last_access: float = time.time()
        self.next: Node | None = None
        self.prev: Node | None = None

# Definition of a Double Ended Queue


class DEQ:
    def __init__(self):
        self.head: Node | None = None
        self.tail: Node | None = None
        self.size: int = 0

    # Add a new node to the front of the queue and return it
    def add(self, data):
        temp = Node(*data)
        temp.next = self.head
        if self.head:
            self.head.prev = temp
        self.head = temp

        if self.size == 0:
            self.tail = self.head

        self.size += 1

        return temp

    # Move a node to the front of the queue
    def to_front(self, node: Node):
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
        else:                  # If the node is in the middle, move to the front
            front.prev = back
            back.next = front

        # Move the node to the front
        node.next = self.head

        # And set the new head
        self.head = node

    # Remove the last node from the queue and return it
    def pop(self):
        # If the DEQ is empty, there is nothing to pop, so return None
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
    def __init__(self, cache_size: int, ttl: int, delimiter: str, path_to_persistence: str, lock: threading.Lock, sleep: int):
        # Config variables
        self.PATH_TO_PERSISTENCE: str = path_to_persistence
        self.MAX_SIZE: int = cache_size
        self.DELIMITER: str = delimiter
        self.TTL: int = ttl
        self.lock: threading.Lock = lock

        # Cache variables
        self.CURRENT_SIZE: int = 0
        self.in_deq: dict = {}
        self.deq: DEQ = DEQ()

        # Time
        self.SLEEP = sleep

        print('Loading cache...')
        if os.path.exists(self.PATH_TO_PERSISTENCE):
            print('Cache found, loading...')

            print('self.PATH_TO_PERSISTENCE', self.PATH_TO_PERSISTENCE)
            # Load cache from persistence
            with open(self.PATH_TO_PERSISTENCE, 'r') as file:
                content = "\n".join(file.readlines())
                registers = content.split(self.DELIMITER+self.DELIMITER+self.DELIMITER)
                
                for line in registers:
                    res, req, TTL = line.split(self.DELIMITER)
                    TTL = int(TTL)
                    node = self.deq.add([req, res, TTL])
                    self.in_deq[req] = node
    
    def add(self, request: str, response: str):
        with self.lock:
            # Check if cache is full and delete oldest nodes while it is
            while self.CURRENT_SIZE + sys.getsizeof(response) > self.MAX_SIZE:
                old_node = self.deq.pop()
                del self.in_deq[old_node.req]
                self.CURRENT_SIZE -= sys.getsizeof(old_node.res)

            # Add request to cache
            node = self.deq.add([request, response, self.TTL])
            self.CURRENT_SIZE += sys.getsizeof(response)
            self.in_deq[request] = node

    def get(self, request: str):
        with self.lock:
            # Check if request is in cache
            if request in self.in_deq:
                node = self.in_deq[request]  # Get node from cache
                node.TTL = self.TTL  # Reset TTL
                node.last_access = time.time()  # Update last access time
                self.deq.to_front(node)  # Move node to front of cache
                return node.res

            # Request not in cache, return None
            return None

    def check_time(self):
        while True:
            self.update_time()
            self.save_cache()
            time.sleep(self.SLEEP)

    def update_time(self):
        with self.lock:
            curr: Node = self.deq.tail

            # Iterate through cache
            while curr != None:
                node = curr

                # Get current time
                now = time.time()

                # Check if TTL is 0 or less since last access
                node.TTL -= now - node.last_access

                # Update last access time
                node.last_access = now

                # If TTL is 0 or less, remove node from cache
                if node.TTL <= 0:
                    self.deq.pop()
                    self.CURRENT_SIZE -= sys.getsizeof(node)
                    del self.in_deq[node.req]

                # Move to next node
                curr = curr.prev

    def save_cache(self):
        with self.lock:
            curr: Node = self.deq.head

            print("chimbo de burro")
            # Iterate through cache
            print(curr)
            while curr != None:
                node = curr

                # Save node to persistence
                with open(self.PATH_TO_PERSISTENCE, 'w') as file:
                    file.write(
                        f'{node.res}{self.DELIMITER}{node.req}{self.DELIMITER}{node.TTL}'+{self.DELIMITER}+{self.DELIMITER}+{self.DELIMITER})

                # Move to next node
                curr = curr.next
