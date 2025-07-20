from flask import Blueprint, request, jsonify, session
from src.utils.i18n import i18n

i18n_bp = Blueprint('i18n', __name__)

@i18n_bp.route('/language', methods=['GET'])
def get_language():
    """Get current language"""
    try:
        current_language = i18n.get_language()
        return jsonify({
            'language': current_language,
            'supported_languages': i18n.supported_languages,
            'is_rtl': i18n.is_rtl(current_language),
            'direction': i18n.get_direction(current_language)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@i18n_bp.route('/language', methods=['POST'])
def set_language():
    """Set language preference"""
    try:
        data = request.get_json()
        language = data.get('language')
        
        if not language:
            return jsonify({'error': 'Language is required'}), 400
        
        if language not in i18n.supported_languages:
            return jsonify({'error': 'Unsupported language'}), 400
        
        # Set language in session
        success = i18n.set_language(language)
        
        if success:
            return jsonify({
                'success': True,
                'language': language,
                'is_rtl': i18n.is_rtl(language),
                'direction': i18n.get_direction(language),
                'message': 'Language updated successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to set language'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@i18n_bp.route('/translations/<language>', methods=['GET'])
def get_translations(language):
    """Get all translations for a specific language"""
    try:
        if language not in i18n.supported_languages:
            return jsonify({'error': 'Unsupported language'}), 400
        
        translations = i18n.translations.get(language, {})
        
        return jsonify({
            'language': language,
            'translations': translations,
            'is_rtl': i18n.is_rtl(language),
            'direction': i18n.get_direction(language)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@i18n_bp.route('/translate', methods=['POST'])
def translate_key():
    """Translate a specific key"""
    try:
        data = request.get_json()
        key = data.get('key')
        language = data.get('language')
        params = data.get('params', {})
        
        if not key:
            return jsonify({'error': 'Translation key is required'}), 400
        
        translation = i18n.translate(key, language, **params)
        
        return jsonify({
            'key': key,
            'translation': translation,
            'language': language or i18n.get_language()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

