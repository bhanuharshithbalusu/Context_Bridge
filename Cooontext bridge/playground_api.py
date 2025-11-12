"""
Flask API Server for ContextBridge Playground
Connects the frontend playground.html to the test_translation.py backend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import traceback
from test_translation import TranslationTester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global translation tester instance
tester = None

def initialize_tester():
    """Initialize the translation tester"""
    global tester
    try:
        logger.info("Initializing Translation Tester...")
        tester = TranslationTester()
        tester.load_model()
        logger.info("✓ Translation Tester initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize tester: {e}")
        traceback.print_exc()
        return False

def map_frontend_to_backend_lang(lang_code):
    """Map frontend language codes to backend language codes"""
    lang_mapping = {
        'en': 'eng_Latn',
        'hi': 'hin_Deva', 
        'te': 'tel_Telu',
        'zh': 'zho_Hans',  # Chinese simplified
        'de': 'deu_Latn',  # German
        # Also handle if full codes are passed
        'eng_Latn': 'eng_Latn',
        'hin_Deva': 'hin_Deva',
        'tel_Telu': 'tel_Telu',
        'zho_Hans': 'zho_Hans',
        'deu_Latn': 'deu_Latn'
    }
    mapped = lang_mapping.get(lang_code, lang_code)
    logger.info(f"Language mapping: {lang_code} -> {mapped}")
    return mapped

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'ContextBridge Translation API',
        'tester_loaded': tester is not None
    })

@app.route('/api/translate', methods=['POST'])
def translate_text():
    """Main translation endpoint for the playground"""
    global tester
    
    if tester is None:
        return jsonify({
            'error': 'Translation model not loaded. Please check server logs.',
            'success': False
        }), 500
    
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'success': False
            }), 400
        
        # Extract parameters
        text = data.get('text', '').strip()
        source_lang = data.get('source_lang', '')
        target_lang = data.get('target_lang', '')
        use_contextual = data.get('use_contextual', False)
        
        # Validate input
        if not text:
            return jsonify({
                'error': 'Text is required',
                'success': False
            }), 400
        
        if not source_lang or not target_lang:
            return jsonify({
                'error': 'Source and target languages are required',
                'success': False
            }), 400
        
        # Map frontend language codes to backend codes
        backend_source = map_frontend_to_backend_lang(source_lang)
        backend_target = map_frontend_to_backend_lang(target_lang)
        
        logger.info(f"Translation request: '{text}' from {backend_source} to {backend_target}")
        
        # Perform translation
        if use_contextual:
            # Use contextual translation with idiom detection
            translation, metadata = tester.translate_contextual(
                text, backend_source, backend_target
            )
            
            # Prepare response with idiom detection info
            response = {
                'success': True,
                'target_text': translation,
                'source_text': text,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'translation_type': 'contextual',
                'metadata': {
                    'idioms_detected': metadata.get('idioms_detected', 0),
                    'idiom_details': metadata.get('idiom_details', []),
                    'translation_strategy': metadata.get('translation_strategy', 'direct')
                }
            }
        else:
            # Use regular translation
            translation, used_fallback = tester.translate(
                text, backend_source, backend_target
            )
            
            # Prepare response
            response = {
                'success': True,
                'target_text': translation,
                'source_text': text,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'translation_type': 'regular',
                'metadata': {
                    'used_fallback': used_fallback,
                    'fallback_reason': 'script_mismatch' if used_fallback else None
                }
            }
        
        # Add script detection info
        detected_script = tester.detect_script(translation)
        expected_script = tester.get_expected_script(backend_target)
        
        response['metadata']['output_script'] = detected_script
        response['metadata']['expected_script'] = expected_script
        response['metadata']['script_correct'] = detected_script == expected_script
        
        logger.info(f"Translation successful: '{translation}'")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        traceback.print_exc()
        return jsonify({
            'error': f'Translation failed: {str(e)}',
            'success': False
        }), 500

@app.route('/api/languages', methods=['GET'])
def get_supported_languages():
    """Get list of supported languages"""
    languages = [
        {'code': 'en', 'name': 'English', 'native': 'English'},
        {'code': 'hi', 'name': 'Hindi', 'native': 'हिन्दी'},
        {'code': 'te', 'name': 'Telugu', 'native': 'తెలుగు'},
        {'code': 'zh', 'name': 'Chinese', 'native': '中文'},
        {'code': 'de', 'name': 'German', 'native': 'Deutsch'}
    ]
    
    return jsonify({
        'success': True,
        'languages': languages
    })

@app.route('/api/test', methods=['GET'])
def test_translation():
    """Test endpoint to verify translation works"""
    global tester
    
    if tester is None:
        return jsonify({
            'error': 'Translation model not loaded',
            'success': False
        }), 500
    
    try:
        # Simple test translation
        test_text = "Hello, world!"
        translation, used_fallback = tester.translate(test_text, 'eng_Latn', 'hin_Deva')
        
        return jsonify({
            'success': True,
            'test_input': test_text,
            'test_output': translation,
            'used_fallback': used_fallback
        })
    except Exception as e:
        return jsonify({
            'error': f'Test translation failed: {str(e)}',
            'success': False
        }), 500

if __name__ == '__main__':
    print("="*80)
    print("CONTEXTBRIDGE PLAYGROUND API SERVER")
    print("="*80)
    
    # Initialize the translation tester
    if initialize_tester():
        print(f"\n✅ Server starting on http://127.0.0.1:5000")
        print(f"✅ Translation API ready at http://127.0.0.1:5000/api/translate")
        print(f"✅ Health check at http://127.0.0.1:5000")
        print(f"✅ Test endpoint at http://127.0.0.1:5000/api/test")
        print("\n" + "="*80)
        
        app.run(host='127.0.0.1', port=5001, debug=True)
    else:
        print("\n❌ Failed to initialize translation system. Check the logs above.")
        print("Make sure you have:")
        print("  1. Trained models in the correct directory")
        print("  2. All required dependencies installed")
        print("  3. Proper CUDA setup (if using GPU)")
