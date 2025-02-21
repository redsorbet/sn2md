# Supernote to text converter (sn2md)

A CLI tool to convert Supernote `.note`, PDFs, and images  to using any LLM supported by the [LLM library](https://llm.datasette.io/en/stable/plugins/directory.html).

![Supernote to Markdown](docs/supernote-to-markdown.png)

Sample output: [20240712_151149.md](./docs/20240712_151149/20240712_151149.md)

The default LLM prompt with gpt-4o-mini is configured to convert images to markdown:

- Supports markdown in .note files (#tags, `## Headers`, `[[Links]]`, etc)
- Supports basic formatting (lists, tables, etc)
- Converts of images of diagrams to [mermaid](https://mermaid.js.org).
- Handles math equations using `$` and `$$` latex math blocks.

## Installation

```sh
pip install sn2md
```

Setup your **OPENAI_API_KEY** environment variable.

## Usage

To import a single Supernote `.note` file, use the `file` command:

```sh
# import one .note file (or PDF, image):
sn2md file <path_to_note_file>

# import a directory of .note files (or PDFs, images):
sn2md directory <path_to_directory>
```

Notes:
- If the source file has not changed, repeated runs of commands will print a warning and exit. You can force re-runs by running with the `--force` flag.
- If the source file has not changed, but the output file has (b/c _maybe_ you modified it manually by adding your own notes?) repeated runs of commands will print a warning and exit. You can force the command with the `--force` flag.


## Configuration

A configuration file can be used to override the program defaults. The
default location is platform specific (eg, `~/Library/Application Support/sn2md.toml` on OSX, `~/.config/sn2md.toml` on Linux, etc).

Values that you can configure:
- `template`: The output template to generate markdown.
- `output_filename_template`: The filename that is generated. Basic template variables are available. (default: `{{file_basename}}.md`).
- `output_path_template`: The directory that is created to store output. Basic template variables are available. (default: `{{file_basename}}`).
- `prompt`: The prompt sent to the LLM. Requires a `{context}` placeholder
  to help the AI understand the context of the previous page.
- `title_prompt`: The prompt sent to the OpenAI API to decode any titles (H1-H4 supernote highlights).
- `model`: The model to use (default: `gpt-4o-mini`). Supports OpenAI out of the box, but additional providers can be configured (see below).
- `api_key`: Your Service provider's API key (defaults to the environmental variable required by the model you've provided. For instance, for OpenAI models `$OPENAI_API_KEY`).

Example instructing the AI to convert text to pirate speak:

```toml
model = "gemini-1.5-pro-latest"
prompt = """###
Context (what the last couple lines of the previous page were converted to markdown):
{context}
###
Convert the following image to markdown:
- Don't convert diagrams or images. Just output "<IMAGE>" on a newline.
- Paraphrase all the text in pirate speak.
"""

template = """
# Pirate Speak
{{llm_output}}
"""
```

### Prompt

The default prompt sent to the LLM is:

```markdown
###
Context (the last few lines of markdown from the previous page):
{context}
###
Convert the image to markdown:
- If there is a simple diagram that the mermaid syntax can achieve, create a mermaid codeblock of it.
- When it is unclear what an image is, don't output anything for it.
- Use $$, $ latex math blocks for math equations.
- Support Obsidian syntaxes and dataview "field:: value" syntax.
- Do not wrap text in codeblocks.
```

This can be overridden in the configuration file. For example, to have underlined text converted to an Obsidian internal link you could append `- Convert any underlined words to internal wiki links (double brackets).`.

### Output Template

You can provide your own [jinja template](https://jinja.palletsprojects.com/en/3.1.x/templates/#synopsis), if you prefer to customize the markdown
output. The default template is:

```jinja
---
created: {{year_month_day}}
tags: supernote
---

{{llm_output}}

# Images
{% for image in images %}
- ![{{ image.name }}]({{image.name}})
{%- endfor %}

{% if keywords %}
# Keywords
{% for keyword in keywords %}
- Page {{ keyword.page_number }}: {{ keyword.content }}
{%- endfor %}
{%- endif %}

{% if links %}
# Links
{% for link in links %}
- Page {{ link.page_number }}: {{ link.type }} {{ link.inout }} [[{{ link.name | replace('.note', '')}}]]
{%- endfor %}
{%- endif %}

{% if titles %}
# Titles
{% for title in titles %}
- Page {{ title.page_number }}: Level {{ title.level }} "{{ title.content }}"
{%- endfor %}
{%- endif %}
```

Several variables are available to the template.

Basic data about the source file (.note, etc):
- `file_name`: The file name (including its extension).
- `file_basename`: The file name without its extension.
- `year_month_day`: The date the source file was created (eg, 2024-05-12).
- `year`: The year the source file was created (eg, 2024).
- `month`: The month the source file was created (eg, 05).
- `day`: The day the source file was created (eg, 12).
- `hour`: The hour the source file was created (eg, 13).
- `minute`: The minute the source file was created (eg, 13).

Data extracted when converting the source file:
- `llm_output`: The content of the source file (deprecated `markdown` field still available as well).
- `images`: an array of image objects with the following properties:
  - `name`: The name of the image file.
  - `rel_path`: The relative path to the image file to where the file was run
    from.
  - `abs_path`: The absolute path to the image file.

Data available in .note source files:
- `links`: an array of links in or out of a .note file with the following properties:
  - `page_number`: The page number the link is on.
  - `type`: The link type (page, file, web)
  - `name`: The basename of the link (url, page, web)
  - `device_path`: The full path of the link
  - `inout`: The direction of the link (in, out)
- `keywords`: an array of keywords in a .note file with the following properties:
  - `page_number`: The page number the keyword is on.
  - `content`: The content of the keyword.
- `titles`: an array of titles in a .note file with the following properties:
  - `page_number`: The page number the title is on.
  - `level`: The level of the title (1-4).
  - `content`: The content of the title. If the area of the title appears to be text,
    the text, otherwise a description of it.

### Other LLM Models

This tool uses [llm](https://llm.datasette.io/), which [supports many services](https://llm.datasette.io/en/stable/other-models.html). You can use any of these models by specifying the model, as long is it a multi-modal model that supports visual inputs (such as gpt-4o-mini, llama3.2-vision, etc).

Here are a couple examples of using this tool with other models.

#### Gemini

To use Gemini:

- Get [a Gemini API key](https://ai.google.dev/gemini-api/docs/api-key). Set this as the `api_key` in the configuration file, or as the `LLM_GEMINI_KEY` environmental variable.
- Install the [gemini llm API](https://llm.datasette.io/en/stable/plugins/directory.html#remote-apis).
- Specify the model in the configuration file as `model`, or use the `--model` CLI flag.

```sh
export LLM_GEMINI_KEY=yourkey
llm install llm-gemini

sn2md -m gemini-1.5-pro-latest file <path_to_note_file>
```

Notes: The default prompt appears to work well with Gemini. Your mileage may vary!

#### Ollama

You can run your own local LLM modals using [Ollama](https://ollama.com/) (or [other supported local methods](https://llm.datasette.io/en/stable/plugins/directory.html#local-models)), using an LLM that supports visual inputs:
- Install Ollama, and install a model that supports visual inputs.
- Install the [ollama llm plugin](https://github.com/taketwo/llm-ollama).
- Specify the model in the configuration file as `model`, or use the `--model` CLI flag.

```sh
# Run ollama in one terminal:
ollama serve

# In another terminal, install a model, and plugin support:
ollama pull llama3.2-vision:11b

llm install llm-ollama
sn2md -m llama3.2-vision:11b file <path_to_note_file>
```

Notes: The default prompt does NOT work well with `llama3.2-vision:11b`. You will need to provide a custom prompt in the configuration file. Basic testing showed this configuration provided basic OCR capabilities (probably not mermaid, ore other markdown features!):

```toml
model = "llama3.2-vision:11b"
prompt = """###
Context (the last few lines of markdown from the previous page):
{context}
###
You are an OCR program. Extract text from the image and format as paragraphs of plain markdown text.
"""
```

Please let me know if you find better prompts!

### Output formats

You can output other formats besides markdown. Contributed examples of configuration files are listed below.

#### Emacs Orgmode

@redsorbet contributed this configuration. Note the use of `output_filename_template` to change the output extension:

```toml
output_filename_template = "{{file_basename}}.org"

template = """
#+title: {{file_basename}}
#+filetags: supernote
{{markdown}}
* Images
{% for image in images %}
- [[{{image.rel_path}}][{{image.name}}]]
{%- endfor %}
{% if keywords %}
* Keywords
{% for keyword in keywords %}
- Page {{ keyword.page_number }}: {{ keyword.content }}
{%- endfor %}
{%- endif %}
{% if links %}
* Links
{% for link in links %}
- Page {{ link.page_number }}: {{ link.type }} {{ link.inout }} [[{{ link.name | replace('.note', '')}}]]
{%- endfor %}
{%- endif %}
{% if titles %}
* Titles
{% for title in titles %}
- Page {{ title.page_number }}: Level {{ title.level }} "{{ title.content }}"
{%- endfor %}
{%- endif %}
"""

prompt = '''
###
Context (the last few lines of orgmode from the previous page):
{context}
###
Convert the image to orgmode:
- If there is a simple diagram that the mermaid syntax can achieve, create a mermaid org babel codeblock of it. Set the :file argument to a reasonable unique file name
- When it is unclear what an image is, do not output anything for it.
- Since this is org mode use latex and the standard begin and end for math equations
- Support LogSeq syntaxes and dataview "field:: value" syntax.
- Do not wrap text in codeblocks.
- Do not mention process or create extra notes.
- If there are sections then create a new org heading and use relative indentation to infer heading level
- If there is no obvious title, then create a short headline appropriate for the content.
- prefer code blocks if a programming language is mentioned
'''
```

#### HTML

A simple Supernote to HTML configuration file to create an HTML page (using tailwind for image styling):

```toml
output_filename_template = "{{file_basename}}.html"

template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
    <title>{{file_basename}}</title>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="max-w-5xl mx-auto px-4 py-8">
        <!-- Metadata -->
        <div class="mb-8 text-gray-600">
            <p>Created: <span>{{ year_month_day }}</span></p>
        </div>

        <!-- LLM Output -->
        <div class="mb-8">
            <h1>{{file_basename}}</h1>
            {{ llm_output }}
        </div>

        <!-- Images Section -->
        <div class="mb-8">
            <h2>Images</h2>
            <div class="flex flex-wrap gap-6">
                {% for image in images %}
                <img src="{{ image.name }}" alt="{{ image.name }}" class="max-w-sm border border-gray-200 rounded-md shadow-md w-1/6">
                {% endfor %}
            </div>
        </div>

        <!-- Keywords Section -->
        {% if keywords %}
        <div class="mb-8">
            <h2>Keywords</h2>
            <ul class="space-y-2">
                {% for keyword in keywords %}
                <li class="flex">
                    <span class="font-medium w-20">Page {{ keyword.page_number }}:</span>
                    <span>{{ keyword.content }}</span>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <!-- Links Section -->
        {% if links %}
        <div class="mb-8">
            <h2>Links</h2>
            <ul class="space-y-2">
                {% for link in links %}
                <li class="flex">
                    <span class="font-medium w-20">Page {{ link.page_number }}:</span>
                    <span>{{ link.type }} {{ link.inout }} <a href="#" class="text-blue-600 hover:underline">{{ link.name | replace('.note', '') }}</a></span>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <!-- Titles Section -->
        {% if titles %}
        <div class="mb-8">
            <h2>Titles</h2>
            <ul class="space-y-2">
                {% for title in titles %}
                <li class="flex">
                    <span class="font-medium w-20">Page {{ title.page_number }}:</span>
                    <span>Level {{ title.level }} "{{ title.content }}"</span>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

prompt = '''###
Context (the last few lines of HTML from the previous page/image):
{context}
###
Convert the image to text:
- Transcribe the text from the image to text.
- Style the text as HTML (assume its already within the body tag).
- Any lines that start with dashes, should be considered unordered lists.
- Use the context above to continue any lists, paragraphs or sections (ie, if its a list, assume the opening <ul> exists, continue it, and close it).
- Do not include the context above in any output.
- Do not export any markdown syntax.
- Do not use code blocks.
- Do not output anything if no text was detected.
- Ignore drawings.
'''
```

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.

### Development

```sh
git clone https://github.com/yourusername/supernote-importer.git
- [supernote-tool library](https://github.com/jya-dev/supernote-tool) for .note file parsing.
cd supernote-importer
poetry install

pytest
```

## License

This project is licensed under the AGPL License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Supernote](https://www.supernote.com/) for their amazing note-taking devices.
- [supernote-tool library](https://github.com/jya-dev/supernote-tool) for .note file parsing.
- [llm](https://llm.datasette.io/) for LLM access.
