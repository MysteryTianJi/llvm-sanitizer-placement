import os
import subprocess
import sys
import time
import shutil

# ==========================================
#              配置区域 (CONFIG)
# ==========================================

# 1. 自动定位项目根目录 (假设脚本在 scripts/ 文件夹下)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # 回退一级到项目根目录

# 2. 关键路径配置
BUILD_DIR = os.path.join(PROJECT_ROOT, "llvm-project", "build")
CLANG_BIN = os.path.join(BUILD_DIR, "bin", "clang")
TEST_FILE = os.path.join(PROJECT_ROOT, "benchmarks", "test.c")

# 3. 编译参数 (针对 M3 Mac 运行 x86 LLVM 的特殊配置)
# -g: 生成调试信息 (方便 ASan 打印行号)
# -O2: 开启优化 (触发 PassPipeline)
TARGET_FLAGS = ["--target=x86_64-apple-darwin", "-O2", "-g"]

# ==========================================
#              工具函数
# ==========================================

def get_sdk_path():
    """获取 macOS SDK 路径，解决找不到 stdio.h 的问题"""
    try:
        return subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    except subprocess.CalledProcessError:
        print("❌ Error: Cannot find macOS SDK.")
        sys.exit(1)

def clean_artifacts():
    """清理中间文件"""
    for f in ["test.o", "test_exec"]:
        if os.path.exists(f):
            os.remove(f)
        # 也要清理生成的 dSYM 调试文件夹
        if os.path.exists(f + ".dSYM"):
            shutil.rmtree(f + ".dSYM")

def run_experiment(location):
    print(f"\n{'='*20} 🧪 Testing Location: {location} {'='*20}")
    
    # 设置环境变量，告诉 C++ 代码插在哪里
    env = os.environ.copy()
    env["THESIS_ASAN_LOC"] = location
    
    sdk_path = get_sdk_path()
    
    # ---------------------------------------------------------
    # 步骤 1: 仅编译 (Compile Only) -> 生成 .o 文件
    # ---------------------------------------------------------
    # 【关键策略】：这里故意 **不加** -fsanitize=address
    # 目的：防止 LLVM 默认逻辑插入 ASan Pass，只允许我们的环境变量触发手动插桩
    # ---------------------------------------------------------
    compile_cmd = [
        CLANG_BIN,
        "-c",                   # 只编译不链接
        TEST_FILE,
        "-o", "test.o",         # 输出中间文件
        "-isysroot", sdk_path,
        "-fsanitize=address"   # 指定 SDK
    ] + TARGET_FLAGS
    
    print(f"🔨 [Step 1] Compiling...")
    # print(f"    Command: {' '.join(compile_cmd)}") # 调试用
    
    start_time = time.time()
    res_compile = subprocess.run(compile_cmd, env=env, stderr=subprocess.PIPE, text=True)
    compile_time = time.time() - start_time

    if res_compile.returncode != 0:
        print("❌ Compilation Failed!")
        print(res_compile.stderr)
        return

    # 验证探针是否生效 (检查 stderr 中是否有 [Thesis] 字样)
    probe_triggered = False
    if "[Thesis]" in res_compile.stderr:
        probe_triggered = True
        print("✅ Custom Probe LOG Detected:")
        for line in res_compile.stderr.split('\n'):
            if "[Thesis]" in line:
                print(f"    └── {line}")
    else:
        if location != "NONE":
            print("⚠️  Warning: No probe log detected. (Did you recompile LLVM?)")

    # ---------------------------------------------------------
    # 步骤 2: 链接 (Link) -> 生成可执行文件
    # ---------------------------------------------------------
    # 【关键策略】：这里 **必须加** -fsanitize=address
    # 目的：告诉链接器把 ASan 的运行时库 (libclang_rt.asan.a) 链进去
    # ---------------------------------------------------------
    link_cmd = [
        CLANG_BIN,
        "test.o",
        "-o", "test_exec",
        "-isysroot", sdk_path,
        "-fsanitize=address"    # <--- 这里才加标志
    ] + TARGET_FLAGS

    print(f"🔗 [Step 2] Linking...")
    res_link = subprocess.run(link_cmd, env=env, stderr=subprocess.PIPE, text=True)
    
    if res_link.returncode != 0:
        print("❌ Linking Failed!")
        print(res_link.stderr)
        return

    # ---------------------------------------------------------
    # 步骤 3: 运行程序 (Runtime Verification)
    # ---------------------------------------------------------
    print(f"🏃 [Step 3] Running Executable...")
    try:
        # 运行生成的程序，捕获输出
        res_run = subprocess.run(["./test_exec"], capture_output=True, text=True)
        
        # 分析运行结果
        if "AddressSanitizer" in res_run.stderr:
            print(f"🛡️  [Result] ASan Triggered! (Bug Caught)")
            # 提取报错的第一行简述
            for line in res_run.stderr.split('\n'):
                if "ERROR: AddressSanitizer" in line:
                    print(f"    └── {line}")
                    break
        else:
            print(f"ℹ️  [Result] Program ran successfully (No ASan error or No Bug).")
            print(f"    Output: {res_run.stdout.strip()}")

    except Exception as e:
        print(f"❌ Execution Error: {e}")

    # 清理垃圾
    clean_artifacts()

# ==========================================
#              主程序入口
# ==========================================
if __name__ == "__main__":
    # 确保 clang 存在
    if not os.path.exists(CLANG_BIN):
        print(f"❌ Critical Error: Clang binary not found at: {CLANG_BIN}")
        print("   Please check your build path.")
        sys.exit(1)
    
    # 确保测试文件存在
    if not os.path.exists(TEST_FILE):
        print(f"❌ Critical Error: Benchmark file not found at: {TEST_FILE}")
        sys.exit(1)

    print(f"🚀 Starting Thesis Experiments...")
    print(f"📂 Project Root: {PROJECT_ROOT}")
    
    # 依次测试所有位置
    # NONE: 用来测试没有任何插桩时的基准情况
    # PRE/MID/POST: 你的三个实验变量
    locations = ["PRE", "MID", "POST"] 
    
    for loc in locations:
        run_experiment(loc)
        print("\n")
