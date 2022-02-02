#!/usr/bin/env bash

USERNAME="danishprakash"
declare REPOS="golang/tools \
    Shopify/kubeaudit \
    hashicorp/nomad \
    hashicorp/terraform-ls \
    hashicorp/vscode-terraform \
    opencontainers/runc \
    ankitects/anki \
    neovim/neovim \
    microsoft/ptvsd \
    microsoft/knack \
    auth0/auth0-python \
    google/kasane \
    python/cpython \
    python/peps \
    VSCodeVim/Vim \
    aws/aws-sam-cli \
    coala/coala-bears"


for REPO in ${REPOS}
do
    curl -s -u danishprakash:${GH_TOKEN} -H "Accept: application/vnd.github.v3+json" "https://api.github.com/repos/${REPO}/commits?author=${USERNAME}" \
        | jq '.[] |  "\(.html_url) | \(.commit.message)"' \
        | awk '
        BEGIN { FS = "|" }
        {
            split($0, a, "|")
            url=a[1]
            match(a[1], "https://github.com/(.*)/commit", org)
            split(a[2], message, "\\\\n")

            gsub(/^[ \t"]+|[ \t]+$/, "", url); gsub(/^[ \t]+|[ \t"]+$/, "", message[1])
            printf "- %s: [%s](%s)    \n", org[1], message[1], url
        }'
done
