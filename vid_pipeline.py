from decord import VideoReader, cpu, gpu
import srt, cv2, os
from datetime import timedelta

def chunk_video_and_subs(
        video_path: str,
        srt_path: str,
        output_dir: str,
        clip_len_sec: int = 10,
        overlap_sec: int = 2,
        use_gpu: bool = False):
    """
    Cut a video into overlapping clips and dump matching subtitle text per clip.

    Each clip is       output_dir/clip_000.mp4
    Its subtitles are   output_dir/clip_000.txt   (plain text)
    """
    # ----------- load video --------------------------------------------------
    vr = VideoReader(video_path, ctx=gpu(0) if use_gpu else cpu(0))
    fps           = vr.get_avg_fps()
    total_frames  = len(vr)
    duration_sec  = total_frames / fps

    # ----------- compute windows --------------------------------------------
    step = clip_len_sec - overlap_sec
    start_times = list(range(0, int(duration_sec - overlap_sec + 1e-3), step))

    # ----------- load subtitles ---------------------------------------------
    with open(srt_path, "r", encoding="utf-8") as f:
        subs_all = list(srt.parse(f.read()))

    os.makedirs(output_dir, exist_ok=True)

    # ----------- iterate -----------------------------------------------------
    for idx, start in enumerate(start_times):
        clip_start  = timedelta(seconds=start)
        clip_end    = timedelta(seconds=start + clip_len_sec)

        # Slice video ---------------------------------------------------------
        start_frame = int(start * fps)
        end_frame   = int(min(start + clip_len_sec, duration_sec) * fps)

        frames = [vr[i].asnumpy() for i in range(start_frame, end_frame)]
        h, w, _ = frames[0].shape
        out_path = os.path.join(output_dir, f"clip_{idx:03d}.mp4")

        vw = cv2.VideoWriter(
            out_path,
            cv2.VideoWriter_fourcc(*'mp4v'),
            fps, (w, h))

        for fr in frames:
            vw.write(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
        vw.release()

        # Slice subtitles -----------------------------------------------------
        lines = []
        for cue in subs_all:
            if cue.end   > clip_start and cue.start < clip_end:
                lines.append(cue.content.replace('\n', ' ').strip())

        txt_path = os.path.join(output_dir, f"clip_{idx:03d}.txt")
        with open(txt_path, "w", encoding="utf-8") as t:
            t.write("\n".join(lines))

        print(f"Saved clip {idx:03d}:  {out_path}  +  {txt_path}")

    print(f"\nTotal clips produced: {len(start_times)}")
    return len(start_times)

chunk_video_and_subs(
    video_path = "./media/design_pattern.mp4",
    srt_path   = "./media/design_pattern.srt",
    output_dir = "./media/clips/",
    clip_len_sec = 10,
    overlap_sec  = 2)
