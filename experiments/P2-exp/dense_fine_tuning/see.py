data = [
    {'role': 'user', 'content': [
            {'type': 'text', 'text': '<video>\nThis video segment is a part of a long educational video on Database Management: Mapping EER Model Constructs to Relational Schemas\nBegining Clip: The video begins with the instructor setting up for the lecture, preparing to discuss the mapping of EER model constructs to relations.\n\nCurrent Segment Transcript: "Okay, hello, can you hear my voice? Yes, ma\'am. Okay, so let\'s start. So today we will continue chapter seven. So we finished from step one to step seven, which included all the different components of an ER diagram. So today we will look at..."\n\nUser Query: Based on the provided context, I need you to do two things for this video segment: \n1. Provide a detailed analysis of the visual information and the educational concept being taught.\n2. Pinpoint the exact start and end times for this specific segment.'
            },
            {'type': 'video', 'path': 'videos/000_Pi1-b50VHB8.mp4'
            }
        ]
    },
    {'role': 'assistant', 'content': [
            {'type': 'text', 'text': "Here is the analysis and timing for the requested segment:\n\n**Timestamp:** [START: 00:00:00] [END: 00:00:30]\n\n**Analysis:** After confirming the audio is working, the instructor begins the lecture on mapping EER models to relations. They recap that steps one to seven for ER diagrams have been covered and introduce today's topic, which is Step 8: Options for Mapping Specialization or Generalization, as shown on the slide. The instructor then switches to a Jamboard to explain the first option, 8A."
            }
        ]
    }
]
print(type(data))