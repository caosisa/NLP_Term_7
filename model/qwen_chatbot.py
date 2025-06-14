# model/qwen_chatbot.py

import json
import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from tqdm import tqdm

MODEL_NAME = "Qwen/Qwen1.5-0.5B-Chat"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 모델 로딩
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, trust_remote_code=True).to(DEVICE)
model.eval()

def generate_answer(prompt, max_new_tokens=100):
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    outputs = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=True, top_p=0.9, temperature=0.8)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return answer.replace(prompt, "").strip()

def main():
    input_path = "./data/test_chat.json"
    output_path = "./outputs/chat_output.json"

    os.makedirs("./outputs", exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    results = []
    for item in tqdm(test_data):
        question = item["user"]
        prompt = f"사용자의 질문: {question}\n챗봇의 답변:"
        answer = generate_answer(prompt)
        results.append({
            "user": question,
            "model": answer
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()