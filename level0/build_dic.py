#!/usr/bin/env python

words = open("test/data/words-6b898d7c48630be05b72b3ae07c5be6617f90d8e").read()
words = [word.rstrip() for word in words.split("\n")]

output = "words = {"
for word in words:
    output += '"%s"=1,' % word
output = output.rstrip(",") + "}"

open("preload.txt", "wb").write(output)
