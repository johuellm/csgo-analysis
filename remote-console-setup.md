
# How to setup a remote console for Spyder in WSL2

Information from:
https://docs.spyder-ide.org/current/faq.html?highlight=run%20cell#install-wsl2


Run from working directory. It makes it easier.

```
python3.11 -m spyder_kernels.console --matplotlib="inline" --ip=127.0.0.1 -f=remotemachine.json &
```


