#!/usr/bin/env python3
"""
Check ACTUAL current models on OpenRouter - Updated August 2025
"""
import requests
import json
from datetime import datetime

def get_current_models():
    """Fetch current models from OpenRouter"""
    url = "https://openrouter.ai/api/v1/models"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            
            # Filter for YOUR requested models
            target_models = {
                'grok': [],
                'claude': [],
                'gpt': [],
                'deepseek': [],
                'qwen': [],
                'gemini': []
            }
            
            for model in models:
                model_id = model.get('id', '')
                model_name = model.get('name', '')
                
                # Check for each type
                if 'grok' in model_id.lower():
                    target_models['grok'].append({'id': model_id, 'name': model_name})
                elif 'claude' in model_id.lower():
                    target_models['claude'].append({'id': model_id, 'name': model_name})
                elif 'gpt' in model_id.lower() or 'openai' in model_id.lower():
                    target_models['gpt'].append({'id': model_id, 'name': model_name})
                elif 'deepseek' in model_id.lower():
                    target_models['deepseek'].append({'id': model_id, 'name': model_name})
                elif 'qwen' in model_id.lower():
                    target_models['qwen'].append({'id': model_id, 'name': model_name})
                elif 'gemini' in model_id.lower() or 'google' in model_id.lower():
                    target_models['gemini'].append({'id': model_id, 'name': model_name})
            
            # Print findings
            print("🔥 CURRENT OPENROUTER MODELS (August 2025)")
            print("=" * 60)
            
            for category, models_list in target_models.items():
                if models_list:
                    print(f"\n📍 {category.upper()} MODELS:")
                    for m in models_list[:5]:  # Top 5
                        print(f"  • {m['id']} - {m['name']}")
            
            # Save to file
            with open('.sophia/CURRENT_MODELS.json', 'w') as f:
                json.dump(target_models, f, indent=2)
            
            print(f"\n✅ Full list saved to .sophia/CURRENT_MODELS.json")
            print(f"Total models available: {len(models)}")
            
            return target_models
            
    except Exception as e:
        print(f"Error fetching models: {e}")
        return None

if __name__ == "__main__":
    get_current_models()
