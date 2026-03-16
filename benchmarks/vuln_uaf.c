#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    int *array = (int*)malloc(10 * sizeof(int));
    array[5] = 100;
    free(array);
    
    // 毫无遮掩的直接打印，强迫指令执行
    printf("UAF Triggered! Value: %d\n", array[5]);
    return 0;
}
