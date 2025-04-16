"""Text analysis command for SimpleAgent.

This module provides the text_analysis command for analyzing text data.
"""

import re
import string
import math
from typing import Dict, Any, List, Tuple, Optional
from collections import Counter
from commands import register_command


def text_analysis(
    text: str,
    analysis_types: List[str] = ["keywords", "statistics", "sentiment", "summary"],
    max_keywords: int = 10,
    summary_ratio: float = 0.2
) -> Dict[str, Any]:
    """
    Analyze text data to extract keywords, statistics, sentiment, and summaries.
    
    Args:
        text: The text to analyze
        analysis_types: Types of analysis to perform (keywords, statistics, sentiment, summary)
        max_keywords: Maximum number of keywords to extract
        summary_ratio: Ratio of original text length for summary (0.1-0.5)
        
    Returns:
        Dictionary containing the analysis results
    """
    # Ensure text is not empty
    if not text or not text.strip():
        return {
            "error": "Empty text provided for analysis",
            "text_length": 0
        }
    
    # Initialize results
    results = {
        "text_length": len(text),
        "text_preview": text[:100] + "..." if len(text) > 100 else text
    }
    
    # Basic text cleaning for analysis
    cleaned_text = text.lower()
    cleaned_text = re.sub(r'<.*?>', '', cleaned_text)  # Remove HTML tags
    cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text)  # Remove punctuation
    
    # Get words and sentences
    words = re.findall(r'\b\w+\b', cleaned_text)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Calculate basic statistics
    if "statistics" in analysis_types:
        word_count = len(words)
        sentence_count = len(sentences)
        avg_word_length = sum(len(word) for word in words) / max(1, word_count)
        avg_sentence_length = word_count / max(1, sentence_count)
        
        results["statistics"] = {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": text.count('\n\n') + 1,
            "average_word_length": round(avg_word_length, 1),
            "average_sentence_length": round(avg_sentence_length, 1),
            "unique_word_count": len(set(words))
        }
    
    # Extract keywords
    if "keywords" in analysis_types:
        # Common English stop words to exclude
        stop_words = set([
            "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
            "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
            "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
            "theirs", "themselves", "this", "that", "these", "those", "am", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "having", "do",
            "does", "did", "doing", "would", "should", "could", "ought", "i'm", "you're",
            "he's", "she's", "it's", "we're", "they're", "i've", "you've", "we've",
            "they've", "i'd", "you'd", "he'd", "she'd", "we'd", "they'd", "i'll", "you'll",
            "he'll", "she'll", "we'll", "they'll", "isn't", "aren't", "wasn't", "weren't",
            "hasn't", "haven't", "hadn't", "doesn't", "don't", "didn't", "won't", "wouldn't",
            "shan't", "shouldn't", "can't", "cannot", "couldn't", "mustn't", "let's", "that's",
            "who's", "what's", "here's", "there's", "when's", "where's", "why's", "how's",
            "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while",
            "of", "at", "by", "for", "with", "about", "against", "between", "into", "through",
            "during", "before", "after", "above", "below", "to", "from", "up", "down", "in",
            "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "any", "both", "each", "few",
            "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very"
        ])
        
        # Filter out stop words and very short words
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count word frequency
        word_counts = Counter(filtered_words)
        
        # Extract top keywords
        keywords = word_counts.most_common(max_keywords)
        
        results["keywords"] = {
            "count": len(keywords),
            "top_keywords": [{"word": word, "frequency": count} for word, count in keywords]
        }
    
    # Perform simple sentiment analysis
    if "sentiment" in analysis_types:
        # Basic positive and negative word lists
        positive_words = set([
            "good", "great", "excellent", "positive", "wonderful", "fantastic", "amazing",
            "love", "happy", "joy", "success", "successful", "beautiful", "best", "better",
            "outstanding", "perfect", "impressive", "awesome", "superb", "brilliant",
            "delightful", "pleasant", "remarkable", "exceptional", "marvelous", "terrific",
            "enjoyable", "favorable", "nice", "satisfying", "valuable", "beneficial",
            "effective", "efficient", "reliable", "helpful", "useful", "innovative",
            "impressive", "authentic", "genuine"
        ])
        
        negative_words = set([
            "bad", "terrible", "poor", "negative", "awful", "horrible", "hate", "dislike",
            "sad", "failure", "worse", "worst", "disappointing", "disappoints", "disappointed",
            "difficult", "hard", "problem", "issue", "concern", "trouble", "fail", "fails",
            "failed", "failing", "inadequate", "inferior", "mediocre", "unsatisfactory",
            "useless", "ineffective", "inefficient", "unreliable", "harmful", "damage",
            "dangerous", "risky", "severe", "serious", "critical", "wrong", "error", "mistake",
            "fault", "flawed", "broken", "defective", "frustrating", "annoying", "irritating"
        ])
        
        # Count positive and negative words
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Calculate sentiment score (-1 to 1)
        total = positive_count + negative_count
        if total > 0:
            sentiment_score = (positive_count - negative_count) / total
        else:
            sentiment_score = 0
            
        # Determine sentiment category
        if sentiment_score > 0.3:
            sentiment_category = "positive"
        elif sentiment_score < -0.3:
            sentiment_category = "negative"
        else:
            sentiment_category = "neutral"
            
        results["sentiment"] = {
            "score": round(sentiment_score, 2),
            "category": sentiment_category,
            "positive_word_count": positive_count,
            "negative_word_count": negative_count
        }
    
    # Generate extractive summary
    if "summary" in analysis_types and sentences:
        # Limit summary_ratio to a reasonable range
        summary_ratio = max(0.1, min(0.5, summary_ratio))
        
        # Calculate number of sentences for summary
        num_sentences = max(1, math.ceil(len(sentences) * summary_ratio))
        
        if len(sentences) <= 3:
            # For very short texts, just include the first sentence
            summary = sentences[0]
        else:
            # For longer texts, use a simple extractive summarization approach
            
            # Calculate word frequency for all words
            word_freq = Counter(words)
            
            # Score sentences by word importance
            sentence_scores = []
            for sentence in sentences:
                # Clean sentence for scoring
                clean_sentence = sentence.lower()
                clean_sentence = re.sub(r'[^\w\s]', '', clean_sentence)
                sentence_words = re.findall(r'\b\w+\b', clean_sentence)
                
                # Don't score very short sentences
                if len(sentence_words) < 3:
                    continue
                
                # Calculate score based on word frequency
                score = sum(word_freq[word] for word in sentence_words if word not in stop_words)
                # Normalize by sentence length to avoid bias towards longer sentences
                normalized_score = score / len(sentence_words)
                
                sentence_scores.append((sentence, normalized_score))
            
            # Sort sentences by score
            ranked_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
            
            # Select top sentences for summary
            top_sentences = ranked_sentences[:num_sentences]
            
            # Sort selected sentences by their original order
            summary_sentences = []
            for sentence in sentences:
                if any(sentence == s[0] for s in top_sentences):
                    summary_sentences.append(sentence)
                if len(summary_sentences) >= num_sentences:
                    break
            
            # Join summary sentences
            summary = " ".join(summary_sentences)
        
        results["summary"] = {
            "text": summary,
            "length": len(summary),
            "ratio": round(len(summary) / len(text), 2)
        }
    
    return results


# Define the schema for the text_analysis command
TEXT_ANALYSIS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "text_analysis",
        "description": "Analyze text to extract keywords, statistics, sentiment, and generate summaries",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to analyze"
                },
                "analysis_types": {
                    "type": "array",
                    "description": "Types of analysis to perform",
                    "items": {
                        "type": "string",
                        "enum": ["keywords", "statistics", "sentiment", "summary"]
                    },
                    "default": ["keywords", "statistics", "sentiment", "summary"]
                },
                "max_keywords": {
                    "type": "integer",
                    "description": "Maximum number of keywords to extract",
                    "default": 10
                },
                "summary_ratio": {
                    "type": "number",
                    "description": "Ratio of original text length for summary (0.1-0.5)",
                    "default": 0.2
                }
            },
            "required": ["text"]
        }
    }
}

# Register the command
register_command("text_analysis", text_analysis, TEXT_ANALYSIS_SCHEMA) 