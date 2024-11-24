#include <stdio.h>

int main() {
#ifdef CONFIG
    // printf("CONFIG=1");
    return 1;
#elif N_CONFIG
    return 2;
#else
    // printf("CONFIG=0");
    return 3;
#endif
    // return 0;
}
