import matplotlib.pyplot as plt
import numpy as np

def create_comparison_bar_plot():
    # Data from benchmark results
    models = ["Gemini-3 Baseline", "Our Solution", "Experimental Fine-tune"]
    metrics = ["Accuracy", "Precision", "Recall", "F1-Score"]
    
    # Values for each model
    # Order: [Accuracy, Precision, Recall, F1-Score]
    values = {
        "Gemini-3 Baseline": [0.8163, 0.4598, 0.5904, 0.5170],
        "Our Solution": [0.9685, 0.8904, 0.9277, 0.9086],
        "Experimental Fine-tune": [0.5659, 0.2783, 0.9873, 0.4342]
    }

    # Set up the bar positions
    x = np.arange(len(metrics))
    width = 0.25  # width of the bars

    fig, ax = plt.subplots(figsize=(12, 7))

    # Plotting each model's metrics
    # Using the same color scheme as the confusion matrices for consistency
    rects1 = ax.bar(x - width, values["Gemini-3 Baseline"], width, label='Gemini-3 Baseline', color='#7f7f7f') # Gray
    rects2 = ax.bar(x, values["Our Solution"], width, label='Our Solution', color='#3071ad') # Blue
    rects3 = ax.bar(x + width, values["Experimental Fine-tune"], width, label='Experimental Fine-tune', color='#c44e52') # Red

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Score (0.0 - 1.0)', fontsize=14, weight='bold')
    ax.set_title('Comparative Performance Metrics across Models', fontsize=18, pad=20, weight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=14, weight='bold')
    ax.legend(fontsize=12, loc='upper left', bbox_to_anchor=(1, 1))

    # Set y-axis limit to 1.1 to give space for labels
    ax.set_ylim(0, 1.1)

    # Function to add labels on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, weight='bold')

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the plot
    output_path = "comparison_bar_plot.png"
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    print(f"Comparison bar plot saved to {output_path}")
    # plt.show()

if __name__ == "__main__":
    create_comparison_bar_plot()
