from edu_cut.preproc.pre_processor import PreProcessor


x = PreProcessor("https://www.youtube.com/watch?v=O4bjWrhL4z0")
x.segment_timestamps()
x.frame_sample()
x.merge_frame_transcript()
