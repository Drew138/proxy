#include "models/ip.c"
#include "models/request.c"
#include <string.h>


size_t next_ip(struct Ip *curr, struct Request req){
    size_t name = curr -> name;
    curr = curr -> next;
    return name;
}
