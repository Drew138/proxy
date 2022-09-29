
#include "parse_ips.c"
#include <stdio.h>

int main() {
    char hola[100] = "192.80.21.123,192.80.21.124,192.80.21.125,192.80.21.126";
    struct Ip* ip = parse_ips(hola);

    // printf("hola");
    while (1) {
        printf("%s\n", ip -> name);
        ip = ip -> next;
    }
    return 0;
}
