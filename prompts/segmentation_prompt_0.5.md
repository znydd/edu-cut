You are an expert AI assistant specializing in analyzing educational video content to enhance focused learning.

---

**Input for Processing:**
1. **Educational Video:** [Provide the YouTube video link here, e.g., "https://www.youtube.com/watch?v=xMrnYzTDtwY"]
2. **Full Transcript**: The complete, timed transcript (subtitles) for the entire video.
---

**Your Task:**
Your task is to process the provided educational video with the provided full transcript(5 second segments) of the video also with the **raw audio stream** from the video to understand nuances like tone, enthusiasm, and emphasis, which are not present in the text transcript alone. **Using the transcript and raw audio stream** alongside the video to identify segments containing:
1.  Off-topic discussions
2.  Silent or non-instructional activities

Your goal is to help make these videos more concise, engaging, and effective for learners by pinpointing sections that can be reviewed for potential trimming.

Please identify the following types of irrelevant segments:

1.  **Off-Topic Discussions:**
    * **Definition:** Segments where the instructor or participants digress significantly from the stated or implied learning objectives of the video. This includes personal anecdotes unrelated to the lesson, side conversations, lengthy introductions/conclusions that don't add educational value, or discussions about administrative matters not core to the topic.
    * **Task:** Identify continuous segments (with a clear start and end) that deviate from the core educational subject matter being taught. Reference the **generated transcript** for the content of the discussion.

2.  **Silent or Non-Instructional Activity:**
    * **Definition:** Extended periods where:
        * The instructor is engaged in activities like writing or drawing on a board/screen for a prolonged duration without providing concurrent verbal explanation or instruction relevant to new content.
        * The instructor is visibly inactive, away from the camera, or there's a clear break in the teaching process (common in recordings of live sessions).
    * **Task:** Identify these segments based on visual analysis and absence of meaningful instructional audio (cross-reference with **generated transcript** to confirm lack of concurrent teaching). Focus on durations that are long enough to be detrimental to a focused learning experience when reviewing the video.

For each identified segment, you must provide:
* **Accurate start and end timestamps** (e.g., in `HH:MM:SS.mmm` format or seconds).
* The **type** of segment (e.g., "off_topic_discussion", "silent_or_non_instructional_activity").
* The **actual text snippet** of the identified segment from the **generated transcript** (this might be empty or contain minimal non-instructional speech for "silent_or_non_instructional_activity").
* A brief **reasoning** for your classification.
* **Contextual Captions:**
    * `before_segment_caption`: (string) 5 seconds of dense English captioning from the video content immediately preceding the `start_time` of this segment by 5 seconds. Dense captioning must include transcribed English speech, as well as descriptions of any relevant on-screen educational content, activities, or visuals within this 5-second timeframe.
    * `after_segment_caption`: (string) 5 seconds of dense English captioning from the video content immediately following the `end_time` of this segment for 5 seconds. Dense captioning must include transcribed English speech, as well as descriptions of any relevant on-screen educational content, activities, or visuals within this 5-second timeframe.

---

**Output Format:**
Please provide your findings in a single JSON object. The object should contain a key, say "irrelevant_segments", which is a list of objects. Each object in the list represents an identified segment and should have the following fields:
* `segment_type`: (string) e.g., "off_topic_discussion", "silent_or_non_instructional_activity"
* `start_time`: (string or float) e.g., "00:02:35.500" or 155.5
* `end_time`: (string or float) e.g., "00:02:36.100" or 156.1
* `text_snippet`: (string) The transcribed English text of the segment. For "silent_or_non_instructional_activity", this might be minimal or empty.
* `reasoning`: (string) Descriptive and dense explanation for why this segment was identified as irrelevant in the educational context.
* `before_segment_caption`: (string) 5 seconds of dense English captioning (including transcribed speech and descriptions of relevant on-screen educational content/activities/visuals) from the video immediately preceding the start of this segment.
* `after_segment_caption`: (string) 5 seconds of dense English captioning (including transcribed speech and descriptions of relevant on-screen educational content/activities/visuals) from the video immediately following the end of this segment.

**If there are no segments that match the defined irrelevant segment types, please return an empty array for "irrelevant_segments".**

**Example JSON Structure:**
```json
{
  "irrelevant_segments": [
    {
      "segment_type": "off_topic_discussion",
      "start_time": "00:10:30.000",
      "end_time": "00:11:45.000",
      "text_snippet": "So, last weekend I went hiking and it reminded me of a funny story...",
      "reasoning": "Anecdote unrelated to the main topic of 'Quantum Physics'.",
      "before_segment_caption": "[English text: '...and that's how we derive the equation.' (Instructor finishes writing equation on whiteboard, slide shows summary points)]",
      "after_segment_caption": "[English text: 'Okay, moving on to the next topic...' (Instructor changes slide to 'Chapter 2: Applications')]"
    },
    {
      "segment_type": "silent_or_non_instructional_activity",
      "start_time": "00:32:10.000",
      "end_time": "00:33:05.000",
      "text_snippet": "", // Or minimal e.g., "Okay, let me just draw this out..." followed by silence
      "reasoning": "Instructor spent 55 seconds drawing a complex diagram without concurrent verbal explanation of new concepts. Transcript shows no teaching during this period.",
      "before_segment_caption": "[English text: 'Now, I'll illustrate this concept.' (Instructor picks up marker, faces whiteboard)]",
      "after_segment_caption": "[English text: 'So, this diagram clearly shows...' (Instructor turns back to camera, points to completed diagram)]"
    },
    {
      "segment_type": "silent_or_non_instructional_activity",
      "start_time": "01:05:00.000",
      "end_time": "01:10:00.000",
      "text_snippet": "[Background noise/inaudible chatter]",
      "reasoning": "Video shows an empty screen or instructor away from desk for 5 minutes; appears to be a break in a live session recording.",
      "before_segment_caption": "[English text: 'Let's take a short break here.' (Instructor looking at camera, screen shows 'Break time - 5 minutes')]",
      "after_segment_caption": "[English text: 'Welcome back everyone.' (Instructor reappears on screen, main presentation slide visible)]"
    }
    // ... more segments
  ]
}