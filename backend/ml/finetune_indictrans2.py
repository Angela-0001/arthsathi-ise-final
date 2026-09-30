"""
LoRA fine-tuning of IndicTrans2 on the financial/legal domain corpus.

Usage:
    python ml/finetune_indictrans2.py \
        --data_path ml/data/domain_corpus.jsonl \
        --output_dir ml/checkpoints/indictrans2-finetuned \
        --epochs 3 --batch_size 8
"""
import argparse
import json
from pathlib import Path

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, TaskType
import torch


def load_corpus(path: str) -> Dataset:
    """Load JSONL file with {"src": "...", "tgt": "...", "src_lang": "en", "tgt_lang": "hi"} lines."""
    rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    return Dataset.from_list(rows)


def preprocess(examples, tokenizer, max_length=256):
    tagged_src = [f"<2{tl}> {s}" for s, tl in zip(examples["src"], examples["tgt_lang"])]
    model_inputs = tokenizer(tagged_src, max_length=max_length, truncation=True, padding=True)
    labels = tokenizer(text_target=examples["tgt"], max_length=max_length, truncation=True, padding=True)
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


def main(args):
    print("Loading base model: ai4bharat/indictrans2-en-indic-1B")
    tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indictrans2-en-indic-1B", trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        "ai4bharat/indictrans2-en-indic-1B",
        trust_remote_code=True,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

    # Apply LoRA
    lora_cfg = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj"],
    )
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    dataset = load_corpus(args.data_path)
    dataset = dataset.map(
        lambda ex: preprocess(ex, tokenizer),
        batched=True,
        remove_columns=dataset.column_names,
    )
    split = dataset.train_test_split(test_size=0.1, seed=42)

    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        predict_with_generate=True,
        fp16=torch.cuda.is_available(),
        logging_steps=50,
        load_best_model_at_end=True,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        tokenizer=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
    )

    trainer.train()
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"Fine-tuned model saved to {args.output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", required=True)
    parser.add_argument("--output_dir", default="ml/checkpoints/indictrans2-finetuned")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=8)
    main(parser.parse_args())
