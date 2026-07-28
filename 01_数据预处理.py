import pandas as pd
import numpy as np
import time
import os

INPUT_FILE = "UserBehavior.csv"
OUTPUT_FILE = "user_behavior_clean.csv"
SAMPLE_SIZE = 1_000_000
USE_SAMPLE = True

def load_data():
    print("读取数据...")
    start = time.time()
    if USE_SAMPLE:
        total_rows = 100_150_807
        df = pd.read_csv(INPUT_FILE, header=None,
                         names=["user_id","item_id","category_id","behavior_type","time_stamp"],
                         skiprows=lambda x: x>0 and np.random.random() > (SAMPLE_SIZE/total_rows),
                         dtype={"user_id":"int32","item_id":"int32","category_id":"int32",
                                "behavior_type":"category","time_stamp":"int64"})
    else:
        df = pd.read_csv(INPUT_FILE, header=None,
                         names=["user_id","item_id","category_id","behavior_type","time_stamp"],
                         dtype={"user_id":"int32","item_id":"int32","category_id":"int32",
                                "behavior_type":"category","time_stamp":"int64"})
    elapsed = time.time() - start
    print(f"数据量 {len(df):,} 条，耗时 {elapsed:.1f} 秒，内存 {df.memory_usage(deep=True).sum()/1024**2:.1f} MB")
    return df

def clean_data(df):
    print("清洗数据...")
    start = time.time()
    original = len(df)
    df = df[df["behavior_type"].isin(["pv","buy","cart","fav"])]
    df["time_stamp"] = pd.to_numeric(df["time_stamp"], errors="coerce")
    df = df.dropna(subset=["time_stamp"])
    df["time_stamp"] = df["time_stamp"].astype("int64")
    df = df[df["time_stamp"].between(1_000_000_000, 20_000_000_000)]
    df["date_time"] = pd.to_datetime(df["time_stamp"], unit="s")
    df["date"] = df["date_time"].dt.date.astype(str)
    df["hour"] = df["date_time"].dt.hour
    df = df[(df["date"] >= "2017-11-25") & (df["date"] <= "2017-12-03")]
    before = len(df)
    df = df.drop_duplicates()
    print(f"清洗后 {len(df):,} 条（移除 {original-len(df):,} 条无用，重复 {before-len(df):,} 条），耗时 {time.time()-start:.1f} 秒")
    return df

def save_data(df):
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"保存至 {OUTPUT_FILE}，共 {len(df):,} 条，大小 {os.path.getsize(OUTPUT_FILE)/1024**2:.1f} MB")

if __name__ == "__main__":
    df = load_data()
    df = clean_data(df)
    save_data(df)
    print("Step 1 完成，下一步运行 02_行为概览分析.py")