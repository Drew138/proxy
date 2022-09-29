#include<stdlib.h>
#include<stdio.h>
#include <string.h>
#include "models/ip.c"


struct Ip* parse_ips(char config_line[100]) {

   char * token = strtok(config_line, ",");
   struct Ip* dummy = (struct Ip *)malloc(sizeof(struct Ip));
   struct Ip* cur = dummy;
   while( token != NULL ) {
      struct Ip* tmp = (struct Ip *)malloc(sizeof(struct Ip));
      tmp -> name = token;
      cur -> next = tmp;
      cur = cur -> next;
      token = strtok(NULL, ",");
   }
   struct Ip* head = dummy -> next;
   struct Ip* tail = cur;
   tail -> next = head;
   return head;
}
