#include <stdio.h>
#include <stdlib.h>

#define N 14 // N=14 大概需要几秒钟

int count = 0;

int isSafe(int board[], int row, int col) {
    for (int i = 0; i < row; i++) {
        if (board[i] == col || abs(board[i] - col) == abs(i - row)) {
            return 0;
        }
    }
    return 1;
}

void solve(int board[], int row) {
    if (row == N) {
        count++;
        return;
    }
    for (int i = 0; i < N; i++) {
        if (isSafe(board, row, i)) {
            board[row] = i;
            solve(board, row + 1);
        }
    }
}

int main() {
    int board[N];
    solve(board, 0);
    printf("N-Queens Done. Solutions for N=%d: %d\n", N, count);
    return 0;
}
