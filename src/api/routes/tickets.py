"""Ticket management API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import get_async_session
from ...database.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketListResponse,
    TicketSummaryResponse,
    TicketMessageCreate,
    TicketMessageResponse,
    TicketStatus,
    ProductCategory,
    APIResponse,
    ErrorResponse,
)
from ...services.ticket_service import TicketService
from ...utils.exceptions import TicketNotFoundError, ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer service ticket",
    description="Create a new ticket with automatic privacy screening and language detection"
)
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession = Depends(get_async_session)
) -> APIResponse:
    """
    Create a new customer service ticket.
    
    The system will automatically:
    - Detect language if not specified
    - Screen content for private information
    - Generate a unique ticket ID
    - Store conversation history
    """
    try:
        ticket_service = TicketService(db)
        ticket = await ticket_service.create_ticket(ticket_data)
        
        logger.info(f"Created ticket {ticket.ticket_id} for {ticket.customer_email}")
        
        return APIResponse(
            success=True,
            message="Ticket created successfully",
            data=ticket.model_dump()
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error creating ticket: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details,
            }
        )
    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to create ticket",
                "error_code": "TICKET_CREATION_FAILED",
            }
        )


@router.get(
    "/{ticket_id}",
    response_model=APIResponse,
    summary="Get ticket by ID",
    description="Retrieve a ticket with all messages and conversation history"
)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_async_session)
) -> APIResponse:
    """Get a ticket by ID with full conversation history."""
    try:
        ticket_service = TicketService(db)
        ticket = await ticket_service.get_ticket(ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Ticket not found",
                    "error_code": "TICKET_NOT_FOUND",
                }
            )
        
        return APIResponse(
            success=True,
            message="Ticket retrieved successfully",
            data=ticket.model_dump()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve ticket",
                "error_code": "TICKET_RETRIEVAL_FAILED",
            }
        )


@router.put(
    "/{ticket_id}",
    response_model=APIResponse,
    summary="Update ticket",
    description="Update ticket status, priority, category, or subject"
)
async def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    db: AsyncSession = Depends(get_async_session)
) -> APIResponse:
    """Update a ticket."""
    try:
        ticket_service = TicketService(db)
        ticket = await ticket_service.update_ticket(ticket_id, ticket_update)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Ticket not found",
                    "error_code": "TICKET_NOT_FOUND",
                }
            )
        
        logger.info(f"Updated ticket {ticket_id}")
        
        return APIResponse(
            success=True,
            message="Ticket updated successfully",
            data=ticket.model_dump()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to update ticket",
                "error_code": "TICKET_UPDATE_FAILED",
            }
        )


@router.post(
    "/{ticket_id}/messages",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add message to ticket",
    description="Add a new message to the ticket conversation with privacy screening"
)
async def add_message_to_ticket(
    ticket_id: str,
    message_data: TicketMessageCreate,
    db: AsyncSession = Depends(get_async_session)
) -> APIResponse:
    """Add a message to a ticket conversation."""
    try:
        ticket_service = TicketService(db)
        message = await ticket_service.add_message(
            ticket_id=ticket_id,
            message_data=message_data
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Ticket not found",
                    "error_code": "TICKET_NOT_FOUND",
                }
            )
        
        logger.info(f"Added message to ticket {ticket_id}")
        
        return APIResponse(
            success=True,
            message="Message added successfully",
            data=message.model_dump()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message to ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to add message",
                "error_code": "MESSAGE_CREATION_FAILED",
            }
        )


@router.get(
    "/",
    response_model=TicketListResponse,
    summary="List tickets",
    description="List tickets with optional filtering and pagination"
)
async def list_tickets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[TicketStatus] = Query(None, description="Filter by status"),
    category: Optional[ProductCategory] = Query(None, description="Filter by category"),
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    db: AsyncSession = Depends(get_async_session)
) -> TicketListResponse:
    """List tickets with filtering and pagination."""
    try:
        ticket_service = TicketService(db)
        
        tickets = await ticket_service.list_tickets(
            page=page,
            page_size=page_size,
            status=status,
            category=category.value if category else None,
            customer_email=customer_email,
        )
        
        return tickets
        
    except Exception as e:
        logger.error(f"Failed to list tickets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve tickets",
                "error_code": "TICKET_LIST_FAILED",
            }
        )


@router.get(
    "/{ticket_id}/summary",
    response_model=APIResponse,
    summary="Get ticket summary",
    description="Get a ticket summary without full message content"
)
async def get_ticket_summary(
    ticket_id: str,
    db: AsyncSession = Depends(get_async_session)
) -> APIResponse:
    """Get a ticket summary."""
    try:
        ticket_service = TicketService(db)
        summary = await ticket_service.get_ticket_summary(ticket_id)
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Ticket not found",
                    "error_code": "TICKET_NOT_FOUND",
                }
            )
        
        return APIResponse(
            success=True,
            message="Ticket summary retrieved successfully",
            data=summary.model_dump()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ticket summary {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve ticket summary",
                "error_code": "TICKET_SUMMARY_FAILED",
            }
        )


@router.get(
    "/search/",
    response_model=APIResponse,
    summary="Search tickets",
    description="Search tickets by content"
)
async def search_tickets(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_async_session)
) -> APIResponse:
    """Search tickets by content."""
    try:
        ticket_service = TicketService(db)
        results = await ticket_service.search_tickets(q, limit)
        
        return APIResponse(
            success=True,
            message=f"Found {len(results)} matching tickets",
            data={
                "query": q,
                "results": [result.model_dump() for result in results],
                "total": len(results)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to search tickets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to search tickets",
                "error_code": "TICKET_SEARCH_FAILED",
            }
        )


@router.get(
    "/statistics/overview",
    response_model=APIResponse,
    summary="Get ticket statistics",
    description="Get overview statistics for tickets"
)
async def get_ticket_statistics(
    db: AsyncSession = Depends(get_async_session)
) -> APIResponse:
    """Get ticket statistics."""
    try:
        ticket_service = TicketService(db)
        stats = await ticket_service.get_statistics()
        
        return APIResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get ticket statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve statistics",
                "error_code": "STATISTICS_FAILED",
            }
        )