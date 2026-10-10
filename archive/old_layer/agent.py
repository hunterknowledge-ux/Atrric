"""
agent.py - Atrric Code Agent (Granite 4.2 8B)
Fokus: Edit kod, refactor, debug, git, testing, dan automasi.
"""

import subprocess
import os
import re

# ======================================================================
# 1. PANGGIL GRANITE
# ======================================================================

def ask_granite(prompt: str) -> str:
    """Hantar prompt ke Granite 4.2 8B."""
    result = subprocess.run(
        ["ollama", "run", "granite4.2:8b", "--num-ctx", "2048", prompt],
        capture_output=True,
        text=True
    )
    return result.stdout

# ======================================================================
# 2. TOOLS
# ======================================================================

def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"❌ File {path} tak jumpa."

def edit_file(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ File {path} dah dikemas kini."

def list_files() -> str:
    return "\n".join(os.listdir("."))

def run_command(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout or result.stderr

def build_rag() -> str:
    return run_command("python build_rag.py")

def query_rag(question: str) -> str:
    return run_command(f'python query_rag.py "{question}"')

def git_status() -> str:
    return run_command("git status")

def git_commit(message: str) -> str:
    return run_command(f'git commit -m "{message}"')

def git_push() -> str:
    return run_command("git push origin main")

def git_add_all() -> str:
    return run_command("git add .")

def run_tests() -> str:
    try:
        return run_command("pytest -v")
    except:
        return run_command("python -m unittest discover")

def run_linter() -> str:
    result = run_command("flake8 . --max-line-length=120")
    if "command not found" in result:
        return "❌ flake8 tidak dipasang. Pasang dengan: pip install flake8"
    return result

def view_logs(lines: int = 20) -> str:
    try:
        with open("logs/query.log", "r") as f:
            content = f.read().splitlines()[-lines:]
        return "\n".join(content)
    except FileNotFoundError:
        return "❌ logs/query.log belum wujud."

def view_build_log(lines: int = 20) -> str:
    try:
        with open("logs/build.log", "r") as f:
            content = f.read().splitlines()[-lines:]
        return "\n".join(content)
    except FileNotFoundError:
        return "❌ logs/build.log belum wujud."

# ======================================================================
# 3. TOOL REGISTRY & PARSING
# ======================================================================

TOOLS = {
    "read_file": read_file,
    "edit_file": edit_file,
    "list_files": list_files,
    "run_command": run_command,
    "build_rag": build_rag,
    "query_rag": query_rag,
    "git_status": git_status,
    "git_commit": git_commit,
    "git_push": git_push,
    "git_add_all": git_add_all,
    "run_tests": run_tests,
    "run_linter": run_linter,
    "view_logs": view_logs,
    "view_build_log": view_build_log,
}

def execute_tool(tool_str: str) -> str:
    match = re.match(r"TOOL:\s*(\w+)\((.*)\)", tool_str, re.IGNORECASE)
    if not match:
        return f"❌ Format tool tidak sah: {tool_str}"

    tool_name = match.group(1).strip()
    args_str = match.group(2).strip()

    if tool_name not in TOOLS:
        return f"❌ Tool '{tool_name}' tidak dikenali."

    try:
        import ast
        args = ast.literal_eval(f"[{args_str}]") if args_str else []
    except:
        args = [args_str]

    try:
        return TOOLS[tool_name](*args)
    except Exception as e:
        return f"❌ Error: {e}"

# ======================================================================
# 4. SYSTEM PROMPT
# ======================================================================

SYSTEM_PROMPT = """Kau adalah Atrric Code Agent — pakar dalam mengedit, refactor, debug, git, testing, dan automasi.

**Tool yang tersedia:**
- read_file(path) — baca fail
- edit_file(path, content) — tulis semula fail
- list_files() — senaraikan file
- run_command(cmd) — jalankan terminal
- build_rag() — jalankan build_rag.py
- query_rag(question) — tanya Atrric
- git_status() — status git
- git_commit(message) — commit dengan mesej
- git_push() — push ke GitHub
- git_add_all() — add semua perubahan
- run_tests() — jalankan pytest
- run_linter() — jalankan flake8
- view_logs(lines) — lihat logs/query.log
- view_build_log(lines) — lihat logs/build.log

**Cara guna tool:**
TOOL: nama_tool(argumen)
Contoh: TOOL: read_file(query_rag.py)
Contoh: TOOL: git_commit("Fix bug")

**Untuk soalan di luar kod, jawab ringkas (1-2 ayat).**"""

# ======================================================================
# 5. AGENT LOOP
# ======================================================================

def agent_loop():
    print("==================================================")
    print("🤖 Atrric Code Agent (Granite 4.2 8B)")
    print("==================================================")
    
    while True:
        user_input = input("\n👤 You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Bye!")
            break

        full_prompt = f"""{SYSTEM_PROMPT}

Arahan pengguna: {user_input}
Berikan jawapan dan jika perlu, gunakan tool dengan format TOOL: nama_tool(argumen).
"""

        response = ask_granite(full_prompt)

        # Semak dan jalankan tool
        tool_pattern = r"TOOL:\s*\w+\(.*\)"
        tool_matches = re.findall(tool_pattern, response, re.IGNORECASE)

        if tool_matches:
            for tool_call in tool_matches:
                tool_result = execute_tool(tool_call)
                print(f"\n🛠️  Executing: {tool_call}")
                print(f"📋 Result:\n{tool_result}\n")
        else:
            print(f"\n🤖 Agent:\n{response}\n")


if __name__ == "__main__":
    agent_loop()