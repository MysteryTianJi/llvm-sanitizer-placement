#include <stdio.h>
#include <stdlib.h>

#define SIZE 30000000

void swap(int* a, int* b) {
    int t = *a; *a = *b; *b = t;
}

int partition(int arr[], int low, int high) {
    int pivot = arr[high];
    int i = (low - 1);
    for (int j = low; j <= high - 1; j++) {
        if (arr[j] < pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return (i + 1);
}

void quickSort(int arr[], int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}

int main() {
    int *arr = (int *)malloc(SIZE * sizeof(int));
    srand(42); // 固定种子保证每次数据一样
    for(int i = 0; i < SIZE; i++) {
        arr[i] = rand() % 100000;
    }

    quickSort(arr, 0, SIZE - 1);

    printf("QuickSort Done. Mid value: %d\n", arr[SIZE/2]);
    free(arr);
    return 0;
}
