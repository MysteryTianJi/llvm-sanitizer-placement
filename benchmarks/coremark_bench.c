#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

// ==========================================
// 强制满足 CoreMark 的傲娇宏定义要求
// ==========================================
#define ITERATIONS 30000
#define FLAGS_STR "-O2"
#define COMPILER_FLAGS "-O2"
#define COMPILER_VERSION "Clang (Apple Silicon)"
#define MEM_LOCATION "STACK"
#define SEED_METHOD 0

// 防止 Mac 系统下 clock_gettime 报错的兼容宏
#ifndef CLOCK_REALTIME
#define CLOCK_REALTIME 0
#endif

// ==========================================
// 暴力缝合区 (注意顺序，portme 必须在最前面)
// ==========================================
#include "core_portme.c"
#include "core_main.c"
#include "core_matrix.c"
#include "core_state.c"
#include "core_util.c"
#include "core_list_join.c" // 👈 刚刚补上的最后一块拼图！
