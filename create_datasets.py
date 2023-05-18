"""Create dataset and upload to S3"""

import datetime
import os
import time

import boto3
import numpy as np
import pandas as pd

import covid

N = 7
OUT_DATA = "out/covid.csv"
S3_BUCKET = "rwright-covid"
S3_OBJECT = "covid.csv"


def main():
    print(f"{datetime.datetime.now()} Script start")

    t0 = time.time()
    dir_name = os.path.dirname(OUT_DATA)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    df = covid.get_data(n=N)
    df = df[(df["date"] < "2023-03-01") & df["pop"].notna() & (df["type"] != "county")]
    df = df.round(2)
    elapsed = int(time.time() - t0)
    print(f"{datetime.datetime.now()} Getting data took: {str(elapsed)} seconds")

    t0 = time.time()
    df.to_csv(OUT_DATA, index=False)
    elapsed = int(time.time() - t0)
    print(f"{datetime.datetime.now()} Writing file took: {str(elapsed)} seconds")

    t0 = time.time()
    s3 = boto3.resource("s3")
    s3.meta.client.upload_file(OUT_DATA, S3_BUCKET, S3_OBJECT)
    elapsed = int(time.time() - t0)
    print(f"{datetime.datetime.now()} Uploading file: {str(elapsed)} seconds")

    print(f"{datetime.datetime.now()} Script complete")


if __name__ == "__main__":
    main()
