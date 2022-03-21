# NYMarkable

> PDF version of NYTimes for the reMarkable

## Install


```bash
$ pip install git+https://github.com/mynameisfiber/nymarkable.git
```


## Usage


### Logging in

To set your system up, first login to nytimes,

```
$ nymarkable login
```

When you are done logging in, close the browser.


### Create standalone PDF

```
$ nymarkable create-edition nytimes.pdf
```

This will download the current edition of the NYTimes and create `nytimes.pdf`. Note that if the browser being used isn't logged in, you will get a visible browser pop up for you to login with. Just close the browser once you are logged in and the creation edition will continue.


### Create edition and send to remarkable

Same as creating a standalone PDF but we also get to supply a device IP. This curently uses the USB web interface to do the upload, so that feature should be enabled and the device connected to your machine.

```
$ nymarkable update-device --device-ip 10.11.99.1 --filename nytimes.pdf
```

Both of these arguments are optional and default to the above values. This may also trigger a login window which you should close once you've logged in


## TODO

- [ ] Support more than just today's version
- [ ] Target filenames not working on reMarkable2?
- [ ] Support for profile location as top level argument
