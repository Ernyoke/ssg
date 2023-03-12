# ssg

ssg - *Static Site Generator* used to generate my static site: [https://ernyoke.github.io](https://ernyoke.github.io/index.html)

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
  "baseHref": "https://ervinszilagyi.dev",
  "meta": {
    "og:title": "Ervin Szilágyi - Personal site",
    "og:image": "images/glider-banner.jpg",
    "og:description": "Personal web page and blog.",
    "og:url": "https://ervinszilagyi.dev"
  },
    "frames": [
    {
      "file": "src/index.md",
      "frame": "src/articles/index_frame.html"
    },
    {
      "file": "src/articles/*.md",
      "frame": "src/articles/article_frame.html"
    },
    {
      "file": "src/*.md",
      "frame": "src/index_frame.html"
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

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run `ssg`

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

4. Install dependencies:

```bash
pip3 install -r requirements.txt
```
5. Run `ssg`