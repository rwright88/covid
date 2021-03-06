"""Create dataset and upload to S3"""

import datetime
import os
import subprocess
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
    print(f"\n-----\nScript started at: {datetime.datetime.now()}")

    t0 = time.time()
    dir_name = os.path.dirname(OUT_DATA)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    df = covid.get_data(n=N)
    df = df[(df["date"] >= "2020-03-01") & df["pop"].notna()]
    df = df.round(2)
    print(f"Getting data took: {str(int(time.time() - t0))} seconds")

    t0 = time.time()
    df.to_csv(OUT_DATA, index=False)
    print(f"Writing file took: {str(int(time.time() - t0))} seconds")

    t0 = time.time()
    s3 = boto3.resource("s3")
    s3.meta.client.upload_file(OUT_DATA, S3_BUCKET, S3_OBJECT)
    print(f"Uploading file to S3 took: {str(int(time.time() - t0))} seconds")

    print(f"Script completed at: {datetime.datetime.now()}\n-----\n")


if __name__ == "__main__":
    main()

