#ifndef "models/ip.c"
#include "models/ip.c"
#endif
#include "models/request.c"
#include <string.h>


char* next_ip(struct Ip *curr, struct Request req){
    char* name = curr -> name;
    curr = curr -> next;
    return name;
}
