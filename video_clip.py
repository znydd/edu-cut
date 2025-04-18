from decord import VideoReader, cpu, gpu
import cv2
import os

def trim_video_with_overlap(video_path, output_dir, clip_length=10, overlap=2):
    vr = VideoReader(video_path, ctx=gpu(0))
    total_frames = len(vr)
    fps = vr.get_avg_fps()
    duration = total_frames / fps

    print(f"Video Duration: {duration:.2f}s, FPS: {fps:.2f}, Total Frames: {total_frames}")

    step = clip_length - overlap
    start_times = list(range(0, int(duration - overlap), step))
    print(start_times)

    os.makedirs(output_dir, exist_ok=True)

    for i, start_sec in enumerate(start_times):
        end_sec = min(start_sec + clip_length, duration)
        start_frame = int(start_sec * fps)
        end_frame = int(end_sec * fps)

        clip_frames = [vr[i].asnumpy() for i in range(start_frame, end_frame)]
        # Get frame size
        height, width, _ = clip_frames[0].shape

        # Define output video path
        output_path = os.path.join(output_dir, f"clip_{i:03d}.mp4")

        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        for frame in clip_frames:
            out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # Convert RGB (Decord) to BGR (OpenCV)

        out.release()
        print(f"Saved: {output_path} ({start_sec:.2f}s - {end_sec:.2f}s)")

    print(f"\nTotal clips saved: {len(start_times)}")
    return len(start_times)

# Example usage
video_path = "./media/speed_back_flip.mp4"
output_dir = "./media/clips/"
trim_video_with_overlap(video_path, output_dir, clip_length=10, overlap=2)
