import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def plot_confusion_matrices():
    # Confusion Matrix Data: [[TN, FP], [FN, TP]]
    # Actual classes: Relevant, Irrelevant
    # Predicted classes: Relevant, Irrelevant
    
    data = {
        "Gemini-3 Baseline": {
            "matrix": [[3337, 537], [317, 457]],
            "tp": 457, "fp": 537, "tn": 3337, "fn": 317
        },
        "Our Solution": {
            "matrix": [[3794, 90], [57, 731]],
            "tp": 731, "fp": 90, "tn": 3794, "fn": 57
        },
        "Experimental Fine-tune": {
            "matrix": [[1866, 2018], [10, 778]],
            "tp": 778, "fp": 2018, "tn": 1866, "fn": 10
        }
    }

    labels = ["Relevant", "Irrelevant"]
    fig, axes = plt.subplots(1, 3, figsize=(22, 7))
    plt.subplots_adjust(wspace=0.6, bottom=0.25)

    # Custom color maps for each
    cmaps = ["Greys", "Blues", "Reds"]

    for i, (name, results) in enumerate(data.items()):
        ax = axes[i]
        matrix = np.array(results["matrix"])
        
        # Calculate totals
        row_sums = matrix.sum(axis=1)  # Actual counts
        col_sums = matrix.sum(axis=0)  # Predicted counts
        grand_total = matrix.sum()
        
        # Calculate percentages for annotation
        percentages = (matrix / grand_total * 100)
        
        # Formatting text labels
        group_names = ['TN','FP','FN','TP']
        group_counts = [f"{value}" for value in matrix.flatten()]
        group_percentages = [f"{value:.1f}%" for value in percentages.flatten()]
        
        box_labels = [f"{v1}\n{v2}\n({v3})" for v1, v2, v3 in zip(group_names, group_counts, group_percentages)]
        box_labels = np.asarray(box_labels).reshape(2,2)
        
        # Heatmap
        sns.heatmap(matrix, annot=box_labels, fmt="", cmap=cmaps[i], cbar=False, ax=ax,
                    xticklabels=labels, yticklabels=labels, annot_kws={"size": 11, "weight": "bold"})
        
        # Column Totals (Predicted)
        ax.text(0.5, 2.15, f'Pred: {col_sums[0]}', ha='center', va='top', fontsize=10, weight='bold', color='black')
        ax.text(1.5, 2.15, f'Pred: {col_sums[1]}', ha='center', va='top', fontsize=10, weight='bold', color='black')
        
        # Row Totals (Actual)
        ax.text(2.05, 0.5, f'Actual:\n{row_sums[0]}', ha='left', va='center', fontsize=10, weight='bold', color='black')
        ax.text(2.05, 1.5, f'Actual:\n{row_sums[1]}', ha='left', va='center', fontsize=10, weight='bold', color='black')

        # Total
        ax.text(2.05, 2.15, f'Total:\n{grand_total}', ha='left', va='top', fontsize=10, weight='bold', color='darkblue')

        ax.set_title(f"{name}", fontsize=15, pad=30, weight='bold')
        ax.set_xlabel("Predicted Label", fontsize=12, labelpad=45)
        if i == 0:
            ax.set_ylabel("Actual Label", fontsize=12)
        else:
            ax.set_ylabel("")

    plt.suptitle("Confusion Matrix with Marginal Totals", fontsize=20, y=1.05, weight='bold')
    
    # Save the combined figure
    plt.savefig("confusion_matrices_combined.png", bbox_inches='tight', dpi=300)
    print("Combined diagram saved to confusion_matrices_combined.png")

    # Save individual figures
    filenames = {
        "Gemini-3 Baseline": "confusion_matrix_gemini.png",
        "Our Solution": "confusion_matrix_solution.png",
        "Experimental Fine-tune": "confusion_matrix_lora.png"
    }
    
    for i, (name, filename) in enumerate(filenames.items()):
        results = data[name]
        fig, ax = plt.subplots(figsize=(8, 7))
        matrix = np.array(results["matrix"])
        row_sums = matrix.sum(axis=1)
        col_sums = matrix.sum(axis=0)
        grand_total = matrix.sum()
        percentages = (matrix / grand_total * 100)
        
        group_names = ['TN','FP','FN','TP']
        group_counts = [f"{value}" for value in matrix.flatten()]
        group_percentages = [f"{value:.1f}%" for value in percentages.flatten()]
        box_labels = [f"{v1}\n{v2}\n({v3})" for v1, v2, v3 in zip(group_names, group_counts, group_percentages)]
        box_labels = np.asarray(box_labels).reshape(2,2)
        
        sns.heatmap(matrix, annot=box_labels, fmt="", cmap=cmaps[i], cbar=False, ax=ax,
                    xticklabels=labels, yticklabels=labels, annot_kws={"size": 13, "weight": "bold"})
        
        ax.text(0.5, 2.15, f'Predicted: {col_sums[0]}', ha='center', va='top', fontsize=11, weight='bold')
        ax.text(1.5, 2.15, f'Predicted: {col_sums[1]}', ha='center', va='top', fontsize=11, weight='bold')
        ax.text(2.05, 0.5, f'Actual: {row_sums[0]}', ha='left', va='center', fontsize=11, weight='bold')
        ax.text(2.05, 1.5, f'Actual: {row_sums[1]}', ha='left', va='center', fontsize=11, weight='bold')
        ax.text(2.05, 2.15, f'Total: {grand_total}', ha='left', va='top', fontsize=11, weight='bold', color='darkblue')

        plt.title(f"{name}", fontsize=17, pad=35, weight='bold')
        plt.xlabel("Predicted Label", fontsize=14, labelpad=50)
        plt.ylabel("Actual Label", fontsize=14)
        
        plt.savefig(filename, bbox_inches='tight', dpi=300)
        print(f"Individual diagram saved to {filename}")
        plt.close()

if __name__ == "__main__":
    sns.set_theme(style="white")
    plot_confusion_matrices()
