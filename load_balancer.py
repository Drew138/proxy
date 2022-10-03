class Ip:
    def __init__(self):
        pass

def which_ip(ips: list(Ip), index: list(int)):
    curr_ip = ips[index[0]]
    index[0] += 1
    return curr_ip