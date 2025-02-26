import cv2, time , os

os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;http'

def stream_rtsp(rtsp_url, max_attempts=10, delay=3):
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("Error: Couldn't open the RTSP stream.")
        return

    # Wait for the first frame (try multiple times)
    print("Waiting for the stream to initialize...")
    attempts = 0
    while attempts < max_attempts:
        ret, frame = cap.read()
        if ret:
            print("Stream initialized successfully.")
            break
        print(f"Retrying... ({attempts + 1}/{max_attempts})")
        time.sleep(delay)
        attempts += 1
    else:
        print("Error: Failed to retrieve frame after multiple attempts.")
        cap.release()
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Lost connection or failed to retrieve frame.")
            break

        cv2.imshow('RTSP Stream', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    rtsp_url = "rtsp://admin:12345@192.168.0.105:554/1"
    stream_rtsp(rtsp_url)