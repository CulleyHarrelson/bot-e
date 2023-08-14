#!/bin/bash

#psql -h botty-dev.cluster-chki9sxssda8.us-east-2.rds.amazonaws.com -U postgres 
#psql -h botty-dev.cluster-chki9sxssda8.us-east-2.rds.amazonaws.com -U postgres \

psql -h bot-e.cluster-chki9sxssda8.us-east-2.rds.amazonaws.com -U postgres \
    "user=postgres sslrootcert=global-bundle.pem sslmode=verify-full"
