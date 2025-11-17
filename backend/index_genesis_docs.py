"""
Index Genesis Documentation into Search Database

Parses genesis_docs.xml and indexes into FTS5 + vector database
for hybrid semantic + keyword search.
"""

import asyncio
import xml.etree.ElementTree as ET
import os
import sys
from pathlib import Path
from docs_search import GenesisDocsSearch

async def index_xml_docs(xml_path: str, db_path: str = "./backend/DATA/genesis_docs.db"):
    """
    Parse genesis_docs.xml and index all documentation.

    Args:
        xml_path: Path to genesis_docs.xml
        db_path: Path to database file
    """
    print(f"📚 Indexing Genesis documentation from: {xml_path}")

    if not os.path.exists(xml_path):
        print(f"❌ Error: File not found: {xml_path}")
        return

    # Initialize search
    searcher = GenesisDocsSearch(db_path=db_path)

    # Parse XML
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        print(f"✅ Parsed XML successfully")
    except Exception as e:
        print(f"❌ Error parsing XML: {e}")
        return

    # Index each section
    total_indexed = 0

    for section in root.findall(".//section"):
        section_name = section.get("name", "Unknown")
        print(f"\n📖 Processing section: {section_name}")

        for api in section.findall(".//api"):
            api_name = api.get("name", "")
            description = api.findtext("description", "")
            parameters = api.findtext("parameters", "")
            example = api.findtext("example", "")

            if not api_name:
                continue

            try:
                await searcher.index_section(
                    section=section_name,
                    api_name=api_name,
                    parameters=parameters,
                    description=description,
                    example=example
                )
                total_indexed += 1
                print(f"  ✓ Indexed: {api_name}")
            except Exception as e:
                print(f"  ✗ Error indexing {api_name}: {e}")

    print(f"\n✅ Indexing complete! Total entries: {total_indexed}")

    # Print statistics
    stats = searcher.get_stats()
    print(f"\n📊 Database Statistics:")
    print(f"  FTS5 entries: {stats['fts_count']}")
    print(f"  Vector entries: {stats['vector_count']}")
    print(f"  Sections: {', '.join(stats['sections'])}")


async def test_search(db_path: str = "./backend/DATA/genesis_docs.db"):
    """Test the search functionality"""
    print("\n🔍 Testing search functionality...\n")

    searcher = GenesisDocsSearch(db_path=db_path)

    # Test queries
    test_queries = [
        ("RayTracer camera setup", "hybrid"),
        ("PBR material properties", "hybrid"),
        ("physics simulation", "fts"),
        ("realistic lighting", "vector")
    ]

    for query, method in test_queries:
        print(f"\n📝 Query: '{query}' (method: {method})")
        results = await searcher.search(query, method=method, limit=3)

        if results:
            for i, result in enumerate(results, 1):
                api_name = result.get("api_name", "N/A")
                section = result.get("section", "N/A")
                method_used = result.get("method", "N/A")
                print(f"  {i}. {api_name} ({section}) [via {method_used}]")

                # Show snippet
                content = result.get("description") or result.get("content", "")
                snippet = content[:100] + "..." if len(content) > 100 else content
                print(f"     {snippet}")
        else:
            print("  No results found")


async def main():
    """Main entry point"""
    # Determine paths
    xml_path = "genesis_docs.xml"

    # Check if file exists in current directory or backend directory
    if not os.path.exists(xml_path):
        xml_path = "./backend/genesis_docs.xml"

    if not os.path.exists(xml_path):
        print("❌ Error: genesis_docs.xml not found in current directory or backend/")
        print("Please ensure genesis_docs.xml is in the correct location")
        return

    # Index documentation
    await index_xml_docs(xml_path)

    # Test search
    await test_search()


if __name__ == "__main__":
    asyncio.run(main())
