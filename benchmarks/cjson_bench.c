#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 🚀 终极白嫖法：直接 include .c 文件！
// 这样你的 Python 脚本就只需要编译 cjson_bench.c 这一个文件，完全不用改脚本逻辑！
#include "cJSON.c"

int main() {
    // 构造一个稍微复杂点的嵌套 JSON 字符串
    const char *json_string = 
        "{\n"
        "  \"project\": \"llvm-sanitizer-placement\",\n"
        "  \"author\": \"tianji\",\n"
        "  \"components\": [\n"
        "    {\"name\": \"Frontend\", \"status\": \"done\"},\n"
        "    {\"name\": \"Optimizer\", \"status\": \"testing\", \"passes\": 150},\n"
        "    {\"name\": \"Backend\", \"status\": \"pending\"}\n"
        "  ],\n"
        "  \"nested_data\": {\"level1\": {\"level2\": {\"level3\": 999}}}\n"
        "}";

    // 循环 20 万次！榨干 CPU，触发海量的 malloc 和 free
    int iterations = 200000;
    
    for (int i = 0; i < iterations; i++) {
        // 1. 构建 JSON 树 (触发大量 malloc)
        cJSON *root = cJSON_Parse(json_string);
        if (!root) {
            printf("Error before: [%s]\n", cJSON_GetErrorPtr());
            return 1;
        }

        // 2. 随便读一个值，防止被优化器当成死代码删掉 (DSE)
        cJSON *author = cJSON_GetObjectItemCaseSensitive(root, "author");
        
        // 最后一次循环打印一下，证明程序跑通了
        if (i == iterations - 1 && cJSON_IsString(author)) {
            printf("✅ cJSON Benchmark Done. Author: %s\n", author->valuestring);
        }

        // 3. 递归销毁 JSON 树 (触发大量 free，ASan 最喜欢查这个)
        cJSON_Delete(root);
    }

    return 0;
}
