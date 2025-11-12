"""
Flask API server for managing idioms with PostgreSQL
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import database_config as db
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# Language code mapping
LANGUAGE_MAP = {
    'en': 'english',
    'hi': 'hindi',
    'te': 'telugu',
    'zh': 'chinese',
    'de': 'german'
}

@app.route('/api/idioms/add', methods=['POST'])
def add_idiom():
    """Add a new idiom"""
    try:
        data = request.json
        language_code = data.get('language')
        idiom = data.get('idiom', '').strip()
        meaning = data.get('meaning', '').strip()
        username = data.get('username', 'anonymous')
        
        if not language_code or not idiom or not meaning:
            return jsonify({
                'success': False,
                'error': 'Language, idiom, and meaning are required'
            }), 400
        
        language = LANGUAGE_MAP.get(language_code)
        if not language:
            return jsonify({
                'success': False,
                'error': f'Invalid language code: {language_code}'
            }), 400
        
        result = db.add_idiom(language, idiom, meaning, username)
        
        if result['success']:
            # Get updated statistics
            stats = db.get_statistics()
            return jsonify({
                'success': True,
                'message': result['message'],
                'id': result['id'],
                'statistics': stats.get('statistics', [])
            }), 201
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/idioms/list', methods=['GET'])
def list_idioms():
    """Get idioms for a specific language and user"""
    try:
        language_code = request.args.get('language')
        username = request.args.get('username')
        
        if not language_code:
            return jsonify({
                'success': False,
                'error': 'Language parameter is required'
            }), 400
        
        language = LANGUAGE_MAP.get(language_code)
        if not language:
            return jsonify({
                'success': False,
                'error': f'Invalid language code: {language_code}'
            }), 400
        
        result = db.get_idioms(language, username)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/idioms/delete', methods=['DELETE'])
def delete_idiom():
    """Delete an idiom"""
    try:
        data = request.json
        language_code = data.get('language')
        idiom_id = data.get('id')
        username = data.get('username')
        
        if not language_code or not idiom_id or not username:
            return jsonify({
                'success': False,
                'error': 'Language, id, and username are required'
            }), 400
        
        language = LANGUAGE_MAP.get(language_code)
        if not language:
            return jsonify({
                'success': False,
                'error': f'Invalid language code: {language_code}'
            }), 400
        
        result = db.delete_idiom(language, idiom_id, username)
        
        if result['success']:
            # Get updated statistics
            stats = db.get_statistics()
            return jsonify({
                'success': True,
                'message': result['message'],
                'statistics': stats.get('statistics', [])
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/idioms/statistics', methods=['GET'])
def get_statistics():
    """Get statistics for all languages"""
    try:
        result = db.get_statistics()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/idioms/training-data', methods=['GET'])
def get_training_data():
    """Get idioms for training if threshold is met"""
    try:
        language_code = request.args.get('language')
        min_count = int(request.args.get('min_count', 10))
        
        if not language_code:
            return jsonify({
                'success': False,
                'error': 'Language parameter is required'
            }), 400
        
        language = LANGUAGE_MAP.get(language_code)
        if not language:
            return jsonify({
                'success': False,
                'error': f'Invalid language code: {language_code}'
            }), 400
        
        result = db.get_training_data(language, min_count)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/idioms/search', methods=['GET'])
def search_idioms():
    """Search for idioms across all languages"""
    try:
        search_term = request.args.get('q', '').strip()
        username = request.args.get('username', '')
        
        if not search_term:
            return jsonify({
                'success': False,
                'error': 'Search term (q) parameter is required'
            }), 400
        
        if len(search_term) < 2:
            return jsonify({
                'success': False,
                'error': 'Search term must be at least 2 characters long'
            }), 400
        
        # Search across all languages
        all_results = []
        
        for lang_code, lang_name in LANGUAGE_MAP.items():
            try:
                result = db.search_idioms(lang_name, search_term, username)
                if result['success'] and result['idioms']:
                    # Add language info to each result
                    for idiom in result['idioms']:
                        idiom['language_code'] = lang_code
                        idiom['language_name'] = lang_name.title()
                    all_results.extend(result['idioms'])
            except Exception as e:
                print(f"Error searching {lang_name}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'results': all_results,
            'total_found': len(all_results),
            'search_term': search_term
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Idiom API is running'
    })

# Serve static files
@app.route('/')
def serve_index():
    """Serve index.html"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

if __name__ == '__main__':
    print("Starting Idiom API Server...")
    print("Initializing database...")
    db.create_idiom_tables()
    print("Server ready!")
    app.run(host='0.0.0.0', port=5002, debug=True)
