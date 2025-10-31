from edu_cut.core.orchestrator import Orchestrator

# First just initialize the PreProcessor object to make the store
# Then download the transcript and rename it as pk_transcript.csv and put it on the subtitle folder
# Then run the other functions

yt_id = "wxBG5Ei7a_w"
# p = PreProcessor(yt_id)
# p.process_subtitle()
# print("Subtitle processed ========================================================")
# p.segment_timestamps()
# print("SEGMENTED timestamps ======================================================")
# p.video_cut()
# print("VIDEO CUT ======================================================")
# p.frame_sample()
# print("FRAME SAMPLE ======================================================")
# p.merge_frame_transcript()

model = [
    "gemma-3-4b-it-BF16.gguf",
    "InternVL3_5-8B-q6_k.gguf",
    "Qwen3-4B-Thinking-2507-F16.gguf",
    "InternVL3_5-8B-q6_k.gguf",
]
o = Orchestrator(yt_id, model[3])
o.get_video_topic()
o.get_video_description()
