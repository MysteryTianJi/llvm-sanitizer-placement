#include <stdio.h>
#include <stdlib.h>

#define V 1800
#define INF 99999

int main() {
    int *dist = (int *)malloc(V * V * sizeof(int));

    // 初始化图
    for (int i = 0; i < V; i++) {
        for (int j = 0; j < V; j++) {
            if (i == j) dist[i * V + j] = 0;
            else dist[i * V + j] = (i + j) % 100 == 0 ? INF : (i + j) % 20;
        }
    }

    // 核心计算
    for (int k = 0; k < V; k++) {
        for (int i = 0; i < V; i++) {
            for (int j = 0; j < V; j++) {
                if (dist[i * V + k] + dist[k * V + j] < dist[i * V + j]) {
                    dist[i * V + j] = dist[i * V + k] + dist[k * V + j];
                }
            }
        }
    }

    printf("Floyd-Warshall Done. Sample dist: %d\n", dist[(V-1)*V + (V-2)]);
    free(dist);
    return 0;
}
