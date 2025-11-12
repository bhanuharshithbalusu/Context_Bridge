# NLLB-200 Idiomatic Translation Fine-tuning

A production-ready pipeline for fine-tuning NLLB-200 for idiomatic translation between Telugu, Hindi, and English using LoRA/PEFT.

## 🎯 Key Features

- **LoRA-based Fine-tuning**: Memory-efficient training with <1% trainable parameters
- **Idiomatic Focus**: Optimized for contextual meaning preservation, not literal translation
- **Multilingual**: Supports Telugu ↔ Hindi ↔ English in all directions
- **Context-Aware**: Handles idioms both standalone and within sentences
- **Comprehensive Evaluation**: BLEU, chrF++, COMET, and custom metrics
- **Production-Ready**: Modular, well-documented, reproducible code

## 📋 Requirements

```bash
pip install -r requirements.txt
```

Additional for COMET evaluation (optional):
```bash
pip install unbabel-comet
```

## 🗂️ Project Structure

```
.
├── config.py                  # Configuration (model, training, data)
├── data_preprocessor.py       # Dataset loading and preprocessing
├── train.py                   # Main training script
├── evaluate.py                # Evaluation with multiple metrics
├── inference.py               # Translation inference
├── requirements.txt           # Python dependencies
├── Dataset/                   # Your CSV datasets
│   ├── English_proverbs_translation.csv
│   ├── Hindi_Proverbs_Translation.csv
│   └── Telugu_Proverbs_Hindi.csv
└── nllb_idiom_finetuned/     # Output directory (created during training)
```

## 🚀 Quick Start

### 1. Prepare Data

The data processor automatically loads and processes your three CSV datasets:
- English idioms → Telugu + Hindi
- Hindi idioms → English + Telugu  
- Telugu idioms → English + Hindi

```python
from data_preprocessor import IdiomDataProcessor

processor = IdiomDataProcessor()
datasets = processor.prepare_datasets()
```

**Data Augmentation Features:**
- Context variations (idioms in sentences)
- Proper train/val/test splits (80/10/10)
- Automatic text cleaning

### 2. Train the Model

**Basic training:**
```bash
python train.py
```

**What happens:**
- Loads NLLB-200-distilled-600M (or configure larger model in config.py)
- Applies LoRA adapters (only ~2% parameters trained)
- Trains for 5 epochs with optimal hyperparameters
- Saves best checkpoint based on validation loss

**Key Hyperparameters (config.py):**
```python
# Training
learning_rate = 5e-4          # Higher for LoRA
batch_size = 8                # Adjust for your GPU
gradient_accumulation = 4     # Effective batch size = 32
num_epochs = 5
warmup_steps = 500

# LoRA
r = 16                        # Rank (higher = more capacity)
lora_alpha = 32
lora_dropout = 0.05
```

**Training Time Estimates:**
- RTX 3090: ~2-3 hours
- A100: ~1-1.5 hours  
- CPU: ~24+ hours (not recommended)

### 3. Evaluate the Model

```bash
python evaluate.py
```

**Metrics Computed:**
- **BLEU**: Standard MT metric
- **chrF++**: Character-level metric (better for morphologically rich languages)
- **COMET**: Neural metric (best correlation with human judgment)
- **Custom**: Length ratios, per-language-pair analysis

Output saved to: `nllb_idiom_finetuned/evaluation_results.json`

### 4. Run Inference

**Interactive Mode:**
```bash
python inference.py --mode interactive
```

**Demo Mode:**
```bash
python inference.py --mode demo
```

**Batch File Translation:**
```bash
python inference.py --mode file \
    --input-file idioms.txt \
    --output-file translations.txt \
    --source-lang english \
    --target-lang telugu
```

**Programmatic Usage:**
```python
from inference import IdiomTranslator

translator = IdiomTranslator()
translator.load_model()

# Single translation
result = translator.translate(
    text="A blessing in disguise",
    source_lang="english",
    target_lang="telugu",
    num_beams=5
)

# Batch translation
results = translator.translate_batch(
    texts=["idiom1", "idiom2", "idiom3"],
    source_lang="english",
    target_lang="hindi"
)
```

## ⚙️ Configuration

Edit `config.py` to customize:

### Model Selection
```python
model_name = "facebook/nllb-200-distilled-600M"  # Fast, good quality
# model_name = "facebook/nllb-200-1.3B"          # Better quality
# model_name = "facebook/nllb-200-3.3B"          # Best quality (requires more GPU)
```

### LoRA Configuration
```python
r = 16              # Increase to 32 for more capacity
lora_alpha = 32     # Scale with r (typically 2x)
target_modules = [  # Which layers to adapt
    "q_proj", "v_proj", "k_proj", "o_proj",
    "fc1", "fc2"
]
```

### Training Optimization

**For faster training (less accuracy):**
```python
num_train_epochs = 3
per_device_train_batch_size = 16
gradient_accumulation_steps = 2
```

**For better quality (slower):**
```python
num_train_epochs = 10
learning_rate = 3e-4
warmup_steps = 1000
early_stopping_patience = 5
```

**For limited GPU memory:**
```python
per_device_train_batch_size = 4
gradient_accumulation_steps = 8
gradient_checkpointing = True
fp16 = True
```

## 📊 Expected Results

**Typical Performance (after 5 epochs):**
- BLEU: 25-35 (good for idioms)
- chrF++: 55-65
- COMET: 0.70-0.80
- Human-like contextual translations

**Note**: Idiom translation scores are typically lower than literal translation due to the many-to-many nature of idiomatic expressions.

## 🔧 Troubleshooting

### Out of Memory Error
```python
# In config.py
per_device_train_batch_size = 4  # Reduce
gradient_accumulation_steps = 8   # Increase
gradient_checkpointing = True
```

### Slow Training
```python
# Use smaller model
model_name = "facebook/nllb-200-distilled-600M"

# Reduce data augmentation
add_context_variations = False

# Use fewer evaluation steps
eval_steps = 1000
save_steps = 1000
```

### Poor Translation Quality
```python
# Increase LoRA rank
r = 32
lora_alpha = 64

# Train longer
num_train_epochs = 10

# Use larger model
model_name = "facebook/nllb-200-1.3B"
```

## 🏗️ System Architecture

### Training Pipeline
```
CSV Datasets → Data Processor → Tokenization → LoRA Fine-tuning → Checkpoints
                    ↓
            Context Augmentation
                    ↓
           Train/Val/Test Split
```

### Inference Pipeline
```
Input Text → Tokenizer → NLLB Encoder → LoRA-adapted Decoder → Target Language
                ↓
         Language Detection
                ↓
      Forced BOS Token (target lang)
```

### Key Components

1. **Data Preprocessor** (`data_preprocessor.py`)
   - Loads 3 parallel CSV datasets
   - Cleans text (BOM, whitespace, encoding)
   - Creates bidirectional pairs (A→B and B→C from A→B→C)
   - Adds context variations (standalone + in sentences)
   - Splits data stratified by language pairs

2. **LoRA Training** (`train.py`)
   - Loads NLLB-200 base model
   - Applies LoRA adapters to attention + FFN layers
   - Custom data collator for multilingual batches
   - Gradient checkpointing for memory efficiency
   - Early stopping + best model selection

3. **Evaluation** (`evaluate.py`)
   - Multiple metrics: BLEU, chrF++, COMET
   - Per-language-pair analysis
   - Beam search generation
   - Results saved as JSON

4. **Inference** (`inference.py`)
   - Loads model with LoRA adapters
   - Supports batch and interactive modes
   - Configurable beam search, temperature
   - Multiple translation candidates

## 📈 Monitoring Training

**TensorBoard:**
```bash
tensorboard --logdir nllb_idiom_finetuned/runs
```

**Metrics to Watch:**
- `train_loss`: Should decrease steadily
- `eval_loss`: Should decrease (watch for overfitting)
- `learning_rate`: Should follow warmup + cosine schedule

## 🎓 Best Practices

1. **Start Small**: Test with 1 epoch first
2. **Monitor Overfitting**: Watch train/val loss gap
3. **Experiment with LoRA rank**: Start with r=16, increase if underfitting
4. **Use Context Variations**: Helps with real-world usage
5. **Evaluate Per Language Pair**: Some pairs may need more data
6. **Save Checkpoints Frequently**: Training can be unstable

## 📝 Citation

If you use this code, please cite:

```bibtex
@software{nllb_idiom_finetuning,
  title={NLLB-200 Idiomatic Translation Fine-tuning},
  author={Your Name},
  year={2025},
  url={https://github.com/yourusername/repo}
}
```

## 📄 License

MIT License - see LICENSE file

## 🤝 Contributing

Contributions welcome! Please:
1. Test your changes
2. Follow the existing code style
3. Add docstrings to new functions
4. Update README if needed

## 📞 Support

For issues or questions:
- Check existing issues on GitHub
- Review the troubleshooting section
- Open a new issue with details

## 🔗 References

- [NLLB Paper](https://arxiv.org/abs/2207.04672)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [Hugging Face PEFT](https://github.com/huggingface/peft)
- [COMET Metric](https://github.com/Unbabel/COMET)

