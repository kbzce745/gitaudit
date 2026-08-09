# [AutoDL - Llama 3 8B LoRA SFT Trainer]
# Prerequisites: pip install unsloth trl transformers

import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# 1. Load Base Model (Llama 3 8B Instruct)
max_seq_length = 2048 
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-8b-Instruct-bnb-4bit",
    max_seq_length = max_seq_length,
    dtype = None,
    load_in_4bit = True,
)

# 2. Add LoRA Adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 16, 
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
)

# 3. Data Formatting
alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input, output in zip(instructions, inputs, outputs):
        text = alpaca_prompt.format(instruction, input, output)
        texts.append(text)
    return { "text" : texts, }

# Load the dataset we generated
# Make sure to upload gitaudit_sft_dataset.jsonl to the same directory in AutoDL
dataset = load_dataset("json", data_files="gitaudit_sft_dataset.jsonl", split="train")
dataset = dataset.map(formatting_prompts_func, batched = True,)

# 4. Training
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60,
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
    ),
)

print("Starting Fine-tuning...")
trainer_stats = trainer.train()

# 5. Save the fine-tuned LoRA weights
print("Saving the model...")
model.save_pretrained("lora_model")
tokenizer.save_pretrained("lora_model")

print("Saving to GGUF for Ollama (this may take a few minutes)...")
model.save_pretrained_gguf("gitaudit_model", tokenizer, quantization_method = "q4_k_m")
print("Training complete! Please download the 'gitaudit_model' folder/GGUF file back to your local PC.")
