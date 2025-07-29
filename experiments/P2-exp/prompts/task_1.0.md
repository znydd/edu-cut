# AI Prompt: Identification of Irrelevant Segments in Educational Videos

You are an expert AI assistant specializing in analyzing educational video content to enhance focused learning.

---

### **Input for Processing:**
* **Educational Video:** `[Provide the YouTube video link here, e.g., "https://www.youtube.com/watch?v=..."]`

---

### **Your Task:**
Your task is to process the provided educational video. **First, generate a comprehensive, timed transcript of the video content. This transcript should be in English.** Then, use this **generated transcript** alongside the video to identify segments containing:
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
* **`start_time` and `end_time` with a 5-second buffer:** After identifying the precise start and end of an irrelevant segment, you must adjust the timestamps for the final output. **Subtract 5 seconds from the segment's actual start time** and **add 5 seconds to its actual end time**. The `start_time` and `end_time` fields in your JSON response must reflect this adjustment. This creates a buffer, making it easier to cut the video. Timestamps should be in `HH:MM:SS.mmm` format or as a float in seconds. If there is no before or after 5 seconds segment then don't include that 5 seconds only the available segments Example: irrelevant segment starting or ending of video.  
* The **`type`** of segment (e.g., "off_topic_discussion", "silent_or_non_instructional_activity").
* The **`text_snippet`** of the identified segment from the **generated transcript**. This snippet must correspond to the **original, un-buffered time range** of the irrelevant content. For "silent\_or\_non\_instructional\_activity", this might be minimal or empty.
* A brief **`reasoning`** for your classification, explaining why the original segment is considered irrelevant.
* **`Contextual Captions`:**
    * `before_segment_caption`: (string) For the 5-second window immediately preceding the **final `start_time`** you provided, give a dense English caption. This caption should be a concise yet comprehensive description integrating the following aspects from that 5-second timeframe:
        * **Scene Description:** Describe primary visual elements on screen (e.g., slide content, diagrams, code on screen, instructor's view), including any key OCR text if visible and relevant.
        * **Activity Context / Environment:** Describe what the instructor is doing (e.g., pointing, writing, typing, demonstrating a physical object) and their interaction with tools or software.
        * **Instructional Content / Key Concept Extraction:** Summarize core educational information from the transcribed English speech within this 5-second window, linking it to the visual elements and instructor actions. Note any key terms, formulas, or concepts briefly introduced or emphasized.
    * `after_segment_caption`: (string) For the 5-second window immediately following the **final `end_time`** you provided, give a dense English caption. This caption should be a concise yet comprehensive description integrating the following aspects from that 5-second timeframe:
        * **Scene Description:** Describe primary visual elements on screen (e.g., slide content, diagrams, code on screen, instructor's view), including any key OCR text if visible and relevant.
        * **Activity Context / Environment:** Describe what the instructor is doing (e.g., pointing, writing, typing, demonstrating a physical object) and their interaction with tools or software.
        * **Instructional Content / Key Concept Extraction:** Summarize core educational information from the transcribed English speech within this 5-second window, linking it to the visual elements and instructor actions. Note any key terms, formulas, or concepts briefly introduced or emphasized.

---

### **Output Format:**
Please provide your findings in a single JSON object. The object should contain a key, say `irrelevant_segments`, which is a list of objects. Each object in the list represents an identified segment and should have the following fields:
* `segment_type`: (string) e.g., "off\_topic\_discussion", "silent\_or\_non\_instructional\_activity"
* `start_time`: (string or float) e.g., "00:02:30.500" or 150.5
* `end_time`: (string or float) e.g., "00:02:41.100" or 161.1
* `text_snippet`: (string) The transcribed English text of the segment. For "silent\_or\_non\_instructional\_activity", this might be minimal or empty.
* `reasoning`: (string) Descriptive and dense explanation for why this segment was identified as irrelevant in the educational context.
* `before_segment_caption`: (string) As defined under "Contextual Captions".
* `after_segment_caption`: (string) As defined under "Contextual Captions".

**If there are no segments that match the defined irrelevant segment types, please return an empty array for `irrelevant_segments`.**

### **Example JSON Structure:**
```json
{
  "irrelevant_segments": [
    {
      "segment_type": "off_topic_discussion",
      "start_time": "00:10:30.000",
      "end_time": "00:11:50.000",
      "text_snippet": "So, last weekend I went hiking and it reminded me of a funny story about my cat getting stuck in a tree, it was quite the adventure trying to get him down...",
      "reasoning": "Extended personal anecdote (1 minute 15 seconds) about a hiking trip and a pet, which is unrelated to the video's main topic of 'Quantum Physics'. The original segment was from 00:10:35.000 to 00:11:45.000.",
      "before_segment_caption": "The instructor is at the whiteboard, having written the equation E=mc^2, which they now circle while stating, '...and that's how we fundamentally derive this core equation in physics,' thus concluding the derivation and emphasizing its importance.",
      "after_segment_caption": "The instructor erases the whiteboard and clicks to a new slide titled 'Chapter 2: Wave-Particle Duality.' They state, 'Alright, with that foundation, let's move on to our next topic: wave-particle duality,' transitioning to the new chapter and introducing this concept."
    },
    {
      "segment_type": "silent_or_non_instructional_activity",
      "start_time": "00:32:05.000",
      "end_time": "00:33:10.000",
      "text_snippet": "// Okay, let me just draw this out carefully... (sound of marker on board)",
      "reasoning": "Instructor spent 55 seconds drawing a complex diagram (Feynman diagram) on the whiteboard without concurrent verbal explanation of new concepts or steps. Original segment was from 00:32:10.000 to 00:33:05.000. Transcript shows minimal speech, unrelated to teaching new material during the drawing.",
      "before_segment_caption": "With the whiteboard partially filled, the instructor faces it and picks up a blue marker, announcing, 'Now, to visualize this interaction, I'll illustrate the complete Feynman diagram,' indicating their intention to draw it to illustrate a concept.",
      "after_segment_caption": "A completed Feynman diagram is now on the whiteboard. The instructor turns back to the camera, points to a specific part of it, and begins to explain, 'So, as you can see in this diagram, the electron and positron annihilate, producing...' focusing on this aspect of the diagram and starting to explain its components."
    }
  ]
}