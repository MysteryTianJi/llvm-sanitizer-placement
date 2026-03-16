import os
import subprocess
import time
import statistics

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BUILD_DIR = os.path.join(PROJECT_ROOT, "llvm-project", "build")
CLANG_BIN = os.path.join(BUILD_DIR, "bin", "clang")
TARGET_FLAGS = ["--target=x86_64-apple-darwin", "-O2"]

BENCHMARKS = ["matrix_mult.c", "sieve.c", "n_queens.c", "quicksort.c", "floyd_warshall.c"]

def get_sdk_path():
    return subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()

def measure_all_metrics(test_file, location, runs=3):
    env = os.environ.copy()
    if location != "NONE": env["THESIS_ASAN_LOC"] = location
    else: env.pop("THESIS_ASAN_LOC", None)
            
    sdk_path = get_sdk_path()
    
    # 1. 测量【编译时间】
    compile_cmd = [CLANG_BIN, "-c", test_file, "-o", "test.o", "-isysroot", sdk_path]
    if location != "NONE": compile_cmd.append("-fsanitize=address")
    compile_cmd.extend(TARGET_FLAGS)
    
    start_compile = time.perf_counter()
    res_compile = subprocess.run(compile_cmd, env=env, stderr=subprocess.PIPE, text=True)
    compile_time = time.perf_counter() - start_compile
    
    if res_compile.returncode != 0: return None

    # 链接
    link_cmd = [CLANG_BIN, "test.o", "-o", "test_exec", "-isysroot", sdk_path]
    if location != "NONE": link_cmd.append("-fsanitize=address")
    link_cmd.extend(TARGET_FLAGS)
    subprocess.run(link_cmd, env=env, stderr=subprocess.PIPE, text=True)

    # 2. 测量【二进制体积】(Bytes)
    binary_size = os.path.getsize("test_exec") if os.path.exists("test_exec") else 0

    # 3. 测量【运行时间】
    run_times = []
    for _ in range(runs):
        start_run = time.perf_counter()
        subprocess.run(["./test_exec"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        run_times.append(time.perf_counter() - start_run)
    
    avg_run_time = statistics.mean(run_times)

    # 清理
    if os.path.exists("test.o"): os.remove("test.o")
    if os.path.exists("test_exec"): os.remove("test_exec")
    
    return {"run_time": avg_run_time, "compile_time": compile_time, "bin_size": binary_size}

if __name__ == "__main__":
    locations = ["NONE", "PRE", "MID", "POST"]
    print("🚀 正在收集多维度数据 (运行时间、编译时间、二进制体积)...\n")
    
    results = {b: {} for b in BENCHMARKS}
    
    for b_name in BENCHMARKS:
        test_file = os.path.join(PROJECT_ROOT, "benchmarks", b_name)
        if not os.path.exists(test_file): continue
        for loc in locations:
            results[b_name][loc] = measure_all_metrics(test_file, loc)

    # 输出极其专业的 Markdown 表格
    print("📊 === 1. 运行时间 (Execution Time - Seconds) ===")
    print("| Benchmark | NONE | PRE-OPT | MID-OPT | POST-OPT |")
    print("|---|---|---|---|---|")
    for b in BENCHMARKS:
        if results[b].get("NONE"):
            print(f"| {b} | {results[b]['NONE']['run_time']:.4f} | {results[b]['PRE']['run_time']:.4f} | {results[b]['MID']['run_time']:.4f} | {results[b]['POST']['run_time']:.4f} |")

    print("\n📦 === 2. 二进制体积 (Binary Size - Bytes) ===")
    print("| Benchmark | NONE | PRE-OPT | MID-OPT | POST-OPT |")
    print("|---|---|---|---|---|")
    for b in BENCHMARKS:
        if results[b].get("NONE"):
            print(f"| {b} | {results[b]['NONE']['bin_size']} | {results[b]['PRE']['bin_size']} | {results[b]['MID']['bin_size']} | {results[b]['POST']['bin_size']} |")

    print("\n⏱️ === 3. 编译耗时 (Compile Time - Seconds) ===")
    print("| Benchmark | NONE | PRE-OPT | MID-OPT | POST-OPT |")
    print("|---|---|---|---|---|")
    for b in BENCHMARKS:
        if results[b].get("NONE"):
            print(f"| {b} | {results[b]['NONE']['compile_time']:.4f} | {results[b]['PRE']['compile_time']:.4f} | {results[b]['MID']['compile_time']:.4f} | {results[b]['POST']['compile_time']:.4f} |")
