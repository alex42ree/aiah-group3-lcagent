from typing import List, Optional
from langchain_core.tools import BaseTool  # Updated import
from pydantic import BaseModel, Field
import xml.etree.ElementTree as ET

class PortExtractorInput(BaseModel):
    """Input for the port extractor tool."""
    xml_content: str = Field(description="The XML content containing port information")
    port_type: Optional[str] = Field(
        default=None,
        description="Optional filter for specific port types (e.g., 'container', 'bulk', 'general')"
    )

class PortExtractorTool(BaseTool):
    """Tool for extracting port names from XML documents containing ISO port information."""
    
    name: str = "port_extractor"
    description: str = """Use this tool to extract port names from XML documents containing ISO port information.
    The XML should contain port elements with name attributes or nested name elements.
    You can optionally filter by port type if specified."""
    args_schema: type[BaseModel] = PortExtractorInput

    def _extract_port_name(self, port_element: ET.Element) -> Optional[str]:
        """Extract port name from a port element using various possible XML structures."""
        # Try to get name from attribute
        if port_element.get('name'):
            return port_element.get('name')
        
        # Try to get name from nested name element
        name_elem = port_element.find('name')
        if name_elem is not None and name_elem.text:
            return name_elem.text.strip()
        
        # Try to get name from portName element
        port_name_elem = port_element.find('portName')
        if port_name_elem is not None and port_name_elem.text:
            return port_name_elem.text.strip()
        
        return None

    def _run(self, xml_content: str, port_type: Optional[str] = None) -> List[str]:
        """Extract port names from the XML content.
        
        Args:
            xml_content: The XML content containing port information
            port_type: Optional filter for specific port types
            
        Returns:
            List of port names found in the XML
        """
        try:
            # Parse XML content
            root = ET.fromstring(xml_content)
            
            # Find all port elements
            # Try different possible XML structures
            port_elements = (
                root.findall('.//port') or  # Direct port elements
                root.findall('.//Port') or  # Capital P
                root.findall('.//PORT') or  # All caps
                root.findall('.//portInfo') or  # Alternative element name
                root.findall('.//PortInfo')  # Capital P alternative
            )
            
            port_names = []
            for port_elem in port_elements:
                # Check port type if specified
                if port_type:
                    port_type_elem = port_elem.find('type')
                    if port_type_elem is None or port_type_elem.text != port_type:
                        continue
                
                # Extract port name
                port_name = self._extract_port_name(port_elem)
                if port_name:
                    port_names.append(port_name)
            
            return port_names
            
        except ET.ParseError as e:
            return [f"Error parsing XML: {str(e)}"]
        except Exception as e:
            return [f"Error processing ports: {str(e)}"]

    async def _arun(self, xml_content: str, port_type: Optional[str] = None) -> List[str]:
        """Async implementation of the port extraction."""
        return self._run(xml_content, port_type) 