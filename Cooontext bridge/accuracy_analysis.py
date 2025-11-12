#!/usr/bin/env python3
"""
Model Accuracy Analysis - Based on existing evaluation results
Provides comprehensive accuracy metrics for the NLLB idiom translation model
"""
import json
import pandas as pd
from pathlib import Path


class AccuracyAnalyzer:
    """Analyze model accuracy from existing evaluation results"""
    
    def __init__(self):
        self.results_file = "nllb_idiom_finetuned/evaluation_results.json"
        
    def load_existing_results(self):
        """Load existing evaluation results"""
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def interpret_metrics(self, results):
        """Interpret and explain the evaluation metrics"""
        print("🎯 MODEL ACCURACY ANALYSIS")
        print("=" * 80)
        print()
        
        if not results:
            print("❌ No evaluation results found!")
            return
        
        # Overall metrics
        overall = results.get('overall', {})
        print("📊 OVERALL MODEL PERFORMANCE:")
        print(f"   Exact Match Rate:  {overall.get('exact_match_pct', 0)*100:.1f}%")
        print(f"   Length Accuracy:   {overall.get('length_ratio', 0):.1%} of expected length")
        print(f"   Avg Prediction:    {overall.get('avg_pred_length', 0):.1f} words")
        print(f"   Avg Reference:     {overall.get('avg_ref_length', 0):.1f} words")
        print()
        
        # Per language pair analysis
        pairs = results.get('by_language_pair', {})
        
        print("🌍 ACCURACY BY LANGUAGE PAIR:")
        print("-" * 60)
        
        accuracy_scores = {}
        
        for pair_name, metrics in pairs.items():
            exact_match = metrics.get('exact_match_pct', 0) * 100
            length_ratio = metrics.get('length_ratio', 0)
            
            # Convert technical names to readable format
            readable_pair = self.format_language_pair(pair_name)
            
            accuracy_scores[readable_pair] = exact_match
            
            # Determine quality level based on exact match and length ratio
            if exact_match > 50:
                quality = "🟢 EXCELLENT"
            elif exact_match > 30:
                quality = "🟡 GOOD"
            elif exact_match > 10:
                quality = "🟠 FAIR"
            else:
                quality = "🔴 NEEDS IMPROVEMENT"
            
            print(f"{readable_pair:25} | Exact Match: {exact_match:5.1f}% | {quality}")
            print(f"{'':25} | Length Ratio: {length_ratio:.2f} | " + 
                  ("✅ Good length" if 0.8 <= length_ratio <= 1.2 else "⚠️ Length issues"))
            print()
        
        # Calculate weighted average accuracy
        if accuracy_scores:
            avg_accuracy = sum(accuracy_scores.values()) / len(accuracy_scores)
            print(f"📈 AVERAGE ACCURACY ACROSS ALL PAIRS: {avg_accuracy:.1f}%")
            print()
        
        # Provide interpretation
        self.provide_interpretation(accuracy_scores, overall)
    
    def format_language_pair(self, pair_name):
        """Convert technical language codes to readable names"""
        mapping = {
            'eng_Latn -> tel_Telu': 'English → Telugu',
            'tel_Telu -> eng_Latn': 'Telugu → English',
            'eng_Latn -> hin_Deva': 'English → Hindi',
            'hin_Deva -> tel_Telu': 'Hindi → Telugu',
            'tel_Telu -> hin_Deva': 'Telugu → Hindi',
            'hin_Deva -> eng_Latn': 'Hindi → English',
        }
        return mapping.get(pair_name, pair_name)
    
    def provide_interpretation(self, accuracy_scores, overall_metrics):
        """Provide detailed interpretation of results"""
        print("🔍 DETAILED ACCURACY INTERPRETATION:")
        print("-" * 60)
        
        # Overall assessment
        avg_accuracy = sum(accuracy_scores.values()) / len(accuracy_scores) if accuracy_scores else 0
        
        if avg_accuracy > 50:
            assessment = "🎉 EXCELLENT performance for specialized idiom translation"
        elif avg_accuracy > 30:
            assessment = "👍 GOOD performance with room for improvement"
        elif avg_accuracy > 15:
            assessment = "⚠️ MODERATE performance, may need more training"
        else:
            assessment = "❌ LOW performance, significant improvement needed"
        
        print(f"Overall Assessment: {assessment}")
        print()
        
        # Best and worst performing pairs
        if accuracy_scores:
            best_pair = max(accuracy_scores, key=accuracy_scores.get)
            worst_pair = min(accuracy_scores, key=accuracy_scores.get)
            
            print(f"🏆 Best Performance:  {best_pair} ({accuracy_scores[best_pair]:.1f}%)")
            print(f"📉 Needs Work:       {worst_pair} ({accuracy_scores[worst_pair]:.1f}%)")
            print()
        
        # Context about idiom translation difficulty
        print("🎯 CONTEXT FOR IDIOM TRANSLATION:")
        print("   • Idioms are inherently difficult to translate")
        print("   • Exact match rates of 30-50% are considered good for idioms")
        print("   • Cultural context matters more than word-for-word accuracy")
        print("   • BLEU scores for idioms are typically lower than general text")
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        if avg_accuracy < 30:
            print("   • Consider training on more idiom-specific data")
            print("   • Increase model size or training epochs")
            print("   • Review data quality and preprocessing")
        else:
            print("   • Model shows good idiom translation capability")
            print("   • Consider fine-tuning on specific low-performing language pairs")
            print("   • Evaluate with human judgment for cultural appropriateness")
        print()

    def calculate_estimated_bleu(self, exact_match_rate):
        """Estimate BLEU score based on exact match rate for idioms"""
        # For idioms, BLEU is typically 2-3x lower than exact match due to n-gram penalties
        estimated_bleu = exact_match_rate * 0.3  # Conservative estimate
        return estimated_bleu

    def create_summary_report(self, results):
        """Create a comprehensive summary report"""
        print("📋 FINAL ACCURACY REPORT")
        print("=" * 80)
        
        if not results:
            print("❌ No evaluation data available")
            return
        
        overall = results.get('overall', {})
        pairs = results.get('by_language_pair', {})
        
        # Calculate summary statistics
        exact_matches = [pair.get('exact_match_pct', 0) * 100 for pair in pairs.values()]
        
        if exact_matches:
            avg_exact = sum(exact_matches) / len(exact_matches)
            max_exact = max(exact_matches)
            min_exact = min(exact_matches)
            
            # Estimate BLEU scores
            estimated_bleu = self.calculate_estimated_bleu(avg_exact)
            
            print(f"📊 SUMMARY STATISTICS:")
            print(f"   Average Exact Match: {avg_exact:.1f}%")
            print(f"   Best Pair Match:     {max_exact:.1f}%")
            print(f"   Worst Pair Match:    {min_exact:.1f}%")
            print(f"   Estimated BLEU:      {estimated_bleu:.1f}")
            print()
            
            print(f"🎯 MODEL GRADE: ", end="")
            if avg_exact > 40:
                print("A- (Excellent for idiom translation)")
            elif avg_exact > 30:
                print("B+ (Good idiom translation performance)")
            elif avg_exact > 20:
                print("B (Acceptable for specialized domain)")
            elif avg_exact > 10:
                print("C+ (Basic functionality)")
            else:
                print("C (Needs significant improvement)")
        
        print()
        print("✅ EVALUATION COMPLETE")
        print("📄 This analysis is based on exact match and length metrics")
        print("💡 For production use, consider additional human evaluation")


def main():
    """Main analysis function"""
    analyzer = AccuracyAnalyzer()
    
    # Load existing results
    results = analyzer.load_existing_results()
    
    # Analyze and display
    analyzer.interpret_metrics(results)
    analyzer.create_summary_report(results)


if __name__ == "__main__":
    main()
