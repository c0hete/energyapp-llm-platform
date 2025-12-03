from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from .. import schemas
from ..deps import get_db, require_admin_session, get_current_user_from_session
from ..models import User, SystemPrompt

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=list[schemas.SystemPromptResponse])
def list_prompts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_session),
):
    """Lista todos los prompts del sistema activos"""
    prompts = (
        db.query(SystemPrompt)
        .filter(SystemPrompt.is_active == True)
        .order_by(SystemPrompt.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return prompts


@router.get("/{prompt_id}", response_model=schemas.SystemPromptResponse)
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_session),
):
    """Obtiene un prompt específico"""
    prompt = db.query(SystemPrompt).filter(
        SystemPrompt.id == prompt_id,
        SystemPrompt.is_active == True
    ).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt no encontrado"
        )
    return prompt


@router.post("", response_model=schemas.SystemPromptResponse)
def create_prompt(
    payload: schemas.SystemPromptCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_session),
):
    """Crea un nuevo prompt del sistema (solo admins)"""
    # Verificar que no exista un prompt con el mismo nombre
    existing = db.query(SystemPrompt).filter(
        SystemPrompt.name == payload.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un prompt con este nombre"
        )

    prompt = SystemPrompt(
        name=payload.name,
        description=payload.description,
        content=payload.content,
        is_default=payload.is_default or False,
        created_by=admin.id,
    )

    # Si este es el default, desmarcar otros como default
    if prompt.is_default:
        db.query(SystemPrompt).update({SystemPrompt.is_default: False})

    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.put("/{prompt_id}", response_model=schemas.SystemPromptResponse)
def update_prompt(
    prompt_id: int,
    payload: schemas.SystemPromptUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_session),
):
    """Actualiza un prompt del sistema (solo admins)"""
    prompt = db.query(SystemPrompt).filter(
        SystemPrompt.id == prompt_id
    ).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt no encontrado"
        )

    # Actualizar campos si se proporcionan
    if payload.name is not None:
        # Verificar que no exista otro con el mismo nombre
        existing = db.query(SystemPrompt).filter(
            SystemPrompt.name == payload.name,
            SystemPrompt.id != prompt_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un prompt con este nombre"
            )
        prompt.name = payload.name

    if payload.description is not None:
        prompt.description = payload.description

    if payload.content is not None:
        prompt.content = payload.content

    if payload.is_default is not None:
        if payload.is_default:
            # Desmarcar otros como default
            db.query(SystemPrompt).update({SystemPrompt.is_default: False})
        prompt.is_default = payload.is_default

    if payload.is_active is not None:
        prompt.is_active = payload.is_active

    db.commit()
    db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_session),
):
    """Elimina un prompt del sistema (solo admins)"""
    prompt = db.query(SystemPrompt).filter(
        SystemPrompt.id == prompt_id
    ).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt no encontrado"
        )

    db.delete(prompt)
    db.commit()
