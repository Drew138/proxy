class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None

class DEQ:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
    
    def add(self, data):
        temp = Node(data)
        temp.next = self.head
        if self.head:
            self.head.prev = temp
        self.head = temp
        
        if self.size == 0:
            self.tail = self.head
        
        self.size += 1
        
        return temp
    
    def to_front(self, node):
        if not node or self.size == 0:
            return
        
        back, front = node.prev, node.next
        node.prev, node.next = None, None
        
        if not back and not front:
            return 
        elif not back and front:
            front.prev = None
        elif back and not front:
            back.next = None
        else:
            front.prev = back
            back.next = front
        
        node.next = self.head
        self.head = node

    def pop(self):
        if self.size() == 0:
            return None
        
        self.size -= 1
        
        if self.size() == 1:
            node = self.head
            node.next, node.prev = None, None
            self.head, self.tail = None, None
            return node

        deleted = self.tail
        self.tail = deleted.prev
        deleted.prev, self.tail.next = None, None
        
        return deleted

class CACHE:
    def __init__(self, path_deq: str, path_in_deq: str, max_size: int):
        self.in_deq = {} # TODO: Read from file!~
        self.deq = DEQ() # TODO: Read from file!~
        
        with open(path_in_deq, 'r') as file:
            for line in file.readlines():
                self.in_deq[line] = None
        
        
        self.MAX_SIZE = None # TODO: CHANGE TO ENV!
    
    def add(self, request, response):
        if self.deq.size == self.MAX_SIZE: 
            self.deq.pop()
            del self.in_deq[request]

        node = self.deq.add(request)
        self.in_deq[request] = node # TODO: What is the req and the res?
        return 1

    def get(self, request, response):
        if request in self.in_deq:
            node = self.in_deq[request]
            self.deq.to_front(node)
            return node.data # TODO: RETORNAR EL RESPONSE! O EL ARCHIVO, LO QUE SEA!
        
        self.add(request, response)