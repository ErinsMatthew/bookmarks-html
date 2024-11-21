# Create Bookmarks HTML File

A Python script to convert a text-based list of URLs to an HTML file you can import into your browser. This script will perform a HTTP GET operation to retrieve the &lt;title&gt; and favicon (if requested) for each bookmark.

## Create List of URLs

The input URL file should contain one URL per line, and can optionally include the name of a folder and subfolder to place the resulting bookmark into. The folder and subfolder separators can be set via the `folder_separator` and `subfolder_separator` configuration values respectively.

```sh
$ cat > urls.txt
https://www.google.com/
https://www.etsy.com/
```

or

```sh
$ cat > urls.txt
Search|https://www.google.com/
Shopping,Handmade|https://www.etsy.com/
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

## Configuration

Configuration is stored in a file named [`config.yml`](config.yml).

| Name | Default Value | Description |
| ---- | ------------- | ----------- |
| urls_file | urls.txt | The path to a text file containing bookmark URLs. One URL per line. File should be encoded as UTF-8 |
| folder_separator | \| | Value to use to separate folder names. |
| subfolder_separator | , | Value to use to separate subfolder names. |
| bookmarks_html_file | bookmarks.html | The path to a text file which this script will write bookmarks in HTML format. Will be encoded as UTF-8. |
| timeout | 60 | Number of seconds before the Web request times out. |
| log_file | bookmark.log | The path to a log file. Will be encoded as UTF-8. |
| log_level | DEBUG | Log level to use for logger. See [Python documentation](https://docs.python.org/3/library/logging.html). |
| rewrite_url | true | Rewrite the URL if a redirect occurs. Can cause undesired effects if redirected to a login page. Valid values include `true` or `false`. |
| sort | true | Whether to sort the list of bookmarks when writing to HTML. Valid values include `true` or `false`. |
| favicon | true | Whether to retrieve and include the favicon or not. Valid values include `true` or `false`. |
| sleep | 0 | Number of milliseconds to sleep between retrieving information about each bookmark. |
| random_sleep | true | Whether to randomize the sleep value. Multiplies the `sleep` value by a random number between 0 and 1. Valid values include `true` or `false`. |
| headers | See YAML. | List of `name` and `value` pairs for headers to send with each request. |

# Future Enhancements

- [ ] Improved sorting.
- [ ] Improved bot avoidance handling.
- [ ] Finish favicon handling.
