#include <stdio.h>
#include <stdlib.h>

#define N 1200 // 调大这个值可以增加运行时间

int main() {
    int *A = (int *)malloc(N * N * sizeof(int));
    int *B = (int *)malloc(N * N * sizeof(int));
    int *C = (int *)malloc(N * N * sizeof(int));

    // 初始化
    for (int i = 0; i < N * N; i++) {
        A[i] = i % 100;
        B[i] = (i + 5) % 100;
        C[i] = 0;
    }

    // 核心计算
    for (int i = 0; i < N; i++) {
        for (int k = 0; k < N; k++) {
            int temp = A[i * N + k];
            for (int j = 0; j < N; j++) {
                C[i * N + j] += temp * B[k * N + j];
            }
        }
    }

    printf("Matrix Mult Done. Checksum: %d\n", C[(N*N)-1]);
    free(A); free(B); free(C);
    return 0;
}
