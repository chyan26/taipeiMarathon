import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Replace 'your_file.csv' with the path to your CSV file
file_path = '2025_tpe_marathon.csv'

# Import the CSV file into a DataFrame
df = pd.read_csv(file_path)

# Display the first few rows of the DataFrame
print(df.head())
# Convert 'Net Time' to hours (handling NaN values)
def time_to_hours(time_str):
    if pd.isna(time_str):  # Handle missing values
        return None
    h, m, s = map(int, time_str.split(':'))
    return h + m / 60 + s / 3600

df['Net Time (Hours)'] = df['Net Time'].apply(time_to_hours)

# Configure Chinese font
rcParams['font.sans-serif'] = ['SimHei']  # Use 'SimHei' for Chinese characters
rcParams['axes.unicode_minus'] = False    # Ensure minus sign displays correctly

# Plot the data
plt.figure(figsize=(8, 5))

# Group data and plot
for group, group_data in df.groupby('Group'):
    plt.hist(group_data['Net Time (Hours)'].dropna(), bins=5, alpha=0.6, label=group)

# Add plot details
plt.title('不同組別的淨時間分佈', fontsize=14)  # Title in Chinese
plt.xlabel('淨時間 (小時)', fontsize=12)       # X-axis label in Chinese
plt.ylabel('頻率', fontsize=12)              # Y-axis label in Chinese
plt.legend(title='組別', fontsize=10)         # Legend in Chinese
plt.grid(True)
plt.show()

unique_groups = df['Group'].unique()
num_unique_groups = df['Group'].nunique()

# Display the results
print(f"Unique Groups: {unique_groups}")
print(f"Number of Unique Groups: {num_unique_groups}")

df['Net Time (Hours)'] = df['Net Time'].apply(time_to_hours)

# Filter rows where Net Time is between 0 and 1 hour
filtered_df = df[(df['Net Time (Hours)'] >= 0) & (df['Net Time (Hours)'] < 1)]

# Print the filtered rows
print(filtered_df)