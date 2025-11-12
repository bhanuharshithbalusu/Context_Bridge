"""
Idiom detection and contextual translation module
"""
import re
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class IdiomDetector:
    """Detect idioms and proverbs within sentences"""
    
    def __init__(self):        # Common English idioms and their patterns
        self.english_idioms = {
            # Common idioms - with better boundary detection
            r"(?:break|breaking|broke|broken)\s+the\s+ice(?!\s+\w)": "break the ice",
            r"(?:bite|biting|bit|bitten)\s+the\s+bullet(?!\s+\w)": "bite the bullet",
            r"(?:spill|spilling|spilled|spilt)\s+the\s+beans(?!\s+\w)": "spill the beans",
            r"(?:hit|hitting|hits)\s+the\s+(?:nail\s+on\s+the\s+head|jackpot)": "hit the nail on the head",
            r"(?:call|calling|called)\s+it\s+a\s+day(?!\s+\w)": "call it a day",
            r"(?:cut|cutting|cuts)\s+(?:corners|to\s+the\s+chase)": "cut corners",
            r"(?:piece|pieces)\s+of\s+cake(?!\s+\w)": "piece of cake",
            r"(?:cost|costs|costing)\s+an?\s+arm\s+and\s+a\s+leg(?!\s+\w)": "cost an arm and a leg",
            r"(?:beat|beating|beats)\s+around\s+the\s+bush(?!\s+\w)": "beat around the bush",
            r"out\s+of\s+the\s+blue(?!\s+\w)": "out of the blue",  # Fixed: won't match "blue tub"
            r"(?:once|one\s+time)\s+in\s+a\s+blue\s+moon(?!\s+\w)": "once in a blue moon",
            r"(?:throw|throwing|threw|thrown)\s+in\s+the\s+towel(?!\s+\w)": "throw in the towel",
            r"(?:let|letting)\s+the\s+cat\s+out\s+of\s+the\s+bag(?!\s+\w)": "let the cat out of the bag",
            r"(?:cross|crossing|crossed)\s+that\s+bridge\s+when\s+(?:we|you|they)\s+(?:come|get)\s+to\s+it": "cross that bridge",
            r"(?:hold|holding|held)\s+(?:your|my|their)\s+horses(?!\s+\w)": "hold your horses",
            r"(?:jump|jumping|jumped)\s+the\s+gun(?!\s+\w)": "jump the gun",
            r"(?:miss|missing|missed)\s+the\s+boat(?!\s+\w)": "miss the boat",
            r"(?:pull|pulling|pulled)\s+(?:someone's|your|my)\s+leg(?!\s+\w)": "pull someone's leg",
            r"(?:under\s+the\s+weather|feeling\s+under\s+the\s+weather)": "under the weather",
            r"(?:the\s+ball\s+is\s+in\s+(?:your|my|their)\s+court)": "ball in your court",
            r"(?:a\s+)?blessing\s+in\s+disguise(?!\s+\w)": "blessing in disguise",
            r"(?:don't|do\s+not)\s+(?:count|counting)\s+(?:your|my|their)\s+chickens\s+(?:before|until)\s+they\s+hatch": "don't count your chickens",
            r"(?:actions?\s+speaks?\s+louder\s+than\s+words?)": "actions speak louder than words",
            r"(?:a\s+)?bird\s+in\s+(?:the\s+)?hand\s+is\s+worth\s+two\s+in\s+the\s+bush": "a bird in the hand",
            r"(?:where\s+there'?s\s+smoke,?\s+there'?s\s+fire)": "where there's smoke, there's fire",
        }
        
        # Telugu proverb patterns (common ones)
        self.telugu_idioms = {
            r"కతికితే\s+అతకదు": "కతికితే అతకదు",
            r"ఎలుకకు\s+పిల్లి\s+సాక్షి": "ఎలుకకు పిల్లి సాక్షి",
            r"ఉల్లి\s+పది\s+తల్లుల\s+పెట్టు": "ఉల్లి పది తల్లుల పెట్టు",
            r"అడవి\s+కాచిన\s+వెన్నెల": "అడవి కాచిన వెన్నెల",
            r"పైన\s+పటారం[,\s]+లోన\s+లొటారం": "పైన పటారం, లోన లొటారం",
        }
        
        # Hindi proverb patterns
        self.hindi_idioms = {
            r"अंधों\s+में\s+काना\s+राजा": "अंधों में काना राजा",
            r"जैसा\s+देश\s+वैसा\s+भेष": "जैसा देश वैसा भेष",
            r"घर\s+की\s+मुर्गी\s+दाल\s+बराबर": "घर की मुर्गी दाल बराबर",        }
    
    def _validate_idiom_context(self, text: str, match, idiom: str) -> bool:
        """
        Validate if a regex match is truly an idiom based on context
        
        Args:
            text: Full text being analyzed
            match: Regex match object
            idiom: Canonical idiom form
            
        Returns:
            bool: True if it's likely a real idiom, False if probably literal
        """
        matched_text = match.group(0).lower()
        start_pos = match.start()
        end_pos = match.end()
        
        # Get surrounding context (10 words before and after)
        words_before = text[:start_pos].split()[-10:]
        words_after = text[end_pos:].split()[:10:]
        
        # Special validation for "out of the blue"
        if idiom == "out of the blue":
            # Check if "blue" is followed by a noun (indicating literal meaning)
            if words_after:
                next_word = words_after[0].lower()
                # Common objects that are blue (literal usage)
                blue_objects = {'tub', 'car', 'house', 'box', 'bag', 'shirt', 'sky', 'ocean', 
                               'water', 'bottle', 'container', 'room', 'building', 'truck'}
                if next_word in blue_objects:
                    return False
        
        # Special validation for "piece of cake"
        if idiom == "piece of cake":
            # Check if followed by words indicating literal cake
            if words_after:
                next_word = words_after[0].lower()
                # If talking about actual cake characteristics, it's literal
                if any(word in ' '.join(words_before + words_after).lower() 
                      for word in ['chocolate', 'vanilla', 'birthday', 'wedding', 'frosting', 'batter', 'slice']):
                    return False
        
        # Special validation for "break the ice"
        if idiom == "break the ice":
            # Check for literal ice contexts
            if any(word in ' '.join(words_before + words_after).lower() 
                   for word in ['frozen', 'cold', 'winter', 'skating', 'hockey', 'cubes', 'freezer']):
                return False
        
        return True  # Default: assume it's an idiom
    
    def detect_idioms(self, text: str, language: str = 'eng_Latn') -> List[Dict]:
        """
        Detect idioms in text and return their positions
        
        Returns:
            List of dicts with: {'idiom': str, 'start': int, 'end': int, 'original': str}
        """
        idioms_found = []
        
        if language == 'eng_Latn' or language == 'eng':
            patterns = self.english_idioms
        elif language == 'tel_Telu' or language == 'tel':
            patterns = self.telugu_idioms
        elif language == 'hin_Deva' or language == 'hin':
            patterns = self.hindi_idioms
        else:
            return idioms_found
          # Search for each idiom pattern
        for pattern, canonical_form in patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Validate context before adding
                if self._validate_idiom_context(text, match, canonical_form):
                    idioms_found.append({
                        'idiom': canonical_form,
                        'start': match.start(),
                        'end': match.end(),
                        'original': match.group(0)
                    })
                else:
                    logger.info(f"Rejected idiom '{canonical_form}' due to literal context: '{match.group(0)}'")
        
        # Sort by position
        idioms_found.sort(key=lambda x: x['start'])
        
        return idioms_found
    
    def split_sentence_with_idioms(self, text: str, idioms: List[Dict]) -> List[Dict]:
        """
        Split sentence into parts: regular text and idioms
        
        Returns:
            List of dicts with: {'type': 'text'|'idiom', 'content': str, 'canonical': str (for idioms)}
        """
        if not idioms:
            return [{'type': 'text', 'content': text}]
        
        parts = []
        current_pos = 0
        
        for idiom in idioms:
            # Add text before idiom
            if current_pos < idiom['start']:
                before_text = text[current_pos:idiom['start']].strip()
                if before_text:
                    parts.append({
                        'type': 'text',
                        'content': before_text
                    })
            
            # Add idiom
            parts.append({
                'type': 'idiom',
                'content': idiom['original'],
                'canonical': idiom['idiom']
            })
            
            current_pos = idiom['end']
        
        # Add remaining text after last idiom
        if current_pos < len(text):
            after_text = text[current_pos:].strip()
            if after_text:
                parts.append({
                    'type': 'text',
                    'content': after_text
                })
        
        return parts


class ContextualTranslator:
    """Translate text with idiom awareness"""
    
    def __init__(self, translation_model):
        """
        Args:
            translation_model: TranslationTester instance with loaded models
        """
        self.translator = translation_model
        self.detector = IdiomDetector()
        
        # Proper idiom translations for each language pair
        self.idiom_translations = {
            ('eng_Latn', 'tel_Telu'): {
                "piece of cake": "చాలా సులువు",  # Very easy
                "out of the blue": "అనుకోకుండా",  # Unexpectedly  
                "break the ice": "మాట్లాడటం మొదలుపెట్టడం",  # Start conversation
                "bite the bullet": "కష్టమైన పని చేయడం",  # Do difficult task
                "spill the beans": "రహస్యం చెప్పడం",  # Tell secret
                "call it a day": "పని ముగించడం",  # Finish work
                "hit the nail on the head": "సరిగ్గా చెప్పడం",  # Say exactly right
                "cost an arm and a leg": "చాలా ఖరీదు",  # Very expensive
                "once in a blue moon": "అరుదుగా",  # Rarely
                "throw in the towel": "వదులుకోవడం",  # Give up
            },
            ('eng_Latn', 'hin_Deva'): {
                "piece of cake": "बहुत आसान",  # Very easy
                "out of the blue": "अचानक से",  # Suddenly
                "break the ice": "बातचीत शुरू करना",  # Start conversation  
                "bite the bullet": "कठिन काम करना",  # Do difficult task
                "spill the beans": "राज़ खोलना",  # Reveal secret
                "call it a day": "काम खत्म करना",  # Finish work
                "hit the nail on the head": "बिलकुल सही कहना",  # Say exactly right
                "cost an arm and a leg": "बहुत महंगा",  # Very expensive
                "once in a blue moon": "कभी कभार",  # Rarely
                "throw in the towel": "हार मान लेना",  # Give up
            },
            ('tel_Telu', 'eng_Latn'): {
                "కతికితే అతకదు": "if you stir it, it won't stick",  # Things don't always work as planned
                "ఎలుకకు పిల్లి సాక్షి": "cat as witness for the mouse",  # Unreliable witness
            },
            ('hin_Deva', 'eng_Latn'): {
                "अंधों में काना राजा": "in the land of the blind, the one-eyed man is king",
                "जैसा देश वैसा भेष": "when in Rome, do as the Romans do",
            }
        }
    
    def translate_with_context(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        preserve_idioms: bool = True
    ) -> Tuple[str, Dict]:
        """
        Translate text while detecting and preserving idiomatic expressions
        
        Args:
            text: Input text
            source_lang: Source language code
            target_lang: Target language code
            preserve_idioms: If True, translate idioms idiomatically
            
        Returns:
            Tuple of (translated_text, metadata)
        """
        # Detect idioms in source text
        idioms_found = self.detector.detect_idioms(text, source_lang)
        
        if not idioms_found:
            # No idioms, translate normally
            logger.info("No idioms detected, translating entire sentence")
            translation, used_fallback = self.translator.translate(
                text, source_lang, target_lang
            )
            return translation, {
                'idioms_detected': 0,
                'used_fallback': used_fallback,
                'method': 'direct'
            }
        
        # Idioms found - use contextual translation
        logger.info(f"Detected {len(idioms_found)} idiom(s) in text")
        
        # Split into parts
        parts = self.detector.split_sentence_with_idioms(text, idioms_found)
          # Translate each part
        translated_parts = []
        idiom_translations = []
        
        for part in parts:
            if part['type'] == 'text':
                # Regular text - translate normally
                trans, _ = self.translator.translate(
                    part['content'],
                    source_lang,
                    target_lang
                )
                translated_parts.append(trans)
            else:
                # Idiom - check if we have a predefined translation
                idiom_key = (source_lang, target_lang)
                canonical_idiom = part['canonical']
                
                if idiom_key in self.idiom_translations and canonical_idiom in self.idiom_translations[idiom_key]:
                    # Use predefined cultural translation
                    idiom_trans = self.idiom_translations[idiom_key][canonical_idiom]
                    logger.info(f"Using predefined translation for '{canonical_idiom}' -> '{idiom_trans}'")
                else:
                    # Fallback to neural translation
                    idiom_trans, _ = self.translator.translate(
                        canonical_idiom,
                        source_lang,
                        target_lang
                    )
                    logger.warning(f"No predefined translation for '{canonical_idiom}', using neural model: '{idiom_trans}'")
                
                translated_parts.append(idiom_trans)
                idiom_translations.append({
                    'original': part['content'],
                    'canonical': canonical_idiom,
                    'translation': idiom_trans
                })
        
        # Join translated parts
        # Try to reconstruct with proper spacing
        final_translation = self._join_parts_intelligently(translated_parts, target_lang)
        
        return final_translation, {
            'idioms_detected': len(idioms_found),
            'idiom_details': idiom_translations,
            'method': 'contextual',
            'parts_translated': len(parts)
        }
    
    def _join_parts_intelligently(self, parts: List[str], target_lang: str) -> str:
        """Join translated parts with appropriate spacing"""
        if not parts:
            return ""
        
        # For Telugu and Hindi, use simple space joining
        # For English, try to be smarter about punctuation
        result = parts[0]
        
        for i in range(1, len(parts)):
            part = parts[i]
            
            # Check if we need space
            if target_lang in ['eng_Latn', 'eng']:
                # English: smart spacing
                if result and not result[-1] in '.,!?;:' and not part[0] in '.,!?;:':
                    result += " " + part
                else:
                    result += part
            else:
                # Telugu/Hindi: simple space
                if result and part:
                    result += " " + part
                else:
                    result += part
        
        return result.strip()

