import sys

# Definition of a Node for a Double Ended Queue
class Node:
    def __init__(self, req: str, res: str, TTL: int):
        self.res : str = res
        self.req : str = req
        self.TTL : int = TTL
        self.next : Node = None
        self.prev : Node = None

# Definition of a Double Ended Queue
class DEQ:
    def __init__(self):
        self.head : Node = None
        self.tail : Node = None
        self.size : int = 0
    
    # Add a new node to the front of the queue and return it
    def add(self, data : list(str, str, int)):
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
        
        
        if back and not front: # If the node is the tail, move to the front AND set the new tail
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
        if self.size() == 0:
            return None
        
        # Reduce size by 1
        self.size -= 1
        
        # If there is only one node in the queue, set the head and tail to None and return the it
        if self.size() == 1:
            node = self.head
            node.next, node.prev = None, None
            self.head, self.tail = None, None
            return node

        # If there are more than one node in the queue, set the tail to the second to last node and return the last node
        deleted = self.tail
        self.tail = deleted.prev
        deleted.prev, self.tail.next = None, None
        
        return deleted

class CACHE:
    def __init__(self, port, targets, cache_size, ttl, unit_time, delimiter, path_to_persistence):
        # Config variables
        self.PATH_TO_PERSISTENCE : str = path_to_persistence
        self.MAX_SIZE : int = cache_size
        self.DELIMITER : str = delimiter
        self.TTL : int = ttl
        self.UNIT_TIME : int = unit_time
        
        # Cache variables
        self.CURRENT_SIZE : int = 0
        self.in_deq : dict = {} 
        self.deq : DEQ = DEQ()
        
        # Load cache from persistence
        with open(self.persistence, 'r') as file:
            for line in reversed(file.readlines()):
                res, req, TTL : int = line.split(self.DELIMITER)
                node = self.deq.add([req, res, TTL])
                self.in_deq[req] = node
    
    def add(self, request: str, response: str):
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
        # Check if request is in cache
        if request in self.in_deq:
            node = self.in_deq[request] # Get node from cache
            node.TTL = self.TTL # Reset TTL
            self.deq.to_front(node) # Move node to front of cache
            return node.res
        
        # Request not in cache, return None
        return None
    
    def update_time(self):
        curr : Node = self.deq.tail
        
        # Iterate through cache
        while curr != None:
            node = curr
            
            # Check if TTL is 0 or less
            node.TTL -= self.UNIT_TIME
            
            # If TTL is 0 or less, remove node from cache
            if node.TTL <= 0:
                self.deq.pop()
                self.CURRENT_SIZE -= sys.getsizeof(node.res)
                del self.in_deq[node.req]
            
            # Move to next node
            curr = curr.prev
    
    def save_cache(self):
        curr : Node = self.deq.head
        
        # Iterate through cache
        while curr != None:
            node = curr
            
            # Save node to persistence
            with open(self.persistence, 'w') as file:
                file.write(f'{node.res}{self.DELIMITER}{node.req}{self.DELIMITER}{node.TTL}'+'\n')
            
            # Move to next node
            curr = curr.next