"""
Simple test script to demonstrate the trained translation model
"""
import torch
import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
from config import MODEL_CONFIG, TRAINING_CONFIG
from idiom_detector import ContextualTranslator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranslationTester:
    """Test the trained translation model"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or TRAINING_CONFIG.output_dir
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        self.tokenizer = None
        self.model = None
        
    def load_model(self):
        """Load the fine-tuned model"""
        logger.info(f"Loading model from {self.model_path}")
        
        # Load tokenizer for fine-tuned model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        
        # Load base model for fine-tuning
        logger.info(f"Loading base model: {MODEL_CONFIG.model_name}")
        base_model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_CONFIG.model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            low_cpu_mem_usage=True,
        )
        
        # Load LoRA adapters for fine-tuned model
        logger.info("Loading LoRA adapters...")
        self.model = PeftModel.from_pretrained(base_model, self.model_path)
        self.model.eval()
        self.model.to(self.device)
        
        # Load separate base model and tokenizer for fallback translations
        logger.info("Loading fallback base NLLB model...")
        self.fallback_tokenizer = AutoTokenizer.from_pretrained(MODEL_CONFIG.model_name)
        self.fallback_model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_CONFIG.model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            low_cpu_mem_usage=True,
        )
        self.fallback_model.eval()
        self.fallback_model.to(self.device)
        
        # Initialize contextual translator
        self.contextual_translator = ContextualTranslator(self)
        
        logger.info("✓ Model loaded successfully!")
    
    def fallback_translate(self, text: str, source_lang: str, target_lang: str, max_length: int = 256) -> str:
        """Use base NLLB model for general translation as fallback"""
        logger.info(f"Using base NLLB for fallback translation: {source_lang} → {target_lang}")
        
        # Set source language on fallback tokenizer
        self.fallback_tokenizer.src_lang = source_lang
        
        # Tokenize
        encoded = self.fallback_tokenizer(
            text,
            return_tensors="pt",
            max_length=max_length,
            truncation=True,
            padding=True
        ).to(self.device)
        
        # Get target language token ID
        forced_bos_token_id = self.fallback_tokenizer.convert_tokens_to_ids(target_lang)
        
        # Generate with fallback base model (without LoRA)
        with torch.no_grad():
            generated_tokens = self.fallback_model.generate(
                **encoded,
                forced_bos_token_id=forced_bos_token_id,
                max_length=max_length,
                num_beams=5,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )
        
        # Decode
        translation = self.fallback_tokenizer.decode(
            generated_tokens[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        ).strip()
        
        return translation
    
    def detect_script(self, text: str) -> str:
        """Detect the dominant script in the text"""
        if not text or not isinstance(text, str):
            return "Unknown"
        
        # Count characters from each script
        telugu_count = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')
        hindi_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        latin_count = sum(1 for c in text if c.isalpha() and ord(c) < 128)
        
        total = len([c for c in text if c.isalpha()])
        
        if total == 0:
            return "Unknown"
        
        # Determine dominant script (>50% threshold)
        if telugu_count / total > 0.5:
            return "Telugu"
        elif hindi_count / total > 0.5:
            return "Devanagari"
        elif latin_count / total > 0.5:
            return "Latin"
        else:
            return "Mixed"
    
    def get_expected_script(self, lang_code: str) -> str:
        """Get expected script for language code"""
        script_map = {
            'eng_Latn': 'Latin',
            'hin_Deva': 'Devanagari',
            'tel_Telu': 'Telugu',
            # Also handle short codes
            'eng': 'Latin',
            'hin': 'Devanagari',
            'tel': 'Telugu',
            'english': 'Latin',
            'hindi': 'Devanagari',
            'telugu': 'Telugu'
        }
        return script_map.get(lang_code.lower(), 'Unknown')
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        max_length: int = 256,
        num_beams: int = 5,
        temperature: float = 1.0,
        top_p: float = 0.9,
        use_fallback: bool = True
    ) -> tuple:
        """Translate a single text with improved generation and script validation
        
        Args:
            text: Source text to translate
            source_lang: Source language code
            target_lang: Target language code
            max_length: Maximum sequence length
            num_beams: Number of beams for beam search
            temperature: Temperature for sampling
            top_p: Top-p for nucleus sampling
            use_fallback: If True, use base NLLB model when wrong script is detected
            
        Returns:
            tuple: (translation, used_fallback)
        """
        # Validate and normalize language codes
        lang_map = {
            'eng': 'eng_Latn',
            'hin': 'hin_Deva',
            'tel': 'tel_Telu',
            'english': 'eng_Latn',
            'hindi': 'hin_Deva',
            'telugu': 'tel_Telu'
        }
        
        # Normalize language codes
        source_lang = lang_map.get(source_lang.lower(), source_lang)
        target_lang = lang_map.get(target_lang.lower(), target_lang)
        
        # Expected output script
        expected_script = self.get_expected_script(target_lang)
        
        # Try fine-tuned model first
        # Set source language
        self.tokenizer.src_lang = source_lang
        
        # Tokenize
        encoded = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=max_length,
            truncation=True,
            padding=True
        ).to(self.device)
        
        # Get target language token ID
        forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(target_lang)
        
        # Generate with fine-tuned model
        with torch.no_grad():
            generated_tokens = self.model.generate(
                **encoded,
                forced_bos_token_id=forced_bos_token_id,
                max_length=max_length,
                min_length=1,
                num_beams=num_beams,
                num_return_sequences=1,
                early_stopping=True,
                no_repeat_ngram_size=3,
                temperature=temperature,
                top_p=top_p,
                do_sample=False,
                repetition_penalty=1.2,
                length_penalty=1.0,
            )
        
        # Decode
        translation = self.tokenizer.decode(
            generated_tokens[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        ).strip()
        
        # Validate output script
        actual_script = self.detect_script(translation)
        
        if actual_script == expected_script:
            # Success! Output is in correct script
            return translation, False
        else:
            # Wrong script detected
            logger.warning(
                f"Fine-tuned model output wrong script: {actual_script} (expected {expected_script})"
            )
            
            if use_fallback:
                # Use base NLLB model to translate to correct language
                logger.info("Attempting fallback translation with base NLLB model...")
                
                # Detect the actual source language of the wrong output
                detected_source = None
                if actual_script == "Devanagari":
                    detected_source = "hin_Deva"
                elif actual_script == "Telugu":
                    detected_source = "tel_Telu"
                elif actual_script == "Latin":
                    detected_source = "eng_Latn"
                
                if detected_source and detected_source != target_lang:
                    # Translate the wrong output to target language
                    fallback_translation = self.fallback_translate(
                        translation, 
                        detected_source, 
                        target_lang,
                        max_length
                    )
                    
                    # Verify fallback translation
                    fallback_script = self.detect_script(fallback_translation)
                    
                    if fallback_script == expected_script:
                        logger.info(f"✓ Fallback translation successful: {fallback_script}")
                        return fallback_translation, True
                    else:
                        logger.warning(
                            f"⚠️  Fallback also produced wrong script: {fallback_script}"
                        )
                        # Return fallback anyway as it might be better
                        return fallback_translation, True
                else:
                    # Can't determine source or already correct, return original
                    return translation, False
            else:
                # No fallback, return as-is with warning
                logger.warning(
                    f"⚠️  Output may be in wrong script: {actual_script} instead of {expected_script}"
                )
                return translation, False
    
    def translate_contextual(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        max_length: int = 256,
        num_beams: int = 5,
    ) -> tuple:
        """
        Translate text with idiom detection and contextual translation
        
        Args:
            text: Source text to translate
            source_lang: Source language code
            target_lang: Target language code
            max_length: Maximum sequence length
            num_beams: Number of beams for beam search
            
        Returns:
            tuple: (translation, metadata_dict)
        """
        # Use contextual translator
        translation, metadata = self.contextual_translator.translate_with_context(
            text, source_lang, target_lang
        )
        
        return translation, metadata


def main():
    """Test translation with example proverbs"""
    print("="*80)
    print("CONTEXTUAL PROVERB TRANSLATION - DEMO")
    print("="*80)
    
    # Initialize tester
    tester = TranslationTester()
    tester.load_model()
    
    # Test examples (English proverbs)
    test_cases = [
        {
            "text": "A bird in the hand is worth two in the bush",
            "src": "eng_Latn",
            "tgt": "hin_Deva",
            "label": "English → Hindi"
        },
        {
            "text": "Don't count your chickens before they hatch",
            "src": "eng_Latn",
            "tgt": "tel_Telu",
            "label": "English → Telugu"
        },
        {
            "text": "Actions speak louder than words",
            "src": "eng_Latn",
            "tgt": "hin_Deva",
            "label": "English → Hindi"
        },
        {
            "text": "Where there's smoke, there's fire",
            "src": "eng_Latn",
            "tgt": "tel_Telu",
            "label": "English → Telugu"
        },
    ]
    
    # Test Hindi proverbs
    test_cases.extend([
        {
            "text": "अंधों में काना राजा",
            "src": "hin_Deva",
            "tgt": "eng_Latn",
            "label": "Hindi → English"
        },
        {
            "text": "जैसा देश वैसा भेष",
            "src": "hin_Deva",
            "tgt": "tel_Telu",
            "label": "Hindi → Telugu"
        },
    ])
    
    print("\n" + "="*80)
    print("TRANSLATION RESULTS")
    print("="*80)
    
    # Translate each test case
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['label']}")
        print(f"   Source: {test['text']}")
        
        translation, used_fallback = tester.translate(
            test['text'],
            test['src'],
            test['tgt']
        )
        
        # Show translation with script validation
        detected_script = tester.detect_script(translation)
        expected_script = tester.get_expected_script(test['tgt'])
        
        print(f"   Translation: {translation}")
        
        if detected_script == expected_script:
            if used_fallback:
                print(f"   ✓ Script: {detected_script} (CORRECT - via fallback base NLLB)")
            else:
                print(f"   ✓ Script: {detected_script} (CORRECT)")
        else:
            print(f"   ⚠️  Script: {detected_script} (Expected: {expected_script})")
    
    print("\n" + "="*80)
    print("CONTEXTUAL TRANSLATION (Idioms in Sentences)")
    print("="*80)
    
    # Test contextual sentences with embedded idioms
    contextual_tests = [
        {
            "text": "She had to bite the bullet and tell her boss about the mistake",
            "src": "eng_Latn",
            "tgt": "tel_Telu",
            "label": "Contextual English → Telugu"
        },
        {
            "text": "We need to break the ice at the meeting tomorrow",
            "src": "eng_Latn",
            "tgt": "hin_Deva",
            "label": "Contextual English → Hindi"
        },
        {
            "text": "Don't spill the beans about the surprise party",
            "src": "eng_Latn",
            "tgt": "tel_Telu",
            "label": "Contextual English → Telugu"
        },
        {
            "text": "వంటలో పదేపదే కలపడం మొదలుపెట్టింది. కతికితే అతకదు అన్నట్టే!",
            "src": "tel_Telu",
            "tgt": "eng_Latn",
            "label": "Contextual Telugu → English"
        },
    ]
    
    for i, test in enumerate(contextual_tests, 1):
        print(f"\n{i}. {test['label']}")
        print(f"   Source: {test['text']}")
        
        # Use contextual translation
        translation, metadata = tester.translate_contextual(
            test['text'],
            test['src'],
            test['tgt']
        )
        
        print(f"   Translation: {translation}")
        
        # Show idiom detection info
        if metadata['idioms_detected'] > 0:
            print(f"   📝 Idioms detected: {metadata['idioms_detected']}")
            for idiom_info in metadata.get('idiom_details', []):
                print(f"      • '{idiom_info['original']}' → '{idiom_info['translation']}'")
        else:
            print(f"   📝 No idioms detected (direct translation)")
    
    print("\n" + "="*80)
    print("INTERACTIVE MODE")
    print("="*80)
    print("\nYou can now enter your own text to translate.")
    print("Language codes: eng_Latn (English), hin_Deva (Hindi), tel_Telu (Telugu)")
    print("Options:")
    print("  - Type 'c' or 'contextual' before text for contextual translation (idiom detection)")
    print("  - Type 'quit' to exit.\n")
    
    while True:
        try:
            text = input("Enter text to translate: ").strip()
            if text.lower() == 'quit':
                break
            
            # Check if contextual mode requested
            use_contextual = False
            if text.lower().startswith('c ') or text.lower().startswith('contextual '):
                use_contextual = True
                text = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
            
            if not text:
                print("❌ Please provide text to translate.")
                continue
            
            src_lang = input("Source language (eng_Latn/hin_Deva/tel_Telu): ").strip()
            tgt_lang = input("Target language (eng_Latn/hin_Deva/tel_Telu): ").strip()
            
            if not src_lang or not tgt_lang:
                print("❌ Please provide all inputs.")
                continue
            
            if use_contextual:
                # Contextual translation with idiom detection
                translation, metadata = tester.translate_contextual(text, src_lang, tgt_lang)
                
                # Show translation with script validation
                detected_script = tester.detect_script(translation)
                expected_script = tester.get_expected_script(tgt_lang)
                
                print(f"\n✓ Translation: {translation}")
                
                if metadata['idioms_detected'] > 0:
                    print(f"📝 Idioms detected: {metadata['idioms_detected']}")
                    for idiom_info in metadata.get('idiom_details', []):
                        print(f"   • '{idiom_info['original']}' → '{idiom_info['translation']}'")
                else:
                    print(f"📝 No idioms detected")
                
                if detected_script == expected_script:
                    print(f"✓ Script: {detected_script} (CORRECT)\n")
                else:
                    print(f"⚠️  Script: {detected_script} (Expected: {expected_script})\n")
            else:
                # Regular translation
                translation, used_fallback = tester.translate(text, src_lang, tgt_lang)
                
                # Show translation with script validation
                detected_script = tester.detect_script(translation)
                expected_script = tester.get_expected_script(tgt_lang)
                
                print(f"\n✓ Translation: {translation}")
                
                if detected_script == expected_script:
                    if used_fallback:
                        print(f"✓ Script: {detected_script} (CORRECT - via fallback base NLLB)\n")
                    else:
                        print(f"✓ Script: {detected_script} (CORRECT)\n")
                else:
                    print(f"⚠️  Script: {detected_script} (Expected: {expected_script})\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("Thank you for testing the Contextual Proverb Translation system!")
    print("="*80)


if __name__ == "__main__":
    main()

