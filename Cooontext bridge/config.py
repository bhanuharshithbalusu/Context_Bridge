"""
Configuration file for NLLB-200 Idiomatic Translation Fine-tuning
"""
from dataclasses import dataclass
from typing import Dict

@dataclass
class ModelConfig:
    """Model configuration"""
    model_name: str = "facebook/nllb-200-distilled-600M"  # Can use 1.3B or 3.3B for better quality
    max_length: int = 256
    
    # Language codes for NLLB
    lang_codes: Dict[str, str] = None
    
    def __post_init__(self):
        self.lang_codes = {
            'telugu': 'tel_Telu',
            'hindi': 'hin_Deva',
            'english': 'eng_Latn'
        }


@dataclass
class LoRAConfig:
    """PEFT LoRA configuration"""
    r: int = 16  # LoRA rank - higher = more capacity but slower
    lora_alpha: int = 32  # LoRA scaling factor
    target_modules: list = None  # Will be set in __post_init__
    lora_dropout: float = 0.05
    bias: str = "none"
    task_type: str = "SEQ_2_SEQ_LM"
    
    def __post_init__(self):
        # Target attention and feed-forward layers
        self.target_modules = [
            "q_proj", 
            "v_proj",
            "k_proj",
            "o_proj",
            "fc1",
            "fc2"
        ]


@dataclass
class TrainingConfig:
    """Training hyperparameters optimized for idiomatic translation"""
    output_dir: str = "./nllb_idiom_finetuned"
    
    # Batch sizes (OPTIMIZED FOR ~24 HOUR TRAINING)
    per_device_train_batch_size: int = 12  # Increased from 8 to reduce total steps
    per_device_eval_batch_size: int = 16
    gradient_accumulation_steps: int = 4  # Effective batch size = 8 * 4 = 32
    
    # Learning rate and scheduler
    learning_rate: float = 5e-4  # Higher for LoRA (vs 1e-5 for full fine-tuning)
    warmup_steps: int = 100  # Reduced from 500 to save time
    lr_scheduler_type: str = "cosine"
    weight_decay: float = 0.01
    
    # Training duration (OPTIMIZED: 5 epochs → 2 epochs)
    num_train_epochs: int = 2  # Reduced from 5 for faster training
    max_steps: int = -1  # -1 means use num_train_epochs
    
    # Optimization
    fp16: bool = True  # Use mixed precision (set False for CPU)
    bf16: bool = False  # Use bfloat16 if available (A100/H100)
    gradient_checkpointing: bool = True  # Reduce memory usage
    
    # Logging and saving (REDUCED FREQUENCY TO SAVE TIME)
    logging_steps: int = 100  # Increased from 50
    eval_steps: int = 750  # Increased from 500 to reduce evaluation overhead
    save_steps: int = 750  # Increased from 500
    save_total_limit: int = 2  # Reduced from 3 to save disk space
    
    # Evaluation
    evaluation_strategy: str = "steps"
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "eval_loss"
    greater_is_better: bool = False
    
    # Other
    seed: int = 42
    dataloader_num_workers: int = 4
    remove_unused_columns: bool = False
    report_to: str = "tensorboard"
    
    # Early stopping (optional)
    early_stopping_patience: int = 2  # Reduced from 3
    early_stopping_threshold: float = 0.0


@dataclass
class DataConfig:
    """Data processing configuration"""
    dataset_dir: str = "./Dataset"
    english_file: str = "English_proverbs_translation.csv"
    hindi_file: str = "Hindi_Proverbs_Translation.csv"
    telugu_file: str = "Telugu_Proverbs_Hindi.csv"
    
    train_split: float = 0.8
    val_split: float = 0.1
    test_split: float = 0.1
    
    # Data augmentation for idioms
    # DISABLED: Context templates cause script mixing issues
    # Re-enable after implementing multilingual templates
    add_context_variations: bool = False
    context_templates: list = None
    
    def __post_init__(self):
        # Templates for contextual idiom usage
        # Currently disabled to maintain script purity
        self.context_templates = [
            "{}",  # Standalone idiom only
        ]


# Global configs
MODEL_CONFIG = ModelConfig()
LORA_CONFIG = LoRAConfig()
TRAINING_CONFIG = TrainingConfig()
DATA_CONFIG = DataConfig()

