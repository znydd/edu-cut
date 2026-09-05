import os
import matplotlib.pyplot as plt
import numpy as np

def plot_average_results():
    # Averaged results data provided by the user
    # Order: Precision, Recall, F1-Score, Accuracy
    categories = ['Precision', 'Recall', 'F1-Score', 'Accuracy']
    
    micro_avg = [0.8904, 0.9277, 0.9086, 0.9685]
    macro_avg = [0.9041, 0.9101, 0.8973, 0.9714]

    # Set up the plot
    x = np.arange(len(categories))
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Custom colors
    color_micro = "#4e79a7" # Soft blue
    color_macro = "#f28e2b" # Soft orange

    rects1 = ax.bar(x - width/2, micro_avg, width, label='Micro-averaged', color=color_micro, alpha=0.85)
    rects2 = ax.bar(x + width/2, macro_avg, width, label='Macro-averaged', color=color_macro, alpha=0.85)

    # Add labels, title and custom x-axis tick labels
    ax.set_ylabel('Scores', fontsize=12, fontweight='bold')
    ax.set_title('Overall Performance Metrics (Averaged)', fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.legend(loc='lower right', frameon=True, shadow=True, fontsize=10)
    
    # Set y-axis limit
    ax.set_ylim(0, 1.1)
    
    # Add horizontal grid lines
    ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=0.3)
    ax.set_axisbelow(True)

    # Function to add labels on top of bars
    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.4f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()

    # Save the plot
    output_path = os.path.join(os.path.dirname(__file__), "result_bar_avg.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Average results plot saved to: {output_path}")

if __name__ == "__main__":
    plot_average_results()
