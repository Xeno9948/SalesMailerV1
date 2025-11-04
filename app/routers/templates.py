from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.models import Brand, EmailTemplate
from app.schemas import EmailTemplateCreate, EmailTemplateRead, EmailTemplateUpdate

router = APIRouter()


@router.get("/", response_model=list[EmailTemplateRead])
def list_templates(session: SessionDep) -> list[EmailTemplate]:
    return session.exec(select(EmailTemplate)).all()


@router.post("/", response_model=EmailTemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(payload: EmailTemplateCreate, session: SessionDep) -> EmailTemplate:
    brand = session.get(Brand, payload.brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    if payload.is_default:
        for template in session.exec(
            select(EmailTemplate).where(EmailTemplate.brand_id == brand.id, EmailTemplate.is_default == True)
        ):
            template.is_default = False
            session.add(template)

    template = EmailTemplate(**payload.model_dump())
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


@router.patch("/{template_id}", response_model=EmailTemplateRead)
def update_template(template_id: int, payload: EmailTemplateUpdate, session: SessionDep) -> EmailTemplate:
    template = session.get(EmailTemplate, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    updates = payload.model_dump(exclude_unset=True)
    if updates.get("is_default"):
        for other in session.exec(
            select(EmailTemplate).where(EmailTemplate.brand_id == template.brand_id, EmailTemplate.id != template.id)
        ):
            if other.is_default:
                other.is_default = False
                session.add(other)

    for field, value in updates.items():
        setattr(template, field, value)

    session.add(template)
    session.commit()
    session.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int, session: SessionDep) -> None:
    template = session.get(EmailTemplate, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    session.delete(template)
    session.commit()
