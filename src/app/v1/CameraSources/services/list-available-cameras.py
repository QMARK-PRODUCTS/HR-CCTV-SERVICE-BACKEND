import cv2, os, time

os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;http'


def detect_rtsp_cameras(base_rtsp_url, max_failures=3, timeout=3):
    available_cameras = []
    consecutive_failures = 0
    channel = 1
    
    while consecutive_failures < max_failures:
        rtsp_url = f"{base_rtsp_url}/{channel}"
        print(f"Checking {rtsp_url}...")

        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        start_time = time.time()
        found = False

        while time.time() - start_time < timeout:
            ret, frame = cap.read()
            if ret:
                print(f"✅ Camera {channel} found: {rtsp_url}")
                available_cameras.append(rtsp_url)
                found = True
                consecutive_failures = 0
                break
            time.sleep(0.2)

        if not found:
            print(f"❌ Camera {channel} not available at {rtsp_url}")
            consecutive_failures += 1
        
        cap.release()
        channel += 1

    return available_cameras

if __name__ == "__main__":
    base_rtsp_url = "rtsp://admin:12345@192.168.0.105:554"
    available_cameras = detect_rtsp_cameras(base_rtsp_url)

    print("\n🎥 Detected RTSP Cameras:")
    for cam in available_cameras:
        print(cam)

    if not available_cameras:
        print("\n❌ No active cameras found.")