#!/usr/bin/env python3
import os, subprocess, time

START = 509
END   = 594

while True:
    for i in range(START, END+1):
        name = f"cart{str(i).zfill(3)}.py"
        if os.path.exists(name):
            print(f"[∞ RUN] {name}")
            subprocess.run(["python", name])
    time.sleep(1)
