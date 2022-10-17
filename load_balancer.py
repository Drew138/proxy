def which_ip(ips: list(), index: list(int)):
    curr_ip = ips[index[0]]
    index[0] += 1
    
    if index[0] > len(ips) - 1:
        index[0] = 0
    
    return curr_ip

