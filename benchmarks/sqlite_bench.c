#include <stdio.h>
#include <stdlib.h>

// 终极白嫖法：直接 include 这 25 万行的数据库源码！
#include "sqlite3.c"

int main() {
    sqlite3 *db;
    char *zErrMsg = 0;
    int rc;

    // 1. 在纯内存中打开数据库 (避免磁盘 I/O 干扰，纯测 CPU 和内存开销)
    rc = sqlite3_open(":memory:", &db);
    if (rc) {
        printf("Can't open database: %s\n", sqlite3_errmsg(db));
        return 0;
    }

    // 2. 建表
    const char *sql_create = "CREATE TABLE THESIS(ID INT PRIMARY KEY NOT NULL, NAME TEXT NOT NULL);";
    sqlite3_exec(db, sql_create, 0, 0, &zErrMsg);

    // 3. 疯狂插入 50000 条数据！(触发海量堆内存分配和 B-Tree 结构重组)
    sqlite3_exec(db, "BEGIN TRANSACTION;", 0, 0, 0);
    char sql_insert[100];
    for (int i = 0; i < 50000; i++) {
        sprintf(sql_insert, "INSERT INTO THESIS (ID, NAME) VALUES (%d, 'LLVM_ASAN_TEST_%d');", i, i);
        sqlite3_exec(db, sql_insert, 0, 0, &zErrMsg);
    }
    sqlite3_exec(db, "COMMIT;", 0, 0, 0);

    // 4. 做一次全表扫描查询
    const char *sql_select = "SELECT COUNT(*) FROM THESIS WHERE ID > 10000;";
    sqlite3_exec(db, sql_select, 0, 0, &zErrMsg);

    printf("✅ SQLite Benchmark Done. Inserted 50000 rows in memory.\n");
    sqlite3_close(db);
    return 0;
}
