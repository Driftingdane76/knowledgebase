import os
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM

model_id = "microsoft/Florence-2-base"
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch_dtype, trust_remote_code=True).to(device)
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

img_path = os.path.join(os.path.dirname(__file__), 'test_htmls', 'mock_crm_dashboard.png')
image = Image.open(img_path).convert("RGB")
width, height = image.size

prompt = "<OCR_WITH_REGION>"
inputs = processor(text=prompt, images=image, return_tensors="pt").to(device, torch_dtype)

with torch.no_grad():
    generated_ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=1024,
        num_beams=3,
        do_sample=False
    )

generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
parsed_result = processor.post_process_generation(generated_text, task=prompt, image_size=(width, height))
ocr_data = parsed_result.get("<OCR_WITH_REGION>", {})

print("LABELS / TOKENS:")
for idx, label in enumerate(ocr_data.get("labels", [])):
    print(f"{idx}: '{label}'")
