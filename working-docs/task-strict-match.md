I want to add a boolean attribute `require_exact_match` to all the editing tools.

When `require_exact_match = false`, for each line in `old_string`, ignore leading and trailing whitespaces when matching against the current state of the file. For example:


`old_string = " hello\n  \tworld"` would be able to match the below 2 lines, even though the number and type of whitespaces are different
```
   hello
   world
```

However, `old_string = " hello\n  \tworld"` would NOT be able to match the below 3 lines, because of the newlines.

```
   hello

   world
```

When `require_exact_match = true`, it will follow the existing behaviour.


In the description of the `require_exact_match` attribute, you must mention something to the effect of:
- The default value users should set is `false`
- If users set `true`, they MUST carefully count and ensure that the number and type of whitespaces on each line matches the existing text exactly.
