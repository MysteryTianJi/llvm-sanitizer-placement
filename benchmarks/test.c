#include <stdio.h>
#include <stdlib.h>

// 一个简单的函数，模拟内存分配和使用
void memory_test() {
    int *array = (int*)malloc(10 * sizeof(int));
    
    // 正常赋值
    for (int i = 0; i < 10; i++) {
        array[i] = i * 2;
    }

    printf("Memory test: array[5] = %d\n", array[5]);

    // 释放内存
    free(array);
    
    // 如果把下面这行注释取消，就是典型的 Use-After-Free 漏洞
    // printf("After free: %d\n", array[5]); 
}

int main() {
    printf("=== Sanitizer Project Test Case ===\n");
    memory_test();
    printf("=== Test Finished Successfully ===\n");
    return 0;
}
