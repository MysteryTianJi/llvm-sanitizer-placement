#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    int *array = (int*)malloc(10 * sizeof(int));
    array[10] = 999; // 越界写
    
    // 必须读取并打印，防止前面的写操作被 DSE 删掉
    printf("OOB Triggered! Value: %d\n", array[10]);
    free(array);
    return 0;
}
