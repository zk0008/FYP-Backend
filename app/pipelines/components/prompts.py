IMAGE_DESCRIPTION_PROMPT = """
Your task is to accurately describe what is in the provided image. Be as detailed as possible in your description.

Use the following steps to guide your description.

<steps>
1. Summarize what the image shows overall in 1 to 2 sentences.
2. If the image contains distinct elements (e.g., graph, table, block of text, embedded images), handle them as such:
    2.1. Graphs: Extract axes titles, units, scales, data series names, key data points/trends, colors/legends annotations, and include them in your description.
    2.2. Tables: List column headers, data types (numeric/categorical), number of rows, highlighted/summary rows, and include them in your description.
    2.3. Diagrams: Describe each labeled part, its relationships/arrows, any flow or hierarchy, and include them in your description.
    2.4. Text blocks (including code blocks): Include a full transcription of the visible text in your description.
    2.5. Images/Objects: Note attributes like count, color, arrangement, and context of the images/objects, and include them in your description.
3. If the image does not contain distinct elements, thoroughly describe the image on top of the earlier summary in step 1.
</steps>

Strictly refer to the following format instructions to guide your response generation.

<format>
You must begin your response with an open curly brace: {
The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}
the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.

Here is the output schema:
```
{"properties": {"image_description": {"description": "Description of input image", "title": "Image Description", "type": "string"}}, "required": ["image_description"]}
```
</format>
"""
