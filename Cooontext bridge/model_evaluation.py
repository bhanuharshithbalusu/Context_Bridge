#!/usr/bin/env python3
"""
Comprehensive Model Accuracy Evaluation Script
Measures BLEU, chrF++, exact match, and other metrics for the fine-tuned NLLB model
"""
import torch
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import sacrebleu
from collections import defaultdict
import logging

from test_translation import TranslationTester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Comprehensive evaluation of the translation model"""
    
    def __init__(self, model_path: str = None):
        """Initialize evaluator with model path"""
        self.tester = TranslationTester(model_path)
        self.tester.load_model()
        
        # Load test datasets
        self.test_data = self.load_test_datasets()
        
    def load_test_datasets(self) -> Dict[str, List[Dict]]:
        """Load test datasets from CSV files"""
        datasets = {}
        
        dataset_files = {
            'english': 'Dataset/English_proverbs_translation.csv',
            'hindi': 'Dataset/Hindi_Proverbs_Translation.csv',
            'telugu': 'Dataset/Telugu_Proverbs_Hindi.csv'
        }
        
        for lang, filename in dataset_files.items():
            try:
                filepath = Path(filename)
                if filepath.exists():
                    df = pd.read_csv(filepath)
                    # Process based on the dataset structure
                    if lang == 'english':
                        # English → Hindi, Telugu
                        test_pairs = []
                        for _, row in df.iterrows():
                            test_pairs.extend([
                                {
                                    'source': row['Source'],
                                    'target': row['Hindi'],
                                    'src_lang': 'eng_Latn',
                                    'tgt_lang': 'hin_Deva',
                                    'pair': 'eng→hin'
                                },
                                {
                                    'source': row['Source'],
                                    'target': row['Telugu'],
                                    'src_lang': 'eng_Latn',
                                    'tgt_lang': 'tel_Telu',
                                    'pair': 'eng→tel'
                                }
                            ])
                        datasets[lang] = test_pairs[:50]  # Limit for evaluation
                        
                    elif lang == 'hindi':
                        test_pairs = []
                        for _, row in df.iterrows():
                            test_pairs.extend([
                                {
                                    'source': row['Hindi'],
                                    'target': row['English'],
                                    'src_lang': 'hin_Deva',
                                    'tgt_lang': 'eng_Latn',
                                    'pair': 'hin→eng'
                                },
                                {
                                    'source': row['Hindi'],
                                    'target': row['Telugu'],
                                    'src_lang': 'hin_Deva',
                                    'tgt_lang': 'tel_Telu',
                                    'pair': 'hin→tel'
                                }
                            ])
                        datasets[lang] = test_pairs[:50]
                        
                    elif lang == 'telugu':
                        test_pairs = []
                        for _, row in df.iterrows():
                            test_pairs.extend([
                                {
                                    'source': row['Telugu'],
                                    'target': row['Hindi'],
                                    'src_lang': 'tel_Telu',
                                    'tgt_lang': 'hin_Deva',
                                    'pair': 'tel→hin'
                                },
                                {
                                    'source': row['Telugu'],
                                    'target': row['English'],
                                    'src_lang': 'tel_Telu',
                                    'tgt_lang': 'eng_Latn',
                                    'pair': 'tel→eng'
                                }
                            ])
                        datasets[lang] = test_pairs[:50]
                        
                    logger.info(f"Loaded {len(datasets[lang])} test pairs from {lang} dataset")
                    
            except Exception as e:
                logger.error(f"Failed to load {lang} dataset: {e}")
                
        return datasets
    
    def calculate_bleu_score(self, predictions: List[str], references: List[str]) -> float:
        """Calculate BLEU score using sacrebleu"""
        try:
            # Format references as list of lists (sacrebleu format)
            refs = [[ref] for ref in references]
            bleu = sacrebleu.corpus_bleu(predictions, list(zip(*refs)))
            return bleu.score
        except Exception as e:
            logger.error(f"Error calculating BLEU: {e}")
            return 0.0
    
    def calculate_chrf_score(self, predictions: List[str], references: List[str]) -> float:
        """Calculate chrF++ score"""
        try:
            refs = [[ref] for ref in references]
            chrf = sacrebleu.corpus_chrf(predictions, list(zip(*refs)))
            return chrf.score
        except Exception as e:
            logger.error(f"Error calculating chrF: {e}")
            return 0.0
    
    def calculate_exact_match(self, predictions: List[str], references: List[str]) -> float:
        """Calculate exact match percentage"""
        if not predictions or not references:
            return 0.0
        
        exact_matches = sum(1 for pred, ref in zip(predictions, references) 
                          if pred.strip().lower() == ref.strip().lower())
        return (exact_matches / len(predictions)) * 100
    
    def evaluate_language_pair(self, test_pairs: List[Dict]) -> Dict[str, float]:
        """Evaluate model on specific language pair"""
        predictions = []
        references = []
        
        logger.info(f"Evaluating {len(test_pairs)} translation pairs...")
        
        for i, pair in enumerate(test_pairs):
            try:
                # Get model prediction
                prediction, used_fallback = self.tester.translate(
                    pair['source'],
                    pair['src_lang'],
                    pair['tgt_lang']
                )
                
                predictions.append(prediction)
                references.append(pair['target'])
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Evaluated {i + 1}/{len(test_pairs)} pairs")
                    
            except Exception as e:
                logger.error(f"Error translating pair {i}: {e}")
                predictions.append("")  # Empty prediction for failed cases
                references.append(pair['target'])
        
        # Calculate metrics
        bleu = self.calculate_bleu_score(predictions, references)
        chrf = self.calculate_chrf_score(predictions, references)
        exact_match = self.calculate_exact_match(predictions, references)
        
        # Calculate average lengths
        avg_pred_len = sum(len(p.split()) for p in predictions) / len(predictions)
        avg_ref_len = sum(len(r.split()) for r in references) / len(references)
        length_ratio = avg_pred_len / avg_ref_len if avg_ref_len > 0 else 0
        
        return {
            'bleu_score': round(bleu, 2),
            'chrf_score': round(chrf, 2),
            'exact_match_pct': round(exact_match, 2),
            'avg_pred_length': round(avg_pred_len, 2),
            'avg_ref_length': round(avg_ref_len, 2),
            'length_ratio': round(length_ratio, 3),
            'num_pairs': len(test_pairs)
        }
    
    def run_full_evaluation(self) -> Dict:
        """Run comprehensive evaluation on all test data"""
        results = {}
        
        print("🧪 COMPREHENSIVE MODEL ACCURACY EVALUATION")
        print("=" * 60)
        print()
        
        # Evaluate each dataset
        all_predictions = []
        all_references = []
        
        for dataset_name, test_pairs in self.test_data.items():
            # Group by language pair
            pairs_by_lang = defaultdict(list)
            for pair in test_pairs:
                pairs_by_lang[pair['pair']].append(pair)
            
            results[dataset_name] = {}
            
            for lang_pair, pairs in pairs_by_lang.items():
                print(f"📊 Evaluating {dataset_name.title()} → {lang_pair}")
                print(f"   Test pairs: {len(pairs)}")
                
                pair_results = self.evaluate_language_pair(pairs)
                results[dataset_name][lang_pair] = pair_results
                
                # Add to overall evaluation
                for pair in pairs:
                    try:
                        pred, _ = self.tester.translate(pair['source'], pair['src_lang'], pair['tgt_lang'])
                        all_predictions.append(pred)
                        all_references.append(pair['target'])
                    except:
                        pass
                
                print(f"   ✅ BLEU: {pair_results['bleu_score']}")
                print(f"   ✅ chrF++: {pair_results['chrf_score']}")
                print(f"   ✅ Exact Match: {pair_results['exact_match_pct']}%")
                print()
        
        # Calculate overall metrics
        if all_predictions and all_references:
            overall_bleu = self.calculate_bleu_score(all_predictions, all_references)
            overall_chrf = self.calculate_chrf_score(all_predictions, all_references)
            overall_exact = self.calculate_exact_match(all_predictions, all_references)
            
            results['overall'] = {
                'bleu_score': round(overall_bleu, 2),
                'chrf_score': round(overall_chrf, 2),
                'exact_match_pct': round(overall_exact, 2),
                'total_pairs_evaluated': len(all_predictions)
            }
        
        return results
    
    def print_evaluation_summary(self, results: Dict):
        """Print formatted evaluation summary"""
        print("🎯 FINAL ACCURACY RESULTS")
        print("=" * 60)
        
        if 'overall' in results:
            overall = results['overall']
            print(f"📈 OVERALL MODEL PERFORMANCE:")
            print(f"   🎯 BLEU Score:    {overall['bleu_score']:.2f}")
            print(f"   🎯 chrF++ Score:  {overall['chrf_score']:.2f}")
            print(f"   🎯 Exact Match:   {overall['exact_match_pct']:.2f}%")
            print(f"   📊 Total Pairs:   {overall['total_pairs_evaluated']}")
            print()
        
        print("📋 DETAILED BREAKDOWN BY LANGUAGE PAIR:")
        print("-" * 60)
        
        for dataset_name, dataset_results in results.items():
            if dataset_name == 'overall':
                continue
                
            print(f"\n📚 {dataset_name.title()} Dataset:")
            for lang_pair, metrics in dataset_results.items():
                print(f"   {lang_pair}: BLEU={metrics['bleu_score']}, chrF++={metrics['chrf_score']}, Exact={metrics['exact_match_pct']}%")
        
        print("\n" + "=" * 60)
        print("📝 EVALUATION COMPLETE!")
    
    def save_results(self, results: Dict, filename: str = "model_evaluation_results.json"):
        """Save evaluation results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {filename}")


def main():
    """Main evaluation function"""
    try:
        print("🚀 Starting Model Accuracy Evaluation...")
        print("Loading model and test data...\n")
        
        evaluator = ModelEvaluator()
        
        # Check if test data was loaded
        total_pairs = sum(len(pairs) for pairs in evaluator.test_data.values())
        if total_pairs == 0:
            print("❌ No test data found! Make sure Dataset CSV files are available.")
            return
        
        print(f"✅ Loaded {total_pairs} test pairs across {len(evaluator.test_data)} datasets\n")
        
        # Run evaluation
        results = evaluator.run_full_evaluation()
        
        # Print summary
        evaluator.print_evaluation_summary(results)
        
        # Save results
        evaluator.save_results(results)
        
        print(f"\n📊 Detailed results saved to: model_evaluation_results.json")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
