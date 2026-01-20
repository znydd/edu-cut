from edu_cut.core.orchestrator import Orchestrator
from edu_cut.preproc.pre_processor import PreProcessor
from test.viz.visualizer import Visualizer
import os

# First just initialize the PreProcessor object to make the store
# if vidoe is already downloaded just put it on the video folder 'yt_id.mp4'
# Then download the transcript and rename it as pk_transcript.csv and put it on the subtitle folder
# Then run the other functions

# "YYNXFsUutbM",  # <-- Bug
# "ES6W4_bXvro",  #
# "r_O-UjZZ744",  #
# "ig0QZxtj3j8",  #  last segment. process it from scratch

ids = [
    "YYNXFsUutbM",  # Bug
    "wxBG5Ei7a_w",  # Done
    "ES6W4_bXvro",  # Done
    "i31yX84EgPE",  # Done
    "r_O-UjZZ744",  # Done
    "ig0QZxtj3j8",  # Done
    "jxrGodnopHo",  # Done
    "OMGPvW8TBHc",
]

YT_ID = "YYNXFsUutbM"
# https://www.youtube.com/watch?v=ig0QZxtj3j8
# https://www.youtube.com/watch?v=r_O-UjZZ744
# =======PreProcess========
# for id in ids:
# p = PreProcessor(YT_ID)
# p.download_video()
# print("Video downloaded ========================================================")
# p.process_subtitle()
# print("Subtitle processed ========================================================")
# p.segment_timestamps()
# print("SEGMENTED timestamps ======================================================")
# p.video_cut()
# print("VIDEO CUT ======================================================")
# p.frame_sample()
# print("FRAME SAMPLE ======================================================")
# p.merge_frame_transcript()

VIZ = True
CLASS = False

model = {
    "0": "gemma-3-4b-it-BF16.gguf",
    "1": "InternVL3_5-8B-q6_k.gguf",
    "2": "Qwen3-4B-Thinking-2507-F16.gguf",
    "3": "Qwen3-VL-4B-Thinking-BF16.gguf",
    "4": "InternVL3_5-8B-q6_k.gguf",
    "5": "gpt-oss-20b-F16.gguf",
    "6": "Qwen3VL-4B-Instruct-F16.gguf",
    "7": "Qwen3-4B-Instruct-2507-F16.gguf",
    "8": "gemma-3-12b-it-q4_0.gguf",
    "9": "Qwen3VL-4B-Instruct-Q8_0.gguf",
}
# =======Core Video analysis========
if CLASS:
    o = Orchestrator(YT_ID, model["9"])
    # o.get_video_topic()
    o.get_video_description()
    # o.get_irrelevant()

# # =======Result Visualization========
id_table = {
   "0": "YYNXFsUutbM", 
   "1": "wxBG5Ei7a_w", 
   "2": "ES6W4_bXvro", 
   "3": "i31yX84EgPE", 
   "4": "r_O-UjZZ744", 
   "5": "ig0QZxtj3j8", 
   "6": "jxrGodnopHo", 
   "7": "OMGPvW8TBHc",
}

if VIZ:
    benchmark_dir = "/home/znyd/hacking/edu-cut/Benchmark/vanila_qwen3_4B_instruct_2507"
    file_path = os.path.join(benchmark_dir, f"{id_table['2']}.csv")
    
    if os.path.exists(file_path):
        test = Visualizer(direct_path=file_path)
        test.clean_classified_response(reasoning=True)
    else:
        print(f"Benchmark file not found: {file_path}")
        # Fallback to default behavior if needed:
        # test = Visualizer(YT_ID)
        # test.clean_classified_response(reasoning=True)
