# ssg

ssg - *Static Site Generator* used to generate my static site: [https://ervinszilagyi.dev](https://ervinszilagyi.dev)

## Install

### Unix

```bash
pip3 install git+ssh://git@github.com/Ernyoke/ssg.git
```

### Windows

```bash
pip install git+ssh://git@github.com/Ernyoke/ssg.git
```

## Usage

```bash
usage: ssg [-h] source destination base_path

positional arguments:
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
        "file": "src/resume.md",
        "action": "STATIC",
        "meta": {
          "og:title": "Resume - ervinszilagyi.dev",
          "og:description": "Ervin's resume"
        }
      },
      {
        "file": "src/index.md",
        "action": "USE_DEFAULT"
      },
      {
        "file": "src/*.md",
        "action": "TAKE_FROM_CONTENT"
      },
      {
        "file": "src/articles/*",
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

### Generate `requirements.txt`

```bash
pip3 install pipreqs
pip3 install pip-tools

pipreqs --savepath=requirements.in && pip-compile
```

### Windows

1. Clone the project:

    ```bash
    git clone git@github.com:Ernyoke/ervin-szilagyi-static-site.git
    ```

2. `cd` into the `ssg` folder

3. Create a virtual environment:

    ```bash
    python -m venv .
    ```

4. Activate the virtual environment:

    ```bash
    .\Scripts\activate.ps1
    ```

5. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

6. Run `ssg`

### Unix

1. Clone the project:

    ```bash
    git clone git@github.com:Ernyoke/ervin-szilagyi-static-site.git
    ```

2. `cd` into the `ssg` folder

3. Create a virtual environment:

    ```bash
    virtualenv -p python3 .
    ```

4. Activate the virtual environment:

    ```bash
    chmod +x ./bin/activate
    source ./bin/activate
    ```

5. Install dependencies:

    ```bash
    pip3 install -r requirements.txt
    ```

6. Run `ssg`