#include <stdio.h>
#include <stdlib.h>

// 技巧 1: 使用 __attribute__((noinline))
// 作用：告诉编译器“这个函数单独编译，不要把它展开到 main 里”。
// 这样编译器在编译 main 的时候，就不知道这个函数里干了坏事。
__attribute__((noinline))
void trigger_uaf(int *p) {
    // 这里的 p[5] 读取会触发 ASan
    // 因为是 noinline，编译器必须生成真实的内存读取指令
    printf("Read after free value: %d\n", p[5]); 
}

int main(int argc, char **argv) {
    // 技巧 2: 把 malloc 的大小跟 argc 挂钩（虽然我们知道是 0+10）
    // 作用：防止编译器在编译时算出具体数值，强迫它生成运行时代码
    int size = 10;
    if (argc > 100) size = 20; 

    int *array = (int*)malloc(size * sizeof(int));
    array[5] = 100;
    
    printf("Freeing memory...\n");
    free(array);

    printf("Triggering Use-After-Free...\n");
    
    // 调用那个禁止内联的函数
    trigger_uaf(array);
    
    printf("=== Test Finished (If you see this, ASan failed) ===\n");
    return 0;
}
