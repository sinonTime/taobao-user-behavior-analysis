import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Microsoft YaHei'
matplotlib.rcParams['axes.unicode_minus'] = False

INPUT_FILE = "user_behavior_clean.csv"

def load_data():
    df = pd.read_csv(INPUT_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df["date_time"] = pd.to_datetime(df["date_time"])
    print(f"数据量 {len(df):,} 条")
    return df

def conversion_funnel(df):
    print("\n=== 转化漏斗 ===")
    users_pv = set(df[df["behavior_type"]=="pv"]["user_id"].unique())
    users_cart = set(df[df["behavior_type"]=="cart"]["user_id"].unique())
    users_fav = set(df[df["behavior_type"]=="fav"]["user_id"].unique())
    users_buy = set(df[df["behavior_type"]=="buy"]["user_id"].unique())
    users_intent = users_cart | users_fav
    total = df["user_id"].nunique()
    funnel = {
        "步骤": ["浏览用户","意向用户","购买用户"],
        "用户数": [len(users_pv), len(users_intent), len(users_buy)]
    }
    funnel_df = pd.DataFrame(funnel)
    funnel_df["转化率"] = funnel_df["用户数"] / funnel_df["用户数"].iloc[0] * 100
    funnel_df["环节转化率"] = [100.0] + [funnel_df["用户数"].iloc[i]/funnel_df["用户数"].iloc[i-1]*100 for i in range(1,3)]
    print(funnel_df.to_string(index=False))
    
    fig, ax = plt.subplots(figsize=(10,6))
    values = funnel_df["用户数"].values / 1e6
    colors = ["#4E79A7","#F28E2B","#76B7B2"]
    bars = ax.barh(range(3), values, color=colors, height=0.6)
    for i, (bar,val,pct,step) in enumerate(zip(bars, values, funnel_df["转化率"], funnel_df["环节转化率"])):
        ax.text(val+0.05, i, f"{val:.1f}M ({pct:.1f}% → {step:.1f}%)", va="center", fontsize=12)
    ax.set_yticks(range(3)); ax.set_yticklabels(funnel_df["步骤"]); ax.set_xlabel("用户数(百万)")
    ax.set_title("用户转化漏斗"); ax.invert_yaxis(); ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout(); plt.savefig("图5_转化漏斗.png", dpi=150, bbox_inches='tight'); plt.close()
    print("✅ 图5保存")
    
    buyers = df[df["behavior_type"]=="buy"]["user_id"].unique()
    buyer_df = df[df["user_id"].isin(buyers)]
    print(f"购买用户中加购占比 {len(set(buyer_df[buyer_df['behavior_type']=='cart']['user_id']))/len(buyers)*100:.1f}%")
    print(f"购买用户中收藏占比 {len(set(buyer_df[buyer_df['behavior_type']=='fav']['user_id']))/len(buyers)*100:.1f}%")
    return funnel_df

def retention_analysis(df):
    print("\n=== 留存分析 ===")
    first_day = df.groupby("user_id")["date"].min().reset_index()
    first_day.columns = ["user_id","first_date"]
    df = df.merge(first_day, on="user_id")
    df["day_offset"] = (df["date"] - df["first_date"]).dt.days
    dates = sorted(df["first_date"].unique())
    records = []
    for d in dates:
        cohort = set(first_day[first_day["first_date"]==d]["user_id"])
        if not cohort: continue
        cohort_df = df[df["user_id"].isin(cohort)]
        for offset in range(0, min(9, (df["date"].max()-d).days+1)):
            target = d + pd.Timedelta(days=offset)
            active = set(cohort_df[cohort_df["date"]==target]["user_id"])
            rate = len(active)/len(cohort)*100
            records.append({"首日":str(d.date()),"偏移天数":offset,"留存率(%)":round(rate,2)})
    ret_df = pd.DataFrame(records)
    print(ret_df.head(20).to_string(index=False))
    
    # 留存曲线
    pivot = ret_df.pivot(index="首日", columns="偏移天数", values="留存率(%)")
    fig, ax = plt.subplots(figsize=(12,6))
    for idx in pivot.index:
        ax.plot(pivot.columns, pivot.loc[idx], marker="o", linewidth=2, label=f"首日 {idx}")
    ax.set_xlabel("距首日天数"); ax.set_ylabel("留存率(%)"); ax.set_title("用户留存曲线")
    ax.legend(loc="upper right", ncol=2); ax.grid(True, alpha=0.3)
    plt.tight_layout(); plt.savefig("图6_留存曲线.png", dpi=150, bbox_inches='tight'); plt.close(); print("✅ 图6保存")
    
    # 核心留存
    next_day = ret_df[ret_df["偏移天数"]==1]["留存率(%)"].mean()
    day3 = ret_df[ret_df["偏移天数"]==3]["留存率(%)"].mean()
    day7 = ret_df[ret_df["偏移天数"]==7]["留存率(%)"].mean()
    print(f"次日留存 {next_day:.1f}%  3日留存 {day3:.1f}%  7日留存 {day7:.1f}%")
    
    # 热力图
    fig, ax = plt.subplots(figsize=(10,6))
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(pivot.columns))); ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels([str(x) for x in pivot.index])
    ax.set_xlabel("距首日天数"); ax.set_ylabel("首次活跃日"); ax.set_title("留存热力图")
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i,j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=9,
                       color="white" if val>50 else "black")
    plt.colorbar(im, ax=ax, label="留存率(%)")
    plt.tight_layout(); plt.savefig("图7_留存热力图.png", dpi=150, bbox_inches='tight'); plt.close(); print("✅ 图7保存")
    
    # 首日行为影响
    first_actions = df[df["day_offset"]==0].groupby("user_id").size().reset_index(name="cnt")
    high = set(first_actions[first_actions["cnt"]>=5]["user_id"])
    low = set(first_actions[first_actions["cnt"]<5]["user_id"])
    d1 = pd.Timestamp("2017-11-26")
    high_ret = len(set(df[(df["user_id"].isin(high)) & (df["date"]==d1)]["user_id"]))
    low_ret = len(set(df[(df["user_id"].isin(low)) & (df["date"]==d1)]["user_id"]))
    print(f"首日行为≥5用户次日留存 {high_ret/len(high)*100:.1f}%  （<5用户 {low_ret/len(low)*100:.1f}%） 差异 {high_ret/len(high)*100 - low_ret/len(low)*100:.1f} 百分点")
    return ret_df

def user_segmentation(df):
    print("\n=== 用户分层 ===")
    base = df["date"].max()
    recency = df.groupby("user_id")["date"].max().reset_index()
    recency["R"] = (base - recency["date"]).dt.days
    frequency = df.groupby("user_id").size().reset_index(name="F")
    rf = recency.merge(frequency, on="user_id")
    r_m, f_m = rf["R"].median(), rf["F"].median()
    rf["用户分层"] = "一般用户"
    rf.loc[(rf["R"]<=r_m)&(rf["F"]>=f_m), "用户分层"] = "高价值用户"
    rf.loc[(rf["R"]<=r_m)&(rf["F"]<f_m), "用户分层"] = "新用户/浅度用户"
    rf.loc[(rf["R"]>r_m)&(rf["F"]>=f_m), "用户分层"] = "沉睡用户"
    rf.loc[(rf["R"]>r_m)&(rf["F"]<f_m), "用户分层"] = "流失用户"
    seg = rf.groupby("用户分层").agg(用户数=("user_id","count"),平均R=("R","mean"),平均F=("F","mean")).reset_index()
    seg["占比(%)"] = (seg["用户数"]/seg["用户数"].sum()*100).round(1)
    seg = seg.sort_values("用户数", ascending=False)
    print(seg.to_string(index=False))
    
    fig, ax = plt.subplots(figsize=(8,8))
    order = ["高价值用户","新用户/浅度用户","沉睡用户","流失用户"]
    seg_idx = seg.set_index("用户分层").reindex(order).dropna()
    colors = ["#4E79A7","#F28E2B","#E15759","#76B7B2"]
    ax.pie(seg_idx["用户数"], labels=seg_idx.index, autopct='%1.1f%%', colors=colors[:len(seg_idx)],
           startangle=90, explode=[0.03]*len(seg_idx))
    ax.set_title("用户分层")
    plt.tight_layout(); plt.savefig("图8_用户分层.png", dpi=150, bbox_inches='tight'); plt.close(); print("✅ 图8保存")
    rf.to_csv("用户分层结果.csv", index=False); print("✅ 分层结果保存")
    return rf, seg

if __name__ == "__main__":
    df = load_data()
    conversion_funnel(df)
    retention_analysis(df)
    user_segmentation(df)
    print("\n=== 全部分析完成 ===")
    print("生成文件：图1-8.png, 整体统计指标.txt, 用户分层结果.csv")
    print("下一步：撰写报告")