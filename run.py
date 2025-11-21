# from edu_cut.core.orchestrator import Orchestrator
from edu_cut.preproc.pre_processor import PreProcessor

# from test.viz.visualizer import Visualizer

# First just initialize the PreProcessor object to make the store
# if vidoe is already downloaded just put it on the video folder 'yt_id.mp4'
# Then download the transcript and rename it as pk_transcript.csv and put it on the subtitle folder
# Then run the other functions

YT_ID = "r_O-UjZZ744"

ids = [
    "YYNXFsUutbM",
    "wxBG5Ei7a_w",
    "ES6W4_bXvro",
    "i31yX84EgPE",
    "r_O-UjZZ744",
    "ig0QZxtj3j8",
    "jxrGodnopHo",
    "OMGPvW8TBHc",
]

# https://www.youtube.com/watch?v=ig0QZxtj3j8
# https://www.youtube.com/watch?v=r_O-UjZZ744
# =======PreProcess========
for id in ids:
    p = PreProcessor(id)
    # p.download_video()
    # print("Video downloaded ========================================================")
    p.process_subtitle()
    print("Subtitle processed ========================================================")
    p.segment_timestamps()
    print("SEGMENTED timestamps ======================================================")
    p.video_cut()
    print("VIDEO CUT ======================================================")
    p.frame_sample()
    print("FRAME SAMPLE ======================================================")
    p.merge_frame_transcript()

# model = [
#     "gemma-3-4b-it-BF16.gguf",
#     "InternVL3_5-8B-q6_k.gguf",
#     "Qwen3-4B-Thinking-2507-F16.gguf",
#     "Qwen3-VL-4B-Thinking-BF16.gguf",
#     "InternVL3_5-8B-q6_k.gguf",
#     "gpt-oss-20b-F16.gguf",
# ]
# # =======Core Video analysis========
# o = Orchestrator(YT_ID, model[3])
# o.get_video_topic()
# o.get_video_description()
# o.get_irrelevant()

# # =======Result Visualization========
# test = Visualizer(YT_ID)
# test.clean_classified_response(reasoning=False)
