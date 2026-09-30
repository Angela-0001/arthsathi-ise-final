"""
BLEU evaluation: fine-tuned model vs. base IndicTrans2 vs. commercial API.

Usage:
    python ml/evaluate_bleu.py --test_path ml/data/test_legal.jsonl
"""
import argparse, json
from pathlib import Path
from sacrebleu.metrics import BLEU

bleu = BLEU()


def load_test(path: str):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def evaluate_model(model_fn, test_data) -> float:
    refs = [[ex["tgt"] for ex in test_data]]
    hyps = [model_fn(ex["src"], ex["src_lang"], ex["tgt_lang"]) for ex in test_data]
    return bleu.corpus_score(hyps, refs).score


def main(args):
    test_data = load_test(args.test_path)

    # --- Fine-tuned model ---
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from peft import PeftModel
    import torch

    tok = AutoTokenizer.from_pretrained("ai4bharat/indictrans2-en-indic-1B", trust_remote_code=True)
    base = AutoModelForSeq2SeqLM.from_pretrained("ai4bharat/indictrans2-en-indic-1B", trust_remote_code=True)
    ft_model = PeftModel.from_pretrained(base, "ml/checkpoints/indictrans2-finetuned").eval()

    def ft_translate(src, src_lang, tgt_lang):
        inputs = tok(f"<2{tgt_lang}> {src}", return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            out = ft_model.generate(**inputs, max_new_tokens=256)
        return tok.decode(out[0], skip_special_tokens=True)

    def base_translate(src, src_lang, tgt_lang):
        inputs = tok(f"<2{tgt_lang}> {src}", return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            out = base.generate(**inputs, max_new_tokens=256)
        return tok.decode(out[0], skip_special_tokens=True)

    ft_bleu = evaluate_model(ft_translate, test_data)
    base_bleu = evaluate_model(base_translate, test_data)

    print(f"Fine-tuned BLEU : {ft_bleu:.2f}")
    print(f"Base model BLEU : {base_bleu:.2f}")
    print(f"Delta           : {ft_bleu - base_bleu:+.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_path", default="ml/data/test_legal.jsonl")
    main(parser.parse_args())
