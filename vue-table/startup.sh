#!/bin/bash

until test -f src/config.js;
do 
    echo "Retrying ..."
done
yarn dev 

