# ssg

ssg - *Static Site Generator* used to generate my static site: [https://ernyoke.github.io](https://ernyoke.github.io/index.html)

## Install

```bash
git clone git@github.com:Ernyoke/ssg.git
cd ssg
pip3 install .
```

## Usage

```bash
usage: python -m ssg [-h] source destination base_path

positional arguments:
  source       Source folder from which the files has to be parsed.
  destination  Destination folder where the results will be stored.
  base_path    Base path of the page.
```

## Development

### Windows

1. Clone the project:
   
```bash
git@github.com:Ernyoke/ervin-szilagyi-static-site.git
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

## Unix

1. Clone the project:
   
```bash
git@github.com:Ernyoke/ervin-szilagyi-static-site.git
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
pip install -r requirements.txt
```
5. Run `ssg`