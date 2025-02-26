import os
import subprocess
import time
from fastapi import BackgroundTasks, FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

HLS_DIR = os.getenv("HLS_DIR", "./hls")  # Default to "./hls" if not set
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"  # Update if needed

async def convert_rtsp_to_hls(background_tasks: BackgroundTasks, rtsp_url: str):
    """Converts an RTSP stream to HLS format asynchronously"""

    stream_id = abs(hash(rtsp_url))  # Ensure non-negative ID
    stream_dir = os.path.join(HLS_DIR, str(stream_id))
    os.makedirs(stream_dir, exist_ok=True)

    background_tasks.add_task(run_ffmpeg, rtsp_url, stream_dir)

    hls_url = f"http://127.0.0.1:8000/hls/{stream_id}/index.m3u8"
    return {"hls_url": hls_url}

def run_ffmpeg(rtsp_url: str, output_dir: str):
    """Runs FFmpeg continuously, restarting on failure"""

    log_file = os.path.join(output_dir, "ffmpeg.log")

    while True:
        cmd = [
            FFMPEG_PATH,
            '-loglevel', 'info',  # Log level
            '-rtsp_transport', 'tcp',  # Use TCP for RTSP (more stable)
            '-rtsp_flags', 'prefer_tcp',
            '-analyzeduration', '10000000',  # Increase analysis time
            '-probesize', '5000000',

            '-i', rtsp_url,  # Input RTSP URL

            # Video Encoding (Force H.264)
            '-c:v', 'libx264',  
            '-preset', 'ultrafast',  # Faster encoding (can be adjusted)
            '-tune', 'zerolatency',  # Reduce latency for live streaming
            '-crf', '23',  # Quality (lower = better, but larger file)
            '-g', '50',  # Keyframe interval (match FPS x2 for smooth seeking)

            # Audio Encoding (AAC)
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ac', '1',  # Mono audio to save bandwidth

            # HLS Settings
            '-hls_time', '2',  # Segment duration
            '-hls_list_size', '5',  # Keep last 5 segments
            '-hls_flags', 'delete_segments',  # Delete old segments to save space
            '-hls_segment_filename', os.path.join(output_dir, "segment_%03d.ts"),  # Segment naming

            # Output HLS
            '-f', 'hls',
            os.path.join(output_dir, "index.m3u8")
        ]

        try:
            print(f"Starting FFmpeg for {rtsp_url} -> {output_dir}")
            with open(log_file, "w") as f:
                process = subprocess.Popen(cmd, stdout=f, stderr=f)
                process.wait()  # Wait for FFmpeg to exit before restarting
        except Exception as e:
            print(f"FFmpeg crashed: {e}")

        print("Restarting FFmpeg in 5 seconds...")
        time.sleep(5)  # Wait before restarting