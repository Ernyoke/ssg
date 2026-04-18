# ssg

ssg - *Static Site Generator* used to generate my static site: [https://ervinszilagyi.dev](https://ervinszilagyi.dev)

## Install

```bash
uv tool install git+https://github.com/Ernyoke/ssg.git
```

## Usage

```bash
usage: ssg [-h] config

positional arguments:
  config      Path of the config.json file

options:
  -h, --help  show this help message and exit
```

Example:

```bash
ssg ./config.json
```

`config.json` content:

```json
{
  "source": "<path to source folder>",
  "destination": "<path to destination folder>",
  "hostname": "ervinszilagyi.dev",
  "baseHref": "https://ervinszilagyi.dev",
  "meta": {
    "default": {
      "og:title": "Ervin Szilágyi - Personal site",
      "og:image": "images/glider-banner.jpg",
      "og:description": "Personal web page and blog.",
      "og:url": "https://ervinszilagyi.dev"
    },
    "matchers": [
      {
        "file": "resume.md",
        "action": "STATIC",
        "meta": {
          "og:title": "Resume - ervinszilagyi.dev",
          "og:description": "Ervin's resume"
        }
      },
      {
        "file": "index.md",
        "action": "USE_DEFAULT"
      },
      {
        "file": "*.md",
        "action": "TAKE_FROM_CONTENT"
      },
      {
        "file": "articles/*",
        "action": "TAKE_FROM_CONTENT"
      }
    ]
  },
  "frames": [
    {
      "file": "index.md",
      "frame": "articles/index_frame.html"
    },
    {
      "file": "articles/*.md",
      "frame": "articles/article_frame.html"
    },
    {
      "file": "*.md",
      "frame": "index_frame.html"
    }
  ]
}
```

## Development

### Building the app

```bash
uv build
```

### Installing from local whl

```bash
uv tool install dist/ssg-*.whl
```

### Running tests

```bash
uv run pytest tests/
```