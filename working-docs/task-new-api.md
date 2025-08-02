The goal is to move away from requiring the hashes for the file / ranges in the editing APIs. 

Instead, we will move to an easier to use mechanism:
- Instead of a range hash, users will specify the current contents of the range as a string directly in the API.
- File hash is no longer required for APIs

There will also be (breaking) changes to the API format to faciliate this:

`patch_text_file_contents`

Current Request Format:

```json
{
  "files": [
    {
      "file_path": "file1.txt",
      "hash": "sha256-hash-from-get-contents",
      "encoding": "utf-8",  // Optional, defaults to utf-8
      "patches": [
        {
          "start": 5,
          "end": 8,
          "range_hash": "sha256-hash-of-content-being-replaced",
          "contents": "New content for lines 5-8\n"
        },
        {
          "start": 15,
          "end": null,  // null means end of file
          "range_hash": "sha256-hash-of-content-being-replaced",
          "contents": "Content to append\n"
        }
      ]
    }
  ]
}
```

New Request Format:

```json
{
  "files": [
    {
      "file_path": "file1.txt",
      "encoding": "utf-8",  // Optional, defaults to utf-8
      "patches": [
        {
          "old_string": "Existing content to be replaced for lines 5-8 and 10-12\n",
          "new_string": "New content for lines 5-8 and 10-12\n"
          "ranges": [
              { "start": 5, "end": 8 },
              { "start": 10, "end": 12 }
          ]
        },
        {
          "old_string": "Existing content to be replaced\n",
          "new_string": "Content to append\n"
          "ranges": [
              { "start": 15, "end": null } // null means end of file
          ]
        }
      ]
    }
  ]
}
```
