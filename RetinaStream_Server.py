import subprocess
import cv2
import numpy as np
import shutil
import platform
import sys

RTMP_PORT = 1935
WIDTH = 1280
HEIGHT = 720
FPS = 60
APP_NAME = "RTMP Preview"

# -------- Ensure ffmpeg is installed --------
def ensure_ffmpeg():
    if shutil.which("ffmpeg"):
        return
    system = platform.system().lower()
    if system == "windows":
        print("Installing ffmpeg via winget...")
        subprocess.run(["winget", "install", "ffmpeg"], shell=True)
    elif system == "linux":
        print("Installing ffmpeg via apt...")
        subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"])
    else:
        print("Please install ffmpeg manually (macOS)")
        sys.exit(1)

# -------- Main RTMP preview --------
def main():
    ensure_ffmpeg()
    print(f"Starting RTMP server on 0.0.0.0:{RTMP_PORT}")
    print(f"RTMP ingest URL: rtmp://<this-ip>:{RTMP_PORT}/live/<anykey>")

    # Start FFmpeg RTMP listener
    ffmpeg = subprocess.Popen([
        "ffmpeg",
        "-listen", "1",
        "-i", f"rtmp://0.0.0.0:{RTMP_PORT}/live",
        "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS}",
        "-vcodec", "rawvideo",
        "-pix_fmt", "bgr24",
        "-f", "rawvideo",
        "pipe:1"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("Waiting for RTMP stream...")

    try:
        while True:
            raw_frame = ffmpeg.stdout.read(WIDTH * HEIGHT * 3)
            if not raw_frame:
                continue

            frame = np.frombuffer(raw_frame, np.uint8).reshape((HEIGHT, WIDTH, 3))
            cv2.imshow(APP_NAME, frame)

            if cv2.waitKey(1) == 27:  # ESC to exit
                break

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ffmpeg.kill()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
