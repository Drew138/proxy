#include<stdio.h>
#include <string.h>
#include "models/ip.c"

// struct Ip {
//     char *name;
//     struct Ip* next;
// };

struct Ip* parse_ips(char* config_line) {
   char * token = strtok(config_line, ",");
   struct Ip* dummy;
   struct Ip* cur = dummy;
   while( token != NULL ) {
      struct Ip* tmp;
      tmp -> name = token;
      cur -> next = tmp;
      cur = cur -> next;

      token = strtok(NULL, ",");
   }
   struct Ip* head = dummy -> next;
   struct Ip* tail = cur -> next;
   tail -> next = head;
   return head;
}
