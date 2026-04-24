"""
Two-stage LLM suggestion engine using Anthropic Claude.
"""

import os
import json
from typing import Dict, List, Optional
from anthropic import Anthropic

class Suggester:
    """Two-stage LLM suggestion pipeline."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        self.model = 'claude-3-sonnet-20240229'
    
    def suggest(self, api_name: str, chemistry_description: str) -> Dict:
        """
        Run two-stage suggestion pipeline.
        
        Returns:
            Full suggestion schema with CQAs, CPPs, design recommendation.
        """
        # Stage 1: Classify and extract
        stage1 = self._stage1_classify(chemistry_description)
        
        # If too vague, return early with clarification questions
        if stage1.get('clarification_needed', False):
            return {
                'api_name': api_name,
                'unit_operation': stage1.get('unit_operation', 'unknown'),
                'unit_operation_confidence': 'low',
                'extracted_facts': stage1.get('extracted_facts', {}),
                'suggested_CQAs': [],
                'suggested_CPPs': [],
                'clarification_questions': stage1.get('clarification_questions', []),
                'requires_chemist_review': True,
                'review_reasons': ['Input too vague for confident suggestions'],
            }
        
        # Stage 2: Suggest CQAs/CPPs/design
        stage2 = self._stage2_suggest(stage1, chemistry_description)
        
        return stage2
    
    def _stage1_classify(self, chemistry: str) -> Dict:
        """Stage 1: Classify chemistry and extract facts."""
        prompt = f"""You are a pharmaceutical process development expert. Analyze the following chemistry description and extract structured information.

Chemistry description: {chemistry}

Return ONLY a JSON object with this exact structure:
{{
    "unit_operation": "string (e.g., Suzuki coupling, hydrogenation, crystallization)",
    "confidence": "high|medium|low",
    "extracted_facts": {{
        "substrates": ["list"],
        "catalyst": "string or null",
        "solvent": "string or null",
        "temperature": "string or null",
        "time": "string or null",
        "scale": "string or null",
        "base": "string or null"
    }},
    "clarification_needed": boolean,
    "clarification_questions": ["if clarification_needed is true, list questions"]
}}

Rules:
- If the chemistry is too vague (less than 20 words, no specific reagents), set clarification_needed=true
- For Suzuki couplings, identify boronic acid/ester and halide
- For hydrogenations, identify catalyst and pressure
- Flag safety concerns: organometallics, H2 pressure, azides, peroxides"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            # Extract JSON
            json_start = content.find('{')
            json_end = content.rfind('}')
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end+1])
            else:
                return {'clarification_needed': True, 'clarification_questions': ['Could not parse chemistry description']}
        except Exception as e:
            return {'clarification_needed': True, 'clarification_questions': [f'Error: {str(e)}']}
    
    def _stage2_suggest(self, stage1: Dict, chemistry: str) -> Dict:
        """Stage 2: Suggest CQAs, CPPs, and design."""
        prompt = f"""Based on the following chemistry analysis, suggest CQAs, CPPs, and experimental design for a QbD-DOE study.

Unit operation: {stage1.get('unit_operation', 'unknown')}
Extracted facts: {json.dumps(stage1.get('extracted_facts', {}))}
Full chemistry: {chemistry}

Return ONLY a JSON object with this exact structure:
{{
    "api_name": "string",
    "unit_operation": "string",
    "unit_operation_confidence": "high|medium|low",
    "extracted_facts": {{...}},
    "suggested_CQAs": [
        {{
            "name": "string",
            "unit": "string",
            "target": number,
            "lower_spec": number,
            "upper_spec": number,
            "weight": 1-5,
            "goal": "maximize|minimize|target",
            "rationale": "string",
            "confidence": "high|medium|low"
        }}
    ],
    "suggested_CPPs": [
        {{
            "name": "string",
            "unit": "string",
            "type": "continuous|categorical",
            "low": number,
            "center": number,
            "high": number,
            "categorical_levels": ["if categorical"],
            "rationale": "string",
            "confidence": "high|medium|low",
            "safety_flag": boolean
        }}
    ],
    "deferred_factors": [{{"name": "string", "reason": "string"}}],
    "noise_factors": ["string"],
    "recommended_design": {{
        "type": "CCD|BBD|DSD|factorial|frac_factorial",
        "n_factors": number,
        "estimated_n_runs": number,
        "center_points": number,
        "replicates": number,
        "rationale": "string"
    }},
    "alternative_designs": [
        {{"type": "string", "n_runs": number, "tradeoff": "string"}}
    ],
    "requires_chemist_review": boolean,
    "review_reasons": ["string"],
    "clarification_questions": ["string"],
    "safety_warnings": ["string"]
}}

HARD RULES:
- Max 7 CPPs, max 5 CQAs
- Never propose temperature above solvent boiling point without flagging pressurized conditions
- Never propose sub-stoichiometric base for deprotonation
- Flag organometallic / H2 pressure / azide / peroxide chemistry with safety_flag: true
- For Suzuki: suggest temperature, catalyst loading, time, base equivalents, solvent ratio
- CQAs: assay, total impurities, yield (minimum)
- Weight impurities higher (4-5) than yield (2-3)
- Use realistic ranges based on chemistry knowledge"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            json_start = content.find('{')
            json_end = content.rfind('}')
            if json_start >= 0 and json_end > json_start:
                result = json.loads(content[json_start:json_end+1])
                result['api_name'] = stage1.get('api_name', 'Unnamed API')
                return result
            else:
                return self._fallback_suggestion(stage1)
        except Exception as e:
            return self._fallback_suggestion(stage1)
    
    def _fallback_suggestion(self, stage1: Dict) -> Dict:
        """Fallback if LLM fails."""
        unit_op = stage1.get('unit_operation', 'chemical_reaction')
        
        # Generic suggestions
        return {
            'api_name': 'Unnamed API',
            'unit_operation': unit_op,
            'unit_operation_confidence': 'low',
            'extracted_facts': stage1.get('extracted_facts', {}),
            'suggested_CQAs': [
                {'name': 'Assay', 'unit': '%', 'target': 98, 'lower_spec': 95, 'upper_spec': 102, 'weight': 5, 'goal': 'target', 'rationale': 'Critical quality attribute', 'confidence': 'high'},
                {'name': 'Total Impurities', 'unit': '%', 'target': 0.5, 'lower_spec': 0, 'upper_spec': 2.0, 'weight': 5, 'goal': 'minimize', 'rationale': 'Patient safety', 'confidence': 'high'},
                {'name': 'Yield', 'unit': '%', 'target': 85, 'lower_spec': 70, 'upper_spec': 100, 'weight': 3, 'goal': 'maximize', 'rationale': 'Economic viability', 'confidence': 'high'},
            ],
            'suggested_CPPs': [
                {'name': 'Temperature', 'unit': '°C', 'type': 'continuous', 'low': 60, 'center': 80, 'high': 100, 'rationale': 'Reaction kinetics', 'confidence': 'medium', 'safety_flag': False},
                {'name': 'Catalyst Loading', 'unit': 'mol%', 'type': 'continuous', 'low': 1, 'center': 3, 'high': 5, 'rationale': 'Rate control', 'confidence': 'medium', 'safety_flag': False},
                {'name': 'Time', 'unit': 'h', 'type': 'continuous', 'low': 2, 'center': 4, 'high': 8, 'rationale': 'Conversion', 'confidence': 'medium', 'safety_flag': False},
            ],
            'deferred_factors': [],
            'noise_factors': ['Raw material lot', 'Operator', 'Equipment'],
            'recommended_design': {'type': 'CCD', 'n_factors': 3, 'estimated_n_runs': 20, 'center_points': 5, 'replicates': 1, 'rationale': 'Standard RSM approach'},
            'alternative_designs': [{'type': 'BBD', 'n_runs': 15, 'tradeoff': 'Fewer runs but no axial points'}],
            'requires_chemist_review': True,
            'review_reasons': ['LLM suggestion failed - using generic defaults'],
            'clarification_questions': ['Please verify all ranges against process knowledge'],
            'safety_warnings': [],
        }
