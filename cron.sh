#!/bin/bash

source ./venv/bin/activate

rm ~/tmp/nytimes.pdf
nymarkable create-edition ~/tmp/nytimes.pdf

if [ -e ~/tmp/nytimes.pdf ]; then
    rmapi rm /Reading/Archive/nytimes
    rmapi mv /Reading/nytimes /Reading/Archive/
    rmapi put ~/tmp/nytimes.pdf /Reading/
fi