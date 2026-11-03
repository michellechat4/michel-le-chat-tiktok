import subprocess, os, sys
import numpy as np, skia
from art import *
os.makedirs("sc", exist_ok=True)
only = sys.argv[1:]
frames_done = 0
for name, a, b in SCENES:
    f0, f1 = round(a * FPS), round(b * FPS)
    tmp, final = f"sc/{name}.tmp.mp4", f"sc/{name}.mp4"
    if only and name not in only:
        continue
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-r", str(FPS),
                          "-g", "60", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    s = skia.Surface(arr)
    for i in range(f0, f1):
        arr[..., :] = 0
        with s as c:
            draw_frame(c, i / FPS)
        arr[..., 3] = 255
        p.stdin.write(arr.tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.rename(tmp, final)
    print("ok", name, f1 - f0, flush=True)
