import json
from django.core.management.base import BaseCommand
from doctor.models import ICD10Entry

class Command(BaseCommand):
    help = "Import ICD-10 JSON into the database with proper parent-child linking"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file", type=str, help="Path to your icd10.json file"
        )

    def handle(self, *args, **kwargs):
        json_file = kwargs["json_file"]
        self.stdout.write(self.style.WARNING(f"Loading ICD-10 from {json_file}..."))

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        def insert_node(node, parent=None):
            """
            Recursively insert a node and its children.
            Fills missing labels with 'Unknown'.
            Links parent correctly.
            """
            label = node.get("label") or "Unknown"
            entry, created = ICD10Entry.objects.get_or_create(
                code=node["code"],
                defaults={
                    "label": label,
                    "kind": node["kind"],
                    "parent": parent,
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Inserted {entry.code} ({entry.kind})"))

            for child in node.get("children", []):
                insert_node(child, entry)

        # Top-level chapters
        for chapter in data:
            insert_node(chapter)

        self.stdout.write(self.style.SUCCESS("✅ ICD-10 import completed!"))
