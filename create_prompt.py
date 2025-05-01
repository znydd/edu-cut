def create_prompt(vid_length, clip_range, prev_clip_range, prev_clip_out, vid_topic, frames, captions):
    prompt = f'''
    You are a multimodal video analyst specializing in educational content.

    ## Context
    This is an educational video, {vid_length} seconds long, broken into chunks of 10 seconds each.
    Your job is to analyze every visual, textual detail from each 10-second clip.

    Topic of the full video: {vid_topic} 
    You are now analyzing the segment: {clip_range[0]}s - {clip_range[1]}s 
    Here is the output you previously gave for the previous segment {prev_clip_range[0]}s - {prev_clip_range[1]}s : 
    just use it as context of past 
    {prev_clip_out}

    ## Video Input
    The following are sampled frames from the current 10-second segment:
    {frames}

    ## Captions / ASR
    <captions>
    {captions}
    </captions>

    Your task:
    - Along with video frame focus on the caption also which is 10 second long and aligned with video.
    - The video frames may not seems similer with caption but the on caption must be saying or teaching so be aware of that. 
    - Describe what is happening on the video.
    - Describe exactly what is being taught if any.
    - Describe more whatever is being taught
    - also align the caption with the video
    - Use OCR for text content and use caption text for reasoning and alignment
    - Output should be descriptive so your explaination matches with the actual video then we can use this explaination to search parts on the video through vector databse

    Don't repeat. Be confident.
    '''

    return prompt

# def serve():
#     vid_topic = "Programming Design pattern"
#     prev_clip_out = "No previous clip just started"
#     clip_range = (0, 10)
#     video_path = "./media/clips"
#     for i in range(5):
#         vid_length = 663
#         prev_clip_range = clip_range.copy()
#         if i > 0:
#             s = clip_range[1]-2
#             clip_range = (s, s+10)#(16, 26)
#         with open(video_path+f"/clip_{i:03d}.txt", "r", encoding="utf-8") as f:
#             captions= f.read().strip()
        

#         video_path+f"/clip_{i:03d}.mp4"
#     return
# serve()
    