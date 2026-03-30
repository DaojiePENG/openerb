"""
Data storage and persistence layer.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import pickle

from .types import Skill, UserProfile, RobotProfile, LearningRecord
from .config import get_storage_config
from .logger import logger


class Storage:
    """Persistent storage manager for the robot system."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize storage system."""
        config = get_storage_config()
        self.db_path = db_path or config.db_path
        self.data_dir = config.data_dir
        self.skills_dir = config.skills_dir
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Skills table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    skill_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT,
                    skill_type TEXT,
                    created_at TEXT,
                    last_modified TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    version INTEGER DEFAULT 1
                )
            """)
            
            # Robot profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS robot_profiles (
                    body_id TEXT PRIMARY KEY,
                    robot_type TEXT,
                    firmware_version TEXT,
                    created_at TEXT,
                    last_updated TEXT,
                    metadata TEXT
                )
            """)
            
            # User profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at TEXT,
                    last_seen TEXT,
                    metadata TEXT
                )
            """)
            
            # Learning records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_records (
                    record_id TEXT PRIMARY KEY,
                    skill_id TEXT,
                    robot_type TEXT,
                    learning_date TEXT,
                    trials INTEGER,
                    successes INTEGER,
                    failures INTEGER,
                    performance_metric REAL,
                    metadata TEXT
                )
            """)
            
            conn.commit()
            logger.info("Database initialized")
    
    # ========================================================================
    # Skill Management
    # ========================================================================
    
    def save_skill(self, skill: Skill) -> bool:
        """Save a skill to storage."""
        try:
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO skills 
                    (skill_id, name, description, status, skill_type, 
                     created_at, last_modified, success_count, failure_count, 
                     success_rate, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    skill.skill_id, skill.name, skill.description,
                    skill.status.value, skill.skill_type.value,
                    skill.created_at.isoformat(), skill.last_modified.isoformat(),
                    skill.success_count, skill.failure_count,
                    skill.success_rate, skill.version
                ))
                conn.commit()
            
            # Save code to file
            skill_dir = self.skills_dir / skill.status.value / skill.skill_id
            skill_dir.mkdir(parents=True, exist_ok=True)
            
            with open(skill_dir / "code.py", "w") as f:
                f.write(skill.code)
            
            with open(skill_dir / "metadata.json", "w") as f:
                json.dump({
                    "skill_id": skill.skill_id,
                    "name": skill.name,
                    "description": skill.description,
                    "tags": skill.tags,
                    "dependencies": skill.dependencies,
                    "supported_robots": [r.value for r in skill.supported_robots],
                    "skill_type": skill.skill_type.value,
                    "status": skill.status.value,
                    "version": skill.version,
                }, f, indent=2)
            
            logger.info(f"Saved skill: {skill.name} ({skill.skill_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to save skill: {e}")
            return False
    
    def load_skill(self, skill_id: str) -> Optional[Skill]:
        """Load a skill from storage."""
        try:
            # Search through status directories
            for status_dir in self.skills_dir.iterdir():
                skill_path = status_dir / skill_id
                if skill_path.exists():
                    with open(skill_path / "metadata.json", "r") as f:
                        metadata = json.load(f)
                    
                    with open(skill_path / "code.py", "r") as f:
                        code = f.read()
                    
                    # Load from database for full info
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM skills WHERE skill_id = ?", (skill_id,))
                        row = cursor.fetchone()
                        
                        if row:
                            from .types import Skill, SkillStatus, SkillType, RobotType
                            return Skill(
                                skill_id=row[0],
                                name=row[1],
                                description=row[2],
                                code=code,
                                status=SkillStatus(row[3]),
                                skill_type=SkillType(row[4]),
                                created_at=datetime.fromisoformat(row[5]),
                                last_modified=datetime.fromisoformat(row[6]),
                                success_count=row[7],
                                failure_count=row[8],
                                success_rate=row[9],
                                version=row[10],
                                tags=metadata.get("tags", []),
                                dependencies=metadata.get("dependencies", []),
                                supported_robots=[
                                    RobotType(r) for r in metadata.get("supported_robots", [])
                                ],
                            )
            
            logger.warning(f"Skill not found: {skill_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to load skill: {e}")
            return None
    
    def list_skills(self, status: Optional[str] = None) -> List[Skill]:
        """List all skills, optionally filtered by status."""
        skills = []
        
        if status:
            status_dir = self.skills_dir / status
            if status_dir.exists():
                for skill_dir in status_dir.iterdir():
                    skill = self.load_skill(skill_dir.name)
                    if skill:
                        skills.append(skill)
        else:
            for status_dir in self.skills_dir.iterdir():
                for skill_dir in status_dir.iterdir():
                    skill = self.load_skill(skill_dir.name)
                    if skill:
                        skills.append(skill)
        
        return skills
    
    # ========================================================================
    # Robot Profile Management
    # ========================================================================
    
    def save_robot_profile(self, profile: RobotProfile) -> bool:
        """Save a robot profile."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO robot_profiles
                    (body_id, robot_type, firmware_version, created_at, last_updated, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    profile.body_id,
                    profile.robot_type.value,
                    profile.firmware_version,
                    profile.created_at.isoformat(),
                    profile.last_updated.isoformat(),
                    json.dumps(profile.metadata),
                ))
                conn.commit()
            
            # Also save as JSON file
            profile_file = self.data_dir / "body_profiles" / f"{profile.body_id}.json"
            profile_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(profile_file, "w") as f:
                json.dump({
                    "body_id": profile.body_id,
                    "robot_type": profile.robot_type.value,
                    "firmware_version": profile.firmware_version,
                    "capabilities": profile.capabilities,
                    "created_at": profile.created_at.isoformat(),
                    "last_updated": profile.last_updated.isoformat(),
                    "metadata": profile.metadata,
                }, f, indent=2)
            
            logger.info(f"Saved robot profile: {profile.body_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save robot profile: {e}")
            return False
    
    def load_robot_profile(self, body_id: str) -> Optional[RobotProfile]:
        """Load a robot profile."""
        try:
            profile_file = self.data_dir / "body_profiles" / f"{body_id}.json"
            if profile_file.exists():
                with open(profile_file, "r") as f:
                    data = json.load(f)
                
                from .types import RobotProfile, RobotType
                return RobotProfile(
                    robot_type=RobotType(data["robot_type"]),
                    body_id=data["body_id"],
                    firmware_version=data["firmware_version"],
                    capabilities=data.get("capabilities", {}),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    last_updated=datetime.fromisoformat(data["last_updated"]),
                    metadata=data.get("metadata", {}),
                )
            
            return None
        except Exception as e:
            logger.error(f"Failed to load robot profile: {e}")
            return None
    
    # ========================================================================
    # User Profile Management
    # ========================================================================
    
    def save_user_profile(self, profile: UserProfile) -> bool:
        """Save a user profile."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_profiles
                    (user_id, name, created_at, last_seen, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    profile.user_id,
                    profile.name,
                    profile.created_at.isoformat(),
                    profile.last_seen.isoformat(),
                    json.dumps({
                        "face_embedding": profile.face_embedding,
                        "preferences": profile.preferences,
                    }),
                ))
                conn.commit()
            
            logger.info(f"Saved user profile: {profile.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save user profile: {e}")
            return False
    
    def load_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load a user profile."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM user_profiles WHERE user_id = ?",
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    metadata = json.loads(row[4])
                    from .types import UserProfile
                    return UserProfile(
                        user_id=row[0],
                        name=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        last_seen=datetime.fromisoformat(row[3]),
                        face_embedding=metadata.get("face_embedding"),
                        preferences=metadata.get("preferences", {}),
                    )
            
            return None
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")
            return None


# Global storage instance
_global_storage: Optional[Storage] = None


def get_storage() -> Storage:
    """Get the global storage instance."""
    global _global_storage
    if _global_storage is None:
        _global_storage = Storage()
    return _global_storage


def set_storage(storage: Storage) -> None:
    """Set the global storage instance."""
    global _global_storage
    _global_storage = storage
