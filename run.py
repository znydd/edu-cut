import os

from edu_cut.core.orchestrator import Orchestrator
from test.viz.visualizer import Visualizer

# First just initialize the PreProcessor object to make the store
# if vidoe is already downloaded just put it on the video folder 'yt_id.mp4'
# Then download the transcript and rename it as pk_transcript.csv and put it on the subtitle folder
# Then run the other functions

# https://www.youtube.com/watch?v=iLCT0i-lCsw
# https://www.youtube.com/watch?v=ZujpN1B9bz0 (till 15:00 mins)
# https://www.youtube.com/watch?v=9t2odwJiHOw (till 9:25 mins)
# https://www.youtube.com/watch?v=HwiaWygjups (till 10:00 mins)

# https://www.youtube.com/watch?v=3PL2DxXv5u0 (10:35)
# https://www.youtube.com/watch?v=yD1Y1chp5R4 (12:00)
# https://www.youtube.com/watch?v=SKZn2DBQuHs (12:30)

# ids = ["iLCT0i-lCsw", "ZujpN1B9bz0", "9t2odwJiHOw", "HwiaWygjups", "3PL2DxXv5u0"] #Indian Live Lectures


# ids = ["yD1Y1chp5R4", "SKZn2DBQuHs"]  # CS50 Lectures
# =======Preprocess========
# for yt_ID in ids:
#     p = PreProcessor(yt_ID)
#     print("Store Created for yt_ID: ", yt_ID)
#     #     # p.download_video()
#     #     # print("video downloaded ========================================================")
#     p.process_subtitle()
#     print("subtitle processed ========================================================")
#     p.segment_timestamps()
#     print("segmented timestamps ======================================================")
#     p.video_cut()
#     print("video cut ======================================================")
#     p.frame_sample()
#     print("frame sample ======================================================")
#     p.merge_frame_transcript()
#     print(
#         "frame transcript merged ======================================================"
#     )

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
    ids = []
    o = Orchestrator("r_O-UjZZ744", model["7"])
    # o.get_video_topic(
    #     "1"
    # )  # For classification use the v2 prompt to get more detailed video topic
    # o.get_video_description()
    o.get_video_topic(
        "2"
    )  # For classification use the v2 prompt to get more detailed video topic
    o.get_irrelevant()

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
    # benchmark_dir = "/home/znyd/hacking/edu-cut/Benchmark/vanila_qwen3_4B_instruct_2507"
    # benchmark_dir = (
    #     "/home/znyd/hacking/edu-cut/Benchmark/vanila_qwen3_4B_instruct_2507_indian_live"
    # )
    # benchmark_dir = (
    #     "/home/znyd/hacking/edu-cut/Benchmark/vanila_qwen3_4B_instruct_2507_new_vid"
    # )
    # benchmark_dir = (
    #     "/home/znyd/hacking/edu-cut/Benchmark/vanila_qwen3_4B_instruct_2507_last_2"
    # )
    # benchmark_dir = "/home/znyd/hacking/edu-cut/Benchmark/strict_prompt"
    # file_path = "/home/znyd/hacking/edu-cut/store/ugzN7W7q2Gk/responses/ugzN7W7q2Gk.csv"
    # file_path = "/home/znyd/hacking/edu-cut/store/M_rIWVO14tA/responses/M_rIWVO14tA.csv"
    # file_path = "/home/znyd/hacking/edu-cut/Benchmark/strict_prompt/OMGPvW8TBHc.csv"

    ids = [
        "i31yX84EgPE",
        "M_rIWVO14tA",
        "ZujpN1B9bz0",
        "OMGPvW8TBHc",
        "YYNXFsUutbM",
        "ES6W4_bXvro",
        "ugzN7W7q2Gk",
        "HwiaWygjups",
        "YA1OdkiHJBY",
        "ig0QZxtj3j8",
        "3PL2DxXv5u0",
        "jxrGodnopHo",
        "wxBG5Ei7a_w",
        "r_O-UjZZ744",
        "yD1Y1chp5R4",
        "DlWTTrHa8bI",
        "SKZn2DBQuHs",
        "9t2odwJiHOw",
        "iLCT0i-lCsw",
        "LdPAkUXKBGI",
    ]
    # id_fx = ["wxBG5Ei7a_w","i31yX84EgPE","YA1OdkiHJBY","YYNXFsUutbM"]
    benchmark_dir = "/home/znyd/hacking/edu-cut/Benchmark/total_20_vid_pred/predicted"
    file_path = os.path.join(benchmark_dir, f"{ids[5]}.csv")

    # Group numbers (# column) to exclude from the final 2D list output
    # exclude_groups = [2, 7, 9, 17, 23, 25, 32, 40, 41, 44, 53]  # e.g., [1, 3, 5] to exclude groups #1, #3, #5
    exclude_groups = []

    if os.path.exists(file_path):
        test = Visualizer(direct_path=file_path)
        test.clean_classified_response(reasoning=True, exclude_groups=exclude_groups)
    else:
        print(f"Benchmark file not found: {file_path}")
        # Fallback to default behavior if needed:
        # test = Visualizer(YT_ID)
        # test.clean_classified_response(reasoning=True)


# First 8 videos

# "yynxfsuutbm",
# "wxbg5ei7a_w",
# "es6w4_bxvro",
# "i31yx84egpe",
# "r_o-ujzz744",
# "ig0qzxtj3j8",
# "jxrgodnopho",
# "omgpvw8tbhc",

# https://www.youtube.com/watch?v=ig0QZxtj3j8
# https://www.youtube.com/watch?v=r_O-UjZZ744

# "frame_00082.png",
# "frame_00083.png"
# "frame_00077.png",
# "frame_00076.png",

# 2nd 5 videos
# ids = [
#     "YA1OdkiHJBY",
#     "DlWTTrHa8bI",
#     "LdPAkUXKBGI",
#     "M_rIWVO14tA",
#     "ugzN7W7q2Gk",
# ]

# conference: https://www.youtube.com/watch?v=ugzN7W7q2Gk

# https://www.youtube.com/watch?v=YA1OdkiHJBY
# https://www.youtube.com/watch?v=DlWTTrHa8bI
# https://www.youtube.com/watch?v=LdPAkUXKBGI
# https://www.youtube.com/watch?v=M_rIWVO14tA
