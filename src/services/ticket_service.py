"""Ticket management service with conversation history and privacy screening integration."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import Ticket, TicketMessage
from ..database.schemas import (
    TicketCreate,
    TicketUpdate, 
    TicketResponse,
    TicketListResponse,
    TicketSummaryResponse,
    TicketMessageCreate,
    TicketMessageResponse,
    TicketStatus,
    SenderType,
)
from .privacy_screening import get_privacy_screening_service
from .language_service import get_language_service

logger = logging.getLogger(__name__)


class TicketService:
    """Service for managing customer service tickets and conversations."""
    
    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the ticket service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.language_service = get_language_service()
    
    def _generate_ticket_id(self) -> str:
        """
        Generate a unique, readable ticket ID.
        
        Returns:
            Formatted ticket ID (e.g., TKT-20241201-A1B2C3D4)
        """
        date_str = datetime.now().strftime("%Y%m%d")
        uuid_part = str(uuid4())[:8].upper()
        return f"TKT-{date_str}-{uuid_part}"
    
    async def create_ticket(self, ticket_data: TicketCreate) -> TicketResponse:
        """
        Create a new customer service ticket with privacy screening.
        
        Args:
            ticket_data: Ticket creation data
            
        Returns:
            Created ticket response
        """
        try:
            # Detect language if not specified or auto-detect needed
            if not ticket_data.language or ticket_data.language == "auto":
                detected_language = self.language_service.detect_language_simple(
                    f"{ticket_data.subject} {ticket_data.content}"
                )
                ticket_data.language = detected_language
            
            # Get privacy screening service
            privacy_service = await get_privacy_screening_service()
            
            # Screen subject and content for PII
            subject_screening = await privacy_service.screen_content(
                ticket_data.subject,
                ticket_data.language
            )
            content_screening = await privacy_service.screen_content(
                ticket_data.content,
                ticket_data.language
            )
            
            # Check if screening passed confidence threshold
            if not subject_screening.is_safe or not content_screening.is_safe:
                logger.warning(
                    f"Privacy screening failed for ticket creation. "
                    f"Subject confidence: {subject_screening.confidence_score:.3f}, "
                    f"Content confidence: {content_screening.confidence_score:.3f}"
                )
                # In production, might want to handle this differently
                # For now, we'll continue but log the issue
            
            # Generate unique ticket ID
            ticket_id = self._generate_ticket_id()
            
            # Create ticket record
            ticket = Ticket(
                ticket_id=ticket_id,
                customer_name=ticket_data.customer_name,
                customer_email=str(ticket_data.customer_email),
                customer_phone=ticket_data.customer_phone,
                subject=subject_screening.screened_text,
                category=ticket_data.category.value if ticket_data.category else None,
                language=ticket_data.language.value if hasattr(ticket_data.language, 'value') else ticket_data.language,
                priority=ticket_data.priority.value if hasattr(ticket_data.priority, 'value') else ticket_data.priority,
                status="open",
            )
            
            self.db.add(ticket)
            
            # Create initial message
            initial_message = TicketMessage(
                ticket_id=ticket_id,
                sender_type=SenderType.CUSTOMER.value,
                content=content_screening.screened_text,
                original_content=ticket_data.content,
                is_screened=True,
            )
            
            self.db.add(initial_message)
            
            # Commit transaction
            await self.db.commit()
            
            # Refresh to get relationships
            await self.db.refresh(ticket)
            await self.db.refresh(initial_message)
            
            # Load messages relationship
            query = select(Ticket).where(Ticket.ticket_id == ticket_id).options(
                selectinload(Ticket.messages)
            )
            result = await self.db.execute(query)
            ticket_with_messages = result.scalar_one()
            
            logger.info(f"Created ticket {ticket_id} for {ticket_data.customer_email}")
            
            return TicketResponse.model_validate(ticket_with_messages)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create ticket: {e}")
            raise
    
    async def get_ticket(self, ticket_id: str) -> Optional[TicketResponse]:
        """
        Get a ticket by ID with all messages.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket response or None if not found
        """
        try:
            query = select(Ticket).where(Ticket.ticket_id == ticket_id).options(
                selectinload(Ticket.messages)
            )
            result = await self.db.execute(query)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return None
            
            return TicketResponse.model_validate(ticket)
            
        except Exception as e:
            logger.error(f"Failed to get ticket {ticket_id}: {e}")
            raise
    
    async def update_ticket(
        self, 
        ticket_id: str, 
        ticket_update: TicketUpdate
    ) -> Optional[TicketResponse]:
        """
        Update a ticket.
        
        Args:
            ticket_id: Ticket ID
            ticket_update: Update data
            
        Returns:
            Updated ticket response or None if not found
        """
        try:
            query = select(Ticket).where(Ticket.ticket_id == ticket_id)
            result = await self.db.execute(query)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return None
            
            # Update fields
            if ticket_update.subject is not None:
                # Screen updated subject
                privacy_service = await get_privacy_screening_service()
                subject_screening = await privacy_service.screen_content(
                    ticket_update.subject,
                    ticket.language
                )
                ticket.subject = subject_screening.screened_text
            
            if ticket_update.status is not None:
                ticket.status = ticket_update.status.value
            
            if ticket_update.priority is not None:
                ticket.priority = ticket_update.priority.value
            
            if ticket_update.category is not None:
                ticket.category = ticket_update.category.value
            
            # Update timestamp
            ticket.updated_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            await self.db.refresh(ticket)
            
            # Get updated ticket with messages
            return await self.get_ticket(ticket_id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update ticket {ticket_id}: {e}")
            raise
    
    async def add_message(
        self,
        ticket_id: str,
        message_data: TicketMessageCreate,
        sender_type: SenderType = SenderType.CUSTOMER,
        attachment_info: Optional[Dict] = None
    ) -> Optional[TicketMessageResponse]:
        """
        Add a message to a ticket conversation.
        
        Args:
            ticket_id: Ticket ID
            message_data: Message data
            sender_type: Type of sender
            attachment_info: Optional attachment metadata
            
        Returns:
            Created message response or None if ticket not found
        """
        try:
            # Check if ticket exists
            ticket_query = select(Ticket).where(Ticket.ticket_id == ticket_id)
            ticket_result = await self.db.execute(ticket_query)
            ticket = ticket_result.scalar_one_or_none()
            
            if not ticket:
                return None
            
            # Screen message content
            privacy_service = await get_privacy_screening_service()
            content_screening = await privacy_service.screen_content(
                message_data.content,
                ticket.language
            )
            
            # Create message
            message = TicketMessage(
                ticket_id=ticket_id,
                sender_type=sender_type.value if hasattr(sender_type, 'value') else sender_type,
                content=content_screening.screened_text,
                original_content=message_data.content,
                is_screened=True,
                attachment_info=attachment_info,
                parent_message_id=message_data.parent_message_id,
            )
            
            self.db.add(message)
            
            # Update ticket timestamp
            ticket.updated_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            await self.db.refresh(message)
            
            logger.info(f"Added message to ticket {ticket_id}")
            
            return TicketMessageResponse.model_validate(message)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to add message to ticket {ticket_id}: {e}")
            raise
    
    async def list_tickets(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[TicketStatus] = None,
        category: Optional[str] = None,
        customer_email: Optional[str] = None,
    ) -> TicketListResponse:
        """
        List tickets with optional filtering and pagination.
        
        Args:
            page: Page number (1-based)
            page_size: Number of tickets per page
            status: Optional status filter
            category: Optional category filter
            customer_email: Optional customer email filter
            
        Returns:
            Paginated ticket list
        """
        try:
            # Build query with filters
            query = select(Ticket)
            conditions = []
            
            if status:
                conditions.append(Ticket.status == status.value)
            
            if category:
                conditions.append(Ticket.category == category)
            
            if customer_email:
                conditions.append(Ticket.customer_email.ilike(f"%{customer_email}%"))
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Add ordering
            query = query.order_by(Ticket.created_at.desc())
            
            # Count total records
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Add pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # Execute query with message loading
            query = query.options(selectinload(Ticket.messages))
            result = await self.db.execute(query)
            tickets = result.scalars().all()
            
            # Convert to response objects
            ticket_responses = [TicketResponse.model_validate(ticket) for ticket in tickets]
            
            has_next = offset + page_size < total
            has_previous = page > 1
            
            return TicketListResponse(
                tickets=ticket_responses,
                total=total,
                page=page,
                page_size=page_size,
                has_next=has_next,
                has_previous=has_previous,
            )
            
        except Exception as e:
            logger.error(f"Failed to list tickets: {e}")
            raise
    
    async def get_ticket_summary(self, ticket_id: str) -> Optional[TicketSummaryResponse]:
        """
        Get a summary of a ticket without full message content.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket summary or None if not found
        """
        try:
            # Query ticket with message count
            query = select(
                Ticket,
                func.count(TicketMessage.message_id).label("message_count")
            ).outerjoin(
                TicketMessage, Ticket.ticket_id == TicketMessage.ticket_id
            ).where(
                Ticket.ticket_id == ticket_id
            ).group_by(Ticket.ticket_id)
            
            result = await self.db.execute(query)
            row = result.first()
            
            if not row:
                return None
            
            ticket, message_count = row
            
            # Create summary response
            summary = TicketSummaryResponse(
                ticket_id=ticket.ticket_id,
                customer_name=ticket.customer_name,
                customer_email=ticket.customer_email,
                subject=ticket.subject,
                status=TicketStatus(ticket.status),
                priority=ticket.priority,
                category=ticket.category,
                language=ticket.language,
                message_count=message_count,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get ticket summary {ticket_id}: {e}")
            raise
    
    async def search_tickets(self, query: str, limit: int = 10) -> List[TicketSummaryResponse]:
        """
        Search tickets by content.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching ticket summaries
        """
        try:
            # Simple text search across subject and customer info
            search_query = select(Ticket).where(
                or_(
                    Ticket.subject.ilike(f"%{query}%"),
                    Ticket.customer_name.ilike(f"%{query}%"),
                    Ticket.customer_email.ilike(f"%{query}%"),
                    Ticket.ticket_id.ilike(f"%{query}%"),
                )
            ).order_by(Ticket.updated_at.desc()).limit(limit)
            
            result = await self.db.execute(search_query)
            tickets = result.scalars().all()
            
            summaries = []
            for ticket in tickets:
                # Get message count
                count_query = select(func.count()).where(
                    TicketMessage.ticket_id == ticket.ticket_id
                )
                count_result = await self.db.execute(count_query)
                message_count = count_result.scalar() or 0
                
                summary = TicketSummaryResponse(
                    ticket_id=ticket.ticket_id,
                    customer_name=ticket.customer_name,
                    customer_email=ticket.customer_email,
                    subject=ticket.subject,
                    status=TicketStatus(ticket.status),
                    priority=ticket.priority,
                    category=ticket.category,
                    language=ticket.language,
                    message_count=message_count,
                    created_at=ticket.created_at,
                    updated_at=ticket.updated_at,
                )
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Failed to search tickets: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, any]:
        """
        Get ticket statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            # Total tickets
            total_query = select(func.count()).select_from(Ticket)
            total_result = await self.db.execute(total_query)
            total_tickets = total_result.scalar()
            
            # By status
            status_query = select(
                Ticket.status,
                func.count(Ticket.ticket_id)
            ).group_by(Ticket.status)
            status_result = await self.db.execute(status_query)
            status_counts = dict(status_result.fetchall())
            
            # By category
            category_query = select(
                Ticket.category,
                func.count(Ticket.ticket_id)
            ).group_by(Ticket.category)
            category_result = await self.db.execute(category_query)
            category_counts = dict(category_result.fetchall())
            
            # By language
            language_query = select(
                Ticket.language,
                func.count(Ticket.ticket_id)
            ).group_by(Ticket.language)
            language_result = await self.db.execute(language_query)
            language_counts = dict(language_result.fetchall())
            
            return {
                "total_tickets": total_tickets,
                "by_status": status_counts,
                "by_category": category_counts,
                "by_language": language_counts,
            }
            
        except Exception as e:
            logger.error(f"Failed to get ticket statistics: {e}")
            raise