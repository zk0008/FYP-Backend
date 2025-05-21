from langchain.output_parsers import PydanticOutputParser
from langchain.output_parsers.fix import OutputFixingParser

from app.llms import gpt_41_nano
from .models import ImageDescription

img_desc_parser = PydanticOutputParser(pydantic_object=ImageDescription)
img_desc_reparser = OutputFixingParser.from_llm(llm=gpt_41_nano, parser=img_desc_parser)
