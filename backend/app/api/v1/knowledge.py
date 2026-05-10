"""Knowledge base management — document upload, search."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_current_tenant_id
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.knowledge import KnowledgeDoc
from app.models.user import User
from app.domain.knowledge import KnowledgeBaseService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/docs")
async def list_docs(
    persona_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tid = get_current_tenant_id()
    query = select(KnowledgeDoc).where(KnowledgeDoc.tenant_id == tid)
    if persona_id:
        query = query.where(KnowledgeDoc.persona_id == persona_id)
    query = query.order_by(KnowledgeDoc.created_at.desc())

    result = await db.execute(query)
    docs = result.scalars().all()
    return [
        {"id": d.id, "title": d.title, "source_type": d.source_type,
         "persona_id": d.persona_id, "created_at": str(d.created_at)}
        for d in docs
    ]


@router.post("/docs/upload", status_code=status.HTTP_201_CREATED)
async def upload_doc(
    title: str,
    persona_id: str | None = None,
    content_text: str = "",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("editor")),
):
    tid = get_current_tenant_id()
    doc = KnowledgeDoc(
        tenant_id=tid,
        persona_id=persona_id,
        title=title,
        source_type="upload",
        content_text=content_text,
    )
    db.add(doc)
    await db.flush()

    # Chunk the document
    svc = KnowledgeBaseService()
    chunks = svc.chunk_document(content_text)
    # TODO: store chunks with embeddings

    return {"id": doc.id, "title": doc.title, "chunks": len(chunks)}


@router.delete("/docs/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doc(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    tid = get_current_tenant_id()
    result = await db.execute(
        select(KnowledgeDoc).where(KnowledgeDoc.id == doc_id, KnowledgeDoc.tenant_id == tid)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await db.delete(doc)
    await db.flush()


@router.post("/search")
async def search_knowledge(
    query: str,
    persona_id: str | None = None,
    top_k: int = 5,
    user: User = Depends(get_current_user),
):
    """Semantic search across knowledge base documents."""
    tid = get_current_tenant_id()
    svc = KnowledgeBaseService()
    results = await svc.hybrid_search(query, tid, persona_id, top_k)
    return {"query": query, "results": results, "total": len(results)}