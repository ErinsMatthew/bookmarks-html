# Create Bookmarks HTML File

A Python script to convert a text-based list of URLs to an HTML file you can import into your browser.

## Create List of URLs

```sh
$ cat > urls.txt
https://www.google.com/
https://www.etsy.com/
```

## Create and Activate [Virtual Environment](https://docs.python.org/3/library/venv.html)

```sh
$ python3 -m venv .venv
$ . .venv/bin/activate
```

## Install Required Dependencies

```sh
(.venv) $ pip install -r requirements.txt
```

## Run Script

```sh
(.venv) $ python bookmark.py
```
