"""
Verify AI service functionality
Run from project root: uv run python verify_ai.py

NOTE: This requires a valid OpenAI API key in your .env file
"""

from services.ai_service import get_ai_service


def verify_ai_service():
    """Verify AI service can perform text analysis"""
    
    print("=" * 60)
    print("AI Service Verification")
    print("=" * 60)
    
    try:
        # Initialize service
        print("\n1. Initializing AI service...")
        ai_service = get_ai_service()
        print("   ✅ AI service initialized")
        
        # Test text analysis
        print("\n2. Testing text analysis...")
        test_text = "My laptop screen keeps flickering and I can't get any work done. This is very urgent!"
        
        try:
            analysis = ai_service.analyze_text(test_text)
            print(f"   ✅ Text analysis complete")
            print(f"      Intent: {analysis.get('intent', {}).get('type', 'unknown')}")
            print(f"      Urgency Score: {analysis.get('urgency_score', 0)}")
            print(f"      Sentiment: {analysis.get('emotion', {}).get('sentiment', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Text analysis failed: {e}")
            return
        
        # Test intent classification
        print("\n3. Testing intent classification...")
        try:
            intent = ai_service.classify_intent(test_text)
            print(f"   ✅ Intent classified: {intent.get('type', 'unknown')}")
            print(f"      Confidence: {intent.get('confidence', 0)}")
        except Exception as e:
            print(f"   ⚠️  Intent classification failed: {e}")
        
        # Test entity extraction
        print("\n4. Testing entity extraction...")
        try:
            entities = ai_service.extract_entities(test_text)
            print(f"   ✅ Entities extracted")
            if entities:
                print(f"      Products: {entities.get('product_mentions', [])}")
                print(f"      Error codes: {entities.get('error_codes', [])}")
        except Exception as e:
            print(f"   ⚠️  Entity extraction failed: {e}")
        
        # Test urgency calculation
        print("\n5. Testing urgency calculation...")
        try:
            urgency = ai_service.calculate_urgency(test_text)
            print(f"   ✅ Urgency calculated: {urgency}")
            if urgency > 0.7:
                print(f"      Status: HIGH URGENCY")
            elif urgency > 0.4:
                print(f"      Status: MEDIUM URGENCY")
            else:
                print(f"      Status: LOW URGENCY")
        except Exception as e:
            print(f"   ⚠️  Urgency calculation failed: {e}")
        
        # Test solution generation
        print("\n6. Testing solution generation...")
        test_context = {
            "ticket_info": {
                "title": "Laptop screen flickering",
                "description": "Screen flickers intermittently",
                "category": "hardware",
                "product_type": "laptop"
            },
            "conversation_flow": [
                {
                    "speaker": "customer",
                    "message": test_text,
                    "timestamp": "2025-01-25T10:00:00Z"
                }
            ]
        }
        
        try:
            solution = ai_service.generate_solution(test_context, [])
            print(f"   ✅ Solution generated")
            print(f"      Confidence: {solution.get('confidence', 0)}")
            print(f"      Difficulty: {solution.get('estimated_difficulty', 'unknown')}")
            print(f"      Steps: {len(solution.get('steps', []))} step(s)")
            print(f"      Requires escalation: {solution.get('requires_escalation', False)}")
            if solution.get('steps'):
                print(f"      First step: {solution['steps'][0][:60]}...")
        except Exception as e:
            print(f"   ⚠️  Solution generation failed: {e}")
        
        # Test context summary generation
        print("\n7. Testing context summary generation...")
        try:
            summary = ai_service.generate_context_summary(
                "Laptop screen flickering",
                "Customer reports intermittent screen flickering",
                []
            )
            print(f"   ✅ Context summary generated")
            print(f"      Summary: {summary[:100]}...")
        except Exception as e:
            print(f"   ⚠️  Context summary generation failed: {e}")
        
        print("\n" + "=" * 60)
        print("✅ AI service verification complete!")
        print("=" * 60)
        print("\n💡 Note: Image analysis and audio transcription")
        print("   require actual media files to test.")
        print("\n📝 Whisper model will be downloaded on first audio use.")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ AI service verification failed: {e}")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Check your .env file has a valid OPENAI_API_KEY")
        print("2. Verify the API key starts with 'sk-'")
        print("3. Ensure you have OpenAI API credits")
        print("=" * 60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verify_ai_service()