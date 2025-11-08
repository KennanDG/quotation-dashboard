from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas.dto import ProjectCreate, ProjectRead
from schemas.models import Project

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    p = Project(**payload.model_dump())
    db.add(p); 
    db.commit(); 
    db.refresh(p)
    return p

@router.get("/", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()