import numpy as np
import torch
import os
import torchvision.transforms as T
from decord import VideoReader, cpu
from PIL import Image
from torchvision.transforms.functional import InterpolationMode
from transformers import AutoModel, AutoTokenizer
from create_prompt import create_prompt
from vector_pipeline import Vector_store

class VLM:
    def __init__(self):
        # transforming images or video frames into normalized tensors
        self.IMAGENET_MEAN = (0.485, 0.456, 0.406)
        self.IMAGENET_STD = (0.229, 0.224, 0.225)

    def build_transform(self, input_size):
        MEAN, STD = self.IMAGENET_MEAN, self.IMAGENET_STD
        transform = T.Compose([
            T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
            T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(mean=MEAN, std=STD)
        ])
        return transform

    def find_closest_aspect_ratio(self, aspect_ratio, target_ratios, width, height, image_size):
        best_ratio_diff = float('inf')
        best_ratio = (1, 1)
        area = width * height
        for ratio in target_ratios:
            target_aspect_ratio = ratio[0] / ratio[1]
            ratio_diff = abs(aspect_ratio - target_aspect_ratio)
            if ratio_diff < best_ratio_diff:
                best_ratio_diff = ratio_diff
                best_ratio = ratio
            elif ratio_diff == best_ratio_diff:
                if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                    best_ratio = ratio
        return best_ratio

    def dynamic_preprocess(self, image, min_num=1, max_num=12, image_size=448, use_thumbnail=False):
        orig_width, orig_height = image.size
        aspect_ratio = orig_width / orig_height

        # calculate the existing image aspect ratio
        target_ratios = set(
            (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
            i * j <= max_num and i * j >= min_num)
        target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

        # find the closest aspect ratio to the target
        target_aspect_ratio = self.find_closest_aspect_ratio(
            aspect_ratio, target_ratios, orig_width, orig_height, image_size)

        # calculate the target width and height
        target_width = image_size * target_aspect_ratio[0]
        target_height = image_size * target_aspect_ratio[1]
        blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

        # resize the image
        resized_img = image.resize((target_width, target_height))
        processed_images = []
        for i in range(blocks):
            box = (
                (i % (target_width // image_size)) * image_size,
                (i // (target_width // image_size)) * image_size,
                ((i % (target_width // image_size)) + 1) * image_size,
                ((i // (target_width // image_size)) + 1) * image_size
            )
            # split the image
            split_img = resized_img.crop(box)
            processed_images.append(split_img)
        assert len(processed_images) == blocks
        if use_thumbnail and len(processed_images) != 1:
            thumbnail_img = image.resize((image_size, image_size))
            processed_images.append(thumbnail_img)
        return processed_images
        
    def load_model(self):
        path = './pretrained/InternVL2_5-1B'
        model = AutoModel.from_pretrained(
            path,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            use_flash_attn=True,
            trust_remote_code=True).eval().cuda()
        tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True, use_fast=False, attn_implementations="flash_attention2")
        return model, tokenizer

    def get_index(self, bound, fps, max_frame, first_idx=0, num_segments=32):
        if bound:
            start, end = bound[0], bound[1]
        else:
            start, end = -100000, 100000
        start_idx = max(first_idx, round(start * fps))
        end_idx = min(round(end * fps), max_frame)
        seg_size = float(end_idx - start_idx) / num_segments
        frame_indices = np.array([
            int(start_idx + (seg_size / 2) + np.round(seg_size * idx))
            for idx in range(num_segments)
        ])
        return frame_indices

    def load_video(self, video_path, bound=None, input_size=448, max_num=1, num_segments=32):
        vr = VideoReader(video_path, ctx=cpu(0), num_threads=1)
        max_frame = len(vr) - 1
        fps = float(vr.get_avg_fps())

        pixel_values_list, num_patches_list = [], []
        transform = self.build_transform(input_size=input_size)
        frame_indices = self.get_index(bound, fps, max_frame, first_idx=0, num_segments=num_segments)
        for frame_index in frame_indices:
            img = Image.fromarray(vr[frame_index].asnumpy()).convert('RGB')
            img = self.dynamic_preprocess(img, image_size=input_size, use_thumbnail=True, max_num=max_num)
            pixel_values = [transform(tile) for tile in img]
            pixel_values = torch.stack(pixel_values)
            num_patches_list.append(pixel_values.shape[0])
            pixel_values_list.append(pixel_values)
        pixel_values = torch.cat(pixel_values_list)
        return pixel_values, num_patches_list

    def inference(self, video_path="./media/back_flip.mp4"):
        generation_config = dict(max_new_tokens=1024, do_sample=False)
        # video_path = './media/back_flip.mp4'
        # pixel_values, num_patches_list = self.load_video(video_path, num_segments=8, max_num=1)
        # pixel_values = pixel_values.to(torch.bfloat16).cuda()
        # video_prefix = ''.join([f'Frame{i+1}: <image>\n' for i in range(len(num_patches_list))])
        model, tokenizer = self.load_model()
        vctr_store = Vector_store()

        # question = video_prefix + 'Describe all the activities on this video like jumping, back flip, dancing etc. Don\'t only describe frames insted describe overall description, activity and dynamic movement. Don\'t repeat.'
        #question = video_prefix + prompt
        # Frame1: <image>\nFrame2: <image>\n...\nFrame8: <image>\n{question}
        # response, history = model.chat(tokenizer, pixel_values, question+" Don\'t repeat", generation_config,
        #                                num_patches_list=num_patches_list, history=None, return_history=True)

        # print(f'User: {question}\nAssistant: {response}')
        # print(doc_embeddings)
        all_output_path = os.path.join('./media', "all_clip_outputs.txt")
        
        vid_topic = "Programming Design pattern"
        vid_length = 663
        prev_clip_out = "No previous clip just started"
        clip_range = (0, 10)
        video_path = "./media/clips"
        for i in range(23):

            clip_id = f"clip_{i:03d}"
            prev_clip_range = "No previous clip range just started" if i == 0 else clip_range
            if i > 0:
                s = clip_range[1]-2
                clip_range = (s, s+10)#(16, 26)
            with open(video_path+f"/{clip_id}.txt", "r", encoding="utf-8") as f:
                captions= f.read().strip()
            video_path_i= video_path+f"/{clip_id}.mp4"
            
            pixel_values, num_patches_list = self.load_video(video_path_i, num_segments=12, max_num=1)
            pixel_values = pixel_values.to(torch.bfloat16).cuda()
            video_prefix = ''.join([f'Frame{i+1}: <image>\n' for i in range(len(num_patches_list))])
            prompt = create_prompt(vid_length, clip_range, prev_clip_range, prev_clip_out, vid_topic, video_prefix, captions)
            # print(prompt)
            # model, tokenizer = self.load_model()
            response = model.chat(tokenizer, pixel_values, prompt+". Don\'t repeat", generation_config,
                                       num_patches_list=num_patches_list, history=None, return_history=False)
            # print(response)
            vctr_store.store(response, clip_range, clip_id)
            with open(all_output_path, "a", encoding="utf-8") as out_f:
                out_f.write(f"\n\n=== Clip: {clip_id} ({clip_range}) ===\n")
                out_f.write(response)
                out_f.write("\n" + "=" * 60 + "\n")

            prev_clip_out = response

        vctr_store.query()

obj = VLM()
obj.inference()