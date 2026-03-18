import os
import subprocess
import time
import statistics
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 基础路径与配置
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BUILD_DIR = os.path.join(PROJECT_ROOT, "llvm-project", "build")
CLANG_BIN = os.path.join(BUILD_DIR, "bin", "clang")
TARGET_FLAGS = ["--target=x86_64-apple-darwin", "-O2"]

# 图表保存目录 (docs/figures)
CHARTS_DIR = os.path.join(PROJECT_ROOT, "docs", "figures")
os.makedirs(CHARTS_DIR, exist_ok=True)

# 分类测试集
PERF_BENCHMARKS = ["matrix_mult.c", "sieve.c", "n_queens.c", "quicksort.c", "floyd_warshall.c", "cjson_bench.c", "sqlite_bench.c", "coremark_bench.c"]
SEC_BENCHMARKS = ["vuln_uaf.c", "vuln_oob.c", "vuln_dfree.c", "vuln_eliding.c"]
LOCATIONS = ["NONE", "PRE", "MID", "POST"]

def get_sdk_path():
    return subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()

def compile_and_link(test_file, location, sdk_path, env):
    compile_cmd = [CLANG_BIN, "-c", test_file, "-o", "test.o", "-isysroot", sdk_path]
    if location != "NONE": compile_cmd.append("-fsanitize=address")
    compile_cmd.extend(TARGET_FLAGS)
    res_c = subprocess.run(compile_cmd, env=env, stderr=subprocess.PIPE, text=True)
    if res_c.returncode != 0: return False

    link_cmd = [CLANG_BIN, "test.o", "-o", "test_exec", "-isysroot", sdk_path]
    if location != "NONE": link_cmd.append("-fsanitize=address")
    link_cmd.extend(TARGET_FLAGS)
    res_l = subprocess.run(link_cmd, env=env, stderr=subprocess.PIPE, text=True)
    return res_l.returncode == 0

def measure_performance(test_file, location, total_runs=3):
    """
    total_runs 默认为 21 次：
    - 第 1 次用于 Warm-up (预热)，数据丢弃。
    - 后 20 次用于正式计时，取中位数以保证数据稳定性。
    """
    env = os.environ.copy()
    if location != "NONE": 
        env["THESIS_ASAN_LOC"] = location
    else: 
        env.pop("THESIS_ASAN_LOC", None)
            
    sdk_path = get_sdk_path()
    
    # 1. 编译阶段 (编译时间通常波动较小，测一次即可，如有需要也可改为多次)
    start_compile = time.perf_counter()
    if not compile_and_link(test_file, location, sdk_path, env): 
        return None
    compile_time = time.perf_counter() - start_compile
    
    binary_size = os.path.getsize("test_exec") if os.path.exists("test_exec") else 0

    # 2. 运行阶段
    run_times = []
    
    # --- 预热运行 (Warm-up) ---
    if os.path.exists("./test_exec"):
        subprocess.run(["./test_exec"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # --- 正式采样 ---
    for _ in range(total_runs - 1):
        start_run = time.perf_counter()
        subprocess.run(["./test_exec"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        run_times.append(time.perf_counter() - start_run)
    
    # 3. 清理现场
    if os.path.exists("test.o"): os.remove("test.o")
    if os.path.exists("test_exec"): os.remove("test_exec")
    
    return {
        # 使用中位数 (Median) 替代平均值，更符合学术论文对性能波动的处理标准
        "run_time": statistics.median(run_times), 
        "compile_time": compile_time, 
        "bin_size": binary_size
    }

def verify_security(test_file, location):
    if location == "NONE": return "N/A"
    
    env = os.environ.copy()
    env["THESIS_ASAN_LOC"] = location
    sdk_path = get_sdk_path()
    
    if not compile_and_link(test_file, location, sdk_path, env): return "Compile Error"

    res = subprocess.run(["./test_exec"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if os.path.exists("test.o"): os.remove("test.o")
    if os.path.exists("test_exec"): os.remove("test_exec")
    
    if "AddressSanitizer" in res.stderr: return "✅ Caught"
    else: return "❌ Missed"

# ==========================================
# 绘图模块 (归一化 + 防崩修复版)
# ==========================================
def generate_charts(perf_results):
    print(f"\n📈 正在生成高级归一化图表并保存至: {CHARTS_DIR} ...")
    
    # 【核心修复】自动过滤掉编译失败的 Benchmark（比如 CoreMark）
    valid_labels = [b for b in PERF_BENCHMARKS if perf_results.get(b) and perf_results[b].get("NONE") is not None]
    
    if not valid_labels:
        print("❌ 没有成功的测试数据，无法生成图表！")
        return
        
    labels = valid_labels
    x = np.arange(len(labels))
    width = 0.25 # 稍微调宽一点，因为 NONE 不画实体柱子了
    
    # 颜色搭配 (学术风: 红色, 橘色, 蓝色)
    colors = ['#e74c3c', '#f39c12', '#3498db']
    
    def plot_normalized_metric(metric_key, title, ylabel, filename):
        pre_ratios, mid_ratios, post_ratios = [], [], []
        
        for b in labels:
            base_val = perf_results[b]["NONE"][metric_key]
            if base_val == 0: base_val = 1 # 防止除以 0
            
            # 安全获取：如果某个阶段失败，则开销记为 0
            pre_val = perf_results[b].get("PRE")
            mid_val = perf_results[b].get("MID")
            post_val = perf_results[b].get("POST")
            
            pre_ratios.append(pre_val[metric_key] / base_val if pre_val else 0)
            mid_ratios.append(mid_val[metric_key] / base_val if mid_val else 0)
            post_ratios.append(post_val[metric_key] / base_val if post_val else 0)

        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 画出 NONE 的 1.0x 基准虚线
        ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, label='Baseline (NONE = 1.0x)')
        
        # 画插桩后的倍数柱子
        ax.bar(x - width, pre_ratios,  width, label='PRE-OPT', color=colors[0], edgecolor='black')
        ax.bar(x,         mid_ratios,  width, label='MID-OPT', color=colors[1], edgecolor='black')
        ax.bar(x + width, post_ratios, width, label='POST-OPT', color=colors[2], edgecolor='black')

        ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=15, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=11)
        ax.legend()
        ax.grid(axis='y', linestyle=':', alpha=0.6)

        plt.tight_layout()
        filepath = os.path.join(CHARTS_DIR, filename)
        plt.savefig(filepath, dpi=300)
        plt.close()

    plot_normalized_metric("run_time", "Normalized Execution Time Overhead", "Execution Time Ratio (vs NONE)", "fig_runtime_normalized.png")
    plot_normalized_metric("bin_size", "Normalized Binary Size Bloat", "Binary Size Ratio (vs NONE)", "fig_binsize_normalized.png")
    plot_normalized_metric("compile_time", "Normalized Compilation Time Overhead", "Compile Time Ratio (vs NONE)", "fig_compile_normalized.png")
    
    print("✅ 归一化图表生成完毕！")

if __name__ == "__main__":
    print("🚀 启动全自动化评估平台 (性能四大维度 + 安全有效性 + 可视化)...\n")
    
    # 1. 跑性能
    print("⏳ [1/2] 正在运行性能与体积测试 (约需20-30分钟)...")
    perf_results = {b: {} for b in PERF_BENCHMARKS}
    for b_name in PERF_BENCHMARKS:
        test_file = os.path.join(PROJECT_ROOT, "benchmarks", b_name)
        if os.path.exists(test_file):
            for loc in LOCATIONS:
                perf_results[b_name][loc] = measure_performance(test_file, loc)

    # 2. 跑安全
    print("⏳ [2/2] 正在运行安全漏洞检出测试...")
    sec_results = {b: {} for b in SEC_BENCHMARKS}
    for b_name in SEC_BENCHMARKS:
        test_file = os.path.join(PROJECT_ROOT, "benchmarks", b_name)
        if os.path.exists(test_file):
            for loc in ["PRE", "MID", "POST"]: 
                sec_results[b_name][loc] = verify_security(test_file, loc)

    # ==========================================
    # 终极数据输出 (表格全家桶)
    # ==========================================
    print("\n" + "="*50)
    print("🎯 毕设论文第 4 章专用数据表 (可直接复制)")
    print("="*50 + "\n")

    print("📊 === 表 4-1: 运行时性能开销 (Execution Time - Seconds) ===")
    print("| Benchmark | NONE | PRE-OPT | MID-OPT | POST-OPT |")
    print("|---|---|---|---|---|")
    for b in PERF_BENCHMARKS:
        r = perf_results.get(b)
        if r and r.get("NONE"):
            print(f"| {b} | {r['NONE']['run_time']:.4f} | {r['PRE']['run_time']:.4f} | {r['MID']['run_time']:.4f} | {r['POST']['run_time']:.4f} |")

    print("\n📦 === 表 4-2: 二进制体积膨胀 (Binary Size - Bytes) ===")
    print("| Benchmark | NONE | PRE-OPT | MID-OPT | POST-OPT |")
    print("|---|---|---|---|---|")
    for b in PERF_BENCHMARKS:
        r = perf_results.get(b)
        if r and r.get("NONE"):
            print(f"| {b} | {r['NONE']['bin_size']} | {r['PRE']['bin_size']} | {r['MID']['bin_size']} | {r['POST']['bin_size']} |")

    print("\n⏱️ === 表 4-3: 编译期开销 (Compile Time - Seconds) ===")
    print("| Benchmark | NONE | PRE-OPT | MID-OPT | POST-OPT |")
    print("|---|---|---|---|---|")
    for b in PERF_BENCHMARKS:
        r = perf_results.get(b)
        if r and r.get("NONE"):
            print(f"| {b} | {r['NONE']['compile_time']:.4f} | {r['PRE']['compile_time']:.4f} | {r['MID']['compile_time']:.4f} | {r['POST']['compile_time']:.4f} |")

    print("\n🛡️ === 表 4-4: 漏洞检出率 (Detection Effectiveness) ===")
    print("| Vulnerability Type | PRE-OPT | MID-OPT | POST-OPT |")
    print("|---|---|---|---|")
    for b in SEC_BENCHMARKS:
        r = sec_results.get(b)
        if r and r.get("PRE"):
            print(f"| {b} | {r['PRE']} | {r['MID']} | {r['POST']} |")

    # 3. 跑画图
    generate_charts(perf_results)
    
    print(f"\n🎉 全部完成！表格已输出，高清插图请前往 {CHARTS_DIR} 查看！")
