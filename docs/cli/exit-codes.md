(cli-exit-codes)=

# Exit Codes

tmuxp uses standard exit codes for scripting and automation.

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error (config validation, tmux command failure) |
| `2` | Usage error (invalid arguments, missing required options) |

## Usage in Scripts

```bash
#!/bin/bash
tmuxp load my-workspace.yaml
if [ $? -ne 0 ]; then
    echo "Failed to load workspace"
    exit 1
fi
```

```bash
#!/bin/bash
tmuxp load -d my-workspace.yaml || {
    echo "tmuxp failed with exit code $?"
    exit 1
}
```
