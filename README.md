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


### rmfakecloud + rmapi + cron

My personal workflow is to have the [cron.sh](cron.sh) run every day on my server and
use `rmapi` to update my device with the most recent nytimes edition. The
script also makes sure that only 12 editions are on the device at any time
since I doubt I ever need more lookback than that.

Take a look at [cron.sh](cron.sh) and modify it according to your needs. I have
`nymarkable` installed with a virtualenv (directory "venv") and an "env" file
that contains the corresponding `export RMAPI_HOST=XXX` for my `rmfakecloud`
install. The cron runs once a day.

```bash
~/code/nymarkable $ ls
README.md  cron.sh  env  nymarkable  nymarkable.egg-info  nytimes.pdf  requirements.txt  setup.py  venv
```


## TODO

- [ ] Support more than just today's version
- [ ] Target filenames not working on reMarkable2?
- [ ] Support for profile location as top level argument
