#include <stdio.h>
#include <stdlib.h>

// 这是一个普通的静态函数。
// 注意：没有加 noinline，意味着我们“允许”它被优化器内联。
static void vulnerable_read(int *p, int condition) {
    // 只有当 condition > 100 时，才会触发 UAF 读取
    if (condition > 100) {
        printf("UAF Triggered! Value: %d\n", p[5]);
    }
}

int main(int argc, char **argv) {
    int *arr = (int*)malloc(10 * sizeof(int));
    arr[5] = 42;
    free(arr); // 尽早释放，制造 UAF 隐患

    // 【核心陷阱】
    // 我们故意传入一个常数 10，这会导致 condition > 100 永远为假 (False)。
    vulnerable_read(arr, 10);

    return 0;
}
