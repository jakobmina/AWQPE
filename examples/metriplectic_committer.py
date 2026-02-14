import subprocess
import os
import sys

THRESHOLD = 1000

def get_change_count():
    try:
        # Sum of insertions and deletions
        cmd = ["git", "diff", "--numstat"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        count = 0
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                # Handle binary files or renames (marks as '-')
                add = int(parts[0]) if parts[0].isdigit() else 0
                sub = int(parts[1]) if parts[1].isdigit() else 0
                count += add + sub
        return count
    except Exception as e:
        print(f"Error checking changes: {e}")
        return 0

def auto_commit():
    count = get_change_count()
    if count >= THRESHOLD:
        print(f"[*] Cambios detectados ({count}) superan el umbral ({THRESHOLD}).")
        print("[*] Ejecutando Commit Metripléptico Automático...")
        try:
            subprocess.run(["git", "add", "."], check=True)
            msg = f"Checkpoint Metripléptico Automático: {count} cambios procesados."
            subprocess.run(["git", "commit", "-m", msg], check=True)
            print("[✓] Commit realizado con éxito.")
        except subprocess.CalledProcessError as e:
            print(f"Error al realizar commit: {e}")
    else:
        print(f"[*] Cambios actuales: {count}. (Umbral: {THRESHOLD})")

if __name__ == "__main__":
    auto_commit()
