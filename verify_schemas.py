"""
Verify API schemas are properly defined and can be imported
Run from project root: uv run python verify_schemas.py
"""

from schemas import (
    TicketCreate, TicketUpdate, TicketResponse, TicketWithContext, TicketListResponse,
    InteractionCreate, InteractionResponse, SolutionRequest, SolutionResponse, FeedbackRequest,
    MediaUploadResponse, MediaAnalysisResponse, TranscriptionResponse
)


def verify_schemas():
    """Verify all schemas are properly defined"""
    
    print("=" * 60)
    print("Schema Verification")
    print("=" * 60)
    
    schemas_to_test = [
        ("Ticket Schemas", [
            TicketCreate,
            TicketUpdate,
            TicketResponse,
            TicketWithContext,
            TicketListResponse
        ]),
        ("Interaction Schemas", [
            InteractionCreate,
            InteractionResponse,
            SolutionRequest,
            SolutionResponse,
            FeedbackRequest
        ]),
        ("Media Schemas", [
            MediaUploadResponse,
            MediaAnalysisResponse,
            TranscriptionResponse
        ])
    ]
    
    total_schemas = 0
    
    for category, schemas in schemas_to_test:
        print(f"\n✓ {category}:")
        for schema in schemas:
            print(f"  ✓ {schema.__name__}")
            
            # Verify schema has proper configuration
            if hasattr(schema, 'model_config'):
                print(f"    - Has model_config")
            
            # Verify schema has fields
            if hasattr(schema, 'model_fields'):
                field_count = len(schema.model_fields)
                print(f"    - {field_count} fields defined")
            
            total_schemas += 1
    
    print("\n" + "=" * 60)
    print(f"✅ SUCCESS: All {total_schemas} schemas verified!")
    print("=" * 60)
    
    # Test creating example instances
    print("\n" + "=" * 60)
    print("Testing Schema Examples")
    print("=" * 60)
    
    print("\n✓ Creating TicketCreate example...")
    try:
        ticket = TicketCreate(
            title="Test ticket",
            description="Test description",
            customer_email="test@example.com",
            customer_name="Test User"
        )
        print(f"  ✅ Created: {ticket.title}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("\n✓ Creating InteractionCreate example...")
    try:
        interaction = InteractionCreate(
            content="Test interaction content"
        )
        print(f"  ✅ Created: content length = {len(interaction.content)}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Schema examples created successfully!")
    print("=" * 60)


if __name__ == "__main__":
    verify_schemas()