#!/bin/bash

storage_account=$ARTIFACT_STORAGE_ACCOUNT_NAME
container_name=$ARTIFACT_STORAGE_CONTAINER_NAME
account_key=$ARTIFACT_STORAGE_ACCOUNT_KEY

upload_file() {
    file=$1
    name="$(basename $file .whl)"
    if az storage blob exists --account-name $storage_account --container-name $container_name --name $name --account-key $account_key ; then
        echo "$file already exists, skipping"
    else
        echo "uploading $file..."
        az storage blob upload --account-name $storage_account --container-name $container_name --file $file --account-key $account_key
    fi
}

files=./python/graphrag/dist/*.whl
for file in $files
do 
    upload_file $file
done