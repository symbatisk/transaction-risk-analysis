import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

amount = "TransactionAmount (INR)"
balance = "CustAccountBalance"

weekday_order = ["Monday","Tuesday" , "Wednesday" , "Thursday", "Friday", "Saturday", "Sunday"]

age_bins = [10,17, 25, 35, 50 , 65, 100]
age_labels = ["<18", "18-25", "26-35", "36-50", "51-65", "66-100"]

def setup_style():
    plt.rcParams["figure.figsize"] = (10,5)
    plt.style.use("ggplot")

# load file
def load_data():
    df = pd.read_csv("data/sample.csv")
    print("Shape: ", df.shape)
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nInfo: ")
    df.info()
    return df

# clean data
def clean_data(df: pd.DataFrame) -> pd.DataFrame:

    df = df.drop_duplicates()
    print("\nMissing value:\n", df.isnull().sum())

    # data
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"], format="%d/%m/%y", errors="coerce")
    df["CustomerDOB"] = pd.to_datetime(df["CustomerDOB"],format="%d/%m/%y",  errors="coerce")

    df["TransactionTime"] = df["TransactionTime"].astype(str).str.zfill(6)
    df["Hour"] = pd.to_datetime(df["TransactionTime"], format= "%H%M%S", errors="coerce").dt.hour

    df = df.dropna(subset=["TransactionDate", amount, "CustLocation", "CustGender"]).copy()
    return df


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["Age"] = ((df["TransactionDate"] - df["CustomerDOB"]).dt.days / 365.25)
    df = df[df["Age"].between(10, 100)]

    df["AgeGroup"] = pd.cut(df["Age"], bins=age_bins, labels= age_labels)


    df["Month"] = df["TransactionDate"].dt.to_period("M")
    df["Weekday"] = df["TransactionDate"].dt.day_name()
    df["Weekday"] = pd.Categorical(df["Weekday"], categories= weekday_order, ordered = True)

    return df

# Outlier detection (IQR)
def detect_outliers_iqr(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    Q1 =df[amount].quantile(0.25)
    Q3 = df[amount].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    anomalies = df[(df[amount] < lower_bound) | (df[amount] > upper_bound)]
    normal = df[(df[amount] >= lower_bound) & (df[amount] <= upper_bound)]
    print(f"\nAnomalies: {len(anomalies)} ({len(anomalies) / len(df) * 100:.2f}%)")
    return anomalies, normal

# plot 1 transaction amount distribution (without outliers)
def plot_transaction_distribution(normal_df: pd.DataFrame) -> None:
    plt.figure(figsize=(10, 5))
    plt.hist(normal_df[amount], bins=40, color="steelblue", edgecolor="white")
    plt.title("Transaction Amount Distribution")
    plt.xlabel("Amount (INR)")
    plt.ylabel("Number of Transactions")  
    plt.tight_layout()
    plt.savefig("plots/01_distribution.png")
    plt.show()

# plot 2 top 10 cities
def plot_top_cities(df: pd.DataFrame) -> None:
    top_cities = df.groupby("CustLocation")[amount].sum().sort_values(ascending=False).head(10)
    plt.figure(figsize=(10, 5))
    bars = plt.bar(top_cities.index, top_cities.values, color="steelblue", edgecolor="white")

    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                str(int(bar.get_height())),
                ha="center", fontsize=9)

    plt.title("Top 10 Cities by Total Transaction Amount")
    plt.ylabel("Total Amount (INR)")
    plt.xlabel("City")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("plots/02_top_cities.png")
    plt.show()

# plot 3 Monthly transaction trend
def plot_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    monthly = df.groupby("Month")[amount].sum().reset_index()
    monthly["Month"] = monthly["Month"].astype(str)

    plt.figure()
    plt.plot(monthly["Month"], monthly[amount], marker="o", color="steelblue", linewidth=2)
    plt.fill_between(monthly["Month"], monthly[amount], alpha=0.1, color="steelblue")
    plt.title("Total Transaction Amount by Month")
    plt.xlabel("Month")
    plt.ylabel("Total Amount (INR)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("plots/03_monthly_trend.png")
    plt.show()

# plot 4 activity by weekday
def plot_weekday_activity(df: pd.DataFrame) -> None:
    weekday_stats = (df.groupby("Weekday", observed=True)[amount].sum().reset_index())

    plt.figure(figsize=(10, 5))
    bars = plt.bar(weekday_stats["Weekday"].astype(str), weekday_stats[amount],color="steelblue", edgecolor="white")

    for bar in bars:
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{bar.get_height():,.0f}",
            ha="center",
            va="bottom",
            fontsize=8
        )

    plt.title("Total Transaction Amount by Weekday")
    plt.xlabel("Weekday")
    plt.ylabel("Total Amount (INR)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("plots/04_weekday_activity.png")
    plt.show()


# plot 5 average transaction amount by gender

def plot_gender_count(df: pd.DataFrame) -> None:
    gender_count = df["CustGender"].value_counts()

    plt.figure()
    bars = plt.bar(gender_count.index, gender_count.values, color=["steelblue", "salmon"], edgecolor="white")

    plt.title("Transaction Count by Gender")
    plt.xlabel("Gender")
    plt.ylabel("Count")

    for i, v in enumerate(gender_count.values):
        plt.text(i, v, str(v), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig("plots/05_gender_count.png")
    plt.show()


# Plot 6 transaction amount by age group (boxplot)
def plot_age_group_boxplot(df: pd.DataFrame) -> None:
    age_box_data = [
        df[df["AgeGroup"] == group][amount].dropna()
        for group in age_labels
        if not df[df["AgeGroup"] == group][amount].dropna().empty
    ]
    age_box_labels = [
        group for group in age_labels
        if not df[df["AgeGroup"] == group][amount].dropna().empty
    ]

    plt.figure(figsize=(10, 5))
    plt.boxplot(age_box_data, tick_labels=age_box_labels, showfliers=False)

    plt.title("Transaction Amount Distribution by Age Group")
    plt.xlabel("Age Group")
    plt.ylabel("Amount (INR)")

    plt.tight_layout()
    plt.savefig("plots/06_age_group_boxplot.png")
    plt.show()

# plot 7 Correlation Between Transaction Features
def plot_correlation_matrix(df: pd.DataFrame) -> None:
    corr_df = df[["TransactionAmount (INR)", "CustAccountBalance", "Age", "Hour"]].dropna()
    corr = corr_df.corr()

    print(corr)
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")

    plt.title("Relationship Between Transaction Amount, Age, Balance and Time")
    plt.tight_layout()
    plt.savefig("plots/07_correlation_matrix.png")
    plt.show()

# plot 8 Transaction Activity by Day of Week and Hour
def plot_weekday_hour_heatmap(df: pd.DataFrame) -> None:
    pivot = df.pivot_table(
        values="TransactionAmount (INR)",
        index="Weekday",
        columns="Hour",
        aggfunc="count"
    )

    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot, cmap="YlGnBu")

    plt.title("Transaction Activity by Day of Week and Hour")
    plt.xlabel("Hour")
    plt.ylabel("Weekday")

    plt.tight_layout()
    plt.savefig("plots/08_heatmap_weekday_hour.png")
    plt.show()


# plot 9 Transaction amount vs account balance
def plot_amount_vs_balance(df: pd.DataFrame) -> None:
    balance_df = df.dropna(subset=[balance]).copy()
    plt.figure(figsize=(10, 5))
    plt.scatter(balance_df[balance], balance_df[amount], alpha=0.3)

    plt.title("Transaction Amount vs Account Balance")
    plt.xlabel("Account Balance")
    plt.ylabel("Transaction Amount (INR)")

    plt.tight_layout()
    plt.savefig("plots/09_amount_vs_balance.png")
    plt.show()



# Key Insights
def print_key_insights(df: pd.DataFrame,anomalies: pd.DataFrame,monthly: pd.DataFrame) -> None:
    print("\n── KEY INSIGHTS ──────────────────────────────────────")
    print(f"Total transactions:      {len(df):,}")
    print(f"Average amount:          {df[amount].mean():,.2f} INR")
    print(f"Median amount:           {df[amount].median():,.2f} INR")
    print(
        f"Anomalies detected:      {len(anomalies):,} "
        f"({len(anomalies) / len(df) * 100:.2f}%)"
    )
    print(f"Most active age group:   {df['AgeGroup'].value_counts().idxmax()}")
    print(f"Top gender by count:     {df['CustGender'].value_counts().idxmax()}")

    peak_month = monthly.loc[monthly[amount].idxmax(), "Month"]
    print(f"Peak transaction month:  {peak_month}")


def main() -> None:
    setup_style()
    df = load_data()
    df = clean_data(df)
    df = create_features(df)

    anomalies, normal = detect_outliers_iqr(df)
    print(f"\nAnomalies: {len(anomalies)} ({len(anomalies) / len(df) * 100:.2f}%)")

    plot_transaction_distribution(normal)
    plot_top_cities(df)
    monthly = plot_monthly_trend(df)
    plot_weekday_activity(df)
    plot_gender_count(df)
    plot_age_group_boxplot(df)
    plot_correlation_matrix(df)
    plot_weekday_hour_heatmap(df)
    plot_amount_vs_balance(df)


    print_key_insights(df, anomalies, monthly)
    print("\nAnalysis completed successfully. Plots saved to 'plots/' folder.")


if __name__ == "__main__":
    main()