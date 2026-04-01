"""Skill Exporter - Import/export skills in various formats.

Provides serialization and import capabilities for skills in
JSON, YAML, and packaged formats for sharing and backup.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SkillExporter:
    """Export and import skills in various formats.
    
    Supports:
    - Individual skill export (JSON, YAML)
    - Batch skill packing (multiple skills)
    - Format conversion
    - Metadata preservation
    
    Example:
        >>> exporter = SkillExporter()
        >>> # Export single skill
        >>> exporter.export_skill(skill_data, format="json")
        >>> # Export multiple
        >>> exporter.pack_skills([skill1, skill2], "skill_pack.zip")
        >>> # Import
        >>> skill = exporter.import_skill("skill_backup.json")
    """

    def __init__(self):
        """Initialize exporter."""
        logger.debug("Initialized SkillExporter")

    def export_skill(
        self,
        skill_data: Dict[str, Any],
        skill_name: str,
        format: str = "json",
        include_metadata: bool = True,
    ) -> str:
        """Export a single skill to string.

        Args:
            skill_data: The skill data to export
            skill_name: Name for the export
            format: Export format (json, yaml)
            include_metadata: Include metadata in export

        Returns:
            Exported skill as string
        """
        export_data = {
            "skill_name": skill_name,
            "export_format_version": "1.0",
            "export_time": datetime.now().isoformat(),
            "skill": skill_data.copy(),
        }

        if not include_metadata:
            # Remove metadata from export
            export_data["skill"].pop("metadata", None)

        if format == "json":
            return json.dumps(export_data, indent=2, default=str)
        elif format == "yaml":
            try:
                import yaml
                return yaml.dump(export_data, default_flow_style=False)
            except ImportError:
                logger.warning("YAML not available, falling back to JSON")
                return json.dumps(export_data, indent=2, default=str)
        else:
            logger.error(f"Unknown format: {format}")
            return ""

    def export_skill_to_file(
        self,
        skill_data: Dict[str, Any],
        skill_name: str,
        file_path: str,
        format: str = "json",
    ) -> bool:
        """Export a skill to file.

        Args:
            skill_data: The skill data
            skill_name: Skill name
            file_path: Path to save file
            format: Export format

        Returns:
            True if successful
        """
        try:
            content = self.export_skill(skill_data, skill_name, format)
            
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            
            logger.info(f"Exported skill to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export skill: {e}")
            return False

    def import_skill(
        self,
        content: str,
        format: str = "json",
    ) -> Optional[Dict[str, Any]]:
        """Import a skill from string.

        Args:
            content: Skill content (JSON/YAML string)
            format: Content format

        Returns:
            Skill data if successful, None otherwise
        """
        try:
            if format == "json":
                data = json.loads(content)
            elif format == "yaml":
                try:
                    import yaml
                    data = yaml.safe_load(content)
                except ImportError:
                    logger.error("YAML not available")
                    return None
            else:
                logger.error(f"Unknown format: {format}")
                return None

            # Validate structure
            if "skill" not in data:
                logger.error("Invalid skill format: missing 'skill' key")
                return None

            skill = data["skill"]
            
            # Clean up import metadata
            skill["metadata"] = skill.get("metadata", {})
            skill["metadata"]["imported_at"] = datetime.now().isoformat()
            
            logger.info(f"Imported skill: {data.get('skill_name')}")
            return skill

        except Exception as e:
            logger.error(f"Failed to import skill: {e}")
            return None

    def import_skill_from_file(
        self,
        file_path: str,
        format: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Import a skill from file.

        Args:
            file_path: Path to skill file
            format: File format (auto-detect if None)

        Returns:
            Skill data if successful
        """
        try:
            path = Path(file_path)
            content = path.read_text()

            # Auto-detect format if not provided
            if format is None:
                if file_path.endswith(".json"):
                    format = "json"
                elif file_path.endswith(".yaml") or file_path.endswith(".yml"):
                    format = "yaml"
                else:
                    format = "json"  # Default to JSON

            return self.import_skill(content, format)
        except Exception as e:
            logger.error(f"Failed to import from file: {e}")
            return None

    def pack_skills(
        self,
        skills: List[Dict[str, Any]],
        output_path: str,
        description: str = "",
    ) -> bool:
        """Pack multiple skills into a single archive.

        Args:
            skills: List of skill data
            output_path: Path to output archive
            description: Pack description

        Returns:
            True if successful
        """
        try:
            import zipfile
            
            pack_data = {
                "pack_format_version": "1.0",
                "created_at": datetime.now().isoformat(),
                "description": description,
                "skill_count": len(skills),
                "skills": skills,
            }

            # Create temporary JSON file and zip it
            temp_file = "/tmp/skill_pack.json"
            Path(temp_file).write_text(
                json.dumps(pack_data, indent=2, default=str)
            )

            # Create zip archive
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(temp_file, arcname="skills.json")
                
                # Add individual skill files
                for i, skill in enumerate(skills):
                    skill_content = json.dumps(
                        {
                            "skill": skill,
                            "skill_name": skill.get("name", f"skill_{i}"),
                        },
                        indent=2,
                        default=str,
                    )
                    zf.writestr(
                        f"skills/{i}_{skill.get('name', 'skill')}.json",
                        skill_content,
                    )

            logger.info(f"Packed {len(skills)} skills to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to pack skills: {e}")
            return False

    def unpack_skills(
        self,
        archive_path: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Unpack skills from archive.

        Args:
            archive_path: Path to skill pack archive

        Returns:
            List of skills if successful
        """
        try:
            import zipfile
            
            archive = Path(archive_path)
            if not archive.exists():
                logger.error(f"Archive not found: {archive_path}")
                return None

            skills = []
            with zipfile.ZipFile(archive, "r") as zf:
                # Read main manifest
                if "skills.json" in zf.namelist():
                    manifest_content = zf.read("skills.json").decode()
                    manifest = json.loads(manifest_content)
                    skills = manifest.get("skills", [])

            logger.info(f"Unpacked {len(skills)} skills from {archive_path}")
            return skills

        except Exception as e:
            logger.error(f"Failed to unpack skills: {e}")
            return None

    def convert_format(
        self,
        skill_data: Dict[str, Any],
        from_format: str,
        to_format: str,
    ) -> str:
        """Convert skill between formats.

        Args:
            skill_data: The skill data
            from_format: Source format
            to_format: Target format

        Returns:
            Converted content
        """
        # For now, both JSON and YAML can be converted through a common format
        skill_name = skill_data.get("name", "skill")
        
        # Export to common format first
        common = self.export_skill(skill_data, skill_name, from_format)
        
        # Import and re-export in target format
        imported = self.import_skill(common, from_format)
        if imported:
            return self.export_skill(imported, skill_name, to_format)
        return ""

    def get_export_stats(
        self,
        skills: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Get statistics about skills to be exported.

        Args:
            skills: List of skills

        Returns:
            Export statistics
        """
        total_size = sum(
            len(json.dumps(s, default=str))
            for s in skills
        )

        return {
            "skill_count": len(skills),
            "total_size_bytes": total_size,
            "average_skill_size_bytes": total_size // len(skills) if skills else 0,
            "skill_names": [s.get("name", "unknown") for s in skills],
        }
