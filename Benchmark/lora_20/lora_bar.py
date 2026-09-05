import os
import matplotlib.pyplot as plt
import numpy as np

def plot_lora_results():
    # LoRA benchmark results provided by the user
    # Order: Precision, Recall, F1-Score, Accuracy
    categories = ['Precision', 'Recall', 'F1-Score', 'Accuracy']
    
    micro_avg = [0.2783, 0.9873, 0.4342, 0.5659]
    macro_avg = [0.3592, 0.9839, 0.4877, 0.6414]

    # Set up the plot
    x = np.arange(len(categories))
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Custom colors (consistent with previous plots)
    color_micro = "#4e79a7" # Soft blue
    color_macro = "#f28e2b" # Soft orange

    rects1 = ax.bar(x - width/2, micro_avg, width, label='Micro-averaged', color=color_micro, alpha=0.85)
    rects2 = ax.bar(x + width/2, macro_avg, width, label='Macro-averaged', color=color_macro, alpha=0.85)

    # Add labels, title and custom x-axis tick labels
    ax.set_ylabel('Scores', fontsize=12, fontweight='bold')
    ax.set_title('LoRA Benchmark: Overall Performance Metrics', fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.legend(loc='upper right', frameon=True, shadow=True, fontsize=10)
    
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
    output_path = os.path.join(os.path.dirname(__file__), "lora_results_bar.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"LoRA results plot saved to: {output_path}")

if __name__ == "__main__":
    plot_lora_results()
