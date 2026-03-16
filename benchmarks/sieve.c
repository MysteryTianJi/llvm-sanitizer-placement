#include <stdio.h>
#include <stdlib.h>

#define LIMIT 150000000 // 1.5亿以内的素数

int main() {
    char *isPrime = (char *)malloc(LIMIT + 1);
    for (int i = 0; i <= LIMIT; i++) isPrime[i] = 1;

    isPrime[0] = 0;
    isPrime[1] = 0;

    for (long long p = 2; p * p <= LIMIT; p++) {
        if (isPrime[p]) {
            for (long long i = p * p; i <= LIMIT; i += p) {
                isPrime[i] = 0;
            }
        }
    }

    int count = 0;
    for (int i = 0; i <= LIMIT; i++) {
        if (isPrime[i]) count++;
    }

    printf("Sieve Done. Primes found: %d\n", count);
    free(isPrime);
    return 0;
}
