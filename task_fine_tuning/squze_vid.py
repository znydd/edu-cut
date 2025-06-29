import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os

def compute_ssim_full(img1, img2):
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    score, _ = ssim(img1_gray, img2_gray, full=True)
    return score

def sample_video_to_new_video(input_path, output_dir, ssim_threshold=0.95, diff_threshold=7, target_frames=60, sample_every_n=5):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Cannot open video: {input_path}")
        return

    # Get video info for writer (keep original resolution and codec)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25  # fallback if 0
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    video_name = os.path.splitext(os.path.basename(input_path))[0]
    save_path = os.path.join(output_dir, f"{video_name}.mp4")
    os.makedirs(output_dir, exist_ok=True)
    out_video = cv2.VideoWriter(save_path, fourcc, fps, (width, height))

    success, prev_frame = cap.read()
    if not success:
        print(f"Failed to read {input_path}")
        return

    kept_frames = [prev_frame]
    frame_idx = 1

    while True:
        for _ in range(sample_every_n):
            success, frame = cap.read()
            if not success:
                break
            frame_idx += 1
        if not success:
            break

        diff = cv2.absdiff(prev_frame, frame)
        mean_diff = np.mean(diff)

        # If frames differ enough, check with SSIM
        if mean_diff > diff_threshold:
            score = compute_ssim_full(prev_frame, frame)
            if score < ssim_threshold:
                kept_frames.append(frame)
                prev_frame = frame

    cap.release()

    # Further subsample if too many frames
    if len(kept_frames) > target_frames:
        step = len(kept_frames) // target_frames
        kept_frames = kept_frames[::step]

    # Write frames to new video
    for frame in kept_frames:
        out_video.write(frame)
    out_video.release()

    print(f"Processed {input_path}: new video saved at {save_path} ({len(kept_frames)} frames).")

# --- Batch processing for multiple videos ---
from concurrent.futures import ThreadPoolExecutor, as_completed
import glob

def process_all_videos(input_folder, output_folder, max_workers=4):
    os.makedirs(output_folder, exist_ok=True)
    video_files = glob.glob(os.path.join(input_folder, "*.mp4"))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(sample_video_to_new_video, video_path, output_folder)
            for video_path in video_files
        ]
        for future in as_completed(futures):
            future.result()

if __name__ == "__main__":
    input_folder = "./cropped_vid"
    output_folder = "./sqz_vid"
    process_all_videos(input_folder, output_folder, max_workers=4)
