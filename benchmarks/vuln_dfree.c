#include <stdio.h>
#include <stdlib.h>

// 全局变量，强制指针逃逸，防止编译器删除 malloc
void *global_ptr; 

int main(int argc, char **argv) {
    int *ptr = (int*)malloc(10 * sizeof(int));
    global_ptr = ptr; 
    
    free(ptr); // 第一次释放
    
    if (argc < 10) { 
        free(ptr); // 第二次释放 (Double Free)
    }
    
    return 0;
}
