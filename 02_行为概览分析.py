import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Microsoft YaHei'
matplotlib.rcParams['axes.unicode_minus'] = False

INPUT_FILE = "user_behavior_clean.csv"

def load_data():
    print("加载数据...")
    df = pd.read_csv(INPUT_FILE)
    df["date_time"] = pd.to_datetime(df["date_time"])
    df["date"] = pd.to_datetime(df["date"])
    print(f"数据量 {len(df):,} 条，用户 {df['user_id'].nunique():,}，商品 {df['item_id'].nunique():,}")
    return df

def plot_behavior_pie(df):
    counts = df["behavior_type"].value_counts()
    pv, cart, fav, buy = counts.get("pv",0), counts.get("cart",0), counts.get("fav",0), counts.get("buy",0)
    print(f"PV→加购 {cart/pv*100:.2f}%  PV→收藏 {fav/pv*100:.2f}%  PV→购买 {buy/pv*100:.2f}%  加购→购买 {buy/cart*100:.2f}%")
    fig, ax = plt.subplots(figsize=(8,8))
    colors = ["#4E79A7","#F28E2B","#E15759","#76B7B2"]
    ax.pie(counts.values, labels=counts.index, autopct='%1.2f%%', colors=colors, startangle=90, explode=[0.02]*4)
    ax.set_title("用户行为类型分布")
    plt.tight_layout()
    plt.savefig("图1_行为类型占比.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 图1保存")

def plot_daily_trend(df):
    daily = df.groupby("date").agg(PV=("behavior_type",lambda x:(x=="pv").sum()),
                                    UV=("user_id","nunique"),
                                    buy=("behavior_type",lambda x:(x=="buy").sum())).reset_index()
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax1.plot(daily["date"], daily["PV"]/1e6, "o-", color="#4E79A7", label="PV(百万)")
    ax1.plot(daily["date"], daily["UV"]/1e6, "s-", color="#F28E2B", label="UV(百万)")
    ax1.set_xlabel("日期"); ax1.set_ylabel("数量（百万）")
    ax1.set_title("每日PV/UV趋势")
    ax1.legend(); ax1.grid(True, alpha=0.3)
    plt.xticks(rotation=30); plt.tight_layout()
    plt.savefig("图2_每日PVUV趋势.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 图2保存")

def plot_hourly_pattern(df):
    hourly = df[df["behavior_type"]=="pv"].groupby("hour").size().reset_index(name="pv_count")
    peak = hourly.loc[hourly["pv_count"].idxmax(), "hour"]
    print(f"最活跃时段 {peak}:00")
    fig, ax = plt.subplots(figsize=(12,5))
    colors = ["#4E79A7"]*24; colors[int(peak)] = "#E15759"
    ax.bar(hourly["hour"], hourly["pv_count"]/1e6, color=colors, edgecolor="white")
    ax.set_xlabel("小时"); ax.set_ylabel("PV(百万)"); ax.set_title("24小时活跃分布")
    ax.set_xticks(range(0,24)); ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig("图3_24小时活跃分布.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 图3保存")

def plot_user_activity_dist(df):
    user_actions = df.groupby("user_id").size().reset_index(name="action_count")
    print(f"人均行为数 {user_actions['action_count'].mean():.1f}，中位数 {user_actions['action_count'].median():.0f}")
    fig, ax = plt.subplots(figsize=(10,5))
    ax.hist(user_actions["action_count"].clip(upper=200), bins=50, color="#4E79A7", edgecolor="white")
    ax.set_xlabel("行为次数（≤200）"); ax.set_ylabel("用户数"); ax.set_title("用户活跃度分布")
    ax.axvline(user_actions["action_count"].median(), color="#E15759", linestyle="--", label=f"中位数={user_actions['action_count'].median():.0f}")
    ax.legend()
    plt.tight_layout()
    plt.savefig("图4_用户活跃度分布.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 图4保存")

def save_summary_stats(df):
    pv = (df["behavior_type"]=="pv").sum()
    buy = (df["behavior_type"]=="buy").sum()
    cart = (df["behavior_type"]=="cart").sum()
    fav = (df["behavior_type"]=="fav").sum()
    stats = {
        "总行为数": len(df), "用户数": df["user_id"].nunique(),
        "商品数": df["item_id"].nunique(),"类目数": df["category_id"].nunique(),
        "PV": pv, "购买": buy, "加购": cart, "收藏": fav,
        "PV→购买": f"{buy/pv*100:.2f}%","PV→加购": f"{cart/pv*100:.2f}%",
        "PV→收藏": f"{fav/pv*100:.2f}%","加购→购买": f"{buy/cart*100:.2f}%" if cart>0 else "N/A",
        "日期范围": f"{df['date'].min()[:10]} ~ {df['date'].max()[:10]}"
    }
    print("\n📊 统计指标：")
    for k,v in stats.items():
        print(f"  {k}: {v}")
    with open("整体统计指标.txt","w",encoding="utf-8") as f:
        for k,v in stats.items():
            f.write(f"{k}: {v}\n")
    print("✅ 统计指标保存")

if __name__ == "__main__":
    df = load_data()
    plot_behavior_pie(df)
    plot_daily_trend(df)
    plot_hourly_pattern(df)
    plot_user_activity_dist(df)
    save_summary_stats(df)
    print("Step 2 完成，下一步运行 03_转化漏斗与留存分析.py")